"""SHA-256 of every file in output/ (except this list, the run log and step logs) and docs/, so a rebuilt package can
be compared with the released one: sha256sum -c output/CHECKSUMS.sha256"""
import hashlib, glob, os
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(os.path.join(HERE,'..'))
files=sorted(f for f in glob.glob('output/**/*',recursive=True)+glob.glob('docs/*') if os.path.isfile(f) and not f.endswith(('CHECKSUMS.sha256','RUN_LOG.txt')) and '/logs/' not in f and not os.path.basename(f).startswith('log_'))
with open('output/CHECKSUMS.sha256','w') as o:
    for f in files: o.write(f"{hashlib.sha256(open(f,'rb').read()).hexdigest()}  {f}\n")
print('checksums written for',len(files),'files')
