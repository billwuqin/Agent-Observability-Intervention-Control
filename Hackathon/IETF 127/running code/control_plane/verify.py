#!/usr/bin/env python3
"""One-command verification for the ICON control plane submission.

Checks, in order:

  1. the unit-test suite passes
  2. the four-scenario matrix passes end to end
  3. the normative CBOR exemplar on disk matches a freshly built one
  4. the schema directory resolves and carries all four artifacts
  5. the consequential path stays inside the latency guardrail

Runs offline, with no third-party packages. Exit 0 only if every check passes.

    python verify.py
"""

from __future__ import annotations

import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from icon_control_plane.harness import (  # noqa: E402
    FaultInjectionRepo,
    NetworkDiagnosisAgent,
    run_hackathon_matrix,
)
from icon_control_plane.receipt import (  # noqa: E402
    build_normative_exemplar,
    content_id,
    schema_dir,
)
from icon_control_plane.gate import TriggerLockGate  # noqa: E402

NOW = 1_800_000_010.0
LATENCY_GUARDRAIL_US = 5_000


class Check:
    def __init__(self) -> None:
        self.rows: list[tuple[str, bool, str]] = []

    def record(self, name: str, ok: bool, detail: str) -> bool:
        self.rows.append((name, ok, detail))
        print(f"  [{'PASS' if ok else 'FAIL'}] {name} — {detail}")
        return ok

    def report(self) -> int:
        failed = [name for name, ok, _ in self.rows if not ok]
        print()
        if failed:
            print(f"VERIFY FAIL — {len(failed)} of {len(self.rows)} checks failed: {', '.join(failed)}")
            return 1
        print(f"VERIFY PASS — {len(self.rows)} of {len(self.rows)} checks")
        return 0


def check_tests(check: Check) -> bool:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    tail = [line for line in proc.stdout.strip().splitlines() if line.strip()]
    summary = tail[-1] if tail else "no output"
    ok = proc.returncode == 0
    if not ok:
        print(proc.stdout)
    return check.record("unit tests", ok, summary)


def check_matrix(check: Check) -> bool:
    reports = run_hackathon_matrix()
    ids = [report.scenario_id for report in reports]
    ok = ids == ["A", "B", "C", "D"] and all(report.ok for report in reports)
    detail = " ".join(f"{report.scenario_id}:{report.verdict}" for report in reports)
    return check.record("scenario matrix", ok, detail)


def check_exemplar(check: Check) -> bool:
    envelope, freshly_built = build_normative_exemplar()
    on_disk = (schema_dir() / "aer_receipt_v1.cbor").read_bytes()
    same = on_disk == freshly_built
    detail = f"{len(on_disk)} bytes, cbor_sha256={content_id(envelope)[5:21]}…"
    if not same:
        detail = "on-disk CBOR does not match the builder output"
    return check.record("normative exemplar", same, detail)


def check_schema_artifacts(check: Check) -> bool:
    directory = schema_dir()
    wanted = [
        "aer_receipt_v1.json",
        "aer_receipt_v1.cddl",
        "aer_receipt_v1.cbor",
        "aer_receipt_v1.example.json",
    ]
    missing = [name for name in wanted if not (directory / name).is_file()]
    ok = not missing
    detail = f"{directory.name}/ complete" if ok else f"missing {', '.join(missing)}"
    return check.record("schema artifacts", ok, detail)


def check_latency(check: Check) -> bool:
    alarm = FaultInjectionRepo().inject()[1]
    target, verb, payload, envelope = NetworkDiagnosisAgent().propose_rate_limit(alarm)
    samples: list[float] = []
    for _ in range(21):
        gate = TriggerLockGate()
        started = time.perf_counter()
        gate.evaluate_envelope(
            "diag-agent@ops.local",
            target,
            verb,
            payload,
            envelope,
            current_time=NOW,
        )
        samples.append((time.perf_counter() - started) * 1_000_000)
    median = statistics.median(samples)
    worst = max(samples)
    ok = median < LATENCY_GUARDRAIL_US
    detail = f"median {median:.0f} us, worst {worst:.0f} us, guardrail {LATENCY_GUARDRAIL_US} us"
    return check.record("consequential latency", ok, detail)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("ICON control plane — verification")
    print(f"python {sys.version.split()[0]} on {sys.platform}")
    print(f"root   {ROOT}")
    print()
    check = Check()
    check_tests(check)
    check_matrix(check)
    check_exemplar(check)
    check_schema_artifacts(check)
    check_latency(check)
    return check.report()


if __name__ == "__main__":
    raise SystemExit(main())
