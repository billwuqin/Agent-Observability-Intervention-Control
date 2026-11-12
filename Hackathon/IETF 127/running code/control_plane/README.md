# Control &amp; Enforcement Plane — exact-action authorization for network agents

Runnable support for the IETF 127 ICON Hackathon work item on the **Control &
Enforcement Plane**: the component that decides whether a proposed network
mutation is permitted, and that refuses everything else.

This is a **self-contained reference implementation**, not a deployment. It
holds no credentials, opens no socket, and calls no model. Its only effect on
the world is a return value and an audit record written to memory.

## What it does

A network agent proposes an action against a managed device. The gate answers
one question: *was this exact action authorized by this exact principal for
this exact target, and can that authorization be proven afterwards?*

Five properties are enforced on every consequential call:

1. **Principal binding** — the receipt was issued to the agent that presents it.
2. **Target binding** — the receipt names the resource URI actually addressed.
3. **Verb binding** — the receipt names the operation actually attempted.
4. **Payload binding** — the SHA-256 of the bytes actually sent matches the
   digest in the receipt. A payload edited in flight does not validate.
5. **Freshness** — the receipt is inside a bounded validity window and carries
   a strictly increasing nonce, so a captured receipt cannot be replayed.

Any violation collapses the session to total refusal. The collapse is
**monotonic and sticky**: it is not a per-action error, and there is no reset
method to call. A new session means a new `TriggerLockGate`.

## What it does not do

The gate is a decision point, not an actuator. It does not push configuration,
hold device credentials it can exercise, or speak NETCONF, gNMI, SNMP, or REST.
Wiring the refusal or the allow to a real device is the integrator's step, and
in this repository the effector is a list of strings.

The prototype's model of an agent is a fixed diagnosis table. There is no LLM,
no planner, and no learned policy. Faults are synthetic.

## Quick start

Python 3.10+ is required. There are no third-party runtime dependencies, no
credentials, no containers required, and no network access.

```sh
python -m unittest discover -s tests -v
python -m icon_control_plane
python verify.py
```

`python -m icon_control_plane` runs the four-scenario matrix and prints the
HUD. Exit status is 0 when the matrix passes, 1 otherwise.

Container, if preferred:

```sh
docker build -t icon-control-plane .
docker run --rm icon-control-plane
```

## The four-scenario matrix

| ID | Scenario | Verb | Expected | Why |
|---|---|---|---|---|
| A | Authorized ambient observation | `QUERY_NEIGHBOR` | `ALLOWED` | Read-only verb on the registered ambient set |
| B | Authorized consequential change | `APPLY_RATE_LIMIT` | `ALLOWED` | Valid Receipt-v1, all five bindings hold |
| C | Rogue state destruction | `PURGE_AUDIT_LOGS` | `REFUSED` | No receipt; session collapses and stays collapsed |
| D | In-flight payload tamper | `APPLY_ACL` | `REFUSED` | Receipt valid, bytes swapped, digest mismatch |

Scenario C also re-attempts a benign `QUERY_NEIGHBOR` on the collapsed session
and asserts it is refused with `PRIOR_COLLAPSE`. That is the property that
separates a trigger lock from an error return.

## Consequence tiers

The tier is declared in the receipt and is not trusted from the caller's verb
string alone.

- **`AMBIENT_OBSERVATION`** — no receipt required. Registered verbs only. A verb
  whose name contains `purge`, `delete`, or `shutdown` is rejected from the
  ambient set regardless of registration: the classification is a defence
  against a caller relabelling a destructive call as ambient.
- **`CONSEQUENTIAL_STATE_CHANGE`** — at least one signature.
- **`CRITICAL_IRREVERSIBLE`** — at least two distinct signers (dual custody).

Refusal to meet the quorum collapses the session; it does not downgrade the
action.

## Receipt-v1

The wire format is defined in `schemas/` as JSON Schema, CDDL, a normative CBOR
encoding, and a worked JSON example.

```
receipt_id = "rcpt_" || hex(SHA-256(canonical_CBOR(unsigned_body)))
```

where `unsigned_body` is `principal`, `action`, and `authorization` without the
`signatures` array. Signatures are Ed25519 over the ASCII `receipt_id`, so the
body is committed to by the identifier and the signatures commit to the
identifier. Map keys use the deterministic CBOR ordering from RFC 8949
§4.2.1 — length first, then bytewise.

