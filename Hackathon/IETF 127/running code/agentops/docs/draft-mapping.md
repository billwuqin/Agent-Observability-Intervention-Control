# Implementation and draft validation map

Mapping to `draft-pei-opsawg-agentops-observability-00`. **Exercised subset** means the local implementation and automated cases demonstrate the listed behavior. It does not mean every normative requirement in that section has been satisfied.

For participant questions about the purpose and limits of this validation, see the [FAQ](faq.md#9-why-include-detection-and-diagnosis-in-an-observability-standard).

| Draft module | Implemented behavior | Validation evidence | Limit |
|---|---|---|---|
| §3 architecture | Event producer, collector-like local list, detector, attribution roles | Nine workflow runs plus JSON replay | In-process, no distributed deployment |
| §4 event model | Required envelope, actor roles, timestamps, per-actor sequence, trace/span IDs, dependencies, delegation, duration and token usage | Contract validation on all events; duplicate/parent/session/sequence/version negative tests | No full CDDL validation or OTLP exporter |
| §4.4 evidence | Original event IDs, evidence references and content hashes, provenance | Diagnosis reference checks, JSON roundtrip | Synthetic content, not access-controlled external storage |
| §5.1 detection | Prefix-only explicit baseline rules using task, plan, action and result evidence | No-future-reference and prefix-invariance tests | Semantic checks are structured field comparisons, not natural-language understanding |
| §5.2 anomaly | Detector, baseline, timestamp, score direction, candidate event IDs | Alarm expectations across nine scenarios | No calibrated probability/confidence or learned anomaly model |
| §5.3 assertion | Intent, retry and latency policy assertions with pass/approaching/violation/unknown states | Scenario assertions and serialized results | App-defined demo TLA, not a universal trust scale |
| §6 attribution | Actor/root output, handoff comparison, dependency chain, evidence resolution and abstention | Planner vs executor tests; tool/timeout/retry tests; missing-evidence case | Restricted rule baseline, not general causal proof |
| §7 benchmark boundary | Task success separate from operational anomaly and diagnosis result | Successful recovered/slow scenarios still expose anomalies | Fixture checks, not network-agent capability or LongRCA benchmark scores |
| §8 processing | Stable IDs, producer-local sequence, unknown event preservation, version check | Input integrity and extension tests | No sampling/retention policy, clock quality or out-of-order processing |
| §9 privacy | Known sensitive-key redaction, exception text omission | Redaction and exception tests | Free-text and cross-domain privacy not fully implemented |
| §10 security | Reject invalid references, escape viewer content, proposal-only control bridge | Evidence forgery, HTML and non-execution tests | No TLS/authentication/tamper-evident storage or production access control |

## ICON alignment

The prototype provides concrete artifacts for execution trajectory capture, agent runtime measurements and accountability evidence (related to ICON OBS-1, OBS-3 and OBS-4). It does not capture hidden model reasoning and does not implement the ICON control/intervention plane. `intervention_request()` emits a local experimental proposal with `execution_status: not-executed`.

H1: implemented telemetry records and measurements are available in `artifacts/*/events.json`.

H2: anomalies and diagnoses can support an intervention decision; the bridge demonstrates the data boundary only.

H3: actual pause/resume/cancel/checkpoint hooks still require an agent-runtime owner and an agreed control interface.

## Standardization feedback from the implementation

The implementation makes the data-model requirements reviewable through concrete event and result examples. It also exposes unresolved interface choices:

| Topic | Current prototype choice | Candidate standards discussion |
|---|---|---|
| Detection observation boundary | Local `extensions.observed_through_event_id` and `prefix_size` on alarms | A portable boundary or watermark with defined behavior for concurrent and delayed events |
| Missing evidence / unresolved diagnosis | Local `status: abstain` wrapper outside the draft diagnosis record | Shared status semantics, evidence availability and revision/supersession rules |
| Actor and role identity | Scenario actor ID and role are the same string | Distinguish instance, role, emitter and attributed responsibility |
| Evidence payload resolution | Sanitized attributes duplicated inline and in `evidence.json` | Access-controlled retrieval, hash verification and cross-domain references |
| Schema extensions | The subset validator accepts local `extensions` | Versioned extension rules and full schema validation |
| Interoperability | One in-process producer/consumer implementation | Independently built producers and consumers using a common encoding |

These are proposed discussion items, not claims that the -00 draft already standardizes the prototype conventions. Detection and attribution methods should remain replaceable; the exchange records and evidence semantics are the relevant standardization boundary.
