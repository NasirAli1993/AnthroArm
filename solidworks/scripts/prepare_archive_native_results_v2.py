"""V2 archive recovery: close this dedicated trial's documents, then package."""
from pathlib import Path
import re,json,hashlib
ROOT=Path('D:/RoboticArm/solidworks')
S=ROOT/'scripts'
src=(S/'ArchiveNativeResultsV1.swb').read_text().replace('ArchiveNativeResultsV1','ArchiveNativeResultsV2')
src=src.replace("' Archive-only fallback: no STEP imports, geometry changes, save/rebuild or preferences.","' Archive fallback: after saved-file/log preflight, closes this dedicated trial session's documents.\n' CloseAllDocuments(True) includes dirty docs; no automatic save is performed.\n' No STEP imports, geometry changes, save/rebuild or preferences.")
src=src.replace('Dim swApp As Object, fso As Object','Dim swApp As Object, fso As Object, openDocument As Object')
src=src.replace('Dim failureNumber As Long, failureText As String','Dim failureNumber As Long, failureText As String\n    Dim closeResult As Boolean, required As Variant, filename As Variant')
names=json.loads((S/'ArchiveNativeResultsV1_source_audit.json').read_text())['required_files']
insertion='    required = Array('+', '.join('"'+n+'"' for n in names)+')\n'+r'''    For Each filename In required
        Check fso.FileExists(outputFolder & CStr(filename)) <> False, "Missing saved deliverable before closing: " & CStr(filename)
        Check FileLen(outputFolder & CStr(filename)) > 0, "Empty saved deliverable before closing: " & CStr(filename)
    Next filename
    LogLine "SAVED_DELIVERABLE_PREFLIGHT_PASS=30 files; successful native V5 build log already verified"
    LogLine "CLOSE_ALL_DOCUMENTS_BEGIN IncludeUnsaved=True; no automatic save requested"
    closeResult = swApp.CloseAllDocuments(True)
    LogLine "CLOSE_ALL_DOCUMENTS_RETURN=" & CStr(closeResult)
    Check (closeResult <> False), "CloseAllDocuments returned False; do not package potentially locked files"
    Set openDocument = swApp.GetFirstDocument()
    Check openDocument Is Nothing, "A CAD document remains open after CloseAllDocuments"
    LogLine "NO_OPEN_CAD_DOCUMENTS_VERIFIED; beginning archive"
'''
src=src.replace('    zipPath = PackageNativeOutput(outputFolder, folder)',insertion+'    zipPath = PackageNativeOutput(outputFolder, folder)')
src=src.replace('ARCHIVE_ONLY_STARTED; no imports, CAD edits, rebuilds or saves','ARCHIVE_RECOVERY_STARTED; saved-file/log preflight then close documents; no imports, CAD edits, rebuilds or saves')
assert re.findall(r'^Public Sub (\w+)',src,re.M)==['main']
assert 'closeResult = swApp.CloseAllDocuments(True)' in src
assert max(map(len,src.splitlines()))<1024
assert src.count('CloseAllDocuments(True)')==2
for ext in ['swb','bas']:
    p=S/('ArchiveNativeResultsV2.'+ext)
    assert not p.exists(),'Preserve existing source'
    p.write_text(('Attribute VB_Name = "ArchiveNativeResultsV2"\n' if ext=='bas' else '')+src,encoding='ascii',newline='\r\n')
report={'status':'Staged source; native execution pending','change_from_v1':'Preflight all 30 saved files; CloseAllDocuments(True), log normalized Boolean return, require GetFirstDocument() Nothing; package with unchanged allowlist payload',
'authorization_scope':'Parent confirms this dedicated trial session contains only our generated project documents and explicitly requests close-all to release native file locks',
'no_automatic_save':True,'source_file_changes':False,
'maximum_physical_line_length':max(map(len,src.splitlines())),
'macro_sha256':hashlib.sha256((S/'ArchiveNativeResultsV2.swb').read_bytes()).hexdigest(),
'references':['https://help.solidworks.com/2021/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISldWorks~CloseAllDocuments.html','https://help.solidworks.com/2018/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISldWorks~GetFirstDocument.html']}
(S/'ArchiveNativeResultsV2_source_audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'macro':str(S/'ArchiveNativeResultsV2.bas'),'audit':report},indent=2))
