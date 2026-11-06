"""Crosswalk of 1998 census tehsils (PCO Report 161 frame) onto 2017 census tehsils, using the
"POPULATION 1998" column of Census 2017 Table 1 (PBS restates 1998 counts on 2017 units).

Steps
 1. District groups: namesake districts plus the district-level flows that balance 1998 totals
    against 2017 restated totals (listed in DISTRICT_EDGES, each checked by population balance).
 2. Within each group, match 1998 units to 2017 units with the resolver in crosswalk_lib
    (name + exact population, exact partitions, else transportation LP with Demobase 2017
    polygon adjacency as the prior).
 3. Lahore, Karachi and Peshawar: the 1951-98 report lists post-2001 towns, not 1998 tehsils, so
    the 1998 side is collapsed to the district (Karachi is one unit at the user's request).
Outputs build/intermediate/crosswalk_tehsil_1998_to_2017_pop.csv
"""
import pandas as pd, numpy as np, geopandas as gpd, json, sys
sys.path.insert(0,'build'); from crosswalk_lib import solve_group, components
OUT='output/'; INT='build/intermediate/'
PROV={'PUNJAB','SINDH','BALOCHISTAN','KHYBER PAKHTUNKHWA','FATA'}
m98=pd.read_csv(OUT+'unit_master_1998.csv'); d98=pd.read_csv(OUT+'district_master_1998.csv')
m17=pd.read_csv(OUT+'unit_master_2017_all.csv')
t17=m17[(m17.unit_type!='district')&m17.province_area.isin(PROV)].copy()
t17['unit_id_2017']=['T17-'+f'{i:04d}' for i in range(1,len(t17)+1)]
D17=m17[(m17.unit_type=='district')&m17.province_area.isin(PROV)].copy()

# --- collapse town frames to district level -------------------------------------------------
COLLAPSE={'KARACHI CITY DISTRICT':'KARACHI CITY DISTRICT (all towns, one unit)',
          'LAHORE CITY DISTRICT':'LAHORE CITY DISTRICT (all towns, one unit)',
          'PESHAWAR DISTRICT':'PESHAWAR DISTRICT (all towns, one unit)'}
rows=[]
for d,label in COLLAPSE.items():
    sub=m98[m98.district_1998==d]
    assert sub.frame_note.notna().all(), d
    rows.append(dict(province_1998=sub.province_1998.iloc[0],district_1998=d,unit_1998=label,unit_type_1998='district_collapsed',
        pop_1998=sub.pop_1998.sum(),area_km2=sub.area_km2.sum(),unit_id_1998='T98-'+d.split()[0][:3]+'-ALL',
        frame_note='1951-98 report lists post-2001 towns here, not 1998 tehsils; collapsed to the district'))
m98=pd.concat([m98[~m98.district_1998.isin(COLLAPSE)],pd.DataFrame(rows)],ignore_index=True)
assert m98.groupby('district_1998').pop_1998.sum().reindex(d98.district_1998).eq(d98.pop_1998.values).all()

# --- district edges (1998 district -> 2017 district), by name or population balance ------------
norm={'D.G.KHAN':'DERA GHAZI KHAN','D.I.KHAN':'DERA ISMAIL KHAN','NAWAB SHAH':'SHAHEED BENAZIRABAD','BOLAN':'KACHHI',
      'JAFARABAD':'JAFFARABAD','MALAKAND PROTECTED AREA':'MALAKAND','LAHORE CITY':'LAHORE'}
def key(s):
    s=s.upper().replace(' DISTRICT','').replace(' AGENCY','').strip(); return norm.get(s,s)
