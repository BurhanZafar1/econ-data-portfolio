"""Build the 2017 -> 2023 tehsil crosswalk (four provinces) with population weights.
Sources: PBS Census 2017 Table 1 (population 2017 by tehsil) and PBS Census 2023 Table 1
(population 2017 restated on 2023 tehsils), via Data Darbar's parsed panels; grouping of
units into territory-covering groups from Data Darbar's subdistrict_crosswalk_2017_2023,
re-verified here. Within restructured groups the correspondence is resolved by exact
population balancing; boundary transfers between two same-named units by the minimal
one-way transfer. Every row carries weight_basis, confidence and a note."""
import pandas as pd, numpy as np, itertools, re, json
OUT='output/'
PROV17={'PUNJAB','SINDH','KHYBER PAKHTUNKHWA','BALOCHISTAN','FATA'}
PROV23={'PUNJAB','SINDH','KHYBER PAKHTUNKHWA','BALOCHISTAN'}
m17=pd.read_csv(OUT+'unit_master_2017_all.csv'); m23=pd.read_csv(OUT+'unit_master_2023_all.csv')
m17=m17[(m17.unit_type!='district')&(m17.province_area.isin(PROV17))].copy()
m23=m23[(m23.unit_type!='district')&(m23.province_area.isin(PROV23))].copy()
m17['province_2023']=m17.province_area.replace({'FATA':'KHYBER PAKHTUNKHWA'})
# unit ids
m17['unit_id_2017']=['T17-'+f'{i:04d}' for i in range(1,len(m17)+1)]
m23['unit_id_2023']=m23.dds_id
assert m23.dds_id.notna().all() and m23.dds_id.is_unique
k17=m17.set_index(['district','unit']); k23=m23.set_index(['district','unit'])
assert k17.index.is_unique and k23.index.is_unique
S=pd.read_parquet('raw/subdistrict_crosswalk_2017_2023.parquet')
def base(n):  # strip tier words for name matching
    n=n.upper()
    for w in ['SUB-DIVISION','SUB DIVISION','SUB-TEHSIL','SUB TEHSIL','TEHSIL','TALUKA','F.R','FR ','SUB-','DISTRICT']: n=n.replace(w,' ')
    return re.sub(r'[^A-Z0-9]+',' ',n).strip()
rows=[]
def add(u17,u23,w,basis,conf,note,group):
    r17=k17.loc[u17]; r23=k23.loc[u23]
    rows.append(dict(district_group=group,unit_id_2017=r17.unit_id_2017,province_2017=r17.province_area,district_2017=u17[0],unit_2017=u17[1],unit_type_2017=r17.unit_type,pop_2017=int(r17.pop_2017),
        unit_id_2023=r23.unit_id_2023,province_2023=r23.province_area,district_2023=u23[0],unit_2023=u23[1],unit_type_2023=r23.unit_type,pop_2017_restated_2023=int(r23.pop_2017_restated),pop_2023=int(r23.pop_2023),
        pop_weight=w,weight_basis=basis,confidence=conf,note=note))
def find(units, district_names, k):
    """resolve 'A + B' lists to (district, unit) keys, searching the districts named in the group"""
    out=[]
    for u in [x.strip() for x in units.split(' + ')]:
        cands=[(d,u) for d in district_names if (d,u) in k.index]
        if len(cands)!=1: raise KeyError((u,district_names,cands))
        out.append(cands[0])
    return out
