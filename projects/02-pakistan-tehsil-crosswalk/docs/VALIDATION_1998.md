# Validation report: 1998 layer (Census 1998 -> 2017, and chained 1998 -> 2023)

Built 3 November 2026. Scope: Punjab, Sindh, Khyber Pakhtunkhwa (with the former FATA) and Balochistan. The 2017 -> 2023 layer has its own report in VALIDATION.md.

## 1. The 1998 frame
The 1998 sub-district units come from PBS/PCO Census Publication 161, *Population of Administrative Units 1951-98* (Data Darbar table census_admin_units_1951_1998). The lowest published tier is used: tehsils, talukas and sub-tehsils; a sub-division only where it has no tehsil rows; each Frontier Region as one unit. That gives 457 units in 114 districts and agencies, and they sum exactly to the published district populations and to the five provincial totals (Punjab 73,621,290; Sindh 30,439,893; NWFP/KP 17,743,645; Balochistan 6,565,885; FATA 3,176,331).

For three districts the 1951-98 report does not list the 1998 census tehsils but the towns and cantonments created under the 2001 local government system (Karachi 24 units, Lahore 7, Peshawar 5). These are not 1998 census units, so the 1998 side is collapsed to the whole district there: Karachi City District (one unit, as Professor Khan asked), Lahore City District (one unit) and Peshawar District (one unit). Peshawar loses nothing (the whole district was one tehsil in 2017, restated 1998 population 2,026,851 = the 1998 district count). Lahore loses the 1998 split between Lahore City and Lahore Cantt tehsils; it can be restored from the 1998 District Census Report of Lahore if needed. After the collapse the 1998 frame has 424 units.

One more thing to know about this frame. The 1951-98 report presents the 1998 counts on the administrative map as it stood when the report was compiled, in the mid-2000s, not as on census day. The Punjab Government's own 1998 census table (34 districts, 118 tehsils, raw/punjab1998/) shows the difference: the report's Punjab has 123 units after the Lahore collapse because it already contains Ahmedpur Sial, Dina, Kallar Kahar, Kallar Sayyadan and Kot Momin, and splits Gujranwala into City and Saddar; district totals agree exactly and 100 of the 118 census-day tehsils are identical in name and population. Elsewhere the report lists Nushki (a district only from about 2004) and folds Umerkot (a district from 1993 to December 2000, population 663,095 at the 1998 census) into Mirpur Khas. So "1998 frame" in these tables means the frame of Census Publication 161. Two helps are provided: the column district_1998_at_census gives the census-day district for the Umerkot talukas and Nushki, and for Punjab a separate layer maps the 118 census-day tehsils onto the report frame and on to 2023 (crosswalk_tehsil_1998census_to_pcoframe_punjab.csv, crosswalk_tehsil_1998census_to_2023_punjab.csv; 128 and 172 rows, 4 and 21 of them inferred). The same table has not been found online for Sindh, KP, Balochistan or FATA; the report frame is the only 1998 tehsil frame available there.

## 2. Completeness
- 1998 frame: 424 of 424 units appear in the crosswalk.
- 2017 frame: 535 of 535 sub-district units appear.
- Districts: 114 of 114 (1998) and 134 of 134 (2017; Islamabad excluded).
- Rows: 598 tehsil rows 1998 -> 2017; 680 tehsil rows 1998 -> 2023 (chained); 142 and 151 district rows.

## 3. Weight checks
- Population weights sum to 1 for every 1998 unit (max deviation 1.4e-15); area weights likewise (2.2e-16). Same for the chained 1998 -> 2023 table.

## 4. Conservation
Pushing the 1998 population of every 1998 unit through the weights reproduces, for every 2017 unit and every 2017 district, the "POPULATION 1998" column PBS printed in Census 2017 Table 1 (max deviation 0 persons). Provincial totals:

| Province | Crosswalk | PBS Census 2017 Table 1, Population 1998 | PCO 1951-98 report |
|---|---|---|---|
| BALOCHISTAN | 6,565,885 | 6,565,885 | 6,565,885 |
| FATA | 3,176,331 | 3,176,331 | 3,176,331 |
| KHYBER PAKHTUNKHWA | 17,743,645 | 17,743,645 | 17,743,645 |
| PUNJAB | 73,621,290 | 73,621,290 | 73,621,290 |
| SINDH | 30,439,893 | 30,439,893 | 30,439,893 |

For the chained 1998 -> 2023 table there is no PBS figure to check against (PBS never printed 1998 populations on 2023 units); the check is that the national total is conserved to the person (131,547,044) and that every 2023 unit is reached.

## 5. How each unit was matched
The same idea as the 2017 -> 2023 layer, written as one procedure for all district groups. Districts are first grouped (a namesake district plus any new district whose restated 1998 population equals the residual of a parent, verified by exact balancing; e.g. Chiniot 965,124 = Jhang 2,834,545 minus 1,869,421). Inside each group the flows from 1998 units to 2017 units are chosen to reproduce both the 1998 populations and PBS's restated 1998 populations exactly while opening as few unexpected cells as possible: same-named pairs cost almost nothing, a pair whose 2017 unit touches the polygon of the 1998 unit's namesake costs more, a non-adjacent pair more still. This is a fixed-charge transportation problem, solved exactly (scipy MILP). Two safeguards: a same-named pair with identical population in both tables is treated as unchanged, and where the district-level flows are unambiguous they are imposed on the tehsil-level solve (e.g. Kasur -> Lahore exactly 21,369 persons). Every opened cell that is not a same-name pair is then graded by re-solving with that cell forbidden: forced (the group cannot balance without it, confidence high), inferred (another balancing allocation exists but is less parsimonious under the adjacency prior, confidence medium) or ambiguous (an equally cheap alternative exists, confidence low).

- Methods: one_to_one 274, split 195, split_and_merge 90, merge 33, one_to_one_renamed 6.
- Confidence: high 532, medium 62, low 4 (1998 -> 2017); chained 1998 -> 2023 inherits the lower of the two layers: high 575, medium 101, low 4.
- 111 1998 units map to more than one 2017 unit; 60 2017 units draw from more than one 1998 unit.

Name spellings differ between the 1951-98 report and the 2017 tables (Buleda / Bulaida, Besham / Bisham, Kutmandai / Kot Mandai, Nurpur / Noorpur, Sobhodhero / Sobho Dero, Tandlianwala / Tandlian Wala, Kallar Sayyadan / Kallar Sayaddan). These were matched with a tolerant string comparison (shared stem and at least 70 percent similarity) within the district group, and every such pair is then confirmed by the population balance; the six pairs matched purely by population balance (one_to_one_renamed) are listed in section 9.

