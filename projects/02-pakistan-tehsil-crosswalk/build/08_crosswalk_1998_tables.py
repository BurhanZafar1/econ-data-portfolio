"""1998 layer, final tables.
 a) crosswalk_tehsil_1998_to_2017.csv : population flows from build/07 plus area weights from PBS's
    published 2017 areas (Census 2017 Table 1): area_ij = area_2017_j * F_ij / P98_j (uniform density
    inside the 2017 unit; exact where a 2017 unit has a single 1998 source).
 b) crosswalk_tehsil_1998_to_2023.csv : chained through the 2017 frame.
       flow_1998(i->k) = sum_j F_ij * pop_weight_2017to2023(j->k)
       area(i->k)      = sum_j area_ij * area_weight_2017to2023(j->k)
 c) district tables for both, aggregated from the tehsil flows.
 d) validation_summary_1998.json
"""
import pandas as pd, numpy as np, json
OUT='output/'; INT='build/intermediate/'
PROV={'PUNJAB','SINDH','BALOCHISTAN','KHYBER PAKHTUNKHWA','FATA'}
KARACHI={'KARACHI CENTRAL DISTRICT','KARACHI EAST DISTRICT','KARACHI SOUTH DISTRICT','KARACHI WEST DISTRICT','KORANGI DISTRICT','MALIR DISTRICT','KEAMARI DISTRICT','KARACHI CITY DISTRICT'}
X=pd.read_csv(INT+'crosswalk_tehsil_1998_to_2017_pop.csv')
m98=pd.read_csv(INT+'unit_master_1998_solved_frame.csv').set_index('unit_id_1998')
m17=pd.read_csv(OUT+'unit_master_2017_all.csv'); t17=m17[(m17.unit_type!='district')&m17.province_area.isin(PROV)].copy()
t17['unit_id_2017']=['T17-'+f'{i:04d}' for i in range(1,len(t17)+1)]; t17=t17.set_index('unit_id_2017')
Y=pd.read_csv(OUT+'crosswalk_tehsil_2017_to_2023.csv')

# ---- a) area weights 1998 -> 2017
X['area_2017_km2']=X.unit_id_2017.map(t17.area_km2)
# PBS 2017 Table 1 prints no sub-district areas for Kohistan and Killa Saifullah; use the area implied by the
# 2023 tables through the 2017->2023 crosswalk (sum of area_2023_k * flow_jk / P_k) and flag it
imp=(Y.area_2023_km2*Y.flow_2017/Y.pop_2017_restated_2023).groupby(Y.unit_id_2017).sum()
X['area_2017_source']=np.where(X.area_2017_km2.notna(),'pbs_2017_table1','implied_from_pbs_2023_areas')
X['area_2017_km2']=X.area_2017_km2.fillna(X.unit_id_2017.map(imp))
assert X.area_2017_km2.notna().all()
X['area_ij']=X.area_2017_km2*X.flow_1998/X.pop_1998_restated_2017
X['area_weight']=X.area_ij/X.groupby('unit_id_1998').area_ij.transform('sum')
nsrc=X.groupby('unit_id_2017').unit_id_1998.transform('nunique')
X['area_basis']=np.where(X.groupby('unit_id_1998').unit_id_1998.transform('size')==1,'identity',np.where(nsrc==1,'pbs_area_2017_exact','pbs_area_2017_uniform_density'))
X.loc[(X.area_2017_source!='pbs_2017_table1')&(X.area_basis!='identity'),'area_basis']='implied_2017_area_uniform_density'
X['area_1998_pco_km2']=X.unit_id_1998.map(m98.area_km2)          # PCO 1951-98 report, check column only
X['area_1998_implied_km2']=X.groupby('unit_id_1998').area_ij.transform('sum')
X['frame_note_1998']=X.unit_id_1998.map(m98.frame_note).fillna('')
X['karachi_division']=X.district_2017.isin(KARACHI)|X.district_1998.isin(KARACHI)
A=X.drop(columns=['area_ij']).sort_values(['unit_id_1998','unit_id_2017']).reset_index(drop=True)
A.to_csv(OUT+'crosswalk_tehsil_1998_to_2017.csv',index=False)
print('1998->2017 rows',len(A),'| area basis',A.area_basis.value_counts().to_dict())
r=A.drop_duplicates('unit_id_1998'); ok=r.area_1998_pco_km2.notna()&(r.area_1998_pco_km2>0)
print('implied 1998 area vs PCO 1998 area: median ratio %.3f, within 10%% for %d of %d units with a PCO area'%((r.area_1998_implied_km2/r.area_1998_pco_km2)[ok].median(),((r.area_1998_implied_km2/r.area_1998_pco_km2)[ok].between(0.9,1.1)).sum(),ok.sum()))

