"""Browser view of the handover run.

    python3 ui.py

Then open http://127.0.0.1:8765. Back and Next step through the same ledger
as demo.py. Result jumps to the scoreboard.
"""

import sys

if sys.version_info < (3, 10):
    import os
    import shutil

    candidate = shutil.which("python3.11") or shutil.which("python3.10")
    if candidate:
        os.execv(candidate, [candidate] + sys.argv)
    sys.stderr.write("Python 3.10 or newer is required.\n")
    raise SystemExit(1)

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import demo
import script
from script import Operator
from world import Proposal

ROOT = Path(__file__).resolve().parent
HTML = (ROOT / "ui.html").read_text(encoding="utf-8")

BLURBS = {
    "D1": "Admit s1 as HD on the small node.",
    "D2": "Admit s2 as HD on the small node.",
    "D3": "Admit s3 as HD on the small node.",
    "D4": "Admit s4. The small node is full: 8 of 8 units.",
    "D5": "s1 cannot become 4K here. Control refuses. Nothing moves.",
    "D6": "s2 cannot become 4K here. Control refuses. Nothing moves.",
    "D7": "Reserve 4K compute for s1 on the large node. s1 is still home on the small node.",
    "D8": "Reserve 15 Mbit/s for s1. That is under the 20 Mbit/s cost ceiling.",
    "D9": "Hand s1 to the large node as 4K. Session id stays s1. Connection c1 becomes c1b. Playback stays 120.",
    "D10": "Reserve 4K compute for s2 on the large node.",
    "D11": "Handing s2 over would put the path at 30 Mbit/s. Control waits.",
    "H1": "The operator approves the s2 handover.",
    "D12": "s2 completes. Connection c2 becomes c2b. Path is 30 of 40.",
    "D13": "The agent asks to move three sessions at once.",
    "D14": "The agent names a node that is not allowed.",
    "D15": "The agent puts a raw subscriber id in the bundle.",
    "D16": "A legal handover of s3 is allowed. State is copied, then the acknowledgement fails.",
    "D17": "The agent tries to drop s3 on the small node anyway.",
    "D18": "The agent tries the same drop again.",
    "I1": "The operator pauses the agent.",
    "D19": "The agent asks to move s4 while the pause is on.",
    "I2": "The operator rolls the partial s3 handover back.",
    "I3": "The operator replaces the plan: move s4 only.",
    "D20": "s4 moves to the large node. Connection c4 becomes c4b. s3 stays on the small node.",
}


def payload():
    world, trace, records = demo.run()
    board = demo.scoreboard(world, trace, records)
    errors = demo.check(world, trace, board)
    if errors:
        raise SystemExit("\n".join(errors))
    steps = script.steps()
    if len(steps) != len(records):
        raise SystemExit("step count does not match the run")
    frames = []
    for step, (record, obs) in zip(steps, records):
        edge, core, reserved, path, paused, grant, partial, homes = obs
        sessions = list(step.sessions) if isinstance(step, Proposal) else []
        target = step.target if isinstance(step, Proposal) else ""
        variant = step.variant if isinstance(step, Proposal) else ""
        frames.append({
            "id": record.id,
            "tick": record.tick,
            "kind": record.kind,
            "action": record.action,
            "decision": record.decision,
            "reason": record.reason,
            "mutated": record.mutated,
            "risk": record.risk,
            "mechanism": record.mechanism,
            "result": record.result,
            "sessions": sessions,
            "target": target or "",
            "variant": variant or "",
            "plan": step.plan if isinstance(step, Operator) else "",
            "edge": edge,
            "core": core,
            "reserved": reserved,
            "path": path,
            "paused": paused,
            "grant": grant,
            "partial": list(partial),
            "homes": [
                {"id": sid, "node": node, "conn": conn, "variant": variant_name, "playback": playback}
                for sid, node, conn, variant_name, playback in homes
            ],
            "blurbTitle": BLURBS[record.id],
            "blurb": BLURBS[record.id],
        })
    body = {"frames": frames, "board": board}
    encoded = json.dumps(body)
    if "user-1001" in encoded or "tok-" in encoded:
        raise SystemExit("UI payload included a subscriber value")
    return encoded.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            body = HTML.encode("utf-8")
            content_type = "text/html; charset=utf-8"
        elif path == "/api/run":
            body = payload()
            content_type = "application/json"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


HOST = "127.0.0.1"
PORT = 8765


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print("ICON handover UI", flush=True)
    print(f"http://{HOST}:{PORT}", flush=True)
    print("Back and Next step through the run. Result jumps to the scoreboard.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
