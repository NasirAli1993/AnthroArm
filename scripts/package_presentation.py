from pathlib import Path
import shutil, json, re, html, zipfile, hashlib
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

root=Path(r'D:\RoboticArm')
dest=root/'share/HumanArm_Demonstration'
dest.mkdir(parents=True,exist_ok=True)

def copy(source,target):
    target=dest/target
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(root/source,target)

# Self-contained presentation assets, without application runtimes or private inputs.
for p in (root/'results/v3/design_stages').glob('*.png'):
    copy(p.relative_to(root),'assets/results/design_stages/'+p.name)
for name in ['hero_arm.png','full_arm_articulation.webm','camera_autonomy.webm','articulation_0.png','vision_autonomy_poster.png','printable_finger_assembled.png','printable_finger_exploded.png','validation.json','camera_autonomy_video.json','articulation_video.json','anatomical_cad_validation.json','printable_finger_build.json','media_validation.json','arduino_install.json','service_validation.json','camera_diagnosis.json','firmware_compile.log']:
    if (root/'results/v3'/name).exists():copy('results/v3/'+name,'assets/results/'+name)
for p in (root/'docs/v3').glob('*'):
    if p.is_file() and p.suffix.lower() in ['.txt','.svg','.csv','.xlsx','.json']:
        copy(p.relative_to(root),'docs/'+p.name)
for name in ['humanoid_hand_demo.webm','v2_precision.json','v2_grasp_validation.json']:
    copy('results/'+name,'assets/archive/'+name)
for name in ['AnthroArm27_ReferenceV3.FCStd','AnthroArm27_ReferenceV3.step','robot_spec.json','components.txt']:
    copy('design/v3/'+name,'CAD/'+name)
for p in (root/'design/v3/printable_finger').rglob('*'):
    if p.is_file() and p.suffix.lower() in ['.fcstd','.step','.stl','.txt','.json']:
        copy(p.relative_to(root),'CAD/printable_finger/'+str(p.relative_to(root/'design/v3/printable_finger')))

mapping={'cad.py':'design/v3/build_reference_arm.py','physics.py':'simulation/v3/model.py','vision.py':'simulation/v3/vision_reach.py','camera.py':'simulation/v3/server.py','firmware.ino':'hardware/single_finger/single_finger.ino','bridge.py':'hardware/servo_console.py'}
source_html={}
copy('simulation/v3/probe_camera.py','code/probe_camera.py')
for alias,path in mapping.items():
    copy(path,'code/'+alias)
    view=alias.replace('.','_')+'.html'
    source_html[alias]='code/'+view
    text=(root/path).read_text(encoding='utf-8')
    page='<!doctype html><html lang="en"><meta charset="utf-8"><title>'+html.escape(path)+'</title><style>body{margin:0;background:#0d1518;color:#dce9eb;font:14px Segoe UI,sans-serif}header{padding:23px 30px;border-bottom:1px solid #304a50;position:sticky;top:0;background:#132126}a{color:#72e0c7;margin-right:25px}h1{font:19px Segoe UI,sans-serif;margin:18px 0 8px}p{color:#abc0c6;font-size:12px}pre{font:12px/1.6 Consolas,monospace;padding:25px 30px;white-space:pre;overflow:auto}</style><header><a href="../index.html#software">Back to presentation</a><a href="'+html.escape(alias)+'" download>Download source snapshot</a><h1>'+html.escape(path)+'</h1><p>Readable source snapshot from the project. This file may depend on other project files, packages and the original directory layout.</p></header><pre>'+html.escape(text)+'</pre></html>'
    (dest/'code'/view).write_text(page,encoding='utf-8')

page=(root/'dashboard/presentation.html').read_text(encoding='utf-8')
for alias,target in source_html.items():page=page.replace('/code/'+alias,target)
page=page.replace('href="/share/HumanArm_Demonstration.zip"','href="OPEN FIRST.txt"').replace('Download offline presentation ↓','How to share this folder')
page=page.replace('/v3results/','assets/results/').replace('/v3docs/','docs/')
page=page.replace('href="/v3/results"','href="assets/results/validation.json"')
page=page.replace('href="/precision"','href="assets/archive/v2_precision.json"').replace('href="/grasp-results"','href="assets/archive/v2_grasp_validation.json"').replace('href="/motion.webm"','href="assets/archive/humanoid_hand_demo.webm"')
for route in ['/v3/live','/v3/vision','/','/design']:
    page=page.replace('href="'+route+'"','href="#offline-live"')
