# Validation report: Pakistan tehsil crosswalk, Census 2017 to Census 2023

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
- 481 of 535 2017 units map to exactly one 2023 unit (same name, or renamed; verified by equal population in both tables). Confidence high.
- 54 2017 units map to more than one 2023 unit. Of the 39 district groups in which units were restructured:
  - 29 groups resolved by exact population balancing: every 2023 unit's restated 2017 population is matched to one 2017 parent such that the parents' 2017 populations are reproduced exactly (a unique or name-preferred partition). Confidence high where the partition is unique.
  - 10 groups do not balance by name and partition alone (boundary transfers between existing units, or new units drawn from more than one parent): ABBOTTABAD DISTRICT, DERA ISMAIL KHAN DISTRICT + FR D.I.KHAN, KACHHI DISTRICT + NASIRABAD DISTRICT, KHARAN DISTRICT, KOHISTAN DISTRICT, MARDAN DISTRICT, MUSAKHEL DISTRICT, PISHIN DISTRICT, QUETTA DISTRICT, TORGHAR DISTRICT. These were resolved by a transportation linear programme whose row sums are the 2017 populations and column sums PBS's restated 2017 populations, with a cost of 0 for same-named pairs and otherwise a cost that rises with the length of boundary the 2023 unit does not share with the parent's same-named 2023 unit (PBS Digital Census 2023 polygons). The LP solution is sparse and conserves population exactly, but the split of a transfer between a parent's several successors is an inference, not a PBS figure. Confidence medium; weight_basis = pbs_restatement+lp_adjacency.
- 19 2023 units receive population from more than one 2017 unit.

## 5. Area weights
Area weights come from PBS's published areas of the 2023 units (Census 2023 Table 1). For one-to-one rows and pure splits they are exact published areas. For the 30 rows where a 2023 unit draws people from more than one 2017 unit, the 2023 unit's area is divided between the sources in proportion to the people each contributed (uniform density within the 2023 unit); area_basis flags these as pbs_area_2023_uniform_density.

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
2. A PBS 2017 tehsil shapefile (or the 2017 block layer with tehsil codes) would turn the 10 LP-resolved groups and the 30 uniform-density area rows into measured figures. Request to PBS pending Professor Khan's go-ahead.
3. Effective dates: the splits in section 6 and every other district change are now dated, with sources, in output/event_register.csv and docs/EVENT_REGISTER.md (second release). The weights themselves still rest on the census tables.

