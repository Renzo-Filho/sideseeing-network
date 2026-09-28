"""Topology-constrained candidate junction complexes for paired review.

This groups source connector candidates linked by a short *eligible road segment*.
It does not certify physical street arms or accepted M2 junctions.
"""

import math

import numpy as np


def short_connector_links(roads, connectors, max_link_m=20.0):
    """Return unique candidate pairs joined consecutively on one short road span.

    A nearby coordinate or planar crossing alone never creates a link. Both
    endpoints must be supplied connector IDs in the candidate table.
    """
    if max_link_m <= 0:
        raise ValueError("max_link_m must be positive")
    if not roads.id.is_unique or not connectors.id.is_unique:
        raise ValueError("Source IDs must be unique")
    points = {row.id: (row.geometry.x, row.geometry.y) for row in connectors.itertuples()}
    links = {}
    for row in roads.itertuples():
        raw = [(float(link["at"]), link["connector_id"]) for link in row.connectors]
        if any(not math.isfinite(at) or at < 0 or at > 1 for at, _ in raw):
            raise ValueError("Invalid connector position")
        ordered = sorted(set(raw))
        length = row.geometry.length
        for (start, a), (end, b) in zip(ordered, ordered[1:]):
            if a == b or a not in points or b not in points:
                continue
            span = (end - start) * length
            if span <= 0 or span > max_link_m:
                continue
            ax, ay = points[a]
            bx, by = points[b]
            straight = math.hypot(ax - bx, ay - by)
            if straight > max_link_m:
                continue
            key = tuple(sorted((a, b)))
            old = links.get(key)
            if old is None or span < old["along_road_m"]:
                links[key] = {"connector_a": key[0], "connector_b": key[1],
                              "along_road_m": span, "straight_m": straight,
                              "road_id": row.id}
    return sorted(links.values(), key=lambda x: (x["connector_a"], x["connector_b"]))


def linked_components(connectors, links, max_diameter_m=35.0):
    """Group linked candidates; flag chains larger than a single local complex."""
    if max_diameter_m <= 0:
        raise ValueError("max_diameter_m must be positive")
    points = {row.id: (row.geometry.x, row.geometry.y) for row in connectors.itertuples()}
    parent = {key: key for key in points}

    def find(key):
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    for link in links:
        a, b = link["connector_a"], link["connector_b"]
        if a not in parent or b not in parent:
            raise ValueError("Link endpoint absent from candidate table")
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    groups = {}
    for key in points:
        groups.setdefault(find(key), []).append(key)
    result = []
    for members in groups.values():
        if len(members) < 2:
            continue
        members = sorted(members)
        coords = np.asarray([points[key] for key in members])
        diameter = float(max(np.linalg.norm(coords[i] - coords[j])
                             for i in range(len(coords)) for j in range(i + 1, len(coords))))
        result.append({"connector_ids": members, "count": len(members),
                       "diameter_m": diameter,
                       "within_diameter_cap": diameter <= max_diameter_m})
    return sorted(result, key=lambda x: (-x["count"], x["connector_ids"]))