# ---- b) chain 1998 -> 2017 -> 2023
Yk=Y[['unit_id_2017','unit_id_2023','province_2023','district_2023','unit_2023','unit_type_2023','pop_2023','pop_weight','area_weight','confidence','area_2023_km2']].rename(columns={'pop_weight':'pw23','area_weight':'aw23','confidence':'conf23'})
Z=X.merge(Yk,on='unit_id_2017',how='left'); assert Z.unit_id_2023.notna().all()
Z['flow_1998_k']=Z.flow_1998*Z.pw23; Z['area_k']=Z.area_ij*Z.aw23
Z['conf']=np.minimum(Z.confidence.map({'high':2,'medium':1}),Z.conf23.map({'high':2,'medium':1}))
g=Z.groupby(['unit_id_1998','unit_id_2023'],as_index=False).agg(flow_1998=('flow_1998_k','sum'),area_ik=('area_k','sum'),conf=('conf','min'),
    via_2017=('unit_2017',lambda s:'; '.join(sorted(set(s)))),province_2023=('province_2023','first'),district_2023=('district_2023','first'),unit_2023=('unit_2023','first'),unit_type_2023=('unit_type_2023','first'),pop_2023=('pop_2023','first'))
for c in ['province_1998','district_1998','unit_1998','unit_type_1998','pop_1998']: g[c]=g.unit_id_1998.map(X.drop_duplicates('unit_id_1998').set_index('unit_id_1998')[c])
g['pop_weight']=g.flow_1998/g.pop_1998
g['area_weight']=g.area_ik/g.groupby('unit_id_1998').area_ik.transform('sum')
g['confidence']=g.conf.map({2:'high',1:'medium'})
g['weight_basis']='chained: 1998->2017 PBS restatement x 2017->2023 PBS restatement'
g['frame_note_1998']=g.unit_id_1998.map(m98.frame_note).fillna('')
g['karachi_division']=g.district_2023.isin(KARACHI)|g.district_1998.isin(KARACHI)
C=g[['unit_id_1998','province_1998','district_1998','unit_1998','unit_type_1998','pop_1998','unit_id_2023','province_2023','district_2023','unit_2023','unit_type_2023','pop_2023','flow_1998','pop_weight','area_weight','via_2017','weight_basis','confidence','frame_note_1998','karachi_division']]
C=C.sort_values(['unit_id_1998','unit_id_2023']).reset_index(drop=True)
C['flow_1998']=C.flow_1998.round(2)
C.to_csv(OUT+'crosswalk_tehsil_1998_to_2023.csv',index=False)
print('1998->2023 rows',len(C),'| 1998 units',C.unit_id_1998.nunique(),'| 2023 units reached',C.unit_id_2023.nunique(),'of',Y.unit_id_2023.nunique())

# ---- c) district tables
def district_table(T,yr_new,pop_new_col,area_src):
    key=['province_1998','district_1998',f'province_{yr_new}',f'district_{yr_new}']
    D=T.groupby(key,as_index=False).agg(flow_1998=('flow_1998','sum'),area=(area_src,'sum'),conf=('confidence',lambda c:'medium' if (c=='medium').any() else 'high'),n_tehsil_rows=('flow_1998','size'))
    D['pop_1998']=D.district_1998.map(T.groupby('district_1998').pop_1998.apply(lambda s:s.groupby(level=0).first().sum()) if False else T.drop_duplicates('unit_id_1998').groupby('district_1998').pop_1998.sum())
    D['pop_weight']=D.flow_1998/D.pop_1998
    D['area_weight']=D.area/D.groupby('district_1998').area.transform('sum')
    D['relation']=np.where(np.isclose(D.pop_weight,1),'whole','part')
    D['karachi_division']=D[f'district_{yr_new}'].isin(KARACHI)|D.district_1998.isin(KARACHI)
    D=D.rename(columns={'conf':'confidence'}).drop(columns='area')
    return D.sort_values(['province_1998','district_1998',f'district_{yr_new}']).reset_index(drop=True)
