"""Render candidate-blind M3/M4 reference annotations for visual QA."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_reference_zones_v2_2026_09_27"
WORK = A / "work/chicago_m3_reference_zones_v2_2026_09_27"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", type=int, choices=[1, 2], default=1)
    args = parser.parse_args()
    refs = json.loads((OUT / f"visual_reference_v{args.version}.json").read_text())
    zones = json.loads((OUT / "zone_selection.json").read_text())["zones"]
    for zone in zones:
        zid = zone["zone_id"]
        image = Image.open(WORK / f"{zid}_ortho.jpg").convert("RGB")
        draw = ImageDraw.Draw(image)
        core = refs["core_bounds_px"]
        draw.rectangle(core, outline="red", width=3)
        for ref in refs["positive_polygons"]:
            if ref["zone_id"] != zid:
                continue
            draw.polygon([tuple(p) for p in ref["pixel_ring"]], outline="magenta", width=4)
            cx = sum(p[0] for p in ref["pixel_ring"]) / len(ref["pixel_ring"])
            cy = sum(p[1] for p in ref["pixel_ring"]) / len(ref["pixel_ring"])
            draw.rectangle((cx-32, cy-12, cx+32, cy+12), fill="white")
            draw.text((cx-30, cy-10), ref["id"].split("_")[-1], fill="black")
        for category, color in (("special_context_points", "orange"), ("negative_points", "yellow")):
            for ref in refs[category]:
                if ref["zone_id"] != zid:
                    continue
                x, y = ref["pixel_xy"]
                draw.ellipse((x-10, y-10, x+10, y+10), fill=color, outline="black", width=2)
        image.save(OUT / f"{zid}_reference_v{args.version}_overlay.png")


if __name__ == "__main__":
    main()
