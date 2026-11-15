# ICON agent handover

Runnable support for the IETF 127 ICON Hackathon: a simulated video session that outgrows a small compute node and has to move to a larger one. Every request is recorded, checked against a policy boundary before the world changes, and can be paused, rolled back, or corrected when the agent steps outside that boundary.

This is an in-process reference run, not a deployment. It plays no video, calls no model, and speaks no network-management protocol. The only outputs are a printed scoreboard, a JSON trace, and a local browser page.

## What it shows

Four HD sessions fill `edge-small` (8 compute units). A 4K session needs 6 units, so it does not fit there. The agent then asks for compute and bandwidth on `core-large` and proposes handovers. Control answers before any session, connection, or playback state moves:

- **allow** when the request is inside capacity, budget, and blast radius
- **refuse** when it is not, with no side effect
- **needs approval** when a 4K move would cross the soft path ceiling but stay under the hard budget

Intervention is separate. An operator can pause the agent, roll back a handover whose acknowledgement failed, and replace the open plan. Those steps are `H1`, `I1`, `I2`, and `I3` in the ledger. `H1` is an approval (control). `I1`–`I3` are intervention.

The workload is a concrete scenario for the ICON use-case discussion. Section 6 of [draft-king-rokui-ainetops-usecases-03](https://datatracker.ietf.org/doc/html/draft-king-rokui-ainetops-usecases-03) does not itself specify a video use case. The drafts this run follows are listed in [HACKATHON-PLAN.md](HACKATHON-PLAN.md).

## Requirements

Python 3.10 or newer. There are no third-party packages, credentials, or containers.

If `python3` on the machine is older than 3.10, these scripts look for `python3.11` or `python3.10` on `PATH` and re-run with that interpreter.

## Run the scoreboard

From this directory:

```sh
python3 demo.py
```

The command prints one line per ledger step, then the scoreboard. Exit status is 0 when the scoreboard matches the frozen ledger in [HACKATHON-PLAN.md](HACKATHON-PLAN.md). Exit status is 1 when it does not. A passing run ends with:

```text
ICON handover scoreboard
  control allow=11 refuse=7 needs_approval=1 paused=1
  allow_still_in_effect=10 allow_rolled_back=1
  probes_caught_before_side_effect=3/3
  intervention pause=completed rollback=completed
  sessions_continuous=s1,s2,s4 sessions_split=0
  s3_home=edge-small s3_conn=c3 playback_sec=120
  blast_radius_max_in_one_allowed_action=1 limit=2
  edge_units=2/8 core_units=14/32 path_mbps=35/40
  secrets_in_trace=0
  human.intervention=3 recovery.attempt=1 checkpoint.restored=1
```

The same run writes `trace.json` in this directory. Subscriber identifiers used as fixtures stay out of that file.

## Run the browser view

In a second terminal, from this directory:

```sh
python3 ui.py
```

Then open [http://127.0.0.1:8765](http://127.0.0.1:8765).

The page serves only on `127.0.0.1`, port 8765. It replays the same ledger as `demo.py`.

| Button | What it does |
| --- | --- |
| Back | Previous step |
| Next | Next step |
| Play | Advance about once a second. Click again to stop. |
| Result | Jump to the last step and the final scoreboard |

The left list is the ledger. `D1`–`D20` are agent requests. `H1` is the operator approval. `I1`, `I2`, and `I3` are pause, rollback, and correction. Select a row to read that step. The two node cards are `edge-small` and `core-large`. The scoreboard card counts only the steps you have reached. The final numbers appear on the last step.

Stop the server with Ctrl-C.

## Layout

| File | Role |
| --- | --- |
| `demo.py` | Runs the ledger, prints the scoreboard, writes `trace.json` |
| `ui.py`, `ui.html` | Local browser replay |
| `script.py` | Frozen step list |
| `world.py` | Two nodes, one path, four sessions |
| `policy.py` | Allow, refuse, and needs-approval checks |
| `control.py` | Applies a proposal only after policy allows it |
| `intervention.py` | Approve, pause, rollback, and correct |
| `trace.py` | Append-only event log |
| `HACKATHON-PLAN.md` | Ledger, check order, and the numbers the demo must print |
