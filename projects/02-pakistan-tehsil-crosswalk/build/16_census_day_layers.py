"""Census-day 1998 frames for Sindh, NWFP (Khyber Pakhtunkhwa), FATA and Balochistan, from the scanned
PCO Census Publication 161 (January 2002), Tables 2, 3, 5 and 6, transcribed by hand from the page images
(raw/census1998_frames/transcribed/*.csv; every province, division and district sum re-added and checked).

The report scan of January 2002 lists the tehsils and districts as they stood on census day (1 March 1998),
with the 1951-1981 counts restated on them. The digital "1998 frame" used elsewhere in this project (PBS web
table, parsed by Data Darbar) is the same report re-issued on the mid-2000s map. This script links the two
with the same resolver as every other layer, then chains the census-day units to 2023, and joins Punjab's
layer (build/14) to give country-wide census-day tables.

Outputs (output/):
  unit_master_1998census_all.csv                       every census-day unit of the four provinces and FATA
  crosswalk_tehsil_1998census_to_pcoframe.csv          census-day tehsil -> report-frame tehsil (population flow)
  crosswalk_tehsil_1998census_to_2023.csv              chained to the Census 2023 frame (pop and area weights)
  crosswalk_district_1998census_to_pcoframe.csv        district level
  crosswalk_district_1998census_to_2023.csv            district level, chained
  validation_summary_censusday.json
"""
import pandas as pd, numpy as np, json, sys, re
import geopandas as gpd
sys.path.insert(0,'build'); from crosswalk_lib import solve_group, namematch, components, district_confidence
OUT='output/'; INT='build/intermediate/'; RAW='raw/census1998_frames/transcribed/'

# ---------------------------------------------------------------- 1. census-day leaves from the transcriptions
def up(s): return re.sub(r'\s+',' ',str(s).strip().upper())
rows=[]
S=pd.read_csv(RAW+'pub161_table5_sindh.csv')
for _,r in S[S.tier=='taluka'].iterrows():
    if r.district in ('KARACHI WEST','MALIR'): continue          # Karachi enters as its five districts, see below
    rows.append(dict(province='SINDH',district=up(r.district)+' DISTRICT',unit=up(r.unit),source_table='Pub161 Table 5',page=r.page,**{c:r[c] for c in ['area_km2','pop_1951','pop_1961','pop_1972','pop_1981','pop_1998']}))
for _,r in S[(S.tier=='district')&S.district.str.startswith(('KARACHI','MALIR'))].iterrows():
    rows.append(dict(province='SINDH',district=up(r.unit),unit=up(r.unit)+' (one unit)',source_table='Pub161 Table 5',page=r.page,**{c:r[c] for c in ['area_km2','pop_1951','pop_1961','pop_1972','pop_1981','pop_1998']}))
K=pd.read_csv(RAW+'pub161_table2_nwfp_table3_fata.csv')
for _,r in K[K.tier=='tehsil'].iterrows():
    rows.append(dict(province='KHYBER PAKHTUNKHWA' if r.table==2 else 'FATA',district=up(r.district),unit=up(r.unit),source_table=f'Pub161 Table {r.table}',page=r.page,**{c:r[c] for c in ['area_km2','pop_1951','pop_1961','pop_1972','pop_1981','pop_1998']}))
frs=K[(K.table==3)&(K.tier=='district')&K.unit.str.startswith('Tribal Area')]
for _,r in frs.iterrows():                                        # the six Frontier Regions have no tehsil row: the district is the unit
    rows.append(dict(province='FATA',district=up(r.district),unit=up(r.unit),source_table='Pub161 Table 3',page=r.page,**{c:r[c] for c in ['area_km2','pop_1951','pop_1961','pop_1972','pop_1981','pop_1998']}))
B=pd.read_csv(RAW+'pub161_table6_balochistan.csv')
bt=B[B.tier=='tehsil'].copy(); bt['nested']=bt.notes.fillna('').str.startswith('under')
for _,r in bt[bt.nested].iterrows():
    parent=re.match(r'under (.*?)(;|$)',r.notes).group(1).strip().split(' (')[0]
    name=up(r.unit);
    if '(PART)' in name: name=f'{name} [{up(parent)}]'           # Quetta Tehsil is printed in two parts, one per sub-division
    rows.append(dict(province='BALOCHISTAN',district=up(r.district)+' DISTRICT',unit=name,sub_division=up(parent),source_table='Pub161 Table 6',page=r.page,**{c:r[c] for c in ['area_km2','pop_1951','pop_1961','pop_1972','pop_1981','pop_1998']}))
