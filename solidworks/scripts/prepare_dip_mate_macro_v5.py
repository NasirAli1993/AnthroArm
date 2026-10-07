"""Stage DIP V5: saved-output preflight, close native docs, then existing ZIP."""
from pathlib import Path
import hashlib, json, re

root = Path(r'D:\RoboticArm\solidworks\scripts')
source = (root / 'AutoDIPMateV4.bas').read_text(encoding='ascii')
source = source.replace('AutoDIPMateV4', 'AutoDIPMateV5')
audit = json.loads((root / 'AutoDIPMateV4_source_audit.json').read_text())
required = audit['packaging_required_filenames']
required_vb = ', '.join('"' + n + '"' for n in required)
close_helper = '''Private Sub CloseSavedDocumentsBeforeArchive()
    Dim fso As Object, required As Variant, filename As Variant
    Dim closeResult As Boolean, remaining As SldWorks.ModelDoc2
    Set fso = CreateObject("Scripting.FileSystemObject")
    required = Array(__REQUIRED__)
    For Each filename In required
        Check (fso.FileExists(outputFolder & CStr(filename)) <> False), "Missing saved result before close: " & CStr(filename)
        Check FileLen(outputFolder & CStr(filename)) > 0, "Empty saved result before close: " & CStr(filename)
    Next filename
    LogLine "SAVED_DELIVERABLE_PREFLIGHT_PASS: two parts, five assemblies, CSV and log"
    LogLine "CLOSE_ALL_DOCUMENTS_BEGIN IncludeUnsaved=True; dedicated project trial; no automatic save requested"
    closeResult = swApp.CloseAllDocuments(True)
    LogLine "CLOSE_ALL_DOCUMENTS_RETURN=" & CStr(closeResult)
    Check (closeResult <> False), "CloseAllDocuments failed; do not archive potentially locked native files"
    Set remaining = swApp.GetFirstDocument()
    Check remaining Is Nothing, "A native CAD document remains open after CloseAllDocuments"
    LogLine "NO_OPEN_CAD_DOCUMENTS_VERIFIED; beginning ZIP of saved results"
End Sub

'''.replace('__REQUIRED__', required_vb)
source = source.replace('Private runtimeLog As String, logReady As Boolean',
    'Private runtimeLog As String, logReady As Boolean\nPrivate currentStage As String')
source = source.replace('Public Sub main()', close_helper + 'Public Sub main()', 1)
source = source.replace('    zipPath = PackageNativeOutput(outputFolder, folder)',
    '    currentStage = "CLOSE_SAVED_DOCUMENTS"\n'
    '    CloseSavedDocumentsBeforeArchive\n'
    '    currentStage = "PACKAGE_SAVED_RESULTS"\n'
    '    zipPath = PackageNativeOutput(outputFolder, folder)', 1)
for old, new in {
    '        ImportOne i, folder, outputFolder':
        '        currentStage = "IMPORT " & linkNames(i)\n        ImportOne i, folder, outputFolder',
    '        MakeDatums i':
        '        currentStage = "DATUMS " & linkNames(i)\n        MakeDatums i',
    '    BuildAssembly template':
        '    currentStage = "BUILD_HINGE_ASSEMBLY"\n    BuildAssembly template',
    '    AddDrivenAngle':
        '    currentStage = "CREATE_DRIVEN_ANGLE"\n    AddDrivenAngle',
    '    SweepAndLimit':
        '    currentStage = "MEASURE_SWEEPS_AND_CONFIGURE_LIMIT"\n    SweepAndLimit',
    '    LogLine "FAIL " & CStr(failNumber) & " | " & failText':
        '    LogLine "FAIL_STAGE=" & currentStage\n    LogLine "FAIL " & CStr(failNumber) & " | " & failText',
}.items():
    assert old in source, old
    source = source.replace(old, new)