## 6. Rows not fixed by a PBS figure (medium = inferred, low = ambiguous), 1998 -> 2017
| district_1998 | unit_1998 | pop_1998 | unit_2017 | flow_1998 | confidence | note |
|---|---|---|---|---|---|---|
| LOWER DIR DISTRICT | JANDUL SUB-DIVISION | 189,357 | LAL QILA SUB-DIVISION | 129,305 | low | 129,305 persons (source-year count) of JANDUL SUB-DIVISION fall in LAL QILA SUB-DIVISION (cell cost 2.00); ambiguous: an equally parsimonious alternative allocation exists |
| LOWER DIR DISTRICT | JANDUL SUB-DIVISION | 189,357 | SAMARBAGH SUB-DIVISION | 60,052 | low | 60,052 persons (source-year count) of JANDUL SUB-DIVISION fall in SAMARBAGH SUB-DIVISION (cell cost 2.00); ambiguous: an equally parsimonious alternative allocation exists |
| LOWER DIR DISTRICT | TIMARGARA SUB-DIVISION | 528,292 | ADENZAI SUB-DIVISION | 168,830 | low | 168,830 persons (source-year count) of TIMARGARA SUB-DIVISION fall in ADENZAI SUB-DIVISION (cell cost 2.00); ambiguous: an equally parsimonious alternative allocation exists |
| MIRPUR KHAS DISTRICT | MIRPUR KHAS TALUKA | 428,275 | SINDHRI TALUKA | 50,234 | low | 50,234 persons (source-year count) of MIRPUR KHAS TALUKA fall in SINDHRI TALUKA (cell cost 4.00); ambiguous: an equally parsimonious alternative allocation exists |
| BADIN DISTRICT | GOLARCHI TALUKA | 191,580 | TANDO GHULAM HYDER TALUKA | 8,889 | medium | 8,889 persons (source-year count) of GOLARCHI TALUKA fall in TANDO GHULAM HYDER TALUKA (cell cost 2.42); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| BADIN DISTRICT | MATLI TALUKA | 312,356 | TANDO MUHAMMAD KHAN TALUKA | 29,083 | medium | 29,083 persons (source-year count) of MATLI TALUKA fall in TANDO MUHAMMAD KHAN TALUKA (cell cost 2.45); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| BADIN DISTRICT | TALHAR TALUKA | 150,158 | TANDO GHULAM HYDER TALUKA | 48,837 | medium | 48,837 persons (source-year count) of TALHAR TALUKA fall in TANDO GHULAM HYDER TALUKA (cell cost 2.50); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| BADIN DISTRICT | TANDO BAGHO TALUKA | 249,728 | TALHAR TALUKA | 6,581 | medium | 6,581 persons (source-year count) of TANDO BAGHO TALUKA fall in TALHAR TALUKA (cell cost 2.23); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| BAHAWALPUR DISTRICT | KHAIRPUR TAMEWALI TEHSIL | 184,914 | YAZMAN TEHSIL | 1,011 | medium | 1,011 persons (source-year count) of KHAIRPUR TAMEWALI TEHSIL fall in YAZMAN TEHSIL (cell cost 2.89); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| D.I.KHAN DISTRICT | D.I.KHAN TEHSIL | 481,757 | DERA ISMAIL KHAN TEHSIL | 362,790 | medium | 362,790 persons (source-year count) of D.I.KHAN TEHSIL fall in DERA ISMAIL KHAN TEHSIL (cell cost 2.00); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| D.I.KHAN DISTRICT | D.I.KHAN TEHSIL | 481,757 | PAHARPUR TEHSIL | 6,445 | medium | 6,445 persons (source-year count) of D.I.KHAN TEHSIL fall in PAHARPUR TEHSIL (cell cost 2.00); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| D.I.KHAN DISTRICT | D.I.KHAN TEHSIL | 481,757 | PAROA TEHSIL | 112,522 | medium | 112,522 persons (source-year count) of D.I.KHAN TEHSIL fall in PAROA TEHSIL (cell cost 2.00); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| D.I.KHAN DISTRICT | DARABAN TEHSIL | 89,413 | PAROA TEHSIL | 18,180 | medium | 18,180 persons (source-year count) of DARABAN TEHSIL fall in PAROA TEHSIL (cell cost 2.52); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| D.I.KHAN DISTRICT | KULACHI TEHSIL | 69,681 | DARABAN TEHSIL | 2,425 | medium | 2,425 persons (source-year count) of KULACHI TEHSIL fall in DARABAN TEHSIL (cell cost 2.38); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| GUJRANWALA DISTRICT | KAMOKI TEHSIL | 414,722 | NOWSHERA VIRKAN TEHSIL | 9,356 | medium | 9,356 persons (source-year count) of KAMOKI TEHSIL fall in NOWSHERA VIRKAN TEHSIL (cell cost 2.64); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| HYDERABAD DISTRICT | TANDO ALLAHYAR TALUKA | 493,526 | CHAMBER TALUKA | 125,558 | medium | 125,558 persons (source-year count) of TANDO ALLAHYAR TALUKA fall in CHAMBER TALUKA (cell cost 2.34); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| HYDERABAD DISTRICT | TANDO ALLAHYAR TALUKA | 493,526 | JHANDO MARI TALUKA | 141,913 | medium | 141,913 persons (source-year count) of TANDO ALLAHYAR TALUKA fall in JHANDO MARI TALUKA (cell cost 2.41); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| HYDERABAD DISTRICT | TANDO MUHAMMAD KHAN TALUKA | 351,815 | BULRI SHAH KARIM TALUKA | 157,683 | medium | 157,683 persons (source-year count) of TANDO MUHAMMAD KHAN TALUKA fall in BULRI SHAH KARIM TALUKA (cell cost 2.57); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| HYDERABAD DISTRICT | TANDO MUHAMMAD KHAN TALUKA | 351,815 | TANDO GHULAM HYDER TALUKA | 57,025 | medium | 57,025 persons (source-year count) of TANDO MUHAMMAD KHAN TALUKA fall in TANDO GHULAM HYDER TALUKA (cell cost 2.69); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| JAFARABAD DISTRICT | JHAT PAT TEHSIL | 164,196 | FARIDABAD TEHSIL | 33,136 | medium | 33,136 persons (source-year count) of JHAT PAT TEHSIL fall in FARIDABAD TEHSIL (cell cost 2.34); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| JAFARABAD DISTRICT | SOHBATPUR TEHSIL | 108,391 | FARIDABAD TEHSIL | 264 | medium | 264 persons (source-year count) of SOHBATPUR TEHSIL fall in FARIDABAD TEHSIL (cell cost 2.32); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| KASUR DISTRICT | KASUR TEHSIL | 1,157,072 | MODEL TOWN TEHSIL | 21,369 | medium | 21,369 persons (source-year count) of KASUR TEHSIL fall in MODEL TOWN TEHSIL (cell cost 2.64); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| KHARAN DISTRICT | KHARAN TEHSIL | 116,541 | SHAHGORI SUB-TEHSIL | 19,641 | medium | 19,641 persons (source-year count) of KHARAN TEHSIL fall in SHAHGORI SUB-TEHSIL (cell cost 2.53); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| KHARAN DISTRICT | WASHUK SUB-TEHSIL | 21,969 | NAG SUB-TEHSIL | 19,956 | medium | 19,956 persons (source-year count) of WASHUK SUB-TEHSIL fall in NAG SUB-TEHSIL (cell cost 2.21); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| KHUSHAB DISTRICT | KHUSHAB TEHSIL | 731,028 | NOWSHERA TEHSIL | 87,922 | medium | 87,922 persons (source-year count) of KHUSHAB TEHSIL fall in NOWSHERA TEHSIL (cell cost 2.26); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| KHUSHAB DISTRICT | KHUSHAB TEHSIL | 731,028 | QUAIDABAD TEHSIL | 162,997 | medium | 162,997 persons (source-year count) of KHUSHAB TEHSIL fall in QUAIDABAD TEHSIL (cell cost 2.32); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| KHUSHAB DISTRICT | NURPUR TEHSIL | 174,683 | NOORPUR TEHSIL | 174,683 | medium | 174,683 persons (source-year count) of NURPUR TEHSIL fall in NOORPUR TEHSIL (cell cost 2.00); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| LARKANA DISTRICT | MIRO KHAN TALUKA | 181,808 | SUJAWAL JUNEJO TALUKA | 83,026 | medium | 83,026 persons (source-year count) of MIRO KHAN TALUKA fall in SUJAWAL JUNEJO TALUKA (cell cost 2.21); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| LARKANA DISTRICT | SHAHDADKOT TALUKA | 190,325 | QUBO SAEED KHAN TALUKA | 63,706 | medium | 63,706 persons (source-year count) of SHAHDADKOT TALUKA fall in QUBO SAEED KHAN TALUKA (cell cost 2.56); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| LOWER DIR DISTRICT | TIMARGARA SUB-DIVISION | 528,292 | SAMARBAGH SUB-DIVISION | 130,020 | medium | 130,020 persons (source-year count) of TIMARGARA SUB-DIVISION fall in SAMARBAGH SUB-DIVISION (cell cost 2.00); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| MANSEHRA DISTRICT | TRIBAL AREA ADJOINING MANSEHRA DISTRICT (F.R.KALA DHAKA) | 174,682 | JUDBA TEHSIL | 84,628 | medium | 84,628 persons (source-year count) of TRIBAL AREA ADJOINING MANSEHRA DISTRICT (F.R.KALA DHAKA) fall in JUDBA TEHSIL (cell cost 4.00); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| MANSEHRA DISTRICT | TRIBAL AREA ADJOINING MANSEHRA DISTRICT (F.R.KALA DHAKA) | 174,682 | KHANDER TEHSIL | 90,054 | medium | 90,054 persons (source-year count) of TRIBAL AREA ADJOINING MANSEHRA DISTRICT (F.R.KALA DHAKA) fall in KHANDER TEHSIL (cell cost 4.00); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| MARDAN DISTRICT | MARDAN TEHSIL | 1,057,394 | KATLANG TEHSIL | 193,377 | medium | 193,377 persons (source-year count) of MARDAN TEHSIL fall in KATLANG TEHSIL (cell cost 2.31); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| MARDAN DISTRICT | TAKHT BHAI TEHSIL | 402,706 | KATLANG TEHSIL | 28,169 | medium | 28,169 persons (source-year count) of TAKHT BHAI TEHSIL fall in KATLANG TEHSIL (cell cost 2.36); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| MASTUNG DISTRICT | DASHT SUB-TEHSIL | 35,077 | QUETTA CITY TEHSIL | 10,507 | medium | 10,507 persons (source-year count) of DASHT SUB-TEHSIL fall in QUETTA CITY TEHSIL (cell cost 2.47); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| MIRPUR KHAS DISTRICT | DIGRI TALUKA | 298,652 | JHUDO TALUKA | 146,013 | medium | 146,013 persons (source-year count) of DIGRI TALUKA fall in JHUDO TALUKA (cell cost 2.49); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| MIRPUR KHAS DISTRICT | DIGRI TALUKA | 298,652 | SHUJAABAD TALUKA | 5,367 | medium | 5,367 persons (source-year count) of DIGRI TALUKA fall in SHUJAABAD TALUKA (cell cost 2.76); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| MIRPUR KHAS DISTRICT | MIRPUR KHAS TALUKA | 428,275 | HUSSAIN BUX MARI TALUKA | 83,219 | medium | 83,219 persons (source-year count) of MIRPUR KHAS TALUKA fall in HUSSAIN BUX MARI TALUKA (cell cost 2.71); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| MIRPUR KHAS DISTRICT | MIRPUR KHAS TALUKA | 428,275 | SHUJAABAD TALUKA | 93,416 | medium | 93,416 persons (source-year count) of MIRPUR KHAS TALUKA fall in SHUJAABAD TALUKA (cell cost 2.68); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| NAROWAL DISTRICT | NAROWAL TEHSIL | 627,300 | ZAFARWAL TEHSIL | 201,421 | medium | 201,421 persons (source-year count) of NAROWAL TEHSIL fall in ZAFARWAL TEHSIL (cell cost 2.68); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| NAROWAL DISTRICT | SHAKARGARH TEHSIL | 637,797 | ZAFARWAL TEHSIL | 116,942 | medium | 116,942 persons (source-year count) of SHAKARGARH TEHSIL fall in ZAFARWAL TEHSIL (cell cost 2.25); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| NASIRABAD DISTRICT | D.M.JAMALI TEHSIL | 104,519 | DERA MURAD JAMALI TEHSIL | 104,107 | medium | 104,107 persons (source-year count) of D.M.JAMALI TEHSIL fall in DERA MURAD JAMALI TEHSIL (cell cost 2.00); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| NASIRABAD DISTRICT | TAMBOO TEHSIL | 91,341 | BABA KOT TEHSIL | 19,531 | medium | 19,531 persons (source-year count) of TAMBOO TEHSIL fall in BABA KOT TEHSIL (cell cost 2.06); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| NAUSHAHRO FEROZE DISTRICT | BHIRIA TALUKA | 265,206 | KANDIARO TALUKA | 61,086 | medium | 61,086 persons (source-year count) of BHIRIA TALUKA fall in KANDIARO TALUKA (cell cost 2.56); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| NAUSHAHRO FEROZE DISTRICT | KANDIARO TALUKA | 316,788 | MEHRABPUR TALUKA | 155,345 | medium | 155,345 persons (source-year count) of KANDIARO TALUKA fall in MEHRABPUR TALUKA (cell cost 2.27); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| NAWAB SHAH DISTRICT | DAULATPUR TALUKA | 246,797 | KAZI AHMED TALUKA | 246,797 | medium | 246,797 persons (source-year count) of DAULATPUR TALUKA fall in KAZI AHMED TALUKA (cell cost 2.00); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| NAWAB SHAH DISTRICT | NAWAB SHAH TALUKA | 576,653 | DAUR TALUKA | 304,625 | medium | 304,625 persons (source-year count) of NAWAB SHAH TALUKA fall in DAUR TALUKA (cell cost 2.42); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| NAWAB SHAH DISTRICT | SAKRAND TALUKA | 279,134 | NAWABSHAH TALUKA | 9,274 | medium | 9,274 persons (source-year count) of SAKRAND TALUKA fall in NAWABSHAH TALUKA (cell cost 2.46); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| PANJGUR DISTRICT | PAROME SUB-TEHSIL | 44,626 | GOWARGO TEHSIL | 24,377 | medium | 24,377 persons (source-year count) of PAROME SUB-TEHSIL fall in GOWARGO TEHSIL (cell cost 2.35); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| SANGHAR DISTRICT | KHIPRO TALUKA | 327,185 | SINDHRI TALUKA | 100,394 | medium | 100,394 persons (source-year count) of KHIPRO TALUKA fall in SINDHRI TALUKA (cell cost 2.40); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| SANGHAR DISTRICT | KHIPRO TALUKA | 327,185 | PITHORO TALUKA | 1,702 | medium | 1,702 persons (source-year count) of KHIPRO TALUKA fall in PITHORO TALUKA (cell cost 2.38); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| SHANGLA DISTRICT | BESHAM TEHSIL | 57,739 | BISHAM TEHSIL | 57,739 | medium | 57,739 persons (source-year count) of BESHAM TEHSIL fall in BISHAM TEHSIL (cell cost 2.00); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| SHANGLA DISTRICT | MARTOONG TEHSIL | 57,441 | ALPURI TEHSIL | 57,441 | medium | 57,441 persons (source-year count) of MARTOONG TEHSIL fall in ALPURI TEHSIL (cell cost 2.00); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| SIALKOT DISTRICT | DASKA TEHSIL | 860,611 | SAMBRIAL TEHSIL | 255,176 | medium | 255,176 persons (source-year count) of DASKA TEHSIL fall in SAMBRIAL TEHSIL (cell cost 2.26); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| SIALKOT DISTRICT | SIALKOT TEHSIL | 1,250,999 | SAMBRIAL TEHSIL | 43,255 | medium | 43,255 persons (source-year count) of SIALKOT TEHSIL fall in SAMBRIAL TEHSIL (cell cost 2.41); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| SUKKUR DISTRICT | PANO AQIL TALUKA | 268,508 | KHANGARH TALUKA | 307 | medium | 307 persons (source-year count) of PANO AQIL TALUKA fall in KHANGARH TALUKA (cell cost 2.77); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| SUKKUR DISTRICT | ROHRI TALUKA | 224,362 | NEW SUKKUR TALUKA | 372 | medium | 372 persons (source-year count) of ROHRI TALUKA fall in NEW SUKKUR TALUKA (cell cost 2.74); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| SWABI DISTRICT | LAHOR TEHSIL | 304,803 | SWABI TEHSIL | 117,245 | medium | 117,245 persons (source-year count) of LAHOR TEHSIL fall in SWABI TEHSIL (cell cost 2.58); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| THARPARKAR DISTRICT | CHACHRO TALUKA | 357,757 | MITHI TALUKA | 25,233 | medium | 25,233 persons (source-year count) of CHACHRO TALUKA fall in MITHI TALUKA (cell cost 2.27); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| THARPARKAR DISTRICT | DIPLO TALUKA | 161,880 | KALOI TALUKA | 69,833 | medium | 69,833 persons (source-year count) of DIPLO TALUKA fall in KALOI TALUKA (cell cost 2.12); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| THARPARKAR DISTRICT | MITHI TALUKA | 241,548 | ISLAMKOT TALUKA | 137,826 | medium | 137,826 persons (source-year count) of MITHI TALUKA fall in ISLAMKOT TALUKA (cell cost 2.55); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| THARPARKAR DISTRICT | MITHI TALUKA | 241,548 | KALOI TALUKA | 3,818 | medium | 3,818 persons (source-year count) of MITHI TALUKA fall in KALOI TALUKA (cell cost 2.67); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| TOBA TEK SINGH DISTRICT | KAMALIA TEHSIL | 509,462 | PIRMAHAL TEHSIL | 288,592 | medium | 288,592 persons (source-year count) of KAMALIA TEHSIL fall in PIRMAHAL TEHSIL (cell cost 2.45); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| TOBA TEK SINGH DISTRICT | TOBA TEK SINGH TEHSIL | 617,035 | KAMALIA TEHSIL | 62,804 | medium | 62,804 persons (source-year count) of TOBA TEK SINGH TEHSIL fall in KAMALIA TEHSIL (cell cost 2.59); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| UPPER DIR DISTRICT | DIR SUB-DIVISION | 343,464 | WARI SUB-DIVISION | 4,082 | medium | 4,082 persons (source-year count) of DIR SUB-DIVISION fall in WARI SUB-DIVISION (cell cost 2.26); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |
| UPPER DIR DISTRICT | WARI SUB-DIVISION | 232,394 | TEMERGARA SUB-DIVISION | 61,407 | medium | 61,407 persons (source-year count) of WARI SUB-DIVISION fall in TEMERGARA SUB-DIVISION (cell cost 2.63); inferred: another balancing allocation exists but is less parsimonious under the adjacency prior |

