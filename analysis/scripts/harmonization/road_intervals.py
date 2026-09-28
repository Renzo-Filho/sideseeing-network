"""Interval-aware road portions for diagnostic block-boundary construction.

Overture ``between`` values are normalized distances along a segment. An absent
``between`` applies to the full segment. This is a candidate visual boundary
rule, not a certified physical-block definition.
"""

from shapely.ops import substring


def _span(rule):
    value = rule.get("between")
    if value is None:
        return 0.0, 1.0
    if len(value) != 2:
        raise ValueError("Road rule requires two between endpoints")
    start, end = map(float, value)
    if not (0 <= start <= end <= 1):
        raise ValueError("Road rule between must be ordered in [0, 1]")
    return start, end


def _active(rule, at):
    start, end = _span(rule)
    return start <= at <= end


def boundary_parts(geometry, *, subclass=None, subclass_rules=None,
                   level_rules=None, road_flags=None):
    """Retain source-road parts lacking explicit link or elevated/covered status.

    Missing level/flag data remain in this diagnostic; level zero itself is a
    visual Z-order and does not prove the road is at ground level.
    """
    if geometry is None or geometry.is_empty or geometry.length == 0:
        return []
    if subclass == "link":
        return []
    groups = (subclass_rules or [], level_rules or [], road_flags or [])
    stops = {0.0, 1.0}
    for rules in groups:
        for rule in rules:
            stops.update(_span(rule))
    ordered = sorted(stops)
    parts = []
    for start, end in zip(ordered, ordered[1:]):
        if end <= start:
            continue
        at = (start + end) / 2
        if any(rule.get("value") == "link" and _active(rule, at)
               for rule in subclass_rules or []):
            continue
        if any(rule.get("value") not in (None, 0) and _active(rule, at)
               for rule in level_rules or []):
            continue
        if any(bool({"is_bridge", "is_tunnel", "is_link", "is_covered"} &
                    set(rule.get("values") or [])) and _active(rule, at)
               for rule in road_flags or []):
            continue
        part = substring(geometry, start, end, normalized=True)
        if part.geom_type == "LineString" and part.length > 0:
            parts.append(part)
    return parts
