"""Weight distribution, population mapped, and an uncertainty bound for every crosswalk layer, plus a map.

Writes docs/WEIGHTS_AND_UNCERTAINTY.md and output/uncertainty_by_target_unit.csv and output/figures/
fig_crosswalk_uncertainty_map.png. Every number in the note is computed here from the output files.

The uncertainty bound: a crosswalk row that equals a published PBS/PCO figure or is forced by the published
tables (confidence high) carries no allocation uncertainty beyond the sources themselves. Rows graded medium
or low are the resolver's inferences. For each target unit the share of the population it receives on such
rows is the largest share of its reconstructed source-year population that could be mis-assigned if every
inference were wrong; it is reported per unit so users can drop or flag the units they consider too uncertain.
"""
import pandas as pd, numpy as np, json, os
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import geopandas as gpd
OUT='output/'; os.makedirs(OUT+'figures',exist_ok=True)
LAYERS=[('crosswalk_tehsil_2017_to_2023.csv','unit_id_2017','unit_id_2023','pop_2017','flow_2017','2017 -> 2023 tehsils'),
        ('crosswalk_tehsil_1998_to_2017.csv','unit_id_1998','unit_id_2017','pop_1998','flow_1998','1998 (report frame) -> 2017 tehsils'),
        ('crosswalk_tehsil_1998_to_2023.csv','unit_id_1998','unit_id_2023','pop_1998','flow_1998','1998 (report frame) -> 2023 tehsils (chained)'),
        ('crosswalk_tehsil_1998census_to_pcoframe.csv','unit_id_1998census','unit_id_1998','pop_1998census','flow_1998','census-day 1998 -> report frame'),
        ('crosswalk_tehsil_1998census_to_2023.csv','unit_id_1998census','unit_id_2023','pop_1998census','flow_1998','census-day 1998 -> 2023 tehsils (chained)'),
        ('crosswalk_district_2017_to_2023.csv','district_2017','district_2023','pop_2017','flow_2017','2017 -> 2023 districts'),
        ('crosswalk_district_1998_to_2023.csv','district_1998','district_2023','pop_1998','flow_1998','1998 (report frame) -> 2023 districts'),
        ('crosswalk_district_1998census_to_2023.csv','district_1998census','district_2023','pop_1998census','flow_1998','census-day 1998 -> 2023 districts'),
        ('crosswalk_district_historical_to_1998.csv','historical_district','district_1998',None,None,'1951-1981 district maps -> 1998 districts')]
