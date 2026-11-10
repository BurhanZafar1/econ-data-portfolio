"""Checks on the released tables (run from the project root: pytest -q). They re-derive the properties the build
asserts, from the CSVs alone, so a user can test a downloaded copy without rebuilding it."""
import os, glob, json, hashlib, pandas as pd, numpy as np, pytest
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); OUT=os.path.join(ROOT,'output')
LAYERS=[('crosswalk_tehsil_2017_to_2023.csv','unit_id_2017','unit_id_2023','pop_2017','flow_2017','pop_2017_restated_2023'),
        ('crosswalk_tehsil_1998_to_2017.csv','unit_id_1998','unit_id_2017','pop_1998','flow_1998','pop_1998_restated_2017'),
        ('crosswalk_tehsil_1998_to_2023.csv','unit_id_1998','unit_id_2023','pop_1998','flow_1998',None),
        ('crosswalk_tehsil_1998census_to_pcoframe.csv','unit_id_1998census','unit_id_1998','pop_1998census','flow_1998','pop_1998_pcoframe'),
        ('crosswalk_tehsil_1998census_to_2023.csv','unit_id_1998census','unit_id_2023','pop_1998census','flow_1998',None),
        ('crosswalk_district_2017_to_2023.csv','district_2017','district_2023','pop_2017','flow_2017','pop_2017_restated_2023'),
        ('crosswalk_district_1998_to_2017.csv','district_1998','district_2017','pop_1998','flow_1998',None),
        ('crosswalk_district_1998_to_2023.csv','district_1998','district_2023','pop_1998','flow_1998',None),
        ('crosswalk_district_1998census_to_pcoframe.csv','district_1998census','district_1998_pcoframe','pop_1998census','flow_1998','pop_1998_pcoframe'),
        ('crosswalk_district_1998census_to_2023.csv','district_1998census','district_2023','pop_1998census','flow_1998',None)]
@pytest.mark.parametrize('f,src,tgt,pop,flow,rest',LAYERS)
def test_weights_and_conservation(f,src,tgt,pop,flow,rest):
    c=pd.read_csv(os.path.join(OUT,f))
    assert not c.duplicated([src,tgt]).any(), 'duplicate source-target pair'
    assert np.allclose(c.groupby(src).pop_weight.sum(),1,atol=1e-9), 'population weights do not sum to 1'
    if 'area_weight' in c: assert np.allclose(c.groupby(src).area_weight.sum(),1,atol=1e-9), 'area weights do not sum to 1'
    srcpop=c.drop_duplicates(src).set_index(src)[pop]
    assert abs(c[flow].sum()-srcpop.sum())<1, 'population not conserved'
    assert np.allclose(c.groupby(src)[flow].sum().reindex(srcpop.index),srcpop,atol=0.5), 'flows of a source unit do not add to its population'
    if rest:  # PBS/PCO printed the source-year population on the target units: must be reproduced exactly
        tgtpop=c.drop_duplicates(tgt).set_index(tgt)[rest]
        assert np.allclose(c.groupby(tgt)[flow].sum().reindex(tgtpop.index),tgtpop,atol=0.5), 'published restated population not reproduced'
    assert set(c.confidence.unique())<={'high','medium','low'}
def test_every_unit_covered():
    m17=pd.read_csv(os.path.join(OUT,'unit_master_2017_all.csv')); m23=pd.read_csv(os.path.join(OUT,'unit_master_2023_all.csv'))
    c=pd.read_csv(os.path.join(OUT,'crosswalk_tehsil_2017_to_2023.csv'))
    assert c.unit_id_2023.nunique()==590 and c.unit_id_2017.nunique()==535
    c98=pd.read_csv(os.path.join(OUT,'crosswalk_tehsil_1998_to_2023.csv')); assert c98.unit_id_2023.nunique()==590 and c98.unit_id_1998.nunique()==424
    cd=pd.read_csv(os.path.join(OUT,'crosswalk_tehsil_1998census_to_2023.csv')); assert cd.unit_id_2023.nunique()==590 and cd.unit_id_1998census.nunique()==417
def test_population_panel_reproduces_pbs_district_rows():
    p=pd.read_csv(os.path.join(OUT,'population_panel_2023_frame_districts.csv'))
    assert np.allclose(p.pop_2017,p.pop_2017_pbs_district_row) and np.allclose(p.pop_2023,p.pop_2023_pbs_district_row)
def test_historical_weights():
    for f in ['crosswalk_district_historical_to_1998.csv','crosswalk_district_historical_to_2023.csv']:
        c=pd.read_csv(os.path.join(OUT,f)); assert np.allclose(c.groupby(['census_year','historical_district']).weight.sum(),1,atol=1e-9)
def test_census_day_transcriptions_add_up():
    R=os.path.join(ROOT,'raw','census1998_frames','transcribed')
    for f,leaf in [('pub161_table5_sindh.csv','taluka'),('pub161_table2_nwfp_table3_fata.csv','tehsil')]:
        t=pd.read_csv(os.path.join(R,f)); d=t[t.tier=='district'].set_index('district').pop_1998; s=t[t.tier==leaf].groupby('district').pop_1998.sum()
        common=s.index.intersection(d.index); assert (s[common]==d[common]).all(), f
    b=pd.read_csv(os.path.join(R,'pub161_table6_balochistan.csv')); bt=b[b.tier=='tehsil']; nested=bt[bt.notes.fillna('').str.startswith('under')]
    assert (nested.groupby('district').pop_1998.sum()==b[b.tier=='district'].set_index('district').pop_1998.reindex(nested.groupby('district').pop_1998.sum().index)).all()
def test_codebook_covers_every_column():
    cb=pd.read_csv(os.path.join(ROOT,'docs','codebook.csv'))
    for f in glob.glob(os.path.join(OUT,'*.csv')):
        cols=set(pd.read_csv(f,nrows=1).columns); assert cols<=set(cb[cb.file==os.path.basename(f)].column), os.path.basename(f)
def test_checksums_match_files():
    bad=[]
    for line in open(os.path.join(OUT,'CHECKSUMS.sha256')):
        h,f=line.strip().split('  ',1); p=os.path.join(ROOT,f)
        if f.startswith('docs/') and f.endswith('.md'): continue   # generated notes carry the build date
        if hashlib.sha256(open(p,'rb').read()).hexdigest()!=h: bad.append(f)
    assert not bad, bad
