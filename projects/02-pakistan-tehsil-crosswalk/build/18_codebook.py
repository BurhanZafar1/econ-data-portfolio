"""Machine-readable codebook: docs/codebook.csv, one row per (file, column) for every CSV in output/, with the
observed type, the number of rows and of missing values, and a description. Descriptions are keyed by column
name (the same name means the same thing in every file) with file-specific overrides where needed. The script
fails if a column has no description, so the codebook cannot silently fall behind the outputs."""
import pandas as pd, numpy as np, glob, os, sys
OUT='output/'
FILES={  # file -> (one-line description, key columns, producing script)
 'crosswalk_tehsil_2017_to_2023.csv':('2017 tehsils onto 2023 tehsils, population and area weights','unit_id_2017,unit_id_2023','build/02c, 04'),
 'crosswalk_tehsil_1998_to_2017.csv':('1998 (report-frame) tehsils onto 2017 tehsils','unit_id_1998,unit_id_2017','build/07, 08'),
 'crosswalk_tehsil_1998_to_2023.csv':('1998 (report-frame) tehsils onto 2023 tehsils, chained through 2017; the base-year table','unit_id_1998,unit_id_2023','build/08'),
 'crosswalk_district_2017_to_2023.csv':('district level, 2017 to 2023','district_2017,district_2023','build/05'),
 'crosswalk_district_1998_to_2017.csv':('district level, 1998 to 2017','district_1998,district_2017','build/08'),
 'crosswalk_district_1998_to_2023.csv':('district level, 1998 to 2023','district_1998,district_2023','build/08'),
 'crosswalk_tehsil_1998census_to_pcoframe.csv':('census-day 1998 units (1 March 1998) onto the report frame, all provinces','unit_id_1998census,unit_id_1998','build/14, 16'),
 'crosswalk_tehsil_1998census_to_2023.csv':('census-day 1998 units onto 2023 tehsils, chained','unit_id_1998census,unit_id_2023','build/16'),
 'crosswalk_tehsil_1998census_to_pcoframe_punjab.csv':('Punjab subset of the census-day layer (third release file, unchanged)','unit_id_1998census,unit_id_1998','build/14'),
 'crosswalk_tehsil_1998census_to_2023_punjab.csv':('Punjab subset, chained to 2023 (third release file, unchanged)','unit_id_1998census,unit_id_2023','build/14'),
 'crosswalk_district_1998census_to_pcoframe.csv':('district level, census-day 1998 to the report frame','district_1998census,district_1998_pcoframe','build/16'),
 'crosswalk_district_1998census_to_2023.csv':('district level, census-day 1998 to 2023','district_1998census,district_2023','build/16'),
 'crosswalk_district_historical_to_1998.csv':('district maps of 1951, 1961, 1972 and 1981 onto the 1998 districts','census_year,historical_district,district_1998,tehsil_1998','build/13'),
 'crosswalk_district_historical_to_2023.csv':('district maps of 1951-1981 onto the 2023 districts','census_year,historical_district,district_2023','build/13'),
 'new_district_lineage.csv':('every district first seen in 2017 or 2023: the earlier tehsils it was formed from','new_district,source_tehsil_id','build/09'),
 'tehsil_district_membership.csv':('every tehsil\'s district in the later frame, with the share of its people there','frame_from,frame_to,unit_id,district_to','build/09'),
 'event_register.csv':('dated district and tehsil changes with sources and grades','province,level,event_type,unit_name,parent_or_source_units,new_or_destination_units','build/10'),
 'population_panel_1998_frame.csv':('1951-1998 populations on the 1998 report frame, tehsils (PCO)','unit_id_1998','build/12'),
 'population_panel_1998_frame_districts.csv':('the same at district level','district_1998','build/12'),
 'population_panel_2023_frame.csv':('all seven censuses on the 2023 tehsils','unit_id_2023','build/12'),
 'population_panel_2023_frame_districts.csv':('all seven censuses on the 2023 districts','district_2023','build/12'),
 'district_lineage_1951_1998.csv':('creation year, parents and former names of every 1998 district and of districts that existed earlier','district_1998','build/13 (hand-compiled table, sources per row)'),
 'district_frames_by_census.csv':('the district map at each census 1951-1998 in 1998-district members','census_year,historical_district','build/13'),
 'unit_master_1998.csv':('the 1998 report frame: every sub-district unit with 1951-1998 populations and area (PCO)','unit_id_1998','build/06'),
 'district_master_1998.csv':('the 1998 report frame at district level','district_1998','build/06'),
 'unit_master_1998census_all.csv':('the census-day 1998 frame, all provinces (Punjab Government table; PCO Publication 161 Tables 2, 3, 5, 6)','unit_id_1998census','build/16'),
 'unit_master_1998census_punjab.csv':('Punjab census-day units (third release file, unchanged)','unit_id_1998census','build/14'),
 'unit_master_2017_all.csv':('every unit in PBS Census 2017 Table 1 (districts and sub-districts)','province,district,unit','build/01'),
 'unit_master_2023_all.csv':('every unit in PBS Census 2023 Table 1 with the Digital Census id','dds_id','build/01'),
 'check_overlay_mismatches.csv':('diagnostic: 2017 units whose free polygon (Demobase) disagrees with the PBS-based crosswalk','unit_id_2017','build/02b'),
 'research_notes_1998_frame.csv':('research log for the 1998 frame questions (Lahore, Karachi, Peshawar towns; Umerkot; Nushki) with sources','job,unit,quantity_or_event','hand-compiled during build/06'),
 'weights_and_uncertainty_by_layer.csv':('per layer: weight distribution, population on inferred rows, population mapped (docs/WEIGHTS_AND_UNCERTAINTY.md)','layer','build/19'),
 'uncertainty_by_target_unit.csv':('per target unit and layer: population received, of which on inferred (medium or low) rows, and the resulting uncertain share','layer,target_unit','build/19'),
 'UNVERIFIED_ocr_extract_pub161_tehsil_lines.csv':('what the scan\'s OCR layer reads for Publication 161 tehsil lines; NOT used anywhere, superseded by the hand transcriptions','line','build/15'),
}
D={  # column -> description
 'province':'province (PUNJAB, SINDH, KHYBER PAKHTUNKHWA, BALOCHISTAN, FATA); in historical files, the province the unit belongs to in 1998',
 'district':'district as printed by PBS in the frame of the file','unit':'unit name as printed by the source',
 'tier':'row type in the scan (province, division, district, tehsil)','pop_1998_ocr':'1998 population as the OCR layer reads it (unverified)','line':'raw OCR text line',
 'unit_id_2017':'stable id of the 2017 unit, T17-nnnn, assigned in this project in PBS table order','unit_2017':'sub-district unit as printed in PBS Census 2017 Table 1','district_2017':'district (or agency / FR) as printed in PBS Census 2017 Table 1',
 'crosswalk_units_2023':'2023 units the crosswalk sends the 2017 unit to','overlay_coverage':'share of the 2017 polygon (Demobase) covered by the crosswalk\'s 2023 units','polygon_mostly_in':'2023 polygons that cover the 2017 polygon, with shares',
 'province_1998':'province in the 1998 report frame','district_1998':'district in the 1998 report frame (PCO 1951-98 report)','province_2017':'province in the 2017 frame',
 'flow_1998':'persons of the source unit\'s 1998 population that fall in the target unit (source-year count)','confidence':'high = equals a published figure or forced by the tables; medium = inferred (another allocation balances but is less plausible given adjacency); low = an equally plausible alternative exists; in lineage and event files: verified / reported / unverified',
 'n_tehsil_rows':'number of tehsil-level rows aggregated into this district row','pop_1998':'population at the 1998 census on the unit of the file\'s frame',
 'pop_weight':'share of the source unit\'s population that goes to the target unit; sums to 1 over the target units of each source','area_weight':'share of the source unit\'s area that goes to the target unit; sums to 1 over the target units of each source',
 'relation':'one_to_one, split, merge, split_and_merge, or renamed, at district level','karachi_division':'True for rows inside Karachi (all frames), so Karachi can be collapsed to one unit',
 'pop_1998_restated_2017':'PBS Census 2017 Table 1, "POPULATION 1998" on the 2017 boundary','pop_2017':'population 2017, PBS Census 2017 Table 1 (or PBS\'s 2017 figure restated on the 2023 unit where the frame is 2023)',
 'province_2023':'province in the 2023 frame','district_2023':'district as printed in PBS Census 2023 Table 1','pop_2023':'population 2023, PBS Census 2023 Table 1',
 'district_1998census':'district on census day, 1 March 1998 (Publication 161 / Punjab Government table)','pop_1998census':'population at the 1998 census on the census-day unit',
 'district_1998_pcoframe':'district in the report frame (the mid-2000s map carrying 1998 counts)','pop_1998_pcoframe':'1998 population of the report-frame unit',
 'flow_2017':'persons of the source unit\'s 2017 population that fall in the target 2023 unit','pop_2017_restated_2023':'PBS Census 2023 Table 1, "POPULATION 2017" on the 2023 boundary',
 'census_year':'census year of the historical district map (1951, 1961, 1972, 1981)','historical_district':'district (or agency, state, FR) as it existed at that census',
 'tehsil_1998':'1998 tehsil used to split a historical district between two 1998 districts (blank when whole districts suffice)','pop_census_year_on_1998_unit':'PCO\'s restated population of the 1998 unit at that census',
 'pop_historical_district':'population of the historical district at that census (sum of its 1998-frame members)','weight':'share of the historical district\'s population in the target district',
 'weight_basis':'how the weight was obtained (pbs_restatement_exact, +milp_adjacency, pco_restatement_exact, proxy_shares_from_<year>, chained ...)','method':'resolver relation (one_to_one, one_to_one_renamed, split, merge, split_and_merge) or, in historical files, the method sentence',
 'lineage_confidence':'grade of the lineage row(s) the weight rests on (verified / reported / unverified)','lineage_source':'source URL(s) of the lineage row(s)',
 'note':'free-text note: for resolver rows the cell cost and the forced / inferred / ambiguous grade; elsewhere caveats','conf_1998_to_2023':'confidence of the 1998 -> 2023 tehsil rows used to chain',
 'via_1998':'1998 units through which a historical district reaches 2023','persons_moved':'persons that changed district between the two frames (absolute count)',
 'district_group':'the set of districts inside which the units were matched (resolver group label)','unit_id_1998':'stable id of the 1998 report-frame unit, T98-nnnn',
 'unit_1998':'sub-district unit as printed in the PCO 1951-98 report','unit_type_1998':'tehsil, taluka, sub_division, sub_tehsil, fr, other','unit_type_2017':'tehsil, sub_division, sub_tehsil, other',
 'area_2017_km2':'area of the 2017 unit, km2, PBS Census 2017 Table 1','area_2017_source':'where the 2017 area comes from (pbs_table or derived)','area_basis':'how the area weight was built (identity, exact, uniform_density_split)',
 'area_1998_pco_km2':'area of the 1998 unit as printed by PCO, km2','area_1998_implied_km2':'area implied for the 1998 unit by summing the 2017 areas it flows into','frame_note_1998':'note on the 1998 unit\'s frame (post-census tehsil, collapsed city district, Nushki, Umerkot)',
 'district_1998_at_census':'district the unit belonged to on census day where it differs from the report frame (Umerkot talukas, Nushki)','unit_id_2023':'PBS Digital Census 2023 unit id, DDS-PP-nnnn (one polygon per unit)',
 'unit_2023':'sub-district unit as printed in PBS Census 2023 Table 1','unit_type_2023':'tehsil, sub_division, sub_tehsil, taluka, other','via_2017':'2017 units through which the 1998 unit reaches 2023',
 'unit_id_1998census':'id of the census-day 1998 unit, T98C-<PB|SD|KP|FA|BA>-nnn','unit_1998census':'unit as printed in the census-day table','via_pco_units':'report-frame units through which the census-day unit reaches 2023',
 'area_1998census_km2':'area of the census-day unit, km2, as printed','unit_1998_pcoframe':'report-frame unit name','area_2023_km2':'area of the 2023 unit, km2, PBS Census 2023 Table 1',
 'overlay_area_weight':'area weight from the free polygon overlay (check only, not used)','status':'district / agency / princely_state / federal_capital at that census',
 'n_1998_districts':'number of 1998 districts inside the historical district','members_1998':'1998 districts (and tehsil parts) that make up the historical district','population':'population of the historical district at that census',
 'all_members_have_pco_figure':'True if PCO prints a figure for every member at that census','created_year':'year the 1998 district was created','created_date':'notification date where found (YYYY-MM-DD)',
 'parent_districts_1998_names':'district(s) it was carved from, in 1998 names','former_names':'earlier names of the district','existed_1951':'yes/no: existed as a district at the 1951 census','existed_1961':'yes/no at the 1961 census','existed_1972':'yes/no at the 1972 census','existed_1981':'yes/no at the 1981 census',
 'notes':'free-text note with the evidence read','source_url':'URL of the source read','source_title':'title of the source read','pop_1981':'population at the 1981 census restated on the unit (PCO)','area_km2':'area, km2, as printed by the source',
 'level':'district or tehsil','event_type':'kind of change (district_created, tehsil_upgraded_to_district, tehsil_created, renamed, transferred, merged ...)','unit_name':'unit the row is about',
 'parent_or_source_units':'units the territory came from','new_or_destination_units':'units the territory went to','year':'year of the event (or of the figure, in the research log)','date':'date of the notification where found (YYYY-MM-DD)',
 'interval':'census interval the event falls in (1998-2017, 2017-2023, post-2023)','in_crosswalk':'yes if the change is carried by a crosswalk layer; no if it falls between frames PBS did not tabulate',
 'new_district':'district first tabulated in 2017 or 2023','frame_first_seen':'first census frame in which the district appears','parent_districts':'district(s) in the earlier frame it was formed from',
 'source_tehsil':'earlier-frame tehsil contributing to the new district','source_tehsil_id':'its unit id','source_tehsil_district':'its district in the earlier frame','persons_from_tehsil':'persons of that tehsil in the new district',
 'share_of_new_district':'share of the new district\'s (restated) population from that tehsil','share_of_source_tehsil':'share of the tehsil\'s population that went to the new district','tehsil_upgraded':'yes if the whole tehsil became the district',
 'event_year':'year the district was created (event register)','event_date':'notification date (event register)','event_source_url':'source URL (event register)','event_confidence':'grade of the event row',
 'pop_1951':'population at the 1951 census restated on the unit (PCO); blank where PCO prints a dash','pop_1961':'population at the 1961 census restated on the unit (PCO)','pop_1972':'population at the 1972 census restated on the unit (PCO)',
 'avail_1951':'True if PCO prints a 1951 figure','avail_1961':'True if PCO prints a 1961 figure','avail_1972':'True if PCO prints a 1972 figure','avail_1981':'True if PCO prints a 1981 figure','mark':'footnote mark printed next to the row in the PCO table',
 'flag_1951':'complete, or the source units with no PCO figure that year','flag_1961':'as flag_1951','flag_1972':'as flag_1951','flag_1981':'as flag_1951','flag_1998':'complete (count) or note','flag_2017':'source of the 2017 figure','flag_2023':'census count',
 'method_pre_1998':'how the 1951-1981 figures were put on the 2023 unit','pop_2017_pbs_district_row':'PBS Census 2023 district row, 2017 population (check column)','pop_2023_pbs_district_row':'PBS Census 2023 district row, 2023 population (check column)',
 'job':'research question label','quantity_or_event':'what was looked up','value':'the figure or fact found','frame_from':'earlier census frame (year)','frame_to':'later census frame (year)','unit_id':'id of the tehsil in the earlier frame',
 'province_from':'province in the earlier frame','district_from':'district in the earlier frame','unit_type':'unit type in the frame of the file','pop_from':'population in the earlier frame','province_to':'province in the later frame','district_to':'district in the later frame',
 'persons':'persons of the tehsil in that later district','share_of_tehsil':'share of the tehsil\'s population in that later district','district_changed':'True if the later district differs from the earlier one','tehsil_name_matches_new_district':'True if the tehsil\'s name matches the later district (upgrade)',
 'frame_note':'note on the unit\'s frame','sub_division':'sub-division the unit is printed under (Balochistan, Publication 161)','source_table':'table the row was transcribed from','page':'page of the scan the row was transcribed from',
 'layer':'crosswalk file (or layer label) the row refers to','target_unit':'id of the target unit (unit id or district name) in that layer','received':'source-year population the target unit receives in total','received_nonhigh':'of which on rows graded medium or low (district layers: inferred flows that cross a district line, in or out)','received_low':'of which on rows graded low','n_sources':'number of source units (rows) contributing','share_uncertain':'received_nonhigh / received, capped at 1','share_low':'received_low / received, capped at 1',
 'source_units':'number of source units in the layer','rows':'number of rows','split_sources':'source units with more than one target','share_rows_w_02_08':'share of rows with population weight in (0.2, 0.8)','share_rows_w_04_06':'share of rows with population weight in (0.4, 0.6)','share_pop_on_nonexact_rows':'share of the population moving on rows graded medium or low (district layers: on inferred cross-district flows)','share_pop_on_low_rows':'share of the population moving on rows graded low','largest_source_share_uncertain':'largest share_uncertain over target units','weights_sum_to_one':'True if the population weights sum to one for every source unit','population_mapped_share':'population carried to the target frame over the source-frame total',
 'province_area':'province as printed in PBS Table 1','pop_1998_restated':'PBS Census 2017 Table 1, "POPULATION 1998" on the 2017 unit','dds_id':'PBS Digital Census 2023 id (DDS- sub-district, DDD- district)','pop_2017_restated':'PBS Census 2023 Table 1, "POPULATION 2017" on the 2023 unit',
}
rows=[]; missing=[]
for f in sorted(glob.glob(OUT+'*.csv')):
    b=os.path.basename(f)
    if b not in FILES: missing.append(('FILE',b)); continue
    d=pd.read_csv(f,low_memory=False)
    for c in d.columns:
        if c not in D: missing.append((b,c)); continue
        s=d[c]; t='integer' if pd.api.types.is_integer_dtype(s) else 'number' if pd.api.types.is_float_dtype(s) and (s.dropna()%1==0).all() and 'weight' not in c and 'share' not in c else 'number' if pd.api.types.is_float_dtype(s) else 'logical' if pd.api.types.is_bool_dtype(s) else 'text'
        rows.append(dict(file=b,file_description=FILES[b][0],key_columns=FILES[b][1],produced_by=FILES[b][2],n_rows=len(d),column=c,type=t,n_missing=int(s.isna().sum()),
                         units='persons' if c.startswith(('pop_','flow_','persons')) else 'km2' if 'km2' in c else 'share (0-1)' if ('weight' in c or 'share' in c or c=='overlay_coverage') else '',description=D[c]))
if missing: print('UNDOCUMENTED:',missing); sys.exit(1)
C=pd.DataFrame(rows); C.to_csv('docs/codebook.csv',index=False)
print('codebook rows',len(C),'files',C.file.nunique())
# keep the row counts in the prose dictionary in step with the files
import re
md=open('docs/DATA_DICTIONARY.md').read(); n=C.groupby('file').n_rows.first()
def fix(m):
    f=m.group(1); return f'{f} ({n[f]:,} rows)' if f in n.index else m.group(0)
md2=re.sub(r'([A-Za-z0-9_]+\.csv) \([\d,]+ rows\)',fix,md)
if md2!=md: open('docs/DATA_DICTIONARY.md','w').write(md2); print('row counts in DATA_DICTIONARY.md refreshed')
