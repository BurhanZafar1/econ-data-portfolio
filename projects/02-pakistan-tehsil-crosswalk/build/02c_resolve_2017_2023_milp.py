"""Re-solve the 2017 -> 2023 tehsil layer with the same fixed-charge transportation resolver used for
1998 -> 2017 (crosswalk_lib.solve_group), so that all layers share one documented method and one
uniqueness check. District groups are taken from the first-release build (02 + 03), which verified them
against the PBS populations; within each group the flows are re-derived here.
Adjacency prior: PBS 2023 tehsil polygons (shared boundary / perimeter, EPSG:32642).
Output: build/intermediate/crosswalk_tehsil_2017_to_2023_pop.csv (replaces the 02+03 file; the 02+03
result is kept as crosswalk_tehsil_2017_to_2023_pop_v1.csv) and a comparison printed to the console.
"""
import pandas as pd, numpy as np, geopandas as gpd, sys, os, shutil
sys.path.insert(0,'build'); from crosswalk_lib import solve_group
INT='build/intermediate/'; OUT='output/'
src=INT+'crosswalk_tehsil_2017_to_2023_pop.csv'; v1=INT+'crosswalk_tehsil_2017_to_2023_pop_v1.csv'
if not os.path.exists(v1): shutil.copy(src,v1)
V=pd.read_csv(v1)
g23=gpd.read_file('raw/pbs_tehsils_2023.geojson').to_crs(32642); g23['geometry']=g23.geometry.buffer(0); g23=g23.set_index('dds_id')
def adjacency(a,b):
    if a not in g23.index or b not in g23.index: return 0.0
    ga,gb=g23.geometry[a],g23.geometry[b]; per=gb.boundary.length
    return ga.boundary.intersection(gb.boundary).length/per if per>0 else 0.0
out=[]
for grp,G in V.groupby('district_group'):
    old=G.drop_duplicates('unit_id_2017')[['unit_id_2017','unit_2017','pop_2017','district_2017']].rename(columns={'unit_id_2017':'id','unit_2017':'name','pop_2017':'n','district_2017':'district'}).reset_index(drop=True)
    new=G.drop_duplicates('unit_id_2023')[['unit_id_2023','unit_2023','pop_2017_restated_2023','district_2023']].rename(columns={'unit_id_2023':'id','unit_2023':'name','pop_2017_restated_2023':'n','district_2023':'district'}).reset_index(drop=True)
    old['n']=old['n'].astype(int); new['n']=new['n'].astype(int)
    dflows={}
    if old.district.nunique()>1 or new.district.nunique()>1:
        dold=old.groupby('district',as_index=False)['n'].sum().assign(id=lambda d:d.district,name=lambda d:d.district)
        dnew=new.groupby('district',as_index=False)['n'].sum().assign(id=lambda d:d.district,name=lambda d:d.district)
        drows,dconf=solve_group(dold,dnew,None,grp+' [district level]')
        if dconf in ('high','medium'): dflows={(a,b):f for a,b,f,_,_,_ in drows}
    rows,conf=solve_group(old,new,adjacency,grp,district_flows=dflows)
    for oid,nid,flow,method,rconf,note in rows:
        out.append(dict(district_group=grp,unit_id_2017=oid,unit_id_2023=nid,flow_2017=flow,method=method,confidence=rconf,note=note))
N=pd.DataFrame(out)
a17=V.drop_duplicates('unit_id_2017').set_index('unit_id_2017'); a23=V.drop_duplicates('unit_id_2023').set_index('unit_id_2023')
for c in ['province_2017','district_2017','unit_2017','unit_type_2017','pop_2017']: N[c]=N.unit_id_2017.map(a17[c])
for c in ['province_2023','district_2023','unit_2023','unit_type_2023','pop_2017_restated_2023','pop_2023']: N[c]=N.unit_id_2023.map(a23[c])
N['pop_weight']=N.flow_2017/N.pop_2017
N['weight_basis']=np.where(N.note.str.startswith('same name')|(N.method=='one_to_one'),'pbs_restatement_exact','pbs_restatement+milp_adjacency')
cols=['district_group','unit_id_2017','province_2017','district_2017','unit_2017','unit_type_2017','pop_2017','unit_id_2023','province_2023','district_2023','unit_2023','unit_type_2023','pop_2017_restated_2023','pop_2023','flow_2017','pop_weight','weight_basis','method','confidence','note']
N=N[cols].sort_values(['unit_id_2017','unit_id_2023']).reset_index(drop=True)
# checks and comparison with v1
assert N.unit_id_2017.nunique()==V.unit_id_2017.nunique() and N.unit_id_2023.nunique()==V.unit_id_2023.nunique()
assert np.allclose(N.groupby('unit_id_2017').pop_weight.sum(),1)
_s=N.groupby('unit_id_2023').flow_2017.sum(); assert (_s==a23.pop_2017_restated_2023.reindex(_s.index).astype(int)).all()
V['flow_2017']=(V.pop_weight*V.pop_2017).round().astype(int)
cmp=N.merge(V[['unit_id_2017','unit_id_2023','flow_2017','confidence']],on=['unit_id_2017','unit_id_2023'],how='outer',suffixes=('','_v1'),indicator=True)
print('rows v1',len(V),'| rows new',len(N),'| pairs in both',(cmp._merge=='both').sum(),'| only new',(cmp._merge=='left_only').sum(),'| only v1',(cmp._merge=='right_only').sum())
both=cmp[cmp._merge=='both']; print('pairs in both with identical flow:',(both.flow_2017==both.flow_2017_v1).sum(),'| persons re-allocated vs v1: %d of %d'%(int((cmp.flow_2017.fillna(0)-cmp.flow_2017_v1.fillna(0)).abs().sum()/2),int(V.flow_2017.sum())))
print('confidence new:',N.confidence.value_counts().to_dict(),'| v1:',V.confidence.value_counts().to_dict())
diff=cmp[(cmp._merge!='both')|(cmp.flow_2017!=cmp.flow_2017_v1)]
print(diff.groupby('district_group').size().to_string() if 'district_group' in diff else '')
N.to_csv(src,index=False)
diff.to_csv(INT+'compare_2017_2023_v1_vs_milp.csv',index=False)