U=pd.DataFrame(rows)
# check: nested Balochistan leaves add to their sub-divisions, and every district's leaves add to the district row
sd=bt[~bt.nested].set_index([bt[~bt.nested].district.map(lambda d:up(d)+' DISTRICT'),bt[~bt.nested].unit.map(lambda u:up(u).split(' (')[0])]).pop_1998
chk=U[U.province=='BALOCHISTAN'].groupby(['district','sub_division']).pop_1998.sum()
assert (chk.reindex(sd.index).values==sd.values).all(), 'Balochistan sub-division sums'
drows=pd.concat([S[S.tier=='district'].assign(d=lambda d:d.unit.map(up)),K[K.tier=='district'].assign(d=lambda d:d.unit.map(up)),B[B.tier=='district'].assign(d=lambda d:d.unit.map(up))])
dpop=drows.set_index('d').pop_1998
got=U.groupby('district').pop_1998.sum()
bad=[(d,int(got[d]),int(dpop[d])) for d in got.index if int(got[d])!=int(dpop[d])]
assert not bad, bad
U['pop_1998']=U.pop_1998.astype(int)
CODE={'SINDH':'SD','KHYBER PAKHTUNKHWA':'KP','FATA':'FA','BALOCHISTAN':'BA'}
U=U.sort_values(['province','district','unit']).reset_index(drop=True)
U['unit_id_1998census']=[f'T98C-{CODE[p]}-{i:03d}' for p,i in zip(U.province,U.groupby('province').cumcount()+1)]
print('census-day leaves:',U.province.value_counts().to_dict())

# ---------------------------------------------------------------- 2. the report frame (web table) and an adjacency proxy
m=pd.read_csv(INT+'unit_master_1998_solved_frame.csv'); m['pop_1998']=m.pop_1998.astype(int)
C23=pd.read_csv(OUT+'crosswalk_tehsil_1998_to_2023.csv')
g23=gpd.read_file('raw/pbs_tehsils_2023.geojson').to_crs(32642); g23['geometry']=g23.geometry.buffer(0); g23=g23.set_index('dds_id')
# each report-frame unit is represented by the union of the 2023 polygons it flows into (population weight > 0)
poly={}
for uid,grp in C23[C23.pop_weight>0].groupby('unit_id_1998'):
    ids=[i for i in grp.unit_id_2023 if i in g23.index]
    if ids: poly[uid]=g23.geometry.loc[ids].union_all() if hasattr(g23.geometry,'union_all') else g23.geometry.loc[ids].unary_union
def adjacency(id_anchor,id_other):
    a,b=poly.get(id_anchor),poly.get(id_other)
    if a is None or b is None: return 0.0
    shared=a.boundary.intersection(b.boundary).length; per=b.boundary.length
    return shared/per if per>0 else 0.0

# ---------------------------------------------------------------- 3. solve province by province
out=[]; dout=[]; summary={}
for prov in ['SINDH','KHYBER PAKHTUNKHWA','FATA','BALOCHISTAN']:
    old=U[U.province==prov].rename(columns={'unit_id_1998census':'id','unit':'name','pop_1998':'n'})[['id','name','n','district']].reset_index(drop=True)
    new=m[m.province_1998==prov].rename(columns={'unit_id_1998':'id','unit_1998':'name','pop_1998':'n','district_1998':'district'})[['id','name','n','district']].reset_index(drop=True)
    assert old.n.sum()==new.n.sum(), (prov,old.n.sum(),new.n.sum())
    # district level first
    dold=old.groupby('district',as_index=False)['n'].sum().assign(id=lambda d:d.district,name=lambda d:d.district)
    dnew=new.groupby('district',as_index=False)['n'].sum().assign(id=lambda d:d.district,name=lambda d:d.district)
    drs,dconf=solve_group(dold,dnew,None,prov+' [district level]')
    dflows={}
    for a,b,f,meth,c,note in drs:
        dout.append(dict(province=prov,district_1998census=a,district_1998_pcoframe=b,flow_1998=f,method=meth,confidence=c,note=note))
        if dconf in ('high','medium'): dflows[(a,b)]=f
    if dconf=='low': print('   district-level flows ambiguous in',prov,'; tehsil solve runs unconstrained')
    groups=components([(a,b) for a,b,f,*_ in drs])
    for o,nn in groups:
        og=old[old.district.isin(o)].reset_index(drop=True); ng=new[new.district.isin(nn)].reset_index(drop=True)
        label=prov+': '+'|'.join(sorted(nn))
        if og.n.sum()!=ng.n.sum():   # a group cut by an ambiguous district solve: fall back to the whole province
            og,ng,label=old,new,prov+' (whole province)'
        rs,conf=solve_group(og,ng,adjacency,label,district_flows={k:v for k,v in dflows.items() if k[0] in set(og.district)})
        for oid,nid,flow,method,rconf,note in rs: out.append(dict(district_group=label,unit_id_1998census=oid,unit_id_1998=nid,flow_1998=flow,method=method,confidence=rconf,note=note))
        if label.endswith('(whole province)'): break
