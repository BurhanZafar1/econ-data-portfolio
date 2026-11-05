"""District crosswalk from the historical district frames of the 1951, 1961, 1972 and 1981 censuses to the
1998 frame, and on to the 2023 frame.

Inputs
 - output/population_panel_1998_frame.csv and ..._districts.csv: PCO's restatement of every census on the
   1998 frame (Census Publication 161).
 - build/intermediate/events_pre1998/lineage_*.csv: for every 1998 district, when it was created and from
   which district(s), with sources (web research, graded verified / reported / unverified).
Method
 For census year Y, a 1998 district d was either its own district (existed_Y = yes) or part of a parent
 (we follow the parent chain until a unit that existed at Y). Districts with two parents are split at the
 tehsil level (TEHSIL_PARENT below), using PCO's tehsil-level restatements. The historical district H is
 then the set of 1998 districts (or tehsils) it covered, and the crosswalk weight of d in H is
 pop_Y(d) / pop_Y(H), both PCO figures on 1998 boundaries. Where PCO printed no figure for a member
 (a dash: the people were counted inside the parent and could not be restated), the member's share is
 taken from the first later census where all members have figures and the row is flagged proxy.
Outputs
 output/crosswalk_district_historical_to_1998.csv, output/crosswalk_district_historical_to_2023.csv,
 output/district_frames_by_census.csv (which districts existed at each census, with sources).
"""
import pandas as pd, numpy as np, glob, re, json
OUT='output/'; YRS=[1951,1961,1972,1981]
P=pd.read_csv(OUT+'population_panel_1998_frame.csv'); Dp=pd.read_csv(OUT+'population_panel_1998_frame_districts.csv').set_index('district_1998')
L=pd.concat([pd.read_csv(f) for f in sorted(glob.glob('build/intermediate/events_pre1998/lineage_*.csv'))],ignore_index=True)
def nm(s):
    s=str(s).upper().strip(); s=re.sub(r'\s*\(.*\)$','',s); s=s.replace(' DISTRICT','').replace(' AGENCY','')
    return {'UPPER DIR':'UPPER DIR','DIR':'DIR'}.get(s,s)
L['k']=L.district_1998.map(nm)
L.drop(columns='k').to_csv(OUT+'district_lineage_1951_1998.csv',index=False)
dist=list(Dp.index); kd={nm(d):d for d in dist}
lin=L.set_index('k')
# historical-only units (never a 1998 unit) that act as parents
HIST_ONLY={'HAZARA':dict(members=['ABBOTTABAD','MANSEHRA','HARIPUR','BATAGRAM'],years=[1951,1961,1972],province='KHYBER PAKHTUNKHWA'),
           'DIR':dict(members=['UPPER DIR','LOWER DIR'],years=[1951,1961,1972,1981],province='KHYBER PAKHTUNKHWA'),
           'MAKRAN':dict(members=['KECH','GWADAR','PANJGUR'],years=[1951,1961,1972],province='BALOCHISTAN'),
           'QUETTA-PISHIN':dict(members=['QUETTA','PISHIN','KILLA ABDULLAH'],years=[1951,1961,1972],province='BALOCHISTAN'),
           'KACHHI':dict(members=['BOLAN','JHAL MAGSI'],years=[1972,1981],province='BALOCHISTAN')}
