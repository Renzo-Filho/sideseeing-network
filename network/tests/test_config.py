"""Areas, protocols and the field log are read from files (docs/ARCHITECTURE.md, section 3)."""
import pytest

from walk2net import fieldlog
from walk2net.config import PROTOCOLS, Area, Protocol, Street, utm_epsg


def test_the_projection_is_the_utm_zone_of_the_place():
    assert utm_epsg(-87.65, 41.88) == 32616   # Chicago
    assert utm_epsg(-46.63, -23.54) == 32723  # São Paulo
    assert Area.load('west_loop').crs == 32616


def test_a_street_knows_its_orientation():
    assert Area.load('west_loop').streets['morgan'].orientation == 'NS'
    assert Street('madison', 'Madison St', ((-87.67, 41.8819), (-87.64, 41.8820))).orientation == 'EW'


def test_protocols_give_the_road_side_and_the_side_of_the_out_leg():
    briefing, october, free = (Protocol.load(name) for name in ('briefing-2026-11', 'oct-2026', 'free-route'))
    assert briefing.road_side_along(0.0) == briefing.road_side_along('EW') == 'left'
    assert (briefing.out_side('NS'), briefing.out_side('EW')) == ('E', 'S')  # east side north, south side east
    assert (october.out_side('NS'), october.out_side('EW')) == ('E', 'N')    # the October plan: north side east
    assert free.road_side_along('NS') is None and free.out_side('EW') is None
    assert all(Protocol.load(path) for path in PROTOCOLS.glob('*.toml'))


def _log(tmp_path, text):
    path = tmp_path / 'field_log.csv'
    path.write_text(text)
    return path


def test_the_field_log_names_each_sessions_protocol(tmp_path):
    log = fieldlog.read(_log(tmp_path, 'session,label,protocol,camera_height_m\na,D1 S1,oct-2026,1.30\nb,D9 S1,briefing-2026-11,\n'))
    assert {s: p.name for s, p in fieldlog.protocols(log, ['a', 'b']).items()} == {'a': 'oct-2026', 'b': 'briefing-2026-11'}
    assert log.at['a', 'camera_height_m'] == 1.30
    with pytest.raises(AssertionError):
        fieldlog.protocols(log, ['c'])


@pytest.mark.parametrize('text', [
    'session,label,protocol,colector\na,D1 S1,oct-2026,x\n',   # a misspelt column
    'session,label\na,D1 S1\n',                                 # no protocol column
    'session,label,protocol\na,D1 S1,\n',                       # a session without its protocol
    'session,label,protocol\na,D1 S1,oct-2026\na,D1 S2,oct-2026\n',  # a session twice
])
def test_a_wrong_field_log_is_refused(tmp_path, text):
    with pytest.raises(AssertionError):
        fieldlog.read(_log(tmp_path, text))


def test_an_unknown_protocol_is_refused(tmp_path):
    with pytest.raises(FileNotFoundError):
        fieldlog.read(_log(tmp_path, 'session,label,protocol\na,D1 S1,nov-2099\n'))
