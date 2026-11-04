"""Tehsil -> district lineage (Prof. Khan's request: "if Tehsil A from 1998 became District A in 2020,
I would like this crosswalk").

 a) tehsil_district_membership.csv : one row per (earlier tehsil, later district) with the share of the
    tehsil's population that lies in that district, for 1998->2017, 2017->2023 and 1998->2023.
 b) new_district_lineage.csv : for every district that is new in a later census frame, the earlier
    tehsils that formed it, their shares, and whether a same-named tehsil was upgraded.
 c) event years and sources are joined from the event register (build/10) when it exists.
"""
import pandas as pd, numpy as np, re, sys, os
sys.path.insert(0,'build'); from crosswalk_lib import namematch, base
OUT='output/'
def dkey(s):
    s=str(s).upper()
    for a,b in [('D.G.KHAN','DERA GHAZI KHAN'),('D.I.KHAN','DERA ISMAIL KHAN'),('NAWAB SHAH','SHAHEED BENAZIRABAD'),('BOLAN','KACHHI'),('JAFARABAD','JAFFARABAD'),('MALAKAND PROTECTED AREA','MALAKAND'),('LAHORE CITY','LAHORE')]: s=s.replace(a,b)
    return re.sub(r' (DISTRICT|AGENCY)$','',s).strip()

def membership(X,f0,f1,flowcol):
    k=[f'unit_id_{f0}',f'province_{f0}',f'district_{f0}',f'unit_{f0}',f'unit_type_{f0}',f'pop_{f0}',f'province_{f1}',f'district_{f1}']
    M=X.groupby(k,as_index=False).agg(persons=(flowcol,'sum'),confidence=('confidence',lambda c:'medium' if (c=='medium').any() else 'high'))
    M['share_of_tehsil']=M.persons/M[f'pop_{f0}']
    M['district_changed']=M[f'district_{f0}'].map(dkey)!=M[f'district_{f1}'].map(dkey)
    M['tehsil_name_matches_new_district']=[bool(namematch(u,d) and ch and t!='district_collapsed') for u,d,ch,t in zip(M[f'unit_{f0}'],M[f'district_{f1}'],M.district_changed,M[f'unit_type_{f0}'])]
    M=M.rename(columns={f'unit_id_{f0}':'unit_id',f'province_{f0}':'province_from',f'district_{f0}':'district_from',f'unit_{f0}':'unit_name',f'unit_type_{f0}':'unit_type',f'pop_{f0}':'pop_from',f'province_{f1}':'province_to',f'district_{f1}':'district_to'})
    M.insert(0,'frame_to',f1); M.insert(0,'frame_from',f0)
    return M
A=pd.read_csv(OUT+'crosswalk_tehsil_1998_to_2017.csv'); Y=pd.read_csv(OUT+'crosswalk_tehsil_2017_to_2023.csv'); C=pd.read_csv(OUT+'crosswalk_tehsil_1998_to_2023.csv')
M=pd.concat([membership(A,'1998','2017','flow_1998'),membership(Y,'2017','2023','flow_2017'),membership(C,'1998','2023','flow_1998')],ignore_index=True)
M['persons']=M.persons.round(2)
M.to_csv(OUT+'tehsil_district_membership.csv',index=False)

# new districts and their lineage
rows=[]
for X,f0,f1,flow in [(A,'1998','2017','flow_1998'),(Y,'2017','2023','flow_2017')]:
    old_d={dkey(d) for d in X[f'district_{f0}'].unique()}
    for d,g in X.groupby(f'district_{f1}'):
        if dkey(d) in old_d: continue
        tot=g[flow].sum()
        parents=sorted(set(g[f'district_{f0}']))
        for (u,uid,pd_),gg in g.groupby([f'unit_{f0}',f'unit_id_{f0}',f'district_{f0}']):
            rows.append(dict(new_district=d,province=g[f'province_{f1}'].iloc[0],frame_first_seen=f1,interval=f'{f0}-{f1}',parent_districts='; '.join(parents),
                source_tehsil=u,source_tehsil_id=uid,source_tehsil_district=pd_,persons_from_tehsil=round(gg[flow].sum(),2),share_of_new_district=round(gg[flow].sum()/tot,6),
                share_of_source_tehsil=round(gg[flow].sum()/gg[f'pop_{f0}'].iloc[0],6),tehsil_upgraded=('not applicable (1998 side is the whole district)' if gg[f'unit_type_{f0}'].iloc[0]=='district_collapsed' else 'yes' if namematch(u,d) else 'no'),
                confidence=('medium' if (gg.confidence=='medium').any() else 'high')))
L=pd.DataFrame(rows)
# join event register when present
ev=OUT+'event_register.csv'
if os.path.exists(ev):
    E=pd.read_csv(ev); E=E[(E.level=='district')&E.event_type.isin(['new_district','tehsil_upgraded_to_district'])]
    E['k']=E.unit_name.map(dkey); E=E.drop_duplicates('k').set_index('k')
    L['k']=L.new_district.map(dkey)
    for c,src in [('event_year','year'),('event_date','date'),('event_source_url','source_url'),('event_confidence','confidence')]: L[c]=L.k.map(E[src])
    L=L.drop(columns='k')
L=L.sort_values(['province','frame_first_seen','new_district','share_of_new_district'],ascending=[True,True,True,False])
L.to_csv(OUT+'new_district_lineage.csv',index=False)
print('membership rows',len(M),'| new districts',L.new_district.nunique(),'| upgraded-tehsil cases',L[L.tehsil_upgraded=='yes'].new_district.nunique())
print(L[L.tehsil_upgraded=='yes'][['new_district','source_tehsil','source_tehsil_district','share_of_new_district','interval']].to_string(index=False))
