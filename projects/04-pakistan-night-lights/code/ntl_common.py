"""Shared helpers for the night-light zonal statistics (used by 03 and 04)."""
import numpy as np, pandas as pd
from rasterio.io import MemoryFile
from exactextract import exact_extract

def pixel_area_km2(transform,height,width):
    """Area of each raster cell on the WGS84 sphere (km2), constant along a row, varying with latitude."""
    R=6371.0088
    dlon=abs(transform.a)
    lat_top=transform.f+np.arange(height)*transform.e
    lat_bot=lat_top+transform.e
    band=(np.sin(np.radians(lat_top))-np.sin(np.radians(lat_bot)))*np.radians(dlon)*R*R
    return np.repeat(band[:,None],width,axis=1).astype('float32')

def zonal(layer,key,value,lit,area,prof,prefix,thresh_value=None,thresh_lit=None,thresh_label=None):
    """Exact area-weighted statistics of `value` (2-D array) inside each polygon of `layer`.
    value: the light raster; lit: 0/1 raster of value>0; area: pixel area km2; prof: rasterio profile for value.
    Optional thresholded rasters give a second pair of columns (sum and lit share above a noise floor)."""
    p_f=prof.copy(); p_f.update(dtype='float32',nodata=None,count=1)
    p_b=prof.copy(); p_b.update(dtype='uint8',nodata=None,count=1)
    with MemoryFile() as m1, MemoryFile() as m2, MemoryFile() as m3, MemoryFile() as m4, MemoryFile() as m5:
        with m1.open(**p_f) as d: d.write(value.astype('float32'),1)
        with m2.open(**p_b) as d: d.write(lit.astype('uint8'),1)
        with m3.open(**p_f) as d: d.write(area,1)
        if thresh_value is not None:
            with m4.open(**p_f) as d: d.write(thresh_value.astype('float32'),1)
            with m5.open(**p_b) as d: d.write(thresh_lit.astype('uint8'),1)
        with m1.open() as v, m2.open() as l, m3.open() as a:
            r=exact_extract(v,layer,['sum','mean','max','count'],include_cols=[key],output='pandas').rename(columns={'sum':f'{prefix}_sum','mean':f'{prefix}_mean','max':f'{prefix}_max','count':'coverage_pixels'})
            r=r.merge(exact_extract(v,layer,['weighted_sum'],weights=a,include_cols=[key],output='pandas').rename(columns={'weighted_sum':f'{prefix}_sum_km2'}),on=key)
            r=r.merge(exact_extract(l,layer,['mean'],include_cols=[key],output='pandas').rename(columns={'mean':f'{prefix}_lit_share'}),on=key)
            r=r.merge(exact_extract(a,layer,['sum'],include_cols=[key],output='pandas').rename(columns={'sum':'pixel_area_km2'}),on=key)
            if thresh_value is not None:
                with m4.open() as tv, m5.open() as tl:
                    r=r.merge(exact_extract(tv,layer,['weighted_sum'],weights=a,include_cols=[key],output='pandas').rename(columns={'weighted_sum':f'{prefix}_sum_{thresh_label}_km2'}),on=key)
                    r=r.merge(exact_extract(tl,layer,['mean'],include_cols=[key],output='pandas').rename(columns={'mean':f'{prefix}_lit_share_{thresh_label}'}),on=key)
    r[f'{prefix}_per_km2']=r[f'{prefix}_sum_km2']/r.pixel_area_km2
    r[f'log1p_{prefix}_sum_km2']=np.log1p(r[f'{prefix}_sum_km2'])
    r[f'asinh_{prefix}_sum_km2']=np.arcsinh(r[f'{prefix}_sum_km2'])   # inverse hyperbolic sine, the usual alternative to log(1+x); both keep zeros
    return r