unresolved=[]
for _,g in S.iterrows():
    if 'ISLAMABAD' in g.district_group: continue
    dn=[x.strip() for x in g.district_group.split(' + ')]
    # districts may be renamed between frames (agency->district); build candidate district lists
    d17=[d for d in dn if d in m17.district.values]; d23=[d for d in dn if d in m23.district.values]
    for d in dn:
        if d.endswith(' AGENCY'): d23.append(d.replace(' AGENCY',' DISTRICT'))
        if d.startswith('FR '): pass
    # 2023 districts that absorbed FRs / splits: look up by the 2023 district(s) of matching units
    d23=sorted(set(d23)|set(m23[m23.district.isin(d23)].district))
    if g.relation in ('exact','renamed'):
        u17=find(g.units_2017,d17,k17)[0]; 
        # 2023 district may differ (e.g. Karachi West -> Keamari, Chitral -> Lower/Upper Chitral)
        c=[(d,u) for (d,u) in k23.index if u==g.units_2023 and (d in d23 or d==g.district_2023)]
        if len(c)!=1: c=[(d,u) for (d,u) in k23.index if u==g.units_2023 and d==g.district_2023]
        assert len(c)==1,(g.units_2023,c)
        u23=c[0]
        p17=int(k17.loc[u17].pop_2017); p23=int(k23.loc[u23].pop_2017_restated)
        assert p17==p23, (u17,u23,p17,p23)
        note='same name' if g.relation=='exact' else f'renamed; matched by {g.matched_by}'
        add(u17,u23,1.0,'pbs_restatement',"high",note,g.district_group)
        continue
    # restructured group
    U17=[x.strip() for x in g.units_2017.split(' + ')]; U23=[x.strip() for x in g.units_2023.split(' + ')]
    K17=[]; 
    for u in U17:
        c=[(d,uu) for (d,uu) in k17.index if uu==u and d in d17]; assert len(c)==1,(u,d17,c); K17.append(c[0])
    K23=[]
    for u in U23:
        c=[(d,uu) for (d,uu) in k23.index if uu==u and (d in d23 or any(d.startswith(x.replace(' DISTRICT','')) for x in dn))]
        if len(c)!=1: c=[(d,uu) for (d,uu) in k23.index if uu==u]
        assert len(c)==1,(u,d23,c); K23.append(c[0])
    P17=np.array([k17.loc[x].pop_2017 for x in K17],dtype=np.int64); P23=np.array([k23.loc[x].pop_2017_restated for x in K23],dtype=np.int64)
    assert P17.sum()==P23.sum(), (g.district_group,P17.sum(),P23.sum())
    m,n=len(K17),len(K23)
    # enumerate assignments of each 2023 unit to one 2017 parent that balance exactly
    sols=[]
    for asg in itertools.product(range(m),repeat=n):
        sums=np.zeros(m,dtype=np.int64)
        for j,i in enumerate(asg): sums[i]+=P23[j]
        if (sums==P17).all(): sols.append(asg)
    def namescore(asg): return sum(1 for j,i in enumerate(asg) if base(K23[j][1])==base(K17[i][1]))
    if sols:
        best=max(namescore(a) for a in sols); sols2=[a for a in sols if namescore(a)==best]
        asg=sols2[0]
        conf='high' if len(sols2)==1 else 'medium'
        for j,i in enumerate(asg):
            w=P23[j]/P17[i]
            note=('unchanged' if w==1 and base(K23[j][1])==base(K17[i][1]) else f'split of {K17[i][1]}: 2023 unit holds {P23[j]:,} of its {P17[i]:,} (PBS restatement)')
            if len(sols2)>1: note+=f'; {len(sols2)} balancing assignments, chose best name match'
            add(K17[i],K23[j],float(w),'pbs_restatement',conf,note,g.district_group)
        continue
    # no exact partition: boundary transfer. Seed by same base name, then one-way transfers from donors to recipients.
    seed={}
    for j,u23 in enumerate(K23):
        for i,u17 in enumerate(K17):
            if base(u23[1])==base(u17[1]): seed[j]=i
    assigned=np.zeros(m,dtype=np.int64)
    for j,i in seed.items(): assigned[i]+=P23[j]
    resid=P17-assigned   # positive: 2017 unit lost people; negative: 2017 unit (its named successor) gained
    unmatched=[j for j in range(n) if j not in seed]
    if unmatched or (resid>0).sum()!=1 or (resid<0).sum()!=1:
        unresolved.append(dict(group=g.district_group,units_2017=g.units_2017,units_2023=g.units_2023,pop_2017=P17.tolist(),restated=P23.tolist(),unmatched=[K23[j][1] for j in unmatched],resid=resid.tolist()))
        continue
    donor=int(np.where(resid>0)[0][0]); recip=int(np.where(resid<0)[0][0]); t=int(resid[donor])
    for j,i in seed.items():
        if i==donor:
            add(K17[i],K23[j],float(P23[j]/P17[i]),'pbs_restatement',"medium",f'boundary transfer: {t:,} persons (2017 count) moved from {K17[donor][1]} to {K23[[jj for jj,ii in seed.items() if ii==recip][0]][1]}; assumes a single one-way transfer',g.district_group)
        else:
            add(K17[i],K23[j],1.0,'pbs_restatement',"medium",f'receives {t:,} persons (2017 count) from {K17[donor][1]}; own 2017 territory kept whole; assumes a single one-way transfer',g.district_group)
    jr=[jj for jj,ii in seed.items() if ii==recip][0]
    add(K17[donor],K23[jr],float(t/P17[donor]),'pbs_restatement',"medium",f'boundary transfer: {t:,} persons (2017 count) moved from {K17[donor][1]} to {K23[jr][1]}; assumes a single one-way transfer',g.district_group)
X=pd.DataFrame(rows)
X.to_csv('build/intermediate/crosswalk_tehsil_2017_to_2023_pop.csv',index=False)
json.dump(unresolved,open('build/intermediate/unresolved_groups.json','w'),indent=1)
print(len(X),'rows;', X.confidence.value_counts().to_dict()); print('unresolved groups:',len(unresolved))
for u in unresolved: print(' ',u['group'],'|',u['units_2017'],'->',u['units_2023'],'| resid',u['resid'],'| unmatched',u['unmatched'])
# coverage
print('2017 units covered', X.unit_id_2017.nunique(),'of',len(m17),'| 2023 units covered',X.unit_id_2023.nunique(),'of',len(m23))
ws=X.groupby('unit_id_2017').pop_weight.sum(); print('weight sums off by >1e-9:', (abs(ws-1)>1e-9).sum())
