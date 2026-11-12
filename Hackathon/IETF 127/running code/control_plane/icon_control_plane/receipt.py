"""Receipt-v1 wire envelope.

The content id is rcpt_ plus the hex SHA-256 of the canonical CBOR encoding
of the unsigned body. The unsigned body is principal, action, and
authorization without signatures. Signatures are over the ASCII receipt_id
and are not inside the hash.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from icon_control_plane import ed25519
from icon_control_plane.cbor_min import decode, encode
from icon_control_plane.gate import TIER_ALIASES, ConsequenceTier, EmiliaReceipt
from icon_control_plane.schema_check import SchemaError, check

_SCHEMA_CACHE: dict[str, Any] | None = None

# Fixed inputs for schemas/aer_receipt_v1.cbor. RFC 8032 test vector 1 is the signer.
_EXEMPLAR_SEED = bytes.fromhex(
    "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
)
_EXEMPLAR_PAYLOAD = b'{"policy":"rate-limit","bps":1000000}'
_EXEMPLAR_AGENT = "diag-agent@ops.local"


class ReceiptSchemaError(ValueError):
    pass


def schema_dir() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "schemas",
        here / "schemas",
    ]
    override = os.environ.get("ICON_SCHEMA_DIR")
    if override:
        candidates.insert(0, Path(override))
    for candidate in candidates:
        if (candidate / "aer_receipt_v1.json").is_file():
            return candidate
    raise ReceiptSchemaError("aer_receipt_v1.json is not on the schema path")


def load_schema() -> dict[str, Any]:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        _SCHEMA_CACHE = json.loads((schema_dir() / "aer_receipt_v1.json").read_text(encoding="utf-8"))
    return _SCHEMA_CACHE


def payload_digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def unsigned_body(envelope: dict[str, Any]) -> dict[str, Any]:
    authorization = dict(envelope["authorization"])
    authorization.pop("signatures", None)
    principal = {"agent_id": envelope["principal"]["agent_id"]}
    public = envelope["principal"].get("public_key_ed25519") or ""
    if public:
        principal["public_key_ed25519"] = public
    return {
        "principal": principal,
        "action": {
            "target_uri": envelope["action"]["target_uri"],
            "verb": envelope["action"]["verb"],
            "consequence_tier": envelope["action"]["consequence_tier"],
            "payload_sha256": envelope["action"]["payload_sha256"],
        },
        "authorization": {
            "monotonic_nonce": authorization["monotonic_nonce"],
            "issued_at": authorization["issued_at"],
            "expires_at": authorization["expires_at"],
        },
    }


def content_id(envelope: dict[str, Any]) -> str:
    digest = hashlib.sha256(encode(unsigned_body(envelope))).hexdigest()
    return "rcpt_" + digest


def _quorum_type(tier: ConsequenceTier) -> str:
    if tier == ConsequenceTier.CRITICAL_IRREVERSIBLE:
        return "DUAL_CUSTODY"
    if tier == ConsequenceTier.CONSEQUENTIAL_STATE_CHANGE:
        return "SINGLE_AGENT"
    return "AMBIENT"


def parse_receipt(envelope: dict[str, Any]) -> EmiliaReceipt:
    try:
        check(load_schema(), envelope)
    except SchemaError as exc:
        raise ReceiptSchemaError(str(exc)) from exc
    expected = content_id(envelope)
    if envelope["receipt_id"] != expected:
        raise ReceiptSchemaError(
            f"receipt_id {envelope['receipt_id']} does not match content id {expected}"
        )
    tier_name = envelope["action"]["consequence_tier"]
    tier = TIER_ALIASES.get(tier_name)
    if tier is None:
        raise ReceiptSchemaError(f"unknown consequence tier {tier_name}")
    authorization = envelope["authorization"]
    return EmiliaReceipt(
        receipt_id=envelope["receipt_id"],
        principal_id=envelope["principal"]["agent_id"],
        target_uri=envelope["action"]["target_uri"],
        verb=envelope["action"]["verb"],
        consequence_tier=tier,
        payload_sha256=envelope["action"]["payload_sha256"],
        monotonic_nonce=int(authorization["monotonic_nonce"]),
        issued_at=float(authorization["issued_at"]),
        expires_at=float(authorization["expires_at"]),
        quorum_type=_quorum_type(tier),
        signatures=list(authorization["signatures"]),
    )


def mint_receipt(
    *,
    agent_id: str,
    target_uri: str,
    verb: str,
    consequence_tier: str,
    payload: bytes,
    monotonic_nonce: int,
    issued_at: int,
    expires_at: int,
    signers: list[tuple[str, bytes]],
    public_key_ed25519: str | None = None,
) -> dict[str, Any]:
    if not signers:
        raise ReceiptSchemaError("mint requires at least one signer")
    agent_public = public_key_ed25519 or ed25519.public_key(signers[0][1]).hex()
    envelope: dict[str, Any] = {
        "receipt_id": "",
        "principal": {
            "agent_id": agent_id,
            "public_key_ed25519": agent_public,
        },
        "action": {
            "target_uri": target_uri,
            "verb": verb,
            "consequence_tier": consequence_tier,
            "payload_sha256": payload_digest(payload),
        },
        "authorization": {
            "monotonic_nonce": monotonic_nonce,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "signatures": [],
        },
    }
    envelope["receipt_id"] = content_id(envelope)
    message = envelope["receipt_id"].encode("ascii")
    signatures = []
    for signer, seed in signers:
        signatures.append({"signer": signer, "sig": ed25519.sign(seed, message).hex()})
    envelope["authorization"]["signatures"] = signatures
    parse_receipt(envelope)
    return envelope


def build_normative_exemplar() -> tuple[dict[str, Any], bytes]:
    envelope = mint_receipt(
        agent_id=_EXEMPLAR_AGENT,
        target_uri="device://router-core-01.ops.local/interfaces/0/policy",
        verb="APPLY_RATE_LIMIT",
        consequence_tier="CONSEQUENTIAL",
        payload=_EXEMPLAR_PAYLOAD,
        monotonic_nonce=7,
        issued_at=1_761_600_000,
        expires_at=1_761_600_030,
        signers=[(_EXEMPLAR_AGENT, _EXEMPLAR_SEED)],
    )
    return envelope, encode(envelope)


def decode_envelope(raw: bytes) -> dict[str, Any]:
    value = decode(raw)
    if not isinstance(value, dict):
        raise ReceiptSchemaError("CBOR envelope is not a map")
    return value


def write_normative_exemplars(directory: Path | None = None) -> Path:
    directory = directory or schema_dir()
    envelope, raw = build_normative_exemplar()
    cbor_path = directory / "aer_receipt_v1.cbor"
    json_path = directory / "aer_receipt_v1.example.json"
    cbor_path.write_bytes(raw)
    json_path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return cbor_path