X=pd.DataFrame(out).drop_duplicates(['unit_id_1998census','unit_id_1998'])
a=U.set_index('unit_id_1998census'); b=m.set_index('unit_id_1998')
X['province']=X.unit_id_1998census.map(a.province); X['district_1998census']=X.unit_id_1998census.map(a.district); X['unit_1998census']=X.unit_id_1998census.map(a.unit); X['pop_1998census']=X.unit_id_1998census.map(a.pop_1998)
X['district_1998_pcoframe']=X.unit_id_1998.map(b.district_1998); X['unit_1998_pcoframe']=X.unit_id_1998.map(b.unit_1998); X['pop_1998_pcoframe']=X.unit_id_1998.map(b.pop_1998)
X['pop_weight']=X.flow_1998/X.pop_1998census
X['weight_basis']=np.where(X.note.str.startswith('same name')|(X.method=='one_to_one'),'pub161_censusday_vs_webframe_exact','pub161_censusday_vs_webframe+milp_adjacency')
X.loc[X.unit_1998_pcoframe.str.contains('all towns'),'note']=X.loc[X.unit_1998_pcoframe.str.contains('all towns'),'note']+'; Karachi is one unit in the report frame (2001 towns), so the five census-day districts map to the collapsed unit'
X=X[['district_group','unit_id_1998census','province','district_1998census','unit_1998census','pop_1998census','unit_id_1998','district_1998_pcoframe','unit_1998_pcoframe','pop_1998_pcoframe','flow_1998','pop_weight','weight_basis','method','confidence','note']]
# ---------------------------------------------------------------- 4. join Punjab (build/14) and check
P=pd.read_csv(OUT+'crosswalk_tehsil_1998census_to_pcoframe_punjab.csv').drop(columns=['area_1998census_km2'])
P['weight_basis']=P.weight_basis.str.replace('punjab_1998_table_vs_pco','punjab1998table_vs_webframe')
PBNAME={'DERA GHAZI KHAN':'D.G.KHAN DISTRICT','MANDI BAHA-UD-DIN':'MANDI BAHAUDDIN DISTRICT','LAHORE':'LAHORE CITY DISTRICT'}   # Punjab table spellings -> report spellings (as in build/14)
P['district_1998census']=[PBNAME.get(d,d+' DISTRICT') for d in P.district_1998census]
X=pd.concat([P[X.columns],X]).sort_values(['unit_id_1998census','unit_id_1998']).reset_index(drop=True)
_in=X.groupby('unit_id_1998').flow_1998.sum()
assert np.allclose(X.groupby('unit_id_1998census').pop_weight.sum(),1) and (_in==b.pop_1998.reindex(_in.index)).all() and set(_in.index)==set(b.index)
X.to_csv(OUT+'crosswalk_tehsil_1998census_to_pcoframe.csv',index=False)
print('tehsil rows',len(X),'| confidence',X.confidence.value_counts().to_dict(),'| census-day units split',(X.groupby('unit_id_1998census').size()>1).sum())
# unit master (Punjab from 14; PCO restated 1951-1981 counts exist only for the Pub161 provinces)
PU=pd.read_csv(OUT+'unit_master_1998census_punjab.csv').rename(columns={'pop_1998':'pop_1998census','area_km2':'area_km2'})
PU['source_table']='Government of the Punjab 1998 census table (raw/punjab1998)'
PU['district_1998census']=[PBNAME.get(d,d+' DISTRICT') for d in PU.district_1998census]
UM=pd.concat([PU.assign(sub_division=np.nan,page=np.nan),U.rename(columns={'district':'district_1998census','unit':'unit_1998census','pop_1998':'pop_1998census'})])
UM=UM[['unit_id_1998census','province','district_1998census','unit_1998census','sub_division','pop_1998census','area_km2','pop_1951','pop_1961','pop_1972','pop_1981','source_table','page']].sort_values('unit_id_1998census')
UM.to_csv(OUT+'unit_master_1998census_all.csv',index=False)
# ---------------------------------------------------------------- 5. chain to 2023
C=C23[['unit_id_1998','unit_id_2023','province_2023','district_2023','unit_2023','pop_2023','pop_weight','area_weight','confidence']].rename(columns={'pop_weight':'w2','area_weight':'aw2','confidence':'c2'})
Z=X.merge(C,on='unit_id_1998'); Z['flow']=Z.flow_1998*Z.w2; Z['area']=Z.pop_weight*Z.aw2
rank={'high':2,'medium':1,'low':0}; inv={2:'high',1:'medium',0:'low'}
Z['c']=np.minimum(Z.confidence.map(rank),Z.c2.map(rank))
G=Z.groupby(['unit_id_1998census','unit_id_2023'],as_index=False).agg(flow_1998=('flow','sum'),area=('area','sum'),conf=('c','min'),via_pco_units=('unit_1998_pcoframe',lambda s:'; '.join(sorted(set(s)))),province_2023=('province_2023','first'),district_2023=('district_2023','first'),unit_2023=('unit_2023','first'),pop_2023=('pop_2023','first'))
for c in ['province','district_1998census','unit_1998census','pop_1998census']: G[c]=G.unit_id_1998census.map(UM.set_index('unit_id_1998census')[c])
G['pop_weight']=G.flow_1998/G.pop_1998census; G['area_weight']=G.area/G.groupby('unit_id_1998census').area.transform('sum'); G['confidence']=G.conf.map(inv)
G['weight_basis']='chained: census-day 1998 unit -> report frame -> 2017 -> 2023'
G=G[['unit_id_1998census','province','district_1998census','unit_1998census','pop_1998census','unit_id_2023','province_2023','district_2023','unit_2023','pop_2023','flow_1998','pop_weight','area_weight','via_pco_units','weight_basis','confidence']].sort_values(['unit_id_1998census','unit_id_2023'])
G_exact=G.copy(); G['flow_1998']=G.flow_1998.round(2)
assert np.allclose(G.groupby('unit_id_1998census').pop_weight.sum(),1) and np.allclose(G.groupby('unit_id_1998census').area_weight.sum(),1)
assert abs(G.flow_1998.sum()-UM.pop_1998census.sum())<1
G.to_csv(OUT+'crosswalk_tehsil_1998census_to_2023.csv',index=False)
print('chained rows',len(G),'| confidence',G.confidence.value_counts().to_dict())
# ---------------------------------------------------------------- 6. district level
D=X.groupby(['province','district_1998census','district_1998_pcoframe'],as_index=False).agg(flow_1998=('flow_1998','sum'))
D['confidence']=D.apply(district_confidence(X,'district_1998census','district_1998_pcoframe'),axis=1)
D['pop_1998census']=D.district_1998census.map(UM.groupby('district_1998census').pop_1998census.sum())
D['pop_1998_pcoframe']=D.district_1998_pcoframe.map(m.groupby('district_1998').pop_1998.sum())
D['pop_weight']=D.flow_1998/D.pop_1998census
assert np.allclose(D.groupby('district_1998census').pop_weight.sum(),1)
D.to_csv(OUT+'crosswalk_district_1998census_to_pcoframe.csv',index=False)
D2=G_exact.groupby(['province','district_1998census','district_2023'],as_index=False).agg(flow_1998=('flow_1998','sum'),area_weight=('area_weight','sum'),confidence=('confidence',lambda s:inv[min(rank[x] for x in s)]))
# (at the 2023 end the weakest unit row is the right grade: most census-day districts are split across several 2023 districts)
D2['pop_1998census']=D2.district_1998census.map(UM.groupby('district_1998census').pop_1998census.sum()); D2['pop_weight']=D2.flow_1998/D2.pop_1998census
# area weight at district level: share of the census-day district's area-weight mass (unit area weights averaged with population weights of the units)
aw=G_exact.assign(w=lambda d:d.area_weight*d.pop_1998census).groupby(['district_1998census','district_2023']).w.sum(); awt=aw.groupby(level=0).transform('sum'); D2['area_weight']=[aw[(a,b)]/awt[(a,b)] for a,b in zip(D2.district_1998census,D2.district_2023)]
assert np.allclose(D2.groupby('district_1998census').pop_weight.sum(),1,atol=1e-10) and np.allclose(D2.groupby('district_1998census').area_weight.sum(),1,atol=1e-10)
D2.to_csv(OUT+'crosswalk_district_1998census_to_2023.csv',index=False)
print('district rows',len(D),'/',len(D2),'| district-level differences (census-day vs report frame):',int((D.pop_weight<1).sum()),'census-day districts split')
summary=dict(census_day_units=int(len(UM)),census_day_districts=int(UM.district_1998census.nunique()),report_frame_units=int(len(m)),tehsil_rows=int(len(X)),tehsil_confidence=X.confidence.value_counts().to_dict(),
             chained_rows=int(len(G)),chained_confidence=G.confidence.value_counts().to_dict(),population_total=int(UM.pop_1998census.sum()),population_total_report_frame=int(m.pop_1998.sum()),
             weights_sum_to_one=True,totals_conserved=True,district_rows=int(len(D)),district_rows_2023=int(len(D2)),
             district_level_flows=dout)
json.dump(summary,open(OUT+'validation_summary_censusday.json','w'),indent=1,default=str)
