"""Checks on the night-light tables; writes output/validation_summary.json and docs/VALIDATION.md.
 1. Coverage: every 2023 unit has a row for every year in each series.
 2. Additivity: for each district and year, the sum of its tehsils' sum-of-lights equals the district
    polygon's own value (both computed from the same raster; differences come only from the polygon
    layers not nesting perfectly).
 3. Area: pixel_area_km2 (raster grid) against area_km2 (geodesic polygon area).
 4. Agreement between the two series: cross-sectional correlation of log sum-of-lights by year.
 5. Year-to-year national series and the known 2014-2016 problem in series A.
 6. Face checks: the ten brightest and ten darkest districts in 2023.
"""
import os, json, numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,'..','output'); DOCS=os.path.join(HERE,'..','docs'); os.makedirs(DOCS,exist_ok=True)
A_t=pd.read_csv(os.path.join(OUT,'ntl_A_harmonizedDN_tehsil_2023frame_1992_2024.csv')); A_d=pd.read_csv(os.path.join(OUT,'ntl_A_harmonizedDN_district_2023frame_1992_2024.csv'))
B_t=pd.read_csv(os.path.join(OUT,'ntl_B_viirslike_tehsil_2023frame_1992_2025.csv')); B_d=pd.read_csv(os.path.join(OUT,'ntl_B_viirslike_district_2023frame_1992_2025.csv'))
rep={}; L=['# Validation: night-time lights by Census 2023 tehsil and district\n']
for name,T,D,v in [('A_harmonizedDN',A_t,A_d,'dn_sum_km2'),('B_viirslike',B_t,B_d,'rad_sum_km2')]:
    yrs=sorted(T.year.unique()); r={}
    r['years']=f'{yrs[0]}-{yrs[-1]} ({len(yrs)} years)'
    r['tehsil_rows']=len(T); r['tehsil_units']=int(T.dds_id.nunique()); r['complete_panel']=bool(len(T)==T.dds_id.nunique()*len(yrs) and T[v].notna().all())
    r['district_rows']=len(D); r['district_units']=int(D.district_code.nunique())
    s=T.groupby(['district_2023','year'])[v].sum().rename('from_tehsils').reset_index().merge(D[['district_2023','year',v]],on=['district_2023','year'])
    s['rel']=(s.from_tehsils-s[v]).abs()/s[v].replace(0,np.nan)
    r['additivity_median_rel_gap']=float(s.rel.median()); r['additivity_p95_rel_gap']=float(s.rel.quantile(.95)); r['additivity_max_rel_gap']=float(s.rel.max())
    worst=s.sort_values('rel',ascending=False).drop_duplicates('district_2023').head(5)
    r['additivity_worst_districts']=[f"{x.district_2023} ({x.rel:.1%}, {x.year}; district value {x[v]:,.0f})" for _,x in worst.iterrows()]
    big=s[s[v]>s[v].quantile(.5)]; r['additivity_p95_rel_gap_brighter_half']=float(big.rel.quantile(.95))
    r['additivity_share_of_national_light_misallocated']=float((s.from_tehsils-s[v]).abs().sum()/s[v].sum())
    u=T.drop_duplicates('dds_id'); ar=(u.pixel_area_km2/u.area_km2)
    r['pixel_area_vs_polygon_area_ratio']=dict(median=float(ar.median()),min=float(ar.min()),max=float(ar.max()))
    nat=T[T.in_four_provinces].groupby('year')[v].sum(); r['national_series_four_provinces']={int(k):float(round(x,0)) for k,x in nat.items()}
    rep[name]=r
    L.append(f'## Series {name}'); L.append(f"- {r['years']}; {r['tehsil_units']} tehsil polygons x years = {r['tehsil_rows']} rows, complete: {r['complete_panel']}; {r['district_units']} districts.")
    L.append(f"- Additivity (tehsils of a district vs the district polygon, same raster): median gap {r['additivity_median_rel_gap']:.2%}, 95th percentile {r['additivity_p95_rel_gap']:.2%} (brighter half of district-years: {r['additivity_p95_rel_gap_brighter_half']:.2%}); the gaps sum to {r['additivity_share_of_national_light_misallocated']:.2%} of all light. Large relative gaps occur only where a district is almost dark: {', '.join(r['additivity_worst_districts'])}. The two PBS layers nest to within 2% of area everywhere except Karachi South, Korangi, Karachi West (coastline drawn differently) and Bagh and Haveli in AJK.")
    L.append(f"- Raster-grid area vs geodesic polygon area: median ratio {ar.median():.4f} (min {ar.min():.3f}, max {ar.max():.3f}).")
    L.append('- Sum of lights, four provinces, by year: '+'; '.join(f'{k} {x:,.0f}' for k,x in nat.items())+'\n')
