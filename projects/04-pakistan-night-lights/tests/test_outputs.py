"""Checks on the released tables (run from the project root: pytest -q)."""
import os, glob, hashlib, pandas as pd, numpy as np, pytest
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); OUT=os.path.join(ROOT,'output')
@pytest.mark.parametrize('f,key,years',[('ntl_A_harmonizedDN_tehsil_2023frame_1992_2024.csv','dds_id',range(1992,2025)),('ntl_B_viirslike_tehsil_2023frame_1992_2025.csv','dds_id',range(1992,2026)),
                                        ('ntl_A_harmonizedDN_district_2023frame_1992_2024.csv','district_code',range(1992,2025)),('ntl_B_viirslike_district_2023frame_1992_2025.csv','district_code',range(1992,2026))])
def test_complete_balanced_panel(f,key,years):
    d=pd.read_csv(os.path.join(OUT,f)); assert not d.duplicated([key,'year']).any()
    assert set(d.year.unique())==set(years) and (d.groupby(key).year.nunique()==len(years)).all()
    pre=[c for c in d.columns if c.endswith('_sum_km2') and not c.startswith(('log1p','asinh'))][0]
    assert (d[pre]>=0).all() and d[pre].notna().all()
    assert np.allclose(d.pixel_area_km2/d.area_km2,1,atol=0.01), 'raster-assigned area differs from geodesic area by over 1 percent'
    assert np.allclose(np.log1p(d[pre]),d['log1p_'+pre],atol=1e-4) and np.allclose(np.arcsinh(d[pre]),d['asinh_'+pre],atol=1e-4)
def test_districts_add_up_from_tehsils():
    t=pd.read_csv(os.path.join(OUT,'ntl_B_viirslike_tehsil_2023frame_1992_2025.csv')); d=pd.read_csv(os.path.join(OUT,'ntl_B_viirslike_district_2023frame_1992_2025.csv'))
    s=t.groupby(['district_2023','year']).rad_sum_km2.sum(); dd=d.set_index(['district_2023','year']).rad_sum_km2
    rel=((s-dd.reindex(s.index)).abs()/dd.reindex(s.index).clip(lower=1)); assert rel.median()<0.01
def test_rankings_are_permutations():
    r=pd.read_csv(os.path.join(OUT,'rankings','rankings_district_long.csv'))
    for k,g in r.groupby(['series','measure','variant','year']):   # rank = 1 + number of units with a strictly larger value (ties, mostly zero light, share the rank)
        v=g.value.values; assert (g['rank'].values==1+np.array([(v>x).sum() for x in v])).all(), k
    n=r.groupby('variant').unit.nunique(); assert n['i_all']==130 and n['ii_no_big5']==125 and n['iii_no_big5_or_adjacent']==104
def test_codebook_and_checksums():
    cb=pd.read_csv(os.path.join(ROOT,'docs','codebook.csv'))
    for f in glob.glob(os.path.join(OUT,'*.csv')): assert set(pd.read_csv(f,nrows=1).columns)<=set(cb[cb.file==os.path.basename(f)].column), f
    bad=[]
    for line in open(os.path.join(OUT,'CHECKSUMS.sha256')):
        h,f=line.strip().split('  ',1)
        if f.startswith('docs/') and f.endswith('.md'): continue
        if hashlib.sha256(open(os.path.join(ROOT,f),'rb').read()).hexdigest()!=h: bad.append(f)
    assert not bad, bad
