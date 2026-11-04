"""The field log (docs/FIELD_PROTOCOL.md, section 4): one row per recording, written by the researcher after each day.
It is an input, not just a record: it names each session's protocol. It stays local (data/<area>/field_log.csv): it
holds collectors' names.
"""
import pandas as pd

from walk2net.config import Protocol

REQUIRED = ('session', 'label', 'protocol')
OPTIONAL = ('leg', 'collector', 'phone', 'camera_height_m', 'start', 'end', 'deviations')


def read(path):
    """The log as a DataFrame indexed by session, checked: the known columns only, required values present, one row
    per session, every protocol defined in network/protocols/."""
    log = pd.read_csv(path, dtype=str, keep_default_na=False)
    unknown = set(log.columns) - set(REQUIRED) - set(OPTIONAL)
    missing = set(REQUIRED) - set(log.columns)
    assert not unknown and not missing, f'{path}: unknown columns {sorted(unknown)}, missing {sorted(missing)}'
    empty = log[list(REQUIRED)].eq('').any(axis=1)
    assert not empty.any(), f'{path}: rows without {"/".join(REQUIRED)}: {log.index[empty].tolist()}'
    assert log['session'].is_unique, f'{path}: sessions listed twice: {log["session"][log["session"].duplicated()].tolist()}'
    for name in log['protocol'].unique():
        Protocol.load(name)  # fails on a protocol with no definition
    if 'camera_height_m' in log:
        log['camera_height_m'] = pd.to_numeric(log['camera_height_m'].replace('', None))
    return log.set_index('session')


def protocols(log, sessions):
    """{session: Protocol} for `sessions`; every one must be in the log."""
    absent = [s for s in sessions if s not in log.index]
    assert not absent, f'sessions missing from the field log: {absent}'
    return {s: Protocol.load(log.at[s, 'protocol']) for s in sessions}
