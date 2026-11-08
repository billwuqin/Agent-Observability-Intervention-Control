# AgentOps observability and failure diagnosis prototype

Runnable support for two IETF 127 ICON Hackathon work items:

1. Agent runtime measurements and a common execution trajectory representation.
2. Anomaly detection and failure attribution with source evidence.

This is a **new controlled prototype**, not a pre-existing deployment. It uses a simulated route-change workflow and transparent rules. It does not implement DuoTrace's VAE or RCTA's LLM pipeline. Its intervention output is a proposal only; there is no live ICON actuator.

## Reading and presenting the demo

- [FAQ](docs/faq.md): events, prefix boundaries, output files, licensing, standards value and limits.
- [Viewer walkthrough](docs/demo-guide.md): how to read each part of the HTML page and demonstrate the cases.
- [Draft validation map](docs/draft-mapping.md): implemented subsets, evidence and outstanding work.

The prototype provides running code and test cases to refine the draft's data model and identify interoperability gaps. Its primary standards contribution is the evidence representation and the semantics of detection/diagnosis outputs. The rule baseline demonstrates a consumer of those records; it is not a proposed mandatory diagnostic algorithm.

## Quick start

Python 3.10+ is required. There are no third-party runtime dependencies, credentials, containers, or network services.

```sh
python3 -m unittest discover -s tests -v
python3 -m agentops demo --out artifacts
python3 -m http.server 8000 --bind 127.0.0.1 --directory artifacts
```

Open `http://127.0.0.1:8000` to inspect results. The self-contained `artifacts/index.html` also works as a local file.

Each scenario folder contains three files:

| Output | Contents | Use |
|---|---|---|
| `events.json` | Normalized execution events with actors, timing, dependencies, attributes and evidence references | Input to detection and attribution |
| `evidence.json` | A map from evidence IDs to sanitized event attributes | Inspect the payload referred to by an event |
| `analysis.json` | Events plus metrics, anomalies, assertions, diagnosis and intervention proposal | Inspect the resulting analysis and its evidence |

A recorded synthetic run is included under [examples/results](examples/results/). Open [its HTML report](examples/results/index.html) locally, or run the commands above to regenerate results under `artifacts/`.

The demo adds `case` and evaluator-owned `ground_truth` to `analysis.json` after analysis. Neither field is supplied to the detector or attributor. In this version, evidence payloads also appear inline in event attributes, so the replay command needs only `events.json`. The file names and packaging are demo conventions, not requirements of the draft.

Replay normalized event records independently from scenario labels:

```sh
python3 -m agentops replay artifacts/planner_error/events.json --out replay-result.json
```

Run commands from this repository root. Package installation is optional (`python3 -m pip install -e .`); it may fetch setuptools and is not needed for the commands above.

## Architecture

```text
Simulated planner / executor / tool / verifier
                     |
             Recorder instrumentation
                     |
             Normalized event JSON
                /             \
     Prefix-only detector     Offline attributor
     anomalies + assertions   actor + root + evidence
                \             /
           Proposal-only ICON bridge
                     |
            JSON artifacts + HTML report
```

`Recorder.call()` instruments synchronous Python callables via a context manager. It measures elapsed time with a monotonic clock, records model/tool boundaries, and emits error events even when a call raises. `Recorder.emit()` records plan, delegation, recovery, and verification events.

`Detector.consume(event)` receives one event at a time. It has no access to future events or evaluator-owned gold labels. The demo streams a completed trace through this API to exercise **prefix replay**. It does not measure live intervention timing or distributed collector latency.

An event is one recorded action or observation, such as a plan, a tool invocation or a tool result. The prefix boundary records how far the detector has read: when it emits an anomaly at `planner_error:e004`, `observed_through_event_id` is `planner_error:e004` and `prefix_size` is 5 (events e000 through e004). These are prototype extension fields, not standardized draft fields. Calls without a matching anomaly rule return `None`; the prototype does not emit a boundary record for every input event. See the [FAQ](docs/faq.md) for the distinction between this read boundary, event time and a policy threshold.

