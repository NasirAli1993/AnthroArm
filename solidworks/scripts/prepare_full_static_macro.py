"""Generate reviewable VBA source; DOES NOT execute or compile SOLIDWORKS code."""
from pathlib import Path
import hashlib, json, re, shutil, zipfile

ROOT = Path('D:/RoboticArm/solidworks')
SOURCE = ROOT / 'scripts/AutoFingerImportV2.swb'
MANIFEST = ROOT / 'transfer/assembly_manifest.json'
AUDIT = ROOT / 'studies/coordinate_transform_audit.json'
OUT = ROOT / 'scripts/AutoFullArmStaticV1.swb'
manifest = json.loads(MANIFEST.read_text(encoding='utf-8-sig'))
audit = json.loads(AUDIT.read_text(encoding='utf-8-sig'))
links = manifest['links']
assert len(links) == 28 and sum(x['body_count'] for x in links) == 293
assert hashlib.sha256(MANIFEST.read_bytes()).hexdigest() == audit['manifest_sha256']
audit_links = {x['link']: x for x in audit['links']}

def number(n):
    if abs(n) < 1e-14:
        n = 0.0
    value = format(n, '.17g').replace('e', 'E')
    return value + '#'

initializers = []
for i, link in enumerate(links):
    matrix = link['world_from_link_home_matrix_mm']
    array = [matrix[r][c] for c in range(3) for r in range(3)]
    array += [matrix[r][3]/1000 for r in range(3)] + [1,0,0,0]
    audit_array = audit_links[link['name']]['sw_array_data_derived_NOT_NATIVE_TESTED']
    assert max(abs(a-b) for a,b in zip(array,audit_array)) < 1e-12
    points = audit_links[link['name']]['expected_world_points_m']
    initializers += [
        f'    linkNames({i}) = "{link["name"]}"',
        f'    expectedCounts({i}) = {link["body_count"]}',
        f'    homeData({i}) = Array({", ".join(map(number,array))})',
        f'    expectedPoints({i}) = Array({", ".join(number(v) for p in points for v in p)})',
    ]

old = SOURCE.read_text(encoding='utf-8-sig')
restore = old[old.index('Private Sub RestorePreferences()'):old.index('Private Sub ValidateNativeMath()')]
restore = restore.replace('    Call swApp.SetUserPreferenceIntegerValue(swImportNeutralAssemblyStructureMapping, oldMapping)',
'''    Call swApp.SetUserPreferenceIntegerValue(swImportNeutralUnits, oldUnits)
    result = (swApp.GetUserPreferenceIntegerValue(swImportNeutralUnits) = oldUnits)
    If Not result Then LogLine "WARNING: could not restore import units"
    Call swApp.SetUserPreferenceIntegerValue(swImportNeutralAssemblyStructureMapping, oldMapping)''')