# These checks improve failure attribution without relaxing geometry/mate gates.
source = source.replace('    Set angle = angleFeature.GetDefinition\n',
    '    Set angle = angleFeature.GetDefinition\n    Check Not angle Is Nothing, "Angle GetDefinition returned Nothing"\n')
source = source.replace('    Set concentric = concentricFeature.GetDefinition\n',
    '    Set concentric = concentricFeature.GetDefinition\n    Check Not concentric Is Nothing, "Concentric GetDefinition returned Nothing"\n')
source = source.replace('    Set selectedFeature = assyModel.SelectionManager.GetSelectedObject6(1, 1)\n',
    '    Set selectedFeature = assyModel.SelectionManager.GetSelectedObject6(1, 1)\n'
    '    Check Not selectedFeature Is Nothing, "Parent selected plane feature unavailable"\n')
source = source.replace('    Set selectedFeature = assyModel.SelectionManager.GetSelectedObject6(2, 1)\n',
    '    Set selectedFeature = assyModel.SelectionManager.GetSelectedObject6(2, 1)\n'
    '    Check Not selectedFeature Is Nothing, "Child selected plane feature unavailable"\n')
source = source.replace('    Set planes(0) = selectedFeature.GetSpecificFeature2\n',
    '    Set planes(0) = selectedFeature.GetSpecificFeature2\n'
    '    Check Not planes(0) Is Nothing, "Parent RefPlane unavailable"\n')
source = source.replace('    Set planes(1) = selectedFeature.GetSpecificFeature2\n',
    '    Set planes(1) = selectedFeature.GetSpecificFeature2\n'
    '    Check Not planes(1) Is Nothing, "Child RefPlane unavailable"\n')
