"""Single-command demo.

    python -m icon_control_plane
    docker build -f icon_control_plane/Dockerfile -t icon-hackathon-control-plane .
    docker run --rm icon-hackathon-control-plane
"""

from __future__ import annotations

import sys

from icon_control_plane.harness import run_hackathon_matrix
from icon_control_plane.hud import render_hud


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    reports = run_hackathon_matrix()
    render_hud(reports)
    return 0 if all(report.ok for report in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
