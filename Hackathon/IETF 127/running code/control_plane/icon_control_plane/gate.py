"""Monotonic trigger lock. Capability state is VALID or bottom.

A failed check collapses the session. Later calls on that session refuse.
There is no reset. A new session is a new TriggerLockGate.
"""

from __future__ import annotations

import enum
import hashlib
import time
from dataclasses import dataclass
from typing import Any

from icon_control_plane import ed25519

COMPLIANCE_REFS: tuple[str, ...] = (
    "NIST-SP-800-171-3.1.2",
    "CMMC-2.0-AC.L2-3.1.5",
)
MAX_TTL_SECONDS = 60.0
# Two consecutive time.time() calls can land a few microseconds over 60.
_TTL_SLACK_SECONDS = 0.001

VERDICT_ALLOWED = "ALLOWED"
VERDICT_REFUSED = "REFUSED_LATTICE_COLLAPSE"


class Reason:
    AMBIENT_PERMITTED = "AMBIENT_PERMITTED"
    AMBIENT_VERB_FORBIDDEN = "AMBIENT_VERB_FORBIDDEN"
    AMBIENT_RATE_LIMIT = "AMBIENT_RATE_LIMIT"
    MISSING_RECEIPT = "MISSING_RECEIPT"
    PRINCIPAL_MISMATCH = "PRINCIPAL_MISMATCH"
    TARGET_URI_MISMATCH = "TARGET_URI_MISMATCH"
    VERB_MISMATCH = "VERB_MISMATCH"
    PAYLOAD_DIGEST_MISMATCH = "PAYLOAD_DIGEST_MISMATCH"
    RECEIPT_EXPIRED = "RECEIPT_EXPIRED"
    NOT_YET_VALID = "NOT_YET_VALID"
    TTL_WINDOW_EXCEEDED = "TTL_WINDOW_EXCEEDED"
    NONCE_REPLAY = "NONCE_REPLAY"
    QUORUM_FAILURE = "QUORUM_FAILURE"
    SIGNATURE_INVALID = "SIGNATURE_INVALID"
    PRIOR_COLLAPSE = "PRIOR_COLLAPSE"
    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    RECEIPT_AUTHORIZED = "RECEIPT_AUTHORIZED"


class ConsequenceTier(str, enum.Enum):
    AMBIENT_OBSERVATION = "AMBIENT_OBSERVATION"
    CONSEQUENTIAL_STATE_CHANGE = "CONSEQUENTIAL_STATE_CHANGE"
    CRITICAL_IRREVERSIBLE = "CRITICAL_IRREVERSIBLE"


class LatticeState(str, enum.Enum):
    UNINITIALIZED = "UNINITIALIZED"
    VALID = "VALID"
    COLLAPSED_REFUSAL = "COLLAPSED_REFUSAL"


TIER_ALIASES: dict[str, ConsequenceTier] = {
    "AMBIENT": ConsequenceTier.AMBIENT_OBSERVATION,
    "AMBIENT_OBSERVATION": ConsequenceTier.AMBIENT_OBSERVATION,
    "CONSEQUENTIAL": ConsequenceTier.CONSEQUENTIAL_STATE_CHANGE,
    "CONSEQUENTIAL_STATE_CHANGE": ConsequenceTier.CONSEQUENTIAL_STATE_CHANGE,
    "CRITICAL_IRREVERSIBLE": ConsequenceTier.CRITICAL_IRREVERSIBLE,
    "TIER_3_CRITICAL_IRREVERSIBLE": ConsequenceTier.CRITICAL_IRREVERSIBLE,
}


@dataclass(frozen=True)
class EmiliaReceipt:
    receipt_id: str
    principal_id: str
    target_uri: str
    verb: str
    consequence_tier: ConsequenceTier
    payload_sha256: str
    monotonic_nonce: int
    issued_at: float
    expires_at: float
    quorum_type: str
    signatures: list[dict[str, str]]

    def is_expired(self, current_time: float | None = None) -> bool:
        now = time.time() if current_time is None else current_time
        return now >= self.expires_at


