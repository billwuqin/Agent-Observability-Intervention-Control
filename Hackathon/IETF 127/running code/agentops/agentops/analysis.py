"""Transparent rule baseline. Does not implement DuoTrace or RCTA models."""
from .contracts import validate_trace, validate_record, validate_diagnosis
from .telemetry import now

BASELINE = {"id": "demo-policy-v1", "call_latency_ms": 50, "max_attempts": 2}


class Detector:
    def __init__(self, baseline=None):
        self.baseline = dict(baseline or BASELINE)
        self.events, self.anomalies, self.assertions = [], [], []

    def consume(self, event):
        validate_trace(self.events + [event])
        self.events.append(event)
        attrs = event.get("attributes", {})
        requirement = next((e.get("attributes", {}).get("required_route") for e in self.events if e["event_type"] == "task.received"), None)
        tests = []
        if event["event_type"] in ("plan.created", "tool.call") and "route" in attrs:
            result = "unknown" if requirement is None else "pass" if attrs["route"] == requirement else "violation"
            tests.append(("route-intent", result, attrs["route"], requirement))
        if event["event_type"] == "recovery.attempt":
            attempt = attrs["attempt"]
            tests.append(("retry-budget", "violation" if attempt > self.baseline["max_attempts"] else "pass", attempt, self.baseline["max_attempts"]))
        duration = event.get("action", {}).get("duration_ms")
        if event["event_type"] in ("tool.result", "model.response") and duration is not None:
            limit = self.baseline["call_latency_ms"]
            result = "violation" if duration > limit else "approaching" if duration >= .8 * limit else "pass"
            tests.append(("call-latency", result, duration, limit))
        reasons = []
        for aid, result, measured, boundary in tests:
            record = {"schema_version": "1.0", "session_id": event["session_id"],
                      "assertion_event_id": f"{event['event_id']}:assert:{aid}", "timestamp": now(),
                      "tla_level": "demo-operational-policy", "assertion_id": aid, "result": result,
                      "evidence_event_ids": [event["event_id"]], "measured_value": measured, "boundary_value": boundary}
            validate_record(record, "assertion")
            self.assertions.append(record)
            if result == "violation":
                reasons.append(aid)
        if event["event_type"] in ("tool.result", "model.response") and event["status"] == "error":
            reasons.append("call-error")
        if event["event_type"] == "verification.result" and event["status"] == "error":
            reasons.append("verification-failure")
        if reasons:
            anomaly = {"schema_version": "1.0", "anomaly_id": event["event_id"] + ":anomaly", "session_id": event["session_id"],
                       "detected_at": now(), "detector": {"name": "explicit-rule-baseline", "version": "0.1.0"},
                       "baseline_id": self.baseline["id"], "score": len(reasons), "score_direction": "higher-is-more-anomalous",
                       "candidate_event_ids": [event["event_id"]], "recommended_action": "observe",
                       "extensions": {"rules": reasons, "observed_through_event_id": event["event_id"], "prefix_size": len(self.events)}}
            validate_record(anomaly, "anomaly")
            self.anomalies.append(anomaly)
        return self.anomalies[-1] if reasons else None


