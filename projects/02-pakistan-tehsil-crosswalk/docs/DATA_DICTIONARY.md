# Data dictionary

## crosswalk_tehsil_2017_to_2023.csv (612 rows)
One row per (2017 unit, 2023 unit) pair with a positive flow. A 2017 unit that was not split has one row with both weights = 1.

| Column | Type | Meaning |
|---|---|---|
| district_group | text | the set of districts inside which the units were matched (Data Darbar group label; "A + B" where districts merged, split or exchanged territory) |
| unit_id_2017 | text | stable id of the 2017 unit, T17-nnnn, assigned in this project in the order of the PBS 2017 tables (province, district, unit) |
| province_2017 | text | province in the 2017 frame: PUNJAB, SINDH, KHYBER PAKHTUNKHWA, BALOCHISTAN, FATA |
| district_2017 | text | district (or agency / FR) as printed in PBS Census 2017 Table 1 |
| unit_2017 | text | sub-district unit name as printed in PBS Census 2017 Table 1 (TEHSIL, TALUKA, SUB-DIVISION, SUB-TEHSIL suffixes kept) |
| unit_type_2017 | text | tehsil, sub_division, sub_tehsil, other |
| pop_2017 | integer | population 2017, PBS Census 2017 Table 1 |
| unit_id_2023 | text | PBS Digital Census 2023 unit id (DDS-PP-nnnn); one polygon per unit in the 2023 boundary file |
| province_2023, district_2023, unit_2023, unit_type_2023 | text | as printed in PBS Census 2023 Table 1 |
| pop_2017_restated_2023 | integer | "POPULATION 2017" printed for the 2023 unit in PBS Census 2023 Table 1 (PBS's own restatement) |
| pop_2023 | integer | population 2023, PBS Census 2023 Table 1 |
| pop_weight | float | share of the 2017 unit's 2017 population that lies in the 2023 unit; sums to 1 over the 2017 unit. Use for counts. |
| weight_basis | text | pbs_restatement: weight = restated population of the 2023 unit / 2017 population of the parent (or the one-way transfer residual); pbs_restatement+lp_adjacency: the group did not balance by name, flow found by transportation LP with 2023-polygon adjacency costs |
| confidence | text | high: pair determined by name and equal population, or by a unique balancing partition; medium: involves an inferred transfer or an LP allocation |
| note | text | plain-language reason for the row |
| area_2023_km2 | float | area of the 2023 unit, PBS Census 2023 Table 1 |
| flow_2017 | integer | people (2017 count) moved along the row = pop_weight x pop_2017 |
| area_weight | float | share of the 2017 unit's land in the 2023 unit; sums to 1 over the 2017 unit. Use for land-based variables. |
| area_basis | text | identity; pbs_area_2023_exact (published areas of the children); pbs_area_2023_uniform_density (2023 unit's area split between sources in proportion to people) |
| overlay_area_weight | float | check only: area share from overlaying a geoBoundaries 2017 polygon on the 2023 polygons, where that polygon matched and covered the row's 2023 units by >= 90%; blank otherwise |
| overlay_coverage | float | share of the geoBoundaries 2017 polygon's area that falls in the crosswalk's 2023 units |
| karachi_division | boolean | TRUE for the seven Karachi districts, so users can collapse Karachi to one unit |

## crosswalk_district_2017_to_2023.csv (143 rows)
Aggregated from the tehsil flows. pop_weight = share of the 2017 district's population in the 2023 district; area_weight from the tehsil area attributions; relation = whole (weight 1) or part; confidence = lowest confidence of the tehsil rows involved.

## unit_master_2017_all.csv, unit_master_2023_all.csv
Every unit (districts included) in PBS Table 1 of each census with area, population and the restated population of the previous census. Islamabad is included here but not in the crosswalk.

## check_overlay_disagreements.csv
For split 2017 units with a matched geoBoundaries polygon: 2023 units that polygon overlaps by more than 2% of its area but which are not in the unit's crosswalk rows. Documents the limits of the geoBoundaries layer.

## Conventions
- Weights are shares of the 2017 unit (forward direction, 2017 -> 2023). To move 2023 data back to 2017 units, use flow_2017 / pop_2017_restated_2023 as the backward weight (share of the 2023 unit's 2017 population that came from each 2017 unit); it sums to 1 over each 2023 unit.
- Counts: multiply by the weight and sum. Rates and means: weighted average with flow_2017 as the weight. Shares of a total: rebuild numerator and denominator as counts.
- Unit names are PBS's own spellings; "TALA GANG", "D.I.KHAN"-style variants were not altered.
