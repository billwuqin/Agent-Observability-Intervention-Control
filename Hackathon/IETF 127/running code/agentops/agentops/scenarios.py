"""Instrumented local routing workflow with a simulated model and network tool."""
import time
from .telemetry import Recorder

CASES = ("clean", "planner_error", "executor_error", "tool_error", "timeout", "retry_exhausted", "recovered_error", "slow_call", "missing_evidence")


def run_scenario(case):
    if case not in CASES:
        raise ValueError("unknown scenario")
    r = Recorder(case)
    start = r.emit("orchestrator", "session.start", kind="orchestrator", phase="pre-execution")
    task = r.emit("user", "task.received", kind="human", parents=[start["event_id"]], phase="pre-execution",
                  attributes={"intent": "Use backup path B", **({} if case == "missing_evidence" else {"required_route": "B"})})
    with r.call("planner", "model", "simulated-planner", parents=[task["event_id"]]) as c:
        time.sleep(.001)
        c["usage"] = {"token_input": 64, "token_output": 24}
        c["attributes"] = {"provider": "local-simulation", "usage_source": "synthetic"}
    route = "A" if case == "planner_error" else "B"
    plan = r.emit("planner", "plan.created", parents=[c["end"]["event_id"]], attributes={"route": route})
    handoff = r.emit("planner", "agent.delegated", parents=[plan["event_id"]], attributes={"route": route},
                     delegation={"from_actor": "planner", "to_actor": "executor", "instruction_ref": plan["evidence"][0]})
    root = plan if case == "planner_error" else None
    if case in ("executor_error", "missing_evidence"):
        route = "A"
    attempts = 3 if case == "retry_exhausted" else 2 if case == "recovered_error" else 1
    last = handoff
    error_ids = []
    for attempt in range(1, attempts + 1):
        if attempt > 1:
            last = r.emit("orchestrator", "recovery.attempt", kind="orchestrator", parents=[last["event_id"]], attributes={"attempt": attempt})
            if case == "retry_exhausted" and attempt == 3:
                root = last
        # Explicit tool.call belongs to executor. Result belongs to tool through a separate measured adapter.
        call = r.emit("executor", "tool.call", "started", parents=[last["event_id"]],
                      action={"kind": "tool", "name": "simulated-route-api"}, attributes={"route": route, "attempt": attempt})
        if case == "executor_error":
            root = call
        begin = time.perf_counter_ns()
        error = case in ("tool_error", "timeout", "retry_exhausted") or (case == "recovered_error" and attempt == 1)
        time.sleep(.08 if case == "slow_call" else .001)
        import math
        attrs = {"route": route, "attempt": attempt, "simulated": True}
        if error:
            attrs["error_type"] = "TimeoutError" if case == "timeout" else "ConnectionError"
        elif error_ids:
            attrs["resolves_event_ids"] = list(error_ids)
        last = r.emit("route-tool", "tool.result", "error" if error else "ok", kind="tool", parents=[call["event_id"]],
                      action={"kind": "tool", "name": "simulated-route-api", "duration_ms": math.ceil((time.perf_counter_ns()-begin)/1_000_000)}, attributes=attrs)
        if error:
            error_ids.append(last["event_id"])
        if case in ("tool_error", "timeout"):
            root = last
    failed = case in ("planner_error", "executor_error", "tool_error", "timeout", "retry_exhausted", "missing_evidence")
    verification = r.emit("verifier", "verification.result", "error" if failed else "ok", kind="verifier", parents=[last["event_id"]],
                          attributes={"expected": "B", "observed": route, "test": "simulated-connectivity"})
    r.end(failed, parents=[verification["event_id"]])
    # Labels are evaluator-owned. Never passed to a detector or attribution function.
    truth = {"case": case, "expected_alarm": case != "clean", "task_failed": failed,
             "root_event_id": root["event_id"] if root else None,
             "responsible_actor": root["actor"]["id"] if root else None,
             "expect_abstention": case == "missing_evidence"}
    return r, truth
