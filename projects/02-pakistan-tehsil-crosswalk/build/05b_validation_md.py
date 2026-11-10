"""Writes docs/VALIDATION.md for the 2017 -> 2023 layer: the prose template in build/templates/VALIDATION_template.md
with every number filled from output/, plus the table of every split and transfer row."""
import pandas as pd, numpy as np, json
OUT='output/'
X=pd.read_csv(OUT+'crosswalk_tehsil_2017_to_2023.csv'); D=pd.read_csv(OUT+'crosswalk_district_2017_to_2023.csv'); V=json.load(open(OUT+'validation_summary.json'))
v1=pd.read_csv('build/intermediate/crosswalk_tehsil_2017_to_2023_pop_v1.csv')
v1['flow_v1']=(v1.pop_weight*v1.pop_2017).round().astype(int); fv='flow_v1'
M=X[['district_group','unit_id_2017','unit_id_2023','flow_2017']].merge(v1[['unit_id_2017','unit_id_2023',fv]].rename(columns={fv:'flow_v1'}),on=['unit_id_2017','unit_id_2023'],how='outer')
M['district_group']=M.district_group.fillna(M.unit_id_2017.map(v1.drop_duplicates('unit_id_2017').set_index('unit_id_2017').district_group))
outdeg=X.groupby('unit_id_2017').size(); indeg=X.groupby('unit_id_2023').size()
same=int(((M.flow_2017==M.flow_v1)&M.flow_2017.notna()&M.flow_v1.notna()).sum())
diff=M[M.flow_2017.fillna(0)!=M.flow_v1.fillna(0)]
persons=int((M.flow_2017.fillna(0)-M.flow_v1.fillna(0)).clip(lower=0).sum())
groups=sorted(set(diff.district_group.dropna().astype(str)))
nice={'ABBOTTABAD DISTRICT':'Abbottabad','DERA ISMAIL KHAN DISTRICT + FR D.I.KHAN':'D.I. Khan + FR D.I. Khan','KACHHI DISTRICT + NASIRABAD DISTRICT':'Kachhi + Nasirabad','KOHISTAN DISTRICT':'Kohistan','MARDAN DISTRICT':'Mardan','MUSAKHEL DISTRICT':'Musakhel','QUETTA DISTRICT':'Quetta','TORGHAR DISTRICT':'Torghar'}
vals=dict(n_rows=len(X),n_drows=len(D),n_one=int((outdeg==1).sum()),n_src=X.unit_id_2017.nunique(),n_split=int((outdeg>1).sum()),n_merge=int((indeg>1).sum()),
          grades=X.confidence.value_counts().to_dict(),basis=X.weight_basis.value_counts().to_dict(),n_same=same,n_v1=len(v1),persons_realloc=f'{persons:,}',pct_realloc=f'{100*persons/X.flow_2017.sum():.2f}',
          n_groups_changed={8:'eight',7:'seven',9:'nine',10:'ten',6:'six'}.get(len(groups),len(groups)),groups_changed=', '.join(nice.get(g,g.title()) for g in groups),
          n_uniform=int((X.area_basis.astype(str).str.contains('uniform')).sum()),dev_pop=f"{V['pop_weight_sum_max_abs_dev']:.1e}",dev_area=f"{V['area_weight_sum_max_abs_dev']:.1e}",today=f'{pd.Timestamp.today():%d %B %Y}')
L=[open('build/templates/VALIDATION_template.md').read().format(**vals).rstrip('\n'),'','## 9. Every split and transfer row',
   '| district_group | unit_2017 | pop_2017 | unit_2023 | pop_2017_restated_2023 | pop_weight | area_weight | method | confidence | note |','|---|---|---|---|---|---|---|---|---|---|']
for _,r in X[X.method!='one_to_one'].sort_values(['district_group','unit_2017','unit_2023']).iterrows():
    L.append(f"| {r.district_group} | {r.unit_2017} | {r.pop_2017:,} | {r.unit_2023} | {r.pop_2017_restated_2023:,} | {r.pop_weight:.4f} | {r.area_weight:.4f} | {r.method} | {r.confidence} | {r.note} |")
open('docs/VALIDATION.md','w').write('\n'.join(L)+'\n'); print('wrote docs/VALIDATION.md',vals['n_rows'],vals['grades'],vals['n_same'],vals['persons_realloc'],vals['groups_changed'])
