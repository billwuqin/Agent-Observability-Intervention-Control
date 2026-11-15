"""Run the ICON video-handover ledger and print the scoreboard.

    python demo.py
"""

import sys

if sys.version_info < (3, 10):
    import os
    import shutil

    candidate = shutil.which("python3.11") or shutil.which("python3.10")
    if candidate:
        os.execv(candidate, [candidate] + sys.argv)
    sys.stderr.write("Python 3.10 or newer is required.\n")
    raise SystemExit(1)

import json
from collections import Counter
from pathlib import Path

import control
import intervention
import script
from script import Operator, steps
from trace import Trace
from world import CORE, Proposal, new_world

EXPECTED_BOARD = """\
ICON handover scoreboard
  control allow=11 refuse=7 needs_approval=1 paused=1
  allow_still_in_effect=10 allow_rolled_back=1
  probes_caught_before_side_effect=3/3
  intervention pause=completed rollback=completed
  sessions_continuous=s1,s2,s4 sessions_split=0
  s3_home=edge-small s3_conn=c3 playback_sec=120
  blast_radius_max_in_one_allowed_action=1 limit=2
  edge_units=2/8 core_units=14/32 path_mbps=35/40
  secrets_in_trace=0
  human.intervention=3 recovery.attempt=1 checkpoint.restored=1"""

LIMITS = {
    "edge_cap": 8,
    "core_cap": 32,
    "hard_budget_mbps": 40,
    "soft_ceiling_mbps": 20,
    "blast_limit": 2,
    "handovers_per_tick": 3,
}


def observe(world) -> tuple:
    homes = tuple(
        (sid, session.home_node, session.connection_id, session.variant, session.playback_sec)
        for sid, session in world.sessions.items()
        if session.home_node is not None
    )
    return (
        world.used("edge-small"),
        world.used("core-large"),
        world.reserved_total("core-large"),
        world.path(),
        world.paused,
        world.grant,
        tuple(sorted(world.partial)),
        homes,
    )


def run():
    world = new_world()
    trace = Trace()
    records = []
    trace.add("session.start", sessions=["s1", "s2", "s3", "s4"])
    announced: set[int] = set()
    planned = False
    for step in steps():
        if isinstance(step, Proposal) and step.tick not in announced and step.tick in (0, 1):
            arriving = ["s1", "s2"] if step.tick == 0 else ["s3", "s4"]
            trace.add("task.received", tick=step.tick, sessions=arriving, limits=LIMITS)
            announced.add(step.tick)
        if isinstance(step, Proposal) and step.id == "D7" and not planned:
            trace.add(
                "plan.created",
                tick=step.tick,
                plan="handover s1 and s2 from edge-small to core-large as 4K",
            )
            planned = True
        if isinstance(step, Proposal):
            record = control.submit(world, step, trace)
            expect = script.DECISION[step.id]
            if (record.decision, record.reason, record.mutated) != expect:
                raise SystemExit(
                    f"{step.id}: got {(record.decision, record.reason, record.mutated)} expected {expect}"
                )
        elif step.command == "approve":
            record = intervention.approve(world, trace, step.id, step.tick, step.target)
        elif step.command == "pause":
            record = intervention.pause(world, trace, step.id, step.tick)
        elif step.command == "rollback":
            record = intervention.rollback(world, trace, step.id, step.tick)
            if world.rolled_back != [step.target]:
                raise SystemExit(f"{step.id}: rolled back {world.rolled_back}, expected {[step.target]}")
        elif step.command == "correct":
            record = intervention.correct(world, trace, step.id, step.tick, step.plan)
        else:
            raise SystemExit(f"unknown step {step}")
        if record.kind == "operator" and record.result != "completed":
            raise SystemExit(f"{record.id} result {record.result}")
        actual = observe(world)
        expected = script.AFTER[record.id]
        if actual != expected:
            raise SystemExit(f"{record.id}: world {actual} != {expected}")
        records.append((record, actual))
    trace.add("session.end", sessions=["s1", "s2", "s3", "s4"])
    return world, trace, records


