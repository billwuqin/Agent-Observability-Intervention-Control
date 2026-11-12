"""ANSI terminal HUD for the hackathon demo. No curses, no third-party UI library."""

from __future__ import annotations

import os
import sys
from typing import TextIO

from icon_control_plane.harness import ScenarioReport

_RESET = "\033[0m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_CYAN = "\033[36m"
_DIM = "\033[2m"


def enable_windows_vt() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint()
        if ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            ctypes.windll.kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except (AttributeError, OSError):
        return


_WIDTH = 68


def _paint(text: str, color: str) -> str:
    return f"{color}{text}{_RESET}"


def _row(text: str) -> str:
    body = text[:_WIDTH]
    return "|" + body.ljust(_WIDTH) + "|"


def _rule() -> str:
    return "+" + ("-" * _WIDTH) + "+"


def render_hud(reports: list[ScenarioReport], out: TextIO | None = None) -> str:
    enable_windows_vt()
    stream = out or sys.stdout
    enrolled = "diag-agent@ops.local"
    lines = [
        _paint(_rule(), _CYAN),
        _paint(_row(" ICON CONTROL PLANE          Slide 2 local gate"), _CYAN),
        _row(f" principal {enrolled}   enrolled: yes"),
        _paint(_rule(), _CYAN),
        _row(" id  verb                  verdict                       us"),
    ]
    for report in reports:
        color = _GREEN if report.allowed else _RED
        lattice = "VALID" if report.lattice_state == "VALID" else "\u22a5"
        lines.append(
            _paint(
                _row(
                    f" {report.scenario_id:<2} {report.verb:<20} {report.verdict:<28} {report.elapsed_us:>6}"
                ),
                color,
            )
        )
        lines.append(_row(f"     reason {report.reason_code}   lattice {lattice}"))
        if report.audit_record:
            refs = ",".join(report.audit_record["compliance_refs"])
            lines.append(_row(f"     audit {refs}"))
        if report.follow_up_refused:
            lines.append(_paint(_row("     follow-up ambient refused (collapse is sticky)"), _RED))
    lines.append(_paint(_rule(), _CYAN))
    failed = [report.scenario_id for report in reports if not report.ok]
    if failed:
        lines.append(_paint(f"matrix FAIL {','.join(failed)}", _RED))
    else:
        lines.append(_paint("matrix PASS  A ambient  B consequential  C rogue  D tamper", _GREEN))
    lines.append(_paint("verification is local. this process makes no network call.", _DIM))
    text = "\n".join(lines)
    stream.write(text + "\n")
    return text
