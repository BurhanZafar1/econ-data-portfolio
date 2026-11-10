"""Download series B: the global NPP-VIIRS-like night-time light annual data, Version 2 (Chen, Yu, Yang et al.;
Harvard Dataverse doi:10.7910/DVN/YGIVCD), one zip per year 1992-2025, and verify each file's md5 against the
Dataverse record.

Usage:  python code/01b_download_viirs_like.py        (downloads into raw/viirs_like_v2/; about 3.4 GB)
The file list raw/viirs_like_list.txt (name, Dataverse file id, size in bytes, md5) was taken from the dataset's
API record on 5 November 2026 (raw/dataverse_YGIVCD.json, dataset version 10). Files already present with the
right size and md5 are skipped, so the script also serves to verify an existing download.
"""
import hashlib, os, sys, urllib.request
HERE=os.path.dirname(os.path.abspath(__file__)); RAW=os.path.join(HERE,'..','raw'); OUT=os.path.join(RAW,'viirs_like_v2'); os.makedirs(OUT,exist_ok=True)
def md5(p):
    h=hashlib.md5()
    with open(p,'rb') as fh:
        for chunk in iter(lambda: fh.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()
rows=[l.split() for l in open(os.path.join(RAW,'viirs_like_list.txt')) if l.strip()]
bad=0
for name,fid,size,m in rows:
    p=os.path.join(OUT,name)
    if os.path.exists(p) and os.path.getsize(p)==int(size) and md5(p)==m: print('ok      ',name); continue
    url=f'https://dataverse.harvard.edu/api/access/datafile/{fid}'
    print('download',name,round(int(size)/1e6,1),'MB',flush=True); urllib.request.urlretrieve(url,p)
    if md5(p)!=m: print('md5 mismatch for',name); bad+=1
if bad: sys.exit('some files failed verification')
print('all files present and verified')