assert 'Set comp.Transform2 =' not in source
assert 'If condition = False Then' in source
assert 'Check (result <> False)' in source
main = source.split('Public Sub main()', 1)[1]
assert main.index('CheckBodyCount importedModels(1)') < main.index('CloseSavedDocumentsBeforeArchive')
assert main.index('CloseSavedDocumentsBeforeArchive') < main.index('zipPath = PackageNativeOutput')
assert max(map(len, source.splitlines())) < 1024
for ext, text in [('bas', source), ('swb', source.split('\n', 1)[1])]:
    (root / ('AutoDIPMateV5.' + ext)).write_bytes(
        text.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii'))

def helper(code, name):
    return re.search(r'^Private Function ' + name + r'\b[\s\S]*?^End Function$', code, re.M).group(0)
v4 = (root / 'AutoDIPMateV4.bas').read_text(encoding='ascii')
assert helper(source, 'PackageNativeOutput') == helper(v4, 'PackageNativeOutput')
audit['files'] = [{'name': p.name, 'bytes': p.stat().st_size,
                   'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                  for p in [root / 'AutoDIPMateV5.bas', root / 'AutoDIPMateV5.swb']]
audit['checks']['max_line_length'] = max(map(len, source.splitlines()))
audit['checks']['saved_output_preflight_before_close'] = True
audit['checks']['close_result_normalized_and_no_documents_readback'] = True
audit['checks']['packaging_helper_identical_to_v4'] = True
audit['packaging_status'] = 'V4_HELPER_REUSED_UNCHANGED_V5_NATIVE_EXECUTION_NOT_RUN'
audit['v5_execution_status'] = 'SOURCE_AUDIT_ONLY_NO_NEW_EXECUTION_TEST_CLAIM'
audit['native_mate_risks_to_observe'] = [
    {'stage': 'DATUMS', 'risk': 'Native plane transform convention or offset direction differs from expected template',
     'gate': 'Unique native plane match and measured axis endpoints at x=0, z=0.024 m parent / z=0 child; stop if mismatch'},
    {'stage': 'BUILD_HINGE_ASSEMBLY', 'risk': 'Imported analytic bore, assembly-context face mapping or qualified datum selection fails',
     'gate': 'Geometry-derived 1.2-mm-radius Y-axis bore; owning-component readback; non-null mate features; clean rebuild'},
    {'stage': 'CREATE_DRIVEN_ANGLE', 'risk': 'Reference-plane API selection, direction reference or angle branch differs natively',
     'gate': 'Assembly-context RefPlane objects; explicit direction mark; actual signed +10-degree readback, one documented FlipDimension attempt'},
    {'stage': 'MEASURE_SWEEPS_AND_CONFIGURE_LIMIT', 'risk': 'Zero-angle branch, repeated solve or standard-to-limit conversion fails',
     'gate': 'Keep driven and limited checkpoints separate; feature error/readback and measured transform checks; no claiming endpoint enforcement'},
    {'stage': 'CLOSE_SAVED_DOCUMENTS / PACKAGE_SAVED_RESULTS', 'risk': 'Native documents remain open or external process still locks a saved file',
     'gate': 'Nine-file preflight, explicit CloseAllDocuments result and GetFirstDocument Nothing, then complete ZIP entry reads'},
]
(root / 'AutoDIPMateV5_source_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
readme = (root / 'AutoDIPMateV4_README.txt').read_text(encoding='ascii')
readme = readme.replace('AutoDIPMateV4', 'AutoDIPMateV5')
readme = readme.replace('V4 ZIP EXPORT\n', 'V5 DOCUMENT CLOSE BEFORE ZIP\n'
    'Native full-arm packaging exposed file locks while CAD documents remain\n'
    'open. After the DIP checks and all saves complete, V5 verifies that all\n'
    'nine named results exist and are nonempty, then calls CloseAllDocuments\n'
    '(True). It normalizes the return and checks GetFirstDocument is Nothing\n'
    'before archiving. This closes documents in the dedicated project trial;\n'
    'the API does not auto-save unsaved edits. All result saves precede it.\n'
    'The unchanged V4 archive helper then creates the ZIP. Native models will\n'
    'be closed when success is shown; reopen a saved checkpoint after download.\n'
    'V4 remains unchanged. V5 has a source audit only: no compile, native test\n'
    'or close-and-package execution is claimed. Earlier V4 dummy packaging\n'
    'fixture evidence does not validate this new native close step.\n'
    'Failure logs now include the current stage and null mate/plane readbacks.\n\n'
    'V4 ZIP EXPORT\n', 1)
readme = readme.replace('run this V4 version', 'run this V5 version')
readme += ('\nOfficial CloseAllDocuments API:\n'
    'https://help.solidworks.com/2021/english/api/sldworksapi/'
    'SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISldWorks~CloseAllDocuments.html\n')
readme += '''
NATIVE RUN TRIAGE - EXPECTED RISKS, NOT OBSERVED DIP FAILURES
DATUMS: inspect FIND_PLANE and DATUM_AXIS logs. An origin/normal/offset mismatch
must be corrected from actual native measurements; never relax the axis gate.
BUILD_HINGE_ASSEMBLY: inspect the qualified reference name and selected owner,
then the analytic bore face. Native face numbering is intentionally unused.
CREATE_DRIVEN_ANGLE: inspect the two RefPlanes and parent direction axis. The
actual signed +10-degree transform establishes branch direction; one logged
FlipDimension correction is allowed. A dimension value alone is not evidence.
SWEEPS/LIMIT: zero-angle degeneracy or conversion may fail even after a valid
10-degree pose. Preserve separate driven checkpoints and the full partial CSV;
do not call a partial sweep complete or a configured limit physically tested.
CLOSE/ZIP: any close result failure, remaining CAD document or archive read
failure stops packaging. Saved native outputs remain available for manual
Close All and the archive-only fallback. Never overwrite a prior ZIP.
Next native priority is compile, two-part import/datums, hinge mates, measured
10-degree pose, repeated zero return, then limit configuration and ZIP. Capture
the failing statement and FAIL_STAGE immediately if the run stops.
'''
(root / 'AutoDIPMateV5_README.txt').write_text(readme, encoding='ascii')
print(json.dumps(audit, indent=2))