D17=district_table(X,'2017','pop_2017','area_ij')
d17=m17[(m17.unit_type=='district')&m17.province_area.isin(PROV)].set_index('district')
D17['pop_1998_restated_2017']=D17.district_2017.map(d17.pop_1998_restated).astype(int); D17['pop_2017']=D17.district_2017.map(d17.pop_2017).astype(int)
D17.to_csv(OUT+'crosswalk_district_1998_to_2017.csv',index=False)
chk=D17.groupby('district_2017').flow_1998.sum()-d17.pop_1998_restated.reindex(D17.district_2017.unique())
print('district 1998->2017 rows',len(D17),'| inflow vs PBS restated 1998 by 2017 district, max abs dev:',int(chk.abs().max()))
D23=district_table(g.rename(columns={'area_ik':'area_ij'}),'2023','pop_2023','area_ij')
m23=pd.read_csv(OUT+'unit_master_2023_all.csv'); d23=m23[m23.unit_type=='district'].set_index('district')
D23['pop_2023']=D23.district_2023.map(d23.pop_2023).astype(int); D23['flow_1998']=D23.flow_1998.round(2)
D23.to_csv(OUT+'crosswalk_district_1998_to_2023.csv',index=False)
print('district 1998->2023 rows',len(D23))

# ---- d) validation
rep={}
rep['tehsil_1998_to_2017']=dict(rows=len(A),units_1998=int(A.unit_id_1998.nunique()),units_1998_in_frame=len(m98),units_2017=int(A.unit_id_2017.nunique()),units_2017_in_frame=len(t17),
    pop_weight_sum_max_abs_dev=float((A.groupby('unit_id_1998').pop_weight.sum()-1).abs().max()),area_weight_sum_max_abs_dev=float((A.groupby('unit_id_1998').area_weight.sum()-1).abs().max()),
    tehsil_conservation_max_abs_dev=int((A.groupby('unit_id_2017').flow_1998.sum()-t17.pop_1998_restated.reindex(A.unit_id_2017.unique())).abs().max()),
    confidence=A.confidence.value_counts().to_dict(),method=A.method.value_counts().to_dict(),area_basis=A.area_basis.value_counts().to_dict(),
    split_1998_units=int((A.groupby('unit_id_1998').size()>1).sum()),units_2017_with_multiple_sources=int((A.groupby('unit_id_2017').size()>1).sum()),
    collapsed_1998_districts=sorted(m98[m98.unit_type_1998=='district_collapsed'].district_1998.tolist()))
prov=A.groupby('province_2017').flow_1998.sum()
rep['provincial_1998_totals']={p:dict(crosswalk=int(prov[p]),pbs_2017_table1_restated=int(d17[d17.province_area==p].pop_1998_restated.sum()),pco_1998_report=int(m98[m98.province_1998==p].pop_1998.sum())) for p in prov.index}
rep['tehsil_1998_to_2023']=dict(rows=len(C),units_1998=int(C.unit_id_1998.nunique()),units_2023=int(C.unit_id_2023.nunique()),
    pop_weight_sum_max_abs_dev=float((C.groupby('unit_id_1998').pop_weight.sum()-1).abs().max()),area_weight_sum_max_abs_dev=float((C.groupby('unit_id_1998').area_weight.sum()-1).abs().max()),
    total_1998_persons_in=float(C.flow_1998.sum()),total_1998_persons_pco=int(m98.pop_1998.sum()),confidence=C.confidence.value_counts().to_dict(),split_1998_units=int((C.groupby('unit_id_1998').size()>1).sum()))
rep['district_1998_to_2017']=dict(rows=len(D17),districts_1998=int(D17.district_1998.nunique()),districts_2017=int(D17.district_2017.nunique()),inflow_vs_pbs_max_abs_dev=int(chk.abs().max()))
rep['district_1998_to_2023']=dict(rows=len(D23),districts_1998=int(D23.district_1998.nunique()),districts_2023=int(D23.district_2023.nunique()))
json.dump(rep,open(OUT+'validation_summary_1998.json','w'),indent=1)
print(json.dumps(rep,indent=1))
