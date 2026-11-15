"""Policy gate. The world changes only after an allow."""

from __future__ import annotations

from trace import Trace
from world import Proposal, Record, World
import policy


def submit(world: World, proposal: Proposal, trace: Trace) -> Record:
    if proposal.tick != world.tick:
        world.tick = proposal.tick
        world.handovers_this_tick = 0
    verdict = policy.evaluate(world, proposal)
    record = Record(
        id=proposal.id,
        kind="control",
        tick=proposal.tick,
        action=proposal.action,
        decision=verdict.decision,
        reason=verdict.reason,
        mutated=False,
        risk=verdict.risk,
        session_count=len(proposal.sessions),
    )
    bundle_fields: list[str] = []
    if proposal.sessions:
        keys: set[str] = set()
        for session_id in proposal.sessions:
            keys.update(world.bundle_for(proposal, world.sessions[session_id]).keys())
        bundle_fields = sorted(keys)
    trace.add(
        "assertion.evaluated",
        proposal_id=proposal.id,
        tick=proposal.tick,
        action=proposal.action,
        decision=verdict.decision,
        reason=verdict.reason,
        risk=verdict.risk,
        measured=verdict.measured,
        bundle_fields=bundle_fields,
        mutated=False,
    )
    if verdict.decision == "allow":
        if proposal.action == "handover" and len(proposal.sessions) != 1:
            raise RuntimeError(f"{proposal.id} allowed a multi-session handover")
        events = world.apply(proposal)
        record.mutated = True
        trace.events[-1]["mutated"] = True
        for event in events:
            trace.add(event.event_type, proposal_id=proposal.id, **event.fields)
    return record
