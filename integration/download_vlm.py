"""Download only a pinned official safetensors model, with all writes on D:."""
from pathlib import Path
import urllib.request,json,hashlib,time
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'models'/'SmolVLM-256M-Instruct';DEST.mkdir(parents=True,exist_ok=True)
REPO='HuggingFaceTB/SmolVLM-256M-Instruct'
REV='7e3e67edbbed1bf9888184d9df282b700a323964'
with urllib.request.urlopen('https://huggingface.co/api/models/'+REPO+'/revision/'+REV+'?blobs=true',timeout=60) as r:meta=json.load(r)
manifest={'repo':REPO,'revision':REV,'files':[]}
for entry in meta['siblings']:
    name=entry['rfilename']
    if '/' in name or name=='.gitattributes':continue
    path=DEST/name;url=f'https://huggingface.co/{REPO}/resolve/{REV}/{name}'
    expected=entry.get('lfs',{}).get('sha256')
    if not path.exists() or (expected and hashlib.sha256(path.read_bytes()).hexdigest()!=expected):
        for attempt in range(3):
            try:
                print('Downloading '+name,flush=True)
                with urllib.request.urlopen(url,timeout=120) as r, path.with_suffix(path.suffix+'.part').open('wb') as f:
                    while chunk:=r.read(1024*1024):f.write(chunk)
                path.with_suffix(path.suffix+'.part').replace(path);break
            except Exception:
                if attempt==2:raise
                time.sleep(2)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if expected and digest!=expected:raise RuntimeError('SHA256 mismatch: '+name)
    manifest['files'].append({'name':name,'bytes':path.stat().st_size,'sha256':digest,'lfs_hash_verified':bool(expected)})
(DEST/'download_manifest.json').write_text(json.dumps(manifest,indent=2))
print('Pinned model download verified',flush=True)