## 9. Every split and transfer row
| district_group | unit_2017 | pop_2017 | unit_2023 | pop_2017_restated_2023 | pop_weight | area_weight | confidence | weight_basis |
|---|---|---|---|---|---|---|---|---|
| AWARAN DISTRICT | JHAL JAO SUB-TEHSIL | 40,010 | JHAL JAO TEHSIL | 21,491 | 0.5371 | 0.676 | high | pbs_restatement |
| AWARAN DISTRICT | JHAL JAO SUB-TEHSIL | 40,010 | KORAK JHAO TEHSIL | 18,519 | 0.4629 | 0.324 | high | pbs_restatement |
| BAHAWALNAGAR DISTRICT | HAROONABAD TEHSIL | 524,715 | HAROONABAD TEHSIL | 517,356 | 0.986 | 0.9879 | medium | pbs_restatement |
| BAHAWALNAGAR DISTRICT | HAROONABAD TEHSIL | 524,715 | CHISHTIAN TEHSIL | 697,125 | 0.014 | 0.0121 | medium | pbs_restatement |
| BANNU DISTRICT + FR BANNU | BANNU TEHSIL | 958,103 | BAKKA KHEL TEHSIL | 168,300 | 0.1757 | 0.4576 | high | pbs_restatement |
| BANNU DISTRICT + FR BANNU | BANNU TEHSIL | 958,103 | BANNU TEHSIL | 563,374 | 0.588 | 0.2843 | high | pbs_restatement |
| BANNU DISTRICT + FR BANNU | BANNU TEHSIL | 958,103 | KAKKI TEHSIL | 82,265 | 0.0859 | 0.0823 | high | pbs_restatement |
| BANNU DISTRICT + FR BANNU | BANNU TEHSIL | 958,103 | MERYAN TEHSIL | 144,164 | 0.1505 | 0.1758 | high | pbs_restatement |
| BUNER DISTRICT | GAGRA TEHSIL | 269,971 | CHAGHARZAI TEHSIL | 109,291 | 0.4048 | 0.5011 | high | pbs_restatement |
| BUNER DISTRICT | DAGGAR TEHSIL | 354,809 | DAGGAR TEHSIL | 176,049 | 0.4962 | 0.3806 | high | pbs_restatement |
| BUNER DISTRICT | DAGGAR TEHSIL | 354,809 | GADEZAI TEHSIL | 178,760 | 0.5038 | 0.6194 | high | pbs_restatement |
| BUNER DISTRICT | GAGRA TEHSIL | 269,971 | GAGRA TEHSIL | 160,680 | 0.5952 | 0.4989 | high | pbs_restatement |
| CHAGAI DISTRICT | DALBANDIN TEHSIL | 127,468 | DALBANDIN SUB-DIVISION | 106,643 | 0.8366 | 0.5071 | high | pbs_restatement |
| CHAGAI DISTRICT | DALBANDIN TEHSIL | 127,468 | YAK MACHH SUB-TEHSIL | 20,825 | 0.1634 | 0.4929 | high | pbs_restatement |
| CHAKWAL DISTRICT | LAWA TEHSIL | 125,770 | LAWA TEHSIL | 117,929 | 0.9377 | 0.9592 | medium | pbs_restatement |
| CHAKWAL DISTRICT | LAWA TEHSIL | 125,770 | TALA GANG TEHSIL | 409,827 | 0.0623 | 0.0408 | medium | pbs_restatement |
| CHARSADDA DISTRICT | TANGI TEHSIL | 426,165 | TANGI TEHSIL | 421,348 | 0.9887 | 0.9924 | medium | pbs_restatement |
| CHARSADDA DISTRICT | TANGI TEHSIL | 426,165 | CHARSADDA TEHSIL | 809,660 | 0.0113 | 0.0076 | medium | pbs_restatement |
| CHITRAL DISTRICT | CHITRAL SUB-DIVISION | 278,328 | CHITRAL SUB-DIVISION | 183,178 | 0.6581 | 0.9487 | high | pbs_restatement |
| CHITRAL DISTRICT | CHITRAL SUB-DIVISION | 278,328 | DROSH SUB-DIVISION | 95,150 | 0.3419 | 0.0513 | high | pbs_restatement |
| FR KOHAT + KOHAT DISTRICT | KOHAT TEHSIL | 848,997 | GUMBAT TEHSIL | 112,340 | 0.1323 | 0.3557 | high | pbs_restatement |
| FR KOHAT + KOHAT DISTRICT | KOHAT TEHSIL | 848,997 | KOHAT TEHSIL | 736,657 | 0.8677 | 0.6443 | high | pbs_restatement |
| FR LAKKI MARWAT + LAKKI MARWAT DISTRICT | LAKKI MARWAT TEHSIL | 578,874 | GHAZNI KHEL TEHSIL | 295,984 | 0.5113 | 0.4538 | high | pbs_restatement |
| FR LAKKI MARWAT + LAKKI MARWAT DISTRICT | LAKKI MARWAT TEHSIL | 578,874 | LAKKI MARWAT TEHSIL | 282,890 | 0.4887 | 0.5462 | high | pbs_restatement |
| FR PESHAWAR + PESHAWAR DISTRICT | PESHAWAR TEHSIL | 4,267,198 | BADHBER TEHSIL | 384,916 | 0.0902 | 0.284 | high | pbs_restatement |
| FR PESHAWAR + PESHAWAR DISTRICT | PESHAWAR TEHSIL | 4,267,198 | CHAM KANI TEHSIL | 461,177 | 0.1081 | 0.1798 | high | pbs_restatement |
| FR PESHAWAR + PESHAWAR DISTRICT | PESHAWAR TEHSIL | 4,267,198 | MATHRA TEHSIL | 408,190 | 0.0957 | 0.1734 | high | pbs_restatement |
| FR PESHAWAR + PESHAWAR DISTRICT | PESHAWAR TEHSIL | 4,267,198 | PESHAWAR TEHSIL | 2,183,787 | 0.5118 | 0.14 | high | pbs_restatement |
| FR PESHAWAR + PESHAWAR DISTRICT | PESHAWAR TEHSIL | 4,267,198 | PISHTA KHARA TEHSIL | 406,984 | 0.0954 | 0.1074 | high | pbs_restatement |
| FR PESHAWAR + PESHAWAR DISTRICT | PESHAWAR TEHSIL | 4,267,198 | SHAH ALAM TEHSIL | 422,144 | 0.0989 | 0.1154 | high | pbs_restatement |
| GUJRANWALA DISTRICT | GUJRANWALA SADDAR TEHSIL | 2,806,529 | GUJRANWALA SADDAR TEHSIL | 963,982 | 0.3435 | 0.8721 | medium | pbs_restatement |
| GUJRANWALA DISTRICT | GUJRANWALA SADDAR TEHSIL | 2,806,529 | GUJRANWALA CITY TEHSIL | 2,102,311 | 0.6565 | 0.1279 | medium | pbs_restatement |
| HARIPUR DISTRICT | HARIPUR TEHSIL | 856,598 | HARIPUR TEHSIL | 683,411 | 0.7978 | 0.7381 | high | pbs_restatement |
| HARIPUR DISTRICT | HARIPUR TEHSIL | 856,598 | KHANPUR TEHSIL | 173,187 | 0.2022 | 0.2619 | high | pbs_restatement |
| JHANG DISTRICT + TOBA TEK SINGH DISTRICT | PIRMAHAL TEHSIL | 422,246 | PIRMAHAL TEHSIL | 421,353 | 0.9979 | 0.9976 | medium | pbs_restatement |
| JHANG DISTRICT + TOBA TEK SINGH DISTRICT | PIRMAHAL TEHSIL | 422,246 | SHORKOT TEHSIL | 549,460 | 0.0021 | 0.0024 | medium | pbs_restatement |
| KALAT DISTRICT | KALAT TEHSIL | 129,094 | DASHT E GORAN SUB-DIVISION | 7,636 | 0.0592 | 0.0537 | high | pbs_restatement |
| KALAT DISTRICT | SURAB TEHSIL | 200,857 | GIDDER SUB-DIVISION | 69,157 | 0.3443 | 0.3748 | high | pbs_restatement |
| KALAT DISTRICT | KALAT TEHSIL | 129,094 | KALAT SUB-DIVISION | 121,458 | 0.9408 | 0.9463 | high | pbs_restatement |
| KALAT DISTRICT | SURAB TEHSIL | 200,857 | SHAHEED MEHARABAD ZEHRI SUB-DIVISION | 49,779 | 0.2478 | 0.1993 | high | pbs_restatement |
| KALAT DISTRICT | SURAB TEHSIL | 200,857 | SURAB SUB-DIVISION | 81,921 | 0.4079 | 0.426 | high | pbs_restatement |
| KHUZDAR DISTRICT | NAL SUB-TEHSIL | 130,897 | GRESHA SUB-TEHSIL | 45,648 | 0.3487 | 0.5942 | high | pbs_restatement |
| KHUZDAR DISTRICT | NAL SUB-TEHSIL | 130,897 | NAL SUB-DIVISION | 85,249 | 0.6513 | 0.4058 | high | pbs_restatement |
| KILLA ABDULLAH DISTRICT | CHAMAN TEHSIL | 434,561 | CHAMAN CITY SUB-DIVISION | 123,206 | 0.2835 | 0.0164 | high | pbs_restatement |
| KILLA ABDULLAH DISTRICT | CHAMAN TEHSIL | 434,561 | CHAMAN SADDAR SUB-DIVISION | 311,355 | 0.7165 | 0.9836 | high | pbs_restatement |
| LAHORE DISTRICT | LAHORE CITY TEHSIL | 3,653,616 | LAHORE CITY TEHSIL | 3,644,787 | 0.9976 | 0.9947 | medium | pbs_restatement |
| LAHORE DISTRICT | LAHORE CITY TEHSIL | 3,653,616 | MODEL TOWN TEHSIL | 2,712,398 | 0.0024 | 0.0053 | medium | pbs_restatement |
| LORALAI DISTRICT | DUKI TEHSIL | 152,977 | DUKI SUB-DIVISION | 100,604 | 0.6576 | 0.2216 | high | pbs_restatement |
| LORALAI DISTRICT | DUKI TEHSIL | 152,977 | LUNI SUB-DIVISION | 10,235 | 0.0669 | 0.1306 | high | pbs_restatement |
| LORALAI DISTRICT | DUKI TEHSIL | 152,977 | TALAO SUB-TEHSIL | 18,155 | 0.1187 | 0.4009 | high | pbs_restatement |
| LORALAI DISTRICT | DUKI TEHSIL | 152,977 | THAL CHUTYALI SUB-DIVISION | 23,983 | 0.1568 | 0.2469 | high | pbs_restatement |
| MANSEHRA DISTRICT | MANSEHRA TEHSIL | 1,017,521 | BAFFA PAKHAL TEHSIL | 406,183 | 0.3992 | 0.4776 | high | pbs_restatement |
| MANSEHRA DISTRICT | OGHI TEHSIL | 264,964 | DARBAND TEHSIL | 49,503 | 0.1868 | 0.2494 | high | pbs_restatement |
| MANSEHRA DISTRICT | MANSEHRA TEHSIL | 1,017,521 | MANSEHRA TEHSIL | 611,338 | 0.6008 | 0.5224 | high | pbs_restatement |
| MANSEHRA DISTRICT | OGHI TEHSIL | 264,964 | OGHI TEHSIL | 215,461 | 0.8132 | 0.7506 | high | pbs_restatement |
| MUZAFFARGARH DISTRICT | KOT ADDU TEHSIL | 1,347,501 | CHOWK SARWAR SHAHEED TEHSIL | 365,714 | 0.2714 | 0.5143 | high | pbs_restatement |
| MUZAFFARGARH DISTRICT | KOT ADDU TEHSIL | 1,347,501 | KOT ADDU TEHSIL | 981,787 | 0.7286 | 0.4857 | high | pbs_restatement |
| NUSHKI DISTRICT | NUSHKI TEHSIL | 178,947 | DAK SUB-TEHSIL | 16,127 | 0.0901 | 0.3564 | high | pbs_restatement |
| NUSHKI DISTRICT | NUSHKI TEHSIL | 178,947 | NUSHKI SUB-DIVISION | 162,820 | 0.9099 | 0.6436 | high | pbs_restatement |
| PANJGUR DISTRICT | PANJGUR TEHSIL | 259,163 | KALLAG SUB-TEHSIL | 12,487 | 0.0482 | 0.1943 | high | pbs_restatement |
| PANJGUR DISTRICT | PANJGUR TEHSIL | 259,163 | PANJGUR SUB-DIVISION | 246,676 | 0.9518 | 0.8057 | high | pbs_restatement |
| RAWALPINDI DISTRICT | KOTLI SATTIAN TEHSIL | 119,295 | KOTLI SATTIAN TEHSIL | 119,193 | 0.9991 | 0.999 | medium | pbs_restatement |
| RAWALPINDI DISTRICT | KOTLI SATTIAN TEHSIL | 119,295 | KAHUTA TEHSIL | 220,848 | 0.0009 | 0.001 | medium | pbs_restatement |
| SHANGLA DISTRICT | ALPURI TEHSIL | 508,361 | ALPURI TEHSIL | 307,333 | 0.6046 | 0.5267 | high | pbs_restatement |
| SHANGLA DISTRICT | ALPURI TEHSIL | 508,361 | CHAKISAR TEHSIL | 110,785 | 0.2179 | 0.3032 | high | pbs_restatement |
| SHANGLA DISTRICT | ALPURI TEHSIL | 508,361 | MARTUNG TEHSIL | 90,243 | 0.1775 | 0.1701 | high | pbs_restatement |
| SHEIKHUPURA DISTRICT | MURIDKE TEHSIL | 639,589 | MURIDKE TEHSIL | 615,436 | 0.9622 | 0.9855 | medium | pbs_restatement |
| SHEIKHUPURA DISTRICT | MURIDKE TEHSIL | 639,589 | FEROZEWALA TEHSIL | 818,642 | 0.0378 | 0.0145 | medium | pbs_restatement |
| SOHBATPUR DISTRICT | SANHRI TEHSIL | 88,788 | HAIR DIN TEHSIL | 13,948 | 0.1571 | 0.2205 | high | pbs_restatement |
| SOHBATPUR DISTRICT | SANHRI TEHSIL | 88,788 | MANJHIPUR TEHSIL | 20,292 | 0.2285 | 0.2477 | high | pbs_restatement |
| SOHBATPUR DISTRICT | SANHRI TEHSIL | 88,788 | PANHWAR TEHSIL | 39,394 | 0.4437 | 0.2991 | high | pbs_restatement |
| SOHBATPUR DISTRICT | SANHRI TEHSIL | 88,788 | SAEED MUHAMMAD KANRANI TEHSIL | 15,154 | 0.1707 | 0.2326 | high | pbs_restatement |
| SOUTH WAZIRISTAN AGENCY | LADHA TEHSIL | 110,842 | LADHA TEHSIL | 77,883 | 0.7026 | 0.6202 | high | pbs_restatement |
| SOUTH WAZIRISTAN AGENCY | LADHA TEHSIL | 110,842 | SHAKTOI TEHSIL | 32,959 | 0.2974 | 0.3798 | high | pbs_restatement |
| UPPER DIR DISTRICT | DIR SUB-DIVISION | 439,525 | DIR SUB-DIVISION | 335,029 | 0.7623 | 0.4934 | high | pbs_restatement |
| UPPER DIR DISTRICT | DIR SUB-DIVISION | 439,525 | LARJUM SUB-DIVISION | 104,496 | 0.2377 | 0.5066 | high | pbs_restatement |
| ABBOTTABAD DISTRICT | ABBOTTABAD TEHSIL | 982,837 | ABBOTTABAD TEHSIL | 939,576 | 0.956 | 0.9208 | medium | pbs_restatement+lp_adjacency |
| ABBOTTABAD DISTRICT | ABBOTTABAD TEHSIL | 982,837 | LOWER TANAWAL TEHSIL | 59,912 | 0.044 | 0.0792 | medium | pbs_restatement+lp_adjacency |
| ABBOTTABAD DISTRICT | HAVELIAN TEHSIL | 350,252 | HAVELIAN TEHSIL | 235,725 | 0.673 | 0.5984 | medium | pbs_restatement+lp_adjacency |
| ABBOTTABAD DISTRICT | HAVELIAN TEHSIL | 350,252 | LORA TEHSIL | 97,876 | 0.2794 | 0.3272 | medium | pbs_restatement+lp_adjacency |
| ABBOTTABAD DISTRICT | HAVELIAN TEHSIL | 350,252 | LOWER TANAWAL TEHSIL | 59,912 | 0.0475 | 0.0744 | medium | pbs_restatement+lp_adjacency |
| DERA ISMAIL KHAN DISTRICT + FR D.I.KHAN | PAHARPUR TEHSIL | 381,086 | DERA ISMAIL KHAN TEHSIL | 730,678 | 0.0137 | 0.0048 | medium | pbs_restatement+lp_adjacency |
| DERA ISMAIL KHAN DISTRICT + FR D.I.KHAN | PAHARPUR TEHSIL | 381,086 | PAHARPUR TEHSIL | 362,606 | 0.9515 | 0.952 | medium | pbs_restatement+lp_adjacency |
| DERA ISMAIL KHAN DISTRICT + FR D.I.KHAN | PAHARPUR TEHSIL | 381,086 | PAROA TEHSIL | 305,594 | 0.0348 | 0.0432 | medium | pbs_restatement+lp_adjacency |
| KACHHI DISTRICT + NASIRABAD DISTRICT | BABA KOT TEHSIL | 49,480 | BABA KOT TEHSIL | 45,446 | 0.9185 | 0.8453 | medium | pbs_restatement+lp_adjacency |
| KACHHI DISTRICT + NASIRABAD DISTRICT | BABA KOT TEHSIL | 49,480 | LANDHI TEHSIL | 6,063 | 0.0815 | 0.1547 | medium | pbs_restatement+lp_adjacency |
| KACHHI DISTRICT + NASIRABAD DISTRICT | BHAG TEHSIL | 73,459 | BHAG SUB-DIVISION | 71,527 | 0.9737 | 0.9391 | medium | pbs_restatement+lp_adjacency |
| KACHHI DISTRICT + NASIRABAD DISTRICT | BHAG TEHSIL | 73,459 | LANDHI TEHSIL | 6,063 | 0.0263 | 0.0609 | medium | pbs_restatement+lp_adjacency |
| KACHHI DISTRICT + NASIRABAD DISTRICT | CHATTAR SUB-TEHSIL | 76,536 | CHATTAR SUB-DIVISION | 25,925 | 0.3387 | 0.8076 | medium | pbs_restatement+lp_adjacency |
| KACHHI DISTRICT + NASIRABAD DISTRICT | CHATTAR SUB-TEHSIL | 76,536 | MIR HASSAN KHOSA TEHSIL | 50,611 | 0.6613 | 0.1924 | medium | pbs_restatement+lp_adjacency |
| KACHHI DISTRICT + NASIRABAD DISTRICT | TAMBOO TEHSIL | 131,056 | LANDHI TEHSIL | 6,063 | 0.0007 | 0.0062 | medium | pbs_restatement+lp_adjacency |
| KACHHI DISTRICT + NASIRABAD DISTRICT | TAMBOO TEHSIL | 131,056 | TAMBOO TEHSIL | 130,959 | 0.9993 | 0.9938 | medium | pbs_restatement+lp_adjacency |
| KHARAN DISTRICT | KHARAN TEHSIL | 80,703 | KHARAN SUB-DIVISION | 66,438 | 0.8232 | 0.6147 | medium | pbs_restatement+lp_adjacency |
| KHARAN DISTRICT | KHARAN TEHSIL | 80,703 | PATKAIN SUB-TEHSIL | 16,493 | 0.1768 | 0.3853 | medium | pbs_restatement+lp_adjacency |
| KHARAN DISTRICT | SUB TEHSIL TOHMULK | 32,670 | PATKAIN SUB-TEHSIL | 16,493 | 0.0682 | 0.0434 | medium | pbs_restatement+lp_adjacency |
| KHARAN DISTRICT | SUB TEHSIL TOHMULK | 32,670 | TOHMULK SUB-TEHSIL | 30,442 | 0.9318 | 0.9566 | medium | pbs_restatement+lp_adjacency |
| KOHISTAN DISTRICT | DASSU SUB-DIVISION | 228,350 | DASSU SUB-DIVISION | 124,374 | 0.5447 | 0.5399 | medium | pbs_restatement+lp_adjacency |
| KOHISTAN DISTRICT | DASSU SUB-DIVISION | 228,350 | HARBAN BHASHA TEHSIL | 32,510 | 0.1424 | 0.3579 | medium | pbs_restatement+lp_adjacency |
| KOHISTAN DISTRICT | DASSU SUB-DIVISION | 228,350 | KANDIA SUB-DIVISION | 83,850 | 0.0215 | 0.0311 | medium | pbs_restatement+lp_adjacency |
| KOHISTAN DISTRICT | DASSU SUB-DIVISION | 228,350 | SEO SUB-DIVISION | 66,552 | 0.2914 | 0.0711 | medium | pbs_restatement+lp_adjacency |
| KOHISTAN DISTRICT | PALAS SUB-DIVISION | 276,325 | BATTAIRA SUB-DIVISION | 93,879 | 0.3397 | 0.1179 | medium | pbs_restatement+lp_adjacency |
| KOHISTAN DISTRICT | PALAS SUB-DIVISION | 276,325 | KANDIA SUB-DIVISION | 83,850 | 0.0051 | 0.0223 | medium | pbs_restatement+lp_adjacency |
| KOHISTAN DISTRICT | PALAS SUB-DIVISION | 276,325 | PALAS SUB-DIVISION | 181,044 | 0.6552 | 0.8598 | medium | pbs_restatement+lp_adjacency |
| KOHISTAN DISTRICT | PATTAN SUB-DIVISION | 202,935 | BANKAND RANOLIA TEHSIL | 56,366 | 0.2778 | 0.5077 | medium | pbs_restatement+lp_adjacency |
| KOHISTAN DISTRICT | PATTAN SUB-DIVISION | 202,935 | KANDIA SUB-DIVISION | 83,850 | 0.0021 | 0.0153 | medium | pbs_restatement+lp_adjacency |
| KOHISTAN DISTRICT | PATTAN SUB-DIVISION | 202,935 | PATTAN SUB-DIVISION | 146,136 | 0.7201 | 0.477 | medium | pbs_restatement+lp_adjacency |
| MARDAN DISTRICT | KATLANG TEHSIL | 343,225 | KATLANG TEHSIL | 316,506 | 0.9222 | 0.9097 | medium | pbs_restatement+lp_adjacency |
| MARDAN DISTRICT | KATLANG TEHSIL | 343,225 | RUSTAM TEHSIL | 241,850 | 0.0778 | 0.0903 | medium | pbs_restatement+lp_adjacency |
| MARDAN DISTRICT | MARDAN TEHSIL | 1,403,002 | GHARI KAPOORA TEHSIL | 266,290 | 0.1898 | 0.1754 | medium | pbs_restatement+lp_adjacency |
| MARDAN DISTRICT | MARDAN TEHSIL | 1,403,002 | MARDAN TEHSIL | 921,581 | 0.6569 | 0.411 | medium | pbs_restatement+lp_adjacency |
| MARDAN DISTRICT | MARDAN TEHSIL | 1,403,002 | RUSTAM TEHSIL | 241,850 | 0.1533 | 0.4136 | medium | pbs_restatement+lp_adjacency |
| MUSAKHEL DISTRICT | DRUG TEHSIL | 37,599 | DRUG TEHSIL | 21,232 | 0.5647 | 0.3785 | medium | pbs_restatement+lp_adjacency |
| MUSAKHEL DISTRICT | DRUG TEHSIL | 37,599 | TIYAR ESSOT SUB-TEHSIL | 9,124 | 0.2427 | 0.3759 | medium | pbs_restatement+lp_adjacency |
| MUSAKHEL DISTRICT | DRUG TEHSIL | 37,599 | ZIMRI PLASEEN SUB-TEHSIL | 9,196 | 0.1926 | 0.2456 | medium | pbs_restatement+lp_adjacency |
| MUSAKHEL DISTRICT | MUSAKHEL TEHSIL | 98,305 | MUSAKHEL TEHSIL | 45,509 | 0.4629 | 0.5265 | medium | pbs_restatement+lp_adjacency |
| MUSAKHEL DISTRICT | MUSAKHEL TEHSIL | 98,305 | TOISAR TEHSIL | 50,843 | 0.5172 | 0.4313 | medium | pbs_restatement+lp_adjacency |
| MUSAKHEL DISTRICT | MUSAKHEL TEHSIL | 98,305 | ZIMRI PLASEEN SUB-TEHSIL | 9,196 | 0.0199 | 0.0421 | medium | pbs_restatement+lp_adjacency |
| PISHIN DISTRICT | BARSHORE SUB-TEHSIL | 103,423 | BARSHORE TEHSIL | 101,356 | 0.98 | 0.9752 | medium | pbs_restatement+lp_adjacency |
| PISHIN DISTRICT | BARSHORE SUB-TEHSIL | 103,423 | NANA SAHIB TEHSIL | 28,503 | 0.02 | 0.0248 | medium | pbs_restatement+lp_adjacency |
| PISHIN DISTRICT | KAREZAT SUB-TEHSIL | 137,466 | BOSTAN TEHSIL | 46,972 | 0.3417 | 0.0856 | medium | pbs_restatement+lp_adjacency |
| PISHIN DISTRICT | KAREZAT SUB-TEHSIL | 137,466 | KAREZAT SUB-DIVISION | 64,058 | 0.466 | 0.571 | medium | pbs_restatement+lp_adjacency |
| PISHIN DISTRICT | KAREZAT SUB-TEHSIL | 137,466 | NANA SAHIB TEHSIL | 28,503 | 0.1923 | 0.3434 | medium | pbs_restatement+lp_adjacency |
| QUETTA DISTRICT | QUETTA CITY TEHSIL | 1,722,746 | SUB-DIVISION CITY | 1,204,306 | 0.6991 | 0.7155 | medium | pbs_restatement+lp_adjacency |
| QUETTA DISTRICT | QUETTA CITY TEHSIL | 1,722,746 | SUB-DIVISION KUCHLAK | 261,209 | 0.0007 | 0.0011 | medium | pbs_restatement+lp_adjacency |
| QUETTA DISTRICT | QUETTA CITY TEHSIL | 1,722,746 | SUB-DIVISION SARIAB | 517,234 | 0.3002 | 0.2834 | medium | pbs_restatement+lp_adjacency |
| QUETTA DISTRICT | QUETTA SADDAR TEHSIL | 527,716 | SUB-DIVISION KUCHLAK | 261,209 | 0.4927 | 0.1225 | medium | pbs_restatement+lp_adjacency |
| QUETTA DISTRICT | QUETTA SADDAR TEHSIL | 527,716 | SUB-DIVISION SADDAR TEHSIL | 267,713 | 0.5073 | 0.8775 | medium | pbs_restatement+lp_adjacency |
| TORGHAR DISTRICT | JUDBA TEHSIL | 96,888 | DAUR MERA TEHSIL | 41,661 | 0.404 | 0.5619 | medium | pbs_restatement+lp_adjacency |
| TORGHAR DISTRICT | JUDBA TEHSIL | 96,888 | JUDBA TEHSIL | 57,745 | 0.596 | 0.4381 | medium | pbs_restatement+lp_adjacency |
| TORGHAR DISTRICT | KHANDER TEHSIL | 74,461 | DAUR MERA TEHSIL | 41,661 | 0.0338 | 0.0168 | medium | pbs_restatement+lp_adjacency |
| TORGHAR DISTRICT | KHANDER TEHSIL | 74,461 | KHANDER TEHSIL | 71,943 | 0.9662 | 0.9832 | medium | pbs_restatement+lp_adjacency |