d98['k']=d98.district_1998.map(key); D17['k']=D17.district.map(key)
edges=[(a,b) for a,b in zip(d98.district_1998,d98.k) if b in set(D17.k)]
edges=[(r.district_1998, D17[D17.k==r.k].district.iloc[0]) for _,r in d98.iterrows() if r.k in set(D17.k)]
def d17name(k): return D17[D17.k==k].district.iloc[0]
def d98name(k): return d98[d98.k==k].district_1998.iloc[0]
EXTRA=[('JHANG','CHINIOT'),('SHEIKHUPURA','NANKANA SAHIB'),('DADU','JAMSHORO'),('JACOBABAD','KASHMORE'),('JAFARABAD','SOHBATPUR'),
       ('SIBI','HARNAI'),('ZHOB','SHERANI'),('KHARAN','WASHUK'),('MANSEHRA','TORGHAR'),('THATTA','SUJAWAL'),
       ('MIRPUR KHAS','UMER KOT'),('SANGHAR','UMER KOT'),
       ('HYDERABAD','MATIARI'),('HYDERABAD','TANDO ALLAHYAR'),('HYDERABAD','TANDO MUHAMMAD KHAN'),
       ('BADIN','MATIARI'),('BADIN','TANDO ALLAHYAR'),('BADIN','TANDO MUHAMMAD KHAN'),
       ('LARKANA','KAMBAR SHAHDAD KOT'),('KHAIRPUR','KAMBAR SHAHDAD KOT'),('LARKANA','KHAIRPUR'),
       ('KASUR','LAHORE'),('UPPER DIR','LOWER DIR'),('MASTUNG','QUETTA'),('SUKKUR','GHOTKI')]
for k in ['KARACHI CENTRAL','KARACHI EAST','KARACHI SOUTH','KARACHI WEST','KORANGI','MALIR']: EXTRA.append(('KARACHI CITY',k))
for a,b in EXTRA: edges.append((d98name(norm.get(a,a)) if norm.get(a,a) in set(d98.k) else d98name(a), d17name(norm.get(b,b))))
groups=components(edges)
assert set(d98.district_1998)=={x for o,_ in groups for x in o}, set(d98.district_1998)-{x for o,_ in groups for x in o}
assert set(D17.district)=={x for _,n in groups for x in n}, set(D17.district)-{x for _,n in groups for x in n}

# --- adjacency from Demobase 2017 polygons ---------------------------------------------------
mt=pd.read_csv(INT+'demobase2017_match.csv')
g=gpd.read_file('raw/demobase/Pakistan.gdb',layer='PK_GEOG1_ADM4_2017_uscb_202401').to_crs(32642)
g['geometry']=g.geometry.buffer(0); g=g.set_index('GEO_MATCH')
geo=dict(zip(mt.unit_id_2017,mt.geo))
def adjacency(id_anchor,id_other):
    a,b=geo.get(id_anchor),geo.get(id_other)
    if a is None or b is None or a not in g.index or b not in g.index: return 0.0
    ga,gb=g.geometry[a],g.geometry[b]
    shared=ga.boundary.intersection(gb.boundary).length; per=gb.boundary.length
    return shared/per if per>0 else 0.0

# --- solve each group ---------------------------------------------------------------------------
out=[]; log=[]; dlog=[]
for gi,(o98,n17) in enumerate(sorted(groups,key=lambda g:sorted(g[1])[0])):
    old=m98[m98.district_1998.isin(o98)].rename(columns={'unit_id_1998':'id','unit_1998':'name','pop_1998':'n'})[['id','name','n','district_1998']].reset_index(drop=True)
    new=t17[t17.district.isin(n17)].rename(columns={'unit_id_2017':'id','unit':'name','pop_1998_restated':'n'})[['id','name','n','district']].reset_index(drop=True)
    old['n']=old['n'].astype(int); new['n']=new['n'].astype(int)
    label='|'.join(sorted(n17))
    old=old.rename(columns={'district_1998':'district'})
    # district-level flows first (names + population balance), imposed on the tehsil solve
    dold=old.groupby('district',as_index=False)['n'].sum().assign(id=lambda d:d.district,name=lambda d:d.district)
    dnew=new.groupby('district',as_index=False)['n'].sum().assign(id=lambda d:d.district,name=lambda d:d.district)
    dflows={}
    if len(dold)>1 or len(dnew)>1:
        drows,dconf=solve_group(dold,dnew,None,label+' [district level]')
        for a,b,f,meth,c,note in drows:
            dlog.append(dict(group=label,district_1998=a,district_2017=b,flow_1998=f,method=meth,confidence=c,note=note))
            if dconf in ('high','medium'): dflows[(a,b)]=f
        if dconf!='high': print('   district-level flows ambiguous; tehsil solve runs unconstrained',flush=True)
    if old['n'].sum()!=new['n'].sum():
        log.append(dict(group=label,pop98=int(old['n'].sum()),pop17_restated=int(new['n'].sum()))); print('IMBALANCE',label,old['n'].sum(),new['n'].sum()); continue
    rows,conf=solve_group(old,new,adjacency,label,district_flows=dflows)
    for oid,nid,flow,method,rconf,note in rows:
        out.append(dict(district_group=label,unit_id_1998=oid,unit_id_2017=nid,flow_1998=flow,method=method,confidence=rconf,note=note))
