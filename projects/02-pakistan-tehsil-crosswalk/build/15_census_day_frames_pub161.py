"""Text extract of the scanned PCO Census Publication 161 (January 2002, frame "as on 1st March 1998"),
the census-day counterpart of the PBS web retabulation used as this project's 1998 frame.

The PDF's OCR layer is poor (district headers and digits are often garbled), so this script only
 1. runs pdftotext and saves the text (raw/census1998_frames/national/pub161_text_extract.txt);
 2. pulls out candidate tehsil / taluka / sub-division / district / agency lines with a best-effort
    reading of the 1998 column, into output/UNVERIFIED_ocr_extract_pub161_tehsil_lines.csv.
Nothing from this file is used in any crosswalk. It exists to make the transcription of Tables 2, 3,
5 and 6 (Sindh, NWFP, FATA, Balochistan; about 240 tehsil rows) a checking job rather than a typing
job: the district totals, which are identical in both frames, are the check. Punjab's census-day frame
comes from the Punjab Government table instead (build/14).
"""
import re, subprocess, sys, pandas as pd, numpy as np
sys.path.insert(0,'build'); from crosswalk_lib import solve_group, namematch, base
PDF='raw/census1998_frames/national/pco_population_of_admin_units_1998/PCO_Population_of_Administrative_Units_1998.pdf'
TXT='raw/census1998_frames/national/pub161_text_extract.txt'
subprocess.run(['pdftotext','-layout',PDF,TXT],check=True)
lines=open(TXT,errors='ignore').read().split('\n')
# table ranges (1-based line numbers found by inspection of the extract): Table 2 NWFP, 3 FATA, 4 Punjab, 5 Sindh, 6 Balochistan
def find(pat):
    for i,l in enumerate(lines):
        if re.search(pat,l): return i
    return None
start={'KHYBER PAKHTUNKHWA':find(r'TABLE-2'),'FATA':find(r'TABLE-3'),'PUNJAB':find(r'TABLE-4'),'SINDH':find(r'TABLE-5'),'BALOCHISTAN':find(r'TABLE-6'),'END':find(r'TABLE-\?|TABLE-7')}
order=['KHYBER PAKHTUNKHWA','FATA','PUNJAB','SINDH','BALOCHISTAN','END']
TIER=r'(Taluka|Tehsil|Tehs[il1]l|Sub-?\s?Division|Sub-?\s?Tehsil|Sub-?\s?Teshil|T\.?\s?A\.?\s?Adj\.?|F\.?\s?R\.?|Protected Area|Agency|AGENCY|DISTRICT|District|D[1l]strict|DIVISION)'
def fixnum(tok):
    t=tok.replace(' ','').replace(',','').replace('.','')
    t=t.replace('l','1').replace('I','1').replace('!','1').replace(']','1').replace('|','1').replace('O','0').replace('o','0').replace('S','5').replace('B','8').replace('_','').replace('-','').replace('(','').replace(')','').replace('~','')
    return int(t) if t.isdigit() else None
rows=[]
for pi,prov in enumerate(order[:-1]):
    a,b=start[prov],start[order[pi+1]]
    if a is None or b is None: continue
    district=None
    for raw in lines[a:b]:
        l=raw.rstrip()
        if not l.strip() or re.match(r'\s*(Rural|Urban|l!rban|Urhan|TABLE|NAME|ADMIN)',l.strip(),re.I): continue
        m=re.match(r'^\s*(?P<name>[A-Za-z!:\.\\][A-Za-z\.\'\-!:\\"\(\)\{\}\[\]\|\d ]{1,40}?\s'+TIER+r')\s+(?P<rest>.*)$',l)
        if not m:
            # district headers whose name OCR mangled: a mostly-uppercase line ending in DISTRICT / AGENCY followed by numbers
            m2=re.match(r'^\s*(?P<name>.{2,40}?(DISTRICT|AGENCY))\s+(?P<rest>[\d\s\.\,\*\#\-!lIO\'\"]+)$',l)
            if m2 and sum(c.isupper() for c in m2.group('name'))>=len(re.sub(r'[^A-Za-z]','',m2.group('name')))*0.6: m=m2
            else: continue
        name=re.sub(r'\s+',' ',m.group('name')).strip(); rest=m.group('rest')
        # numeric tokens: groups separated by 2+ spaces; last one is 1998
        toks=[t for t in re.split(r'\s{2,}',rest.strip()) if t]
        nums=[fixnum(t) for t in toks]
        p98=nums[-1] if nums else None
        tier=re.search(TIER,name).group(1)
        is_dist=bool(re.search(r'DISTRICT|AGENCY',name)) and not re.search(r'T\.?\s?A\.?\s?Adj|F\.?\s?R',name)
        if is_dist:
            district=name; rows.append(dict(province=prov,district=district,unit=name,tier='district',pop_1998_ocr=p98,line=l.strip()[:120])); continue
        if 'DIVISION' in name.upper() and name.isupper(): continue
        rows.append(dict(province=prov,district=district,unit=name,tier=tier,pop_1998_ocr=p98,line=l.strip()[:120]))
F=pd.DataFrame(rows)
F=F[F.province!='PUNJAB']        # Punjab handled from the clean Punjab Government table
F.to_csv('output/UNVERIFIED_ocr_extract_pub161_tehsil_lines.csv',index=False)
print('extracted rows by province:',F.groupby('province').size().to_dict())
