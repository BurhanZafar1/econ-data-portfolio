"""Constant-boundary population panel, censuses 1951 to 2023.

PCO Census Publication 161 (Population of Administrative Units 1951-98) restates the 1951, 1961, 1972
and 1981 counts on the 1998 frame, district by district and, for most units, tehsil by tehsil. So the
1998 frame already carries five censuses. This script
 a) writes that panel on the 424-unit 1998 frame used by the crosswalk (population_panel_1998_frame.csv),
    with the PCO footnote mark and a coverage flag for every cell;
 b) pushes it through the 1998 -> 2023 crosswalk to give every 2023 tehsil and district a population at
    every census since 1951 (population_panel_2023_frame.csv). For 2017 the PBS restatement on 2023
    units is used directly; 2023 is the census count.
Values before 1998 on 2023 units assume that the 1998 shares of a 1998 unit across 2023 units also held
in the earlier year; cells that rest on a 1998 unit with no PCO figure for that year are flagged partial.
"""
import pandas as pd, numpy as np
OUT='output/'; INT='build/intermediate/'
YRS=[1951,1961,1972,1981,1998]
raw=pd.read_parquet('raw/census_admin_units_1951_1998.parquet'); raw=raw[raw.locality=='all'].copy()
raw['district']=raw.district.str.upper().str.strip(); raw['unit']=raw.unit.str.upper().str.strip()
m98=pd.read_csv(INT+'unit_master_1998_solved_frame.csv')      # 424 units (three town-frame districts collapsed)
full=pd.read_csv(OUT+'unit_master_1998.csv')                   # 457 units with pop_1951..pop_1998 and mark
# ---- a) 1998-frame panel
P=m98[['unit_id_1998','province_1998','district_1998','unit_1998','unit_type_1998','pop_1998']].copy()
hist=full.set_index('unit_id_1998')[['pop_1951','pop_1961','pop_1972','pop_1981','mark']]
for y in YRS[:-1]: P[f'pop_{y}']=P.unit_id_1998.map(hist[f'pop_{y}'])
P['mark']=P.unit_id_1998.map(hist['mark'])
# collapsed districts take the PCO district row
D=raw[raw.unit_type=='district'].copy()
# the six Frontier Regions carry their name in `unit` only ("Tribal Area Adjoining Bannu District")
fr=D.unit.str.upper().str.startswith('TRIBAL AREA ADJOINING')
D.loc[fr,'district']='FR '+D.loc[fr,'unit'].str.upper().str.replace('TRIBAL AREA ADJOINING ','',regex=False).str.replace(' DISTRICT','',regex=False)
Dp=D.pivot_table(index='district',columns='census_year',values='population',aggfunc='first'); Dm=D.pivot_table(index='district',columns='census_year',values='mark',aggfunc='first')
for i,r in P[P.unit_type_1998=='district_collapsed'].iterrows():
    for y in YRS[:-1]: P.loc[i,f'pop_{y}']=Dp.loc[r.district_1998,y]
    P.loc[i,'mark']=Dm.loc[r.district_1998,1981]
for y in YRS[:-1]:
    P[f'avail_{y}']=np.where(P[f'pop_{y}'].notna(),'pco','not separately printed (inside a parent unit)')
P['note']=np.where(P.unit_type_1998=='district_collapsed','district total; the 1951-98 report lists post-2001 towns here, not 1998 tehsils','')
P['note']=np.where(P.mark.notna()&(P.mark!=''),P.note+' PCO footnote mark '+P.mark.fillna('')+' (see source PDF)',P.note)
cols=['unit_id_1998','province_1998','district_1998','unit_1998','unit_type_1998']+[f'pop_{y}' for y in YRS]+[f'avail_{y}' for y in YRS[:-1]]+['mark','note']
P=P[cols]; P.to_csv(OUT+'population_panel_1998_frame.csv',index=False)
# district-level 1998 frame panel straight from the PCO district rows
dist=pd.read_csv(OUT+'district_master_1998.csv')[['province_1998','district_1998','pop_1998']]
kmap={d:d for d in dist.district_1998}
for d in Dp.index:
    k=d.replace('TRIBAL AREA ADJOINING ','FR ').replace(' DISTRICT','')
    for dd in dist.district_1998:
        if dd==d or dd.replace(' AGENCY','')==d.replace(' AGENCY','') or dd==k: kmap[dd]=d
