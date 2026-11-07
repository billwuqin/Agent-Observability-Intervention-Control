# Participant FAQ

[README](../README.md) · [Demo walkthrough](demo-guide.md)

These answers describe prototype v0.1.0 and its mapping to draft revision -00. Proposed standardization work is distinguished from behavior already exercised by this implementation.

## 1. What has actually been implemented?

The local workflow has a simulated planner, executor, routing tool and verifier. Instrumentation produces normalized event records and measures local task/model/tool elapsed duration. A rule detector consumes events incrementally. A retrospective attributor compares task constraints, plans, handoffs, actions and results to select a supported actor/root pair or abstain. A local HTML report exposes the records and decisions.

The model, network state, tool faults and provider token counts are simulated. The durations are actual local measurements. The implementation does not reproduce DuoTrace's VAE or RCTA's LLM algorithm. The ICON bridge emits a review proposal and cannot execute control commands.

## 2. What are events.json, evidence.json and analysis.json?

| File | Structure | Meaning |
|---|---|---|
| `events.json` | Array of normalized events | What the instrumented workflow recorded, in replay order |
| `evidence.json` | Evidence-ID-to-payload object | Sanitized structured attributes associated with an event |
| `analysis.json` | Analysis result object | Metrics, anomalies, assertions, diagnosis, intervention proposal, analysis duration and a copy of events |

In `planner_error`, the diagnosis selects `planner_error:e004`. The corresponding event has type `plan.created`, actor `planner` and attribute `route: A`. Its evidence reference points to `planner_error:e004:evidence`, whose payload in `evidence.json` is `{"route": "A"}`. The task event records the required route B. Comparing these records explains the conflict.

In the current prototype, `evidence.json` duplicates the sanitized `attributes` already present in events. The detector and attributor read those inline attributes; they do not dereference a separate evidence service. This demonstrates the reference-to-payload relationship, not a completed remote evidence-store implementation. The evidence hash covers the sanitized attribute payload, not the full event or the entire trace. Hash verification and access-controlled retrieval are future work.

The `demo` command adds `case` and `ground_truth` to the analysis result **after** `analyze(events)` returns. They are evaluator metadata. The `replay` command consumes only an event array and does not attach these gold labels. Never feed the entire demo `analysis.json` into a diagnostic model as if it were unlabelled input.

These three filenames are a packaging choice for this demonstration. The draft describes record models and their semantics, not a mandatory three-file layout.

## 3. What is an event?

An event is one recorded action, observation or lifecycle transition. It does not necessarily represent an anomaly or a network incident.

| Event type | Example |
|---|---|
| `task.received` | A user asks for backup route B |
| `plan.created` | A planner selects a route |
| `agent.delegated` | A planner sends instructions to an executor |
| `model.request` / `model.response` | A model request and its response |
| `tool.call` / `tool.result` | A tool invocation and its result |
| `verification.result` | A verifier reports a check outcome |
| `session.end` | The task completes or fails |

The event envelope identifies the session, event, actor, timestamp, producer-local sequence, phase, type and status. Optional fields describe action measurements, parents and evidence. A logical action may produce more than one event: a tool invocation and its result are separate records. Event count and logical-step count are therefore not automatically equivalent across implementations.

## 4. What is the visible-prefix boundary?

The prefix boundary identifies the last event available to the detector when it issues a decision. In the planner-error case, its first anomaly contains:

```json
{
  "observed_through_event_id": "planner_error:e004",
  "prefix_size": 5
}
```

At this point it has consumed e000, e001, e002, e003 and e004. The later delegation, tool execution, verification failure and terminal event are outside that decision's input. The earlier task and the newly observed conflicting plan are sufficient for this particular rule to signal an anomaly.

These two fields live under the anomaly record's `extensions`. They are prototype conventions intended to support discussion; the -00 draft does not define them as standard fields. `prefix_size` counts consumed records globally in this replay. It is different from `sequence`, which counts events from a single actor.

`detected_at` is the wall-clock time when the detector emits its record. During replay it is the replay time, not the historical source event time. It cannot by itself prove real-time detection lead time.

There are also policy boundaries: for example, a 50 ms latency threshold. Those are limits on acceptable behavior. The prefix boundary is instead a limit on **which evidence was available**.

## 5. Does the detector output a boundary for every event? Is this live monitoring?

`consume(event)` updates the detector's visible prefix on every call. It emits an anomaly with a prefix boundary only when an anomaly rule fires. It returns `None` otherwise. Applicable checks can still produce pass, approaching or unknown assertion records.

The demo first generates the whole execution, then replays it one event at a time. This tests prefix access and prevents the detector from using future records. The offline attributor intentionally receives the completed trace. A live integration still needs event delivery, timing and buffering policies, and an actual runtime connection. No live pause or rollback is exercised here.

## 6. Are all components open source?

The external runtime consists of CPython and its standard library, which are open source. There are no third-party runtime packages and no proprietary model service calls. Optional local serving uses `http.server`.

This contribution follows the ICON repository's existing [public-domain declaration](../../../.github/LICENSE.md). No separate module license is introduced. CPython and external tools retain their own licensing terms. Code availability does not imply that the prototype has achieved production readiness or interoperability certification.