# overrides: parent of a 1998 district at a given census (where the lineage file's parent column cannot be used directly)
PARENT_OVERRIDE={('ABBOTTABAD',1951):'HAZARA',('ABBOTTABAD',1961):'HAZARA',('ABBOTTABAD',1972):'HAZARA',
                 ('MANSEHRA',1951):'HAZARA',('MANSEHRA',1961):'HAZARA',('MANSEHRA',1972):'HAZARA',
                 ('HARIPUR',1951):'HAZARA',('HARIPUR',1961):'HAZARA',('HARIPUR',1972):'HAZARA',('HARIPUR',1981):'ABBOTTABAD',
                 ('BATAGRAM',1951):'HAZARA',('BATAGRAM',1961):'HAZARA',('BATAGRAM',1972):'HAZARA',('BATAGRAM',1981):'MANSEHRA',
                 ('LOWER DIR',1951):'DIR',('LOWER DIR',1961):'DIR',('LOWER DIR',1972):'DIR',('LOWER DIR',1981):'DIR',
                 ('UPPER DIR',1951):'DIR',('UPPER DIR',1961):'DIR',('UPPER DIR',1972):'DIR',('UPPER DIR',1981):'DIR',
                 ('KECH',1951):'MAKRAN',('KECH',1961):'MAKRAN',('KECH',1972):'MAKRAN',('GWADAR',1951):'MAKRAN',('GWADAR',1961):'MAKRAN',('GWADAR',1972):'MAKRAN',
                 ('PANJGUR',1951):'MAKRAN',('PANJGUR',1961):'MAKRAN',('PANJGUR',1972):'MAKRAN',
                 ('QUETTA',1951):'QUETTA-PISHIN',('QUETTA',1961):'QUETTA-PISHIN',('QUETTA',1972):'QUETTA-PISHIN',
                 ('PISHIN',1951):'QUETTA-PISHIN',('PISHIN',1961):'QUETTA-PISHIN',('PISHIN',1972):'QUETTA-PISHIN',('PISHIN',1981):'PISHIN',
                 ('KILLA ABDULLAH',1951):'QUETTA-PISHIN',('KILLA ABDULLAH',1961):'QUETTA-PISHIN',('KILLA ABDULLAH',1972):'QUETTA-PISHIN',('KILLA ABDULLAH',1981):'PISHIN',
                 ('BOLAN',1972):'KACHHI',('BOLAN',1981):'KACHHI',('JHAL MAGSI',1972):'KACHHI',('JHAL MAGSI',1981):'KACHHI',
                 ('NASIRABAD',1951):'SIBI',('NASIRABAD',1961):'SIBI',('NASIRABAD',1972):'SIBI',
                 ('JAFARABAD',1951):'SIBI',('JAFARABAD',1961):'SIBI',('JAFARABAD',1972):'SIBI',('JAFARABAD',1981):'NASIRABAD',
                 ('FR LAKKI MARWAT',1951):'FR BANNU',('FR LAKKI MARWAT',1961):'FR BANNU',('FR LAKKI MARWAT',1972):'FR BANNU',('FR LAKKI MARWAT',1981):'FR BANNU',
                 ('FR TANK',1951):'FR D.I.KHAN',('FR TANK',1961):'FR D.I.KHAN',('FR TANK',1972):'FR D.I.KHAN',('FR TANK',1981):'FR D.I.KHAN',
                 ('KASUR',1951):'LAHORE CITY',('KASUR',1961):'LAHORE CITY',('KASUR',1972):'LAHORE CITY'}
# two-parent districts: which parent each 1998 tehsil belonged to
TEHSIL_PARENT={'CHAKWAL':{'TALAGANG TEHSIL':'ATTOCK','CHAKWAL TEHSIL':'JHELUM','CHOA SAIDAN SHAH TEHSIL':'JHELUM','KALLAR KAHAR TEHSIL':'JHELUM'},
               'SANGHAR':{'KHIPRO TALUKA':'THARPARKAR','SANGHAR TALUKA':'THARPARKAR','SHAHDADPUR TALUKA':'NAWAB SHAH','SINJHORO TALUKA':'NAWAB SHAH','TANDO ADAM TALUKA':'NAWAB SHAH','JAM NAWAZ ALI TALUKA':'NAWAB SHAH'},
               'KOHISTAN':{'DASSU TEHSIL':'SWAT','PATTAN TEHSIL':'HAZARA','PALAS TEHSIL':'HAZARA'}}
# how the historical unit was enumerated (where it was not an ordinary district)
STATUS={('KALAT',1951):'princely state (Balochistan States Union), enumerated as a state',('KHARAN',1951):'princely state (Balochistan States Union)',('LASBELA',1951):'princely state (Balochistan States Union)',
        ('MAKRAN',1951):'princely state (Balochistan States Union); Makran district 1955-1977',('SWAT',1951):'princely state',('SWAT',1961):'princely state',('DIR',1951):'princely state',('DIR',1961):'princely state',
        ('CHITRAL',1951):'princely state',('CHITRAL',1961):'princely state',('KHAIRPUR',1951):'princely state (Khairpur State), district from 1955',
        ('BAHAWALPUR',1951):'district of Bahawalpur State (state merged 1955)',('BAHAWALNAGAR',1951):'district of Bahawalpur State',('RAHIM YAR KHAN',1951):'district of Bahawalpur State',
        ('KARACHI CITY',1951):'Federal Capital Area in 1951, outside Sindh; one unit here as agreed',('MALAKAND PROTECTED AREA',1951):'Malakand Agency (included Bajaur until 1973)',('MALAKAND PROTECTED AREA',1961):'Malakand Agency (included Bajaur until 1973)'}
