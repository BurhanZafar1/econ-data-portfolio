"""Combine the per-province event registers (web-sourced, build/intermediate/events/events_*.csv)
into output/event_register.csv and write docs/EVENT_REGISTER.md.
Every dated row carries the URL that was read and a confidence grade; rows the research could not
date are kept with confidence 'unverified' and a blank year, so the register says what is not known."""
import pandas as pd, numpy as np, glob, re
OUT='output/'
cols=['province','level','event_type','unit_name','parent_or_source_units','new_or_destination_units','year','date','interval','notes','source_url','source_title','confidence']
first=[f for f in sorted(glob.glob('build/intermediate/events/events_*.csv')) if 'pass2' not in f]
E=pd.concat([pd.read_csv(f) for f in first],ignore_index=True)[cols]
# second research pass: replaces a first-pass row (same province and unit_name) when it dated the event or raised its grade
P2=pd.concat([pd.read_csv(f) for f in sorted(glob.glob('build/intermediate/events/events_*_pass2.csv'))],ignore_index=True)[cols]
rank={'verified':2,'reported':1,'unverified':0}
E['_k']=E.province.str.upper()+'|'+E.unit_name.str.upper().str.strip(); P2['_k']=P2.province.str.upper()+'|'+P2.unit_name.str.upper().str.strip()
replaced=0
for k,r in P2.set_index('_k').iterrows():
    idx=E.index[(E._k==k)&(E.level=='tehsil')]
    if len(idx)==0: continue
    cur=E.loc[idx[0]]
    if rank.get(str(r.confidence).strip().lower(),0)>rank.get(str(cur.confidence).strip().lower(),0) or (pd.isna(cur.year) and not pd.isna(r.year)):
        for c in cols: E.loc[idx[0],c]=r[c]
        E.loc[idx[0],'notes']=str(r['notes'])+' (second research pass)'; replaced+=1
    elif str(r.confidence).strip().lower()=='unverified' and isinstance(r['notes'],str) and len(r['notes'])>20:
        E.loc[idx[0],'notes']=str(cur['notes'])+' Second pass: '+r['notes']
E=E.drop(columns='_k'); print('second pass replaced',replaced,'rows')
E['unit_name']=E.unit_name.str.replace(r'\s*\(not in input\)','',regex=True).str.strip()
isnote=E.unit_name.str.contains('FRAME NOTE|reference row',case=False,regex=True)
E.loc[isnote,['level','event_type']]=['note','note']
E['year']=pd.to_numeric(E.year,errors='coerce').astype('Int64')
E['confidence']=E.confidence.str.strip().str.lower().replace({'reported ':'reported'})
assert E.confidence.isin(['verified','reported','unverified']).all(), E.confidence.unique()
# which events are visible between two census frames in the crosswalk tables
def norm(s): return re.sub(r'\s+',' ',re.sub(r'\(.*?\)','',str(s)).upper()).strip()
d17=set(pd.read_csv(OUT+'unit_master_2017_all.csv').district.map(norm)); d23=set(pd.read_csv(OUT+'unit_master_2023_all.csv').district.map(norm))
u17=set(pd.read_csv(OUT+'unit_master_2017_all.csv').unit.map(norm)); u23=set(pd.read_csv(OUT+'unit_master_2023_all.csv').unit.map(norm))
def in_cw(r):
    n=norm(r.unit_name)
    if r.level=='district':
        if r.event_type in ('new_district','tehsil_upgraded_to_district'): return 'yes' if (n in d17 or n in d23) else 'no (not a separate unit in the census tables)'
        if r.event_type=='district_transfer': return 'yes (as a population flow between the two frames)'
        return 'n/a'
    if r.event_type=='new_tehsil': return 'yes' if (n in u17 or n in u23) else 'no (not in the census tables)'
    return 'n/a'
E['in_crosswalk']=E.apply(in_cw,axis=1)
E=E.sort_values(['province','level','year','unit_name'],na_position='last').reset_index(drop=True)
E.to_csv(OUT+'event_register.csv',index=False)
# ---- markdown summary
L=['# Event register: dated district and tehsil changes, 1998 to 2026\n',
   'Professor Khan asked for the changes in the years they happened, not just at the three censuses. This register lists every district change the crosswalk detected between census frames, every new tehsil, and the districts notified after the 2017 census, each with the year, the source that was read, and a grade: **verified** (an official notification or two independent news reports), **reported** (one news report or a Wikipedia page that cites one), **unverified** (nothing found; the year is blank rather than guessed).\n',
   'The weights in the crosswalk tables exist only between census frames, because only there did PBS publish populations on both old and new boundaries. The register dates the changes; it does not add weights for in-between years. A user who needs, say, the 2010 district frame can take the 1998 -> 2017 table and keep only the changes dated 2010 or earlier, using the lineage table to see which tehsils each new district took.\n',
   '## Counts']
c=E[E.level!='note'].groupby(['province','level']).size().unstack(fill_value=0); c['total']=c.sum(axis=1)
L.append('| Province | district rows | tehsil rows | total |'); L.append('|---|---|---|---|')
for p,r in c.iterrows(): L.append(f"| {p} | {r.get('district',0)} | {r.get('tehsil',0)} | {r.total} |")
cc=E.confidence.value_counts()
L.append(f"\nConfidence over all {len(E)} rows: verified {cc.get('verified',0)}, reported {cc.get('reported',0)}, unverified {cc.get('unverified',0)}. Of the district-level rows, {int(((E.level=='district')&(E.confidence!='unverified')).sum())} of {int((E.level=='district').sum())} are dated.\n")
L.append('## District-level changes')
L.append('| Province | Change | Unit | From | Year | Date | In crosswalk | Grade | Note |'); L.append('|---|---|---|---|---|---|---|---|---|')
for _,x in E[E.level=='district'].iterrows():
    L.append(f"| {x.province} | {x.event_type} | {x.unit_name} | {x.parent_or_source_units} | {'' if pd.isna(x.year) else int(x.year)} | {'' if pd.isna(x.date) else x.date} | {x.in_crosswalk} | {x.confidence} | {str(x.notes).replace('|','/')} |")
L.append('\n## Tehsil-level changes')
L.append('| Province | District | Change | Unit | From | Year | Grade | Note |'); L.append('|---|---|---|---|---|---|---|---|')
for _,x in E[E.level=='tehsil'].iterrows():
    L.append(f"| {x.province} | {x.new_or_destination_units if x.event_type!='new_tehsil' else ''} | {x.event_type} | {x.unit_name} | {x.parent_or_source_units} | {'' if pd.isna(x.year) else int(x.year)} | {x.confidence} | {str(x.notes).replace('|','/')} |")
L.append('\n## Notes on the census frames')
for _,x in E[E.level=='note'].iterrows(): L.append(f"- {x.province}: {x.notes}")
L.append('\nSources for every row are in output/event_register.csv (columns source_url, source_title).')
open('docs/EVENT_REGISTER.md','w').write('\n'.join(L)+'\n')
print(len(E),'rows;',cc.to_dict()); print(c)
