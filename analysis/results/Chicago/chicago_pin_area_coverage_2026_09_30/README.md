# Chicago PIN area coverage by property class — 30 September 2026

Counts **PINs, not floor-area mass**. Script: `analysis/scripts/audit_chicago_pin_area_coverage.py`. Universe: 883,597 Chicago-linked Cook PINs (Assessor Parcel Universe 2024). A PIN "has area" if it appears with a positive area in Cook residential `char_bldg_sf`, condo `char_unit_sf` or `char_building_sf`, or commercial `bldgsf` (key PIN or listed PIN). Sources are not deduplicated beyond "any"; no areas are summed. DuPage is not included.

Result: 560,885 of 883,597 PINs (63.5%) have an area. By class group: residential class 2xx 69.0% (of 733,909; condo class 299 lacks area on 213,655 of 287,178), class 3 79.0%, class 5 84.9%, exempt (`EX`) **1.5%** of 49,958, vacant class 1 0.1% (no building expected), railroad (`R`) 0%. See `pin_area_coverage_by_class_group.csv`.

Limits: PIN share is not area share. Condo towers and exempt institutions carry large floor area and are the least covered; the area-weighted gap is unknown. Area definitions differ by source (exterior residential, unit, building, commercial building sf) and are not comparable.