NOTES={'NASIRABAD':'sources differ on the 1974 parent (Sibi per the High Court history, Kalat per the 1998 DCR, Kachhi per Wikipedia); the Nasirabad plain was Sibi\'s Nasirabad tehsil in 1951 and 1961, so Sibi is used through 1972',
       'KOHISTAN':'west bank (Dassu, Kandia) was Swat Kohistan, east bank (Pattan, Palas) was Hazara Kohistan; assignment by tehsil follows that convention',
       'SANGHAR':'Sanghar was created in 1954 from Nawabshah (Shahdadpur, Sinjhoro) and Tharparkar (Sanghar, Khipro); Tando Adam and Jam Nawaz Ali are assigned to Nawabshah by location',
       'CHAKWAL':'Talagang tehsil came from Attock, the rest from Jhelum'}
def existed(k,y):
    if k in HIST_ONLY: return y in HIST_ONLY[k]['years']
    if k not in lin.index: return True
    v=str(lin.loc[k,f'existed_{y}']).strip().lower()
    if v=='yes': return True
    if v=='no': return False
    return not pd.isna(Dp.loc[kd[k],f'pop_{y}']) if k in kd else True   # unclear: own unit if PCO printed a figure
def parent(k,y):
    if (k,y) in PARENT_OVERRIDE: return PARENT_OVERRIDE[(k,y)]
    p=str(lin.loc[k,'parent_districts_1998_names']) if k in lin.index else ''
    ps=[nm(x) for x in p.split(';') if x.strip() and x.strip().lower()!='nan']
    return ps[0] if ps else None
def hist_unit(k,y,depth=0):
    """the unit k (1998 name) was part of at census y, following the parent chain"""
    if (k,y) in PARENT_OVERRIDE and depth<=6: return hist_unit(PARENT_OVERRIDE[(k,y)],y,depth+1)
    if existed(k,y) or depth>6: return k
    p=parent(k,y)
    if p is None or p==k: return k
    return hist_unit(p,y,depth+1)
