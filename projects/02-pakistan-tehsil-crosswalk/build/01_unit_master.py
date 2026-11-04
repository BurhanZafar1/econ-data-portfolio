"""Build unit master tables for the 2017 and 2023 census frames from PBS Table 1
(as parsed by Data Darbar from PBS's published Excel tables). Four provinces only."""
import pandas as pd, numpy as np, re, sys
RAW='raw/'; OUT='output/'
PROV={'PUNJAB','SINDH','KHYBER PAKHTUNKHWA','BALOCHISTAN'}
def t1(year):
    p=pd.read_parquet(RAW+f'census_panel_{year}.parquet')
    p=p[(p.table_id=='1')&(p.locality=='all')&(p.sex=='all')]
    return p
def pivot(p, cols):
    w=p.pivot_table(index=[c for c in ['province_area','district','unit','unit_type','dds_id'] if c in p.columns],
                    columns='indicator', values='value', aggfunc='first').reset_index()
    w=w.rename(columns=cols)
    return w
# ---- 2023
p=t1(2023)
w23=pivot(p,{'AREA SQ.K.M':'area_km2','POPULATION-2023 / ALL SEXES':'pop_2023','POPULATION 2017':'pop_2017_restated'})
w23=w23[['province_area','district','unit','unit_type','dds_id','area_km2','pop_2023','pop_2017_restated']]
# ---- 2017
p=t1(2017)
w17=pivot(p,{'AREA (SQ. KM.)':'area_km2','POPULATION - 2017 / ALL SEXES':'pop_2017','POPULATION 1998':'pop_1998_restated'})
w17=w17[['province_area','district','unit','unit_type','area_km2','pop_2017','pop_1998_restated']]
print('2023 rows',len(w23), w23.unit_type.value_counts().to_dict()); print('2017 rows',len(w17), w17.unit_type.value_counts().to_dict())
print('2017 provinces', w17.province_area.value_counts().to_dict()); print('2023 provinces', w23.province_area.value_counts().to_dict())
w17.to_csv(OUT+'unit_master_2017_all.csv',index=False); w23.to_csv(OUT+'unit_master_2023_all.csv',index=False)
# checks against the KP 2023 Table 1 PDF read on 2 Nov 2026
chk={('ABBOTTABAD TEHSIL'):(1003339,939576),('BANKAND RANOLIA TEHSIL'):(205851,56366),('PALAS SUB-DIVISION'):(137502,181044),('WANA TEHSIL'):(184645,153156),('PESHAWAR TEHSIL'):(2113596,2183787)}
for u,(a,b) in chk.items():
    r=w23[(w23.unit==u)&(w23.province_area=='KHYBER PAKHTUNKHWA')]
    print(u, 'OK' if len(r)==1 and int(r.pop_2023.iloc[0])==a and int(r.pop_2017_restated.iloc[0])==b else ('MISMATCH',r[['pop_2023','pop_2017_restated']].values))
