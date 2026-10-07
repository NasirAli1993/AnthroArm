"""Preserve V5; reselect parent immediately before FixComponent, as Full V6."""
from pathlib import Path
import json, hashlib

root = Path(r'D:\RoboticArm\solidworks\scripts')
source = (root / 'AutoDIPMateV5.bas').read_text(encoding='ascii')
source = source.replace('AutoDIPMateV5', 'AutoDIPMateV6')
old = '''        comp.Transform2 = t
        If i = 0 Then
            assy.FixComponent
'''
new = '''        comp.Transform2 = t
        If i = 0 Then
            ' Re-establish selection after transform, matching proven full-arm V6.
            assyModel.ClearSelection2 True
            Check comp.Select4(False, Nothing, False), "Cannot reselect parent for fixing"
            assy.FixComponent
'''
assert source.count(old) == 1
source = source.replace(old, new, 1)
for ext, content in [('bas', source), ('swb', source.split('\n', 1)[1])]:
    (root / ('AutoDIPMateV6.' + ext)).write_bytes(
        content.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii'))
audit = json.loads((root / 'AutoDIPMateV5_source_audit.json').read_text())
audit['files'] = [{'name': p.name, 'bytes': p.stat().st_size,
                   'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                  for p in [root / 'AutoDIPMateV6.bas', root / 'AutoDIPMateV6.swb']]
audit['v6_status'] = 'NATIVE_NOT_EXECUTED_SOURCE_FIX_ONLY'
audit['v5_execution_status'] = 'NATIVE_EXECUTED_STOPPED_AT_PARENT_FIXCOMPONENT_BEFORE_MATE_CREATION'
audit['v6_only_behavior_change'] = 'Clear selections and reselect parent after Transform2, immediately before FixComponent; matches native-successful full-arm V6 sequence'
audit['v5_observed_native_failure'] = 'Parent component did not become fixed; root screenshot dip_v5_native_attempt.png shows first component floating'
audit['v6_other_native_operations'] = 'UNCHANGED_FROM_V5'
(root / 'AutoDIPMateV6_source_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
readme = (root / 'AutoDIPMateV5_README.txt').read_text(encoding='ascii').replace('AutoDIPMateV5', 'AutoDIPMateV6')
readme = readme.replace('V5 DOCUMENT CLOSE BEFORE ZIP\n', 'V6 PARENT FIXING REPAIR\n'
    'Native V5 reached assembly creation but stopped because the parent stayed\n'
    'floating. V6 clears selection and explicitly selects that component again\n'
    'after setting Transform2, immediately before FixComponent. This matches\n'
    'the successful native full-arm V6 sequence. No other native operation is\n'
    'changed. V5 is preserved; V6 native execution has not yet been performed.\n\n'
    'V5 DOCUMENT CLOSE BEFORE ZIP\n', 1)
readme = readme.replace('run this V5 version', 'run this V6 version')
(root / 'AutoDIPMateV6_README.txt').write_text(readme, encoding='ascii')
print(json.dumps(audit['files'], indent=2))
