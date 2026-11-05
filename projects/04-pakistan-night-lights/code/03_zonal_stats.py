"""Series A. Night-time light intensity for every Census 2023 tehsil and district, 1992-2024, from the
harmonized DMSP-VIIRS digital-number rasters (Li, Zhou, Zhao and Zhao 2020, figshare v10).

For each year the script cuts a window around Pakistan, builds a 0/1 "lit" raster (DN > 0) and a
pixel-area raster (km2, varying with latitude), and computes exact area-weighted zonal statistics
with exactextract: every pixel counts in proportion to the share of its area inside the polygon, so
border pixels are split rather than assigned whole.

Per unit and year:
  dn_sum            sum of DN over the unit (pixel DN x covered fraction)        "sum of lights"
  dn_mean           area-weighted mean DN                                           intensity
  dn_max            brightest pixel touching the unit
  dn_lit_share      share of the unit's area with DN > 0
  dn_sum_km2        sum of DN x pixel area (DN.km2; comparable across latitudes)
  dn_per_km2        dn_sum_km2 / pixel_area_km2
  log1p_dn_sum_km2  ln(1 + dn_sum_km2)
  dn_sum_gt7_km2, dn_lit_share_gt7   the same with only pixels above DN 7, the noise floor the
                    dataset's authors recommend ("we suggested using pixels with DN values greater than 7")
  pixel_area_km2    the unit's area as seen by the raster grid (close to area_km2 from the polygon)
  series_note       flags 2014-2016, whose dim-light coverage in Pakistan is far below both 2013 and
                    2017 in the source files (see docs/README.md)
DN is 0-63. 1992-2013 are inter-calibrated DMSP-OLS stable lights (satellites F10 to F18); 2014-2024 are
VIIRS composites converted to the DMSP scale (sensor_basis records which).

Usage: python code/03_zonal_stats.py   (after 01 and 02). About 2 minutes for all years.
"""
import os, re, glob, numpy as np, pandas as pd, geopandas as gpd, rasterio, sys
from rasterio.windows import from_bounds
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from ntl_common import pixel_area_km2, zonal
HERE=os.path.dirname(os.path.abspath(__file__)); RAW=os.path.join(HERE,'..','raw','harmonized_ntl'); OUT=os.path.join(HERE,'..','output')
teh=gpd.read_file(os.path.join(OUT,'boundaries_tehsil_2023.gpkg')); dis=gpd.read_file(os.path.join(OUT,'boundaries_district_2023.gpkg'))
minx,miny,maxx,maxy=teh.total_bounds; pad=0.2
files=sorted(glob.glob(os.path.join(RAW,'Harmonized_DN_NTL_*.tif'))); assert files,'run 01_download_nightlights.py first'
out_t=[];out_d=[]
for f in files:
    year=int(re.search(r'_(\d{4})_',f).group(1)); basis=re.search(r'_(calDMSP|simVIIRS)',f).group(1)
    with rasterio.open(f) as src:
        win=from_bounds(minx-pad,miny-pad,maxx+pad,maxy+pad,src.transform).round_offsets().round_lengths()
        dn=src.read(1,window=win); tr=src.window_transform(win); prof=src.profile.copy()
    assert dn.max()<=63,(year,dn.max())
    prof.update(height=dn.shape[0],width=dn.shape[1],transform=tr,compress='lzw')
    area=pixel_area_km2(tr,*dn.shape)
    note='2014-2016: source files under-record dim lights relative to 2013 and 2017; use with care' if 2014<=year<=2016 else ''
    for layer,key,store in [(teh,'dds_id',out_t),(dis,'district_code',out_d)]:
        r=zonal(layer,key,dn,dn>0,area,prof,'dn',thresh_value=np.where(dn>7,dn,0),thresh_lit=dn>7,thresh_label='gt7')
        r.insert(0,'sensor_basis',basis); r.insert(0,'year',year); r['series_note']=note; store.append(r)
    nat=out_t[-1].merge(teh[['dds_id','in_four_provinces']],on='dds_id').query('in_four_provinces').dn_sum_km2.sum()
    print(year,basis,'sum of lights, four provinces (DN.km2): %.0f'%nat,flush=True)
T=pd.concat(out_t); D=pd.concat(out_d)
T=T.merge(teh[['dds_id','name','district','province','in_four_provinces','outside_census_frame','area_km2']],on='dds_id').rename(columns={'name':'tehsil_2023','district':'district_2023','province':'province_2023'})
D=D.merge(dis[['district_code','name','census_name','province','in_four_provinces','outside_census_frame','area_km2']],on='district_code').rename(columns={'name':'district_2023','province':'province_2023'})
stats=['area_km2','pixel_area_km2','dn_sum','dn_mean','dn_max','dn_lit_share','dn_sum_km2','dn_per_km2','log1p_dn_sum_km2','dn_sum_gt7_km2','dn_lit_share_gt7','coverage_pixels','series_note']
T=T[['year','sensor_basis','dds_id','tehsil_2023','district_2023','province_2023','in_four_provinces','outside_census_frame']+stats].sort_values(['dds_id','year'])
D=D[['year','sensor_basis','district_code','district_2023','census_name','province_2023','in_four_provinces','outside_census_frame']+stats].sort_values(['district_code','year'])
for X in (T,D):
    for c in stats[:-1]: X[c]=X[c].astype(float).round(6)
T.to_csv(os.path.join(OUT,'ntl_A_harmonizedDN_tehsil_2023frame_1992_2024.csv'),index=False)
D.to_csv(os.path.join(OUT,'ntl_A_harmonizedDN_district_2023frame_1992_2024.csv'),index=False)
T.pivot(index=['dds_id','tehsil_2023','district_2023','province_2023'],columns='year',values='dn_sum_km2').reset_index().to_csv(os.path.join(OUT,'ntl_A_harmonizedDN_tehsil_wide_dn_sum_km2.csv'),index=False)
D.pivot(index=['district_code','district_2023','province_2023'],columns='year',values='dn_sum_km2').reset_index().to_csv(os.path.join(OUT,'ntl_A_harmonizedDN_district_wide_dn_sum_km2.csv'),index=False)
print('tehsil rows',len(T),'district rows',len(D))
