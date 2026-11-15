"""In-memory streaming world: two nodes, one path, four sessions."""

from __future__ import annotations

import copy
from dataclasses import dataclass

EDGE = "edge-small"
CORE = "core-large"
ALLOW = {EDGE, CORE}
EDGE_CAP = 8
CORE_CAP = 32
HARD_BUDGET = 40
SOFT_CEILING = 20
BLAST_LIMIT = 2
RATE_LIMIT = 3
PLAYBACK = 120

UNITS = {"HD": 2, "4K": 6}
MBPS = {"HD": 5, "4K": 15}

# A handover of this session copies state and then the target ack fails.
ACK_FAILS = {"s3"}


@dataclass
class Session:
    session_id: str
    connection_id: str
    subscriber_token: str
    home_node: str | None = None
    variant: str = "HD"
    playback_sec: int = PLAYBACK
    buffer_sec: int = 4
    key_id: str = ""
    acked: bool = False

    def __post_init__(self) -> None:
        if not self.key_id:
            self.key_id = f"key-{self.session_id}"


@dataclass
class Proposal:
    id: str
    tick: int
    action: str
    sessions: list[str]
    target: str | None = None
    variant: str | None = None
    mbps: int | None = None
    bundle_extra: dict | None = None


@dataclass
class Record:
    id: str
    kind: str
    tick: int
    action: str
    decision: str
    reason: str
    mutated: bool
    risk: str = "-"
    result: str = "-"
    mechanism: str = "-"
    session_count: int = 0
    accepted: bool | None = None
    applied: bool | None = None


@dataclass
class ApplyEvent:
    event_type: str
    fields: dict


def new_world() -> "World":
    sessions = {
        "s1": Session("s1", "c1", "tok-s1"),
        "s2": Session("s2", "c2", "tok-s2"),
        "s3": Session("s3", "c3", "tok-s3"),
        "s4": Session("s4", "c4", "tok-s4"),
    }
    return World(sessions=sessions)