Ed25519 is implemented in `ed25519.py` against RFC 8032, and the test suite
checks it against the RFC's own test vectors. It is **not constant-time**; this
implementation does not target an adversary sharing the CPU.

## Audit output

Every decision, allowed or refused, appends a record containing the principal,
target URI, verb, receipt id, lattice state, reason code, compliance
references, and elapsed microseconds. Refusals carry the same structure as
allows, so a downstream collector does not have to special-case them.

The four AUDIT pillars map as follows:

- **Agent attribution** — `principal_id` on every record; the receipt is bound
  to it and cannot be presented by another agent.
- **Provenance** — `receipt_id` is the content id of the authorization itself.
- **Delegation traceability** — `quorum_type` plus the full signer set.
- **Tamper-evident evidence** — `audit_digest` chains receipt, principal, verb,
  payload digest, and nonce.

The digest is a plain SHA-256 over a delimited string. It supports comparison,
not authentication, and it is not a signature.

## Measurements and interpretation

Latencies are actual elapsed wall-clock durations of local in-process calls,
captured with `time.perf_counter()`.

- Ambient allow: tens of microseconds.
- Consequential allow, including CBOR decode, schema check, content-id
  recomputation, and five binding checks: tens of microseconds.
- Refusal: single-digit to low tens of microseconds.

The reported figure is dominated by CBOR decode and SHA-256, not by I/O,
because there is no I/O. A real deployment adding a device round trip will be
bounded by that round trip, not by this gate. The `<5ms` target is met with
roughly two orders of magnitude of headroom in-process; treat that as a
statement about the gate's arithmetic, not about end-to-end action latency.

The test suite asserts a median under 5 ms for the consequential path and under
1 ms for the ambient path, on eleven and twenty-one samples respectively. These
are guardrails against regression, not benchmark claims.

## Safety and limits

- The gate never performs the action. `effector.run()` in `harness.py` records a
  string.
- `verify_signatures` defaults to **off**. The matrix exercises binding checks;
  the dual-custody signature path is exercised separately by the test suite with
  an explicit keyring. A deployment must enable it.
- The JSON Schema checker covers the keywords this schema uses. It is not a
  general validator and should be replaced by a conforming implementation in
  production.
- Timestamps are integers. Clock skew between issuer and gate is not modelled;
  the window is absolute, not relative to a distributed clock.
- No persistence. The nonce ledger lives for the lifetime of the gate object, so
  replay protection across a process restart requires an external store.
- The CBOR decoder rejects indefinite lengths and trailing bytes, but it is not
  hardened against hostile input in the way a general-purpose decoder would be.

## Layout

```
icon_control_plane/
  gate.py           monotonic lattice, reason codes, tier and quorum policy
  receipt.py        Receipt-v1 mint, parse, content id, normative exemplar
  cbor_min.py       deterministic CBOR encode/decode for the receipt map
  ed25519.py        RFC 8032 sign and verify, standard library only
  schema_check.py   narrow JSON Schema checker for the frozen document
  harness.py        four-scenario matrix and the stub diagnosis agent
  hud.py            ANSI terminal rendering of the matrix
  __main__.py       entry point
schemas/            JSON Schema, CDDL, normative CBOR, worked example
tests/              invariants, wire format, timing guardrails
verify.py           one-command check: tests, matrix, vectors, timing
```

## Standards context

The control plane is the enforcement counterpart to observability work: an
observability record says what an agent did, and this says what it was permitted
to do. The receipt format is offered as a discussion artifact for the ICON
requirements work, specifically the boundary between an agent's proposal and a
network element's acceptance of it.

## Licensing

This contribution follows the repository's existing public-domain declaration.
No separate module license is introduced.

## References

- [ICON requirements](https://datatracker.ietf.org/doc/draft-mcw-opsawg-icon-requirements/)
- [AgentOps Observability draft](https://datatracker.ietf.org/doc/draft-pei-opsawg-agentops-observability/)
- [RFC 8032](https://www.rfc-editor.org/rfc/rfc8032) — EdDSA
- [RFC 8949](https://www.rfc-editor.org/rfc/rfc8949) — CBOR, §4.2.1 deterministic encoding
