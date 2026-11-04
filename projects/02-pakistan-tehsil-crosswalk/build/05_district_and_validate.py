"""District-level crosswalk (aggregated from the tehsil flows) and validation checks."""
import pandas as pd, numpy as np, json
OUT='output/'
X=pd.read_csv(OUT+'crosswalk_tehsil_2017_to_2023.csv')
m17=pd.read_csv(OUT+'unit_master_2017_all.csv'); m23=pd.read_csv(OUT+'unit_master_2023_all.csv')
KARACHI={'KARACHI CENTRAL DISTRICT','KARACHI EAST DISTRICT','KARACHI SOUTH DISTRICT','KARACHI WEST DISTRICT','KORANGI DISTRICT','MALIR DISTRICT','KEAMARI DISTRICT'}
X['karachi_division']=X.district_2023.isin(KARACHI)
# ---- district crosswalk
d17=m17[(m17.unit_type=='district')&m17.province_area.isin(['PUNJAB','SINDH','KHYBER PAKHTUNKHWA','BALOCHISTAN','FATA'])].set_index('district')
d23=m23[(m23.unit_type=='district')&m23.province_area.isin(['PUNJAB','SINDH','KHYBER PAKHTUNKHWA','BALOCHISTAN'])].set_index('district')
f=X.assign(flow=X.flow_2017, area_flow=X.area_weight*X.unit_id_2017.map(X.groupby('unit_id_2017').area_2023_km2.first()))  # placeholder, area handled below
D=X.groupby(['province_2017','district_2017','province_2023','district_2023']).agg(flow_2017=('flow_2017','sum')).reset_index()
D['pop_2017']=D.district_2017.map(d17.pop_2017).astype(int)
D['pop_weight']=D.flow_2017/D.pop_2017
# area: attribute each tehsil row's area_ij (= area_weight * total area of the 2017 unit's attributed land) to districts
X['area_ij']=X.area_weight*X.groupby('unit_id_2017').apply(lambda g:(g.area_2023_km2*g.flow_2017/g.pop_2017_restated_2023).sum(),include_groups=False).reindex(X.unit_id_2017).values
DA=X.groupby(['district_2017','district_2023']).area_ij.sum().reset_index()
D=D.merge(DA,on=['district_2017','district_2023']); D['area_weight']=D.area_ij/D.groupby('district_2017').area_ij.transform('sum'); D=D.drop(columns='area_ij')
D['pop_2017_restated_2023']=D.district_2023.map(d23.pop_2017_restated).astype(int); D['pop_2023']=D.district_2023.map(d23.pop_2023).astype(int)
D['confidence']=D.apply(lambda r: X[(X.district_2017==r.district_2017)&(X.district_2023==r.district_2023)].confidence.map({'high':2,'medium':1}).min(),axis=1).map({2:'high',1:'medium'})
D['karachi_division']=D.district_2023.isin(KARACHI)
D['relation']=np.where(D.pop_weight==1,'whole', 'part')
D=D.sort_values(['province_2017','district_2017','district_2023'])
D.to_csv(OUT+'crosswalk_district_2017_to_2023.csv',index=False)
X=X.drop(columns='area_ij')
X.to_csv(OUT+'crosswalk_tehsil_2017_to_2023.csv',index=False)
# district-level conservation: flows into each 2023 district must equal PBS restated 2017 pop of the district
chk=D.groupby('district_2023').flow_2017.sum()
diff=(chk-d23.pop_2017_restated.reindex(chk.index)).abs()
print('district rows',len(D),'| 2017 districts',D.district_2017.nunique(),'of',len(d17),'| 2023 districts',D.district_2023.nunique(),'of',len(d23))
print('2023 districts whose inflow != PBS restated 2017 pop:', (diff>0).sum()); print(diff[diff>0])
# ---- validation report
rep={}
rep['tehsil_rows']=len(X); rep['units_2017']=int(X.unit_id_2017.nunique()); rep['units_2017_in_frame']=int((m17.unit_type!='district')[m17.province_area.isin(['PUNJAB','SINDH','KHYBER PAKHTUNKHWA','BALOCHISTAN','FATA'])].sum())
rep['units_2023']=int(X.unit_id_2023.nunique()); rep['units_2023_in_frame']=int(((m23.unit_type!='district')&m23.province_area.isin(['PUNJAB','SINDH','KHYBER PAKHTUNKHWA','BALOCHISTAN'])).sum())
rep['pop_weight_sum_max_abs_dev']=float((X.groupby('unit_id_2017').pop_weight.sum()-1).abs().max())
rep['area_weight_sum_max_abs_dev']=float((X.groupby('unit_id_2017').area_weight.sum()-1).abs().max())
inflow=X.groupby('unit_id_2023').flow_2017.sum(); target=m23.set_index('dds_id').pop_2017_restated.reindex(inflow.index)
rep['tehsil_conservation_max_abs_dev']=int((inflow-target).abs().max())
# provincial totals
prov=X.groupby('province_2023').flow_2017.sum(); provt=m23[(m23.unit_type=='district')].groupby('province_area').pop_2017_restated.sum()
rep['provincial_2017_totals']={p:dict(crosswalk=int(prov[p]),pbs_2023_table1=int(provt[p]),pbs_2017_table1=int(m17[(m17.unit_type=='district')&(m17.province_area.replace({'FATA':'KHYBER PAKHTUNKHWA'})==p)].pop_2017.sum())) for p in prov.index}
rep['confidence']=X.confidence.value_counts().to_dict(); rep['weight_basis']=X.weight_basis.value_counts().to_dict(); rep['area_basis']=X.area_basis.value_counts().to_dict()
rep['relation_counts']={'one_to_one':int((X.groupby('unit_id_2017').size()==1).sum()),'split_or_transfer_2017_units':int((X.groupby('unit_id_2017').size()>1).sum()),'2023_units_with_multiple_sources':int((X.groupby('unit_id_2023').size()>1).sum())}
json.dump(rep,open(OUT+'validation_summary.json','w'),indent=1)
print(json.dumps(rep,indent=1))