rows=[]; frames=[]
for y in YRS:
    # (member unit, 1998 district, tehsil or None) -> historical unit
    assign=[]
    for d in dist:
        k=nm(d)
        if k in TEHSIL_PARENT and not existed(k,y):
            for t,pk in TEHSIL_PARENT[k].items():
                assign.append((d,t,hist_unit(pk,y)))
        else:
            assign.append((d,None,hist_unit(k,y)))
    A=pd.DataFrame(assign,columns=['district_1998','tehsil_1998','hist'])
    def val(d,t,col):
        if t is None or (isinstance(t,float) and np.isnan(t)): return Dp.loc[d,col]
        s=P[(P.district_1998==d)&(P.unit_1998==t)]
        assert len(s)==1,(d,t); return s[col].iloc[0]
    A['pop_y']=[val(d,t,f'pop_{y}') for d,t in zip(A.district_1998,A.tehsil_1998)]
    A['pop_1998']=[val(d,t,'pop_1998') for d,t in zip(A.district_1998,A.tehsil_1998)]
    for later in [yy for yy in YRS+[1998] if yy>y]:
        A[f'pop_{later}_ref']=[val(d,t,f'pop_{later}') for d,t in zip(A.district_1998,A.tehsil_1998)]
    for h,g in A.groupby('hist'):
        prov=Dp.loc[kd[h],'province_1998'] if h in kd else HIST_ONLY[h]['province']
        total=g.pop_y.sum(skipna=True)
        if g.pop_y.notna().all():
            w=g.pop_y/total; basis='pco_restatement_exact'; ref=None
        else:
            ref=None
            for later in [yy for yy in YRS+[1998] if yy>y]:
                if g[f'pop_{later}_ref'].notna().all(): ref=later; break
            w=g[f'pop_{ref}_ref']/g[f'pop_{ref}_ref'].sum(); basis=f'proxy_shares_from_{ref}'
        for (_,r),wi in zip(g.iterrows(),w):
            k=nm(r.district_1998)
            conf=str(lin.loc[k,'confidence']) if k in lin.index else 'verified'
            src=str(lin.loc[k,'source_url']) if k in lin.index else ''
            note='; '.join(x for x in [STATUS.get((h,y),''),NOTES.get(k,'')] if x)
            if (r.tehsil_1998 is None or (isinstance(r.tehsil_1998,float))) and len(g)==1: method='same unit'
            elif basis.startswith('proxy'): method='member had no PCO figure in this year; share taken from '+str(ref)
            else: method='PCO restated populations on 1998 boundaries'
            rows.append(dict(census_year=y,province=prov,historical_district=h,district_1998=r.district_1998,tehsil_1998=r.tehsil_1998 if isinstance(r.tehsil_1998,str) else '',
                pop_census_year_on_1998_unit=r.pop_y,pop_historical_district=total,weight=round(float(wi),6),weight_basis=basis,method=method,
                lineage_confidence=conf,lineage_source=src,note=note))
        frames.append(dict(census_year=y,province=prov,historical_district=h,status=STATUS.get((h,y),'district' if h in kd or h in HIST_ONLY else ''),n_1998_districts=g.district_1998.nunique(),members_1998='; '.join(sorted(set(g.district_1998))),population=total,all_members_have_pco_figure=bool(g.pop_y.notna().all())))
X=pd.DataFrame(rows); F=pd.DataFrame(frames)
X.to_csv(OUT+'crosswalk_district_historical_to_1998.csv',index=False); F.to_csv(OUT+'district_frames_by_census.csv',index=False)
# chain to 2023 districts
D23=pd.read_csv(OUT+'crosswalk_district_1998_to_2023.csv')[['district_1998','district_2023','province_2023','pop_weight','confidence']].rename(columns={'pop_weight':'w_1998_to_2023','confidence':'conf_1998_to_2023'})
Z=X.merge(D23,on='district_1998')
Z['weight']=Z.weight*Z.w_1998_to_2023
Z=Z.groupby(['census_year','province','historical_district','district_2023','province_2023'],as_index=False).agg(weight=('weight','sum'),pop_historical_district=('pop_historical_district','first'),weight_basis=('weight_basis',lambda s:'; '.join(sorted(set(s)))),lineage_confidence=('lineage_confidence',lambda s:'unverified' if 'unverified' in set(s) else 'reported' if 'reported' in set(s) else 'verified'),conf_1998_to_2023=('conf_1998_to_2023',lambda s:'medium' if 'medium' in set(s) else 'high'),via_1998=('district_1998',lambda s:'; '.join(sorted(set(s)))))
Z['persons_moved']=(Z.weight*Z.pop_historical_district).round(1)
Z.to_csv(OUT+'crosswalk_district_historical_to_2023.csv',index=False)
# checks
chk={}
for y in YRS:
    s=X[X.census_year==y].groupby('historical_district').weight.sum(); chk[y]=dict(historical_districts=int(F[F.census_year==y].shape[0]),weights_sum_to_1=bool(np.allclose(s,1)),
        population_allocated=float(X[X.census_year==y].drop_duplicates(['historical_district']).pop_historical_district.sum()),pco_tehsil_panel_total=float(P[f'pop_{y}'].sum()),pco_province_total_four_provinces_and_fata={1951:33644227,1961:42762709,1972:65071791,1981:83913358}[y],
        proxy_rows=int((X[(X.census_year==y)].weight_basis.str.startswith('proxy')).sum()))
    z=Z[Z.census_year==y].groupby('historical_district').weight.sum(); chk[y]['chained_weights_sum_to_1']=bool(np.allclose(z,1))
json.dump(chk,open(OUT+'validation_summary_backward.json','w'),indent=1); print(json.dumps(chk,indent=1))
print(F.groupby('census_year').size())