source = r'''Option Explicit
' STAGED SOURCE ONLY: not compiled or executed in SOLIDWORKS.
' Requires SOLIDWORKS type library AND SOLIDWORKS constants type library.
' Upload this source and all 28 STEP files FLAT in the same directory.
' Save its .swp in that directory before running main.
' Produces native static home-pose geometry, not mates/motion/FEA.
' Source matrices: column-vector world_from_link_home, translation mm.
' SW MathTransform: transposed rotation storage, translation m, scale 1.
' Source inputs and any existing output files are never overwritten.
' No shell/network calls or account operations.

Private swApp As SldWorks.SldWorks
Private mathUtil As SldWorks.MathUtility
Private runtimeLog As String
Private logReady As Boolean
Private oldMapping As Long, oldUnits As Long
Private oldInterconnect As Boolean, oldSolidSurface As Boolean, oldDiagnostics As Boolean
Private prefsCaptured As Boolean
Private linkNames(0 To 27) As String
Private expectedCounts(0 To 27) As Long
Private homeData(0 To 27) As Variant
Private expectedPoints(0 To 27) As Variant
Private nativePaths(0 To 27) As String
Private importedModels(0 To 27) As SldWorks.ModelDoc2
Private components(0 To 27) As SldWorks.Component2

Private Sub LogLine(ByVal message As String)
    Dim channel As Integer, entry As String
    entry = Format$(Now, "yyyy-mm-dd hh:nn:ss") & " | " & message
    Debug.Print entry
    If logReady Then
        channel = FreeFile
        Open runtimeLog For Append As #channel
        Print #channel, entry
        Close #channel
    End If
End Sub

Private Sub Check(ByVal condition As Boolean, ByVal message As String)
    If Not condition Then Err.Raise vbObjectError + 720, "AutoFullArmStaticV1", message
End Sub

Private Function CountArray(ByVal items As Variant) As Long
    If IsEmpty(items) Then
        CountArray = 0
    ElseIf IsArray(items) Then
        CountArray = UBound(items) - LBound(items) + 1
    Else
        Err.Raise vbObjectError + 721, "CountArray", "Expected an array or Empty"
    End If
End Function

Private Sub InitData()
__INITIALIZERS__
End Sub

__RESTORE__

Private Sub ConfigureImport()
    oldMapping = swApp.GetUserPreferenceIntegerValue(swImportNeutralAssemblyStructureMapping)
    oldUnits = swApp.GetUserPreferenceIntegerValue(swImportNeutralUnits)
    oldInterconnect = swApp.GetUserPreferenceToggle(swMultiCAD_Enable3DInterconnect)
    oldSolidSurface = swApp.GetUserPreferenceToggle(swImportNeutral_SolidandSurface)
    oldDiagnostics = swApp.GetUserPreferenceToggle(swImportNeutralRunDiagnostics)
    prefsCaptured = True
    Call swApp.SetUserPreferenceToggle(swMultiCAD_Enable3DInterconnect, False)
    Check swApp.GetUserPreferenceToggle(swMultiCAD_Enable3DInterconnect) = False, "Cannot disable 3D Interconnect"
    Call swApp.SetUserPreferenceIntegerValue(swImportNeutralAssemblyStructureMapping, swImportNeutralAssemblyStructureMapping_MultibodyPart)
    Check swApp.GetUserPreferenceIntegerValue(swImportNeutralAssemblyStructureMapping) = swImportNeutralAssemblyStructureMapping_MultibodyPart, "Cannot set multibody mapping"
    Call swApp.SetUserPreferenceIntegerValue(swImportNeutralUnits, swImportNeutralUnits_ImportFileUnits)
    Check swApp.GetUserPreferenceIntegerValue(swImportNeutralUnits) = swImportNeutralUnits_ImportFileUnits, "Cannot set file-specified units"
    Call swApp.SetUserPreferenceToggle(swImportNeutral_SolidandSurface, True)
    Check swApp.GetUserPreferenceToggle(swImportNeutral_SolidandSurface), "Cannot enable solids/surfaces"
    Call swApp.SetUserPreferenceToggle(swImportNeutralRunDiagnostics, False)
    Check swApp.GetUserPreferenceToggle(swImportNeutralRunDiagnostics) = False, "Cannot disable automatic healing"
    LogLine "PREFERENCES_SET: classic STEP, multibody part, source-file mm, no automatic healing"
End Sub

Private Sub ValidateTransform(ByVal linkIndex As Long, ByVal transform As SldWorks.MathTransform, ByVal stage As String)
    Dim point As SldWorks.MathPoint
    Dim pointData(2) As Double
    Dim vPoint As Variant, actual As Variant, expected As Variant
    Dim i As Long, axis As Long, errorM As Double, maximumError As Double
    Check Not transform Is Nothing, "Missing transform: " & linkNames(linkIndex)
    expected = expectedPoints(linkIndex)
    For i = 0 To 3
        For axis = 0 To 2
            pointData(axis) = 0#
        Next axis
        If i > 0 Then pointData(i - 1) = 0.01
        vPoint = pointData
        Set point = mathUtil.CreatePoint(vPoint)
        Check Not point Is Nothing, "CreatePoint failed"
        Set point = point.MultiplyTransform(transform)
        Check Not point Is Nothing, "MultiplyTransform failed"
        actual = point.ArrayData
        For axis = 0 To 2
            errorM = Abs(CDbl(actual(axis)) - CDbl(expected(i * 3 + axis)))
            If errorM > maximumError Then maximumError = errorM
        Next axis
    Next i
    LogLine linkNames(linkIndex) & " " & stage & " MATH_POINT_MAX_ERROR_M=" & CStr(maximumError)
    Check maximumError < 0.000000001, "Transform point check failed: " & linkNames(linkIndex) & " " & stage
End Sub

Private Function HomeTransform(ByVal linkIndex As Long) As SldWorks.MathTransform
    Dim data(15) As Double, values As Variant, arrayData As Variant
    Dim i As Long
    values = homeData(linkIndex)
    For i = 0 To 15
        data(i) = CDbl(values(i))
    Next i
    arrayData = data
    Set HomeTransform = mathUtil.CreateTransform(arrayData)
    Check Not HomeTransform Is Nothing, "CreateTransform failed: " & linkNames(linkIndex)
End Function

Private Sub SaveNew(ByVal model As SldWorks.ModelDoc2, ByVal destination As String)
    Dim result As Boolean, errors As Long, warnings As Long
    Check Len(Dir$(destination)) = 0, "Refusing existing destination: " & destination
    model.ClearSelection2 True
    result = model.Extension.SaveAs(destination, swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, errors, warnings)
    LogLine "SAVE " & destination & " RETURN=" & CStr(result) & " ERRORS=" & CStr(errors) & " WARNINGS=" & CStr(warnings)
    Check result And errors = 0, "Native save failed: " & destination
    Check Len(Dir$(destination)) > 0, "Saved file missing: " & destination
    Check FileLen(destination) > 0, "Saved file empty: " & destination
    LogLine "SAVED_BYTES=" & CStr(FileLen(destination))
End Sub

Private Sub ImportOne(ByVal linkIndex As Long, ByVal inputFolder As String, ByVal outputFolder As String)
    Dim inputPath As String, stem As String
    Dim model As SldWorks.ModelDoc2, alreadyOpen As SldWorks.ModelDoc2
    Dim part As SldWorks.PartDoc, stepData As SldWorks.ImportStepData
    Dim body As SldWorks.Body2
    Dim bodies As Variant, sheets As Variant, box As Variant
    Dim loadErrors As Long, i As Long, axis As Long
    Dim low(2) As Double, high(2) As Double, largestSpan As Double, span As Double
    stem = linkNames(linkIndex)
    inputPath = inputFolder & stem & ".step"
    nativePaths(linkIndex) = outputFolder & stem & ".SLDPRT"
    LogLine "IMPORT_STARTED " & CStr(linkIndex + 1) & "/28 SOURCE=" & inputPath
    Set alreadyOpen = swApp.GetOpenDocumentByName(inputPath)
    Check alreadyOpen Is Nothing, "Source already open; close it before fresh import: " & inputPath
    Set stepData = swApp.GetImportFileData(inputPath)
    Check Not stepData Is Nothing, "No ImportStepData: " & stem
    stepData.MapConfigurationData = False
    Set model = swApp.LoadFile4(inputPath, "r", stepData, loadErrors)
    LogLine stem & " LOAD_ERRORS=" & CStr(loadErrors)
    Check Not model Is Nothing, "LoadFile4 returned Nothing: " & stem
    Check loadErrors = 0, "LoadFile4 error: " & stem
    Check model.GetType = swDocPART, "Expected one multibody Part: " & stem
    Set part = model
    bodies = part.GetBodies2(swSolidBody, False)
    sheets = part.GetBodies2(swSheetBody, False)
    LogLine stem & " SOLIDS=" & CStr(CountArray(bodies)) & " EXPECTED=" & CStr(expectedCounts(linkIndex)) & " SHEETS=" & CStr(CountArray(sheets))
    Check CountArray(bodies) = expectedCounts(linkIndex), "Wrong solid count: " & stem
    Check CountArray(sheets) = 0, "Unexpected sheet bodies: " & stem
    For axis = 0 To 2
        low(axis) = 1E+30
        high(axis) = -1E+30
    Next axis
    For i = LBound(bodies) To UBound(bodies)
        Set body = bodies(i)
        LogLine stem & " BODY=" & body.Name
        box = body.GetBodyBox
        Check IsArray(box), "No body bounding box: " & stem
        For axis = 0 To 2
            If CDbl(box(axis)) < low(axis) Then low(axis) = CDbl(box(axis))
            If CDbl(box(axis + 3)) > high(axis) Then high(axis) = CDbl(box(axis + 3))
        Next axis
    Next i
    For axis = 0 To 2
        span = high(axis) - low(axis)
        LogLine stem & " APPROX_MIN_MAX_SPAN_AXIS_" & CStr(axis) & "_MM=" & CStr(low(axis) * 1000#) & "," & CStr(high(axis) * 1000#) & "," & CStr(span * 1000#)
        If span > largestSpan Then largestSpan = span
    Next axis
    ' Gross scale gate only; approximate boxes are not precision dimensional evidence.
    Check largestSpan > 0.003 And largestSpan < 0.5, "Gross scale gate failed; expected each rigid link between 3 and 500 mm"
    SaveNew model, nativePaths(linkIndex)
    Set importedModels(linkIndex) = model
    LogLine stem & " IMPORT_COUNT_SCALE_SAVE_PASS; exact dimensions/geometry diagnostics pending"
End Sub

Private Function AssemblyTemplate() As String
    Dim path As String
    path = swApp.GetUserPreferenceStringValue(swDefaultTemplateAssembly)
    If Len(path) = 0 Then path = swApp.GetDocumentTemplate(swDocASSEMBLY, "", 0, 0#, 0#)
    Check Len(path) > 0, "No assembly template configured; create one blank assembly manually then rerun"
    Check Len(Dir$(path)) > 0, "Assembly template does not exist: " & path
    LogLine "ASSEMBLY_TEMPLATE=" & path
    AssemblyTemplate = path
End Function

Private Sub CreateStaticAssembly(ByVal outputFolder As String, ByVal templatePath As String)
    Dim model As SldWorks.ModelDoc2, assembly As SldWorks.AssemblyDoc
    Dim comp As SldWorks.Component2, transform As SldWorks.MathTransform
    Dim items As Variant, i As Long, result As Boolean
    Set model = swApp.NewDocument(templatePath, 0, 0#, 0#)
    Check Not model Is Nothing, "NewDocument failed for assembly template"
    Check model.GetType = swDocASSEMBLY, "Template did not create an Assembly"
    Set assembly = model
    For i = 0 To 27
        ' Imported parts remain open/in memory, as AddComponent5 requires.
        Set comp = assembly.AddComponent5(nativePaths(i), swAddComponentConfigOptions_CurrentSelectedConfig, "", False, "", 0#, 0#, 0#)
        Check Not comp Is Nothing, "AddComponent5 failed: " & linkNames(i)
        Set components(i) = comp
        model.ClearSelection2 True
        result = comp.Select4(False, Nothing, False)
        Check result, "Could not select component: " & linkNames(i)
        If comp.IsFixed Then assembly.UnfixComponent
        Check Not comp.IsFixed, "Cannot float before positioning: " & linkNames(i)
        Set transform = HomeTransform(i)
        Set comp.Transform2 = transform
        Set transform = comp.Transform2
        ValidateTransform i, transform, "PLACEMENT_READBACK"
        model.ClearSelection2 True
        result = comp.Select4(False, Nothing, False)
        Check result, "Could not select component for static fixing: " & linkNames(i)
        assembly.FixComponent
        Check comp.IsFixed, "Static fixing failed: " & linkNames(i)
        LogLine "COMPONENT_PLACED_FIXED " & CStr(i + 1) & "/28 " & comp.Name2
    Next i
    model.ClearSelection2 True
    result = model.EditRebuild3
    LogLine "ASSEMBLY_REBUILD_RETURN=" & CStr(result)
    Check result, "Assembly rebuild reported failure"
    items = assembly.GetComponents(True)
    LogLine "TOP_LEVEL_COMPONENT_COUNT=" & CStr(CountArray(items))
    Check CountArray(items) = 28, "Wrong top-level component count"
    For i = 0 To 27
        Set transform = components(i).Transform2
        ValidateTransform i, transform, "POST_REBUILD_READBACK"
        Check components(i).IsFixed, "Component not fixed after rebuild: " & linkNames(i)
    Next i
    model.ShowNamedView2 "*Isometric", 7
    model.ViewZoomtofit2
    SaveNew model, outputFolder & "AnthroArm27_STATIC_HOME.SLDASM"
    LogLine "STATIC_ASSEMBLY_SAVED: 28 fixed components, 293 source solids; NO MATES OR MOTION"
End Sub

' Sole public no-argument entry point.
Public Sub main()
    Dim macroPath As String, folder As String, outputFolder As String, runStamp As String
    Dim templatePath As String, failureText As String, failureNumber As Long
    Dim i As Long, total As Long, transform As SldWorks.MathTransform
    On Error GoTo Failed
    Set swApp = Application.SldWorks
    macroPath = swApp.GetCurrentMacroPathName()
    Check Len(macroPath) > 0 And InStrRev(macroPath, "\") > 0, "Save running macro before running main"
    folder = Left$(macroPath, InStrRev(macroPath, "\"))
    runStamp = Format$(Now, "yyyymmdd_hhnnss") & "_" & CStr(CLng(Timer * 1000#))
    outputFolder = folder & "AnthroArm27_Static_" & runStamp & "\"
    Check Len(Dir$(Left$(outputFolder, Len(outputFolder) - 1), vbDirectory)) = 0, "Refusing existing output folder"
    MkDir Left$(outputFolder, Len(outputFolder) - 1)
    runtimeLog = outputFolder & "Native_Static_Build.log"
    Check Len(Dir$(runtimeLog)) = 0, "Refusing existing log"
    logReady = True
    LogLine "RUN_STARTED: static native import and placement; not joints/motion/FEA"
    LogLine "MACRO_PATH=" & macroPath
    LogLine "OUTPUT_FOLDER=" & outputFolder
    LogLine "SOLIDWORKS_REVISION=" & swApp.RevisionNumber
    InitData
    For i = 0 To 27
        Check Len(Dir$(folder & linkNames(i) & ".step")) > 0, "Missing flat sibling STEP: " & linkNames(i)
        total = total + expectedCounts(i)
    Next i
    Check total = 293, "Embedded body counts inconsistent"
    LogLine "PREFLIGHT: all 28 STEP inputs present; expected 293 solid bodies"
    templatePath = AssemblyTemplate()
    Set mathUtil = swApp.GetMathUtility
    Check Not mathUtil Is Nothing, "Cannot access MathUtility"
    For i = 0 To 27
        Set transform = HomeTransform(i)
        ValidateTransform i, transform, "NATIVE_MATH_PRECHECK"
    Next i
    ConfigureImport
    For i = 0 To 27
        ImportOne i, folder, outputFolder
    Next i
    RestorePreferences
    CreateStaticAssembly outputFolder, templatePath
    LogLine "COMPLETED_STATIC_STAGE_ONLY"
    LogLine "PENDING: reopen verification, native dimensions/Import Diagnostics, actual joint mates, interference, Motion, FEA, hardware"
    MsgBox "Static native arm saved: 28 parts + assembly + log." & vbCrLf & outputFolder & vbCrLf & "All components fixed. No mates, Motion or FEA performed.", vbInformation
    logReady = False
    Exit Sub
Failed:
    failureNumber = Err.Number
    failureText = Err.Description
    On Error Resume Next
    LogLine "FAIL " & CStr(failureNumber) & " | " & failureText
    LogLine "Partial outputs preserved; complete static stage did not pass."
    RestorePreferences
    MsgBox "AutoFullArmStaticV1 stopped: " & CStr(failureNumber) & vbCrLf & failureText & vbCrLf & "Log: " & runtimeLog, vbExclamation
    logReady = False
End Sub
'''.replace('__INITIALIZERS__', '\n'.join(initializers)).replace('__RESTORE__', restore)