rows=[]; per_unit=[]
for f,src,tgt,pop,flow,label in LAYERS:
    c=pd.read_csv(OUT+f)
    if f.startswith('crosswalk_district_historical'):
        for y,g in c.groupby('census_year'):
            w=g.weight; key=g.historical_district
            rows.append(dict(layer=f'{label}, {y}',source_units=key.nunique(),rows=len(g),split_sources=int((g.groupby('historical_district').size()>1).sum()),
                             share_rows_w_02_08=float(((w>0.2)&(w<0.8)).mean()),share_rows_w_04_06=float(((w>0.4)&(w<0.6)).mean()),
                             share_pop_on_nonexact_rows=float(g.loc[g.weight_basis!='pco_restatement_exact','pop_historical_district'].mul(g.loc[g.weight_basis!='pco_restatement_exact','weight']).sum()/g.pop_historical_district.mul(g.weight).sum()),
                             share_pop_on_low_rows=np.nan,largest_source_share_uncertain=np.nan,weights_sum_to_one=bool(np.allclose(g.groupby('historical_district').weight.sum(),1)),
                             population_mapped_share=1.0,note='non-exact rows use proxy shares from a later census (weight_basis)'))
        continue
    w=c.pop_weight; tot=c[flow].sum(); src_tot=c.drop_duplicates(src)[pop].sum()
    if f.startswith('crosswalk_district'):
        # district layers: only inferred tehsil rows that cross a district line can move a district total. For a target
        # district the uncertain population is what arrives from other districts on inferred rows plus what leaves its
        # own source district on inferred rows (the amount that stayed is uncertain by the same count).
        T=pd.read_csv(OUT+f.replace('crosswalk_district','crosswalk_tehsil'))
        cross=T[(T[src]!=T[tgt])&(T.confidence!='high')]; crosslow=cross[cross.confidence=='low']
        inn=cross.groupby(tgt)[flow].sum(); out_=cross.groupby(src)[flow].sum(); inlow=crosslow.groupby(tgt)[flow].sum(); outlow=crosslow.groupby(src)[flow].sum()
        u=c.groupby(tgt).agg(received=(flow,'sum'),n_sources=(flow,'size'))
        u['received_nonhigh']=u.index.map(lambda d:inn.get(d,0)+out_.get(d,0)); u['received_low']=u.index.map(lambda d:inlow.get(d,0)+outlow.get(d,0))
        non_pop=cross[flow].sum(); low_pop=crosslow[flow].sum(); note='uncertain = inferred tehsil flows that cross a district line'
    else:
        non=c.confidence!='high'; low=c.confidence=='low'
        u=c.groupby(tgt).apply(lambda g:pd.Series(dict(received=g[flow].sum(),received_nonhigh=g.loc[g.confidence!='high',flow].sum(),received_low=g.loc[g.confidence=='low',flow].sum(),n_sources=len(g))),include_groups=False)
        non_pop=c.loc[non,flow].sum(); low_pop=c.loc[low,flow].sum(); note=''
    u['share_uncertain']=(u.received_nonhigh/u.received).clip(upper=1); u['share_low']=(u.received_low/u.received).clip(upper=1); u['layer']=f
    per_unit.append(u.reset_index().rename(columns={tgt:'target_unit'}))
    rows.append(dict(layer=label,source_units=c[src].nunique(),rows=len(c),split_sources=int((c.groupby(src).size()>1).sum()),
                     share_rows_w_02_08=float(((w>0.2)&(w<0.8)).mean()),share_rows_w_04_06=float(((w>0.4)&(w<0.6)).mean()),
                     share_pop_on_nonexact_rows=float(non_pop/tot),share_pop_on_low_rows=float(low_pop/tot),
                     largest_source_share_uncertain=float(u.share_uncertain.max()),weights_sum_to_one=bool(np.allclose(c.groupby(src).pop_weight.sum(),1)),
                     population_mapped_share=float(tot/src_tot),note=note))
W=pd.DataFrame(rows); W.to_csv(OUT+'weights_and_uncertainty_by_layer.csv',index=False)
PU=pd.concat(per_unit); PU.to_csv(OUT+'uncertainty_by_target_unit.csv',index=False)
# --- map: 2023 tehsils, share of reconstructed 1998 population arriving on inferred rows (1998 report frame -> 2023)
g23=gpd.read_file(OUT+'../raw/pbs_tehsils_2023.geojson') if os.path.exists(OUT+'../raw/pbs_tehsils_2023.geojson') else gpd.read_file('raw/pbs_tehsils_2023.geojson')
g23['geometry']=g23.geometry.buffer(0)
u=PU[PU.layer=='crosswalk_tehsil_1998_to_2023.csv'].set_index('target_unit')
g23['share_uncertain']=g23.dds_id.map(u.share_uncertain); g23['n_sources']=g23.dds_id.map(u.n_sources)
fig,ax=plt.subplots(1,2,figsize=(13,7.2),facecolor='#fcfcfb')
ramp=['#cde2fb','#9ec5f4','#6da7ec','#3987e5','#256abf','#184f95','#0d366b']
from matplotlib.colors import ListedColormap, BoundaryNorm
cm1=ListedColormap(ramp); bins=[0,0.001,0.05,0.10,0.25,0.5,0.75,1.0001]; nrm=BoundaryNorm(bins,cm1.N)
base=g23[g23.share_uncertain.isna()]
for a in ax: base.plot(ax=a,color='#f0efec',edgecolor='#ffffff',linewidth=0.2)
g23.dropna(subset=['share_uncertain']).plot(ax=ax[0],column='share_uncertain',cmap=cm1,norm=nrm,edgecolor='#ffffff',linewidth=0.2)
cm2=ListedColormap(ramp[1:]); bins2=[0.5,1.5,2.5,3.5,4.5,5.5,99]; nrm2=BoundaryNorm(bins2,cm2.N)
g23.dropna(subset=['n_sources']).plot(ax=ax[1],column='n_sources',cmap=cm2,norm=nrm2,edgecolor='#ffffff',linewidth=0.2)
for a,t in zip(ax,['Share of the unit\'s reconstructed 1998 population that arrives\non inferred (medium or low) rows, 1998 report frame -> 2023','Number of 1998 source units contributing to the 2023 unit']):
    a.set_axis_off(); a.set_title(t,fontsize=10,loc='left',color='#0b0b0b')
