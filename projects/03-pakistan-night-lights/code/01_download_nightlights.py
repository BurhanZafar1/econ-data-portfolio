"""Download the harmonized DMSP-VIIRS night-time light rasters (Li, Zhou, Zhao and Zhao, 2020,
Scientific Data 7:168, updated to 1992-2024 in figshare version 10) and verify each file's md5.

Usage:  python code/01_download_nightlights.py            (downloads into raw/harmonized_ntl/)
Source: https://doi.org/10.6084/m9.figshare.9828827   (CC BY 4.0)
Files:  Harmonized_DN_NTL_<year>_calDMSP.tif for 1992-2013 (inter-calibrated DMSP-OLS stable lights)
        Harmonized_DN_NTL_<year>_simVIIRS.tif for 2014-2024 (VIIRS converted to DMSP-like digital numbers)
Each file is a global GeoTIFF, 30 arc-second pixels (about 0.9 km at Pakistan's latitudes), uint8 DN 0-63.
About 1.1 GB in all.
"""
import json, hashlib, os, sys, urllib.request
ARTICLE='https://api.figshare.com/v2/articles/9828827'
OUT=os.path.join(os.path.dirname(__file__),'..','raw','harmonized_ntl'); os.makedirs(OUT,exist_ok=True)
meta=json.load(urllib.request.urlopen(ARTICLE))
json.dump(meta,open(os.path.join(OUT,'..','figshare_9828827.json'),'w'),indent=1)
files=[f for f in meta['files'] if f['name'].startswith('Harmonized_DN_NTL_')]
print(meta['title']); print(len(files),'files')
def md5(p):
    h=hashlib.md5()
    with open(p,'rb') as fh:
        for chunk in iter(lambda: fh.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()
for f in sorted(files,key=lambda x:x['name']):
    p=os.path.join(OUT,f['name'])
    if os.path.exists(p) and os.path.getsize(p)==f['size'] and md5(p)==f['computed_md5']:
        print('ok      ',f['name']); continue
    print('download',f['name'],round(f['size']/1e6,1),'MB'); urllib.request.urlretrieve(f['download_url'],p)
    if md5(p)!=f['computed_md5']: sys.exit('md5 mismatch for '+f['name'])
print('all files present and verified')
