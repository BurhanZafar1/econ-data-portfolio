"""1998 frame: sub-district units as listed in PBS/PCO 'Population of Administrative Units 1951-98'
(Census Publication 161), as parsed by Data Darbar (census_admin_units_1951_1998), four provinces + FATA.
Lowest published tier is kept: tehsils / sub-tehsils; a sub-division only where it has no tehsil rows;
Frontier Regions are single units. For Lahore, Karachi and Peshawar the report lists the post-2001
towns and cantonments, not the 1998 census tehsils; they are flagged (frame_note)."""
import pandas as pd, numpy as np
a=pd.read_parquet('raw/census_admin_units_1951_1998.parquet')
prov={'PUNJAB PROVINCE':'PUNJAB','SINDH PROVINCE':'SINDH','NORTH WEST FRONTIER PROVINCE':'KHYBER PAKHTUNKHWA','BALOCHISTAN PROVINCE':'BALOCHISTAN','F.A.T.A.':'FATA'}
a=a[(a.locality=='all')&a.province.isin(prov)].copy(); a['prov']=a.province.map(prov)
a=a.fillna({'sub_division':'','tehsil':'','mark':''})
w=a.pivot_table(index=['prov','district','sub_division','tehsil','unit','unit_type'],columns='census_year',values='population',aggfunc='first').reset_index()
w.columns=[str(c) for c in w.columns]
mk=a[a.census_year==1998].groupby(['prov','district','sub_division','tehsil','unit','unit_type'])['mark'].first().reset_index()
w=w.merge(mk,on=['prov','district','sub_division','tehsil','unit','unit_type'],how='left').fillna({'mark':''})
ar=a[a.census_year==1998].groupby(['prov','district','unit','unit_type'],dropna=False).area_sq_km.first().reset_index()
w=w.merge(ar,on=['prov','district','unit','unit_type'],how='left')
# districts
d=w[w.unit_type=='district'].copy()
d['district_std']=d.district.str.upper().str.strip()
# FR rows: district column is 'Tribal Area Adjoining', unit is the full name
d.loc[d.district.str.startswith('Tribal Area'),'district_std']=d.unit.str.upper().str.replace('TRIBAL AREA ADJOINING ','FR ').str.replace(' DISTRICT','')
# units
t=w[w.unit_type=='tehsil'].copy()
sd=w[(w.unit_type=='sub_division')].copy()
has_kids=set(zip(t.prov,t.district,t.sub_division))
sd=sd[[ (p,dd,s) not in has_kids for p,dd,s in zip(sd.prov,sd.district,sd.sub_division)]]
fr=d[d.district.str.startswith('Tribal Area')].copy()
u=pd.concat([t,sd,fr],ignore_index=True)
u['district_std']=u.district.str.upper().str.strip()
u.loc[u.district.str.startswith('Tribal Area'),'district_std']=u.unit.str.upper().str.replace('TRIBAL AREA ADJOINING ','FR ').str.replace(' DISTRICT','')
u['unit_std']=u.unit.str.upper().str.strip()
u['frame_note']=np.where(u.district_std.isin(['LAHORE CITY DISTRICT','KARACHI CITY DISTRICT','PESHAWAR DISTRICT'])&u.unit_std.str.contains('TOWN|CANTT',regex=True).fillna(False),'post-2001 town/cantonment as listed in the 1951-98 report, not a 1998 census tehsil','')
u=u.rename(columns={'1998':'pop_1998','1981':'pop_1981','1972':'pop_1972','1961':'pop_1961','1951':'pop_1951','area_sq_km':'area_km2'})
u=u[['prov','district_std','unit_std','unit_type','pop_1998','pop_1981','pop_1972','pop_1961','pop_1951','area_km2','mark','frame_note']].rename(columns={'prov':'province_1998','district_std':'district_1998','unit_std':'unit_1998','unit_type':'unit_type_1998'})
u=u.sort_values(['province_1998','district_1998','unit_1998']).reset_index(drop=True)
u['unit_id_1998']=['T98-'+f'{i:04d}' for i in range(1,len(u)+1)]
d=d.rename(columns={'1998':'pop_1998','1981':'pop_1981','area_sq_km':'area_km2','prov':'province_1998'})[['province_1998','district_std','pop_1998','pop_1981','area_km2']].rename(columns={'district_std':'district_1998'}).drop_duplicates(['province_1998','district_1998'])
# align district names with the unit file (two agencies carry 'AGENCY' only on their tehsil rows)
ud=set(u.district_1998); d['district_1998']=[x if x in ud else (x+' AGENCY' if x+' AGENCY' in ud else x) for x in d.district_1998]
assert set(d.district_1998)==ud, set(d.district_1998)^ud
# checks: units sum to districts
s=u.groupby(['province_1998','district_1998']).pop_1998.sum()
chk=d.set_index(['province_1998','district_1998']).pop_1998
diff=(s-chk.reindex(s.index)); assert diff.abs().max()==0 and diff.notna().all(); print('districts where units do not sum to district pop:'); print(diff[diff.abs()>0])
print(len(u),'units;',len(d),'districts; province sums:',u.groupby('province_1998').pop_1998.sum().astype(int).to_dict())
u.to_csv('output/unit_master_1998.csv',index=False); d.to_csv('output/district_master_1998.csv',index=False)
