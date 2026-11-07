"""Explicit subset validation, not a complete CDDL validator."""
import math
from datetime import datetime


class ContractError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise ContractError(message)


def stamp(value):
    require(isinstance(value, str), "timestamp must be text")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError("invalid timestamp") from exc
    require(parsed.tzinfo is not None, "timestamp requires timezone")


def validate_record(r, kind):
    common = ["schema_version", "session_id"]
    fields = {
        "event": ["event_id", "timestamp", "sequence", "actor", "phase", "event_type", "status"],
        "anomaly": ["anomaly_id", "detected_at", "detector", "baseline_id", "score", "score_direction", "candidate_event_ids"],
        "assertion": ["assertion_event_id", "timestamp", "tla_level", "assertion_id", "result", "evidence_event_ids"],
        "diagnosis": ["diagnosis_id", "created_at", "method", "responsible_actor_id", "root_cause_event_id", "terminal_event_id", "evidence_event_ids", "failure_chain"],
    }
    require(kind in fields and isinstance(r, dict), "unknown record kind")
    for f in common + fields[kind]:
        require(f in r, "missing " + f)
    require(r["schema_version"] == "1.0", "unsupported schema version")
    require(isinstance(r["session_id"], str) and bool(r["session_id"]), "invalid session id")
    stamp(r.get("timestamp", r.get("detected_at", r.get("created_at"))))
    if kind == "event":
        require(type(r["sequence"]) is int and r["sequence"] >= 0, "invalid sequence")
        require(r["phase"] in ("pre-execution", "execution", "post-execution"), "invalid phase")
        require(r["status"] in ("started", "ok", "error", "cancelled", "unknown"), "invalid status")
        require(isinstance(r["actor"], dict) and bool(r["actor"].get("id")), "missing actor id")
        require(r["actor"].get("kind") in ("human", "agent", "orchestrator", "model", "tool", "verifier", "environment", "other"), "invalid actor kind")
        require(isinstance(r["event_id"], str) and bool(r["event_id"]), "invalid event id")
        require(isinstance(r.get("parent_event_ids", []), list), "parents must be an array")
        require(all(isinstance(x, str) for x in r.get("parent_event_ids", [])), "parent ids must be text")
        require(isinstance(r.get("attributes", {}), dict), "attributes must be an object")
        action = r.get("action", {})
        for k in ("duration_ms", "token_input", "token_output"):
            if k in action:
                require(type(action[k]) is int and action[k] >= 0, "invalid " + k)
    elif kind == "anomaly":
        require(type(r["score"]) in (int, float) and math.isfinite(r["score"]), "invalid score")
        require(bool(r["candidate_event_ids"]), "empty candidates")
        require(r["score_direction"] in ("higher-is-more-anomalous", "lower-is-more-anomalous"), "invalid direction")
    elif kind == "assertion":
        require(r["result"] in ("pass", "approaching", "violation", "unknown"), "invalid assertion result")
    else:
        require(bool(r["evidence_event_ids"]) and bool(r["failure_chain"]), "empty diagnosis evidence")
        require(all(x["role"] in ("root-cause", "propagation", "exposure", "terminal") for x in r["failure_chain"]), "invalid causal role")


def validate_trace(events):
    require(bool(events), "empty trace")
    ids, sessions, sequences = set(), set(), {}
    for e in events:
        validate_record(e, "event")
        require(e["event_id"] not in ids, "duplicate event id")
        sessions.add(e["session_id"])
        actor = e["actor"]["id"]
        require(e["sequence"] > sequences.get(actor, -1), "non-monotonic producer sequence")
        sequences[actor] = e["sequence"]
        # This replay profile requires parent-before-child delivery.
        require(all(x in ids for x in e.get("parent_event_ids", [])), "missing or future parent")
        ids.add(e["event_id"])
    require(len(sessions) == 1, "mixed sessions")


def validate_diagnosis(d, events):
    validate_record(d, "diagnosis")
    index = {e["event_id"]: e for e in events}
    refs = [d["root_cause_event_id"], d["terminal_event_id"], *d["evidence_event_ids"]]
    refs += [x["event_id"] for x in d["failure_chain"]]
    require(all(x in index for x in refs), "diagnosis cites nonexistent evidence")
    require(all(index[x]["session_id"] == d["session_id"] for x in refs), "cross-session evidence")
    require(d["responsible_actor_id"] in {e["actor"]["id"] for e in events}, "unknown responsible actor")
    require(index[d["terminal_event_id"]]["event_type"] == "session.end", "invalid terminal event")
    require(index[d["terminal_event_id"]]["status"] == "error", "terminal is not a failure")
    for link in d["failure_chain"]:
        require(link["actor_id"] == index[link["event_id"]]["actor"]["id"], "incorrect evidence actor")