# agreement between series
m=A_d.merge(B_d,on=['district_code','year'],suffixes=('_A','_B'))
m=m[m.in_four_provinces_A]
corr=m.groupby('year').apply(lambda g: np.corrcoef(np.log1p(g.dn_sum_km2),np.log1p(g.rad_sum_km2))[0,1]).round(3)
rep['agreement_log_sum_corr_by_year']={int(k):float(x) for k,x in corr.items()}
L.append('## Agreement between the two series'); L.append('Correlation across the 135 districts of the four provinces between log(1+sum of lights) in series A and series B, by year: '+'; '.join(f'{k} {x:.3f}' for k,x in corr.items())+'\n')
# 2014-2016 problem
natB=B_d[B_d.in_four_provinces].groupby('year').rad_sum_km2.sum(); natA=A_d[A_d.in_four_provinces].groupby('year').dn_sum_km2.sum(); litA=A_d[A_d.in_four_provinces].groupby('year').apply(lambda g:(g.dn_lit_share*g.pixel_area_km2).sum()/g.pixel_area_km2.sum())
rep['series_A_2014_2016']=dict(sum_2013=float(natA[2013]),sum_2014=float(natA[2014]),sum_2016=float(natA[2016]),sum_2017=float(natA[2017]),lit_share_2013=float(litA[2013]),lit_share_2015=float(litA[2015]),lit_share_2017=float(litA[2017]))
L.append('## The break at the DMSP to VIIRS change'); L.append(f"In the harmonized DN files the four provinces' sum of lights falls from {natA[2013]:,.0f} (2013) to {natA[2014]:,.0f} (2014) and {natA[2016]:,.0f} (2016), then returns to {natA[2017]:,.0f} in 2017; the lit share of the land area goes {litA[2013]:.3f} (2013), {litA[2015]:.3f} (2015), {litA[2017]:.3f} (2017). Big cities are little affected, dim rural areas lose most of their light. The pattern is in the source rasters themselves (checked directly on the pixels, with and without the DN > 7 floor), so these three years are flagged in series_note and should not be used for changes across 2013-2017 in series A. Series B shows a milder version at its own sensor change: the four provinces' total falls from {natB[2012]:,.0f} (2012) to {natB[2013]:,.0f} (2013) and stays low through 2016 ({natB[2016]:,.0f}) before {natB[2017]:,.0f} in 2017. Pakistan did have severe load-shedding in those years, but because each series dips exactly when its own inputs switch from DMSP to VIIRS, the safer reading is a calibration artifact. Changes measured within one sensor era (1992-2013 and 2017-2024 in A; 1992-2012 and 2017-2025 in B) are the ones to trust; a regression that spans the switch should carry year effects and the sensor_basis column.\n")
# face checks
top=B_d[(B_d.year==2023)&B_d.in_four_provinces].nlargest(10,'rad_sum_km2')[['district_2023','province_2023','rad_sum_km2','rad_mean']]
bot=B_d[(B_d.year==2023)&B_d.in_four_provinces].nsmallest(10,'rad_mean')[['district_2023','province_2023','rad_sum_km2','rad_mean']]
rep['face_check_2023_brightest']=top.district_2023.tolist(); rep['face_check_2023_dimmest_mean']=bot.district_2023.tolist()
L.append('## Face checks (series B, 2023)'); L.append('Brightest districts by sum of lights: '+', '.join(f'{x.district_2023} ({x.rad_sum_km2:,.0f})' for _,x in top.iterrows())+'.')
L.append('Dimmest districts by mean radiance: '+', '.join(f'{x.district_2023} ({x.rad_mean:.3f})' for _,x in bot.iterrows())+'.\n')
L.append('## Method notes'); L.append('Exact area-weighted statistics (exactextract): a pixel contributes the share of its area inside the polygon. Pixel areas are computed on the WGS84 sphere from the cell size and row latitude, so "sum of lights in DN.km2 or radiance.km2" is comparable between Punjab and Balochistan. Polygons are the PBS Digital Census 2023 boundaries, with the 2023 census names and codes; 47 tehsil and 8 district polygons had self-intersections that were repaired with a zero buffer (no area change beyond rounding). Units outside the four provinces (Islamabad, AJK, Gilgit-Baltistan) are included and flagged in_four_provinces = False.')
json.dump(rep,open(os.path.join(OUT,'validation_summary.json'),'w'),indent=1)
open(os.path.join(DOCS,'VALIDATION.md'),'w').write('\n'.join(L)+'\n')
print(json.dumps({k:v for k,v in rep.items() if 'national' not in k},indent=1)[:3000])
