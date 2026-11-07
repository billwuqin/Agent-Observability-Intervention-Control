import hashlib
import json
import math
import time
import uuid
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone

from .contracts import validate_record


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


SENSITIVE = {"password", "authorization", "api_key", "access_token", "secret"}


def sanitize(value):
    """Key-based redaction only; free text still needs a deployment-specific policy."""
    if isinstance(value, dict):
        return {k: "[REDACTED]" if k.lower() in SENSITIVE else sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    return value


class Recorder:
    def __init__(self, session_id=None):
        self.session_id = session_id or "run-" + uuid.uuid4().hex[:12]
        self.trace_id = uuid.uuid4().hex
        self.events, self.evidence = [], {}
        self.sequences = defaultdict(int)
        self.started = time.perf_counter_ns()

    def emit(self, actor, event_type, status="ok", *, kind="agent", parents=(), attributes=None, action=None, phase="execution", delegation=None):
        self.sequences[actor] += 1
        eid = f"{self.session_id}:e{len(self.events):03d}"
        attrs = sanitize(attributes or {})
        payload = json.dumps(attrs, sort_keys=True, ensure_ascii=False).encode()
        digest = "sha256:" + hashlib.sha256(payload).hexdigest()
        ref = {"id": eid + ":evidence", "hash": digest, "media_type": "application/json", "sensitivity": "internal", "provenance": "observed"}
        self.evidence[ref["id"]] = attrs
        event = {"schema_version": "1.0", "event_id": eid, "session_id": self.session_id,
                 "timestamp": now(), "sequence": self.sequences[actor], "trace_id": self.trace_id,
                 "span_id": uuid.uuid4().hex[:16], "actor": {"id": actor, "kind": kind, "role": actor},
                 "phase": phase, "event_type": event_type, "status": status,
                 "parent_event_ids": list(parents), "attributes": attrs, "evidence": [ref]}
        if action is not None:
            event["action"] = action
        if delegation is not None:
            event["delegation"] = delegation
        validate_record(event, "event")
        self.events.append(event)
        return event

    @contextmanager
    def call(self, actor, call_kind, name, *, parents=(), attributes=None, kind="agent"):
        begin_type, end_type = ("model.request", "model.response") if call_kind == "model" else ("tool.call", "tool.result")
        begin = self.emit(actor, begin_type, "started", kind=kind, parents=parents,
                          action={"kind": call_kind, "name": name}, attributes=attributes)
        ctx = {"start": begin, "attributes": {}, "usage": {}}
        start = time.perf_counter_ns()
        status = "ok"
        try:
            yield ctx
        except Exception as exc:
            status = "error"
            ctx["attributes"]["error_type"] = type(exc).__name__
            # Do not serialize arbitrary exception text, which can contain secrets.
            raise
        finally:
            duration = math.ceil((time.perf_counter_ns() - start) / 1_000_000)
            action = {"kind": call_kind, "name": name, "duration_ms": duration, **ctx["usage"]}
            ctx["end"] = self.emit(actor, end_type, status, kind=kind,
                                    parents=[begin["event_id"]], attributes=ctx["attributes"], action=action)

    def end(self, failed, parents=()):
        return self.emit("orchestrator", "session.end", "error" if failed else "ok", kind="orchestrator",
                         parents=parents, phase="post-execution", action={"kind": "task", "name": "route-change",
                         "duration_ms": math.ceil((time.perf_counter_ns() - self.started) / 1_000_000)})


def metrics(events):
    durations = defaultdict(list)
    counts = defaultdict(int)
    for e in events:
        a = e.get("action", {})
        if "duration_ms" in a:
            durations[a["kind"]].append(a["duration_ms"])
        if e["status"] == "error" and e["event_type"] in ("model.response", "tool.result"):
            counts["call_errors"] += 1
            counts["timeouts"] += int(e.get("attributes", {}).get("error_type") == "TimeoutError")
        counts["retries"] += int(e["event_type"] == "recovery.attempt")
        counts["token_input"] += a.get("token_input", 0)
        counts["token_output"] += a.get("token_output", 0)
    return {"duration_ms": dict(durations), "counts": dict(counts),
            "measurement": "perf_counter_ns elapsed duration, rounded up to ms",
            "token_source": "simulated provider usage, not measured LLM tokens"}
