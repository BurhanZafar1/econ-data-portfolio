"""Area weights, from PBS's own published areas (Census 2023 Table 1, sq km of each 2023 unit).
For 2017 unit i and 2023 unit j with population flow F_ij (from the population crosswalk) and
PBS 2017-restated population P_j of the 2023 unit: the land of j attributed to i is
    area_ij = area_j * F_ij / P_j        (uniform density within the 2023 unit)
and area_weight_ij = area_ij / sum_j area_ij. For 1:1 rows and pure splits this reduces to the
published areas exactly (no density assumption); only rows where a 2023 unit draws people from
more than one 2017 unit (boundary transfers) use the assumption, and are flagged.
A geoBoundaries 2017 polygon overlay is kept as an independent check column where that polygon
covers the crosswalk's 2023 units by >= 90% (the geoBoundaries layer mixes vintages and is not
used as a source)."""
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
# overlay check
p23=gpd.read_file('raw/pbs_tehsils_2023.geojson').to_crs(32642); p23['geometry']=p23.geometry.buffer(0); p23=p23.set_index('dds_id')
g17=gpd.read_file('raw/gb_PAK_ADM3_2017.geojson').to_crs(32642); g17['geometry']=g17.geometry.buffer(0)
gd=pd.read_csv('build/gb_adm3_2017_with_district.csv')[['shapeID','dist']]; g17=g17.merge(gd,on='shapeID')
def base(n):
    n=n.upper()
    for w in ['SUB-DIVISION','SUB DIVISION','SUB-TEHSIL','SUB TEHSIL','TEHSIL','TALUKA','F.R','FR ','SUB-','DISTRICT','SUB']: n=n.replace(w,' ')
    n=re.sub(r'[^A-Z0-9]+',' ',n).strip()
    return n.replace('TALA GANG','TALAGANG').replace('CHIKSAR','CHAKISAR').replace('D I KHAN','DERA ISMAIL KHAN').replace('MUSA KHEL','MUSAKHEL').replace('DALBADIN','DALBANDIN')
g17['b']=g17.shapeName.map(base); g17['d']=g17.dist.str.upper().str.replace('QILLA','KILLA').str.replace('SHEIKHPURA','SHEIKHUPURA')
X['overlay_area_weight']=np.nan; X['overlay_coverage']=np.nan
for uid,grp in X[X.area_basis!='identity'].groupby('unit_id_2017'):
    r=grp.iloc[0]; b=base(r.unit_2017); d=r.district_2017.upper().replace(' DISTRICT','').replace(' AGENCY','')
    cand=g17[(g17.b==b)&(g17.d.str.contains(d.split()[0]))]
    if len(cand)!=1: continue
    poly=cand.geometry.iloc[0]; A=poly.area
    inter={j:poly.intersection(p23.loc[j].geometry).area for j in grp.unit_id_2023}; s=sum(inter.values())
    X.loc[grp.index,'overlay_coverage']=s/A
    if s/A>=0.9:
        for k in grp.index: X.loc[k,'overlay_area_weight']=inter[X.loc[k,'unit_id_2023']]/s
X=X.drop(columns=['area_ij'])
X.to_csv(OUT+'crosswalk_tehsil_2017_to_2023.csv',index=False)
print(X.area_basis.value_counts()); print('area weight sums off:',(abs(X.groupby('unit_id_2017').area_weight.sum()-1)>1e-9).sum())
o=X[X.overlay_area_weight.notna()]
print('overlay check available for',o.unit_id_2017.nunique(),'units;', 'max |pbs area wt - overlay wt| =',(o.area_weight-o.overlay_area_weight).abs().max().round(3))
print(o[(o.area_weight-o.overlay_area_weight).abs()>0.1][['unit_2017','unit_2023','pop_weight','area_weight','overlay_area_weight','overlay_coverage']].round(3).to_string())