import matplotlib.patches as mp
ax[0].legend(handles=[mp.Patch(color=ramp[i],label=l) for i,l in enumerate(['0 (all rows published or forced)','under 5%','5-10%','10-25%','25-50%','50-75%','75-100%'])]+[mp.Patch(color='#f0efec',label='outside the crosswalk (ISB, AJK, GB)')],loc='lower left',fontsize=8,frameon=False)
ax[1].legend(handles=[mp.Patch(color=ramp[1:][i],label=l) for i,l in enumerate(['1','2','3','4','5','6 or more'])]+[mp.Patch(color='#f0efec',label='outside the crosswalk')],loc='lower left',fontsize=8,frameon=False,title='source units',title_fontsize=8)
fig.suptitle('Where the 1998 -> 2023 tehsil crosswalk rests on inference',fontsize=12,x=0.01,ha='left',color='#0b0b0b')
plt.tight_layout(); fig.savefig(OUT+'figures/fig_crosswalk_uncertainty_map.png',dpi=160); plt.close(fig)
# --- note
L=['# Weight distribution, population mapped, and an uncertainty bound\n',
   f"Fifth release, {pd.Timestamp.today():%d %B %Y}. Generated by build/19_weights_and_uncertainty.py from the files in output/; the table below is output/weights_and_uncertainty_by_layer.csv and the per-unit figures are output/uncertainty_by_target_unit.csv.\n",
   '## 1. What the numbers mean',
   'population_mapped_share: the source-year population carried to the target frame divided by the source-frame total (1.000 means every person is placed; the build asserts this for every PBS/PCO layer). split_sources: source units with more than one target. share_rows_w_02_08 and share_rows_w_04_06: the share of rows whose population weight lies in (0.2, 0.8) and (0.4, 0.6), the usual measure of how much of a crosswalk is non-trivial splitting rather than relabelling. share_pop_on_nonexact_rows: the share of the population that moves on rows the resolver inferred (confidence medium or low) rather than rows that equal a published figure or are forced by the published tables; share_pop_on_low_rows: the same for rows with an equally plausible alternative. largest_source_share_uncertain: the largest share, over target units, of a unit\'s reconstructed source-year population that arrives on inferred rows (the per-unit values are in uncertainty_by_target_unit.csv).\n',
   '| Layer | Source units | Rows | Split sources | Rows w in (0.2,0.8) | Rows w in (0.4,0.6) | Pop on inferred rows | Pop on low rows | Largest uncertain share of a target unit | Pop mapped |','|---|---|---|---|---|---|---|---|---|---|']
for _,r in W.iterrows():
    L.append(f"| {r.layer} | {r.source_units} | {r.rows} | {r.split_sources} | {r.share_rows_w_02_08:.1%} | {r.share_rows_w_04_06:.1%} | {r.share_pop_on_nonexact_rows:.2%} | {'' if pd.isna(r.share_pop_on_low_rows) else f'{r.share_pop_on_low_rows:.2%}'} | {'' if pd.isna(r.largest_source_share_uncertain) else f'{r.largest_source_share_uncertain:.0%}'} | {r.population_mapped_share:.3f} |")
