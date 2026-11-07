import argparse
import json
import platform
import sys
import time
from pathlib import Path
from . import __version__
from .analysis import BASELINE, Detector, diagnose, intervention_request
from .contracts import validate_trace
from .scenarios import CASES, run_scenario
from .telemetry import metrics
from .ui import render_html


def analyze(events):
    validate_trace(events)
    t = time.perf_counter_ns()
    detector = Detector()
    for event in events:
        detector.consume(event)
    result = diagnose(events)
    return {"events": events, "metrics": metrics(events), "anomalies": detector.anomalies,
            "assertions": detector.assertions, "diagnosis": result,
            "intervention": intervention_request(detector.anomalies, result),
            "analysis_duration_ms": (time.perf_counter_ns() - t) / 1_000_000}


def write_json(file, data):
    file.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def demo(out):
    out.mkdir(parents=True, exist_ok=True)
    runs = []
    for case in CASES:
        recorder, truth = run_scenario(case)
        result = analyze(recorder.events)
        result["case"] = case
        result["ground_truth"] = truth
        folder = out / case
        folder.mkdir(exist_ok=True)
        write_json(folder / "events.json", recorder.events)
        write_json(folder / "evidence.json", recorder.evidence)
        write_json(folder / "analysis.json", result)
        runs.append(result)
    eligible = [r for r in runs if r["ground_truth"]["task_failed"]]
    answered = [r for r in eligible if r["diagnosis"]["status"] == "diagnosed"]
    correct = [r for r in answered if r["diagnosis"]["record"]["root_cause_event_id"] == r["ground_truth"]["root_event_id"] and r["diagnosis"]["record"]["responsible_actor_id"] == r["ground_truth"]["responsible_actor"]]
    alarm_matches = sum(bool(r["anomalies"]) == r["ground_truth"]["expected_alarm"] for r in runs)
    summary = {"prototype_version": __version__, "environment": {"python": sys.version.split()[0], "platform": platform.platform(), "dependencies": "Python standard library only"},
               "baseline": BASELINE, "case_count": len(runs), "alarm_expectations_met": alarm_matches,
               "failed_case_count": len(eligible), "diagnosed_count": len(answered), "correct_actor_and_root_count": len(correct),
               "abstention_count": len(eligible)-len(answered), "supported_label_cases": sum(r["ground_truth"]["root_event_id"] is not None for r in eligible),
               "scope": "Controlled synthetic scenarios; baseline rules and fixtures were designed together. Not a held-out benchmark or model-quality result.",
               "measurement_limits": "Durations measured locally. Model responses, token counts, network state and tool faults are simulated. No external LLM, network device or actuator is used.",
               "runs": runs}
    write_json(out / "report.json", summary)
    (out / "index.html").write_text(render_html(summary), encoding="utf-8")
    print(json.dumps({k:v for k,v in summary.items() if k != "runs"}, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(description="AgentOps controlled prototype")
    sub = parser.add_subparsers(dest="command", required=True)
    d = sub.add_parser("demo", help="run nine measured synthetic workflows and build HTML report")
    d.add_argument("--out", type=Path, default=Path("artifacts"))
    r = sub.add_parser("replay", help="analyze normalized event JSON, no ground-truth input")
    r.add_argument("events", type=Path)
    r.add_argument("--out", type=Path, default=Path("replay-result.json"))
    args = parser.parse_args()
    if args.command == "demo":
        demo(args.out)
    else:
        result = analyze(json.loads(args.events.read_text(encoding="utf-8")))
        write_json(args.out, result)
        print(args.out)


if __name__ == "__main__":
    main()