for y in YRS[:-1]: dist[f'pop_{y}']=[Dp.loc[kmap[d],y] if kmap[d] in Dp.index else np.nan for d in dist.district_1998]
dist['mark']=[Dm.loc[kmap[d],1951] if kmap[d] in Dm.index else '' for d in dist.district_1998]
dist=dist[['province_1998','district_1998']+[f'pop_{y}' for y in YRS]+['mark']]
dist.to_csv(OUT+'population_panel_1998_frame_districts.csv',index=False)
# coverage report
cov={y:dict(units_with_figure=int(P[f'pop_{y}'].notna().sum()),units=len(P),
            share_of_1998_population_covered=float(P.loc[P[f'pop_{y}'].notna(),'pop_1998'].sum()/P.pop_1998.sum()),
            districts_with_figure=int(dist[f'pop_{y}'].notna().sum())) for y in YRS}
# ---- b) 2023-frame panel via the 1998 -> 2023 crosswalk
C=pd.read_csv(OUT+'crosswalk_tehsil_1998_to_2023.csv')
X=C.merge(P[['unit_id_1998']+[f'pop_{y}' for y in YRS[:-1]]],on='unit_id_1998')
rows=[]
for k,g in X.groupby('unit_id_2023'):
    r=dict(unit_id_2023=k,province_2023=g.province_2023.iloc[0],district_2023=g.district_2023.iloc[0],unit_2023=g.unit_2023.iloc[0],unit_type_2023=g.unit_type_2023.iloc[0])
    for y in YRS:
        v=g[f'pop_{y}'] if y!=1998 else g.pop_1998
        w=g.pop_weight
        have=v.notna()
        r[f'pop_{y}']=float((v[have]*w[have]).sum()) if have.any() else np.nan
        r[f'flag_{y}']='complete' if have.all() else ('partial: no PCO figure for '+'; '.join(g.unit_1998[~have].unique()) if have.any() else 'no PCO figure for any source unit')
    rows.append(r)
K=pd.DataFrame(rows)
m23=pd.read_csv(OUT+'unit_master_2023_all.csv'); u23=m23[m23.unit_type!='district'].set_index('dds_id')
K['pop_2017']=K.unit_id_2023.map(u23.pop_2017_restated); K['pop_2023']=K.unit_id_2023.map(u23.pop_2023)
K['flag_2017']='PBS Census 2023 Table 1, 2017 population on 2023 boundary'; K['flag_2023']='census count'
K['method_pre_1998']='PCO 1951-98 restatement on the 1998 frame, pushed through the 1998 -> 2023 population weights (assumes the 1998 shares held in the earlier year)'
K['karachi_division']=K.district_2023.isin({'KARACHI CENTRAL DISTRICT','KARACHI EAST DISTRICT','KARACHI SOUTH DISTRICT','KARACHI WEST DISTRICT','KORANGI DISTRICT','MALIR DISTRICT','KEAMARI DISTRICT'})
for y in YRS: K[f'pop_{y}']=K[f'pop_{y}'].round(1)
K=K[['unit_id_2023','province_2023','district_2023','unit_2023','unit_type_2023']+[f'pop_{y}' for y in YRS+[2017,2023]]+[f'flag_{y}' for y in YRS+[2017,2023]]+['method_pre_1998','karachi_division']]
K.to_csv(OUT+'population_panel_2023_frame.csv',index=False)
# district level on the 2023 frame
G=K.groupby(['province_2023','district_2023'],as_index=False).agg(**{f'pop_{y}':(f'pop_{y}','sum') for y in YRS+[2017,2023]},**{f'flag_{y}':(f'flag_{y}',lambda s:'complete' if (s=='complete').all() else 'partial') for y in YRS[:-1]})
d23=m23[m23.unit_type=='district'].set_index('district')
G['pop_2017_pbs_district_row']=G.district_2023.map(d23.pop_2017_restated); G['pop_2023_pbs_district_row']=G.district_2023.map(d23.pop_2023)
G.to_csv(OUT+'population_panel_2023_frame_districts.csv',index=False)
chk=(G.pop_2023-G.pop_2023_pbs_district_row).abs().max(), (G.pop_2017-G.pop_2017_pbs_district_row).abs().max()
# ---- checks
rep=dict(coverage_1998_frame=cov,
    totals_1998_frame={y:float(P[f'pop_{y}'].sum()) for y in YRS},
    totals_2023_frame={y:float(K[f'pop_{y}'].sum()) for y in YRS+[2017,2023]},
    pco_province_totals={y:float(raw[(raw.unit_type=='province')&(raw.census_year==y)&raw.province.str.isupper()&~raw.province.str.contains('FEDERAL CAPITAL')].population.sum()) for y in YRS},
    district_2023_vs_pbs_rows=dict(max_abs_dev_2023=float(chk[0]),max_abs_dev_2017=float(chk[1])),
    units_2023=len(K),districts_2023=len(G))
import json; json.dump(rep,open(OUT+'validation_summary_panel.json','w'),indent=1); print(json.dumps(rep,indent=1))
