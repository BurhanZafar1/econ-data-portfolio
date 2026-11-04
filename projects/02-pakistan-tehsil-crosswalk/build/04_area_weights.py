"""Area weights, from PBS's own published areas (Census 2023 Table 1, sq km of each 2023 unit).
For 2017 unit i and 2023 unit j with population flow F_ij (from the population crosswalk) and
PBS 2017-restated population P_j of the 2023 unit: the land of j attributed to i is
    area_ij = area_j * F_ij / P_j        (uniform density within the 2023 unit)
and area_weight_ij = area_ij / sum_j area_ij. For 1:1 rows and pure splits this reduces to the
published areas exactly (no density assumption); only rows where a 2023 unit draws people from
more than one 2017 unit (boundary transfers) use the assumption, and are flagged.
An overlay of the US Census Bureau Demobase 2017 tehsil polygons on the PBS 2023 polygons is
kept as a check column only: the two layers are different digitisations and carry label swaps,
so they are not used as a source (see check_overlay_mismatches.csv)."""
import pandas as pd, numpy as np, geopandas as gpd, re
OUT='output/'
X=pd.read_csv('build/intermediate/crosswalk_tehsil_2017_to_2023_pop.csv')
m23=pd.read_csv(OUT+'unit_master_2023_all.csv').set_index('dds_id')
X['area_2023_km2']=X.unit_id_2023.map(m23.area_km2)
X['flow_2017']=(X.pop_weight*X.pop_2017).round().astype(int)
X['area_ij']=X.area_2023_km2*X.flow_2017/X.pop_2017_restated_2023
tot=X.groupby('unit_id_2017').area_ij.transform('sum')
X['area_weight']=X.area_ij/tot
nsrc=X.groupby('unit_id_2023').unit_id_2017.transform('nunique')
X['area_basis']=np.where(X.groupby('unit_id_2017').unit_id_2017.transform('size')==1,'identity',np.where(nsrc==1,'pbs_area_2023_exact','pbs_area_2023_uniform_density'))
# overlay check: US Census Bureau Demobase 2017 tehsil polygons x PBS 2023 polygons (build/02b_overlay.py)
I=pd.read_csv('build/intermediate/overlay_2017x2023.csv')
X=X.merge(I[['unit_id_2017','dds_id','share_of_2017']].rename(columns={'dds_id':'unit_id_2023','share_of_2017':'ov'}),on=['unit_id_2017','unit_id_2023'],how='left')
X['ov']=X.ov.fillna(0)
X['overlay_coverage']=X.groupby('unit_id_2017').ov.transform('sum')          # share of the 2017 polygon inside its crosswalk 2023 units
X['overlay_area_weight']=np.where(X.overlay_coverage>0,X.ov/X.overlay_coverage,np.nan)
X=X.drop(columns='ov')
# label/geometry mismatches: 2017 polygons that lie mostly outside the 2023 units the crosswalk assigns them to
m23=pd.read_csv(OUT+'unit_master_2023_all.csv').set_index('dds_id')
bad=X[X.overlay_coverage<0.5].drop_duplicates('unit_id_2017')
rows=[]
for _,r in bad.iterrows():
    top=I[I.unit_id_2017==r.unit_id_2017].sort_values('share_of_2017',ascending=False).head(2)
    rows.append(dict(unit_id_2017=r.unit_id_2017,unit_2017=r.unit_2017,district_2017=r.district_2017,crosswalk_units_2023='; '.join(X[X.unit_id_2017==r.unit_id_2017].unit_2023),overlay_coverage=round(r.overlay_coverage,3),
        polygon_mostly_in='; '.join(f"{m23.loc[d].unit} ({s:.2f})" for d,s in zip(top.dds_id,top.share_of_2017))))
pd.DataFrame(rows).to_csv(OUT+'check_overlay_mismatches.csv',index=False)
X=X.drop(columns=['area_ij'])
X.to_csv(OUT+'crosswalk_tehsil_2017_to_2023.csv',index=False)
print(X.area_basis.value_counts()); print('area weight sums off:',(abs(X.groupby('unit_id_2017').area_weight.sum()-1)>1e-9).sum())
print('overlay coverage of 2017 polygons by their crosswalk 2023 units: median %.3f, below 0.5 for %d units (listed in check_overlay_mismatches.csv)'%(X.drop_duplicates('unit_id_2017').overlay_coverage.median(),len(rows)))
s=X[(X.groupby('unit_id_2017').unit_id_2017.transform('size')>1)&(X.overlay_coverage>=0.8)]
print('split units with coverage>=0.8:',s.unit_id_2017.nunique(),'; corr(area_weight, overlay_area_weight)=%.3f; corr(pop_weight, overlay)=%.3f'%(s.area_weight.corr(s.overlay_area_weight),s.pop_weight.corr(s.overlay_area_weight)))
