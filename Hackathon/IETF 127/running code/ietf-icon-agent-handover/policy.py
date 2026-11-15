"""Control checks. First match wins, in the order fixed by the plan."""

from __future__ import annotations

from dataclasses import dataclass

from world import (
    ALLOW,
    BLAST_LIMIT,
    CORE,
    CORE_CAP,
    EDGE,
    EDGE_CAP,
    HARD_BUDGET,
    RATE_LIMIT,
    SOFT_CEILING,
    UNITS,
    Proposal,
    World,
)

KNOWN = {
    "request_compute",
    "request_bandwidth",
    "set_variant",
    "handover",
    "release_source",
}
FORBIDDEN = ("subscriber_id", "raw_key", "playback_url")


@dataclass
class Verdict:
    decision: str
    reason: str
    risk: str
    measured: dict


def evaluate(world: World, proposal: Proposal) -> Verdict:
    risk = classify(world, proposal)
    if world.paused:
        return Verdict("paused", "PAUSED", risk, {"paused": True})
    if proposal.action not in KNOWN:
        return Verdict("refuse", "UNKNOWN", risk, {"action": proposal.action})
    if proposal.action == "release_source":
        session = world.sessions[proposal.sessions[0]]
        if not session.acked:
            return Verdict(
                "refuse",
                "RELEASE_BEFORE_ACK",
                risk,
                {"session_id": session.session_id, "acked": False},
            )
    if proposal.target is not None and proposal.target not in ALLOW:
        return Verdict(
            "refuse",
            "TARGET_NOT_ALLOWED",
            risk,
            {"target": proposal.target},
        )
    forbidden = forbidden_fields(world, proposal)
    if forbidden:
        return Verdict("refuse", "SECRET_IN_BUNDLE", risk, {"fields": forbidden})
    if proposal.action == "handover" and len(proposal.sessions) > BLAST_LIMIT:
        return Verdict(
            "refuse",
            "BLAST_RADIUS",
            risk,
            {"sessions": len(proposal.sessions), "limit": BLAST_LIMIT},
        )
    if (
        proposal.action == "handover"
        and world.handovers_this_tick + len(proposal.sessions) > RATE_LIMIT
    ):
        return Verdict(
            "refuse",
            "RATE_LIMIT",
            risk,
            {"sessions": world.handovers_this_tick + len(proposal.sessions), "limit": RATE_LIMIT},
        )
    capacity = capacity_over(world, proposal)
    if capacity is not None:
        return Verdict("refuse", "OVER_CAPACITY", risk, capacity)
    budget = budget_over(world, proposal)
    if budget is not None:
        return Verdict("refuse", "OVER_BUDGET", risk, budget)
    if needs_human(world, proposal):
        path_after = world.project_handover_path(proposal.sessions[0], proposal.variant or "4K")
        return Verdict(
            "needs_approval",
            "NEEDS_HUMAN",
            risk,
            {"path_after": path_after, "soft_ceiling": SOFT_CEILING, "hard_budget": HARD_BUDGET},
        )
    return Verdict("allow", allow_reason(proposal), risk, allow_measured(world, proposal))


def classify(world: World, proposal: Proposal) -> str:
    if forbidden_fields(world, proposal) or bad_target(proposal) or len(proposal.sessions) > BLAST_LIMIT:
        return "critical"
    if proposal.action == "handover" and proposal.variant == "4K":
        path_after = world.project_handover_path(proposal.sessions[0], "4K")
        if path_after > SOFT_CEILING:
            return "high"
        return "medium"
    if proposal.variant == "4K" and proposal.action in {"set_variant", "request_compute"}:
        return "medium"
    return "low"


def bad_target(proposal: Proposal) -> bool:
    return proposal.target is not None and proposal.target not in ALLOW


def forbidden_fields(world: World, proposal: Proposal) -> list[str]:
    found = []
    for session_id in proposal.sessions:
        bundle = world.bundle_for(proposal, world.sessions[session_id])
        for key in FORBIDDEN:
            if key in bundle and key not in found:
                found.append(key)
    return found


