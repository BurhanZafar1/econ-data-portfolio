"""Machine-readable codebook: docs/codebook.csv, one row per (file, column) for every CSV in output/ (the 5 x 5
transition tables are described once as a family). The script fails if a column has no description."""
import pandas as pd, glob, os, sys, re
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(os.path.join(HERE,'..'))
FILES={
 'boundaries_units_2023.csv':('every 2023 polygon (tehsil and district layers) with geodesic area and census-frame flags','dds_id / district_code','code/02'),
 'ntl_A_harmonizedDN_tehsil_2023frame_1992_2024.csv':('series A (harmonized DMSP-VIIRS digital numbers), one row per tehsil and year','dds_id,year','code/03'),
 'ntl_A_harmonizedDN_district_2023frame_1992_2024.csv':('series A, one row per district and year','district_code,year','code/03'),
 'ntl_A_harmonizedDN_tehsil_wide_dn_sum_km2.csv':('series A sum of lights, one column per year, tehsils','dds_id','code/03'),
 'ntl_A_harmonizedDN_district_wide_dn_sum_km2.csv':('series A sum of lights, one column per year, districts','district_code','code/03'),
 'ntl_B_viirslike_tehsil_2023frame_1992_2025.csv':('series B (NPP-VIIRS-like radiance), one row per tehsil and year','dds_id,year','code/04'),
 'ntl_B_viirslike_district_2023frame_1992_2025.csv':('series B, one row per district and year','district_code,year','code/04'),
 'ntl_B_viirslike_tehsil_wide_rad_sum_km2.csv':('series B sum of lights, one column per year, tehsils','dds_id','code/04'),
 'ntl_B_viirslike_district_wide_rad_sum_km2.csv':('series B sum of lights, one column per year, districts','district_code','code/04'),
 'panel_ntl_census_tehsil_2023frame.csv':('analysis panel: both series and the crosswalked census populations on 2023 tehsils','dds_id,year','code/06'),
 'panel_ntl_census_district_2023frame.csv':('analysis panel at district level','district_code,year','code/06'),
 'rankings/rankings_district_long.csv':('every district rank, by series, measure, variant and year','series,measure,variant,year,unit','code/07'),
 'rankings/ranks_wide_A_size.csv':('ranks with one column per year (series A, sum of lights)','variant,unit','code/07'),
 'rankings/ranks_wide_A_density.csv':('ranks, series A, light per km2','variant,unit','code/07'),
 'rankings/ranks_wide_A_percap.csv':('ranks, series A, light per thousand people (census years)','variant,unit','code/07'),
 'rankings/ranks_wide_B_size.csv':('ranks, series B, sum of lights','variant,unit','code/07'),
 'rankings/ranks_wide_B_density.csv':('ranks, series B, light per km2','variant,unit','code/07'),
 'rankings/ranks_wide_B_percap.csv':('ranks, series B, light per thousand people','variant,unit','code/07'),
 'rankings/mobility_summary.csv':('rank stability statistics by series, measure, variant and year or era','series,measure,variant,year','code/07'),
 'rankings/rank_changes_by_period.csv':('every district\'s rank change within each era','series,measure,variant,period,unit','code/07'),
 'rankings/rank_changes_three_year_windows.csv':('rank change measured on three-year window means (1992-94 against the last three years)','series,measure,variant,unit','code/07'),
 'rankings/adjacent_to_big_cities.csv':('districts whose boundary touches Islamabad, Lahore, Peshawar, Quetta or Karachi (dropped in variant iii)','district_adjacent_to_big_five','code/07'),
 'rankings/transition_quintiles_<series>_<measure>_<variant>_<from>_<to>.csv':('5 x 5 counts: row = quintile in the first year, column = quintile in the last year of the period (1 = brightest fifth)','first column','code/07'),
}
D={
 'year':'calendar year of the annual composite (or of the rank); in mobility_summary also an era label such as "1992-2010 (DMSP era)"',
 'sensor_basis':'input sensor behind the year: series A calDMSP (inter-calibrated DMSP-OLS) or simVIIRS (VIIRS converted to DMSP scale); series B DMSP-derived (1992-2012) or VIIRS (2013 on)',
 'sensor_basis_A':'sensor_basis of series A for that year','sensor_basis_B':'sensor_basis of series B for that year',
 'dds_id':'PBS Digital Census 2023 tehsil id (one polygon per unit)','district_code':'PBS Digital Census 2023 district id (DDD-...)',
 'tehsil_2023':'tehsil name in the PBS 2023 boundary file','district_2023':'district name in the PBS 2023 boundary file','census_name':'district name as printed in PBS Census 2023 Table 1 (where it differs from the boundary file)',
 'province_2023':'province (or territory) of the unit','in_four_provinces':'True for Punjab, Sindh, Khyber Pakhtunkhwa and Balochistan','outside_census_frame':'True if the polygon has no row in the 2023 census tables (AJK, GB, some Islamabad units)',
 'area_km2':'geodesic area of the polygon, km2 (WGS84 ellipsoid)','pixel_area_km2':'area the raster grid assigns to the unit, km2 (sum of pixel areas weighted by the share of each pixel inside the unit)',
 'dn_sum':'sum over pixels of DN x share of the pixel inside the unit (series A)','dn_mean':'area-weighted mean DN','dn_max':'maximum DN of any pixel touching the unit','dn_lit_share':'share of the unit\'s area with DN > 0',
 'dn_sum_km2':'sum of DN x pixel area (km2): the sum of lights in DN.km2','dn_per_km2':'dn_sum_km2 / pixel_area_km2','log1p_dn_sum_km2':'log(1 + dn_sum_km2)','asinh_dn_sum_km2':'inverse hyperbolic sine of dn_sum_km2',
 'dn_sum_gt7_km2':'sum of lights counting only pixels with DN > 7 (the dim-light floor the series A authors recommend)','dn_lit_share_gt7':'share of the unit\'s area with DN > 7',
 'rad_sum':'sum over pixels of radiance x share of the pixel inside the unit (series B, nW/cm2/sr)','rad_mean':'area-weighted mean radiance, nW/cm2/sr','rad_max':'maximum radiance of any pixel touching the unit','rad_lit_share':'share of the unit\'s area with radiance > 0',
 'rad_sum_km2':'sum of radiance x pixel area: the sum of lights in nW/cm2/sr.km2','rad_per_km2':'rad_sum_km2 / pixel_area_km2','log1p_rad_sum_km2':'log(1 + rad_sum_km2)','asinh_rad_sum_km2':'inverse hyperbolic sine of rad_sum_km2',
 'rad_sum_gt1_km2':'sum of lights counting only pixels above 1 nW/cm2/sr (noise floor variant)','rad_lit_share_gt1':'share of the unit\'s area with radiance > 1 nW/cm2/sr',
 'coverage_pixels':'number of pixels touching the unit (weighted by coverage)','series_note':'caution attached to the year (sensor transition years), blank otherwise','series_note_A':'series_note of series A','series_note_B':'series_note of series B',
 'name':'unit name in the boundary file','district':'district of the unit (boundary file)','province':'province of the unit',
 'pop_1951':'population at the 1951 census on the 2023 unit (PCO restatement pushed through the crosswalk; project 02)','pop_1961':'as pop_1951, 1961','pop_1972':'as pop_1951, 1972','pop_1981':'as pop_1951, 1981','pop_1998':'population 1998 on the 2023 unit (crosswalk)','pop_2017':'PBS 2017 population restated on the 2023 unit','pop_2023':'population 2023 (census count)',
 'pop_2017_pbs_district_row':'PBS Census 2023 district row, 2017 population (check)','pop_2023_pbs_district_row':'PBS Census 2023 district row, 2023 population (check)',
 'pop_census':'census population in a census year (1998, 2017, 2023), blank in other years; nothing is interpolated','rad_sum_km2_per_1000':'rad_sum_km2 per thousand people, census years only','dn_sum_km2_per_1000':'dn_sum_km2 per thousand people, census years only',
 'series':'A (harmonized DMSP-VIIRS DN) or B (NPP-VIIRS-like radiance)','measure':'size (sum of lights), density (light per km2) or percap (light per thousand people, census years)','variant':'i_all (all units), ii_no_big5 (without Islamabad, Lahore, Peshawar, Quetta, Karachi), iii_no_big5_or_adjacent (also without districts touching them)',
 'unit':'district (Census 2023 districts of the four provinces plus Islamabad; Karachi\'s seven districts as one unit KARACHI)','value':'the measure\'s value for the unit in that year','rank':'rank within the variant, 1 = brightest; ties (mostly districts with zero light in early years) share the lowest rank of the tied group','percentile':'rank expressed as a percentile of the units ranked (0 = brightest)',
 'n_units':'number of units ranked','spearman_vs_first_year':'Spearman correlation of the year\'s ranking with the first year of the series or era','spearman_vs_previous':'Spearman correlation with the previous year\'s ranking','share_same_quintile':'share of units in the same quintile as in the first year (era rows)','mean_abs_rank_change':'mean absolute change in rank since the first year (era rows)','share_moved_10_or_more':'share of units whose rank changed by 10 or more places (era rows)','climbers_20_or_more':'number of units that climbed 20 or more places (era rows)','fallers_20_or_more':'number of units that fell 20 or more places (era rows)',
 'period':'era label (DMSP era, VIIRS era, end to end)','year_from':'first year of the period','year_to':'last year of the period','rank_from':'rank in year_from','rank_to':'rank in year_to','places_climbed':'rank_from minus rank_to (positive = climbed)','quintile_from':'quintile in year_from (1 = brightest fifth)','quintile_to':'quintile in year_to',
 'rank_1992_94':'rank on the mean of 1992-1994 values','rank_end_window':'rank on the mean of the last three years available','spearman':'Spearman correlation between the two window rankings','district_adjacent_to_big_five':'district whose boundary touches one of the five big-city districts',
}
rows=[]; missing=[]
for f in sorted(glob.glob('output/*.csv')+glob.glob('output/rankings/*.csv')):
    b=os.path.relpath(f,'output'); fam=re.sub(r'transition_quintiles_.*','transition_quintiles_<series>_<measure>_<variant>_<from>_<to>.csv',b)
    if fam!=b and any(r['file']==fam for r in rows): continue
    if fam not in FILES: missing.append(('FILE',b)); continue
    d=pd.read_csv(f,low_memory=False)
    for c in d.columns:
        if fam!=b: desc='quintile in the first year (row label)' if c==d.columns[0] else f'number of units in quintile {c} in the last year'
        elif re.fullmatch(r'\d{4}',c): desc='sum of lights in that year (dn_sum_km2 for series A, rad_sum_km2 for series B) or, in ranks_wide files, the rank in that year'
        elif c in D: desc=D[c]
        else: missing.append((b,c)); continue
        s=d[c]; t='integer' if pd.api.types.is_integer_dtype(s) else 'number' if pd.api.types.is_float_dtype(s) else 'logical' if pd.api.types.is_bool_dtype(s) else 'text'
        rows.append(dict(file=fam,file_description=FILES[fam][0],key_columns=FILES[fam][1],produced_by=FILES[fam][2],n_rows=len(d),column=c,type=t,n_missing=int(s.isna().sum()),
                         units='km2' if 'km2' in c and 'sum' not in c and 'per' not in c else 'nW/cm2/sr' if c in ('rad_sum','rad_mean','rad_max') else 'DN (0-63)' if c in ('dn_sum','dn_mean','dn_max') else 'nW/cm2/sr.km2' if c.startswith('rad_sum') and 'km2' in c and 'log' not in c else 'DN.km2' if c.startswith('dn_sum') and 'km2' in c else 'share (0-1)' if 'share' in c else 'persons' if c.startswith('pop_') else '',description=desc))
if missing: print('UNDOCUMENTED:',missing); sys.exit(1)
C=pd.DataFrame(rows); C.to_csv('docs/codebook.csv',index=False); print('codebook rows',len(C),'files',C.file.nunique())
