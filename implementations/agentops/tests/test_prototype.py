import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentops.analysis import Detector, diagnose, intervention_request
from agentops.cli import analyze
from agentops.contracts import ContractError, validate_trace, validate_diagnosis
from agentops.scenarios import CASES, run_scenario
from agentops.telemetry import Recorder, metrics, sanitize
from agentops.ui import render_html


class PrototypeTests(unittest.TestCase):
    def fixture(self, case):
        # Test logic independent of scheduler latency; demo measures real elapsed time separately.
        with patch('agentops.scenarios.time.sleep'):
            r, truth = run_scenario(case)
        for e in r.events:
            if 'duration_ms' in e.get('action', {}):
                e['action']['duration_ms'] = 80 if case == 'slow_call' and e['event_type'] == 'tool.result' else 1
        return r, truth

    def test_all_scenarios_alarm_and_outcome(self):
        for case in CASES:
            with self.subTest(case=case):
                r, truth = self.fixture(case)
                result = analyze(r.events)
                self.assertEqual(bool(result['anomalies']), truth['expected_alarm'])
                self.assertEqual(r.events[-1]['status'] == 'error', truth['task_failed'])

    def test_planner_responsibility_through_handoff(self):
        r, truth = self.fixture('planner_error')
        d = diagnose(r.events)['record']
        self.assertEqual(d['responsible_actor_id'], 'planner')
        self.assertEqual(d['root_cause_event_id'], truth['root_event_id'])
        self.assertEqual({x['role'] for x in d['failure_chain']}, {'root-cause','propagation','exposure','terminal'})

    def test_executor_deviation_keeps_responsibility(self):
        r, truth = self.fixture('executor_error')
        d = diagnose(r.events)['record']
        self.assertEqual(d['responsible_actor_id'], 'executor')
        self.assertEqual(d['root_cause_event_id'], truth['root_event_id'])

    def test_tool_failure_diagnosis(self):
        r, truth = self.fixture('tool_error')
        d = diagnose(r.events)['record']
        self.assertEqual(d['responsible_actor_id'], 'route-tool')
        self.assertEqual(d['root_cause_event_id'], truth['root_event_id'])

    def test_timeout_measurement(self):
        r, truth = self.fixture('timeout')
        self.assertEqual(metrics(r.events)['counts']['timeouts'], 1)
        self.assertEqual(diagnose(r.events)['record']['root_cause_event_id'], truth['root_event_id'])

    def test_retry_policy_root(self):
        r, truth = self.fixture('retry_exhausted')
        d = diagnose(r.events)['record']
        self.assertEqual(d['responsible_actor_id'], 'orchestrator')
        self.assertEqual(d['root_cause_event_id'], truth['root_event_id'])
        self.assertEqual(metrics(r.events)['counts']['retries'], 2)

    def test_recovered_error_is_not_terminal_failure(self):
        r, _ = self.fixture('recovered_error')
        result = analyze(r.events)
        self.assertTrue(result['anomalies'])
        self.assertEqual(result['diagnosis']['status'], 'not-applicable')

    def test_latency_violation_can_coexist_with_success(self):
        r, _ = self.fixture('slow_call')
        result = analyze(r.events)
        self.assertTrue(any('call-latency' in a['extensions']['rules'] for a in result['anomalies']))
        self.assertEqual(r.events[-1]['status'], 'ok')

    def test_missing_evidence_abstains(self):
        r, _ = self.fixture('missing_evidence')
        self.assertEqual(diagnose(r.events)['status'], 'abstain')

    def test_unrelated_failed_branch_is_not_selected(self):
        r,_ = self.fixture('tool_error')
        unrelated = copy.deepcopy(r.events[4])
        unrelated.update(event_id='unrelated',actor={'id':'other','kind':'agent'},sequence=1,event_type='tool.call',attributes={'route':'A'},parent_event_ids=[r.events[1]['event_id']])
        r.events.insert(4,unrelated)
        self.assertEqual(diagnose(r.events)['record']['responsible_actor_id'],'route-tool')

    def test_latency_approaching_boundary(self):
        r,_ = self.fixture('clean')
        event=next(e for e in r.events if e['event_type']=='model.response')
        event['action']['duration_ms']=40
        result=analyze(r.events)
        self.assertTrue(any(a['assertion_id']=='call-latency' and a['result']=='approaching' for a in result['assertions']))

    def test_prefix_boundary_and_no_future_references(self):
        r, _ = self.fixture('planner_error')
        d = Detector()
        visible = set()
        for e in r.events:
            visible.add(e['event_id'])
            a = d.consume(e)
            if a:
                self.assertTrue(set(a['candidate_event_ids']) <= visible)
                self.assertEqual(a['extensions']['prefix_size'], len(visible))
        self.assertLess(d.anomalies[0]['extensions']['prefix_size'], len(r.events))

    def test_future_suffix_does_not_change_prefix(self):
        r, _ = self.fixture('planner_error')
        prefix = r.events[:5]
        a,b = Detector(),Detector()
        for e in prefix:
            a.consume(copy.deepcopy(e)); b.consume(copy.deepcopy(e))
        for e in r.events[5:]:
            a.consume(e)
        selected = [{k:v for k,v in x.items() if k != 'detected_at'} for x in a.anomalies if x['extensions']['prefix_size'] <= 5]
        self.assertEqual(selected,[{k:v for k,v in x.items() if k != 'detected_at'} for x in b.anomalies])

    def test_duplicate_event_rejected(self):
        r,_ = self.fixture('clean')
        with self.assertRaisesRegex(ContractError,'duplicate'):
            validate_trace(r.events+[r.events[-1]])

    def test_broken_parent_rejected(self):
        r,_ = self.fixture('clean'); r.events[1]['parent_event_ids']=['absent']
        with self.assertRaisesRegex(ContractError,'parent'):
            validate_trace(r.events)

    def test_mixed_sessions_rejected(self):
        r,_ = self.fixture('clean'); r.events[-1]['session_id']='other'
        with self.assertRaisesRegex(ContractError,'sessions'):
            validate_trace(r.events)

    def test_actor_sequence_rejected(self):
        r,_ = self.fixture('clean'); r.events[-1]['sequence']=0
        with self.assertRaisesRegex(ContractError,'sequence'):
            validate_trace(r.events)

    def test_unsupported_major_version(self):
        r,_ = self.fixture('clean'); r.events[0]['schema_version']='2.0'
        with self.assertRaisesRegex(ContractError,'version'):
            validate_trace(r.events)

    def test_unknown_event_and_extensions_preserved(self):
        r,_ = self.fixture('clean'); r.events[2]['event_type']='vendor.custom';r.events[2]['vendor']={'x':1}
        validate_trace(r.events)
        self.assertEqual(analyze(r.events)['events'][2]['vendor'],{'x':1})

    def test_optional_attributes_can_be_omitted(self):
        r,_ = self.fixture('clean')
        for e in r.events:
            e.pop('attributes',None)
        validate_trace(r.events)
        self.assertEqual(analyze(r.events)['diagnosis']['status'],'not-applicable')

    def test_invalid_evidence_rejected(self):
        r,_ = self.fixture('planner_error'); d=diagnose(r.events)['record'];d['evidence_event_ids'].append('invented')
        with self.assertRaisesRegex(ContractError,'nonexistent'):
            validate_diagnosis(d,r.events)

    def test_wrong_chain_actor_rejected(self):
        r,_ = self.fixture('planner_error'); d=diagnose(r.events)['record'];d['failure_chain'][0]['actor_id']='executor'
        with self.assertRaisesRegex(ContractError,'actor'):
            validate_diagnosis(d,r.events)

    def test_nested_redaction(self):
        result=sanitize({'password':'never-export','nested':[{'Authorization':'Bearer hidden'}],'public':'hello'})
        self.assertNotIn('never-export',json.dumps(result));self.assertNotIn('Bearer hidden',json.dumps(result))
        self.assertEqual(result['public'],'hello')

    def test_call_exception_captured_without_secret_text(self):
        r=Recorder('test')
        with self.assertRaises(TimeoutError):
            with r.call('agent','tool','test-api'):
                raise TimeoutError('secret credential')
        self.assertEqual(r.events[-1]['status'],'error')
        self.assertNotIn('secret credential',json.dumps(r.events))
        self.assertGreaterEqual(r.events[-1]['action']['duration_ms'],0)

    def test_usage_is_preserved(self):
        r,_ = self.fixture('clean');m=metrics(r.events)
        self.assertEqual(m['counts']['token_input'],64)
        self.assertIn('simulated',m['token_source'])

    def test_intervention_is_proposal_only(self):
        r,_ = self.fixture('executor_error');result=analyze(r.events)
        self.assertEqual(result['intervention']['execution_status'],'not-executed')
        self.assertTrue(result['intervention']['requires_authorization'])

    def test_html_escapes_log_content(self):
        r,t = self.fixture('missing_evidence');result=analyze(r.events);result['case']='safe';result['diagnosis']['reason']='<script>alert(1)</script>'
        report={'runs':[result],'scope':'test','measurement_limits':'test','prototype_version':'test','case_count':1,'alarm_expectations_met':1,'correct_actor_and_root_count':0,'failed_case_count':1,'abstention_count':1}
        html=render_html(report)
        self.assertNotIn('<script>',html)
        self.assertIn('&lt;script&gt;',html)

    def test_replay_json_roundtrip(self):
        r,_ = self.fixture('planner_error')
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/'events.json';file.write_text(json.dumps(r.events))
            self.assertEqual(analyze(json.loads(file.read_text()))['diagnosis']['record']['responsible_actor_id'],'planner')


if __name__ == '__main__':
    unittest.main()