The Dir case: the 1998 Lower Dir sub-divisions (Timargara, Jandul) and Upper Dir (Dir, Wari) became seven sub-divisions in 2017, 61,407 persons moved from Upper to Lower Dir, and the tables alone cannot say which 1998 sub-division Lal Qila and Samarbagh were cut from. The Mirpur Khas case: Sindhri taluka (150,628 in 1998 terms) draws from Mirpur Khas taluka and from Khipro (Sanghar); the share of Mirpur Khas is an inference.

## 7. Area weights
Area weights use PBS's published 2017 areas (Census 2017 Table 1): area of the 2017 unit times the share of its restated 1998 population that came from the 1998 unit. Rows by basis: identity 313, pbs_area_2017_exact 191, pbs_area_2017_uniform_density 89, implied_2017_area_uniform_density 5. PBS printed no sub-district areas for Kohistan and Killa Saifullah in 2017; there the 2017 unit's area is the one implied by the 2023 tables through the 2017 -> 2023 crosswalk (flagged implied_2017_area_uniform_density). As a check, the area of each 1998 unit implied by the crosswalk is compared with the area printed in the 1951-98 report: the median ratio is 1.00 and 282 of the 335 units with a printed 1998 area agree within 10 percent (columns area_1998_implied_km2 and area_1998_pco_km2). The disagreements are mostly in Balochistan and FATA, where the published areas themselves changed between reports.

## 8. Open items
1. Lahore 1998: the City / Cantt tehsil split is not in the 1951-98 report; one unit for now.
2. The 1998 Karachi towns are 2001 units; Karachi is one unit as agreed.
3. The uniform-density assumption in area weights applies to rows where a 2017 unit has more than one 1998 source (89 rows); a PBS 1998 or 2017 tehsil shapefile would replace it with measurement.
4. The chained 1998 -> 2023 weights multiply two PBS-based layers; a row is only as good as the weaker layer, which the confidence column records.

