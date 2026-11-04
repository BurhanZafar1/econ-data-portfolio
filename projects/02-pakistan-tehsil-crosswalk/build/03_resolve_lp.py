"""Resolve the restructured groups that do not balance exactly: a transportation LP
moves each 2017 unit's population into 2023 units, with row sums = PBS 2017 population
and column sums = PBS's 2017 population restated on 2023 units. Costs: 0 for a same-named
pair; otherwise 1 + 4*(1 - share of the child's perimeter shared with the parent's
same-named 2023 unit), from the PBS Digital Census 2023 polygons; 6 if not adjacent.
The LP vertex is sparse (at most m+n-1 flows). All rows get confidence 'medium'."""
import pandas as pd, numpy as np, json, re, geopandas as gpd
from scipy.optimize import linprog
OUT='output/'
X=pd.read_csv('build/intermediate/crosswalk_tehsil_2017_to_2023_pop.csv')
U=json.load(open('build/intermediate/unresolved_groups.json'))
m17=pd.read_csv(OUT+'unit_master_2017_all.csv'); m23=pd.read_csv(OUT+'unit_master_2023_all.csv')
m17=m17[m17.unit_type!='district'].copy(); m23=m23[m23.unit_type!='district'].copy()
m17['unit_id_2017']=['T17-'+f'{i:04d}' for i in range(1,len(m17[m17.province_area.isin({'PUNJAB','SINDH','KHYBER PAKHTUNKHWA','BALOCHISTAN','FATA'})])+1)]+[None]*len(m17[~m17.province_area.isin({'PUNJAB','SINDH','KHYBER PAKHTUNKHWA','BALOCHISTAN','FATA'})])
# the id assignment above must match 02; rebuild identically:
m17=pd.read_csv(OUT+'unit_master_2017_all.csv'); m17=m17[(m17.unit_type!='district')&(m17.province_area.isin({'PUNJAB','SINDH','KHYBER PAKHTUNKHWA','BALOCHISTAN','FATA'}))].copy()
m17['unit_id_2017']=['T17-'+f'{i:04d}' for i in range(1,len(m17)+1)]
poly=gpd.read_file('raw/pbs_tehsils_2023.geojson').to_crs(32642); poly['geometry']=poly.geometry.buffer(0)
poly=poly.set_index('dds_id')
def base(n):
    n=n.upper()
    for w in ['SUB-DIVISION','SUB DIVISION','SUB-TEHSIL','SUB TEHSIL','TEHSIL','TALUKA','F.R','FR ','SUB-','DISTRICT']: n=n.replace(w,' ')
    return set(re.sub(r'[^A-Z0-9]+',' ',n).split())
def namematch(a,b):
    A,B=base(a),base(b); return bool(A) and bool(B) and (A<=B or B<=A)
rows=[]
for u in U:
    dn=[x.strip() for x in u['group'].split(' + ')]
    U17=u['units_2017'].split(' + '); U23=u['units_2023'].split(' + ')
    R17=[m17[(m17.unit==x)&(m17.district.isin(dn))].iloc[0] for x in U17]
    def find23(x):
        c=m23[(m23.unit==x)&(m23.district.isin(dn))]
        if len(c)!=1: c=m23[(m23.unit==x)&(m23.district.str.split().str[0].isin([d.split()[0] for d in dn]))]
        if len(c)!=1:  # district split e.g. Kohistan -> Upper/Lower/Kolai Palas Kohistan
            c=m23[(m23.unit==x)&(m23.district.str.contains(dn[0].split()[0]))]
        assert len(c)==1,(x,dn,len(c)); return c.iloc[0]
    R23=[find23(x) for x in U23]
    P17=np.array([r.pop_2017 for r in R17]); P23=np.array([r.pop_2017_restated for r in R23]); assert P17.sum()==P23.sum()
    m,n=len(R17),len(R23)
    seed={}
    for j in range(n):
        c=[i for i in range(m) if namematch(R23[j].unit,R17[i].unit)]
        if len(c)==1: seed[j]=c[0]
    anchor={i:j for j,i in seed.items()}
    C=np.zeros((m,n))
    for i in range(m):
        for j in range(n):
            if seed.get(j)==i: C[i,j]=0; continue
            if i in anchor:
                ga=poly.loc[R17[i].name if False else R23[anchor[i]].dds_id].geometry; gc=poly.loc[R23[j].dds_id].geometry
                shared=ga.boundary.intersection(gc.boundary).length; per=gc.boundary.length
                C[i,j]=1+4*(1-shared/per) if shared>0 else 6
            else: C[i,j]=3
    A_eq=[]; b_eq=[]
    for i in range(m):
        a=np.zeros(m*n); a[i*n:(i+1)*n]=1; A_eq.append(a); b_eq.append(P17[i])
    for j in range(n):
        a=np.zeros(m*n); a[j::n]=1; A_eq.append(a); b_eq.append(P23[j])
    res=linprog(C.ravel(),A_eq=np.array(A_eq),b_eq=np.array(b_eq),bounds=(0,None),method='highs')
    assert res.success, u['group']
    F=np.round(res.x.reshape(m,n)).astype(np.int64)
    assert (F.sum(1)==P17).all() and (F.sum(0)==P23).all()
    for i in range(m):
        for j in range(n):
            if F[i,j]<=0: continue
            w=F[i,j]/P17[i]
            if seed.get(j)==i and F[i,j]==P23[j] and F[i,j]==P17[i]: note='unchanged'
            elif seed.get(j)==i: note=f'same-named successor keeps {F[i,j]:,} of {P17[i]:,} (2017 count)'
            else: note=f'{F[i,j]:,} persons (2017 count) of {R17[i].unit} allocated to {R23[j].unit}; adjacency cost {C[i,j]:.2f}'
            note+='; group does not balance by name alone, resolved by transportation LP with 2023-polygon adjacency prior'
            rows.append(dict(district_group=u['group'],unit_id_2017=R17[i].unit_id_2017,province_2017=R17[i].province_area,district_2017=R17[i].district,unit_2017=R17[i].unit,unit_type_2017=R17[i].unit_type,pop_2017=int(P17[i]),
                unit_id_2023=R23[j].dds_id,province_2023=R23[j].province_area,district_2023=R23[j].district,unit_2023=R23[j].unit,unit_type_2023=R23[j].unit_type,pop_2017_restated_2023=int(P23[j]),pop_2023=int(R23[j].pop_2023),
                pop_weight=float(w),weight_basis='pbs_restatement+lp_adjacency',confidence='medium',note=note))
    print(f"\n## {u['group']}"); 
    for r in rows:
        if r['district_group']==u['group']: print(f"  {r['unit_2017']:28s} -> {r['unit_2023']:28s} w={r['pop_weight']:.4f}  {r['note'][:70]}")
Y=pd.concat([X,pd.DataFrame(rows)],ignore_index=True)
Y.to_csv('build/intermediate/crosswalk_tehsil_2017_to_2023_pop.csv',index=False)
print('\nTOTAL rows',len(Y), Y.confidence.value_counts().to_dict(), '| 2017 units',Y.unit_id_2017.nunique(),'of',len(m17),'| 2023 units',Y.unit_id_2023.nunique(),'of',(m23.province_area!='ISLAMABAD').sum())
ws=Y.groupby('unit_id_2017').pop_weight.sum(); print('weight sums off:', (abs(ws-1)>1e-9).sum())
