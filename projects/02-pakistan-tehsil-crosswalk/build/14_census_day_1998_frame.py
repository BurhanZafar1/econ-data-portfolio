"""The census-day 1998 tehsil frame (1 March 1998) versus the PCO report frame.

PCO's *Population of Administrative Units 1951-98* prints 1998 populations on the administrative map of
the mid-2000s (it contains Ahmedpur Sial, Dina, Kallar Kahar, Kallar Sayyadan, Kot Momin, Gujranwala City
and Saddar, Nushki, and the 2001 towns of Lahore, Karachi and Peshawar), so "1998 frame" elsewhere in this
project means that report's frame. For Punjab the Punjab Government published the 1998 census by the
tehsils as they stood on census day (34 districts, 118 tehsils; raw/punjab1998/). This script
 a) cross-checks the two frames (every district total agrees; 109 tehsils agree to the person),
 b) builds crosswalk_tehsil_1998census_to_pcoframe_punjab.csv with the same resolver as the other layers
    (Lahore's two census-day tehsils map to the collapsed Lahore unit, since the report's Lahore towns are
    not nested in either tehsil),
 c) chains it to the 2023 frame: crosswalk_tehsil_1998census_to_2023_punjab.csv.
Other provinces: added if a census-day table is found (see raw/census1998_frames/SOURCES_1998_frames.csv).
"""
import pandas as pd, numpy as np, re, sys
sys.path.insert(0,'build'); from crosswalk_lib import solve_group, namematch
OUT='output/'; INT='build/intermediate/'
t=pd.read_html('raw/punjab1998/punjab_1998_tehsil_table.xls')[1]; t.columns=t.iloc[0]; t=t.iloc[1:]
t=t.rename(columns={'Admin_Unit':'unit','District':'district','Area_Measurment_Sqkm':'area_km2','Both_sexes':'pop_1998'})
t['pop_1998']=t.pop_1998.astype(int); t['area_km2']=t.area_km2.astype(float)
D=t[t.unit.str.endswith('DISTRICT')].copy(); T=t[~t.unit.str.endswith('DISTRICT')].copy()
assert (T.groupby('district').pop_1998.sum().reindex(D.district).values==D.pop_1998.values).all()
T['unit_id_1998census']=['T98C-PB-'+f'{i:03d}' for i in range(1,len(T)+1)]
T['province']='PUNJAB'
NAME={'DERA GHAZI KHAN':'D.G.KHAN DISTRICT','MANDI BAHA-UD-DIN':'MANDI BAHAUDDIN DISTRICT','LAHORE':'LAHORE CITY DISTRICT'}
T['district_pco']=[NAME.get(d,d+' DISTRICT') for d in T.district]
m=pd.read_csv(INT+'unit_master_1998_solved_frame.csv'); mp=m[m.province_1998=='PUNJAB'].copy()
assert set(T.district_pco)==set(mp.district_1998), set(T.district_pco)^set(mp.district_1998)
# a) cross-check
dsum=mp.groupby('district_1998').pop_1998.sum(); assert (dsum.reindex(T.groupby('district_pco').pop_1998.sum().index).values==T.groupby('district_pco').pop_1998.sum().values).all()
same=0
for _,r in T.iterrows():
    c=mp[(mp.district_1998==r.district_pco)&(mp.pop_1998==r.pop_1998)&mp.unit_1998.map(lambda u:namematch(u,r.unit))]
    same+=len(c)>0
print(f'census-day Punjab tehsils {len(T)}; PCO-frame Punjab units {len(mp)}; district totals all agree; tehsils identical in name and population: {same}')
# b) crosswalk by district group
rows=[]
for d,g in T.groupby('district_pco'):
    old=g.rename(columns={'unit_id_1998census':'id','unit':'name','pop_1998':'n'})[['id','name','n']].assign(district=d).reset_index(drop=True)
    new=mp[mp.district_1998==d].rename(columns={'unit_id_1998':'id','unit_1998':'name','pop_1998':'n'})[['id','name','n']].assign(district=d).reset_index(drop=True)
    new['n']=new['n'].astype(int)
    rs,conf=solve_group(old,new,None,d)
    for oid,nid,flow,method,rconf,note in rs: rows.append(dict(district_group=d,unit_id_1998census=oid,unit_id_1998=nid,flow_1998=flow,method=method,confidence=rconf,note=note))
