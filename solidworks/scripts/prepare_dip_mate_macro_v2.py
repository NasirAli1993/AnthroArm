"""Preserve DIP V1; generate staged V2 with native-discovered BOOL fixes."""
from pathlib import Path

root = Path(r'D:\RoboticArm\solidworks\scripts')
source = (root / 'prepare_dip_mate_macro.py').read_text(encoding='ascii')
source = source.replace('AutoFullArmStaticV2', 'AutoFullArmStaticV3')
source = source.replace('AutoDIPMateV1', 'AutoDIPMateV2')
repairs = {
    'Check Not comp.IsFixed,': 'Check (comp.IsFixed = False),',
    'Check comp.IsFixed,': 'Check (comp.IsFixed <> False),',
    'Check Not concentric.LockRotation,': 'Check (concentric.LockRotation = False),',
    'Check Not components(1).IsFixed,': 'Check (components(1).IsFixed = False),',
    'Check Not angle.IsAdvancedMate,': 'Check (angle.IsAdvancedMate = False),',
    'Check angle.IsAdvancedMate,': 'Check (angle.IsAdvancedMate <> False),',
    'angle.FlipDimension = Not angle.FlipDimension':
        'angle.FlipDimension = (angle.FlipDimension = False)',
}
for old, new in repairs.items():
    assert old in source, old
    source = source.replace(old, new)
exec(compile(source, str(root / 'prepare_dip_mate_macro.py'), 'exec'))

result = (root / 'AutoDIPMateV2.bas').read_text(encoding='ascii')
assert 'If condition = False Then' in result
assert 'Check (result <> False)' in result
assert 'Check (errors = 0)' in result
assert 'If Not condition Then' not in result
assert 'Check Not comp.IsFixed' not in result
assert 'Check Not components(1).IsFixed' not in result
assert 'Check Not angle.IsAdvancedMate' not in result
assert '= Not angle.FlipDimension' not in result
readme = (root / 'AutoDIPMateV1_README.txt').read_text(encoding='ascii')
readme = readme.replace('AutoDIPMateV1', 'AutoDIPMateV2')
readme = readme.replace('PURPOSE\n', 'V2 FIX\n'
    'Uses explicit zero/nonzero Boolean comparisons for native COM returns.\n'
    'Native V2 full-arm execution showed SaveAs success, zero errors, and an\n'
    'incorrect failure from bitwise Not applied to a noncanonical true value.\n'
    'This repair changes only result interpretation, not geometry acceptance.\n'
    'DIP V1 remains preserved; run this V2 version for the native finger test.\n\n'
    'PURPOSE\n', 1)
(root / 'AutoDIPMateV2_README.txt').write_text(readme, encoding='ascii')