cw=pd.DataFrame(out)
# attach attributes
a98=m98.set_index('unit_id_1998'); a17=t17.set_index('unit_id_2017')
cw['province_1998']=cw.unit_id_1998.map(a98.province_1998); cw['district_1998']=cw.unit_id_1998.map(a98.district_1998)
cw['unit_1998']=cw.unit_id_1998.map(a98.unit_1998); cw['unit_type_1998']=cw.unit_id_1998.map(a98.unit_type_1998); cw['pop_1998']=cw.unit_id_1998.map(a98.pop_1998).astype(int)
cw['province_2017']=cw.unit_id_2017.map(a17.province_area); cw['district_2017']=cw.unit_id_2017.map(a17.district)
cw['unit_2017']=cw.unit_id_2017.map(a17.unit); cw['unit_type_2017']=cw.unit_id_2017.map(a17.unit_type)
cw['pop_1998_restated_2017']=cw.unit_id_2017.map(a17.pop_1998_restated).astype(int); cw['pop_2017']=cw.unit_id_2017.map(a17.pop_2017).astype(int)
cw['pop_weight']=cw.flow_1998/cw.pop_1998
cw['weight_basis']=np.where(cw.note.str.startswith('same name')|(cw.method=='one_to_one'),'pbs_restatement_exact','pbs_restatement+milp_adjacency')
cw.loc[cw.unit_type_1998=='district_collapsed','note']=cw.loc[cw.unit_type_1998=='district_collapsed','note'].fillna('')+' 1998 side is the whole district (1951-98 report lists post-2001 towns, not 1998 tehsils)'
cols=['district_group','unit_id_1998','province_1998','district_1998','unit_1998','unit_type_1998','pop_1998','unit_id_2017','province_2017','district_2017','unit_2017','unit_type_2017','pop_1998_restated_2017','pop_2017','flow_1998','pop_weight','weight_basis','method','confidence','note']
cw=cw[cols].sort_values(['unit_id_1998','unit_id_2017']).reset_index(drop=True)
cw.to_csv(INT+'crosswalk_tehsil_1998_to_2017_pop.csv',index=False)
m98.to_csv(INT+'unit_master_1998_solved_frame.csv',index=False)
json.dump(log,open(INT+'unbalanced_groups_1998.json','w'),indent=1)
pd.DataFrame(dlog).to_csv(INT+'district_level_solve_log.csv',index=False)
dfl=cw.groupby(['district_group','district_1998','district_2017'],as_index=False).agg(flow_1998=('flow_1998','sum'),rows=('flow_1998','size'),confidence=('confidence',lambda c:'medium' if (c=='medium').any() else 'high'))
dfl.to_csv(INT+'district_flows_1998_to_2017.csv',index=False)
# checks
print('rows',len(cw),'| 1998 units covered',cw.unit_id_1998.nunique(),'of',len(m98),'| 2017 units covered',cw.unit_id_2017.nunique(),'of',len(t17))
s=cw.groupby('unit_id_1998').pop_weight.sum(); print('weights sum to 1:',np.allclose(s,1))
r=cw.groupby('unit_id_2017').flow_1998.sum(); print('inflows equal restated 1998:',(r==a17.pop_1998_restated.loc[r.index].astype(int)).all())
print(cw.method.value_counts()); print(cw.confidence.value_counts())
print('split 1998 units:',(cw.groupby('unit_id_1998').size()>1).sum())