def capacity_over(world: World, proposal: Proposal) -> dict | None:
    if proposal.action == "set_variant":
        session = world.sessions[proposal.sessions[0]]
        node = session.home_node or EDGE
        cap = EDGE_CAP if node == EDGE else CORE_CAP
        projected = world.used(node) - UNITS[session.variant] + UNITS[proposal.variant or "HD"]
        if projected > cap:
            return {"projected_units": projected, "limit": cap, "node": node}
        return None
    if proposal.action == "request_compute":
        node = proposal.target or EDGE
        cap = EDGE_CAP if node == EDGE else CORE_CAP
        projected = projected_reserve(world, node, proposal.sessions[0], proposal.variant or "HD")
        if projected > cap:
            return {"projected_units": projected, "limit": cap, "node": node}
        return None
    if proposal.action == "handover":
        node = proposal.target or CORE
        cap = EDGE_CAP if node == EDGE else CORE_CAP
        projected = projected_handover_units(world, proposal)
        if projected > cap:
            return {"projected_units": projected, "limit": cap, "node": node}
    return None


def budget_over(world: World, proposal: Proposal) -> dict | None:
    projected = projected_path(world, proposal)
    if projected is None:
        return None
    if projected > HARD_BUDGET:
        return {"path_after": projected, "limit": HARD_BUDGET}
    return None


def needs_human(world: World, proposal: Proposal) -> bool:
    return (
        proposal.action == "handover"
        and proposal.variant == "4K"
        and proposal.target == CORE
        and not world.grant
        and len(proposal.sessions) == 1
        and world.project_handover_path(proposal.sessions[0], "4K") > SOFT_CEILING
    )


def allow_reason(proposal: Proposal) -> str:
    if proposal.action == "request_bandwidth":
        return "WITHIN_BUDGET"
    if proposal.action == "handover":
        return "HANDOVER_ALLOWED"
    if proposal.action == "release_source":
        return "SOURCE_RELEASED"
    return "WITHIN_CAPACITY"


def allow_measured(world: World, proposal: Proposal) -> dict:
    if proposal.action == "handover":
        variant = proposal.variant or "HD"
        return {
            "sessions": len(proposal.sessions),
            "limit": BLAST_LIMIT,
            "path_after": world.project_handover_path(proposal.sessions[0], variant),
            "hard_budget": HARD_BUDGET,
        }
    if proposal.action == "request_bandwidth":
        return {"mbps": proposal.mbps, "limit": HARD_BUDGET}
    node = proposal.target or EDGE
    cap = EDGE_CAP if node == EDGE else CORE_CAP
    return {"limit": cap, "node": node}


def projected_path(world: World, proposal: Proposal) -> int | None:
    if proposal.action == "request_bandwidth":
        session_id = proposal.sessions[0]
        current = world.bandwidth_holds.get(session_id, 0)
        if world.sessions[session_id].home_node == CORE:
            return world.path() + (proposal.mbps or 0)
        return world.path() - current + (proposal.mbps or 0)
    if proposal.action == "handover" and len(proposal.sessions) == 1:
        variant = proposal.variant or world.sessions[proposal.sessions[0]].variant
        return world.project_handover_path(proposal.sessions[0], variant)
    return None


def projected_reserve(world: World, node: str, session_id: str, variant: str) -> int:
    extra = 0
    for other, (where, units, _variant) in world.reservations.items():
        if other == session_id:
            continue
        if where == node and world.sessions[other].home_node != node:
            extra += units
    return world.used(node) + extra + UNITS[variant]


def projected_handover_units(world: World, proposal: Proposal) -> int:
    session_id = proposal.sessions[0]
    session = world.sessions[session_id]
    node = proposal.target or CORE
    variant = proposal.variant or session.variant
    cost = UNITS[variant]
    extra = 0
    for other, (where, units, _variant) in world.reservations.items():
        if other == session_id:
            continue
        if where == node and world.sessions[other].home_node != node:
            extra += units
    if session.home_node == node:
        return world.used(node) - UNITS[session.variant] + cost + extra
    return world.used(node) + cost + extra
