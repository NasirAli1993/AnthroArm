"""Prepare explicit CAD-only upload sets; no upload or native test is performed."""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path('D:/RoboticArm/solidworks')
transfer = root / 'transfer'
out = root / 'project' / 'trial_upload'
out.mkdir(parents=True, exist_ok=True)

sets = {
    '01_index_DIP_import_test.zip': [
        transfer / 'links/index_intermediate.step',
        transfer / 'links/index_distal.step',
    ],
    '02_complete_arm_CAD.zip': [
        transfer / 'full_arm_home_reference.step',
        *sorted((transfer / 'links').glob('*.step')),
    ],
}
inventory = {'scope': 'Local packaging only. No CAD has been uploaded and no SOLIDWORKS native test has run.', 'packages': []}
for name, paths in sets.items():
    destination = out / name
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in paths:
            z.write(path, path.relative_to(transfer).as_posix())
    with zipfile.ZipFile(destination) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(paths)
    inventory['packages'].append({
        'file': destination.name,
        'bytes': destination.stat().st_size,
        'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
        'source_files': [p.relative_to(transfer).as_posix() for p in paths],
        'zip_integrity': 'PASS',
    })
(out / 'upload_inventory.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
print(json.dumps([{k:v for k,v in package.items() if k != 'source_files'} for package in inventory['packages']], indent=2))
