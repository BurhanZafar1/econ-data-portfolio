"""Analysis-ready panel: night lights (both series) joined to the crosswalked census populations on the
Census 2023 units, tehsil and district, 1992-2025.

Inputs: output/ntl_A_*.csv, output/ntl_B_*.csv (this project) and, from the crosswalk project,
output/population_panel_2023_frame.csv and population_panel_2023_frame_districts.csv (every 2023 unit at
the censuses of 1951, 1961, 1972, 1981, 1998, 2017 and 2023).
Output: output/panel_ntl_census_tehsil_2023frame.csv and ..._district_2023frame.csv, one row per unit and
year 1992-2025, with
  - series B measures (rad_*) and series A measures (dn_*), each with its series_note
  - pop_census: the census population in census years (1998, 2017, 2023) and blank otherwise; no
    interpolation is done, so nothing is invented between censuses
  - rad_sum_km2_per_1000 and dn_sum_km2_per_1000: light per thousand people in census years
  - pop_1951 .. pop_2023 repeated on every row for convenience (constant-frame population history)
Only the four provinces' units carry census populations (the crosswalk covers those); Islamabad, AJK and
Gilgit-Baltistan rows keep their light measures with blank population.
"""
import os, pandas as pd, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,'..','output')
CW=os.environ.get('CROSSWALK_OUTPUT',next((p for p in [os.path.join(HERE,'..','..','02-pakistan-tehsil-crosswalk','output'),os.path.join(HERE,'..','..','pk_crosswalk','output')] if os.path.isdir(p)),''))
A_t=pd.read_csv(os.path.join(OUT,'ntl_A_harmonizedDN_tehsil_2023frame_1992_2024.csv')); A_d=pd.read_csv(os.path.join(OUT,'ntl_A_harmonizedDN_district_2023frame_1992_2024.csv'))
B_t=pd.read_csv(os.path.join(OUT,'ntl_B_viirslike_tehsil_2023frame_1992_2025.csv')); B_d=pd.read_csv(os.path.join(OUT,'ntl_B_viirslike_district_2023frame_1992_2025.csv'))
P_t=pd.read_csv(os.path.join(CW,'population_panel_2023_frame.csv')); P_d=pd.read_csv(os.path.join(CW,'population_panel_2023_frame_districts.csv'))
CENSUS={1998:'pop_1998',2017:'pop_2017',2023:'pop_2023'}
def build(B,A,P,key,pkey,ids):
    a=A.drop(columns=[c for c in ['area_km2','pixel_area_km2','coverage_pixels','in_four_provinces','outside_census_frame','tehsil_2023','district_2023','province_2023','census_name'] if c in A.columns]).rename(columns={'sensor_basis':'sensor_basis_A','series_note':'series_note_A'})
    b=B.rename(columns={'sensor_basis':'sensor_basis_B','series_note':'series_note_B'})
    m=b.merge(a,on=[key,'year'],how='outer')
    popcols=[c for c in P.columns if c.startswith('pop_')]
    pp=P[[pkey]+popcols].copy()
    m=m.merge(pp,left_on=ids,right_on=pkey,how='left')
    if pkey!=ids: m=m.drop(columns=[pkey])
    m['pop_census']=np.nan
    for y,c in CENSUS.items(): m.loc[m.year==y,'pop_census']=m.loc[m.year==y,c]
    m['rad_sum_km2_per_1000']=m.rad_sum_km2/(m.pop_census/1000)
    m['dn_sum_km2_per_1000']=m.dn_sum_km2/(m.pop_census/1000)
    return m.sort_values([key,'year'])
T=build(B_t,A_t,P_t,'dds_id','unit_id_2023','dds_id')
# district: join on district name (PBS 2023 names in both files)
P_d2=P_d.rename(columns={'district_2023':'census_name'})
D=build(B_d,A_d,P_d2,'district_code','census_name','census_name')
front_t=['dds_id','tehsil_2023','district_2023','province_2023','in_four_provinces','outside_census_frame','year','area_km2']
front_d=['district_code','district_2023','census_name','province_2023','in_four_provinces','outside_census_frame','year','area_km2']
T=T[front_t+[c for c in T.columns if c not in front_t]]; D=D[front_d+[c for c in D.columns if c not in front_d]]
T.to_csv(os.path.join(OUT,'panel_ntl_census_tehsil_2023frame.csv'),index=False); D.to_csv(os.path.join(OUT,'panel_ntl_census_district_2023frame.csv'),index=False)
print('tehsil panel',T.shape,'| units with census population',T[T.year==2023].pop_2023.notna().sum(),'| district panel',D.shape,'| districts with census population',D[D.year==2023].pop_2023.notna().sum())
# quick sanity: light per capita in 2023, top and bottom five districts (series B)
x=D[(D.year==2023)&D.pop_census.notna()].sort_values('rad_sum_km2_per_1000')
print('lowest light per 1000 people, 2023:',x.head(5)[['district_2023','rad_sum_km2_per_1000']].round(3).values.tolist())
print('highest:',x.tail(5)[['district_2023','rad_sum_km2_per_1000']].round(3).values.tolist())
