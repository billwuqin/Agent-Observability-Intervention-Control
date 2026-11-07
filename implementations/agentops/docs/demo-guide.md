# Five-minute demonstration

[README](../README.md) · [Participant FAQ](faq.md)

## How to read the HTML viewer

### Summary and navigation

The top summary counts controlled scenarios, matching alarm expectations, correct attributions among failed tasks, and abstentions. “9/9 alarm expectations met” includes the clean case with no alarm. It is not a percentage of failed tasks detected early. “5/6 failed cases correctly attributed” retains the missing-evidence abstention in the denominator.

Click a scenario name to jump to its section. Its summary shows the diagnostic status, selected actor, root event ID and number of anomaly signals. The event table lists recorded events in replay order. The highlighted row is the selected root; an `error` status on a later row is not automatically the root.

### Example: planner_error and executor_error

In `planner_error`, the task requires route B. The planner selects A at `planner_error:e004`, delegates A, and the executor follows A. The later verifier failure exposes the defect; the planner event is the selected root.

In `executor_error`, the plan selects B but the executor's `tool.call` at `executor_error:e006` requests A. The attributor selects the executor. Open the two scenarios to show how recorded instructions and actions distinguish responsibility.

### Expandable evidence panels

| Panel | What to inspect | Interpretation |
|---|---|---|
| Anomalies and prefix boundary | `extensions.rules`, `observed_through_event_id`, `prefix_size`, candidate IDs | Why a rule fired and which records were available at that decision |
| Assertions | `assertion_id`, `result`, `measured_value`, `boundary_value` | Which application constraint or threshold passed, approached a limit, failed or was unknown |
| Diagnosis and evidence chain | `responsible_actor_id`, `root_cause_event_id`, `evidence_event_ids`, `failure_chain` | The selected cause and the original events supporting it |
| Runtime measurements | Task/model/tool duration lists, errors, retries, token counters and `token_source` | Durations measured on local simulated operations; token counts are synthetic |
| ICON intervention proposal (not executed) | `requested_action`, `requires_authorization`, `execution_status` | A review proposal with references, not an executed control action |

`machine-validated` in a diagnosis refers to record structure and evidence-reference checks. It is not independent validation of causal truth. The local `extensions.validation_scope` makes this explicit.

### Status vocabulary

- `diagnosed`: this rule baseline produced a supported record.
- `not-applicable`: there is no completed failed task for the retrospective diagnosis profile.
- `abstain`: the task failed but available evidence and supported rules do not justify a root selection.

Successful `recovered_error` and `slow_call` runs still contain operational anomalies. Their lack of a failed-task diagnosis is intentional.

## Suggested presentation sequence

1. Run the test suite and demo commands in the README. Open `artifacts/index.html`.
2. Show `clean`: the route intent is B, the plan and execution agree, and the verifier passes. Show measured task/model/tool duration and explicitly simulated token usage.
3. Show `planner_error`: intent B, planner chooses A, executor follows A. The root highlights the planner's original `plan.created` event. Expand the failure chain and evidence list.
4. Show `executor_error`: planner chooses B, executor calls the tool with A. The responsible actor changes to executor. This illustrates responsibility transfer rather than blaming the final verifier.
5. Show `recovered_error` and `slow_call`: both tasks succeed but operational events still require attention. Anomaly detection and task success are different dimensions.
6. Show `missing_evidence`: the attributor abstains rather than inventing an upstream root.
7. Expand the intervention proposal. It contains references, but execution status remains `not-executed`. Ask the ICON team which control interface and runtime owner should consume this output.

## Expected cases

| Case | Task | Expected alarm | Expected diagnosis |
|---|---|---|---|
| clean | success | no | not applicable |
| planner_error | failure | yes | planner / plan event |
| executor_error | failure | yes | executor / tool-call event |
| tool_error | failure | yes | route-tool / unresolved tool result |
| timeout | failure | yes | route-tool / timeout result |
| retry_exhausted | failure | yes | orchestrator / retry exceeding budget |
| recovered_error | success | yes | not applicable |
| slow_call | success | yes | not applicable |
| missing_evidence | failure | yes | abstain |

The retry case uses a declared operational policy: the earliest decision exceeding the retry budget is the attribution target. It does not assert that a tool outage is never a causal contributor.

## Suggested English explanation

“We implemented two prototype capabilities. The first exports agent execution records and measured local runtime durations. The second consumes these records to detect anomalies and attribute failures using explicit rules and recorded handoffs. The implementation validates selected data-model and processing requirements of the draft. We currently use simulated model and network operations, so these results establish functional behavior on controlled cases, not performance on real networks or a research benchmark. Our next integration step is to connect a real agent runtime and agree on the control interface with ICON.”