page=page.replace('Open v3 live studio ↗','About live controls').replace('Open articulated physics ↗','About live controls').replace('Open v3 controls ↗','About live controls').replace('Open camera / imitation controls ↗','About live camera controls').replace('Open vision experiment ↗','About live vision controls')
page=page.replace('Open the saved construction walkthrough ↗','About the live project').replace('Open the earlier v2 studio ↗','About the earlier live studio')
page=page.replace('PROJECT PRESENTATION · DESIGN, CODE & HARDWARE','OFFLINE PRESENTATION · CAD, RECORDINGS & SOURCE')
page=page.replace('Current v3 measurement report available. Open it to inspect conditions.','Packaged v3 measurement report. The recordings and gallery work offline.')
offline_panel='''<section class="section" id="offline-live"><div class="sectionhead"><div class="eyebrow">Offline package</div><h2>Recordings and CAD work here. Live control needs the project servers.</h2><p>This copy opens directly as a local HTML file. It includes the CAD gallery, videos, reports, guides and readable source snapshots. It does not install software, start a server, access a camera or command hardware.</p></div><div class="downloadlist"><a href="CAD/AnthroArm27_ReferenceV3.FCStd">Native full-arm FreeCAD assembly<small>Open in a compatible FreeCAD installation</small></a><a href="CAD/AnthroArm27_ReferenceV3.step">Full-arm STEP export<small>CAD interchange file; digital geometry</small></a><a href="CAD/printable_finger/TendonFinger_FitTest.FCStd">Native one-finger fit-test assembly<small>Separate mechanical prototype; unprinted and untested</small></a><a href="CAD/printable_finger/READ_ME_FIRST.txt">Read before printing<small>Fit, clearances, cord routing and mounting limitations</small></a><a href="OPEN FIRST.txt">Package opening guide<small>Contents, viewing, source and hardware limits</small></a><a href="PACKAGE_MANIFEST.json">Package manifest<small>File sizes and SHA256 hashes for this snapshot</small></a></div></section>'''
page=page.replace('<footer>',offline_panel+'<footer>',1)
assets=json.loads((root/'docs/v3/presentation_assets.json').read_text(encoding='utf-8'))
assets['hero_image']=assets['hero_image'].replace('/v3results/','assets/results/')
for item in assets['cad_views']:item['image']=item['image'].replace('/v3results/','assets/results/')
report=json.loads((root/'results/v3/validation.json').read_text(encoding='utf-8'))
snapshot={'model':report.get('model'),'version':report.get('version'),'passed':report.get('passed'),'checks':len(report.get('checks',{}))}
start=page.index('async function checkEvidence()')
end=page.index('</script>',start)
offline_js='''const offlineAssets='''+json.dumps(assets,ensure_ascii=False)+''';
const offlineReport='''+json.dumps(snapshot)+''';
setupCad(offlineAssets.cad_views);
$('heroImage').src=offlineAssets.hero_image;$('heroImage').classList.remove('hidden');$('heroPending').classList.add('hidden');$('heroCaption').textContent=offlineAssets.hero_caption;
$('v3ReportState').textContent=offlineReport.passed?'Packaged report · passed checks':'Packaged report · inspect results';$('v3ReportState').classList.add('ready');$('modelStatus').classList.add('ready');$('modelStatus').querySelector('span').textContent='Offline snapshot: '+offlineReport.model+' v'+offlineReport.version+' · '+offlineReport.checks+' recorded checks.';
'''
page=page[:start]+offline_js+page[end:]
assert 'fetch(' not in page,'Offline page must not fetch file:// resources'
(dest/'index.html').write_text(page,encoding='utf-8')
guide='''HUMANOID ARM DEMONSTRATION — OPEN THIS FIRST

1. Extract the entire ZIP to one folder. Keep the subfolders together.
2. Open index.html in a recent Edge, Chrome or Firefox browser.
3. The CAD gallery, both current v3 videos, guides and source viewers work
   from local files. Use the video controls to play the recordings.
4. If a browser blocks a recording, open its .webm file directly from
   assets/results in a compatible video player. Do not edit server settings.

WHAT THIS PACKAGE CONTAINS
  index.html       Offline project presentation and eight-minute talk track
  assets/results   Current v3 CAD images, actual simulation recordings/reports
  assets/archive   Explicitly versioned earlier v2 recording and reports
  docs             Assembly guide, wiring SVG, BOM CSV and sizing workbook
  CAD              Native full-arm FreeCAD assembly and STEP export
  CAD/printable_finger  Separate fit-test finger CAD, STEP and STL in millimeters
  code             Readable source snapshots and original source downloads
  PACKAGE_MANIFEST.json  Per-file sizes and SHA256 checksums

WHAT IT DOES NOT DO
This package does not start the local simulation servers, access a webcam,
install software or operate physical motors. Links marked About live controls
explain this boundary. The original D:\\RoboticArm installation runs live
studios locally. A localhost/127.0.0.1 address is not a public sharing link.
The six source snapshots document the code; they are not a complete portable
runtime. They depend on other project files and compatible packages.
code/probe_camera.py is the camera diagnosis utility. It records scalar frame
statistics for available backends, without saving or transmitting camera images.

CURRENT RECORDED EVIDENCE
V3 is a seven-arm-axis, twenty-hand-axis simulation. Its recorded report
passes seven checks. The camera experiment uses a calibrated virtual RGB-D
camera and a known upright 50 mm orange target. Three trials approached and
touched it. Autonomous pickup was not demonstrated. The 33-second motion
video and 10.05-second vision video show integrated simulated physics.
Numerical tracking/localization results do not establish hardware accuracy.
Tracking below 0.01 degrees describes the independent-axis test without
object contact, not contact poses. The computer's only registered camera was
the ToDesk virtual camera; its feed was distorted. Live hand imitation has
not been validated with a usable camera. The camera_diagnosis.json file
records this limitation. No webcam frames are included in this package.

HARDWARE STATUS
No physical robot or finger has been built or powered. The single-finger
geometry is a fit-test prototype. Read its READ_ME_FIRST.txt and the separate
prototype_assembly.txt before fabricating anything. Full-arm motor, gearing,
structure, bearing, wiring and stopping design remains to be engineered.
The UNO firmware source starts disarmed, but it is not a safety controller.

OPENING ENGINEERING FILES
FCStd requires compatible FreeCAD software. STEP opens in compatible CAD
software. STL files in CAD/printable_finger/stl_mm use millimeters. XLSX opens
in a compatible spreadsheet application; the CSV is a plain BOM export.
There are no application installers, external runtimes, trained models,
credentials, webcam captures or the user's original requirements document
inside this presentation package. Official source links require the internet.

SHARING
Share the ZIP or the entire extracted folder, preserving all subfolders.
Do not send index.html alone. The package includes project-created CAD,
documentation and source snapshots; third-party software is referenced rather
than bundled. Confirm appropriate permissions before publishing project files.
'''
(dest/'OPEN FIRST.txt').write_text(guide,encoding='utf-8')

