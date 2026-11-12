# FAQ

Questions this prototype tends to raise, answered directly.

## Scope

**Is this a real deployment?**
No. It is a controlled reference implementation. It performs no network I/O,
holds no device credentials it can exercise, and its only effector is a list of
strings that records what *would* have run.

**Is it a proposal for a standard?**
It is a discussion artifact. The receipt format is offered as input to the ICON
requirements work, not as a finished wire specification. It has one
implementation and no interoperability testing, which is exactly why it belongs
in a hackathon rather than a working group last call.

**Does it duplicate the AgentOps observability work?**
No, it is the complement. That work records what an agent did and diagnoses
what went wrong. This decides, beforehand, whether the agent was permitted to do
it. The two meet at the receipt: an observability record can cite a
`receipt_id`, and the receipt proves the action was authorized.

**Why not contribute to the existing draft instead of running code?**
Because running code settles arguments that prose cannot. Whether monotonic
collapse is usable as a control-plane primitive is not a question you answer in
a paragraph.

## Design

**Why does a failed check collapse everything instead of returning an error?**
Because the threat model includes a compromised or hallucinating agent, and such
an agent responds to errors by retrying. An error return is a suggestion. A
collapse is a stop.

Concretely: if `PURGE_AUDIT_LOGS` returned `denied` and the session stayed
valid, the next thing the agent tries is `DELETE_AUDIT_LOGS`, then
`ROTATE_AUDIT_LOGS`, and one of them is on the ambient list. The collapse makes
the first refusal final.

**Isn't collapsing on everything fragile? A bug means total outage.**
Yes. That is the trade, and it should be argued about rather than assumed. The
mitigations are that the gate is small enough to audit, that the ambient path
has no shared state to corrupt, and that recovery is "start a new session"
rather than "clear a flag." If the collapse proves too blunt in practice, the
right refinement is a narrower collapse domain — per-target rather than
per-session — not a reset method.

**Why is there no reset?**
A reset is a bypass. Anything that can return the lattice to `VALID` is a path
an attacker will look for, and the cheapest way to prove none exists is to not
have one. `TriggerLockGate.lattice_state` is a read-only property; the test
suite asserts assignment raises.

**Why is the nonce ledger in memory only?**
Because persistence was out of scope for the prototype and an in-memory ledger
makes the demo hermetic. This is a real gap: replay protection across a process
restart needs an external store, and that store becomes a dependency and a
failure domain. It is the first thing to build before this leaves a demo
environment.

**Why not use a standard JSON Schema library?**
`schema_check.py` covers only the keywords this frozen document uses, so it adds
no dependency and no supply chain. It is explicitly not a general validator, and
a deployment should replace it with a conforming implementation.

**Why is `verify_signatures` off by default?**
Because the four-scenario matrix is testing *bindings*, and turning signature
verification on would require distributing an enrolled keyring to every caller
of the demo. A deployment must turn it on. The test suite exercises the strict
path, including a deliberately corrupted signature, so the code path is not
untested — it is just not on the default demo path.

**Why Ed25519 rather than a MAC?**
A MAC requires a shared secret, so the verifier can also forge. This receipt is
designed to be checkable by a party that should not be able to mint one.

**Is the Ed25519 implementation safe?**
It is correct against the RFC 8032 test vectors and it is not constant-time. A
bad signature collapses the gate. It does not target an adversary sharing the
CPU, and it is not a substitute for a vetted library in production.

## The wire format

**Why is `receipt_id` a hash rather than a UUID?**
Because a UUID asserts nothing. A content id means the identifier *is* the
authorization: recompute it and you know the body has not changed. It also makes
signatures self-referential — signing the id signs the body without a
canonicalization step at verification time.

**Why are signatures over the ASCII id rather than over the body?**
It removes any possibility of two implementations disagreeing about body
serialization at the point where a signature would fail. The body is committed
to transitively, through the id.

**Why is the TTL ceiling 60 seconds?**
It is a guardrail against an issuer that would otherwise mint a day-long
authorization. A consequential network change should be authorized close to when
it happens. The exact number is a policy choice and belongs in configuration,
not in the format.

**What stops an issuer from minting a receipt for anything it wants?**
Nothing, inside this component. The gate checks that the receipt covers the
action; it does not check that the action is wise. Trust in the issuer is
assumed, and constraining the issuer is a policy question for the layer above.

**Can two actions share a receipt?**
No. The receipt binds one verb, one target URI, and one payload digest. Reuse
with a different payload fails the digest check; reuse with the same payload
fails the nonce check.

## Interpretation

**Are the latency numbers a benchmark?**
No. They are guardrails against regression in an in-process call with no I/O.
The `<5ms` target from the original plan is met with roughly two orders of
magnitude of headroom, and that should be read as a statement about the gate's
arithmetic — CBOR decode and SHA-256 — not about end-to-end action latency. A
real deployment adding a device round trip will be bounded by the round trip.

**What is the single biggest gap?**
Context freshness. The gate proves the *action* was authorized. It does not
prove the agent was looking at current network state when it decided. An agent
reasoning over a stale topology will produce a correctly authorized, correctly
bound, and completely wrong change — and pass this gate. Binding a state digest
into the receipt is the obvious next step and is not implemented.

**What would you do with a second week?**
In order: a persistent nonce ledger, then context binding (a state digest in the
receipt), then a real effector behind the allow path so the first integration
failure is found in a lab rather than a production network.

## Practical

**How do I run just the tests?**
`python -m unittest discover -s tests -t . -v`

**How do I run the container?**
`docker build -t icon-control-plane .` then `docker run --rm icon-control-plane`.

**Can I use this in my own product?**
The repository declares public domain. See `LICENSE`.

**Where do I report a problem?**
Open an issue on the repository this directory lives in.
