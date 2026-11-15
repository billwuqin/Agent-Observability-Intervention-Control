"""Operator commands. A proposal cannot set the pause flag or roll the world back."""

from __future__ import annotations

from trace import Trace
from world import CORE, CORE_CAP, EDGE, EDGE_CAP, Record, World

OPERATOR = "operator-1"


def approve(world: World, trace: Trace, step_id: str, tick: int, target: str) -> Record:
    accepted = True
    world.grant = True
    applied = world.grant
    trace.add(
        "human.intervention",
        proposal_id=step_id,
        tick=tick,
        mechanism="control",
        command="approve",
        operator_id=OPERATOR,
        scope=target,
        accepted=accepted,
        applied=applied,
        result="completed",
        grant="4K moves from edge-small to core-large may use the hard budget for this run",
    )
    return _record(step_id, tick, "approve", "incident grant", False, "control", "completed", accepted, applied)


def pause(world: World, trace: Trace, step_id: str, tick: int) -> Record:
    before = _brief(world)
    accepted = True
    world.paused = True
    applied = world.paused
    after = _brief(world)
    trace.add(
        "human.intervention",
        proposal_id=step_id,
        tick=tick,
        mechanism="intervention",
        command="pause",
        operator_id=OPERATOR,
        scope="agent",
        accepted=accepted,
        applied=applied,
        result="completed",
        before=before,
        after=after,
    )
    return _record(step_id, tick, "pause", "out of band", False, "intervention", "completed", accepted, applied)


def rollback(world: World, trace: Trace, step_id: str, tick: int) -> Record:
    if world.checkpoint is None or world.checkpoint_proposal is None or world.checkpoint_id is None:
        raise RuntimeError("rollback requested with no checkpoint")
    target = world.checkpoint_proposal
    checkpoint_id = world.checkpoint_id
    before = _brief(world)
    world.restore(world.checkpoint)
    world.rolled_back.append(target)
    after = _brief(world)
    accepted = True
    applied = target in world.rolled_back and not world.partial
    trace.add(
        "recovery.attempt",
        proposal_id=step_id,
        tick=tick,
        mechanism="intervention",
        command="rollback",
        operator_id=OPERATOR,
        scope="workflow",
        target_proposal=target,
        checkpoint_id=checkpoint_id,
        accepted=accepted,
        applied=applied,
        result="completed",
        before=before,
        after=after,
    )
    trace.add(
        "checkpoint.restored",
        proposal_id=step_id,
        checkpoint_id=checkpoint_id,
        target_proposal=target,
    )
    return _record(step_id, tick, "rollback", "workflow scope", True, "intervention", "completed", accepted, applied)


def correct(world: World, trace: Trace, step_id: str, tick: int, plan: str) -> Record:
    accepted = True
    world.pending_plan = plan
    world.paused = False
    applied = world.pending_plan == plan and not world.paused
    trace.add(
        "human.intervention",
        proposal_id=step_id,
        tick=tick,
        mechanism="intervention",
        command="correct",
        operator_id=OPERATOR,
        scope="plan",
        accepted=accepted,
        applied=applied,
        result="completed",
        plan=plan,
    )
    trace.add("plan.revised", proposal_id=step_id, tick=tick, plan=plan)
    return _record(step_id, tick, "correct", "plan replace", False, "intervention", "completed", accepted, applied)


def _record(
    step_id: str,
    tick: int,
    action: str,
    reason: str,
    mutated: bool,
    mechanism: str,
    result: str,
    accepted: bool,
    applied: bool,
) -> Record:
    return Record(
        id=step_id,
        kind="operator",
        tick=tick,
        action=action,
        decision=action,
        reason=reason,
        mutated=mutated,
        result=result,
        mechanism=mechanism,
        accepted=accepted,
        applied=applied,
    )


def _brief(world: World) -> dict:
    return {
        "edge": f"{world.used(EDGE)}/{EDGE_CAP}",
        "core": f"{world.used(CORE)}/{CORE_CAP}",
        "path": world.path(),
        "partial": sorted(world.partial),
        "homes": {sid: session.home_node for sid, session in world.sessions.items()},
        "connections": {sid: session.connection_id for sid, session in world.sessions.items()},
    }
