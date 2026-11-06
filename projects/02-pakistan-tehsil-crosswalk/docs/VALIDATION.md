# Validation report: Pakistan tehsil crosswalk, Census 2017 to Census 2023

Revised 5 November 2026 (third release): the layer was re-solved with the same resolver as the 1998 layer so that all layers share one method and one grading of every row.

(The 1998 layer has its own report, VALIDATION_1998.md.)

Built 3 November 2026. Scope: Punjab, Sindh, Khyber Pakhtunkhwa (including the former FATA, which the 2023 frame places inside KP) and Balochistan. Islamabad, AJK and Gilgit-Baltistan are excluded.

## 1. Completeness
- 2017 frame: 535 of 535 sub-district units (tehsils, talukas, sub-divisions, sub-tehsils) appear in the crosswalk.
- 2023 frame: 590 of 590 sub-district units appear.
- Districts: 134 of 134 (2017, incl. 7 FATA agencies and 6 Frontier Regions) and 135 of 135 (2023).
- Rows: 612 tehsil rows, 143 district rows.

## 2. Weight checks
- Population weights sum to 1 for every 2017 unit (max deviation 3.3e-16).
- Area weights sum to 1 for every 2017 unit (max deviation 3.3e-16).

## 3. Conservation
Pushing PBS's 2017 population of every 2017 unit through the population weights reproduces, for every 2023 unit, the "POPULATION 2017" column PBS printed in Census 2023 Table 1 (max deviation 0 persons), and for every 2023 district its restated 2017 total. Provincial totals:

| Province (2023 frame) | Crosswalk | PBS Census 2023 Table 1, Population 2017 | PBS Census 2017 Table 1 |
|---|---|---|---|
| BALOCHISTAN | 12,335,129 | 12,335,129 | 12,335,129 |
| KHYBER PAKHTUNKHWA | 35,501,964 | 35,501,964 | 35,501,964 |
| PUNJAB | 109,989,655 | 109,989,655 | 109,989,655 |
| SINDH | 47,854,510 | 47,854,510 | 47,854,510 |

This is exact by construction: the weights are PBS's own restated populations divided by the 2017 populations. The substantive check is therefore the one PBS implicitly made when it restated 2017 onto the 2023 units; the crosswalk cannot be more accurate than that restatement. Where PBS's restatement differs from the 2017 count for a unit whose published area is unchanged (for example Dera Ismail Khan, Paharpur and Paroa tehsils, where areas are identical in both censuses but the three 2017 populations move by -5,229, +18,480 and -13,251), the restatement may reflect block reassignments or corrections rather than a boundary change; the crosswalk records it as a transfer with confidence "medium".

