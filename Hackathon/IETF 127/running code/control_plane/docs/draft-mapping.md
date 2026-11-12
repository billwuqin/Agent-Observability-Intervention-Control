# Draft mapping

What this prototype implements, what it only partly implements, and what it
deliberately leaves to an integrator.

The requirements identifiers below are from
[draft-mcw-opsawg-icon-requirements-02](https://datatracker.ietf.org/doc/draft-mcw-opsawg-icon-requirements/),
section 5.2 (Control Requirements) and 5.3.1 (Runtime Execution Intervention).
Where this document says "not implemented," that is a scope statement, not a
claim that the requirement is unimportant.

## Summary

The prototype targets the Agent Enforcement Plane as described in §4.3 —
specifically the point "before tool invocation or network actions," where the
draft says policy enforcement happens. It does not attempt the Agent Management
Plane, and it does not attempt the Function Modules & Tools layer of §4.3.1.

Of the seventeen control requirements, one is directly and completely
addressed, five are partly addressed, and eleven are out of scope for a
control-plane-only prototype. That ratio is the honest headline, and it is why
the deliverable is a *gate*, not a framework.

## Directly addressed

**CTL-14 — Degraded behavior on control plane unreachability.** *Fail-Safe is
the default and only mode.*

This is the strongest correspondence in the prototype. The gate fails closed
without needing to detect an outage. If the authorization channel is
unreachable, no valid receipt arrives, and the Consequential path refuses by
construction rather than by a liveness check. There is no separate "am I still
connected?" branch that could itself fail open.

The draft offers three fallback modes: Fail-Safe, Fail-Hold, and Fail-Local.
This prototype implements Fail-Safe and deliberately does not implement the
other two.

- **Fail-Hold** (finish the current action, reject new ones) requires the gate
  to know what "current action" means, which requires the orchestrator's task
  state. That is a Management Plane concern.
- **Fail-Local** (continue on cached authorizations) is precisely the property
  the nonce ledger exists to prevent. Caching a receipt and replaying it is
  indistinguishable from an attack that steals one. A design that offers
  Fail-Local must bound it with something stronger than a nonce and a
  timestamp — for example a hardware-attested counter — and this prototype does
  not have one.

That asymmetry is worth discussing: the draft presents three modes as
equivalent choices, and from an execution-gate perspective they are not.

## Partly addressed

**CTL-1 — Action risk classification.** *Tier is consumed and enforced; it is
not derived.*

The gate enforces three consequence tiers and applies different evidence
requirements to each. It does **not** compute the tier from operation type,
target device role, or stability impact. The tier is declared by the receipt
issuer, and the gate's only contribution to classification is a denylist: an
ambient-registered verb whose name contains `purge`, `delete`, or `shutdown` is
refused as misclassified regardless of registration.

So the enforcement half of CTL-1 is present and the classification half is
missing. A caller that lies about the tier in a receipt can only do so by
producing a receipt that its own signer vouched for — which shifts the problem
to signer trust rather than solving it.

**CTL-3 — Rate limiting and concurrency control.** *Ambient only; collapses
rather than queues.*

A per-gate token counter limits ambient verbs per second. Exceeding it
collapses the session. The draft says exceeded actions "must be queued or
rejected with explicit feedback"; this rejects, and the feedback is the refusal
record.

There is no per-device, per-operator, or global limit, and no concurrency
control, because those require a shared view across gates and the prototype has
no shared state. Collapsing rather than queueing is a deliberate stance — a
burst is treated as a possible storm, and a storm is not given a queue to fill
— but it is a stance, not a requirement match.

**CTL-5 — Temporal and contextual validity.** *Action freshness, not context
freshness.*

The receipt carries `issued_at` and `expires_at` with a hard ceiling of 60
seconds between them, plus a strictly increasing nonce. The payload digest
binds the exact bytes. Together these give freshness and integrity **of the
action**.

They do not give freshness of the **context the agent reasoned over**. An agent
that read a stale topology, computed a correct action against it, and obtained
a valid receipt for that action will pass this gate. Binding the gate to the
network state the agent observed would require committing to a state digest in
the receipt, and nothing in this prototype does that. It is the most
interesting open problem the prototype surfaces.

**CTL-6 — Separation of duties.** *Quorum without role decomposition.*

`CRITICAL_IRREVERSIBLE` requires at least two **distinct** signers, and with
`verify_signatures=True` each signature is checked against an enrolled Ed25519
key. That is a real dual-custody control.

It is not the five-role decomposition the draft specifies (Read-Only, Propose,
Validate, Approve, Execute), and there are no distinct credentials per role. Two
signers could, in this implementation, be two keys held by the same operator.

**CTL-9 — Progressive authorization upgrade and downgrade.** *One-way only.*

The lattice moves from `VALID` to `COLLAPSED_REFUSAL` and never back. The
downgrade direction the draft asks for is therefore native and irreversible,
which is stronger than the requirement: authorization cannot be widened by any
call the agent can make.

Upgrade — returning to a higher authorization level — is not implemented, by
design. A gate that can be argued back into `VALID` is a gate with a bypass.

**CTL-17 — Dynamic boundary adaptation.** *Tightening only.*

Same mechanism as CTL-9: boundaries can be tightened to total refusal at
runtime. There is no policy injection channel and no path to widen. Global
coordination policy across a multi-agent environment is out of scope.

## Adjacent but not the requirement

**CTL-10 — Change attribution.** The attribution half is present: `principal_id`
appears on every audit record and is bound into the receipt, so an action cannot
be performed under another agent's authorization. The **distributed locking**
half is entirely absent — no locks, no owner identity on a target resource, no
conflict notifications.

**INT-1 — Execution interruption.** Collapse is an immediate kill-switch for the
session: it clears the session handles and marks credentials dead, and every
subsequent call refuses. But it is triggered *by gate evaluation*, not by an
out-of-band supervisor signal, and there is no pause/resume, no before/after
state reporting, and no accepted-versus-applied distinction. The draft's
emphasis that emergency intervention must work "independently of the agent's
internal LLM reasoning state" is met in the narrow sense that this gate has no
LLM in it at all.

## Out of scope

Not implemented, and not attempted: CTL-2 (blast radius), CTL-4 (cancellation
semantics), CTL-7 (fine-grained and YANG node-level scope), CTL-8 (escalation
chains), CTL-11 (cross-domain policy conflict), CTL-12 (four-level authority
precedence), CTL-13 (intent validation), CTL-15 (management plane HA),
CTL-16 (state reconciliation), and INT-2 through INT-4 (rollback, escalation,
correction).

Several of these — CTL-11 and CTL-12 in particular — are where the genuinely
hard distributed-systems problems live. A control plane that refuses everything
it does not understand, and refuses locally, can defer those problems. A control
plane that must *resolve* conflicts between four authority levels and multiple
policy domains cannot.

## What the prototype is claiming

Not conformance. The claim is narrower:

1. The five bindings in Receipt-v1 are sufficient to make an exact-action
   authorization checkable after the fact, and cheap enough to sit in the
   invocation path.
2. Monotonic collapse is a viable primitive for CTL-14's Fail-Safe mode, and it
   composes better with the other control requirements than a reset-able error
   return does.
3. The contextual-freshness gap (CTL-5) is the boundary where an execution gate
   stops being sufficient on its own, and that boundary is worth naming
   explicitly in the requirements text.

Point 3 is the contribution that would most benefit from discussion.