`diagnose(events)` performs retrospective attribution using task constraints, original plan/handoff records, action parameters, tool outcomes and the terminal outcome. It distinguishes faithful execution of a faulty plan from an executor's independent deviation. Unknown failure modes abstain. The rules are scenario-specific and do not establish general causal inference.

## Files

| File | Responsibility |
|---|---|
| `agentops/telemetry.py` | Event envelope, timings, usage counters, evidence hashes, key-based redaction |
| `agentops/contracts.py` | Explicit subset validation and evidence-reference checks |
| `agentops/analysis.py` | Detector, attributor and non-executing intervention proposal |
| `agentops/scenarios.py` | Nine controlled network-agent workflows and evaluator labels |
| `agentops/cli.py` | Demo execution, replay and result export |
| `agentops/ui.py` | Escaped, self-contained HTML results viewer |
| `tests/test_prototype.py` | Regression, invalid-input, prefix-isolation and safety tests |
| `docs/draft-mapping.md` | Draft sections, evidence and explicit limits |
| `docs/demo-guide.md` | Presentation sequence and expected behavior |
| `docs/faq.md` | Participant questions and standards discussion |

## Development environment and components

Verified locally with CPython 3.12.14 on macOS 26.5.2, arm64. Python 3.10+ compatibility is a declared target, not a tested OS/version matrix.

Open-source components are CPython and its standard library (`time`, `json`, `hashlib`, `uuid`, `datetime`, `unittest`, `http.server`). No LangChain, OpenTelemetry SDK, Prometheus, Grafana, external LLM or network emulator is integrated in this version. No upstream code is vendored. The new features are implemented in the modules above. Third-party projects retain their own licenses.

### Licensing status

The external runtime dependencies are open source. This contribution follows the repository's existing [public-domain declaration](../../../../.github/LICENSE.md). No separate module license is introduced. CPython and other external tools retain their own licensing terms.

## Measurements and interpretation

- Model-call, tool-call and whole-task durations are actual elapsed durations of local simulated operations, rounded up to milliseconds.
- Model token usage is supplied synthetic provider metadata (64 input / 24 output per case), not tokens measured from an LLM.
- Errors, timeouts and retries are actual emitted records of deliberately configured simulated outcomes. The timeout scenario injects `TimeoutError`; it does not implement a real network deadline.
- `call_latency_ms=50` and `max_attempts=2` are explicit demo policy values, not learned baselines or calibrated production limits.
- Successful tasks can still contain operational anomalies. `slow_call` succeeds with a latency violation; `recovered_error` succeeds after a tool error. Task success is reported separately from anomaly detection.
- Five of six failed scenarios have supported actor/root labels and receive correct rule-based diagnoses in the recorded run. One missing-evidence failure abstains. The full failed-case denominator is six, not five.
- This is functional validation on fixtures designed with the rules, not a held-out benchmark, an early-warning accuracy claim, or a reproduction of paper results.

## Safety and limits

The demo never changes a device, contacts an LLM service, or executes intervention commands. Serve locally on `127.0.0.1`. Event contents are untrusted and HTML-escaped. Key-based redaction covers known credential field names, not arbitrary free-text secrets. Evidence hashes support content comparison, not authentication, anonymization or tamper-proof storage.

The replay contract requires one session with parents delivered before children. It checks producer-local sequence numbers, but does not solve cross-host clock synchronization or arbitrary out-of-order graph ingestion. The validator covers an explicit subset of the draft; it is not a complete CDDL/JSON Schema validator. No end-to-end IETF conformance or interoperability claim is made.

## Branch and publication

This contribution resides under `Hackathon/IETF 127/running code/agentops/` on branch `agentops-observability-demo`. Its scope is a controlled prototype and documentation for review. Integration into the default branch and connection to an actual ICON control interface are separate steps.

## References

- [AgentOps Observability draft](https://datatracker.ietf.org/doc/draft-pei-opsawg-agentops-observability/), section mapping based on revision -00.
- [ICON requirements](https://datatracker.ietf.org/doc/draft-mcw-opsawg-icon-requirements/).
- [AgentOps survey](https://arxiv.org/abs/2606.01581).
- [DuoTrace](https://arxiv.org/abs/2608.29646), conceptual inspiration only.
- [LongRCA](https://arxiv.org/abs/2608.15242), conceptual inspiration only.
