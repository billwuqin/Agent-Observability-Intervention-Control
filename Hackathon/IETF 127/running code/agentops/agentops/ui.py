import html
import json


def render_html(report):
    esc = html.escape
    sections = []
    for run in report["runs"]:
        d = run["diagnosis"]
        record = d.get("record", {})
        root = record.get("root_cause_event_id")
        rows = []
        for e in run["events"]:
            rows.append('<tr class="%s"><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                "root" if e["event_id"] == root else "", esc(e["event_id"]), esc(e["actor"]["id"]), esc(e["event_type"]),
                esc(e["status"]), esc(str(e.get("action", {}).get("duration_ms", "")))))
        sections.append(f'''<section id="{esc(run['case'])}"><h2>{esc(run['case'])}</h2>
        <p><b>Diagnosis:</b> {esc(d['status'])} &nbsp; <b>Actor:</b> {esc(record.get('responsible_actor_id','—'))}
        &nbsp; <b>Root:</b> {esc(root or '—')} &nbsp; <b>Anomaly signals:</b> {len(run['anomalies'])}</p>
        <p>{esc(record.get('extensions',{}).get('rationale',d.get('reason','')))}</p>
        <table><thead><tr><th>Event</th><th>Actor</th><th>Type</th><th>Status</th><th>Elapsed ms</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
        <details><summary>Anomalies and prefix boundary</summary><pre>{esc(json.dumps(run['anomalies'],indent=2))}</pre></details>
        <details><summary>Assertions</summary><pre>{esc(json.dumps(run['assertions'],indent=2))}</pre></details>
        <details><summary>Diagnosis and evidence chain</summary><pre>{esc(json.dumps(d,indent=2))}</pre></details>
        <details><summary>Runtime measurements</summary><pre>{esc(json.dumps(run['metrics'],indent=2))}</pre></details>
        <details><summary>ICON intervention proposal (not executed)</summary><pre>{esc(json.dumps(run['intervention'],indent=2))}</pre></details>
        </section>''')
    nav = ' '.join(f'<a href="#{esc(r["case"])}">{esc(r["case"])}</a>' for r in report['runs'])
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
    <title>AgentOps prototype results</title><style>
    body{{font:16px system-ui;margin:40px auto;padding:0 24px;max-width:1200px;color:#172a43;background:#f7f9fb}}
    h1{{font-size:34px}}h2{{color:#087f73}}section{{background:white;padding:24px;margin:24px 0;border:1px solid #dce4ec;border-radius:8px}}
    nav a{{display:inline-block;margin:4px 12px 4px 0;color:#235f9e}}table{{width:100%;border-collapse:collapse;font-size:14px}}
    th,td{{padding:8px;border-bottom:1px solid #dce4ec;text-align:left}}.root{{background:#fff0e8}}details{{margin:16px 0}}
    pre{{overflow:auto;background:#f2f5f8;padding:16px}}.notice{{border-left:4px solid #b94943;padding:14px;background:#fff3f0}}
    </style><h1>AgentOps Observability and Failure Diagnosis</h1>
    <p>Controlled prototype v{esc(report['prototype_version'])}</p>
    <p class="notice">{esc(report['scope'])}<br>{esc(report['measurement_limits'])}</p>
    <p><b>{report['case_count']} scenarios</b> · {report['alarm_expectations_met']}/{report['case_count']} alarm expectations met ·
    {report['correct_actor_and_root_count']}/{report['failed_case_count']} failed cases correctly attributed · {report['abstention_count']} abstention</p>
    <nav>{nav}</nav>{''.join(sections)}</html>'''
