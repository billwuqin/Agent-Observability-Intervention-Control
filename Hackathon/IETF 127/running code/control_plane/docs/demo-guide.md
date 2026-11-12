# Demo guide

A five-minute run through, in the order that makes the argument.

## Before you start

```sh
python verify.py
```

Five checks, roughly a second. If any check fails, do not present — the timing
guardrails are the only environmental dependency, and a failure there means the
box is loaded.

## The setup sentence

> An agent can now change a network device. The observability work tells us what
> it did afterwards. This is the part that decides whether it was allowed to do
> it at all, before the change reaches the device.

## Run it

```sh
python -m icon_control_plane
```

Four rows, one per scenario. Read them in this order.

**Row A — `QUERY_NEIGHBOR`, ALLOWED.** The boring case, and it should be shown
first. A read-only verb on the registered ambient set passes without a receipt.
The point to make: the common path costs nothing administratively. If the
control plane taxes every harmless operation, operators route around it.

**Row B — `APPLY_RATE_LIMIT`, ALLOWED.** The interesting allow. A real state
change on a real target with a real receipt. Point at the reason code:
`RECEIPT_AUTHORIZED`, not `DEFAULT_ALLOW` or `POLICY_PASS`. The gate did not
decide this was a good idea; it decided the agent could *prove* this exact
action was authorized.

Now the number on the right. Tens of microseconds, for CBOR decode, schema
check, content-id recomputation, and five binding checks. Make the point
explicitly: the cost of proof is not the reason to skip proof.

**Row C — `PURGE_AUDIT_LOGS`, REFUSED.** The rogue case. No receipt exists for
destroying the audit log, so the session collapses.

Two things to draw out, in this order:

1. The reason is `MISSING_RECEIPT`. The gate did not weigh intent or score
   risk. There was no authorization artifact for this action, so the answer is
   no.
2. The line underneath: *follow-up ambient refused (collapse is sticky)*. After
   the refusal, the harness retries a harmless `QUERY_NEIGHBOR` on the same
   session and is refused with `PRIOR_COLLAPSE`. **This is the whole design.**
   An error return lets an agent try again with a different verb. A collapse
   does not.

If someone asks "what resets it" — nothing does. There is no reset method, and
the test suite asserts one cannot be added by assignment:

```
test_no_unlock_after_collapse
```

A new session is a new gate. That is the recovery path, and it is deliberate
that recovery requires starting over rather than clearing a flag.

**Row D — `APPLY_ACL`, REFUSED.** The subtle case, and the one worth the most
time.

Here the receipt is *valid*. Correct principal, correct target, correct verb,
correct tier, correct signature. The only problem is that the bytes actually
submitted are not the bytes the receipt covers — the destination was rewritten
from `192.0.2.0/24` to `0.0.0.0/0` in flight.

`PAYLOAD_DIGEST_MISMATCH`. The lesson: authorization attaches to the payload,
not to the verb. "Apply an ACL" is not an action. "Apply *this* ACL to *this*
device" is an action.

This is also where you answer the obvious objection — *why not just validate
the payload against a policy?* Because policy evaluation is a decision, and a
decision can be argued with. A digest either matches or it does not.

## The line to close on

> Every row is a refusal that happens before the device is touched, or an allow
> that can be re-proved afterwards from the receipt alone. There is no row where
> the gate trusts the agent's account of what it was about to do.

## Anticipated questions

**"What happens on a real device?"** Nothing, here. The effector is a list of
strings. Wiring refusal and allow to NETCONF or gNMI is the integrator's step,
and it is the step where the interesting failure modes live — a gate that says
no and a device that changed anyway.

**"How fast is it really?"** Tens of microseconds, in-process, no I/O. The `<5ms`
figure in the original plan is met with two orders of magnitude of headroom. Say
plainly that this measures the gate, not the action: a device round trip will
dominate a real deployment.

**"Why CBOR?"** Deterministic encoding. The receipt id is a hash of the encoded
body, so two implementations that agree on the body must produce identical bytes
or they will compute different ids. JSON cannot promise that without a
canonicalization profile, and CBOR §4.2.1 already specifies the ordering.

**"Why not mTLS / OAuth / SPIFFE?"** Those establish *who is calling*. This
establishes *what they are allowed to do, to which object, with which bytes*.
They compose: the identity from the transport layer is the thing that should
appear as `principal.agent_id` here.

**"Is the signature checked?"** Not by default. `verify_signatures=False` in the
matrix, because the matrix is testing bindings, not key management. The test
suite runs the strict path with an enrolled keyring. Say this before someone
reads the source and asks.
