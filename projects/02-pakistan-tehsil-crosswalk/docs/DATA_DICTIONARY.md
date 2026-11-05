# Data dictionary

All population figures are persons as published; all areas are square kilometres as published. Years in column names are census years, and a column such as pop_1998_restated_2017 is PBS's own count of the 1998 population on the 2017 boundary.

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
| overlay_coverage | float | check only: share of the US Census Bureau Demobase 2017 polygon of the 2017 unit that falls inside the crosswalk's 2023 units (1 = the free polygon agrees with the crosswalk) |
| overlay_area_weight | float | check only: area share of the row from that overlay; blank where the 2017 polygon did not match |
| karachi_division | boolean | TRUE for the seven Karachi districts, so users can collapse Karachi to one unit |

## crosswalk_tehsil_1998_to_2017.csv (598 rows)
Same layout as above with the years shifted: unit_id_1998 (T98-nnnn, assigned in the order of the PCO 1951-98 report), province_1998, district_1998, unit_1998, unit_type_1998 (tehsil, sub_division, district for a Frontier Region, district_collapsed for Karachi, Lahore and Peshawar), pop_1998 (PCO report), then the 2017 unit columns, pop_1998_restated_2017 (the "POPULATION 1998" PBS printed for the 2017 unit), pop_2017, flow_1998 (persons of the 1998 count moved along the row), pop_weight, weight_basis (pbs_restatement_exact for same-name or one-to-one rows; pbs_restatement+milp_adjacency for rows opened by the solver), method (one_to_one, one_to_one_renamed, split, merge, split_and_merge), confidence, note, area_2017_km2, area_2017_source (pbs_2017_table1, or implied_from_pbs_2023_areas for Kohistan and Killa Saifullah where PBS printed no sub-district areas), area_weight, area_basis, area_1998_pco_km2 and area_1998_implied_km2 (check columns: the area printed in the 1951-98 report and the area implied by the crosswalk), frame_note_1998 (flags the three collapsed districts), karachi_division.

## crosswalk_tehsil_1998_to_2023.csv (678 rows)
The base-year table: 1998 units onto 2023 units, chained through 2017. Columns: the 1998 unit columns, the 2023 unit columns, flow_1998 (persons of the 1998 count, fractional because it multiplies two shares), pop_weight, area_weight, via_2017 (the 2017 unit(s) the row passes through), weight_basis, confidence (the lower of the two layers), frame_note_1998, karachi_division. There is no PBS restatement of 1998 on 2023 units, so no pop_1998_restated_2023 column exists.

## crosswalk_district_1998_to_2017.csv (142 rows), crosswalk_district_1998_to_2023.csv (151 rows)
Aggregated from the tehsil flows: province_1998, district_1998, province/district of the later frame, flow_1998, n_tehsil_rows, pop_1998, pop_weight, area_weight, relation (whole / part), confidence, karachi_division, and for 1998 -> 2017 pop_1998_restated_2017 and pop_2017; for 1998 -> 2023 pop_2023.

## new_district_lineage.csv
One row per (new district, earlier tehsil that contributed to it) for every district that first appears in the 2017 or 2023 frame. Columns: new_district, province, frame_first_seen, interval, parent_districts, source_tehsil, source_tehsil_id, source_tehsil_district, persons_from_tehsil, share_of_new_district (sums to 1 over the new district), share_of_source_tehsil, tehsil_upgraded (yes when a tehsil of the same name as the new district existed in the parent: the "Tehsil A became District A" case), confidence, and from the event register event_year, event_date, event_source_url, event_confidence.

## tehsil_district_membership.csv (1,435 rows)
For every earlier tehsil, the district(s) it falls in on the later frame: frame_from, frame_to, unit_id, province_from, district_from, unit_name, unit_type, pop_from, province_to, district_to, persons, share_of_tehsil, district_changed, tehsil_name_matches_new_district, confidence. Covers 1998 -> 2017, 2017 -> 2023 and 1998 -> 2023.

## event_register.csv
One row per dated change: province, level (district / tehsil), event_type (new_district, tehsil_upgraded_to_district, district_transfer, new_tehsil, renamed, merged, abolished), unit_name, parent_or_source_units, new_or_destination_units, year, date, interval (1998-2017, 2017-2023, post-2023), in_crosswalk (whether the change is visible between two census frames in these tables), notes (one plain sentence), source_url, source_title, confidence (verified: official notification or two independent news reports; reported: one news or Wikipedia source; unverified: not found, year blank).

