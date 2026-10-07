from pathlib import Path
import json, platform, importlib.metadata, hashlib, sys, os
ROOT=Path(__file__).resolve().parents[1]
packages={d.metadata['Name']:d.version for d in importlib.metadata.distributions() if d.metadata['Name']}
report={'python':sys.version,'python_executable':sys.executable,'platform':platform.platform(),'packages':packages,'downloads':[],
 'project_root':str(ROOT),'temporary_directory':os.environ.get('TEMP'),'cache':os.environ.get('PIP_CACHE_DIR')}
for p in sorted((ROOT/'downloads').iterdir()):
    if p.is_file():
        h=hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
        report['downloads'].append({'name':p.name,'bytes':p.stat().st_size,'sha256':h.hexdigest()})
(ROOT/'results'/'environment.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(ROOT/'software'/'requirements-lock.txt').write_text('\n'.join(f'{k}=={v}' for k,v in sorted(packages.items()) if k.lower()!='opencv-python')+'\n',encoding='utf-8')
print(json.dumps({'python':sys.executable,'packages':len(packages),'download_hashes':len(report['downloads'])}))
