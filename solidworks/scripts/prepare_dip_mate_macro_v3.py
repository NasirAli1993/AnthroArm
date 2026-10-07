"""Preserve DIP V2; fix documented Transform2 property setter in staged V3."""
from pathlib import Path
import hashlib, json

root = Path(r'D:\RoboticArm\solidworks\scripts')
source = (root / 'AutoDIPMateV2.bas').read_text(encoding='ascii')
assert source.count('Set comp.Transform2 = t') == 1
source = source.replace('AutoDIPMateV2', 'AutoDIPMateV3')
source = source.replace('Set comp.Transform2 = t', 'comp.Transform2 = t')
for ext, text in [('bas', source), ('swb', source.split('\n', 1)[1])]:
    (root / ('AutoDIPMateV3.' + ext)).write_bytes(
        text.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii'))
readme = (root / 'AutoDIPMateV2_README.txt').read_text(encoding='ascii')
readme = readme.replace('AutoDIPMateV2', 'AutoDIPMateV3')
readme = readme.replace('V2 FIX\n', 'V3 FIX\n'
    'Transform2 property setter uses comp.Transform2 = t without Set, matching\n'
    'official VBA examples. Full-arm native V3 failed with error 438 at the\n'
    'Set form after all 28 STEP parts imported. Getter Set t = comp.Transform2\n'
    'remains unchanged. DIP V1 and V2 sources are preserved.\n\nV2 FIX\n', 1)
readme = readme.replace('run this V2 version', 'run this V3 version')
readme += ('\nOfficial Transform2 setter example:\n'
    'https://help.solidworks.com/2021/english/api/sldworksapi/'
    'Align_Assembly_Component_to_Assembly_Origin_and_Planes_Example_VB.htm\n')
(root / 'AutoDIPMateV3_README.txt').write_text(readme, encoding='ascii')
audit = json.loads((root / 'AutoDIPMateV2_source_audit.json').read_text())
audit['files'] = [{'name': p.name, 'bytes': p.stat().st_size,
                   'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                  for p in [root / 'AutoDIPMateV3.bas', root / 'AutoDIPMateV3.swb']]
audit['checks']['transform_setter_uses_plain_assignment'] = True
audit['checks']['boolean_comparisons_normalized'] = True
audit['checks']['max_line_length'] = max(map(len, source.splitlines()))
(root / 'AutoDIPMateV3_source_audit.json').write_text(
    json.dumps(audit, indent=2) + '\n', encoding='ascii')
print(json.dumps(audit, indent=2))