## 9. Every split, merge and renamed row (1998 -> 2017)
| district_group | unit_1998 | pop_1998 | unit_2017 | pop_1998_restated_2017 | flow_1998 | pop_weight | area_weight | method | confidence |
|---|---|---|---|---|---|---|---|---|---|
| ABBOTTABAD DISTRICT | ABBOTTABAD TEHSIL | 880,666 | ABBOTTABAD TEHSIL | 628,766 | 628,766 | 0.7140 | 0.7311 | split | high |
| ABBOTTABAD DISTRICT | ABBOTTABAD TEHSIL | 880,666 | HAVELIAN TEHSIL | 251,900 | 251,900 | 0.2860 | 0.2689 | split | high |
| ATTOCK DISTRICT | ATTOCK TEHSIL | 500,770 | ATTOCK TEHSIL | 261,829 | 261,829 | 0.5229 | 0.7422 | split | high |
| ATTOCK DISTRICT | ATTOCK TEHSIL | 500,770 | HAZRO TEHSIL | 238,941 | 238,941 | 0.4771 | 0.2578 | split | high |
| AWARAN DISTRICT | AWARAN TEHSIL | 49,586 | AWARAN TEHSIL | 27,156 | 27,156 | 0.5477 | 0.7407 | split | high |
| AWARAN DISTRICT | AWARAN TEHSIL | 49,586 | GISHKORE SUB-TEHSIL | 22,430 | 22,430 | 0.4523 | 0.2593 | split | high |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | GOLARCHI TALUKA | 191,580 | GOLARCHI (S.F.RAHU) TALUKA | 182,691 | 182,691 | 0.9536 | 0.9819 | split | high |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | GOLARCHI TALUKA | 191,580 | TANDO GHULAM HYDER TALUKA | 114,751 | 8,889 | 0.0464 | 0.0181 | split_and_merge | medium |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | HALA TALUKA | 240,497 | HALA TALUKA | 161,981 | 126,299 | 0.5252 | 0.5131 | split_and_merge | high |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | HALA TALUKA | 240,497 | SAEEDABAD TALUKA | 114,198 | 114,198 | 0.4748 | 0.4869 | split | high |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | MATIARI TALUKA | 253,747 | HALA TALUKA | 161,981 | 35,682 | 0.1406 | 0.1591 | split_and_merge | high |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | MATIARI TALUKA | 253,747 | MATIARI TALUKA | 218,065 | 218,065 | 0.8594 | 0.8409 | split | high |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | MATLI TALUKA | 312,356 | MATLI TALUKA | 283,273 | 283,273 | 0.9069 | 0.9613 | split | high |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | MATLI TALUKA | 312,356 | TANDO MUHAMMAD KHAN TALUKA | 166,190 | 29,083 | 0.0931 | 0.0387 | split_and_merge | medium |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | TALHAR TALUKA | 150,158 | TALHAR TALUKA | 107,902 | 101,321 | 0.6748 | 0.7630 | split_and_merge | high |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | TALHAR TALUKA | 150,158 | TANDO GHULAM HYDER TALUKA | 114,751 | 48,837 | 0.3252 | 0.2370 | split_and_merge | medium |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | TANDO ALLAHYAR TALUKA | 493,526 | CHAMBER TALUKA | 125,558 | 125,558 | 0.2544 | 0.3108 | split | medium |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | TANDO ALLAHYAR TALUKA | 493,526 | JHANDO MARI TALUKA | 141,913 | 141,913 | 0.2875 | 0.4028 | split | medium |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | TANDO ALLAHYAR TALUKA | 493,526 | TANDO ALLAHYAR TALUKA | 226,055 | 226,055 | 0.4580 | 0.2864 | split | high |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | TANDO BAGHO TALUKA | 249,728 | TALHAR TALUKA | 107,902 | 6,581 | 0.0264 | 0.0201 | split_and_merge | medium |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | TANDO BAGHO TALUKA | 249,728 | TANDO BAGO TALUKA | 243,147 | 243,147 | 0.9736 | 0.9799 | split | high |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | TANDO MUHAMMAD KHAN TALUKA | 351,815 | BULRI SHAH KARIM TALUKA | 157,683 | 157,683 | 0.4482 | 0.6521 | split | medium |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | TANDO MUHAMMAD KHAN TALUKA | 351,815 | TANDO GHULAM HYDER TALUKA | 114,751 | 57,025 | 0.1621 | 0.1641 | split_and_merge | medium |
| BADIN DISTRICT|HYDERABAD DISTRICT|MATIARI DISTRICT|TANDO ALLAHYAR DISTRICT|TANDO MUHAMMAD KHAN DISTRICT | TANDO MUHAMMAD KHAN TALUKA | 351,815 | TANDO MUHAMMAD KHAN TALUKA | 166,190 | 137,107 | 0.3897 | 0.1838 | split_and_merge | high |
| BAHAWALPUR DISTRICT | BAHAWALPUR TEHSIL | 806,580 | BAHAWALPUR CITY TEHSIL | 419,542 | 419,542 | 0.5201 | 0.6667 | split | high |
| BAHAWALPUR DISTRICT | BAHAWALPUR TEHSIL | 806,580 | BAHAWALPUR SADDAR TEHSIL | 387,038 | 387,038 | 0.4799 | 0.3333 | split | high |
| BAHAWALPUR DISTRICT | KHAIRPUR TAMEWALI TEHSIL | 184,914 | KHAIRPUR TAMEWALI TEHSIL | 183,903 | 183,903 | 0.9945 | 0.9560 | split | high |
| BAHAWALPUR DISTRICT | KHAIRPUR TAMEWALI TEHSIL | 184,914 | YAZMAN TEHSIL | 406,798 | 1,011 | 0.0055 | 0.0440 | split_and_merge | medium |
| BAHAWALPUR DISTRICT | YAZMAN TEHSIL | 405,787 | YAZMAN TEHSIL | 406,798 | 405,787 | 1.0000 | 1.0000 | merge | high |
| BANNU DISTRICT | BANNU TEHSIL | 675,667 | BANNU TEHSIL | 572,957 | 572,957 | 0.8480 | 0.6536 | split | high |
| BANNU DISTRICT | BANNU TEHSIL | 675,667 | DOMEL TEHSIL | 102,710 | 102,710 | 0.1520 | 0.3464 | split | high |
| BUNER DISTRICT | DAGGAR/BUNER TEHSIL | 506,048 | DAGGAR TEHSIL | 197,120 | 197,120 | 0.3895 | 0.4086 | split | high |
| BUNER DISTRICT | DAGGAR/BUNER TEHSIL | 506,048 | GAGRA TEHSIL | 151,877 | 151,877 | 0.3001 | 0.2332 | split | high |
| BUNER DISTRICT | DAGGAR/BUNER TEHSIL | 506,048 | KHADO KHEL TEHSIL | 69,812 | 69,812 | 0.1380 | 0.1839 | split | high |
| BUNER DISTRICT | DAGGAR/BUNER TEHSIL | 506,048 | MANDANR TEHSIL | 87,239 | 87,239 | 0.1724 | 0.1743 | split | high |
| CHAKWAL DISTRICT | TALAGANG TEHSIL | 380,421 | LAWA TEHSIL | 95,626 | 95,626 | 0.2514 | 0.3104 | split | high |
| CHAKWAL DISTRICT | TALAGANG TEHSIL | 380,421 | TALA GANG TEHSIL | 284,795 | 284,795 | 0.7486 | 0.6896 | split | high |
| CHARSADDA DISTRICT | CHARSADDA TEHSIL | 767,903 | CHARSADDA TEHSIL | 527,152 | 527,152 | 0.6865 | 0.6857 | split | high |
| CHARSADDA DISTRICT | CHARSADDA TEHSIL | 767,903 | SHABQADAR TEHSIL | 240,751 | 240,751 | 0.3135 | 0.3143 | split | high |
| CHINIOT DISTRICT|JHANG DISTRICT | CHINIOT TEHSIL | 965,124 | BHAWANA TEHSIL | 272,754 | 272,754 | 0.2826 | 0.3326 | split | high |
| CHINIOT DISTRICT|JHANG DISTRICT | CHINIOT TEHSIL | 965,124 | CHINIOT TEHSIL | 382,876 | 382,876 | 0.3967 | 0.2683 | split | high |
| CHINIOT DISTRICT|JHANG DISTRICT | CHINIOT TEHSIL | 965,124 | LALIAN TEHSIL | 309,494 | 309,494 | 0.3207 | 0.3992 | split | high |
| CHINIOT DISTRICT|JHANG DISTRICT | JHANG TEHSIL | 1,199,166 | 18-HAZARI TEHSIL | 200,036 | 200,036 | 0.1668 | 0.3767 | split | high |
| CHINIOT DISTRICT|JHANG DISTRICT | JHANG TEHSIL | 1,199,166 | JHANG TEHSIL | 999,130 | 999,130 | 0.8332 | 0.6233 | split | high |
| DADU DISTRICT|JAMSHORO DISTRICT | K.N.SHAH TALUKA | 253,309 | KHAIRPUR NATHAN SHAH TALUKA | 253,309 | 253,309 | 1.0000 | 1.0000 | one_to_one_renamed | high |
| DADU DISTRICT|JAMSHORO DISTRICT | KOTRI TALUKA | 307,679 | KOTRI TALUKA | 207,574 | 207,574 | 0.6746 | 0.3134 | split | high |
| DADU DISTRICT|JAMSHORO DISTRICT | KOTRI TALUKA | 307,679 | MANJHAND TALUKA | 100,105 | 100,105 | 0.3254 | 0.6866 | split | high |
| DERA BUGTI DISTRICT | BAIKER SUB-TEHSIL | 5,404 | BAIKER SUB-TEHSIL | 5,305 | 5,305 | 0.9817 | 0.9934 | split | high |
| DERA BUGTI DISTRICT | BAIKER SUB-TEHSIL | 5,404 | PHELAWAGH TEHSIL | 11,760 | 99 | 0.0183 | 0.0066 | split_and_merge | high |
| DERA BUGTI DISTRICT | DERA BUGTI TEHSIL | 34,375 | DERA BUGTI TEHSIL | 32,403 | 32,403 | 0.9426 | 0.8843 | split | high |
| DERA BUGTI DISTRICT | DERA BUGTI TEHSIL | 34,375 | SUI TEHSIL | 62,699 | 1,972 | 0.0574 | 0.1157 | split_and_merge | high |
| DERA BUGTI DISTRICT | PHELAWAGH TEHSIL | 11,661 | PHELAWAGH TEHSIL | 11,760 | 11,661 | 1.0000 | 1.0000 | merge | high |
| DERA BUGTI DISTRICT | SUI TEHSIL | 60,727 | SUI TEHSIL | 62,699 | 60,727 | 1.0000 | 1.0000 | merge | high |
| DERA GHAZI KHAN DISTRICT | DERA GHAZI KHAN TEHSIL | 1,151,236 | DERA GHAZI KHAN TEHSIL | 712,930 | 712,930 | 0.6193 | 0.5275 | split | high |
| DERA GHAZI KHAN DISTRICT | DERA GHAZI KHAN TEHSIL | 1,151,236 | KOT CHHUTTA TEHSIL | 438,306 | 438,306 | 0.3807 | 0.4725 | split | high |
| DERA ISMAIL KHAN DISTRICT | D.I.KHAN TEHSIL | 481,757 | DERA ISMAIL KHAN TEHSIL | 362,790 | 362,790 | 0.7531 | 0.4310 | split | medium |
| DERA ISMAIL KHAN DISTRICT | D.I.KHAN TEHSIL | 481,757 | PAHARPUR TEHSIL | 218,589 | 6,445 | 0.0134 | 0.0180 | split_and_merge | medium |
| DERA ISMAIL KHAN DISTRICT | D.I.KHAN TEHSIL | 481,757 | PAROA TEHSIL | 130,702 | 112,522 | 0.2336 | 0.5510 | split_and_merge | medium |
| DERA ISMAIL KHAN DISTRICT | DARABAN TEHSIL | 89,413 | DARABAN TEHSIL | 73,658 | 71,233 | 0.7967 | 0.8607 | split_and_merge | high |
| DERA ISMAIL KHAN DISTRICT | DARABAN TEHSIL | 89,413 | PAROA TEHSIL | 130,702 | 18,180 | 0.2033 | 0.1393 | split_and_merge | medium |
| DERA ISMAIL KHAN DISTRICT | KULACHI TEHSIL | 69,681 | DARABAN TEHSIL | 73,658 | 2,425 | 0.0348 | 0.0396 | split_and_merge | medium |
| DERA ISMAIL KHAN DISTRICT | KULACHI TEHSIL | 69,681 | KULACHI TEHSIL | 67,256 | 67,256 | 0.9652 | 0.9604 | split | high |
| DERA ISMAIL KHAN DISTRICT | PAHAR PUR TEHSIL | 212,144 | PAHARPUR TEHSIL | 218,589 | 212,144 | 1.0000 | 1.0000 | merge | high |
| FAISALABAD DISTRICT | JARANWALA TEHSIL | 1,054,698 | JARANWALA TEHSIL | 1,061,846 | 1,054,698 | 1.0000 | 1.0000 | merge | high |
| FAISALABAD DISTRICT | SAMMUNDRI TEHSIL | 515,785 | JARANWALA TEHSIL | 1,061,846 | 7,148 | 0.0139 | 0.0159 | split_and_merge | high |
| FAISALABAD DISTRICT | SAMMUNDRI TEHSIL | 515,785 | SAMMUNDRI TEHSIL | 508,637 | 508,637 | 0.9861 | 0.9841 | split | high |
| FR D.I.KHAN | TRIBAL AREA ADJOINING D.I.KHAN DISTRICT | 38,990 | TRIBAL AREA ADJ. DERA ISMAIL KHAN DISTRICT | 38,990 | 38,990 | 1.0000 | 1.0000 | one_to_one_renamed | high |
| GHOTKI DISTRICT|SUKKUR DISTRICT | KHANGARH TALUKA | 85,866 | KHANGARH TALUKA | 86,173 | 85,866 | 1.0000 | 1.0000 | merge | high |
| GHOTKI DISTRICT|SUKKUR DISTRICT | PANO AQIL TALUKA | 268,508 | KHANGARH TALUKA | 86,173 | 307 | 0.0011 | 0.0067 | split_and_merge | medium |
| GHOTKI DISTRICT|SUKKUR DISTRICT | PANO AQIL TALUKA | 268,508 | PANO AQIL TALUKA | 268,201 | 268,201 | 0.9989 | 0.9933 | split | high |
| GHOTKI DISTRICT|SUKKUR DISTRICT | ROHRI TALUKA | 224,362 | NEW SUKKUR TALUKA | 159,475 | 372 | 0.0017 | 0.0003 | split_and_merge | medium |
| GHOTKI DISTRICT|SUKKUR DISTRICT | ROHRI TALUKA | 224,362 | ROHRI TALUKA | 223,990 | 223,990 | 0.9983 | 0.9997 | split | high |
| GHOTKI DISTRICT|SUKKUR DISTRICT | SUKKUR TALUKA | 374,178 | NEW SUKKUR TALUKA | 159,475 | 159,103 | 0.4252 | 0.3031 | split_and_merge | high |
| GHOTKI DISTRICT|SUKKUR DISTRICT | SUKKUR TALUKA | 374,178 | SUKKUR CITY TALUKA | 215,075 | 215,075 | 0.5748 | 0.6969 | split | high |
| GUJRANWALA DISTRICT | GUJRANWALA CITY TEHSIL | 1,280,358 | GUJRANWALA CITY TEHSIL | 115,122 | 115,122 | 0.0899 | 0.2065 | split | high |
| GUJRANWALA DISTRICT | GUJRANWALA CITY TEHSIL | 1,280,358 | GUJRANWALA SADDAR TEHSIL | 1,812,137 | 1,165,236 | 0.9101 | 0.7935 | split_and_merge | high |
| GUJRANWALA DISTRICT | GUJRANWALA SADDAR TEHSIL | 646,901 | GUJRANWALA SADDAR TEHSIL | 1,812,137 | 646,901 | 1.0000 | 1.0000 | merge | high |
| GUJRANWALA DISTRICT | KAMOKI TEHSIL | 414,722 | KAMOKE TEHSIL | 405,366 | 405,366 | 0.9774 | 0.9824 | split | high |
| GUJRANWALA DISTRICT | KAMOKI TEHSIL | 414,722 | NOWSHERA VIRKAN TEHSIL | 424,082 | 9,356 | 0.0226 | 0.0176 | split_and_merge | medium |
| GUJRANWALA DISTRICT | NOWSHERA VIRKAN TEHSIL | 414,726 | NOWSHERA VIRKAN TEHSIL | 424,082 | 414,726 | 1.0000 | 1.0000 | merge | high |
| HANGU DISTRICT | HANGU TEHSIL | 314,529 | HANGU TEHSIL | 163,117 | 163,117 | 0.5186 | 0.6098 | split | high |
| HANGU DISTRICT | HANGU TEHSIL | 314,529 | TALL TEHSIL | 151,412 | 151,412 | 0.4814 | 0.3902 | split | high |
| HARNAI DISTRICT|SIBI DISTRICT | HARNAI TEHSIL | 76,652 | HARNAI TEHSIL | 51,482 | 51,482 | 0.6716 | 0.1039 | split | high |
| HARNAI DISTRICT|SIBI DISTRICT | HARNAI TEHSIL | 76,652 | KHOAST SUB-TEHSIL | 9,908 | 9,908 | 0.1293 | 0.6497 | split | high |
| HARNAI DISTRICT|SIBI DISTRICT | HARNAI TEHSIL | 76,652 | SHAHRIG TEHSIL | 15,262 | 15,262 | 0.1991 | 0.2464 | split | high |
| JACOBABAD DISTRICT|KASHMORE DISTRICT | KANDHKOT TALUKA | 393,501 | KANDHKOT TALUKA | 217,447 | 217,447 | 0.5526 | 0.5163 | split | high |
| JACOBABAD DISTRICT|KASHMORE DISTRICT | KANDHKOT TALUKA | 393,501 | TANGWANI TALUKA | 190,774 | 176,054 | 0.4474 | 0.4837 | split_and_merge | high |
| JACOBABAD DISTRICT|KASHMORE DISTRICT | THUL TALUKA | 356,705 | TANGWANI TALUKA | 190,774 | 14,720 | 0.0413 | 0.0379 | split_and_merge | high |
| JACOBABAD DISTRICT|KASHMORE DISTRICT | THUL TALUKA | 356,705 | THUL TALUKA | 341,985 | 341,985 | 0.9587 | 0.9621 | split | high |
| JAFFARABAD DISTRICT|SOHBATPUR DISTRICT | GANDAKA TEHSIL | 57,727 | GANDHAKA TEHSIL | 52,767 | 52,767 | 0.9141 | 0.9678 | split | high |
| JAFFARABAD DISTRICT|SOHBATPUR DISTRICT | GANDAKA TEHSIL | 57,727 | USTA MUHAMMAD TEHSIL | 107,463 | 4,960 | 0.0859 | 0.0322 | split_and_merge | high |
| JAFFARABAD DISTRICT|SOHBATPUR DISTRICT | JHAT PAT TEHSIL | 164,196 | FARIDABAD TEHSIL | 33,400 | 33,136 | 0.2018 | 0.1646 | split_and_merge | medium |
| JAFFARABAD DISTRICT|SOHBATPUR DISTRICT | JHAT PAT TEHSIL | 164,196 | JHAT PAT TEHSIL | 131,060 | 131,060 | 0.7982 | 0.8354 | split | high |
| JAFFARABAD DISTRICT|SOHBATPUR DISTRICT | SOHBATPUR TEHSIL | 108,391 | FARIDABAD TEHSIL | 33,400 | 264 | 0.0024 | 0.0016 | split_and_merge | medium |
| JAFFARABAD DISTRICT|SOHBATPUR DISTRICT | SOHBATPUR TEHSIL | 108,391 | SANHRI TEHSIL | 66,681 | 66,681 | 0.6152 | 0.4969 | split | high |
| JAFFARABAD DISTRICT|SOHBATPUR DISTRICT | SOHBATPUR TEHSIL | 108,391 | SOHBATPUR TEHSIL | 41,446 | 41,446 | 0.3824 | 0.5014 | split | high |
| JAFFARABAD DISTRICT|SOHBATPUR DISTRICT | USTA MUHAMMAD TEHSIL | 102,503 | USTA MUHAMMAD TEHSIL | 107,463 | 102,503 | 1.0000 | 1.0000 | merge | high |
| JHELUM DISTRICT | DINA TEHSIL | 180,291 | DINA TEHSIL | 183,373 | 180,291 | 1.0000 | 1.0000 | merge | high |
| JHELUM DISTRICT | JHELUM TEHSIL | 336,651 | DINA TEHSIL | 183,373 | 3,082 | 0.0092 | 0.0191 | split_and_merge | high |
| JHELUM DISTRICT | JHELUM TEHSIL | 336,651 | JHELUM TEHSIL | 333,569 | 333,569 | 0.9908 | 0.9809 | split | high |
| KAMBAR SHAHDAD KOT DISTRICT|KHAIRPUR DISTRICT|LARKANA DISTRICT | DOKRI TALUKA | 308,975 | BAKRANI TALUKA | 171,813 | 139,942 | 0.4529 | 0.4566 | split_and_merge | high |
| KAMBAR SHAHDAD KOT DISTRICT|KHAIRPUR DISTRICT|LARKANA DISTRICT | DOKRI TALUKA | 308,975 | DOKRI TALUKA | 169,033 | 169,033 | 0.5471 | 0.5434 | split | high |
| KAMBAR SHAHDAD KOT DISTRICT|KHAIRPUR DISTRICT|LARKANA DISTRICT | KHAIRPUR TALUKA | 288,655 | KHAIRPUR TALUKA | 275,255 | 275,255 | 0.9536 | 0.9495 | split | high |
| KAMBAR SHAHDAD KOT DISTRICT|KHAIRPUR DISTRICT|LARKANA DISTRICT | KHAIRPUR TALUKA | 288,655 | KINGRI TALUKA | 228,630 | 13,400 | 0.0464 | 0.0505 | split_and_merge | high |
| KAMBAR SHAHDAD KOT DISTRICT|KHAIRPUR DISTRICT|LARKANA DISTRICT | KINGRI TALUKA | 214,066 | KINGRI TALUKA | 228,630 | 214,066 | 1.0000 | 1.0000 | merge | high |
| KAMBAR SHAHDAD KOT DISTRICT|KHAIRPUR DISTRICT|LARKANA DISTRICT | LARKANA TALUKA | 466,424 | BAKRANI TALUKA | 171,813 | 31,871 | 0.0683 | 0.1256 | split_and_merge | high |
| KAMBAR SHAHDAD KOT DISTRICT|KHAIRPUR DISTRICT|LARKANA DISTRICT | LARKANA TALUKA | 466,424 | LARKANA TALUKA | 434,553 | 434,553 | 0.9317 | 0.8744 | split | high |
| KAMBAR SHAHDAD KOT DISTRICT|KHAIRPUR DISTRICT|LARKANA DISTRICT | MIRO KHAN TALUKA | 181,808 | MIRO KHAN TALUKA | 98,782 | 98,782 | 0.5433 | 0.4928 | split | high |
| KAMBAR SHAHDAD KOT DISTRICT|KHAIRPUR DISTRICT|LARKANA DISTRICT | MIRO KHAN TALUKA | 181,808 | SUJAWAL JUNEJO TALUKA | 83,026 | 83,026 | 0.4567 | 0.5072 | split | medium |
| KAMBAR SHAHDAD KOT DISTRICT|KHAIRPUR DISTRICT|LARKANA DISTRICT | RATO DERO TALUKA | 227,373 | KINGRI TALUKA | 228,630 | 1,164 | 0.0051 | 0.0048 | split_and_merge | high |
| KAMBAR SHAHDAD KOT DISTRICT|KHAIRPUR DISTRICT|LARKANA DISTRICT | RATO DERO TALUKA | 227,373 | RATODERO TALUKA | 226,209 | 226,209 | 0.9949 | 0.9952 | split | high |
| KAMBAR SHAHDAD KOT DISTRICT|KHAIRPUR DISTRICT|LARKANA DISTRICT | SHAHDADKOT TALUKA | 190,325 | QUBO SAEED KHAN TALUKA | 63,706 | 63,706 | 0.3347 | 0.7114 | split | medium |
| KAMBAR SHAHDAD KOT DISTRICT|KHAIRPUR DISTRICT|LARKANA DISTRICT | SHAHDADKOT TALUKA | 190,325 | SHAHDAD KOT TALUKA | 126,619 | 126,619 | 0.6653 | 0.2886 | split | high |
| KAMBAR SHAHDAD KOT DISTRICT|KHAIRPUR DISTRICT|LARKANA DISTRICT | WARAH TALUKA | 283,227 | NASIRABAD TALUKA | 113,779 | 113,779 | 0.4017 | 0.3078 | split | high |
| KAMBAR SHAHDAD KOT DISTRICT|KHAIRPUR DISTRICT|LARKANA DISTRICT | WARAH TALUKA | 283,227 | WARAH TALUKA | 169,448 | 169,448 | 0.5983 | 0.6922 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | AIRPORT SUB-DIVISION | 88,027 | 88,027 | 0.0089 | 0.0116 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | ARAM BAGH SUB-DIVISION | 131,880 | 131,880 | 0.0134 | 0.0011 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | BALDIA SUB-DIVISION | 406,264 | 406,264 | 0.0412 | 0.0096 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | BIN QASIM SUB-DIVISION | 108,045 | 108,045 | 0.0110 | 0.1267 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | CIVIL LINES SUB-DIVISION | 282,580 | 282,580 | 0.0287 | 0.0207 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | FEROZABAD SUB-DIVISION | 558,702 | 558,702 | 0.0567 | 0.0057 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | GADAP SUB-DIVISION | 39,642 | 39,642 | 0.0040 | 0.3130 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | GARDEN SUB-DIVISION | 325,716 | 325,716 | 0.0330 | 0.0011 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | GULBERG SUB-DIVISION | 424,620 | 424,620 | 0.0431 | 0.0040 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | GULSHAN-E-IQBAL SUB-DIVISION | 440,447 | 440,447 | 0.0447 | 0.0082 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | GULZAR-E-HIJRI SUB-DIVISION | 122,852 | 122,852 | 0.0125 | 0.0224 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | HARBOUR SUB-DIVISION | 223,450 | 223,450 | 0.0227 | 0.0142 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | IBRAHIM HYDRI SUB-DIVISION | 483,770 | 483,770 | 0.0491 | 0.0275 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | JAMSHED QUARTERS SUB-DIVISION | 388,385 | 388,385 | 0.0394 | 0.0031 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | KORANGI SUB-DIVISION | 549,159 | 549,159 | 0.0557 | 0.0167 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | LANDHI SUB-DIVISION | 409,451 | 409,451 | 0.0415 | 0.0054 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | LIAQUATABAD SUB-DIVISION | 379,058 | 379,058 | 0.0385 | 0.0017 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | LYARI SUB-DIVISION | 594,966 | 594,966 | 0.0604 | 0.0017 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | MANGHOPIR SUB-DIVISION | 118,267 | 118,267 | 0.0120 | 0.0970 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | MAURIPUR SUB-DIVISION | 85,980 | 85,980 | 0.0087 | 0.1276 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | MODEL COLONY SUB-DIVISION | 252,271 | 252,271 | 0.0256 | 0.0026 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | MOMINABAD SUB-DIVISION | 596,593 | 596,593 | 0.0605 | 0.0054 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | MURAD MEMON SUB-DIVISION | 214,900 | 214,900 | 0.0218 | 0.0553 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | NAZIMABAD SUB-DIVISION | 363,193 | 363,193 | 0.0368 | 0.0023 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | NEW KARACHI SUB-DIVISION | 582,866 | 582,866 | 0.0591 | 0.0051 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | NORTH NAZIMABAD SUB-DIVISION | 528,194 | 528,194 | 0.0536 | 0.0065 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | ORANGI SUB-DIVISION | 337,186 | 337,186 | 0.0342 | 0.0026 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | SADDAR SUB-DIVISION | 133,437 | 133,437 | 0.0135 | 0.0099 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | SHAH FAISAL SUB-DIVISION | 348,234 | 348,234 | 0.0353 | 0.0060 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | SHAH MUREED SUB-DIVISION | 16,414 | 16,414 | 0.0017 | 0.0783 | split | high |
| KARACHI CENTRAL DISTRICT|KARACHI EAST DISTRICT|KARACHI SOUTH DISTRICT|KARACHI WEST DISTRICT|KORANGI DISTRICT|MALIR DISTRICT | KARACHI CITY DISTRICT (all towns, one unit) | 9,856,318 | SITE SUB-DIVISION | 321,769 | 321,769 | 0.0326 | 0.0071 | split | high |
| KARAK DISTRICT | KARAK TEHSIL | 162,128 | KARAK TEHSIL | 175,758 | 162,128 | 1.0000 | 1.0000 | merge | high |
| KARAK DISTRICT | TAKHT-E-NASRITI TEHSIL | 170,042 | KARAK TEHSIL | 175,758 | 13,630 | 0.0802 | 0.1423 | split_and_merge | high |
| KARAK DISTRICT | TAKHT-E-NASRITI TEHSIL | 170,042 | TAKHT-E-NASRATI TEHSIL | 156,412 | 156,412 | 0.9198 | 0.8577 | split | high |
| KASUR DISTRICT|LAHORE DISTRICT | KASUR TEHSIL | 1,157,072 | KASUR TEHSIL | 902,792 | 902,792 | 0.7802 | 0.7873 | split | high |
| KASUR DISTRICT|LAHORE DISTRICT | KASUR TEHSIL | 1,157,072 | KOT RADHA KISHAN TEHSIL | 232,911 | 232,911 | 0.2013 | 0.2099 | split | high |
| KASUR DISTRICT|LAHORE DISTRICT | KASUR TEHSIL | 1,157,072 | MODEL TOWN TEHSIL | 1,409,228 | 21,369 | 0.0185 | 0.0028 | split_and_merge | medium |
| KASUR DISTRICT|LAHORE DISTRICT | LAHORE CITY DISTRICT (all towns, one unit) | 6,318,745 | LAHORE CANTT TEHSIL | 918,730 | 918,730 | 0.1454 | 0.2638 | split | high |
| KASUR DISTRICT|LAHORE DISTRICT | LAHORE CITY DISTRICT (all towns, one unit) | 6,318,745 | LAHORE CITY TEHSIL | 2,219,399 | 2,219,399 | 0.3512 | 0.1211 | split | high |
| KASUR DISTRICT|LAHORE DISTRICT | LAHORE CITY DISTRICT (all towns, one unit) | 6,318,745 | MODEL TOWN TEHSIL | 1,409,228 | 1,387,859 | 0.2196 | 0.1968 | split_and_merge | high |
| KASUR DISTRICT|LAHORE DISTRICT | LAHORE CITY DISTRICT (all towns, one unit) | 6,318,745 | RAIWIND TEHSIL | 357,934 | 357,934 | 0.0566 | 0.2643 | split | high |
| KASUR DISTRICT|LAHORE DISTRICT | LAHORE CITY DISTRICT (all towns, one unit) | 6,318,745 | SHALIMAR TEHSIL | 1,434,823 | 1,434,823 | 0.2271 | 0.1540 | split | high |
| KECH DISTRICT | BULEDA SUB-TEHSIL | 33,265 | BULAIDA SUB-TEHSIL | 35,251 | 33,265 | 1.0000 | 1.0000 | merge | high |
| KECH DISTRICT | ZAMURAN SUB-TEHSIL | 39,842 | BULAIDA SUB-TEHSIL | 35,251 | 1,986 | 0.0498 | 0.0715 | split_and_merge | high |
| KECH DISTRICT | ZAMURAN SUB-TEHSIL | 39,842 | ZAMORAN SUB-TEHSIL | 37,856 | 37,856 | 0.9502 | 0.9285 | split | high |
| KHANEWAL DISTRICT | KHANEWAL TEHSIL | 542,602 | KHANEWAL TEHSIL | 607,012 | 542,602 | 1.0000 | 1.0000 | merge | high |
| KHANEWAL DISTRICT | MIAN CHANNU TEHSIL | 612,436 | KHANEWAL TEHSIL | 607,012 | 64,410 | 0.1052 | 0.0642 | split_and_merge | high |
| KHANEWAL DISTRICT | MIAN CHANNU TEHSIL | 612,436 | MIAN CHANNU TEHSIL | 548,026 | 548,026 | 0.8948 | 0.9358 | split | high |
| KHARAN DISTRICT|WASHUK DISTRICT | BESIMA SUB-TEHSIL | 38,555 | BESIMA SUB-TEHSIL | 16,740 | 16,740 | 0.4342 | 0.4671 | split | high |
| KHARAN DISTRICT|WASHUK DISTRICT | BESIMA SUB-TEHSIL | 38,555 | WASHUK SUB-TEHSIL | 23,828 | 21,815 | 0.5658 | 0.5329 | split_and_merge | high |
| KHARAN DISTRICT|WASHUK DISTRICT | KHARAN TEHSIL | 116,541 | KHARAN TEHSIL | 43,772 | 43,772 | 0.3756 | 0.2735 | split | high |
| KHARAN DISTRICT|WASHUK DISTRICT | KHARAN TEHSIL | 116,541 | SAR KHARAN TEHSIL | 29,768 | 29,768 | 0.2554 | 0.1909 | split | high |
| KHARAN DISTRICT|WASHUK DISTRICT | KHARAN TEHSIL | 116,541 | SHAHGORI SUB-TEHSIL | 19,641 | 19,641 | 0.1685 | 0.1933 | split | medium |
| KHARAN DISTRICT|WASHUK DISTRICT | KHARAN TEHSIL | 116,541 | SUB TEHSIL TOHMULK | 23,360 | 23,360 | 0.2004 | 0.3423 | split | high |
| KHARAN DISTRICT|WASHUK DISTRICT | WASHUK SUB-TEHSIL | 21,969 | NAG SUB-TEHSIL | 19,956 | 19,956 | 0.9084 | 0.8726 | split | medium |
| KHARAN DISTRICT|WASHUK DISTRICT | WASHUK SUB-TEHSIL | 21,969 | WASHUK SUB-TEHSIL | 23,828 | 2,013 | 0.0916 | 0.1274 | split_and_merge | high |
| KHUSHAB DISTRICT | KHUSHAB TEHSIL | 731,028 | KHUSHAB TEHSIL | 480,109 | 480,109 | 0.6568 | 0.5273 | split | high |
| KHUSHAB DISTRICT | KHUSHAB TEHSIL | 731,028 | NOWSHERA TEHSIL | 87,922 | 87,922 | 0.1203 | 0.2034 | split | medium |
| KHUSHAB DISTRICT | KHUSHAB TEHSIL | 731,028 | QUAIDABAD TEHSIL | 162,997 | 162,997 | 0.2230 | 0.2693 | split | medium |
| KHUSHAB DISTRICT | NURPUR TEHSIL | 174,683 | NOORPUR TEHSIL | 174,683 | 174,683 | 1.0000 | 1.0000 | one_to_one_renamed | medium |
| KILLA ABDULLAH DISTRICT | GULISTAN TEHSIL | 130,561 | GULISTAN TEHSIL | 66,883 | 66,883 | 0.5123 | 0.8663 | split | high |
| KILLA ABDULLAH DISTRICT | GULISTAN TEHSIL | 130,561 | KILLA ABDULLAH TEHSIL | 110,937 | 63,678 | 0.4877 | 0.1337 | split_and_merge | high |
| KILLA ABDULLAH DISTRICT | KILLA ABDULLAH TEHSIL | 47,259 | KILLA ABDULLAH TEHSIL | 110,937 | 47,259 | 1.0000 | 1.0000 | merge | high |
| KILLA SAIFULLAH DISTRICT | KILLA SAIFULLAH TEHSIL | 92,141 | KILLA SAIFULLAH TEHSIL | 63,472 | 63,472 | 0.6889 | 0.6421 | split | high |
| KILLA SAIFULLAH DISTRICT | KILLA SAIFULLAH TEHSIL | 92,141 | SHINKI SUB-TEHSIL | 28,669 | 28,669 | 0.3111 | 0.3579 | split | high |
| KILLA SAIFULLAH DISTRICT | MUSLIM BAGH TEHSIL | 69,038 | KAN MEHTARZAI SUB-TEHSIL | 24,168 | 24,168 | 0.3501 | 0.2888 | split | high |
| KILLA SAIFULLAH DISTRICT | MUSLIM BAGH TEHSIL | 69,038 | MUSLIM BAGH TEHSIL | 44,870 | 44,870 | 0.6499 | 0.7112 | split | high |
| KOHAT DISTRICT | KOHAT TEHSIL | 461,842 | KOHAT TEHSIL | 470,648 | 461,842 | 1.0000 | 1.0000 | merge | high |
| KOHAT DISTRICT | LACHI TEHSIL | 100,802 | KOHAT TEHSIL | 470,648 | 8,806 | 0.0874 | 0.0229 | split_and_merge | high |
| KOHAT DISTRICT | LACHI TEHSIL | 100,802 | LACHI TEHSIL | 91,996 | 91,996 | 0.9126 | 0.9771 | split | high |
| KOHISTAN DISTRICT | DASSU TEHSIL | 184,746 | DASSU SUB-DIVISION | 137,519 | 137,519 | 0.7444 | 0.6662 | split | high |
| KOHISTAN DISTRICT | DASSU TEHSIL | 184,746 | KANDIA SUB-DIVISION | 46,437 | 46,437 | 0.2514 | 0.3326 | split | high |
| KOHISTAN DISTRICT | DASSU TEHSIL | 184,746 | PALAS SUB-DIVISION | 166,403 | 790 | 0.0043 | 0.0012 | split_and_merge | high |
| KOHISTAN DISTRICT | PALAS TEHSIL | 165,613 | PALAS SUB-DIVISION | 166,403 | 165,613 | 1.0000 | 1.0000 | merge | high |
| KOHLU DISTRICT | KOHLU TEHSIL | 49,025 | GRISANI SUB-TEHSIL | 4,057 | 4,057 | 0.0828 | 0.1849 | split | high |
| KOHLU DISTRICT | KOHLU TEHSIL | 49,025 | KOHLU TEHSIL | 26,702 | 26,702 | 0.5447 | 0.2455 | split | high |
| KOHLU DISTRICT | KOHLU TEHSIL | 49,025 | TAMBOO TEHSIL | 18,266 | 18,266 | 0.3726 | 0.5696 | split | high |
| LAKKI MARWAT DISTRICT | LAKKI MARWAT TEHSIL | 337,306 | LAKKI MARWAT TEHSIL | 339,934 | 337,306 | 1.0000 | 1.0000 | merge | high |
| LAKKI MARWAT DISTRICT | NAURANG TEHSIL | 152,719 | LAKKI MARWAT TEHSIL | 339,934 | 2,628 | 0.0172 | 0.0306 | split_and_merge | high |
| LAKKI MARWAT DISTRICT | NAURANG TEHSIL | 152,719 | SARAI NAURANG TEHSIL | 150,091 | 150,091 | 0.9828 | 0.9694 | split | high |
| LODHRAN DISTRICT | DUNYAPUR TEHSIL | 338,080 | DUNYAPUR TEHSIL | 350,202 | 338,080 | 1.0000 | 1.0000 | merge | high |
| LODHRAN DISTRICT | LODHRAN TEHSIL | 472,188 | DUNYAPUR TEHSIL | 350,202 | 12,122 | 0.0257 | 0.0270 | split_and_merge | high |
| LODHRAN DISTRICT | LODHRAN TEHSIL | 472,188 | LODHRAN TEHSIL | 460,066 | 460,066 | 0.9743 | 0.9730 | split | high |
| LOWER DIR DISTRICT|UPPER DIR DISTRICT | DIR SUB-DIVISION | 343,464 | DIR SUB-DIVISION | 235,324 | 235,324 | 0.6851 | 0.6404 | split | high |
| LOWER DIR DISTRICT|UPPER DIR DISTRICT | DIR SUB-DIVISION | 343,464 | SHARINGAL SUB-DIVISION | 104,058 | 104,058 | 0.3030 | 0.3559 | split | high |
| LOWER DIR DISTRICT|UPPER DIR DISTRICT | DIR SUB-DIVISION | 343,464 | WARI SUB-DIVISION | 175,069 | 4,082 | 0.0119 | 0.0037 | split_and_merge | medium |
| LOWER DIR DISTRICT|UPPER DIR DISTRICT | JANDUL SUB-DIVISION | 189,357 | LAL QILA SUB-DIVISION | 129,305 | 129,305 | 0.6829 | 0.6200 | split | low |
| LOWER DIR DISTRICT|UPPER DIR DISTRICT | JANDUL SUB-DIVISION | 189,357 | SAMARBAGH SUB-DIVISION | 190,072 | 60,052 | 0.3171 | 0.3800 | split_and_merge | low |
| LOWER DIR DISTRICT|UPPER DIR DISTRICT | TIMARGARA SUB-DIVISION | 528,292 | ADENZAI SUB-DIVISION | 168,830 | 168,830 | 0.3196 | 0.3342 | split | low |
| LOWER DIR DISTRICT|UPPER DIR DISTRICT | TIMARGARA SUB-DIVISION | 528,292 | SAMARBAGH SUB-DIVISION | 190,072 | 130,020 | 0.2461 | 0.2575 | split_and_merge | medium |
| LOWER DIR DISTRICT|UPPER DIR DISTRICT | TIMARGARA SUB-DIVISION | 528,292 | TEMERGARA SUB-DIVISION | 290,849 | 229,442 | 0.4343 | 0.4083 | split_and_merge | high |
| LOWER DIR DISTRICT|UPPER DIR DISTRICT | WARI SUB-DIVISION | 232,394 | TEMERGARA SUB-DIVISION | 290,849 | 61,407 | 0.2642 | 0.1969 | split_and_merge | medium |
| LOWER DIR DISTRICT|UPPER DIR DISTRICT | WARI SUB-DIVISION | 232,394 | WARI SUB-DIVISION | 175,069 | 170,987 | 0.7358 | 0.8031 | split_and_merge | high |
| MANSEHRA DISTRICT|TORGHAR DISTRICT | TRIBAL AREA ADJOINING MANSEHRA DISTRICT (F.R.KALA DHAKA) | 174,682 | JUDBA TEHSIL | 84,628 | 84,628 | 0.4845 | 0.3282 | split | medium |
| MANSEHRA DISTRICT|TORGHAR DISTRICT | TRIBAL AREA ADJOINING MANSEHRA DISTRICT (F.R.KALA DHAKA) | 174,682 | KHANDER TEHSIL | 90,054 | 90,054 | 0.5155 | 0.6718 | split | medium |
| MARDAN DISTRICT | MARDAN TEHSIL | 1,057,394 | KATLANG TEHSIL | 221,546 | 193,377 | 0.1829 | 0.3006 | split_and_merge | medium |
| MARDAN DISTRICT | MARDAN TEHSIL | 1,057,394 | MARDAN TEHSIL | 864,017 | 864,017 | 0.8171 | 0.6994 | split | high |
| MARDAN DISTRICT | TAKHT BHAI TEHSIL | 402,706 | KATLANG TEHSIL | 221,546 | 28,169 | 0.0699 | 0.1319 | split_and_merge | medium |
| MARDAN DISTRICT | TAKHT BHAI TEHSIL | 402,706 | TAKHT BHAI TEHSIL | 374,537 | 374,537 | 0.9301 | 0.8681 | split | high |
| MASTUNG DISTRICT|QUETTA DISTRICT | DASHT SUB-TEHSIL | 35,077 | DASHT TEHSIL | 24,570 | 24,570 | 0.7005 | 0.9879 | split | high |
| MASTUNG DISTRICT|QUETTA DISTRICT | DASHT SUB-TEHSIL | 35,077 | QUETTA CITY TEHSIL | 638,896 | 10,507 | 0.2995 | 0.0121 | split_and_merge | medium |
| MASTUNG DISTRICT|QUETTA DISTRICT | QUETTA TEHSIL (PART) | 638,896 | QUETTA CITY TEHSIL | 638,896 | 628,389 | 0.9836 | 0.8573 | split_and_merge | high |
| MASTUNG DISTRICT|QUETTA DISTRICT | QUETTA TEHSIL (PART) | 638,896 | QUETTA SADDAR TEHSIL | 120,512 | 10,507 | 0.0164 | 0.1427 | split_and_merge | high |
| MASTUNG DISTRICT|QUETTA DISTRICT | QUETTA TEHSIL (PART) | 110,005 | QUETTA SADDAR TEHSIL | 120,512 | 110,005 | 1.0000 | 1.0000 | merge | high |
| MIRPUR KHAS DISTRICT|SANGHAR DISTRICT|UMER KOT DISTRICT | DIGRI TALUKA | 298,652 | DIGRI TALUKA | 147,272 | 147,272 | 0.4931 | 0.5980 | split | high |
| MIRPUR KHAS DISTRICT|SANGHAR DISTRICT|UMER KOT DISTRICT | DIGRI TALUKA | 298,652 | JHUDO TALUKA | 146,013 | 146,013 | 0.4889 | 0.3795 | split | medium |
| MIRPUR KHAS DISTRICT|SANGHAR DISTRICT|UMER KOT DISTRICT | DIGRI TALUKA | 298,652 | SHUJAABAD TALUKA | 98,783 | 5,367 | 0.0180 | 0.0225 | split_and_merge | medium |
| MIRPUR KHAS DISTRICT|SANGHAR DISTRICT|UMER KOT DISTRICT | KHIPRO TALUKA | 327,185 | KHIPRO TALUKA | 225,089 | 225,089 | 0.6880 | 0.9343 | split | high |
| MIRPUR KHAS DISTRICT|SANGHAR DISTRICT|UMER KOT DISTRICT | KHIPRO TALUKA | 327,185 | PITHORO TALUKA | 81,182 | 1,702 | 0.0052 | 0.0028 | split_and_merge | medium |
| MIRPUR KHAS DISTRICT|SANGHAR DISTRICT|UMER KOT DISTRICT | KHIPRO TALUKA | 327,185 | SINDHRI TALUKA | 150,628 | 100,394 | 0.3068 | 0.0629 | split_and_merge | medium |
| MIRPUR KHAS DISTRICT|SANGHAR DISTRICT|UMER KOT DISTRICT | MIRPUR KHAS TALUKA | 428,275 | HUSSAIN BUX MARI TALUKA | 83,219 | 83,219 | 0.1943 | 0.2589 | split | medium |
| MIRPUR KHAS DISTRICT|SANGHAR DISTRICT|UMER KOT DISTRICT | MIRPUR KHAS TALUKA | 428,275 | MIRPUR KHAS TALUKA | 201,406 | 201,406 | 0.4703 | 0.0297 | split | high |
| MIRPUR KHAS DISTRICT|SANGHAR DISTRICT|UMER KOT DISTRICT | MIRPUR KHAS TALUKA | 428,275 | SHUJAABAD TALUKA | 98,783 | 93,416 | 0.2181 | 0.4639 | split_and_merge | medium |
| MIRPUR KHAS DISTRICT|SANGHAR DISTRICT|UMER KOT DISTRICT | MIRPUR KHAS TALUKA | 428,275 | SINDHRI TALUKA | 150,628 | 50,234 | 0.1173 | 0.2475 | split_and_merge | low |
| MIRPUR KHAS DISTRICT|SANGHAR DISTRICT|UMER KOT DISTRICT | PITHORO TALUKA | 79,480 | PITHORO TALUKA | 81,182 | 79,480 | 1.0000 | 1.0000 | merge | high |
| MOHMAND AGENCY | PRINGHAR TEHSIL | 18,620 | PRANG GHAR TEHSIL | 18,620 | 18,620 | 1.0000 | 1.0000 | one_to_one_renamed | high |
| MULTAN DISTRICT | JALALPUR PIRWALA TEHSIL | 357,840 | JALALPUR PIRWALA TEHSIL | 364,716 | 357,840 | 1.0000 | 1.0000 | merge | high |
| MULTAN DISTRICT | MULTAN CITY TEHSIL | 1,500,617 | MULTAN CITY TEHSIL | 1,381,478 | 1,381,478 | 0.9206 | 0.5976 | split | high |
| MULTAN DISTRICT | MULTAN CITY TEHSIL | 1,500,617 | MULTAN SADDAR TEHSIL | 950,034 | 119,139 | 0.0794 | 0.4024 | split_and_merge | high |
| MULTAN DISTRICT | MULTAN SADDAR TEHSIL | 830,895 | MULTAN SADDAR TEHSIL | 950,034 | 830,895 | 1.0000 | 1.0000 | merge | high |
| MULTAN DISTRICT | SHUJABAD TEHSIL | 427,499 | JALALPUR PIRWALA TEHSIL | 364,716 | 6,876 | 0.0161 | 0.0224 | split_and_merge | high |
| MULTAN DISTRICT | SHUJABAD TEHSIL | 427,499 | SHUJABAD TEHSIL | 420,623 | 420,623 | 0.9839 | 0.9776 | split | high |
| MUSAKHEL DISTRICT | MUSAKHEL TEHSIL | 109,234 | DRUG TEHSIL | 28,638 | 28,638 | 0.2622 | 0.4147 | split | high |
| MUSAKHEL DISTRICT | MUSAKHEL TEHSIL | 109,234 | MUSAKHEL TEHSIL | 80,596 | 80,596 | 0.7378 | 0.5853 | split | high |
| NANKANA SAHIB DISTRICT|SHEIKHUPURA DISTRICT | FEROZEWALA TEHSIL | 999,185 | FEROZEWALA TEHSIL | 396,069 | 396,069 | 0.3964 | 0.2670 | split | high |
| NANKANA SAHIB DISTRICT|SHEIKHUPURA DISTRICT | FEROZEWALA TEHSIL | 999,185 | MURIDKE TEHSIL | 452,369 | 452,369 | 0.4527 | 0.5371 | split | high |
| NANKANA SAHIB DISTRICT|SHEIKHUPURA DISTRICT | FEROZEWALA TEHSIL | 999,185 | SHARAK PUR TEHSIL | 150,747 | 150,747 | 0.1509 | 0.1959 | split | high |
| NANKANA SAHIB DISTRICT|SHEIKHUPURA DISTRICT | SAFDARABAD TEHSIL | 588,617 | SAFDARABAD TEHSIL | 227,715 | 227,715 | 0.3869 | 0.4542 | split | high |
| NANKANA SAHIB DISTRICT|SHEIKHUPURA DISTRICT | SAFDARABAD TEHSIL | 588,617 | SANGLA HILL TEHSIL | 188,020 | 188,020 | 0.3194 | 0.2197 | split | high |
| NANKANA SAHIB DISTRICT|SHEIKHUPURA DISTRICT | SAFDARABAD TEHSIL | 588,617 | SHAH KOT TEHSIL | 172,882 | 172,882 | 0.2937 | 0.3261 | split | high |
| NAROWAL DISTRICT | NAROWAL TEHSIL | 627,300 | NAROWAL TEHSIL | 425,879 | 425,879 | 0.6789 | 0.7939 | split | high |
| NAROWAL DISTRICT | NAROWAL TEHSIL | 627,300 | ZAFARWAL TEHSIL | 318,363 | 201,421 | 0.3211 | 0.2061 | split_and_merge | medium |
| NAROWAL DISTRICT | SHAKARGARH TEHSIL | 637,797 | SHAKARGARH TEHSIL | 520,855 | 520,855 | 0.8166 | 0.8388 | split | high |
| NAROWAL DISTRICT | SHAKARGARH TEHSIL | 637,797 | ZAFARWAL TEHSIL | 318,363 | 116,942 | 0.1834 | 0.1612 | split_and_merge | medium |
| NASIRABAD DISTRICT | CHATTAR TEHSIL | 50,034 | CHATTAR SUB-TEHSIL | 50,446 | 50,034 | 1.0000 | 1.0000 | merge | high |
| NASIRABAD DISTRICT | D.M.JAMALI TEHSIL | 104,519 | CHATTAR SUB-TEHSIL | 50,446 | 412 | 0.0039 | 0.0100 | split_and_merge | high |
| NASIRABAD DISTRICT | D.M.JAMALI TEHSIL | 104,519 | DERA MURAD JAMALI TEHSIL | 104,107 | 104,107 | 0.9961 | 0.9900 | split | medium |
| NASIRABAD DISTRICT | TAMBOO TEHSIL | 91,341 | BABA KOT TEHSIL | 19,531 | 19,531 | 0.2138 | 0.5861 | split | medium |
| NASIRABAD DISTRICT | TAMBOO TEHSIL | 91,341 | TAMBOO TEHSIL | 71,810 | 71,810 | 0.7862 | 0.4139 | split | high |
| NAUSHAHRO FEROZE DISTRICT | BHIRIA TALUKA | 265,206 | BHIRIA TALUKA | 204,120 | 204,120 | 0.7697 | 0.6975 | split | high |
| NAUSHAHRO FEROZE DISTRICT | BHIRIA TALUKA | 265,206 | KANDIARO TALUKA | 222,529 | 61,086 | 0.2303 | 0.3025 | split_and_merge | medium |
| NAUSHAHRO FEROZE DISTRICT | KANDIARO TALUKA | 316,788 | KANDIARO TALUKA | 222,529 | 161,443 | 0.5096 | 0.6078 | split_and_merge | high |
| NAUSHAHRO FEROZE DISTRICT | KANDIARO TALUKA | 316,788 | MEHRABPUR TALUKA | 155,345 | 155,345 | 0.4904 | 0.3922 | split | medium |
| NOWSHERA DISTRICT | NOWSHERA TEHSIL | 874,373 | JEHANGIRA TEHSIL | 208,704 | 208,704 | 0.2387 | 0.4108 | split | high |
| NOWSHERA DISTRICT | NOWSHERA TEHSIL | 874,373 | NOWSHERA TEHSIL | 419,549 | 419,549 | 0.4798 | 0.3884 | split | high |
| NOWSHERA DISTRICT | NOWSHERA TEHSIL | 874,373 | PABBI TEHSIL | 246,120 | 246,120 | 0.2815 | 0.2008 | split | high |
| NUSHKI DISTRICT | DAK SUB-TEHSIL | 10,947 | NUSHKI TEHSIL | 98,030 | 10,947 | 1.0000 | 1.0000 | merge | high |
| NUSHKI DISTRICT | NUSHKI TEHSIL | 87,083 | NUSHKI TEHSIL | 98,030 | 87,083 | 1.0000 | 1.0000 | merge | high |
| PANJGUR DISTRICT | PANJGUR TEHSIL | 166,857 | PANJGUR TEHSIL | 168,268 | 166,857 | 1.0000 | 1.0000 | merge | high |
| PANJGUR DISTRICT | PAROME SUB-TEHSIL | 44,626 | GOWARGO TEHSIL | 24,377 | 24,377 | 0.5463 | 0.3015 | split | medium |
| PANJGUR DISTRICT | PAROME SUB-TEHSIL | 44,626 | PANJGUR TEHSIL | 168,268 | 1,411 | 0.0316 | 0.0063 | split_and_merge | high |
| PANJGUR DISTRICT | PAROME SUB-TEHSIL | 44,626 | PAROME TEHSIL | 18,838 | 18,838 | 0.4221 | 0.6923 | split | high |
| PISHIN DISTRICT | KAREZAT SUB-TEHSIL | 75,416 | KAREZAT SUB-TEHSIL | 63,375 | 63,375 | 0.8403 | 0.9489 | split | high |
| PISHIN DISTRICT | KAREZAT SUB-TEHSIL | 75,416 | PISHIN TEHSIL | 131,261 | 12,041 | 0.1597 | 0.0511 | split_and_merge | high |
| PISHIN DISTRICT | PISHIN TEHSIL | 148,087 | PISHIN TEHSIL | 131,261 | 119,220 | 0.8051 | 0.9292 | split_and_merge | high |
| PISHIN DISTRICT | PISHIN TEHSIL | 148,087 | SARANAN TEHSIL | 28,867 | 28,867 | 0.1949 | 0.0708 | split | high |
| RAWALPINDI DISTRICT | KAHUTA TEHSIL | 155,080 | KAHUTA TEHSIL | 153,719 | 153,719 | 0.9912 | 0.9922 | split | high |
| RAWALPINDI DISTRICT | KAHUTA TEHSIL | 155,080 | KOTLI SATTIAN TEHSIL | 82,711 | 1,361 | 0.0088 | 0.0078 | split_and_merge | high |
| RAWALPINDI DISTRICT | KOTLI SATTIAN TEHSIL | 81,523 | KOTLI SATTIAN TEHSIL | 82,711 | 81,350 | 0.9979 | 0.9986 | split_and_merge | high |
| RAWALPINDI DISTRICT | KOTLI SATTIAN TEHSIL | 81,523 | MURREE TEHSIL | 176,599 | 173 | 0.0021 | 0.0014 | split_and_merge | high |
| RAWALPINDI DISTRICT | MURREE TEHSIL | 176,426 | MURREE TEHSIL | 176,599 | 176,426 | 1.0000 | 1.0000 | merge | high |
| SAHIWAL DISTRICT | CHICHAWATNI TEHSIL | 785,357 | CHICHAWATNI TEHSIL | 787,062 | 785,357 | 1.0000 | 1.0000 | merge | high |
| SAHIWAL DISTRICT | SAHIWAL TEHSIL | 1,057,837 | CHICHAWATNI TEHSIL | 787,062 | 1,705 | 0.0016 | 0.0021 | split_and_merge | high |
| SAHIWAL DISTRICT | SAHIWAL TEHSIL | 1,057,837 | SAHIWAL TEHSIL | 1,056,132 | 1,056,132 | 0.9984 | 0.9979 | split | high |
| SARGODHA DISTRICT | BHALWAL TEHSIL | 479,045 | BHALWAL TEHSIL | 254,732 | 252,680 | 0.5275 | 0.5661 | split_and_merge | high |
| SARGODHA DISTRICT | BHALWAL TEHSIL | 479,045 | BHERA TEHSIL | 226,365 | 226,365 | 0.4725 | 0.4339 | split | high |
| SARGODHA DISTRICT | KOT MOMIN TEHSIL | 340,842 | BHALWAL TEHSIL | 254,732 | 2,052 | 0.0060 | 0.0056 | split_and_merge | high |
| SARGODHA DISTRICT | KOT MOMIN TEHSIL | 340,842 | KOT MOMIN TEHSIL | 338,790 | 338,790 | 0.9940 | 0.9944 | split | high |
| SHAHEED BENAZIRABAD DISTRICT | DAULATPUR TALUKA | 246,797 | KAZI AHMED TALUKA | 246,797 | 246,797 | 1.0000 | 1.0000 | one_to_one_renamed | medium |
| SHAHEED BENAZIRABAD DISTRICT | NAWAB SHAH TALUKA | 576,653 | DAUR TALUKA | 304,625 | 304,625 | 0.5283 | 0.8401 | split | medium |
| SHAHEED BENAZIRABAD DISTRICT | NAWAB SHAH TALUKA | 576,653 | NAWABSHAH TALUKA | 281,302 | 272,028 | 0.4717 | 0.1599 | split_and_merge | high |
| SHAHEED BENAZIRABAD DISTRICT | SAKRAND TALUKA | 279,134 | NAWABSHAH TALUKA | 281,302 | 9,274 | 0.0332 | 0.0159 | split_and_merge | medium |
| SHAHEED BENAZIRABAD DISTRICT | SAKRAND TALUKA | 279,134 | SAKRAND TALUKA | 269,860 | 269,860 | 0.9668 | 0.9841 | split | high |
| SHANGLA DISTRICT | ALPURI TEHSIL | 172,960 | ALPURI TEHSIL | 297,718 | 172,960 | 1.0000 | 1.0000 | merge | high |
| SHANGLA DISTRICT | BESHAM TEHSIL | 57,739 | BISHAM TEHSIL | 57,739 | 57,739 | 1.0000 | 1.0000 | one_to_one_renamed | medium |
| SHANGLA DISTRICT | CHAKESAR TEHSIL | 67,317 | ALPURI TEHSIL | 297,718 | 67,317 | 1.0000 | 1.0000 | merge | high |
| SHANGLA DISTRICT | MARTOONG TEHSIL | 57,441 | ALPURI TEHSIL | 297,718 | 57,441 | 1.0000 | 1.0000 | merge | medium |
| SHERANI DISTRICT|ZHOB DISTRICT | ASHWAT SUB-TEHSIL | 18,412 | ASHWAT SUB-TEHSIL | 13,247 | 13,247 | 0.7195 | 0.3617 | split | high |
| SHERANI DISTRICT|ZHOB DISTRICT | ASHWAT SUB-TEHSIL | 18,412 | KASHATOO SUB-TEHSIL | 5,165 | 5,165 | 0.2805 | 0.6383 | split | high |
| SIALKOT DISTRICT | DASKA TEHSIL | 860,611 | DASKA TEHSIL | 605,435 | 605,435 | 0.7035 | 0.6420 | split | high |
| SIALKOT DISTRICT | DASKA TEHSIL | 860,611 | SAMBRIAL TEHSIL | 298,431 | 255,176 | 0.2965 | 0.3580 | split_and_merge | medium |
| SIALKOT DISTRICT | SIALKOT TEHSIL | 1,250,999 | SAMBRIAL TEHSIL | 298,431 | 43,255 | 0.0346 | 0.0675 | split_and_merge | medium |
| SIALKOT DISTRICT | SIALKOT TEHSIL | 1,250,999 | SIALKOT TEHSIL | 1,207,744 | 1,207,744 | 0.9654 | 0.9325 | split | high |
| SUJAWAL DISTRICT|THATTA DISTRICT | KETI BUNDER TALUKA | 25,700 | KETI BUNDER TALUKA | 41,410 | 25,700 | 1.0000 | 1.0000 | merge | high |
| SUJAWAL DISTRICT|THATTA DISTRICT | KHARO CHAN TALUKA | 25,666 | KETI BUNDER TALUKA | 41,410 | 15,710 | 0.6121 | 0.2732 | split_and_merge | high |
| SUJAWAL DISTRICT|THATTA DISTRICT | KHARO CHAN TALUKA | 25,666 | KHARO CHAN TALUKA | 9,956 | 9,956 | 0.3879 | 0.7268 | split | high |
| SWABI DISTRICT | LAHOR TEHSIL | 304,803 | LAHOR TEHSIL | 187,558 | 187,558 | 0.6153 | 0.6427 | split | high |
| SWABI DISTRICT | LAHOR TEHSIL | 304,803 | SWABI TEHSIL | 258,006 | 117,245 | 0.3847 | 0.3573 | split_and_merge | medium |
| SWABI DISTRICT | SWABI TEHSIL | 722,001 | RAZAR TEHSIL | 376,106 | 376,106 | 0.5209 | 0.3988 | split | high |
| SWABI DISTRICT | SWABI TEHSIL | 722,001 | SWABI TEHSIL | 258,006 | 140,761 | 0.1950 | 0.2025 | split_and_merge | high |
| SWABI DISTRICT | SWABI TEHSIL | 722,001 | TOPI TEHSIL | 205,134 | 205,134 | 0.2841 | 0.3988 | split | high |
| SWAT DISTRICT | SWAT TEHSIL | 1,006,234 | BABUZAI TEHSIL | 321,995 | 321,995 | 0.3200 | 0.0638 | split | high |
| SWAT DISTRICT | SWAT TEHSIL | 1,006,234 | BARIKOT TEHSIL | 99,975 | 99,975 | 0.0994 | 0.0900 | split | high |
| SWAT DISTRICT | SWAT TEHSIL | 1,006,234 | BEHRAIN TEHSIL | 125,247 | 125,247 | 0.1245 | 0.6230 | split | high |
| SWAT DISTRICT | SWAT TEHSIL | 1,006,234 | CHARBAGH TEHSIL | 73,682 | 73,682 | 0.0732 | 0.0346 | split | high |
| SWAT DISTRICT | SWAT TEHSIL | 1,006,234 | KABAL TEHSIL | 244,142 | 244,142 | 0.2426 | 0.1042 | split | high |
| SWAT DISTRICT | SWAT TEHSIL | 1,006,234 | KHAWAZAKHELA TEHSIL | 141,193 | 141,193 | 0.1403 | 0.0842 | split | high |
| THARPARKAR DISTRICT | CHACHRO TALUKA | 357,757 | CHACHRO TALUKA | 167,235 | 167,235 | 0.4675 | 0.5544 | split | high |
| THARPARKAR DISTRICT | CHACHRO TALUKA | 357,757 | DAHLI TALUKA | 165,289 | 165,289 | 0.4620 | 0.3481 | split | high |
| THARPARKAR DISTRICT | CHACHRO TALUKA | 357,757 | MITHI TALUKA | 125,137 | 25,233 | 0.0705 | 0.0975 | split_and_merge | medium |
| THARPARKAR DISTRICT | DIPLO TALUKA | 161,880 | DIPLO TALUKA | 92,047 | 92,047 | 0.5686 | 0.7666 | split | high |
| THARPARKAR DISTRICT | DIPLO TALUKA | 161,880 | KALOI TALUKA | 73,651 | 69,833 | 0.4314 | 0.2334 | split_and_merge | medium |
| THARPARKAR DISTRICT | MITHI TALUKA | 241,548 | ISLAMKOT TALUKA | 137,826 | 137,826 | 0.5706 | 0.5936 | split | medium |
| THARPARKAR DISTRICT | MITHI TALUKA | 241,548 | KALOI TALUKA | 73,651 | 3,818 | 0.0158 | 0.0081 | split_and_merge | medium |
| THARPARKAR DISTRICT | MITHI TALUKA | 241,548 | MITHI TALUKA | 125,137 | 99,904 | 0.4136 | 0.3983 | split_and_merge | high |
| TOBA TEK SINGH DISTRICT | KAMALIA TEHSIL | 509,462 | KAMALIA TEHSIL | 283,674 | 220,870 | 0.4335 | 0.3284 | split_and_merge | high |
| TOBA TEK SINGH DISTRICT | KAMALIA TEHSIL | 509,462 | PIRMAHAL TEHSIL | 288,592 | 288,592 | 0.5665 | 0.6716 | split | medium |
| TOBA TEK SINGH DISTRICT | TOBA TEK SINGH TEHSIL | 617,035 | KAMALIA TEHSIL | 283,674 | 62,804 | 0.1018 | 0.0862 | split_and_merge | medium |
| TOBA TEK SINGH DISTRICT | TOBA TEK SINGH TEHSIL | 617,035 | TOBA TEK SINGH TEHSIL | 554,231 | 554,231 | 0.8982 | 0.9138 | split | high |