def scoreboard(world, trace, records) -> str:
    controls = [record for record, _obs in records if record.kind == "control"]
    allow = sum(1 for record in controls if record.decision == "allow")
    refuse = sum(1 for record in controls if record.decision == "refuse")
    needs = sum(1 for record in controls if record.decision == "needs_approval")
    paused = sum(1 for record in controls if record.decision == "paused")
    rolled = sum(1 for record in controls if record.decision == "allow" and record.id in world.rolled_back)
    probes = [
        record
        for record in controls
        if record.id in {"D13", "D14", "D15"} and record.decision == "refuse" and not record.mutated
    ]
    continuous = [
        sid
        for sid in ("s1", "s2", "s4")
        if _continuous(world, sid)
    ]
    split = sum(
        1
        for sid, session in world.sessions.items()
        if session.home_node is not None and sid in world.partial
    )
    blast = max(
        (record.session_count for record in controls if record.decision == "allow" and record.action == "handover"),
        default=0,
    )
    exported = json.dumps(trace.events)
    secrets = exported.count("user-1001")
    counts = Counter(event["event_type"] for event in trace.events)
    pause = next(record for record, _obs in records if record.id == "I1")
    undo = next(record for record, _obs in records if record.id == "I2")
    session = world.sessions["s3"]
    return "\n".join(
        [
            "ICON handover scoreboard",
            f"  control allow={allow} refuse={refuse} needs_approval={needs} paused={paused}",
            f"  allow_still_in_effect={allow - rolled} allow_rolled_back={rolled}",
            f"  probes_caught_before_side_effect={len(probes)}/3",
            f"  intervention pause={pause.result} rollback={undo.result}",
            f"  sessions_continuous={','.join(continuous)} sessions_split={split}",
            f"  s3_home={session.home_node} s3_conn={session.connection_id} playback_sec={session.playback_sec}",
            f"  blast_radius_max_in_one_allowed_action={blast} limit=2",
            f"  edge_units={world.used('edge-small')}/8 core_units={world.used(CORE)}/32 path_mbps={world.path()}/40",
            f"  secrets_in_trace={secrets}",
            (
                f"  human.intervention={counts['human.intervention']} "
                f"recovery.attempt={counts['recovery.attempt']} "
                f"checkpoint.restored={counts['checkpoint.restored']}"
            ),
        ]
    )


def _continuous(world, session_id: str) -> bool:
    session = world.sessions[session_id]
    original = {"s1": "c1", "s2": "c2", "s3": "c3", "s4": "c4"}[session_id]
    return (
        session.home_node == CORE
        and session.connection_id == f"{original}b"
        and session.playback_sec == 120
        and session.session_id == session_id
    )


def check(world, trace, board: str) -> list[str]:
    errors = []
    if board != EXPECTED_BOARD:
        errors.append("scoreboard does not match the ledger")
    exported = json.dumps(trace.events)
    path = Path(__file__).with_name("trace.json")
    path.write_text(exported + "\n", encoding="utf-8")
    if "user-1001" in path.read_text(encoding="utf-8"):
        errors.append("exported trace contains user-1001")
    secret_in_script = any(
        isinstance(step, Proposal) and (step.bundle_extra or {}).get("subscriber_id") == "user-1001"
        for step in steps()
    )
    if not secret_in_script:
        errors.append("D15 no longer carries the subscriber id fixture")
    counts = Counter(event["event_type"] for event in trace.events)
    expected_counts = {
        "assertion.evaluated": 20,
        "human.intervention": 3,
        "recovery.attempt": 1,
        "checkpoint.created": 4,
        "checkpoint.restored": 1,
        "session.start": 1,
        "session.end": 1,
        "task.received": 2,
        "plan.created": 1,
        "plan.revised": 1,
    }
    for name, count in expected_counts.items():
        if counts[name] != count:
            errors.append(f"{name}={counts[name]} expected {count}")
    humans = [event for event in trace.events if event["event_type"] == "human.intervention"]
    if [event["command"] for event in humans] != ["approve", "pause", "correct"]:
        errors.append(f"human commands {[event['command'] for event in humans]}")
    if [event["mechanism"] for event in humans] != ["control", "intervention", "intervention"]:
        errors.append(f"human mechanisms {[event['mechanism'] for event in humans]}")
    results = [event for event in trace.events if event["event_type"] == "tool.result"]
    statuses = [event["status"] for event in results]
    if statuses != ["success", "success", "failed", "success"]:
        errors.append(f"tool results {statuses}")
    if world.pending_plan != "handover s4 only":
        errors.append(f"pending plan {world.pending_plan!r}")
    if world.paused:
        errors.append("pause flag still set after correction")
    return errors


def print_log(records) -> None:
    print("ICON video handover — decision log")
    for record, obs in records:
        edge, core, _reserved, path, _paused, _grant, partial, _homes = obs
        suffix = f" partial={','.join(partial)}" if partial else ""
        print(
            f"{record.id:<4} tick={record.tick:<2} {record.decision:<14} {record.reason:<20} "
            f"mutated={str(record.mutated).lower():<5} "
            f"edge={edge}/8 core={core}/32 path={path}/40{suffix}"
        )


def main() -> int:
    try:
        world, trace, records = run()
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 1
    print_log(records)
    board = scoreboard(world, trace, records)
    print()
    print(board)
    errors = check(world, trace, board)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print()
    print("Browser view: python3 ui.py")
    print("http://127.0.0.1:8765")
    return 0


if __name__ == "__main__":
    sys.exit(main())