class Links(HTMLParser):
    def __init__(self):super().__init__();self.values=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ('src','href') and v:self.values.append(v)
missing=[];rooted=[]
for file in dest.rglob('*.html'):
    parser=Links();parser.feed(file.read_text(encoding='utf-8'))
    for value in parser.values:
        if value.startswith(('https://','http://','data:','#','mailto:')):continue
        if value.startswith('/'):rooted.append((str(file.relative_to(dest)),value));continue
        rel=unquote(urlsplit(value).path)
        if not (file.parent/rel).exists() and rel!='PACKAGE_MANIFEST.json':missing.append((str(file.relative_to(dest)),value))
assert not missing,missing
assert not rooted,rooted
for item in assets['cad_views']:assert (dest/item['image']).exists(),item
manifest={'title':'HumanArm Demonstration','model':snapshot,'scope':'Offline presentation; physical hardware unbuilt; camera approach and touch, no autonomous pickup','files':[]}
for p in sorted(dest.rglob('*')):
    if p.is_file() and p.name!='PACKAGE_MANIFEST.json':
        manifest['files'].append({'path':p.relative_to(dest).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(dest/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
archive=root/'share/HumanArm_Demonstration.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(dest.rglob('*')):
        if p.is_file():z.write(p,'HumanArm_Demonstration/'+p.relative_to(dest).as_posix())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'folder':str(dest),'zip':str(archive),'zip_bytes':archive.stat().st_size,'files':len(manifest['files'])+1,'broken_local_references':len(missing),'rooted_local_references':len(rooted),'offline_fetch_calls':0,'zip_crc_check':'passed'},indent=2))
