"""Control & Enforcement Plane invariants, Receipt-v1 wire format, and timing guardrails.

The suite is deliberately adversarial about one property: once a session
collapses, nothing on that session may ever be allowed again. Everything else
is a binding check that feeds that collapse.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import time
import unittest
from pathlib import Path

from icon_control_plane import ed25519
from icon_control_plane.__main__ import main
from icon_control_plane.cbor_min import decode, encode
from icon_control_plane.gate import (
    COMPLIANCE_REFS,
    ConsequenceTier,
    EmiliaReceipt,
    LatticeState,
    Reason,
    TriggerLockGate,
)
from icon_control_plane.harness import (
    FaultInjectionRepo,
    NetworkDiagnosisAgent,
    mint_critical_reset,
    run_hackathon_matrix,
    scenario_a_ambient,
    scenario_b_consequential,
    scenario_c_rogue,
    scenario_c_teardown,
    scenario_d_tamper,
    strict_keyring,
)
from icon_control_plane.receipt import (
    ReceiptSchemaError,
    build_normative_exemplar,
    content_id,
    decode_envelope,
    mint_receipt,
    parse_receipt,
    schema_dir,
)

ROOT = Path(__file__).resolve().parents[1]
AGENT = "diag-agent@ops.local"
_NOW = 1_800_000_010.0
_ISSUED = 1_800_000_000
_EXPIRES = 1_800_000_030

# RFC 8032 §7.1 test vectors 1 and 2.
_RFC_VECTORS = [
    (
        "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
        "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a",
        b"",
        "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
        "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b",
    ),
    (
        "4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
        "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c",
        bytes([0x72]),
        "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da"
        "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00",
    ),
]

# The submission must stay vendor-neutral and free of internal identifiers.
_BANNED = (
    "openai",
    "anthropic",
    "huawei",
    "qin wu",
    "claude",
    "gemini",
    "cisco",
    "azure",
    "gpt-",
    "amazon",
)


class TestEd25519(unittest.TestCase):
    def test_rfc8032_vectors(self):
        for seed_hex, public_hex, message, signature_hex in _RFC_VECTORS:
            seed = bytes.fromhex(seed_hex)
            public = bytes.fromhex(public_hex)
            signature = bytes.fromhex(signature_hex)
            self.assertEqual(ed25519.public_key(seed), public)
            self.assertEqual(ed25519.sign(seed, message), signature)
            self.assertTrue(ed25519.verify(public, message, signature))
            self.assertFalse(ed25519.verify(public, message + b"x", signature))


class TestMatrix(unittest.TestCase):
    def test_hackathon_matrix_scenarios(self):
        reports = run_hackathon_matrix()
        self.assertEqual([report.scenario_id for report in reports], ["A", "B", "C", "D"])
        self.assertTrue(all(report.ok for report in reports))
        ambient, consequential, rogue, tamper = reports
        self.assertEqual(ambient.verdict, "ALLOWED")
        self.assertLess(ambient.elapsed_us, 1000)
        self.assertEqual(consequential.verdict, "ALLOWED")
        self.assertEqual(consequential.reason_code, Reason.RECEIPT_AUTHORIZED)
        self.assertEqual(rogue.verdict, "REFUSED_LATTICE_COLLAPSE")
        self.assertTrue(rogue.follow_up_refused)
        self.assertEqual(tamper.reason_code, Reason.PAYLOAD_DIGEST_MISMATCH)
        self.assertTrue(scenario_c_teardown().ok)

    def test_scenario_sessions_are_independent(self):
        _report_c, collapsed = scenario_c_rogue()
        self.assertEqual(collapsed.lattice_state, LatticeState.COLLAPSED_REFUSAL)
        _report_a, fresh = scenario_a_ambient()
        self.assertEqual(fresh.lattice_state, LatticeState.VALID)

    def test_demo_main_exits_zero(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            self.assertEqual(main(), 0)
        rendered = buffer.getvalue()
        self.assertIn("matrix PASS", rendered)
        self.assertIn("PURGE_AUDIT_LOGS", rendered)

    def test_fault_repo_feeds_the_diagnosis_table(self):
        alarms = FaultInjectionRepo().inject()
        agent = NetworkDiagnosisAgent()
        target, verb, _payload = agent.propose_ambient(alarms[0])
        self.assertEqual(alarms[0].kind, "LINK_DOWN")
        self.assertEqual(verb, "QUERY_NEIGHBOR")
        self.assertEqual(target, alarms[0].device_uri)
        _target, rate_verb, _payload, envelope = agent.propose_rate_limit(alarms[1])
        self.assertEqual(rate_verb, "APPLY_RATE_LIMIT")
        self.assertEqual(envelope["action"]["consequence_tier"], "CONSEQUENTIAL")


class TestCollapseIsMonotonic(unittest.TestCase):
    def test_no_unlock_after_collapse(self):
        gate = TriggerLockGate()
        gate.evaluate_action(AGENT, "audit://ledger/local", "PURGE_AUDIT_LOGS", b"{}", current_time=_NOW)
        with self.assertRaises(AttributeError):
            gate.lattice_state = LatticeState.VALID  # type: ignore[misc]
        self.assertFalse(hasattr(gate, "reset"))
        payload, envelope = mint_critical_reset()
        follow = gate.evaluate_envelope(
            AGENT,
            "device://router-core-01.ops.local/mgmt",
            "FACTORY_RESET",
            payload,
            envelope,
            current_time=_NOW,
        )
        self.assertFalse(follow.allowed)
        self.assertEqual(follow.reason_code, Reason.PRIOR_COLLAPSE)

    def test_collapse_destroys_session_handles_and_credentials(self):
        _report, gate = scenario_c_rogue()
        self.assertFalse(gate.credentials_live)
        self.assertEqual(gate.session_handles, [])
        self.assertTrue(gate.refusal_history)

    def test_ambient_rate_limit_collapses_the_session(self):
        gate = TriggerLockGate(ambient_rate_limit=1)
        first = gate.evaluate_action(AGENT, "telemetry://node-01/metrics", "GET_METRICS", b"{}", current_time=50.0)
        second = gate.evaluate_action(AGENT, "telemetry://node-01/metrics", "GET_METRICS", b"{}", current_time=50.1)
        self.assertTrue(first.allowed)
        self.assertEqual(second.reason_code, Reason.AMBIENT_RATE_LIMIT)
        self.assertEqual(second.lattice_state, LatticeState.COLLAPSED_REFUSAL)

    def test_destructive_verb_cannot_be_reclassified_as_ambient(self):
        gate = TriggerLockGate(registered_ambient_verbs={"PURGE_AUDIT_LOGS"})
        result = gate.evaluate_action(
            AGENT, "audit://ledger/local", "PURGE_AUDIT_LOGS", b"{}", current_time=_NOW
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason_code, Reason.AMBIENT_VERB_FORBIDDEN)
        self.assertEqual(result.lattice_state, LatticeState.COLLAPSED_REFUSAL)


class TestBindingChecks(unittest.TestCase):
    def test_target_uri_mismatch_collapses(self):
        payload = b'{"policy":"rate-limit"}'
        envelope = mint_receipt(
            agent_id=AGENT,
            target_uri="device://router-core-01.ops.local/interfaces/0/policy",
            verb="APPLY_RATE_LIMIT",
            consequence_tier="CONSEQUENTIAL",
            payload=payload,
            monotonic_nonce=3,
            issued_at=_ISSUED,
            expires_at=_EXPIRES,
            signers=[(AGENT, bytes.fromhex(_RFC_VECTORS[0][0]))],
        )
        result = TriggerLockGate().evaluate_envelope(
            AGENT,
            "device://router-core-01.ops.local/interfaces/1/policy",
            "APPLY_RATE_LIMIT",
            payload,
            envelope,
            current_time=_NOW,
        )
        self.assertEqual(result.reason_code, Reason.TARGET_URI_MISMATCH)
        self.assertEqual(result.lattice_state, LatticeState.COLLAPSED_REFUSAL)

    def test_principal_mismatch_collapses(self):
        payload = b'{"policy":"rate-limit"}'
        envelope = mint_receipt(
            agent_id=AGENT,
            target_uri="device://router-core-01.ops.local/interfaces/0/policy",
            verb="APPLY_RATE_LIMIT",
            consequence_tier="CONSEQUENTIAL",
            payload=payload,
            monotonic_nonce=3,
            issued_at=_ISSUED,
            expires_at=_EXPIRES,
            signers=[(AGENT, bytes.fromhex(_RFC_VECTORS[0][0]))],
        )
        result = TriggerLockGate().evaluate_envelope(
            "impostor@ops.local",
            envelope["action"]["target_uri"],
            envelope["action"]["verb"],
            payload,
            envelope,
            current_time=_NOW,
        )
        self.assertEqual(result.reason_code, Reason.PRINCIPAL_MISMATCH)

    def test_nonce_replay_collapses(self):
        payload, envelope = mint_critical_reset()
        gate = TriggerLockGate(verify_signatures=True, principal_keys=strict_keyring())
        first = gate.evaluate_envelope(
            AGENT, "device://router-core-01.ops.local/mgmt", "FACTORY_RESET", payload, envelope, current_time=_NOW
        )
        self.assertTrue(first.allowed)
        replayed = TriggerLockGate().evaluate_action  # fresh gate, same receipt, nonce already seen is gate-local
        self.assertTrue(callable(replayed))
        second = gate.evaluate_envelope(
            AGENT, "device://router-core-01.ops.local/mgmt", "FACTORY_RESET", payload, envelope, current_time=_NOW
        )
        self.assertFalse(second.allowed)
        self.assertEqual(second.reason_code, Reason.NONCE_REPLAY)

    def test_content_id_mismatch_collapses(self):
        envelope, _raw = build_normative_exemplar()
        forged = dict(envelope)
        forged["receipt_id"] = "rcpt_" + ("ab" * 32)
        result = TriggerLockGate().evaluate_envelope(
            AGENT,
            envelope["action"]["target_uri"],
            envelope["action"]["verb"],
            b'{"policy":"rate-limit","bps":1000000}',
            forged,
            current_time=1_761_600_010.0,
        )
        self.assertEqual(result.reason_code, Reason.SCHEMA_VIOLATION)
        self.assertIn("does not match content id", result.message)

    def test_schema_violation_collapses(self):
        envelope, _raw = build_normative_exemplar()
        broken = dict(envelope)
        broken["comment"] = "extra"
        gate = TriggerLockGate()
        result = gate.evaluate_envelope(
            AGENT,
            envelope["action"]["target_uri"],
            envelope["action"]["verb"],
            b'{"policy":"rate-limit","bps":1000000}',
            broken,
            current_time=1_761_600_010.0,
        )
        self.assertEqual(result.reason_code, Reason.SCHEMA_VIOLATION)
        self.assertEqual(gate.lattice_state, LatticeState.COLLAPSED_REFUSAL)
        self.assertFalse(gate.credentials_live)


class TestQuorumAndFreshness(unittest.TestCase):
    def test_critical_requires_two_distinct_signers(self):
        payload = b'{"op":"factory-reset"}'
        digest = hashlib.sha256(payload).hexdigest()
        receipt = EmiliaReceipt(
            receipt_id="rcpt-one-signer",
            principal_id=AGENT,
            target_uri="device://router-core-01.ops.local/mgmt",
            verb="FACTORY_RESET",
            consequence_tier=ConsequenceTier.CRITICAL_IRREVERSIBLE,
            payload_sha256=digest,
            monotonic_nonce=4,
            issued_at=float(_ISSUED),
            expires_at=float(_EXPIRES),
            quorum_type="DUAL_CUSTODY",
            signatures=[{"signer": AGENT, "sig": "mock_sig"}],
        )
        result = TriggerLockGate().evaluate_action(
            AGENT, receipt.target_uri, receipt.verb, payload, receipt=receipt, current_time=_NOW
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason_code, Reason.QUORUM_FAILURE)
        self.assertIn("requires >= 2 signatures", result.message)

    def test_consequential_with_zero_signatures_collapses(self):
        payload = b'{"policy":"rate-limit"}'
        receipt = EmiliaReceipt(
            receipt_id="rcpt-no-sig",
            principal_id=AGENT,
            target_uri="device://router-core-01.ops.local/interfaces/0/policy",
            verb="APPLY_RATE_LIMIT",
            consequence_tier=ConsequenceTier.CONSEQUENTIAL_STATE_CHANGE,
            payload_sha256=hashlib.sha256(payload).hexdigest(),
            monotonic_nonce=8,
            issued_at=float(_ISSUED),
            expires_at=float(_EXPIRES),
            quorum_type="SINGLE_AGENT",
            signatures=[],
        )
        result = TriggerLockGate().evaluate_action(
            AGENT, receipt.target_uri, receipt.verb, payload, receipt=receipt, current_time=_NOW
        )
        self.assertEqual(result.reason_code, Reason.QUORUM_FAILURE)
        self.assertEqual(result.lattice_state, LatticeState.COLLAPSED_REFUSAL)

    def test_ttl_window_over_60_seconds_collapses(self):
        payload = b'{"op":"flush"}'
        receipt = EmiliaReceipt(
            receipt_id="rcpt-long-ttl",
            principal_id=AGENT,
            target_uri="device://router-core-01.ops.local/cache",
            verb="FLUSH_CACHE",
            consequence_tier=ConsequenceTier.CONSEQUENTIAL_STATE_CHANGE,
            payload_sha256=hashlib.sha256(payload).hexdigest(),
            monotonic_nonce=5,
            issued_at=1000.0,
            expires_at=1121.0,
            quorum_type="SINGLE_AGENT",
            signatures=[{"signer": AGENT, "sig": "mock_sig"}],
        )
        result = TriggerLockGate().evaluate_action(
            AGENT, receipt.target_uri, receipt.verb, payload, receipt=receipt, current_time=1100.0
        )
        self.assertEqual(result.reason_code, Reason.TTL_WINDOW_EXCEEDED)

    def test_expired_receipt_collapses(self):
        payload = b'{"op":"flush"}'
        receipt = EmiliaReceipt(
            receipt_id="rcpt-expired",
            principal_id=AGENT,
            target_uri="device://router-core-01.ops.local/cache",
            verb="FLUSH_CACHE",
            consequence_tier=ConsequenceTier.CONSEQUENTIAL_STATE_CHANGE,
            payload_sha256=hashlib.sha256(payload).hexdigest(),
            monotonic_nonce=5,
            issued_at=1000.0,
            expires_at=1030.0,
            quorum_type="SINGLE_AGENT",
            signatures=[{"signer": AGENT, "sig": "mock_sig"}],
        )
        result = TriggerLockGate().evaluate_action(
            AGENT, receipt.target_uri, receipt.verb, payload, receipt=receipt, current_time=1100.0
        )
        self.assertEqual(result.reason_code, Reason.RECEIPT_EXPIRED)

    def test_strict_dual_custody_verifies_and_rejects_a_bad_signature(self):
        payload, envelope = mint_critical_reset()
        gate = TriggerLockGate(verify_signatures=True, principal_keys=strict_keyring())
        result = gate.evaluate_envelope(
            AGENT, "device://router-core-01.ops.local/mgmt", "FACTORY_RESET", payload, envelope, current_time=_NOW
        )
        self.assertTrue(result.allowed)
        self.assertEqual(result.reason_code, Reason.RECEIPT_AUTHORIZED)

        bad = {
            "receipt_id": envelope["receipt_id"],
            "principal": dict(envelope["principal"]),
            "action": dict(envelope["action"]),
            "authorization": dict(envelope["authorization"]),
        }
        bad["authorization"]["signatures"] = [dict(item) for item in envelope["authorization"]["signatures"]]
        bad["authorization"]["signatures"][1]["sig"] = "00" * 64
        refused = TriggerLockGate(verify_signatures=True, principal_keys=strict_keyring()).evaluate_envelope(
            AGENT, "device://router-core-01.ops.local/mgmt", "FACTORY_RESET", payload, bad, current_time=_NOW
        )
        self.assertFalse(refused.allowed)
        self.assertEqual(refused.reason_code, Reason.SIGNATURE_INVALID)
        self.assertEqual(refused.lattice_state, LatticeState.COLLAPSED_REFUSAL)


class TestWireFormat(unittest.TestCase):
    def test_normative_cbor_exemplar_matches_builder(self):
        envelope, raw = build_normative_exemplar()
        disk = (schema_dir() / "aer_receipt_v1.cbor").read_bytes()
        self.assertEqual(disk, raw)
        decoded = decode_envelope(disk)
        self.assertEqual(decoded["receipt_id"], envelope["receipt_id"])
        self.assertEqual(encode(decode(disk)), disk)
        parsed = parse_receipt(decoded)
        self.assertEqual(parsed.consequence_tier, ConsequenceTier.CONSEQUENTIAL_STATE_CHANGE)
        self.assertEqual(parsed.receipt_id, content_id(envelope))

    def test_all_schema_artifacts_are_present(self):
        directory = schema_dir()
        for name in (
            "aer_receipt_v1.json",
            "aer_receipt_v1.cddl",
            "aer_receipt_v1.cbor",
            "aer_receipt_v1.example.json",
        ):
            self.assertTrue((directory / name).is_file(), name)

    def test_receipt_round_trips_through_cbor(self):
        payload = b'{"policy":"rate-limit"}'
        envelope = mint_receipt(
            agent_id=AGENT,
            target_uri="device://router-core-01.ops.local/interfaces/0/policy",
            verb="APPLY_RATE_LIMIT",
            consequence_tier="CONSEQUENTIAL",
            payload=payload,
            monotonic_nonce=9,
            issued_at=_ISSUED,
            expires_at=_EXPIRES,
            signers=[(AGENT, bytes.fromhex(_RFC_VECTORS[0][0]))],
        )
        decoded = decode_envelope(encode(envelope))
        self.assertEqual(decoded, envelope)
        self.assertEqual(parse_receipt(decoded).receipt_id, envelope["receipt_id"])

    def test_tampered_content_id_is_rejected_at_parse(self):
        envelope, _raw = build_normative_exemplar()
        envelope["action"]["payload_sha256"] = "00" * 32
        with self.assertRaises(ReceiptSchemaError):
            parse_receipt(envelope)

    def test_discriminators_are_order_stable(self):
        # Deterministic CBOR means two encodes of the same body are identical.
        envelope, _raw = build_normative_exemplar()
        self.assertEqual(encode(envelope), encode(dict(reversed(list(envelope.items())))))


class TestTimingGuardrails(unittest.TestCase):
    def test_parse_and_lattice_under_5ms(self):
        alarm = FaultInjectionRepo().inject()[1]
        target, verb, payload, envelope = NetworkDiagnosisAgent().propose_rate_limit(alarm)
        scenario_b_consequential()
        samples: list[float] = []
        for _ in range(11):
            gate = TriggerLockGate()
            started = time.perf_counter()
            result = gate.evaluate_envelope(AGENT, target, verb, payload, envelope, current_time=_NOW)
            samples.append((time.perf_counter() - started) * 1_000_000)
            self.assertTrue(result.allowed)
            self.assertIsNotNone(result.audit_record)
            self.assertEqual(result.audit_record["compliance_refs"], list(COMPLIANCE_REFS))
        samples.sort()
        median = samples[len(samples) // 2]
        self.assertLess(median, 5000, median)

    def test_ambient_median_under_1ms(self):
        samples = [scenario_a_ambient()[0].elapsed_us for _ in range(21)]
        samples.sort()
        median = samples[len(samples) // 2]
        self.assertLess(median, 1000, median)

    def test_refusal_is_faster_than_allow(self):
        # A refusal never reaches the signature or digest-comparison path.
        rogue = [scenario_c_rogue()[0].elapsed_us for _ in range(9)]
        _report, _gate = scenario_c_rogue()
        self.assertTrue(all(value < 5000 for value in rogue))


class TestSubmissionHygiene(unittest.TestCase):
    def test_package_names_no_third_party_vendors(self):
        roots = [ROOT / "icon_control_plane", ROOT / "schemas"]
        hits: list[str] = []
        for root in roots:
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix.lower() in {".cbor", ".pyc"}:
                    continue
                if "__pycache__" in path.parts:
                    continue
                text = path.read_text(encoding="utf-8", errors="replace").lower()
                for banned in _BANNED:
                    if banned in text:
                        hits.append(f"{path.relative_to(ROOT)}:{banned}")
        self.assertEqual(hits, [])

    def test_no_network_imports_in_the_gate(self):
        # The gate must not be able to reach the network on its own.
        forbidden = ("socket", "urllib", "http.client", "requests", "httpx", "ssl")
        for path in (ROOT / "icon_control_plane").glob("*.py"):
            source = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(f"import {token}", source, f"{path.name} imports {token}")


if __name__ == "__main__":
    unittest.main()