## 4. How each unit was matched
One procedure for every district group (build/crosswalk_lib.py, used for both the 2017 -> 2023 and 1998 -> 2017 layers). Within a group the flows from 2017 units to 2023 units must reproduce both the 2017 populations and PBS's restated 2017 populations exactly, and the solver opens as few unexpected cells as possible: same-named pairs cost almost nothing, a pair whose 2023 unit touches the polygon of the 2017 unit's namesake costs more, non-adjacent pairs more still (fixed-charge transportation problem, solved exactly with scipy's MILP). A same-named pair with identical population in both tables is treated as unchanged, and district-level flows are imposed on the tehsil solve where they are unambiguous. Every opened cell that is not a same-name pair is then graded by re-solving with that cell forbidden:
- **forced** (confidence high): the group cannot balance without it, so the flow is an arithmetic consequence of PBS's figures;
- **inferred** (confidence medium): another balancing allocation exists but is less parsimonious under the adjacency prior; the flow is an inference, not a PBS figure;
- **ambiguous** (confidence low): an equally parsimonious alternative exists; the note names it.

Result: 479 of 535 2017 units map to exactly one 2023 unit; 56 are split; 22 2023 units draw from more than one 2017 unit. Rows by grade: {'high': 580, 'medium': 33}. Rows by basis: {'pbs_restatement_exact': 525, 'pbs_restatement+milp_adjacency': 88}. Compared with the first release (exact partitions plus a transportation LP for ten groups), 584 of 612 rows are unchanged and 724,678 persons (0.35 percent) are allocated differently, all inside eight of those ten groups (Abbottabad, D.I. Khan + FR D.I. Khan, Kachhi + Nasirabad, Kohistan, Mardan, Musakhel, Quetta, Torghar); the first-release file is kept as build/intermediate/crosswalk_tehsil_2017_to_2023_pop_v1.csv and the differences in compare_2017_2023_v1_vs_milp.csv.

## 5. Area weights
Area weights come from PBS's published areas of the 2023 units (Census 2023 Table 1). For one-to-one rows and pure splits they are exact published areas. For the 35 rows where a 2023 unit draws people from more than one 2017 unit, the 2023 unit's area is divided between the sources in proportion to the people each contributed (uniform density within the 2023 unit); area_basis flags these as pbs_area_2023_uniform_density.

As an independent check, a 2017-vintage tehsil polygon layer (geoBoundaries PAK ADM3, boundaryYearRepresented 2017, sourced from Pathways Data / PBS) was overlaid on the 2023 polygons for the split units where its polygon could be matched by name and covered the crosswalk's 2023 units by at least 90%. The overlay agrees with the published-area weights within 0.1 for most such units but disagrees materially for Chitral, Nushki, Alpuri, Dir, Chattar and Pattan (column overlay_area_weight). The geoBoundaries layer mixes vintages (its Jhang still contains Chiniot; its Kharan covers Washuk; its Peshawar polygon is the FR Peshawar area), so it is not used as a source. A PBS-supplied 2017 tehsil shapefile would replace this check with a measurement.

## 6. Spot checks against known events
| Event | Crosswalk | Source status |
|---|---|---|
| FATA merged into KP (25th Amendment, May 2018); agencies became districts, Frontier Regions became sub-divisions of settled districts | 7 agencies map one-to-one to the 7 new districts; FR Bannu -> Wazir Sub-Division (Bannu), FR Peshawar -> Hassan Khel (Peshawar), FR Kohat -> Darra Adam Khel (Kohat), FR Lakki -> Bettani (Lakki Marwat), FR Tank -> Jandola (Tank), FR D.I.Khan -> Drazanda (D.I. Khan), all with equal populations | Structure visible in PBS Census 2023 Table 1 (opened); the amendment itself not re-verified here |
| Kohistan split into Upper Kohistan, Lower Kohistan (2014) and Kolai-Palas (2017) | 4 2017 sub-divisions -> 8 2023 units across the three districts; populations balance after small transfers into Kandia | Dates from Wikipedia citing Dawn and The News (not opened); PBS tables confirm the 2023 structure |
| Chitral split into Lower and Upper Chitral (2018) | Chitral Sub-Division -> Chitral + Drosh (Lower Chitral); Mastuj -> Upper Chitral, one-to-one | PBS tables; notification not verified |
| Karachi West split, Keamari District created (2020) | Baldia, Mauripur, SITE and Harbour (renamed Keamari) sub-divisions move whole to Keamari; populations unchanged | PBS tables; notification not verified |
| Kalat split, Surab District (Balochistan) | Surab Tehsil -> Surab + Gidder sub-divisions (balances exactly); Kalat Tehsil -> Kalat, Dasht-e-Goran, Shaheed Meharabad Zehri | PBS tables; notification not verified |
| Killa Abdullah split, Chaman District | Chaman Tehsil -> Chaman City + Chaman Saddar sub-divisions (balances exactly) | PBS tables; notification not verified |
| Loralai split, Duki District | Duki Tehsil -> Duki, Luni, Talao, Thal Chutyali (balances exactly) | PBS tables; notification not verified |
| Punjab's five new districts of October 2022 (Murree, Talagang, Wazirabad, Kot Addu, Taunsa) | Not in the 2023 census frame: PBS tabulated Census 2023 on the pre-2022 Punjab districts (Murree remains a tehsil of Rawalpindi, etc.). The crosswalk follows the census frame. | Dawn 16 Oct 2022 (opened) for the notifications; PBS Census 2023 Punjab tables for the frame |
| Kot Addu Tehsil split, Chowk Sarwar Shaheed Tehsil | Kot Addu -> Kot Addu + Chowk Sarwar Shaheed (balances exactly) | PBS tables; notification not verified |
| Peshawar Tehsil split into six tehsils | Peshawar Tehsil -> Peshawar, Badhber, Cham Kani, Mathra, Pishta Khara, Shah Alam (balances exactly) | PBS tables; notification not verified |

## 7. Name matching
All 2017-to-2023 pairs were matched on exact unit names within the district, or on PBS populations where names changed; no fuzzy string matching was used. Renamed pairs (78) and their matching key are listed in the crosswalk notes (e.g. Harbour Sub-Division -> Keamari Sub-Division, matched by population 401,115; Phelawagh Tehsil -> Qadirabad Sub-Division, 28,054). The grouping of units into territory-covering groups follows Data Darbar's subdistrict_crosswalk_2017_2023 (release 2026-11-01), and every group was re-verified here against the PBS populations.

## 8. Open items
1. PBS's 2017 restatement has no published method note. Whether it is an exact re-aggregation of 2017 census blocks or a proration cannot be told from the tables; the D.I. Khan case above suggests adjustments beyond boundary changes in at least some districts.
2. A PBS 2017 tehsil shapefile (or the 2017 block layer with tehsil codes) would turn the inferred rows and the uniform-density area rows into measured figures. Request to PBS pending Professor Khan's go-ahead.
3. Effective dates: the splits in section 6 and every other district change are now dated, with sources, in output/event_register.csv and docs/EVENT_REGISTER.md (second release). The weights themselves still rest on the census tables.

## 9. Every split and transfer row
| district_group | unit_2017 | pop_2017 | unit_2023 | pop_2017_restated_2023 | pop_weight | area_weight | method | confidence | note |
|---|---|---|---|---|---|---|---|---|---|
| ABBOTTABAD DISTRICT | ABBOTTABAD TEHSIL | 982,837 | ABBOTTABAD TEHSIL | 939,576 | 0.9390 | 0.8919 | split_and_merge | high | same name |
| ABBOTTABAD DISTRICT | ABBOTTABAD TEHSIL | 982,837 | LOWER TANAWAL TEHSIL | 59,912 | 0.0610 | 0.1081 | split | high | 59,912 persons (source-year count) of ABBOTTABAD TEHSIL fall in LOWER TANAWAL TEHSIL (cell cost 2.18); forced: the group cannot balance without this cell |
| ABBOTTABAD DISTRICT | HAVELIAN TEHSIL | 350,252 | ABBOTTABAD TEHSIL | 939,576 | 0.0475 | 0.0413 | split_and_merge | high | 16,651 persons (source-year count) of HAVELIAN TEHSIL fall in ABBOTTABAD TEHSIL (cell cost 2.50); forced: the group cannot balance without this cell |
| ABBOTTABAD DISTRICT | HAVELIAN TEHSIL | 350,252 | HAVELIAN TEHSIL | 235,725 | 0.6730 | 0.6198 | split | high | same name |
| ABBOTTABAD DISTRICT | HAVELIAN TEHSIL | 350,252 | LORA TEHSIL | 97,876 | 0.2794 | 0.3389 | split | medium | 97,876 persons (source-year count) of HAVELIAN TEHSIL fall in LORA TEHSIL (cell cost 2.59); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| AWARAN DISTRICT | JHAL JAO SUB-TEHSIL | 40,010 | JHAL JAO TEHSIL | 21,491 | 0.5371 | 0.6760 | split | high | same name |
| AWARAN DISTRICT | JHAL JAO SUB-TEHSIL | 40,010 | KORAK JHAO TEHSIL | 18,519 | 0.4629 | 0.3240 | split | high | 18,519 persons (source-year count) of JHAL JAO SUB-TEHSIL fall in KORAK JHAO TEHSIL (cell cost 2.31); forced: the group cannot balance without this cell |
| BAHAWALNAGAR DISTRICT | CHISHTIAN TEHSIL | 689,766 | CHISHTIAN TEHSIL | 697,125 | 1.0000 | 1.0000 | merge | high | same name |
| BAHAWALNAGAR DISTRICT | HAROONABAD TEHSIL | 524,715 | CHISHTIAN TEHSIL | 697,125 | 0.0140 | 0.0121 | split_and_merge | high | 7,359 persons (source-year count) of HAROONABAD TEHSIL fall in CHISHTIAN TEHSIL (cell cost 2.46); forced: the group cannot balance without this cell |
| BAHAWALNAGAR DISTRICT | HAROONABAD TEHSIL | 524,715 | HAROONABAD TEHSIL | 517,356 | 0.9860 | 0.9879 | split | high | same name |
| BANNU DISTRICT + FR BANNU | BANNU TEHSIL | 958,103 | BAKKA KHEL TEHSIL | 168,300 | 0.1757 | 0.4576 | split | high | 168,300 persons (source-year count) of BANNU TEHSIL fall in BAKKA KHEL TEHSIL (cell cost 2.75); forced: the group cannot balance without this cell |
| BANNU DISTRICT + FR BANNU | BANNU TEHSIL | 958,103 | BANNU TEHSIL | 563,374 | 0.5880 | 0.2843 | split | high | same name |
| BANNU DISTRICT + FR BANNU | BANNU TEHSIL | 958,103 | KAKKI TEHSIL | 82,265 | 0.0859 | 0.0823 | split | high | 82,265 persons (source-year count) of BANNU TEHSIL fall in KAKKI TEHSIL (cell cost 2.12); forced: the group cannot balance without this cell |
| BANNU DISTRICT + FR BANNU | BANNU TEHSIL | 958,103 | MERYAN TEHSIL | 144,164 | 0.1505 | 0.1758 | split | high | 144,164 persons (source-year count) of BANNU TEHSIL fall in MERYAN TEHSIL (cell cost 2.63); forced: the group cannot balance without this cell |
| BUNER DISTRICT | DAGGAR TEHSIL | 354,809 | DAGGAR TEHSIL | 176,049 | 0.4962 | 0.3806 | split | high | same name |
| BUNER DISTRICT | DAGGAR TEHSIL | 354,809 | GADEZAI TEHSIL | 178,760 | 0.5038 | 0.6194 | split | high | 178,760 persons (source-year count) of DAGGAR TEHSIL fall in GADEZAI TEHSIL (cell cost 2.14); forced: the group cannot balance without this cell |
| BUNER DISTRICT | GAGRA TEHSIL | 269,971 | CHAGHARZAI TEHSIL | 109,291 | 0.4048 | 0.5011 | split | medium | 109,291 persons (source-year count) of GAGRA TEHSIL fall in CHAGHARZAI TEHSIL (cell cost 2.55); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| BUNER DISTRICT | GAGRA TEHSIL | 269,971 | GAGRA TEHSIL | 160,680 | 0.5952 | 0.4989 | split | high | same name |
| CHAGAI DISTRICT | DALBANDIN TEHSIL | 127,468 | DALBANDIN SUB-DIVISION | 106,643 | 0.8366 | 0.5071 | split | high | same name |
| CHAGAI DISTRICT | DALBANDIN TEHSIL | 127,468 | YAK MACHH SUB-TEHSIL | 20,825 | 0.1634 | 0.4929 | split | high | 20,825 persons (source-year count) of DALBANDIN TEHSIL fall in YAK MACHH SUB-TEHSIL (cell cost 2.39); forced: the group cannot balance without this cell |
| CHAKWAL DISTRICT | LAWA TEHSIL | 125,770 | LAWA TEHSIL | 117,929 | 0.9377 | 0.9592 | split | high | same name |
| CHAKWAL DISTRICT | LAWA TEHSIL | 125,770 | TALA GANG TEHSIL | 409,827 | 0.0623 | 0.0408 | split_and_merge | high | 7,841 persons (source-year count) of LAWA TEHSIL fall in TALA GANG TEHSIL (cell cost 2.47); forced: the group cannot balance without this cell |
| CHAKWAL DISTRICT | TALA GANG TEHSIL | 401,986 | TALA GANG TEHSIL | 409,827 | 1.0000 | 1.0000 | merge | high | same name |
| CHARSADDA DISTRICT | CHARSADDA TEHSIL | 804,843 | CHARSADDA TEHSIL | 809,660 | 1.0000 | 1.0000 | merge | high | same name |
| CHARSADDA DISTRICT | TANGI TEHSIL | 426,165 | CHARSADDA TEHSIL | 809,660 | 0.0113 | 0.0076 | split_and_merge | high | 4,817 persons (source-year count) of TANGI TEHSIL fall in CHARSADDA TEHSIL (cell cost 2.51); forced: the group cannot balance without this cell |
| CHARSADDA DISTRICT | TANGI TEHSIL | 426,165 | TANGI TEHSIL | 421,348 | 0.9887 | 0.9924 | split | high | same name |
| CHITRAL DISTRICT | CHITRAL SUB-DIVISION | 278,328 | CHITRAL SUB-DIVISION | 183,178 | 0.6581 | 0.9487 | split | high | same name |
| CHITRAL DISTRICT | CHITRAL SUB-DIVISION | 278,328 | DROSH SUB-DIVISION | 95,150 | 0.3419 | 0.0513 | split | high | 95,150 persons (source-year count) of CHITRAL SUB-DIVISION fall in DROSH SUB-DIVISION (cell cost 1.95); forced: the group cannot balance without this cell |
| DERA ISMAIL KHAN DISTRICT + FR D.I.KHAN | DERA ISMAIL KHAN TEHSIL | 725,449 | DERA ISMAIL KHAN TEHSIL | 730,678 | 0.8873 | 0.6892 | split_and_merge | high | same name |
| DERA ISMAIL KHAN DISTRICT + FR D.I.KHAN | DERA ISMAIL KHAN TEHSIL | 725,449 | PAROA TEHSIL | 305,594 | 0.1127 | 0.3108 | split_and_merge | high | 81,757 persons (source-year count) of DERA ISMAIL KHAN TEHSIL fall in PAROA TEHSIL (cell cost 2.61); forced: the group cannot balance without this cell |
| DERA ISMAIL KHAN DISTRICT + FR D.I.KHAN | PAHARPUR TEHSIL | 381,086 | DERA ISMAIL KHAN TEHSIL | 730,678 | 0.0485 | 0.0175 | split_and_merge | high | 18,480 persons (source-year count) of PAHARPUR TEHSIL fall in DERA ISMAIL KHAN TEHSIL (cell cost 2.31); forced: the group cannot balance without this cell |
| DERA ISMAIL KHAN DISTRICT + FR D.I.KHAN | PAHARPUR TEHSIL | 381,086 | PAHARPUR TEHSIL | 362,606 | 0.9515 | 0.9825 | split | high | same name |
| DERA ISMAIL KHAN DISTRICT + FR D.I.KHAN | PAROA TEHSIL | 292,343 | DRAZANDA SUB-DIVISION | 68,506 | 0.2343 | 0.6127 | split | high | 68,506 persons (source-year count) of PAROA TEHSIL fall in DRAZANDA SUB-DIVISION (cell cost 2.74); forced: the group cannot balance without this cell |
| DERA ISMAIL KHAN DISTRICT + FR D.I.KHAN | PAROA TEHSIL | 292,343 | PAROA TEHSIL | 305,594 | 0.7657 | 0.3873 | split_and_merge | high | same name |
| DERA ISMAIL KHAN DISTRICT + FR D.I.KHAN | TRIBAL AREA ADJ. DERA ISMAIL KHAN DISTRICT | 68,506 | DERA ISMAIL KHAN TEHSIL | 730,678 | 1.0000 | 1.0000 | merge | high | same name |
| FR KOHAT + KOHAT DISTRICT | KOHAT TEHSIL | 848,997 | GUMBAT TEHSIL | 112,340 | 0.1323 | 0.3557 | split | medium | 112,340 persons (source-year count) of KOHAT TEHSIL fall in GUMBAT TEHSIL (cell cost 2.63); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| FR KOHAT + KOHAT DISTRICT | KOHAT TEHSIL | 848,997 | KOHAT TEHSIL | 736,657 | 0.8677 | 0.6443 | split | high | same name |
| FR LAKKI MARWAT + LAKKI MARWAT DISTRICT | LAKKI MARWAT TEHSIL | 578,874 | GHAZNI KHEL TEHSIL | 295,984 | 0.5113 | 0.4538 | split | high | 295,984 persons (source-year count) of LAKKI MARWAT TEHSIL fall in GHAZNI KHEL TEHSIL (cell cost 2.50); forced: the group cannot balance without this cell |
| FR LAKKI MARWAT + LAKKI MARWAT DISTRICT | LAKKI MARWAT TEHSIL | 578,874 | LAKKI MARWAT TEHSIL | 282,890 | 0.4887 | 0.5462 | split | high | same name |
| FR PESHAWAR + PESHAWAR DISTRICT | PESHAWAR TEHSIL | 4,267,198 | BADHBER TEHSIL | 384,916 | 0.0902 | 0.2840 | split | high | 384,916 persons (source-year count) of PESHAWAR TEHSIL fall in BADHBER TEHSIL (cell cost 4.00); forced: the group cannot balance without this cell |
| FR PESHAWAR + PESHAWAR DISTRICT | PESHAWAR TEHSIL | 4,267,198 | CHAM KANI TEHSIL | 461,177 | 0.1081 | 0.1798 | split | high | 461,177 persons (source-year count) of PESHAWAR TEHSIL fall in CHAM KANI TEHSIL (cell cost 2.77); forced: the group cannot balance without this cell |
| FR PESHAWAR + PESHAWAR DISTRICT | PESHAWAR TEHSIL | 4,267,198 | MATHRA TEHSIL | 408,190 | 0.0957 | 0.1734 | split | high | 408,190 persons (source-year count) of PESHAWAR TEHSIL fall in MATHRA TEHSIL (cell cost 2.63); forced: the group cannot balance without this cell |
| FR PESHAWAR + PESHAWAR DISTRICT | PESHAWAR TEHSIL | 4,267,198 | PESHAWAR TEHSIL | 2,183,787 | 0.5118 | 0.1400 | split | high | same name |
| FR PESHAWAR + PESHAWAR DISTRICT | PESHAWAR TEHSIL | 4,267,198 | PISHTA KHARA TEHSIL | 406,984 | 0.0954 | 0.1074 | split | high | 406,984 persons (source-year count) of PESHAWAR TEHSIL fall in PISHTA KHARA TEHSIL (cell cost 2.36); forced: the group cannot balance without this cell |
| FR PESHAWAR + PESHAWAR DISTRICT | PESHAWAR TEHSIL | 4,267,198 | SHAH ALAM TEHSIL | 422,144 | 0.0989 | 0.1154 | split | high | 422,144 persons (source-year count) of PESHAWAR TEHSIL fall in SHAH ALAM TEHSIL (cell cost 2.69); forced: the group cannot balance without this cell |
| GUJRANWALA DISTRICT | GUJRANWALA CITY TEHSIL | 259,764 | GUJRANWALA CITY TEHSIL | 2,102,311 | 1.0000 | 1.0000 | merge | high | same name |
| GUJRANWALA DISTRICT | GUJRANWALA SADDAR TEHSIL | 2,806,529 | GUJRANWALA CITY TEHSIL | 2,102,311 | 0.6565 | 0.1279 | split_and_merge | high | 1,842,547 persons (source-year count) of GUJRANWALA SADDAR TEHSIL fall in GUJRANWALA CITY TEHSIL (cell cost 1.00); forced: the group cannot balance without this cell |
| GUJRANWALA DISTRICT | GUJRANWALA SADDAR TEHSIL | 2,806,529 | GUJRANWALA SADDAR TEHSIL | 963,982 | 0.3435 | 0.8721 | split | high | same name |
| HARIPUR DISTRICT | HARIPUR TEHSIL | 856,598 | HARIPUR TEHSIL | 683,411 | 0.7978 | 0.7381 | split | high | same name |
| HARIPUR DISTRICT | HARIPUR TEHSIL | 856,598 | KHANPUR TEHSIL | 173,187 | 0.2022 | 0.2619 | split | high | 173,187 persons (source-year count) of HARIPUR TEHSIL fall in KHANPUR TEHSIL (cell cost 2.45); forced: the group cannot balance without this cell |
| JHANG DISTRICT + TOBA TEK SINGH DISTRICT | PIRMAHAL TEHSIL | 422,246 | PIRMAHAL TEHSIL | 421,353 | 0.9979 | 0.9976 | split | high | same name |
| JHANG DISTRICT + TOBA TEK SINGH DISTRICT | PIRMAHAL TEHSIL | 422,246 | SHORKOT TEHSIL | 549,460 | 0.0021 | 0.0024 | split_and_merge | high | 893 persons (source-year count) of PIRMAHAL TEHSIL fall in SHORKOT TEHSIL (cell cost 2.75); forced: the group cannot balance without this cell |
| JHANG DISTRICT + TOBA TEK SINGH DISTRICT | SHORKOT TEHSIL | 548,567 | SHORKOT TEHSIL | 549,460 | 1.0000 | 1.0000 | merge | high | same name |
| KACHHI DISTRICT + NASIRABAD DISTRICT | BABA KOT TEHSIL | 49,480 | BABA KOT TEHSIL | 45,446 | 0.9165 | 0.8419 | split_and_merge | high | same name |
| KACHHI DISTRICT + NASIRABAD DISTRICT | BABA KOT TEHSIL | 49,480 | LANDHI TEHSIL | 6,063 | 0.0835 | 0.1581 | split_and_merge | medium | 4,131 persons (source-year count) of BABA KOT TEHSIL fall in LANDHI TEHSIL (cell cost 2.50); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| KACHHI DISTRICT + NASIRABAD DISTRICT | BHAG TEHSIL | 73,459 | BHAG SUB-DIVISION | 71,527 | 0.9737 | 0.9391 | split | high | same name |
| KACHHI DISTRICT + NASIRABAD DISTRICT | BHAG TEHSIL | 73,459 | LANDHI TEHSIL | 6,063 | 0.0263 | 0.0609 | split_and_merge | high | 1,932 persons (source-year count) of BHAG TEHSIL fall in LANDHI TEHSIL (cell cost 2.61); forced: the group cannot balance without this cell |
| KACHHI DISTRICT + NASIRABAD DISTRICT | CHATTAR SUB-TEHSIL | 76,536 | CHATTAR SUB-DIVISION | 25,925 | 0.3387 | 0.8076 | split | high | same name |
| KACHHI DISTRICT + NASIRABAD DISTRICT | CHATTAR SUB-TEHSIL | 76,536 | MIR HASSAN KHOSA TEHSIL | 50,611 | 0.6613 | 0.1924 | split | high | 50,611 persons (source-year count) of CHATTAR SUB-TEHSIL fall in MIR HASSAN KHOSA TEHSIL (cell cost 1.96); forced: the group cannot balance without this cell |
| KACHHI DISTRICT + NASIRABAD DISTRICT | TAMBOO TEHSIL | 131,056 | BABA KOT TEHSIL | 45,446 | 0.0007 | 0.0030 | split_and_merge | medium | 97 persons (source-year count) of TAMBOO TEHSIL fall in BABA KOT TEHSIL (cell cost 2.48); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| KACHHI DISTRICT + NASIRABAD DISTRICT | TAMBOO TEHSIL | 131,056 | TAMBOO TEHSIL | 130,959 | 0.9993 | 0.9970 | split | high | same name |
| KALAT DISTRICT | KALAT TEHSIL | 129,094 | DASHT E GORAN SUB-DIVISION | 7,636 | 0.0592 | 0.0537 | split | high | 7,636 persons (source-year count) of KALAT TEHSIL fall in DASHT E GORAN SUB-DIVISION (cell cost 1.67); forced: the group cannot balance without this cell |
| KALAT DISTRICT | KALAT TEHSIL | 129,094 | KALAT SUB-DIVISION | 121,458 | 0.9408 | 0.9463 | split | high | same name |
| KALAT DISTRICT | SURAB TEHSIL | 200,857 | GIDDER SUB-DIVISION | 69,157 | 0.3443 | 0.3748 | split | medium | 69,157 persons (source-year count) of SURAB TEHSIL fall in GIDDER SUB-DIVISION (cell cost 2.02); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| KALAT DISTRICT | SURAB TEHSIL | 200,857 | SHAHEED MEHARABAD ZEHRI SUB-DIVISION | 49,779 | 0.2478 | 0.1993 | split | high | 49,779 persons (source-year count) of SURAB TEHSIL fall in SHAHEED MEHARABAD ZEHRI SUB-DIVISION (cell cost 2.10); forced: the group cannot balance without this cell |
| KALAT DISTRICT | SURAB TEHSIL | 200,857 | SURAB SUB-DIVISION | 81,921 | 0.4079 | 0.4260 | split | high | same name |
| KHARAN DISTRICT | KHARAN TEHSIL | 80,703 | KHARAN SUB-DIVISION | 66,438 | 0.8232 | 0.6147 | split | high | same name |
| KHARAN DISTRICT | KHARAN TEHSIL | 80,703 | PATKAIN SUB-TEHSIL | 16,493 | 0.1768 | 0.3853 | split_and_merge | medium | 14,265 persons (source-year count) of KHARAN TEHSIL fall in PATKAIN SUB-TEHSIL (cell cost 1.90); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| KHARAN DISTRICT | SUB TEHSIL TOHMULK | 32,670 | PATKAIN SUB-TEHSIL | 16,493 | 0.0682 | 0.0434 | split_and_merge | medium | 2,228 persons (source-year count) of SUB TEHSIL TOHMULK fall in PATKAIN SUB-TEHSIL (cell cost 2.15); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| KHARAN DISTRICT | SUB TEHSIL TOHMULK | 32,670 | TOHMULK SUB-TEHSIL | 30,442 | 0.9318 | 0.9566 | split | high | same name |
| KHUZDAR DISTRICT | NAL SUB-TEHSIL | 130,897 | GRESHA SUB-TEHSIL | 45,648 | 0.3487 | 0.5942 | split | high | 45,648 persons (source-year count) of NAL SUB-TEHSIL fall in GRESHA SUB-TEHSIL (cell cost 2.38); forced: the group cannot balance without this cell |
| KHUZDAR DISTRICT | NAL SUB-TEHSIL | 130,897 | NAL SUB-DIVISION | 85,249 | 0.6513 | 0.4058 | split | high | same name |
| KILLA ABDULLAH DISTRICT | CHAMAN TEHSIL | 434,561 | CHAMAN CITY SUB-DIVISION | 123,206 | 0.2835 | 0.0164 | split | high | same name |
| KILLA ABDULLAH DISTRICT | CHAMAN TEHSIL | 434,561 | CHAMAN SADDAR SUB-DIVISION | 311,355 | 0.7165 | 0.9836 | split | high | same name |
| KOHISTAN DISTRICT | DASSU SUB-DIVISION | 228,350 | DASSU SUB-DIVISION | 124,374 | 0.5447 | 0.5519 | split | high | same name |
| KOHISTAN DISTRICT | DASSU SUB-DIVISION | 228,350 | HARBAN BHASHA TEHSIL | 32,510 | 0.1424 | 0.3659 | split | medium | 32,510 persons (source-year count) of DASSU SUB-DIVISION fall in HARBAN BHASHA TEHSIL (cell cost 1.97); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| KOHISTAN DISTRICT | DASSU SUB-DIVISION | 228,350 | PALAS SUB-DIVISION | 181,044 | 0.0215 | 0.0095 | split_and_merge | medium | 4,914 persons (source-year count) of DASSU SUB-DIVISION fall in PALAS SUB-DIVISION (cell cost 2.24); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| KOHISTAN DISTRICT | DASSU SUB-DIVISION | 228,350 | SEO SUB-DIVISION | 66,552 | 0.2914 | 0.0727 | split | medium | 66,552 persons (source-year count) of DASSU SUB-DIVISION fall in SEO SUB-DIVISION (cell cost 2.06); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| KOHISTAN DISTRICT | KANDIA SUB-DIVISION | 77,101 | KANDIA SUB-DIVISION | 83,850 | 1.0000 | 1.0000 | merge | high | same name |
| KOHISTAN DISTRICT | PALAS SUB-DIVISION | 276,325 | BATTAIRA SUB-DIVISION | 93,879 | 0.3397 | 0.1223 | split | high | 93,879 persons (source-year count) of PALAS SUB-DIVISION fall in BATTAIRA SUB-DIVISION (cell cost 2.43); forced: the group cannot balance without this cell |
| KOHISTAN DISTRICT | PALAS SUB-DIVISION | 276,325 | PALAS SUB-DIVISION | 181,044 | 0.6374 | 0.8680 | split_and_merge | high | same name |
| KOHISTAN DISTRICT | PALAS SUB-DIVISION | 276,325 | PATTAN SUB-DIVISION | 146,136 | 0.0229 | 0.0097 | split_and_merge | medium | 6,316 persons (source-year count) of PALAS SUB-DIVISION fall in PATTAN SUB-DIVISION (cell cost 2.42); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| KOHISTAN DISTRICT | PATTAN SUB-DIVISION | 202,935 | BANKAND RANOLIA TEHSIL | 56,366 | 0.2778 | 0.4224 | split | medium | 56,366 persons (source-year count) of PATTAN SUB-DIVISION fall in BANKAND RANOLIA TEHSIL (cell cost 2.42); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| KOHISTAN DISTRICT | PATTAN SUB-DIVISION | 202,935 | KANDIA SUB-DIVISION | 83,850 | 0.0333 | 0.1978 | split_and_merge | medium | 6,749 persons (source-year count) of PATTAN SUB-DIVISION fall in KANDIA SUB-DIVISION (cell cost 2.95); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| KOHISTAN DISTRICT | PATTAN SUB-DIVISION | 202,935 | PATTAN SUB-DIVISION | 146,136 | 0.6890 | 0.3797 | split_and_merge | high | same name |
| LAHORE DISTRICT | LAHORE CITY TEHSIL | 3,653,616 | LAHORE CITY TEHSIL | 3,644,787 | 0.9976 | 0.9947 | split | high | same name |
| LAHORE DISTRICT | LAHORE CITY TEHSIL | 3,653,616 | MODEL TOWN TEHSIL | 2,712,398 | 0.0024 | 0.0053 | split_and_merge | medium | 8,829 persons (source-year count) of LAHORE CITY TEHSIL fall in MODEL TOWN TEHSIL (cell cost 2.25); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| LAHORE DISTRICT | MODEL TOWN TEHSIL | 2,703,569 | MODEL TOWN TEHSIL | 2,712,398 | 1.0000 | 1.0000 | merge | high | same name |
| LORALAI DISTRICT | DUKI TEHSIL | 152,977 | DUKI SUB-DIVISION | 100,604 | 0.6576 | 0.2216 | split | high | same name |
| LORALAI DISTRICT | DUKI TEHSIL | 152,977 | LUNI SUB-DIVISION | 10,235 | 0.0669 | 0.1306 | split | high | 10,235 persons (source-year count) of DUKI TEHSIL fall in LUNI SUB-DIVISION (cell cost 2.62); forced: the group cannot balance without this cell |
| LORALAI DISTRICT | DUKI TEHSIL | 152,977 | TALAO SUB-TEHSIL | 18,155 | 0.1187 | 0.4009 | split | high | 18,155 persons (source-year count) of DUKI TEHSIL fall in TALAO SUB-TEHSIL (cell cost 2.65); forced: the group cannot balance without this cell |
| LORALAI DISTRICT | DUKI TEHSIL | 152,977 | THAL CHUTYALI SUB-DIVISION | 23,983 | 0.1568 | 0.2469 | split | high | 23,983 persons (source-year count) of DUKI TEHSIL fall in THAL CHUTYALI SUB-DIVISION (cell cost 2.56); forced: the group cannot balance without this cell |
| MANSEHRA DISTRICT | MANSEHRA TEHSIL | 1,017,521 | BAFFA PAKHAL TEHSIL | 406,183 | 0.3992 | 0.4776 | split | high | 406,183 persons (source-year count) of MANSEHRA TEHSIL fall in BAFFA PAKHAL TEHSIL (cell cost 2.27); forced: the group cannot balance without this cell |
| MANSEHRA DISTRICT | MANSEHRA TEHSIL | 1,017,521 | MANSEHRA TEHSIL | 611,338 | 0.6008 | 0.5224 | split | high | same name |
| MANSEHRA DISTRICT | OGHI TEHSIL | 264,964 | DARBAND TEHSIL | 49,503 | 0.1868 | 0.2494 | split | medium | 49,503 persons (source-year count) of OGHI TEHSIL fall in DARBAND TEHSIL (cell cost 2.38); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| MANSEHRA DISTRICT | OGHI TEHSIL | 264,964 | OGHI TEHSIL | 215,461 | 0.8132 | 0.7506 | split | high | same name |
| MARDAN DISTRICT | KATLANG TEHSIL | 343,225 | KATLANG TEHSIL | 316,506 | 0.2954 | 0.2629 | split_and_merge | high | same name |
| MARDAN DISTRICT | KATLANG TEHSIL | 343,225 | RUSTAM TEHSIL | 241,850 | 0.7046 | 0.7371 | split | medium | 241,850 persons (source-year count) of KATLANG TEHSIL fall in RUSTAM TEHSIL (cell cost 2.73); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| MARDAN DISTRICT | MARDAN TEHSIL | 1,403,002 | GHARI KAPOORA TEHSIL | 266,290 | 0.1898 | 0.1870 | split | high | 266,290 persons (source-year count) of MARDAN TEHSIL fall in GHARI KAPOORA TEHSIL (cell cost 1.86); forced: the group cannot balance without this cell |
| MARDAN DISTRICT | MARDAN TEHSIL | 1,403,002 | KATLANG TEHSIL | 316,506 | 0.1533 | 0.3750 | split_and_merge | medium | 215,131 persons (source-year count) of MARDAN TEHSIL fall in KATLANG TEHSIL (cell cost 2.72); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| MARDAN DISTRICT | MARDAN TEHSIL | 1,403,002 | MARDAN TEHSIL | 921,581 | 0.6569 | 0.4380 | split | high | same name |
| MUSAKHEL DISTRICT | DRUG TEHSIL | 37,599 | DRUG TEHSIL | 21,232 | 0.5647 | 0.3839 | split | high | same name |
| MUSAKHEL DISTRICT | DRUG TEHSIL | 37,599 | TIYAR ESSOT SUB-TEHSIL | 9,124 | 0.1907 | 0.2997 | split_and_merge | medium | 7,171 persons (source-year count) of DRUG TEHSIL fall in TIYAR ESSOT SUB-TEHSIL (cell cost 2.50); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| MUSAKHEL DISTRICT | DRUG TEHSIL | 37,599 | ZIMRI PLASEEN SUB-TEHSIL | 9,196 | 0.2446 | 0.3163 | split | medium | 9,196 persons (source-year count) of DRUG TEHSIL fall in ZIMRI PLASEEN SUB-TEHSIL (cell cost 4.00); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| MUSAKHEL DISTRICT | MUSAKHEL TEHSIL | 98,305 | MUSAKHEL TEHSIL | 45,509 | 0.4629 | 0.5218 | split | high | same name |
| MUSAKHEL DISTRICT | MUSAKHEL TEHSIL | 98,305 | TIYAR ESSOT SUB-TEHSIL | 9,124 | 0.0199 | 0.0508 | split_and_merge | medium | 1,953 persons (source-year count) of MUSAKHEL TEHSIL fall in TIYAR ESSOT SUB-TEHSIL (cell cost 2.70); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| MUSAKHEL DISTRICT | MUSAKHEL TEHSIL | 98,305 | TOISAR TEHSIL | 50,843 | 0.5172 | 0.4274 | split | high | 50,843 persons (source-year count) of MUSAKHEL TEHSIL fall in TOISAR TEHSIL (cell cost 2.61); forced: the group cannot balance without this cell |
| MUZAFFARGARH DISTRICT | KOT ADDU TEHSIL | 1,347,501 | CHOWK SARWAR SHAHEED TEHSIL | 365,714 | 0.2714 | 0.5143 | split | high | 365,714 persons (source-year count) of KOT ADDU TEHSIL fall in CHOWK SARWAR SHAHEED TEHSIL (cell cost 2.38); forced: the group cannot balance without this cell |
| MUZAFFARGARH DISTRICT | KOT ADDU TEHSIL | 1,347,501 | KOT ADDU TEHSIL | 981,787 | 0.7286 | 0.4857 | split | high | same name |
| NUSHKI DISTRICT | NUSHKI TEHSIL | 178,947 | DAK SUB-TEHSIL | 16,127 | 0.0901 | 0.3564 | split | high | 16,127 persons (source-year count) of NUSHKI TEHSIL fall in DAK SUB-TEHSIL (cell cost 1.92); forced: the group cannot balance without this cell |
| NUSHKI DISTRICT | NUSHKI TEHSIL | 178,947 | NUSHKI SUB-DIVISION | 162,820 | 0.9099 | 0.6436 | split | high | same name |
| PANJGUR DISTRICT | PANJGUR TEHSIL | 259,163 | KALLAG SUB-TEHSIL | 12,487 | 0.0482 | 0.1943 | split | high | 12,487 persons (source-year count) of PANJGUR TEHSIL fall in KALLAG SUB-TEHSIL (cell cost 1.93); forced: the group cannot balance without this cell |
| PANJGUR DISTRICT | PANJGUR TEHSIL | 259,163 | PANJGUR SUB-DIVISION | 246,676 | 0.9518 | 0.8057 | split | high | same name |
| PISHIN DISTRICT | BARSHORE SUB-TEHSIL | 103,423 | BARSHORE TEHSIL | 101,356 | 0.9800 | 0.9752 | split | high | same name |
| PISHIN DISTRICT | BARSHORE SUB-TEHSIL | 103,423 | NANA SAHIB TEHSIL | 28,503 | 0.0200 | 0.0248 | split_and_merge | medium | 2,067 persons (source-year count) of BARSHORE SUB-TEHSIL fall in NANA SAHIB TEHSIL (cell cost 2.36); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| PISHIN DISTRICT | KAREZAT SUB-TEHSIL | 137,466 | BOSTAN TEHSIL | 46,972 | 0.3417 | 0.0856 | split | high | 46,972 persons (source-year count) of KAREZAT SUB-TEHSIL fall in BOSTAN TEHSIL (cell cost 2.47); forced: the group cannot balance without this cell |
| PISHIN DISTRICT | KAREZAT SUB-TEHSIL | 137,466 | KAREZAT SUB-DIVISION | 64,058 | 0.4660 | 0.5710 | split | high | same name |
| PISHIN DISTRICT | KAREZAT SUB-TEHSIL | 137,466 | NANA SAHIB TEHSIL | 28,503 | 0.1923 | 0.3434 | split_and_merge | medium | 26,436 persons (source-year count) of KAREZAT SUB-TEHSIL fall in NANA SAHIB TEHSIL (cell cost 2.17); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| QUETTA DISTRICT | QUETTA CITY TEHSIL | 1,722,746 | SUB-DIVISION CITY | 1,204,306 | 0.6991 | 0.7110 | split | high | same name |
| QUETTA DISTRICT | QUETTA CITY TEHSIL | 1,722,746 | SUB-DIVISION SADDAR TEHSIL | 267,713 | 0.0007 | 0.0074 | split_and_merge | medium | 1,206 persons (source-year count) of QUETTA CITY TEHSIL fall in SUB-DIVISION SADDAR TEHSIL (cell cost 2.78); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| QUETTA DISTRICT | QUETTA CITY TEHSIL | 1,722,746 | SUB-DIVISION SARIAB | 517,234 | 0.3002 | 0.2816 | split | medium | 517,234 persons (source-year count) of QUETTA CITY TEHSIL fall in SUB-DIVISION SARIAB (cell cost 2.55); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| QUETTA DISTRICT | QUETTA SADDAR TEHSIL | 527,716 | SUB-DIVISION KUCHLAK | 261,209 | 0.4950 | 0.1235 | split | medium | 261,209 persons (source-year count) of QUETTA SADDAR TEHSIL fall in SUB-DIVISION KUCHLAK (cell cost 1.88); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| QUETTA DISTRICT | QUETTA SADDAR TEHSIL | 527,716 | SUB-DIVISION SADDAR TEHSIL | 267,713 | 0.5050 | 0.8765 | split_and_merge | high | same name |
| RAWALPINDI DISTRICT | KAHUTA TEHSIL | 220,746 | KAHUTA TEHSIL | 220,848 | 1.0000 | 1.0000 | merge | high | same name |
| RAWALPINDI DISTRICT | KOTLI SATTIAN TEHSIL | 119,295 | KAHUTA TEHSIL | 220,848 | 0.0009 | 0.0010 | split_and_merge | high | 102 persons (source-year count) of KOTLI SATTIAN TEHSIL fall in KAHUTA TEHSIL (cell cost 2.61); forced: the group cannot balance without this cell |
| RAWALPINDI DISTRICT | KOTLI SATTIAN TEHSIL | 119,295 | KOTLI SATTIAN TEHSIL | 119,193 | 0.9991 | 0.9990 | split | high | same name |
| SHANGLA DISTRICT | ALPURI TEHSIL | 508,361 | ALPURI TEHSIL | 307,333 | 0.6046 | 0.5267 | split | high | same name |
| SHANGLA DISTRICT | ALPURI TEHSIL | 508,361 | CHAKISAR TEHSIL | 110,785 | 0.2179 | 0.3032 | split | high | 110,785 persons (source-year count) of ALPURI TEHSIL fall in CHAKISAR TEHSIL (cell cost 2.47); forced: the group cannot balance without this cell |
| SHANGLA DISTRICT | ALPURI TEHSIL | 508,361 | MARTUNG TEHSIL | 90,243 | 0.1775 | 0.1701 | split | high | 90,243 persons (source-year count) of ALPURI TEHSIL fall in MARTUNG TEHSIL (cell cost 4.00); forced: the group cannot balance without this cell |
| SHEIKHUPURA DISTRICT | FEROZEWALA TEHSIL | 794,489 | FEROZEWALA TEHSIL | 818,642 | 1.0000 | 1.0000 | merge | high | same name |
| SHEIKHUPURA DISTRICT | MURIDKE TEHSIL | 639,589 | FEROZEWALA TEHSIL | 818,642 | 0.0378 | 0.0145 | split_and_merge | high | 24,153 persons (source-year count) of MURIDKE TEHSIL fall in FEROZEWALA TEHSIL (cell cost 2.26); forced: the group cannot balance without this cell |
| SHEIKHUPURA DISTRICT | MURIDKE TEHSIL | 639,589 | MURIDKE TEHSIL | 615,436 | 0.9622 | 0.9855 | split | high | same name |
| SOHBATPUR DISTRICT | SANHRI TEHSIL | 88,788 | HAIR DIN TEHSIL | 13,948 | 0.1571 | 0.2205 | split | high | 13,948 persons (source-year count) of SANHRI TEHSIL fall in HAIR DIN TEHSIL (cell cost 2.00); forced: the group cannot balance without this cell |
| SOHBATPUR DISTRICT | SANHRI TEHSIL | 88,788 | MANJHIPUR TEHSIL | 20,292 | 0.2285 | 0.2477 | split | high | 20,292 persons (source-year count) of SANHRI TEHSIL fall in MANJHIPUR TEHSIL (cell cost 2.00); forced: the group cannot balance without this cell |
| SOHBATPUR DISTRICT | SANHRI TEHSIL | 88,788 | PANHWAR TEHSIL | 39,394 | 0.4437 | 0.2991 | split | high | 39,394 persons (source-year count) of SANHRI TEHSIL fall in PANHWAR TEHSIL (cell cost 2.00); forced: the group cannot balance without this cell |
| SOHBATPUR DISTRICT | SANHRI TEHSIL | 88,788 | SAEED MUHAMMAD KANRANI TEHSIL | 15,154 | 0.1707 | 0.2326 | split | high | 15,154 persons (source-year count) of SANHRI TEHSIL fall in SAEED MUHAMMAD KANRANI TEHSIL (cell cost 2.00); forced: the group cannot balance without this cell |
| SOUTH WAZIRISTAN AGENCY | LADHA TEHSIL | 110,842 | LADHA TEHSIL | 77,883 | 0.7026 | 0.6202 | split | high | same name |
| SOUTH WAZIRISTAN AGENCY | LADHA TEHSIL | 110,842 | SHAKTOI TEHSIL | 32,959 | 0.2974 | 0.3798 | split | high | 32,959 persons (source-year count) of LADHA TEHSIL fall in SHAKTOI TEHSIL (cell cost 2.80); forced: the group cannot balance without this cell |
| TORGHAR DISTRICT | JUDBA TEHSIL | 96,888 | DAUR MERA TEHSIL | 41,661 | 0.4300 | 0.5880 | split | medium | 41,661 persons (source-year count) of JUDBA TEHSIL fall in DAUR MERA TEHSIL (cell cost 2.62); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| TORGHAR DISTRICT | JUDBA TEHSIL | 96,888 | JUDBA TEHSIL | 57,745 | 0.5700 | 0.4120 | split_and_merge | high | same name |
| TORGHAR DISTRICT | KHANDER TEHSIL | 74,461 | JUDBA TEHSIL | 57,745 | 0.0338 | 0.0089 | split_and_merge | medium | 2,518 persons (source-year count) of KHANDER TEHSIL fall in JUDBA TEHSIL (cell cost 1.80); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| TORGHAR DISTRICT | KHANDER TEHSIL | 74,461 | KHANDER TEHSIL | 71,943 | 0.9662 | 0.9911 | split | high | same name |
| UPPER DIR DISTRICT | DIR SUB-DIVISION | 439,525 | DIR SUB-DIVISION | 335,029 | 0.7623 | 0.4934 | split | high | same name |
| UPPER DIR DISTRICT | DIR SUB-DIVISION | 439,525 | LARJUM SUB-DIVISION | 104,496 | 0.2377 | 0.5066 | split | high | 104,496 persons (source-year count) of DIR SUB-DIVISION fall in LARJUM SUB-DIVISION (cell cost 1.51); forced: the group cannot balance without this cell |