X=pd.DataFrame(rows)
a=T.set_index('unit_id_1998census'); b=mp.set_index('unit_id_1998')
X['province']='PUNJAB'; X['district_1998census']=X.unit_id_1998census.map(a.district); X['unit_1998census']=X.unit_id_1998census.map(a.unit); X['pop_1998census']=X.unit_id_1998census.map(a.pop_1998); X['area_1998census_km2']=X.unit_id_1998census.map(a.area_km2)
X['district_1998_pcoframe']=X.unit_id_1998.map(b.district_1998); X['unit_1998_pcoframe']=X.unit_id_1998.map(b.unit_1998); X['pop_1998_pcoframe']=X.unit_id_1998.map(b.pop_1998).astype(int)
X['pop_weight']=X.flow_1998/X.pop_1998census
X['weight_basis']=np.where(X.note.str.startswith('same name')|(X.method=='one_to_one'),'punjab_1998_table_vs_pco_exact','punjab_1998_table_vs_pco+milp')
X.loc[X.unit_1998_pcoframe.str.contains('all towns'),'note']=X.loc[X.unit_1998_pcoframe.str.contains('all towns'),'note']+'; the report lists 2001 towns for Lahore, which are not nested in the two census-day tehsils, so both map to the collapsed Lahore unit'
X=X[['district_group','unit_id_1998census','province','district_1998census','unit_1998census','pop_1998census','area_1998census_km2','unit_id_1998','district_1998_pcoframe','unit_1998_pcoframe','pop_1998_pcoframe','flow_1998','pop_weight','weight_basis','method','confidence','note']].sort_values(['unit_id_1998census','unit_id_1998'])
_in=X.groupby('unit_id_1998').flow_1998.sum(); assert np.allclose(X.groupby('unit_id_1998census').pop_weight.sum(),1) and (_in==b.pop_1998.reindex(_in.index).astype(int)).all()
X.to_csv(OUT+'crosswalk_tehsil_1998census_to_pcoframe_punjab.csv',index=False)
print('rows',len(X),'| confidence',X.confidence.value_counts().to_dict(),'| census-day tehsils split',(X.groupby("unit_id_1998census").size()>1).sum())
# c) chain to 2023
C=pd.read_csv(OUT+'crosswalk_tehsil_1998_to_2023.csv')[['unit_id_1998','unit_id_2023','province_2023','district_2023','unit_2023','pop_2023','pop_weight','area_weight','confidence']].rename(columns={'pop_weight':'w2','area_weight':'aw2','confidence':'c2'})
Z=X.merge(C,on='unit_id_1998')
Z['flow']=Z.flow_1998*Z.w2
# area: census-day tehsil area split in proportion to persons, then area weights of the PCO unit onwards
Z['area']=Z.area_1998census_km2*Z.pop_weight*Z.aw2
rank={'high':2,'medium':1,'low':0}; inv={2:'high',1:'medium',0:'low'}
Z['c']=np.minimum(Z.confidence.map(rank),Z.c2.map(rank))
G=Z.groupby(['unit_id_1998census','unit_id_2023'],as_index=False).agg(flow_1998=('flow','sum'),area=('area','sum'),conf=('c','min'),via_pco_units=('unit_1998_pcoframe',lambda s:'; '.join(sorted(set(s)))),province_2023=('province_2023','first'),district_2023=('district_2023','first'),unit_2023=('unit_2023','first'),pop_2023=('pop_2023','first'))
for c in ['district_1998census','unit_1998census','pop_1998census','area_1998census_km2']: G[c]=G.unit_id_1998census.map(a.rename(columns={'district':'district_1998census','unit':'unit_1998census','pop_1998':'pop_1998census','area_km2':'area_1998census_km2'})[c])
G['pop_weight']=G.flow_1998/G.pop_1998census; G['area_weight']=G.area/G.groupby('unit_id_1998census').area.transform('sum'); G['confidence']=G.conf.map(inv)
G['weight_basis']='chained: census-day 1998 tehsil -> PCO frame -> 2017 -> 2023'
G=G[['unit_id_1998census','district_1998census','unit_1998census','pop_1998census','area_1998census_km2','unit_id_2023','province_2023','district_2023','unit_2023','pop_2023','flow_1998','pop_weight','area_weight','via_pco_units','weight_basis','confidence']].sort_values(['unit_id_1998census','unit_id_2023'])
G['flow_1998']=G.flow_1998.round(2)
assert np.allclose(G.groupby('unit_id_1998census').pop_weight.sum(),1)
G.to_csv(OUT+'crosswalk_tehsil_1998census_to_2023_punjab.csv',index=False)
print('chained rows',len(G),'| confidence',G.confidence.value_counts().to_dict(),'| total conserved',abs(G.flow_1998.sum()-T.pop_1998.sum())<1)
T[['unit_id_1998census','province','district','unit','pop_1998','area_km2']].rename(columns={'district':'district_1998census','unit':'unit_1998census'}).to_csv(OUT+'unit_master_1998census_punjab.csv',index=False)
