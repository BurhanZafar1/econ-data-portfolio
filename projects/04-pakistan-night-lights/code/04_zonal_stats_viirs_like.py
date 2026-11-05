"""Series B. Night-time light radiance for every Census 2023 tehsil and district, 1992-2025, from the
global NPP-VIIRS-like annual night-time light data, Version 2 (Chen, Yu, Yang et al.; Harvard Dataverse
doi:10.7910/DVN/YGIVCD, updated July 2026). One consistent series on the VIIRS radiance scale
(nW/cm2/sr), 15 arc-second pixels (about 460 m), built by the authors from DMSP for 1992-2012 and
VIIRS from 2013 with a cross-sensor calibration.

Step 1 clips each global file (10 GB uncompressed inside a 70-150 MB zip) to a window around Pakistan
and caches it in raw/viirs_like_v2_clip/ (about 1 MB a year). Step 2 computes the same exact
area-weighted statistics as series A:
  rad_sum, rad_mean, rad_max, rad_lit_share (radiance > 0), rad_sum_km2 (radiance x pixel km2),
  rad_per_km2, log1p_rad_sum_km2, and rad_sum_gt1_km2 / rad_lit_share_gt1 counting only pixels above
  1 nW/cm2/sr (a conservative noise floor; the authors' validation uses the full field).

Usage: python code/04_zonal_stats_viirs_like.py   (after 02 and the series B download). About 5 minutes.
Download (34 zips, 3.3 GB): https://dataverse.harvard.edu/api/access/datafile/<id> for the files
<year>_Version2.zip listed in raw/viirs_like_list.txt (ids from the Dataverse API), into raw/viirs_like_v2/.
"""
import os, re, glob, zipfile, numpy as np, pandas as pd, geopandas as gpd, rasterio, sys
from rasterio.windows import from_bounds
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from ntl_common import pixel_area_km2, zonal
HERE=os.path.dirname(os.path.abspath(__file__)); RAW=os.path.join(HERE,'..','raw','viirs_like_v2'); CLIP=os.path.join(HERE,'..','raw','viirs_like_v2_clip'); OUT=os.path.join(HERE,'..','output')
os.makedirs(CLIP,exist_ok=True)
teh=gpd.read_file(os.path.join(OUT,'boundaries_tehsil_2023.gpkg')); dis=gpd.read_file(os.path.join(OUT,'boundaries_district_2023.gpkg'))
minx,miny,maxx,maxy=teh.total_bounds; pad=0.2
zips=sorted(glob.glob(os.path.join(RAW,'*_Version2.zip'))); assert zips,'download the Version2 zips first'
# step 1: clip
for z in zips:
    year=int(os.path.basename(z)[:4]); dst=os.path.join(CLIP,f'nppviirs_like_V2_{year}_pakistan.tif')
    if os.path.exists(dst): continue
    tifs=[n for n in zipfile.ZipFile(z).namelist() if n.lower().endswith('.tif')]; assert len(tifs)==1,z
    with rasterio.open(f'zip://{z}!{tifs[0]}') as src:
        win=from_bounds(minx-pad,miny-pad,maxx+pad,maxy+pad,src.transform).round_offsets().round_lengths()
        a=src.read(1,window=win); tr=src.window_transform(win); prof=src.profile.copy()
    prof.update(height=a.shape[0],width=a.shape[1],transform=tr,compress='deflate',tiled=True,blockxsize=256,blockysize=256,count=1)
    with rasterio.open(dst,'w',**prof) as d: d.write(a,1)
    print('clipped',year,a.shape,'max %.1f'%a.max(),flush=True)
# step 2: zonal statistics
out_t=[];out_d=[]
for f in sorted(glob.glob(os.path.join(CLIP,'nppviirs_like_V2_*_pakistan.tif'))):
    year=int(re.search(r'V2_(\d{4})_',f).group(1))
    with rasterio.open(f) as src: rad=src.read(1); tr=src.transform; prof=src.profile.copy()
    rad=np.where(np.isfinite(rad)&(rad>0),rad,0).astype('float32')     # negatives/NaN (none expected) to 0
    area=pixel_area_km2(tr,*rad.shape)
    for layer,key,store in [(teh,'dds_id',out_t),(dis,'district_code',out_d)]:
        r=zonal(layer,key,rad,rad>0,area,prof,'rad',thresh_value=np.where(rad>1,rad,0),thresh_lit=rad>1,thresh_label='gt1')
        r.insert(0,'sensor_basis','DMSP-derived' if year<=2012 else 'VIIRS'); r.insert(0,'year',year)
        r['series_note']='2013-2016: national sum of lights about a quarter below 2012 and 2017, at the DMSP to VIIRS change in the source; compare years within one sensor era' if 2013<=year<=2016 else ''
        store.append(r)
    nat=out_t[-1].merge(teh[['dds_id','in_four_provinces']],on='dds_id').query('in_four_provinces').rad_sum_km2.sum()
    print(year,'sum of lights, four provinces (nW/cm2/sr . km2): %.0f'%nat,flush=True)
T=pd.concat(out_t); D=pd.concat(out_d)
T=T.merge(teh[['dds_id','name','district','province','in_four_provinces','outside_census_frame','area_km2']],on='dds_id').rename(columns={'name':'tehsil_2023','district':'district_2023','province':'province_2023'})
D=D.merge(dis[['district_code','name','census_name','province','in_four_provinces','outside_census_frame','area_km2']],on='district_code').rename(columns={'name':'district_2023','province':'province_2023'})
stats=['area_km2','pixel_area_km2','rad_sum','rad_mean','rad_max','rad_lit_share','rad_sum_km2','rad_per_km2','log1p_rad_sum_km2','rad_sum_gt1_km2','rad_lit_share_gt1','coverage_pixels','series_note']
T=T[['year','sensor_basis','dds_id','tehsil_2023','district_2023','province_2023','in_four_provinces','outside_census_frame']+stats].sort_values(['dds_id','year'])
D=D[['year','sensor_basis','district_code','district_2023','census_name','province_2023','in_four_provinces','outside_census_frame']+stats].sort_values(['district_code','year'])
for X in (T,D):
    for c in stats[:-1]: X[c]=X[c].astype(float).round(6)
T.to_csv(os.path.join(OUT,'ntl_B_viirslike_tehsil_2023frame_1992_2025.csv'),index=False)
D.to_csv(os.path.join(OUT,'ntl_B_viirslike_district_2023frame_1992_2025.csv'),index=False)
T.pivot(index=['dds_id','tehsil_2023','district_2023','province_2023'],columns='year',values='rad_sum_km2').reset_index().to_csv(os.path.join(OUT,'ntl_B_viirslike_tehsil_wide_rad_sum_km2.csv'),index=False)
D.pivot(index=['district_code','district_2023','province_2023'],columns='year',values='rad_sum_km2').reset_index().to_csv(os.path.join(OUT,'ntl_B_viirslike_district_wide_rad_sum_km2.csv'),index=False)
print('tehsil rows',len(T),'district rows',len(D))
