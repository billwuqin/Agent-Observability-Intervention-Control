"""The frozen ledger from the hackathon plan, Section 2.5."""

from __future__ import annotations

from dataclasses import dataclass

from world import CORE, EDGE, Proposal


@dataclass
class Operator:
    id: str
    tick: int
    command: str
    target: str = ""
    plan: str = ""


def home(session_id: str, node: str, connection: str, variant: str) -> tuple:
    return (session_id, node, connection, variant, 120)


def steps() -> list:
    return [
        Proposal("D1", 0, "request_compute", ["s1"], EDGE, "HD"),
        Proposal("D2", 0, "request_compute", ["s2"], EDGE, "HD"),
        Proposal("D3", 1, "request_compute", ["s3"], EDGE, "HD"),
        Proposal("D4", 1, "request_compute", ["s4"], EDGE, "HD"),
        Proposal("D5", 2, "set_variant", ["s1"], variant="4K"),
        Proposal("D6", 2, "set_variant", ["s2"], variant="4K"),
        Proposal("D7", 3, "request_compute", ["s1"], CORE, "4K"),
        Proposal("D8", 3, "request_bandwidth", ["s1"], mbps=15),
        Proposal("D9", 3, "handover", ["s1"], CORE, "4K"),
        Proposal("D10", 3, "request_compute", ["s2"], CORE, "4K"),
        Proposal("D11", 3, "handover", ["s2"], CORE, "4K"),
        Operator("H1", 3, "approve", target="D11"),
        Proposal("D12", 3, "handover", ["s2"], CORE, "4K"),
        Proposal("D13", 4, "handover", ["s3", "s4", "s1"], CORE, "HD"),
        Proposal("D14", 4, "handover", ["s3"], "node-unknown", "HD"),
        Proposal(
            "D15",
            4,
            "handover",
            ["s4"],
            CORE,
            "HD",
            bundle_extra={"subscriber_id": "user-1001"},
        ),
        Proposal("D16", 5, "handover", ["s3"], CORE, "HD"),
        Proposal("D17", 5, "release_source", ["s3"]),
        Proposal("D18", 5, "release_source", ["s3"]),
        Operator("I1", 5, "pause"),
        Proposal("D19", 5, "handover", ["s4"], CORE, "HD"),
        Operator("I2", 5, "rollback", target="D16"),
        Operator("I3", 6, "correct", plan="handover s4 only"),
        Proposal("D20", 6, "handover", ["s4"], CORE, "HD"),
    ]


# decision, reason, mutated
DECISION = {
    "D1": ("allow", "WITHIN_CAPACITY", True),
    "D2": ("allow", "WITHIN_CAPACITY", True),
    "D3": ("allow", "WITHIN_CAPACITY", True),
    "D4": ("allow", "WITHIN_CAPACITY", True),
    "D5": ("refuse", "OVER_CAPACITY", False),
    "D6": ("refuse", "OVER_CAPACITY", False),
    "D7": ("allow", "WITHIN_CAPACITY", True),
    "D8": ("allow", "WITHIN_BUDGET", True),
    "D9": ("allow", "HANDOVER_ALLOWED", True),
    "D10": ("allow", "WITHIN_CAPACITY", True),
    "D11": ("needs_approval", "NEEDS_HUMAN", False),
    "D12": ("allow", "HANDOVER_ALLOWED", True),
    "D13": ("refuse", "BLAST_RADIUS", False),
    "D14": ("refuse", "TARGET_NOT_ALLOWED", False),
    "D15": ("refuse", "SECRET_IN_BUNDLE", False),
    "D16": ("allow", "HANDOVER_ALLOWED", True),
    "D17": ("refuse", "RELEASE_BEFORE_ACK", False),
    "D18": ("refuse", "RELEASE_BEFORE_ACK", False),
    "D19": ("paused", "PAUSED", False),
    "D20": ("allow", "HANDOVER_ALLOWED", True),
}


def _placed(*rows: tuple) -> tuple:
    return tuple(rows)


FOUR_HD = _placed(
    home("s1", EDGE, "c1", "HD"),
    home("s2", EDGE, "c2", "HD"),
    home("s3", EDGE, "c3", "HD"),
    home("s4", EDGE, "c4", "HD"),
)
AFTER_S1 = _placed(
    home("s1", CORE, "c1b", "4K"),
    home("s2", EDGE, "c2", "HD"),
    home("s3", EDGE, "c3", "HD"),
    home("s4", EDGE, "c4", "HD"),
)
AFTER_S2 = _placed(
    home("s1", CORE, "c1b", "4K"),
    home("s2", CORE, "c2b", "4K"),
    home("s3", EDGE, "c3", "HD"),
    home("s4", EDGE, "c4", "HD"),
)
FINAL = _placed(
    home("s1", CORE, "c1b", "4K"),
    home("s2", CORE, "c2b", "4K"),
    home("s3", EDGE, "c3", "HD"),
    home("s4", CORE, "c4b", "HD"),
)

# edge, core, reserved, path, paused, grant, partial, homes
AFTER = {
    "D1": (2, 0, 0, 0, False, False, (), _placed(home("s1", EDGE, "c1", "HD"))),
    "D2": (4, 0, 0, 0, False, False, (), _placed(home("s1", EDGE, "c1", "HD"), home("s2", EDGE, "c2", "HD"))),
    "D3": (6, 0, 0, 0, False, False, (), _placed(home("s1", EDGE, "c1", "HD"), home("s2", EDGE, "c2", "HD"), home("s3", EDGE, "c3", "HD"))),
    "D4": (8, 0, 0, 0, False, False, (), FOUR_HD),
    "D5": (8, 0, 0, 0, False, False, (), FOUR_HD),
    "D6": (8, 0, 0, 0, False, False, (), FOUR_HD),
    "D7": (8, 0, 6, 0, False, False, (), FOUR_HD),
    "D8": (8, 0, 6, 15, False, False, (), FOUR_HD),
    "D9": (6, 6, 6, 15, False, False, (), AFTER_S1),
    "D10": (6, 6, 12, 15, False, False, (), AFTER_S1),
    "D11": (6, 6, 12, 15, False, False, (), AFTER_S1),
    "H1": (6, 6, 12, 15, False, True, (), AFTER_S1),
    "D12": (4, 12, 12, 30, False, True, (), AFTER_S2),
    "D13": (4, 12, 12, 30, False, True, (), AFTER_S2),
    "D14": (4, 12, 12, 30, False, True, (), AFTER_S2),
    "D15": (4, 12, 12, 30, False, True, (), AFTER_S2),
    "D16": (4, 12, 12, 35, False, True, ("s3",), AFTER_S2),
    "D17": (4, 12, 12, 35, False, True, ("s3",), AFTER_S2),
    "D18": (4, 12, 12, 35, False, True, ("s3",), AFTER_S2),
    "I1": (4, 12, 12, 35, True, True, ("s3",), AFTER_S2),
    "D19": (4, 12, 12, 35, True, True, ("s3",), AFTER_S2),
    "I2": (4, 12, 12, 30, True, True, (), AFTER_S2),
    "I3": (4, 12, 12, 30, False, True, (), AFTER_S2),
    "D20": (2, 14, 14, 35, False, True, (), FINAL),
}
