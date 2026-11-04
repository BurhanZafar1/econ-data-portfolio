"""Overlay the US Census Bureau Demobase 2017 tehsil polygons (PK_GEOG1_ADM4_2017, 535 units in
the four provinces and FATA, named as in PBS Census 2017 Table 1) on the PBS Digital Census 2023
tehsil polygons. Output: one row per (2017 unit, 2023 unit) pair with intersection area."""
import geopandas as gpd, pandas as pd, numpy as np, re
OUT='output/'; INT='build/intermediate/'
PROV={'PUNJAB','SINDH','BALOCHISTAN','KHYBER PAKHTUNKHWA','FATA'}
g=gpd.read_file('raw/demobase/Pakistan.gdb',layer='PK_GEOG1_ADM4_2017_uscb_202401')
g['province']=g.ADM1_NAME.str.replace('\xa0',' ').str.strip().str.upper().replace({'FEDERALLY ADMINISTERED TRIBAL AREAS':'FATA'})
g=g[g.province.isin(PROV)].copy()
for c in ['ADM3_NAME','ADM4_NAME']: g[c]=g[c].str.replace('\xa0',' ').str.strip().str.upper()
m17=pd.read_csv(OUT+'unit_master_2017_all.csv'); m17=m17[(m17.unit_type!='district')&m17.province_area.isin(PROV)].copy()
m17['unit_id_2017']=['T17-'+f'{i:04d}' for i in range(1,len(m17)+1)]
m17['u']=m17.unit.str.upper().str.strip()
# 1) exact (province, district, unit); 2) (province, unit) if unique on both sides; 3) by district first word + unit
key=g.set_index(['province','ADM3_NAME','ADM4_NAME']).GEO_MATCH
m17['geo']=[key.get((p,d,u)) for p,d,u in zip(m17.province_area,m17.district,m17.u)]
g2=g.groupby(['province','ADM4_NAME']).GEO_MATCH.agg(list)
for i,r in m17[m17.geo.isna()].iterrows():
    c=g2.get((r.province_area,r.u),[])
    if len(c)==1 and (m17[(m17.province_area==r.province_area)&(m17.u==r.u)].shape[0]==1): m17.loc[i,'geo']=c[0]
for i,r in m17[m17.geo.isna()].iterrows():
    c=g[(g.province==r.province_area)&(g.ADM3_NAME.str.split().str[0]==r.district.split()[0])&(g.ADM4_NAME.str.split().str[0]==r.u.split()[0])]
    if len(c)==1: m17.loc[i,'geo']=c.GEO_MATCH.iloc[0]
print('matched',m17.geo.notna().sum(),'of',len(m17)); print(m17[m17.geo.isna()][['district','unit']].to_string())
assert m17.geo.dropna().is_unique
m17[['unit_id_2017','province_area','district','unit','geo']].to_csv(INT+'demobase2017_match.csv',index=False)
G=g.set_index('GEO_MATCH').loc[m17.geo.dropna()].reset_index().to_crs(32642); G['geometry']=G.geometry.buffer(0)
G=G.merge(m17[['geo','unit_id_2017']],left_on='GEO_MATCH',right_on='geo')
G['area17_km2']=G.area/1e6
P=gpd.read_file('raw/pbs_tehsils_2023.geojson').to_crs(32642); P['geometry']=P.geometry.buffer(0); P['area23_km2']=P.area/1e6
inter=gpd.overlay(G[['unit_id_2017','area17_km2','geometry']],P[['dds_id','area23_km2','geometry']],how='intersection',keep_geom_type=False)
inter['inter_km2']=inter.area/1e6
inter=inter[inter.inter_km2>0.01][['unit_id_2017','dds_id','area17_km2','area23_km2','inter_km2']]
inter['share_of_2017']=inter.inter_km2/inter.area17_km2; inter['share_of_2023']=inter.inter_km2/inter.area23_km2
inter.to_csv(INT+'overlay_2017x2023.csv',index=False)
print(len(inter),'intersections; 2017 polygons covered:', inter.groupby('unit_id_2017').share_of_2017.sum().describe().round(3).to_dict())
