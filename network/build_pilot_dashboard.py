"""Quick-overview SideSeeing dashboard for the pilot: sensors, Wi-Fi and raw GPS only.

Run with the sideseeing-tools venv from the repo root:
    ../sideseeing-tools/venv/bin/python network/build_pilot_dashboard.py [--serve]

Skipped on purpose (large runs): frame extraction, anonymization, SAM3 segmentation,
OSRM map matching (it also snaps GPS, which Study 1 forbids) and assessment events.
"""
import sys
from pathlib import Path

from sideseeing_tools.export import Report
from sideseeing_tools.sideseeing import SideSeeingDS
from sideseeing_tools.workspace import SideSeeingWorkspace

ROOT = Path(__file__).resolve().parents[1] / 'data'
WS = ROOT / 'pilot_workspace'

SideSeeingWorkspace(str(WS)).setup_data_directory(SideSeeingDS(str(ROOT / 'pilot')))  # symlinks, no copies
Report().generate_report(input_dir=str(WS), output_dir=str(WS / 'report'),
                         title='Near West Side pilot, 14 Oct 2026', metadata_csv=str(WS / 'metadata.csv'))

if '--serve' in sys.argv:  # same report behind the Dataviz server; do not press "Extract Frames"
    from sideseeing_tools.dataviz import start_server
    start_server(input_dir=str(WS), output_dir=str(WS / 'report'), port=5000, host='127.0.0.1')