@dataclass
class ExecutionResult:
    allowed: bool
    lattice_state: LatticeState
    message: str
    receipt_id: str | None = None
    audit_digest: str | None = None
    reason_code: str = ""
    verdict: str = ""
    audit_record: dict[str, Any] | None = None
    elapsed_us: int = 0


def _distinct_signers(signatures: list[dict[str, str]]) -> int:
    return len({entry.get("signer", "") for entry in signatures})


class TriggerLockGate:
    """Execution gate. Collapse is sticky for the life of this object."""

    def __init__(
        self,
        registered_ambient_verbs: set[str] | None = None,
        *,
        verify_signatures: bool = False,
        principal_keys: dict[str, bytes] | None = None,
        ambient_rate_limit: int | None = 10_000,
    ):
        self.registered_ambient_verbs = registered_ambient_verbs or {
            "GET_METRICS",
            "READ_STATUS",
            "WRITE_TELEMETRY_LOG",
            "HEARTBEAT",
            "QUERY_NEIGHBOR",
        }
        self._lattice_state = LatticeState.VALID
        self.last_nonce = 0
        self.refusal_history: list[str] = []
        self.audit_log: list[dict[str, Any]] = []
        self.verify_signatures = verify_signatures
        self.principal_keys = principal_keys or {}
        self.ambient_rate_limit = ambient_rate_limit
        self.session_handles = ["execution-channel", "credential-handle"]
        self.credentials_live = True
        self._ambient_window_start = 0.0
        self._ambient_count = 0

    @property
    def lattice_state(self) -> LatticeState:
        return self._lattice_state

    def evaluate_envelope(
        self,
        principal_id: str,
        target_uri: str,
        verb: str,
        payload_bytes: bytes,
        envelope: dict[str, Any],
        current_time: float | None = None,
    ) -> ExecutionResult:
        """Parse a Receipt-v1 envelope, then run the gate. A schema failure collapses."""
        started = time.perf_counter()
        if self._lattice_state == LatticeState.COLLAPSED_REFUSAL:
            return self.evaluate_action(
                principal_id=principal_id,
                target_uri=target_uri,
                verb=verb,
                payload_bytes=payload_bytes,
                receipt=None,
                current_time=current_time,
                started_at=started,
            )
        from icon_control_plane.receipt import ReceiptSchemaError, parse_receipt

        try:
            receipt = parse_receipt(envelope)
        except ReceiptSchemaError as exc:
            return self._collapse(
                f"Schema violation: {exc}",
                Reason.SCHEMA_VIOLATION,
                principal_id=principal_id,
                target_uri=target_uri,
                verb=verb,
                receipt_id=envelope.get("receipt_id") if isinstance(envelope, dict) else None,
                started=started,
            )
        return self.evaluate_action(
            principal_id=principal_id,
            target_uri=target_uri,
            verb=verb,
            payload_bytes=payload_bytes,
            receipt=receipt,
            current_time=current_time,
            started_at=started,
        )

    def evaluate_action(
        self,
        principal_id: str,
        target_uri: str,
        verb: str,
        payload_bytes: bytes,
        receipt: EmiliaReceipt | None = None,
        current_time: float | None = None,
        started_at: float | None = None,
    ) -> ExecutionResult:
        started = time.perf_counter() if started_at is None else started_at
        now = time.time() if current_time is None else current_time
        ctx = {
            "principal_id": principal_id,
            "target_uri": target_uri,
            "verb": verb,
            "receipt_id": None if receipt is None else receipt.receipt_id,
            "started": started,
        }

        if self._lattice_state == LatticeState.COLLAPSED_REFUSAL:
            return self._finish(
                allowed=False,
                state=LatticeState.COLLAPSED_REFUSAL,
                message="TRIGGER LOCK ENGAGED: Prior collapse invariant forbids all subsequent actions.",
                reason_code=Reason.PRIOR_COLLAPSE,
                audit_digest=None,
                **ctx,
            )

        payload_digest = hashlib.sha256(payload_bytes).hexdigest()

        if verb in self.registered_ambient_verbs:
            if any(token in verb.lower() for token in ("purge", "delete", "shutdown")):
                return self._collapse(
                    f"Malicious verb classification: {verb} cannot be ambient.",
                    Reason.AMBIENT_VERB_FORBIDDEN,
                    **ctx,
                )
            if self._ambient_rate_exceeded(now):
                return self._collapse(
                    f"Ambient rate limit exceeded for verb '{verb}'.",
                    Reason.AMBIENT_RATE_LIMIT,
                    **ctx,
                )
            audit_digest = hashlib.sha256(
                f"{principal_id}:{verb}:{payload_digest}:{now}".encode()
            ).hexdigest()
            return self._finish(
                allowed=True,
                state=LatticeState.VALID,
                message="Ambient action permitted within sandbox boundaries.",
                reason_code=Reason.AMBIENT_PERMITTED,
                audit_digest=audit_digest,
                **ctx,
            )

        if receipt is None:
            return self._collapse(
                f"Consequential verb '{verb}' attempted without an exact EMILIA action receipt.",
                Reason.MISSING_RECEIPT,
                **ctx,
            )

        if receipt.principal_id != principal_id:
            return self._collapse(
                f"Principal mismatch: receipt belongs to '{receipt.principal_id}', caller is '{principal_id}'.",
                Reason.PRINCIPAL_MISMATCH,
                **ctx,
            )
        if receipt.target_uri != target_uri:
            return self._collapse(
                f"Target URI mismatch: receipt specifies '{receipt.target_uri}', attempted '{target_uri}'.",
                Reason.TARGET_URI_MISMATCH,
                **ctx,
            )
        if receipt.verb != verb:
            return self._collapse(
                f"Verb mismatch: receipt specifies '{receipt.verb}', attempted '{verb}'.",
                Reason.VERB_MISMATCH,
                **ctx,
            )
        if receipt.payload_sha256 != payload_digest:
            return self._collapse(
                f"Payload digest mismatch: receipt expected {receipt.payload_sha256}, actual payload was {payload_digest}.",
                Reason.PAYLOAD_DIGEST_MISMATCH,
                **ctx,
            )

        window = receipt.expires_at - receipt.issued_at
        if window <= 0 or window > MAX_TTL_SECONDS + _TTL_SLACK_SECONDS:
            return self._collapse(
                f"Receipt TTL window {window} seconds exceeds the {MAX_TTL_SECONDS:.0f}s maximum.",
                Reason.TTL_WINDOW_EXCEEDED,
                **ctx,
            )
        if receipt.is_expired(now):
            return self._collapse(
                f"Receipt expired: expiration {receipt.expires_at} <= current time {now}.",
                Reason.RECEIPT_EXPIRED,
                **ctx,
            )
        if now < receipt.issued_at:
            return self._collapse(
                f"Receipt not yet valid: issued_at {receipt.issued_at} > current time {now}.",
                Reason.NOT_YET_VALID,
                **ctx,
            )
        if receipt.monotonic_nonce <= self.last_nonce:
            return self._collapse(
                f"Nonce regression/replay: receipt nonce {receipt.monotonic_nonce} <= last seen {self.last_nonce}.",
                Reason.NONCE_REPLAY,
                **ctx,
            )

        distinct = _distinct_signers(receipt.signatures)
        if receipt.consequence_tier == ConsequenceTier.CRITICAL_IRREVERSIBLE:
            if distinct < 2:
                return self._collapse(
                    f"Quorum failure: Tier 3 action '{verb}' requires >= 2 signatures, got {distinct}.",
                    Reason.QUORUM_FAILURE,
                    **ctx,
                )
        elif distinct < 1:
            return self._collapse(
                f"Quorum failure: Consequential action '{verb}' requires >= 1 signature, got {distinct}.",
                Reason.QUORUM_FAILURE,
                **ctx,
            )

        if self.verify_signatures:
            failure = self._signature_failure(receipt)
            if failure is not None:
                return self._collapse(failure, Reason.SIGNATURE_INVALID, **ctx)

        self.last_nonce = receipt.monotonic_nonce
        audit_digest = hashlib.sha256(
            f"{receipt.receipt_id}:{principal_id}:{verb}:{payload_digest}:{receipt.monotonic_nonce}".encode()
        ).hexdigest()
        return self._finish(
            allowed=True,
            state=LatticeState.VALID,
            message=f"Exact action '{verb}' authorized via EMILIA receipt {receipt.receipt_id}.",
            reason_code=Reason.RECEIPT_AUTHORIZED,
            audit_digest=audit_digest,
            **ctx,
        )

    def _signature_failure(self, receipt: EmiliaReceipt) -> str | None:
        signers = [entry.get("signer", "") for entry in receipt.signatures]
        if receipt.principal_id not in signers:
            return f"Signature verification failed: principal '{receipt.principal_id}' did not sign."
        for entry in receipt.signatures:
            signer = entry.get("signer", "")
            material = entry.get("sig", "")
            public = self.principal_keys.get(signer)
            if public is None:
                return f"Signature verification failed: signer '{signer}' is not enrolled."
            try:
                signature = bytes.fromhex(material)
            except ValueError:
                return f"Signature verification failed: signer '{signer}' signature is not hex."
            if not ed25519.verify(public, receipt.receipt_id.encode("ascii"), signature):
                return f"Signature verification failed: signer '{signer}' signature did not verify."
        return None

    def _ambient_rate_exceeded(self, now: float) -> bool:
        limit = self.ambient_rate_limit
        if limit is None:
            return False
        if now - self._ambient_window_start >= 1.0:
            self._ambient_window_start = now
            self._ambient_count = 0
        self._ambient_count += 1
        return self._ambient_count > limit

    def _collapse(self, human: str, reason_code: str, **ctx: Any) -> ExecutionResult:
        self._lattice_state = LatticeState.COLLAPSED_REFUSAL
        self.session_handles.clear()
        self.credentials_live = False
        self.refusal_history.append(human)
        return self._finish(
            allowed=False,
            state=LatticeState.COLLAPSED_REFUSAL,
            message=f"TRIGGER LOCK ENGAGED: Monotonic lattice collapse to total refusal. Reason: {human}",
            reason_code=reason_code,
            audit_digest=None,
            **ctx,
        )

    def _finish(
        self,
        *,
        allowed: bool,
        state: LatticeState,
        message: str,
        reason_code: str,
        audit_digest: str | None,
        principal_id: str,
        target_uri: str,
        verb: str,
        receipt_id: str | None,
        started: float,
    ) -> ExecutionResult:
        elapsed_us = int((time.perf_counter() - started) * 1_000_000)
        record = {
            "compliance_refs": list(COMPLIANCE_REFS),
            "verdict": VERDICT_ALLOWED if allowed else VERDICT_REFUSED,
            "reason": reason_code,
            "principal_id": principal_id,
            "target_uri": target_uri,
            "verb": verb,
            "receipt_id": receipt_id,
            "lattice_state": state.value,
            "audit_digest": audit_digest,
            "elapsed_us": elapsed_us,
        }
        self.audit_log.append(record)
        return ExecutionResult(
            allowed=allowed,
            lattice_state=state,
            message=message,
            receipt_id=receipt_id,
            audit_digest=audit_digest,
            reason_code=reason_code,
            verdict=record["verdict"],
            audit_record=record,
            elapsed_us=elapsed_us,
        )