OpenTelemetry, LangChain, Prometheus, Grafana, DuoTrace and RCTA are not integrated dependencies of this version. The last two inform the research context, but their algorithms are not implemented by this rule baseline.

## 7. How should I read the HTML page?

Start with the scenario navigation, then inspect one case's summary, event table and expandable details. The highlighted event is the selected root. The five expandable sections expose anomaly decisions and prefix boundaries, assertions, diagnosis/evidence, runtime measurements, and the intervention proposal. The [walkthrough](demo-guide.md) explains the fields and provides a five-minute demonstration sequence.

A successful task can still have an operational anomaly. `recovered_error` succeeds after a tool error; `slow_call` succeeds despite violating the latency threshold. `not-applicable` means there is no completed failed task for the retrospective diagnosis profile. `abstain` means the task failed but this attributor cannot support a root-cause conclusion with its rules and available evidence.

## 8. What value do anomaly detection and root-cause localization add for agents?

Detection can reveal constraint violations, excessive retries, call failures or slow execution before a task terminates. In a live system, that can support an operator's decision to pause, constrain or review execution. Detection quality still depends on useful baselines, observable evidence and acceptable false-alarm rates.

Attribution supports targeted debugging and recovery planning. If the planner requests A despite an intent of B, and the executor follows A, the planner's instruction is a candidate origin. If the planner requests B but the executor issues A, the executor introduced the deviation. Blaming the verifier that later reports failure would obscure that distinction.

Neither a high anomaly score nor temporal precedence establishes causality. Multiple defects, missing logs and unsuccessful recovery can make responsibility ambiguous. The current rules cover specific controlled cases; more general methods need uncertainty handling and independently labelled evaluation data.

## 9. Why include detection and diagnosis in an observability standard?

They establish concrete consumers of observability data. Supporting diagnosis requires evidence that generic success/failure counters omit: stable event IDs, actor/role identifiers, handoff instructions, dependency links, original payload references and verifier outcomes.

The proposed interoperability boundary includes:

- How producers identify and correlate events and evidence.
- How detectors express an anomaly, its baseline, score semantics and candidate events.
- How application assertions express boundary evaluations.
- How diagnosers report a responsible actor, root event, source evidence and causal-chain roles.
- How downstream consumers recognize the limits and provenance of those results.

Different teams can choose different detectors or attribution algorithms while consuming and producing comparable records. The standard should not require this demo's route rules, a specific VAE/LLM, a universal threshold, or automatic destructive recovery.

Observability and diagnosis outputs also need a clear relationship with existing tracing systems and network-management use cases. The prototype currently demonstrates the data boundary locally; it does not establish that a new transport is necessary or that every field belongs in an IETF standard.

## 10. What has this demo validated for standardization?

It shows that selected draft fields can represent controlled executions, that consumers can use IDs and dependencies to recover evidence, and that structurally valid analysis outputs can describe these cases. It also provides negative-input and prefix-isolation test cases.

The [draft mapping](draft-mapping.md) records the exercised requirements and limits. Single-implementation functional checks do not demonstrate independent cross-vendor interoperability, complete draft conformance, causal correctness in general, or production readiness.

Useful feedback for the next draft revision includes:

1. Whether and how to standardize an observation boundary for online decisions, including asynchronous delivery.
2. How to represent unavailable evidence, unresolved diagnoses and revised conclusions. The demo's `abstain` wrapper is local, not a standard diagnosis record.
3. Whether `actor.id`, workflow role and emitted-event ownership need distinct semantics for responsibility attribution.
4. How to validate evidence hashes, schema extensions and references across trust domains.
5. How to map the records onto an existing telemetry encoding and test them with independently implemented producers and consumers.

## 11. Is this a benchmark of network-management agent capability?

The demo exercises diagnosis of an agent's own execution. A network-task benchmark asks whether an agent configured, diagnosed or optimized a network correctly. AgentOps evaluation asks whether an operational method detected and attributed a failure in that agent system. The same trajectory can support both evaluations with separate targets and scores.

In the recorded run, 28 automated tests pass and all nine scenario-level alarm expectations match. Six tasks fail: five receive the expected actor/root pair and one abstains. The full failed-case denominator remains six. The rules and fixtures were developed together, so these are functional checks, not held-out accuracy or research benchmark results.

## 12. Can the output trigger ICON intervention?

It can provide evidence for an intervention decision. The current bridge emits `requested_action: human-review` when anomaly records exist, with `requires_authorization: true` and `execution_status: not-executed`. It does not implement an ICON protocol or connect to control hooks.

An urgent pause in a future integration need not wait for complete root-cause attribution. The runtime and policy owner must define action authorization, execution, acknowledgements and recovery behavior. H1 concerns the records, H2 their decision-support use, and H3 ownership of actual runtime control instrumentation.

## Suggested short answer in a standards discussion

“This prototype provides running code and reproducible test cases for the proposed observability records. Detection and diagnosis show which evidence the records need to carry and how downstream systems can use it. We have exercised selected requirements in a controlled implementation; independent interoperability and live control integration remain future work.”