def diagnose(events, baseline=None):
    validate_trace(events)
    baseline = baseline or BASELINE
    terminal = next((e for e in reversed(events) if e["event_type"] == "session.end"), None)
    if terminal is None or terminal["status"] != "error":
        return {"status": "not-applicable", "reason": "No completed failed task"}
    by_id = {e["event_id"]: e for e in events}
    relevant, pending = set(), [terminal["event_id"]]
    while pending:
        eid = pending.pop()
        if eid not in relevant:
            relevant.add(eid)
            pending.extend(by_id[eid].get("parent_event_ids", []))
    task = next((e for e in events if e["event_type"] == "task.received"), None)
    required = task.get("attributes", {}).get("required_route") if task else None
    plans = {e["event_id"]: e for e in events if e["event_type"] == "plan.created"}
    handoffs = {e["event_id"]: e for e in events if e["event_type"] == "agent.delegated"}
    recovered = {ref for e in events if e["status"] == "ok" for ref in e.get("attributes", {}).get("resolves_event_ids", [])}
    root, evidence, rationale, category = None, [], "", ""
    # Compare executed instructions with task intent and recorded handoff.
    for call in events:
        if call["event_type"] != "tool.call" or required is None or call["event_id"] not in relevant:
            continue
        route = call.get("attributes", {}).get("route")
        if route is None or route == required:
            continue
        root, evidence = call, [task["event_id"], call["event_id"]]
        rationale, category = "Executed route violates the recorded task constraint.", "D1"
        for parent in call["parent_event_ids"]:
            handoff = handoffs.get(parent)
            if handoff and handoff.get("delegation", {}).get("to_actor") == call["actor"]["id"] and handoff.get("attributes", {}).get("route") == route:
                for pid in handoff["parent_event_ids"]:
                    plan = plans.get(pid)
                    if plan and plan.get("attributes", {}).get("route") == route:
                        root = plan
                        evidence += [plan["event_id"], handoff["event_id"]]
                        rationale, category = "Executor followed the recorded handoff. The earlier plan introduced the conflicting route.", "C1"
        break
    if root is None:
        root = next((e for e in events if e["event_id"] in relevant and e["event_type"] == "recovery.attempt" and e.get("attributes", {}).get("attempt", 0) > baseline["max_attempts"]), None)
        if root:
            evidence, rationale, category = [root["event_id"]], "Orchestrator exceeded the configured retry budget.", "D3"
    if root is None:
        root = next((e for e in events if e["event_id"] in relevant and e["event_type"] == "tool.result" and e["status"] == "error" and e["event_id"] not in recovered), None)
        if root:
            evidence = [root["event_id"], *root["parent_event_ids"]]
            rationale, category = "Recorded tool failure remained unresolved at task termination.", "X2"
    if root is None:
        return {"status": "abstain", "reason": "Insufficient supported evidence for this rule baseline", "terminal_event_id": terminal["event_id"]}
    chain = [{"event_id": root["event_id"], "actor_id": root["actor"]["id"], "role": "root-cause"}]
    # Structural descendant test avoids labeling unrelated branch events as propagation.
    descendants = {root["event_id"]}
    for e in events:
        if e["event_id"] == root["event_id"]:
            continue
        dependent = any(p in descendants for p in e["parent_event_ids"])
        if dependent:
            descendants.add(e["event_id"])
        role = "terminal" if e["event_id"] == terminal["event_id"] else "exposure" if dependent and e["event_type"] == "verification.result" and e["status"] == "error" else "propagation" if dependent and e["event_id"] in relevant and e["event_type"] in ("agent.delegated", "tool.call", "tool.result") else None
        if role:
            chain.append({"event_id": e["event_id"], "actor_id": e["actor"]["id"], "role": role})
    evidence = list(dict.fromkeys(evidence + [x["event_id"] for x in chain]))
    diagnosis = {"schema_version": "1.0", "diagnosis_id": terminal["session_id"] + ":diagnosis", "session_id": terminal["session_id"],
                 "created_at": now(), "method": {"name": "handoff-and-dependency-rule-baseline", "version": "0.1.0"},
                 "responsible_actor_id": root["actor"]["id"], "root_cause_event_id": root["event_id"],
                 "terminal_event_id": terminal["event_id"], "evidence_event_ids": evidence, "failure_chain": chain,
                 "category": category, "validation": "machine-validated", "extensions": {"rationale": rationale, "validation_scope": "record structure and evidence references only"}}
    validate_diagnosis(diagnosis, events)
    return {"status": "diagnosed", "record": diagnosis}


def intervention_request(anomalies, diagnosis):
    """Proposal-only ICON bridge. It cannot call, pause, cancel, or resume a runtime."""
    return {"schema_version": "demo-bridge-0.1", "requested_action": "human-review" if anomalies else "none",
            "execution_status": "not-executed", "requires_authorization": True,
            "anomaly_ids": [x["anomaly_id"] for x in anomalies],
            "diagnosis_id": diagnosis.get("record", {}).get("diagnosis_id"),
            "note": "Experimental local proposal, not an ICON control protocol or actuator"}