## population_panel_1998_frame.csv (424 rows), population_panel_1998_frame_districts.csv (114 rows)
PCO's restatement of the 1951, 1961, 1972 and 1981 censuses on the 1998 frame, plus 1998: unit columns, pop_1951 .. pop_1998, avail_YYYY (pco, or "not separately printed (inside a parent unit)"), mark (PCO footnote mark), note.

## population_panel_2023_frame.csv (590 rows), population_panel_2023_frame_districts.csv (135 rows)
Every 2023 tehsil (district) at the seven censuses: pop_1951 .. pop_1998 (1998-frame figures pushed through the 1998 -> 2023 population weights), pop_2017 (PBS restatement on 2023 units), pop_2023 (count); flag_YYYY ("complete", or the 1998 source units with no PCO figure that year), method_pre_1998, karachi_division. District file adds the PBS district rows for 2017 and 2023 as a check.

## district_lineage_1951_1998.csv (128 rows)
province, district_1998, created_year, created_date, parent_districts_1998_names, former_names, existed_1951 / 1961 / 1972 / 1981 (yes / no / unclear), notes, source_url, source_title, confidence (verified / reported / unverified). Extra rows for historical units that are not 1998 districts (Hazara, Dir, Makran, Quetta-Pishin, Kachhi, Tamboo, Bolan Pass, Umerkot, Karachi East/West/South/Central/Malir).

## district_frames_by_census.csv
census_year, province, historical_district, status (district, princely state, Federal Capital Area, agency), n_1998_districts, members_1998, population (PCO, on 1998 boundaries), all_members_have_pco_figure.

## crosswalk_district_historical_to_1998.csv (479 rows), crosswalk_district_historical_to_2023.csv (604 rows)
census_year, province, historical_district, district_1998 (and tehsil_1998 where a two-parent district is split at tehsil level), pop_census_year_on_1998_unit, pop_historical_district, weight (sums to 1 over the historical district), weight_basis (pco_restatement_exact, or proxy_shares_from_YYYY), method, lineage_confidence, lineage_source, note. The 2023 file chains through the 1998 -> 2023 district weights: historical_district -> district_2023 with weight, persons_moved, via_1998, conf_1998_to_2023.

## unit_master_1998.csv (457 rows), district_master_1998.csv (114 rows)
The 1998 frame from the PCO 1951-98 report: province_1998, district_1998, unit_1998, unit_type_1998, pop_1998, pop_1981, pop_1972, pop_1961, pop_1951, area_km2, mark (the report's footnote marks), frame_note (the 36 Karachi, Lahore and Peshawar town rows), unit_id_1998. The crosswalk uses this file with the three town-frame districts collapsed to one unit each (build/intermediate/unit_master_1998_solved_frame.csv, 424 units).

## crosswalk_district_2017_to_2023.csv (143 rows)
Aggregated from the tehsil flows. pop_weight = share of the 2017 district's population in the 2023 district; area_weight from the tehsil area attributions; relation = whole (weight 1) or part; confidence = lowest confidence of the tehsil rows involved.

## unit_master_2017_all.csv, unit_master_2023_all.csv
Every unit (districts included) in PBS Table 1 of each census with area, population and the restated population of the previous census. Islamabad is included here but not in the crosswalk.

## check_overlay_mismatches.csv
2017 units whose Demobase 2017 polygon lies mostly (coverage below 0.5) outside the 2023 units the crosswalk assigns them to, with the 2023 units the polygon actually covers. These are label swaps and digitisation differences in the free polygon layer, documented so nobody uses that layer as a source of weights.

## Conventions
- Weights are shares of the earlier unit (forward direction). To move later-frame data back to earlier units, use flow / (restated population of the later unit) as the backward weight; it sums to 1 over each later unit. For the chained 1998 -> 2023 table the backward weight is flow_1998 divided by the sum of flow_1998 over the 2023 unit.
- Counts: multiply by the weight and sum. Rates and means: weighted average with the flow column as the weight. Shares of a total: rebuild numerator and denominator as counts.
- Ids: unit_id_1998 = T98-nnnn, unit_id_2017 = T17-nnnn (both assigned in this project), unit_id_2023 = PBS Digital Census dds_id. District files use district names as ids.
- Unit names are PBS's own spellings; "TALA GANG", "D.I.KHAN"-style variants were not altered.
