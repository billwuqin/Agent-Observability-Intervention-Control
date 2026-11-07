"""Run the suite and regenerate measured evidence before a demo/release."""
import io
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from agentops.cli import demo

if __name__ == '__main__':
    out = Path('artifacts')
    out.mkdir(exist_ok=True)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.discover('tests'))
    (out/'tests.txt').write_text(stream.getvalue(), encoding='utf-8')
    record = {'executed_at': datetime.now(timezone.utc).isoformat(), 'tests_run': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped), 'passed': result.wasSuccessful()}
    (out/'validation.json').write_text(json.dumps(record,indent=2)+'\n', encoding='utf-8')
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise SystemExit(1)
    demo(out)