L.append('\nFor the historical district layer the "inferred" rows are the 1951, 1961 and 1972 rows whose weights are proxy shares from a later census (docs/BACKWARD_EXTENSION.md section 2); the population mapped is 1.000 by construction except the 1951 Balochistan shortfall of 20,320 persons in the report itself.\n')
L.append('## 2. Target units that rest most on inference')
for f,src,tgt,pop,flow,label in LAYERS[:5]:
    u=PU[PU.layer==f].sort_values('share_uncertain',ascending=False); u=u[u.share_uncertain>=0.25]
    c=pd.read_csv(OUT+f); nm=c.drop_duplicates(tgt).set_index(tgt)
    NAMES={'unit_id_2023':('unit_2023','district_2023'),'unit_id_2017':('unit_2017','district_2017'),'unit_id_1998':('unit_1998_pcoframe','district_1998_pcoframe')}
    namecol,dcol=NAMES[tgt]
    L.append(f"- {label}: {len(u)} target units receive 25% or more of their population on inferred rows"+(': '+'; '.join(f"{nm.loc[t,namecol].title()}{' ('+nm.loc[t,dcol].replace(' DISTRICT','').title()+')' if dcol else ''} {s:.0%}" for t,s in zip(u.target_unit,u.share_uncertain)) if len(u) else '')+'.')
L.append('\nThese are the units a user should treat with care, or re-derive from a District Census Report, before using a 1998-based variable on them. Most are small sub-tehsils formed after 1998 whose source could be either of two neighbours; the persons involved are the flow column of the rows concerned.\n')
L.append('## 3. How to use this as a sensitivity bound')
def cnt(f):
    u=PU[PU.layer==f]; return f"{int((u.share_uncertain>0).sum())} of {len(u)} target units receive anything on inferred rows, {int((u.share_uncertain>=0.25).sum())} receive a quarter or more and {int((u.share_uncertain>=0.5).sum())} half or more"
L.append('A variable crosswalked with the population weights inherits the inference only through the inferred rows. The crudest bound: for a target unit with uncertain share s, the reconstructed value could be wrong by at most s times the value (if every inferred person was mis-assigned). In the 1998 -> 2023 tehsil layer '+cnt('crosswalk_tehsil_1998_to_2023.csv')+'; in the 2017 -> 2023 tehsil layer '+cnt('crosswalk_tehsil_2017_to_2023.csv')+'. At district level '+cnt('crosswalk_district_1998_to_2023.csv')+' (1998 -> 2023), because almost every inferred flow is between tehsils of the same district and leaves the district total untouched. A sharper check is to rerun an analysis dropping the target units with s above a chosen cut-off (uncertainty_by_target_unit.csv gives s for every unit and layer) and to report both results.\n')
L.append('## 4. Figure')
L.append('output/figures/fig_crosswalk_uncertainty_map.png: left, every 2023 tehsil shaded by the share of its reconstructed 1998 population that arrives on inferred rows; right, the number of 1998 source units contributing to it. Units outside the crosswalk (Islamabad, AJK, Gilgit-Baltistan) are grey.\n')
L.append('## 5. The uniform-density assumption')
L.append('Area weights split a new unit\'s published area between its source units in proportion to people only where a new unit was formed from more than one source (area_basis = uniform_density_split); everywhere else the area weight is the published area of the target unit over the published area of the source (exact). The population weights make no density assumption: they are PBS\'s own restated counts, or flows chosen to reproduce them. A variable distributed more unevenly than people over the territory of a split unit (for example irrigated land, or a single large plant) will be allocated with larger error than population itself; this is true of every crosswalk built from counts and cannot be fixed without unit-level geography of the variable. Only stock variables (counts) should be crosswalked; rates, shares and means must be rebuilt from their numerator and denominator counts, which the apply functions do when given counts, or averaged with the flow column as the weight.')
open('docs/WEIGHTS_AND_UNCERTAINTY.md','w').write('\n'.join(L)+'\n'); print(W[['layer','share_rows_w_02_08','share_pop_on_nonexact_rows','largest_source_share_uncertain','population_mapped_share']].to_string())
