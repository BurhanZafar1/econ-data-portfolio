"""SHA-256 of every file in output/ and docs/ (except this list and the run log), so a rebuilt package can be
compared with the released one: sha256sum -c output/CHECKSUMS.sha256"""
import hashlib, glob, os
files=sorted(f for f in glob.glob('output/**/*',recursive=True)+glob.glob('docs/*') if os.path.isfile(f) and not f.endswith(('CHECKSUMS.sha256','RUN_LOG.txt')))
with open('output/CHECKSUMS.sha256','w') as o:
    for f in files: o.write(f"{hashlib.sha256(open(f,'rb').read()).hexdigest()}  {f}\n")
print('checksums written for',len(files),'files')