assert '__INITIALIZERS__' not in source
assert re.findall(r'^Public Sub (\w+)', source, re.M) == ['main']
assert len(re.findall(r'^Private (?:Sub|Function) ',source,re.M)) == len(re.findall(r'^End (?:Sub|Function)$',source,re.M)) - 1
assert max(map(len,source.splitlines())) < 1024
assert 'CreateDocument(' not in source  # correct documented method is NewDocument.
OUT.write_text(source, encoding='ascii', newline='\r\n')
OUT.with_suffix('.bas').write_text('Attribute VB_Name = "AutoFullArmStaticV1"\n' + source,encoding='ascii',newline='\r\n')
report = {
    'status':'STAGED SOURCE ONLY; not compiled or executed in SOLIDWORKS',
    'source_manifest_sha256': hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
    'macro_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),
    'links':len(links),'expected_solids':293,
    'all_embedded_transforms_match_source_audit': True,
    'all_required_step_files_present': all((ROOT/'transfer'/x['step_file']).is_file() for x in links),
    'public_entrypoints':['main'],
    'maximum_physical_line_length':max(map(len,source.splitlines())),
    'procedure_end_count_consistent':True,
    'native_execution':False,
    'scope':'28 imported multibody SLDPRT + one all-fixed static home-pose SLDASM + progressive log, if executed successfully',
    'not_included':['mates','kinematic articulation','Motion Analysis','FEA','manufacturing qualification'],
}
(ROOT/'scripts/AutoFullArmStaticV1_source_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
