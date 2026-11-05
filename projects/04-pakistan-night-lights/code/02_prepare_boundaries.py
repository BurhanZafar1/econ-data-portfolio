"""Fix the unit list at the Census 2023 frame and prepare the polygons.

Inputs (raw/boundaries/): pbs_tehsils_2023.geojson (649 sub-district units, key dds_id) and
pbs_districts_2023.geojson (156 districts, key district_code), the PBS Digital Census 2023 boundaries as
redistributed by Data Darbar (https://darbar.adaad.org/, release 2026-11-01). Both include Islamabad,
AJK and Gilgit-Baltistan; the column outside_census_frame marks polygons that have no row in the 2023
census tables, and province identifies the four provinces.

Output (output/): boundaries_tehsil_2023.gpkg and boundaries_district_2023.gpkg with valid geometries and
a geodesic area (area_km2), plus boundaries_units_2023.csv listing the units.
"""
import geopandas as gpd, pandas as pd, numpy as np, os
from pyproj import Geod
HERE=os.path.dirname(__file__); RAW=os.path.join(HERE,'..','raw','boundaries'); OUT=os.path.join(HERE,'..','output'); os.makedirs(OUT,exist_ok=True)
geod=Geod(ellps='WGS84')
def area_km2(geom): return abs(geod.geometry_area_perimeter(geom)[0])/1e6
for name,key in [('tehsil','dds_id'),('district','district_code')]:
    g=gpd.read_file(os.path.join(RAW,f'pbs_{name}s_2023.geojson')).to_crs(4326)
    bad=(~g.geometry.is_valid).sum(); g['geometry']=g.geometry.buffer(0)
    assert g.geometry.is_valid.all() and g[key].is_unique
    g['area_km2']=[area_km2(x) for x in g.geometry]
    g['in_four_provinces']=g.province.isin(['PUNJAB','SINDH','KHYBER PAKHTUNKHWA','BALOCHISTAN'])
    g['outside_census_frame']=g.outside_census_frame.fillna(False).astype(bool)
    g.to_file(os.path.join(OUT,f'boundaries_{name}_2023.gpkg'),driver='GPKG')
    print(f'{name}s: {len(g)} polygons, {bad} repaired, total area {g.area_km2.sum():,.0f} km2, four provinces {g.in_four_provinces.sum()}')
    if name=='tehsil': g.drop(columns='geometry').to_csv(os.path.join(OUT,'boundaries_units_2023.csv'),index=False)