class World:
    def __init__(self, sessions: dict[str, Session]) -> None:
        self.sessions = sessions
        self.reservations: dict[str, tuple[str, int, str]] = {}
        self.bandwidth_holds: dict[str, int] = {}
        self.partial: dict[str, dict] = {}
        self.grant = False
        self.paused = False
        self.tick = -1
        self.handovers_this_tick = 0
        self.pending_plan = ""
        self.checkpoint: dict | None = None
        self.checkpoint_id: str | None = None
        self.checkpoint_proposal: str | None = None
        self.rolled_back: list[str] = []

    def used(self, node: str) -> int:
        return sum(
            UNITS[session.variant]
            for session in self.sessions.values()
            if session.home_node == node
        )

    def reserved_total(self, node: str) -> int:
        extra = sum(
            units
            for sid, (where, units, _variant) in self.reservations.items()
            if where == node and self.sessions[sid].home_node != node
        )
        return self.used(node) + extra

    def path(self) -> int:
        total = 0
        for session in self.sessions.values():
            if session.home_node == CORE:
                total += MBPS[session.variant]
            elif session.session_id in self.partial:
                variant = self.partial[session.session_id]["variant"]
                total += MBPS[variant]
            elif session.session_id in self.bandwidth_holds:
                total += self.bandwidth_holds[session.session_id]
        return total

    def project_handover_path(self, session_id: str, variant: str) -> int:
        session = self.sessions[session_id]
        if session.home_node == CORE and session.variant == variant and session_id not in self.partial:
            return self.path()
        hold = 0
        if session.home_node != CORE and session_id not in self.partial:
            hold = self.bandwidth_holds.get(session_id, 0)
        return self.path() - hold + MBPS[variant]

    def bundle_for(self, proposal: Proposal, session: Session) -> dict:
        variant = proposal.variant or session.variant
        bundle = {
            "session_id": session.session_id,
            "playback_sec": session.playback_sec,
            "buffer_sec": session.buffer_sec,
            "variant": variant,
            "key_id": session.key_id,
            "subscriber_token": session.subscriber_token,
        }
        if proposal.bundle_extra:
            bundle.update(proposal.bundle_extra)
        return bundle

    def snapshot(self) -> dict:
        return {
            "sessions": copy.deepcopy(self.sessions),
            "reservations": copy.deepcopy(self.reservations),
            "bandwidth_holds": copy.deepcopy(self.bandwidth_holds),
            "partial": copy.deepcopy(self.partial),
            "grant": self.grant,
        }

    def restore(self, saved: dict) -> None:
        self.sessions = copy.deepcopy(saved["sessions"])
        self.reservations = copy.deepcopy(saved["reservations"])
        self.bandwidth_holds = copy.deepcopy(saved["bandwidth_holds"])
        self.partial = copy.deepcopy(saved["partial"])
        self.grant = saved["grant"]

    def apply(self, proposal: Proposal) -> list[ApplyEvent]:
        action = proposal.action
        if action == "request_compute":
            self._admit_or_reserve(proposal)
            return []
        if action == "request_bandwidth":
            self.bandwidth_holds[proposal.sessions[0]] = proposal.mbps or 0
            return []
        if action == "set_variant":
            self.sessions[proposal.sessions[0]].variant = proposal.variant or "HD"
            return []
        if action == "handover":
            return self._handover(proposal)
        if action == "release_source":
            session = self.sessions[proposal.sessions[0]]
            session.home_node = None
            return []
        raise ValueError(f"unknown action {action}")

    def _admit_or_reserve(self, proposal: Proposal) -> None:
        session = self.sessions[proposal.sessions[0]]
        variant = proposal.variant or "HD"
        units = UNITS[variant]
        if proposal.target == EDGE:
            session.home_node = EDGE
            session.variant = variant
            return
        self.reservations[session.session_id] = (proposal.target or CORE, units, variant)

    def _handover(self, proposal: Proposal) -> list[ApplyEvent]:
        session = self.sessions[proposal.sessions[0]]
        target = proposal.target or CORE
        variant = proposal.variant or session.variant
        checkpoint_id = f"cp-{proposal.id}"
        self.checkpoint = self.snapshot()
        self.checkpoint_id = checkpoint_id
        self.checkpoint_proposal = proposal.id
        events = [
            ApplyEvent(
                "checkpoint.created",
                {"checkpoint_id": checkpoint_id, "session_id": session.session_id},
            ),
            ApplyEvent(
                "tool.call",
                {"tool": "session.exchange", "session_id": session.session_id, "target": target},
            ),
        ]
        bundle = self.bundle_for(proposal, session)
        # Drop forbidden material before it is stored. Policy already refused
        # those proposals; this keeps a partial copy from becoming a leak.
        for key in ("subscriber_id", "raw_key", "playback_url"):
            bundle.pop(key, None)
        self.partial[session.session_id] = bundle
        events.append(
            ApplyEvent(
                "tool.call",
                {"tool": "state.copy", "session_id": session.session_id, "target": target},
            )
        )
        self.handovers_this_tick += len(proposal.sessions)
        if session.session_id in ACK_FAILS:
            events.append(
                ApplyEvent(
                    "tool.result",
                    {
                        "tool": "target.ack",
                        "session_id": session.session_id,
                        "status": "failed",
                    },
                )
            )
            return events
        self._commit_handover(session, target, variant)
        events.append(
            ApplyEvent(
                "tool.call",
                {
                    "tool": "connection.rebind",
                    "session_id": session.session_id,
                    "connection_id": session.connection_id,
                },
            )
        )
        events.append(
            ApplyEvent(
                "tool.result",
                {
                    "tool": "target.ack",
                    "session_id": session.session_id,
                    "status": "success",
                },
            )
        )
        return events

    def _commit_handover(self, session: Session, target: str, variant: str) -> None:
        self.partial.pop(session.session_id, None)
        self.reservations.pop(session.session_id, None)
        self.bandwidth_holds.pop(session.session_id, None)
        session.home_node = target
        session.variant = variant
        if not session.connection_id.endswith("b"):
            session.connection_id = f"{session.connection_id}b"
        session.acked = True
        session.playback_sec = PLAYBACK
