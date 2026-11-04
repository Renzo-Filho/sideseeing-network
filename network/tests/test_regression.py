"""The pipeline still reproduces the published Morgan result (docs/RESULTS.md, phase 2b section 7): the phase 2b fit at
the measured camera height, re-run from its stored inputs and scored, must give the stored evaluation value for value.

It needs the local West Loop data (network/data/west_loop/) and about a minute of CPU, so it runs only on request:
    python -m pytest -m slow
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from walk2net.config import ROOT, Area

GRAPH = ROOT / 'data' / 'west_loop' / 'graph'
SESSIONS = ('2026-10-19-15-43-14-478', '2026-10-19-16-37-31-946')  # D1, Morgan
PUBLISHED = GRAPH / 'phase2b_h130'


def flat(tree, prefix=''):
    for key, value in tree.items():
        if isinstance(value, dict):
            yield from flat(value, f'{prefix}{key}.')
        else:
            yield f'{prefix}{key}', value


@pytest.mark.slow
@pytest.mark.skipif(not (PUBLISHED / 'eval' / 'summary.json').exists(), reason='needs the local West Loop data')
def test_the_published_morgan_fit_is_reproduced(tmp_path):
    from experiments import phase2b

    area = Area.load('west_loop')
    phase2b.fit(area, area.streets['morgan'], area.data / 'workspace', GRAPH / 'phase0' / 'rotation_windows.csv',
                GRAPH / 'phase2a' / 'prepared', GRAPH / 'phase2a_far', GRAPH / 'phase2b_measured', tmp_path, SESSIONS,
                height_m=1.30)
    subprocess.run([sys.executable, '-m', 'walk2net.evaluate.score', '--area', 'west_loop', '--street', 'morgan',
                    '--fit', str(tmp_path), '--out', str(tmp_path / 'eval')], cwd=ROOT, check=True, capture_output=True)
    for name in ('summary.json', 'eval/summary.json'):
        published = dict(flat(json.loads((PUBLISHED / name).read_text())))
        rerun = dict(flat(json.loads((tmp_path / name).read_text())))
        assert rerun == published, [key for key in published.keys() | rerun.keys() if published.get(key) != rerun.get(key)]
    assert (tmp_path / 'walking_lines.csv').read_text() == (PUBLISHED / 'walking_lines.csv').read_text()
