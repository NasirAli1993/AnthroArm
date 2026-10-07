"""Write the human-readable SOLIDWORKS handoff and zip the checked neutral data."""
from pathlib import Path
import csv, html, json, shutil, zipfile

ROOT=Path(r'D:\RoboticArm\solidworks')
OUT=ROOT/'transfer'
manifest=json.loads((OUT/'assembly_manifest.json').read_text(encoding='utf-8'))
report=json.loads((OUT/'transfer_validation.json').read_text(encoding='utf-8'))
assert report['passed'], 'Do not package a failed geometry transfer.'
with (OUT/'component_inventory.csv').open(encoding='utf-8-sig',newline='') as f:
    inventory=list(csv.DictReader(f))
texts={r['name']:(OUT/r['step_file']).read_text(encoding='utf-8') for r in manifest['links']}
missing=[c['name'] for c in inventory if c['name'] not in texts[c['link']]]
integrity=dict(body_names_in_step=len(inventory)-len(missing),missing_body_names=missing,all_step_units_mm=all('SI_UNIT(.MILLI.,.METRE.)' in text for text in texts.values()),joint_count=sum(r['joint'] is not None for r in manifest['links']),unique_component_names=len({c['name'] for c in inventory})==len(inventory),parent_links_resolve=all(r['parent'] is None or r['parent'] in texts for r in manifest['links']))
integrity['passed']=not missing and integrity['all_step_units_mm'] and integrity['joint_count']==27 and integrity['unique_component_names'] and integrity['parent_links_resolve']
assert integrity['passed'], 'Package metadata integrity check failed.'
(OUT/'package_integrity.json').write_text(json.dumps(integrity,indent=2),encoding='utf-8')

readme='''SOLIDWORKS TRANSFER — ANTHRO ARM 27

STATUS
Prepared on D: from the existing FreeCAD V3 design. This package contains neutral
STEP geometry and the assembly definition. SOLIDWORKS is not installed/licensed
for this work yet. No native SLDPRT, SLDASM, mates, motion study, FEA result or
SOLIDWORKS test result is claimed. No cloud upload has been performed by this script.

WHAT IS HERE
full_arm_home_reference.step: all 293 solids in their existing assembled home pose.
links/: 28 individual rigid-link STEP files, each in its local coordinate frame.
joint_schedule.csv: 27 joints, parent-child order, axes, positions, angular limits.
assembly_manifest.json: full transform matrices for automatic assembly placement.
component_inventory.csv: all 293 bodies with short component explanations.
transfer_validation.json: actual FreeCAD/OpenCascade reimport checks for every link.
preview.png: existing FreeCAD CAD rendering, NOT a SOLIDWORKS screenshot.

UNITS AND FRAMES
STEP dimensions and matrix translations are millimetres. Do not scale by 1000.
Angles have explicit radian and degree fields. Each link's local +Z points toward
the fingertips, +X toward the palm, and +Y toward the thumb/index side. The shoulder
base is at world [0,0,1080] mm with an X rotation of 180 degrees, so the zero-pose
arm hangs down. The supplied reference is the bent home pose, not the zero pose.
Matrices use column vectors: p_world = R * p_local + translation.

FIRST VISUAL IMPORT
Open full_arm_home_reference.step in SOLIDWORKS, inspect the STEP import options,
and verify millimetres and 293 solid bodies. Run Import Diagnostics and inspect
any healing before saving to a new native file. Compare the silhouette with
preview.png. This gives a reviewable static import; it does not create articulation.

BUILD THE ARTICULATED ASSEMBLY
1. Open each file in links/ as one multibody part. If the importer recognizes a
   STEP assembly, choose its mapping to a multibody part. Preserve the original
   origin/orientation and named bodies. Save each as its own SLDPRT under a new
   native/ folder on D:. These are imported B-rep features, not original sketches
   and loft feature history. The editable procedural design remains in FreeCAD.
2. Create an SLDASM and insert all 28 link parts. Keep the bodies within each link
   rigid; do not give 293 shell panels and fasteners independent moving joints.
3. Position each part using world_from_link_home_matrix_mm from the manifest. Fix
   only base_link to the world fixture. Verify the home pose against the reference.
   These JSON transforms are assembly data, not a ready-to-run SOLIDWORKS macro.
4. In parent-child order, construct reference axes at each joint's origin using
   origin_xyz_mm, origin_rpy_deg and axis_joint_local. The manifest also gives the
   same axis in parent coordinates. Use datum axes/planes when a decorative shell
   face does not represent the true joint axis. Do not use guessed visual axes.
5. Add one revolute/hinge relationship per row in joint_schedule.csv. Constrain
   relative translation and axis tilt while leaving exactly one rotation free.
   Set the stated angle limits and a named angular zero reference. Confirm the
   sign with a small positive jog. Shoulder axes and MCP axes intentionally share
   centers but belong to separate serial links; do not merge those carriers.
6. Check 27 independent rotational degrees of freedom before adding motors. An
   unexpectedly rigid joint usually indicates a fixed component, rigid nested
   subassembly, duplicate mate or angle constraint locking the desired motion.
7. Save the assembly and record all import warnings and mate errors. This work is
   still pending a licensed SOLIDWORKS session; no fabricated completion is implied.

PROPOSED TESTS INSIDE SOLIDWORKS — ALL PENDING
A. Import: confirm 28 link parts / 293 bodies, millimetres, valid solids and origin
   placement. Compare outer dimensions and a known phalanx length with source CAD.
B. Kinematics: from home, jog each of the 27 axes individually. Confirm direction,
   travel limits and parent-child motion, then play open/fist/pinch/point poses.
C. Interference: test neutral and representative bent poses. Classify expected
   contact separately from unintended shell collisions. Existing concept motor
   envelopes and cable routes may intersect; they are not production packaging.
D. Motion Analysis, if included in the license: specify mass/inertia, gravity,
   motor motion and suitable contacts; inspect tracking, reactions and solver
   convergence. Prescribed animation alone is not a dynamic simulation result.
E. Structural FEA, if licensed: begin with a real single-finger part after its
   material, pin/bearing support, tendon load and manufacturing details are chosen.
   Refine the mesh and compare stress/displacement convergence. Arbitrary loads or
   material assignments would not qualify the arm's load capacity.
F. Camera-guided motion: the existing OpenCV/MuJoCo camera controller is external.
   Importing STEP does not transfer vision, Python control or autonomous behavior.
   A SOLIDWORKS control/API bridge and validated test case would be separate work.

ENGINEERING LIMITS
The 27 commanded simulation axes are a kinematic target. The motor bodies, reducer
envelopes, cable paths and some bearing interfaces remain concepts. STEP validity
does not prove manufacturability, strength, assembly fit, contact clearance or
physical safety. Simulation effort limits in the schedule are NOT hardware ratings.
The separate one-finger prototype is documented in the existing D:\\RoboticArm project.

OFFICIAL REFERENCES
SOLIDWORKS STEP import options and body names:
https://help.solidworks.com/2025/english/SolidWorks/sldworks/t_reading_step_iges_acis_sw.htm
SOLIDWORKS hinge mates, angular limits and Motion requirement:
https://help.solidworks.com/2025/english/SolidWorks/motionstudies/t_hinge_mates.htm
These official help search results were checked during preparation. Actual option
labels and availability must be verified in the SOLIDWORKS version used.
'''
(OUT/'READ_ME_FIRST.txt').write_text(readme,encoding='utf-8')
preview=Path(r'D:\RoboticArm\results\v3\hero_arm.png')
if preview.exists():shutil.copy2(preview,OUT/'preview.png')
maxvol=max(x['volume_relative_error'] for x in report['links'])
maxcent=max(x['reconstructed_world_centroid_error_mm'] for x in report['links'])
rows=''.join('<tr><td>'+html.escape(r['name'])+'</td><td>'+html.escape(r['parent'] or 'Fixed world')+'</td><td>'+str(r['body_count'])+'</td><td><a href="'+r['step_file']+'">STEP</a></td></tr>' for r in manifest['links'])
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Human Arm — SOLIDWORKS transfer</title><style>body{font:17px/1.6 system-ui,sans-serif;max-width:1040px;margin:40px auto;padding:0 24px;color:#17232b;background:#f4f7f8}h1{line-height:1.12;font-size:42px}a{color:#005d88}figure{margin:20px 0}img{max-width:100%;max-height:550px;object-fit:contain;background:white;width:100%}.status{padding:18px 22px;border-left:5px solid #bd7d13;background:#fff3db}table{border-collapse:collapse;width:100%;background:white}th,td{text-align:left;padding:8px 12px;border-bottom:1px solid #d5dfe4}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.card{padding:18px;background:#fff;border:1px solid #d5dfe4}.card b{font-size:30px;display:block}pre{white-space:pre-wrap;font:15px/1.55 system-ui;background:white;padding:24px}figcaption{font-size:14px;color:#485861}@media(max-width:600px){.cards{grid-template-columns:1fr}h1{font-size:32px}}</style><h1>Human arm<br>SOLIDWORKS transfer package</h1><p class="status"><b>Geometry prepared; native SOLIDWORKS work pending.</b> This is a checked STEP transfer from FreeCAD. SOLIDWORKS import, articulation, motion studies and structural tests have not run.</p><div class="cards"><div class="card"><b>28</b>rigid links</div><div class="card"><b>293</b>named solid bodies</div><div class="card"><b>27</b>revolute joint definitions</div></div><figure><img src="preview.png" alt="Existing FreeCAD rendering of the articulated human-shaped arm"><figcaption>Existing FreeCAD CAD render. This is not a SOLIDWORKS screenshot.</figcaption></figure><p><a href="full_arm_home_reference.step">Open assembled STEP reference</a> · <a href="READ_ME_FIRST.txt">Read complete handoff</a> · <a href="joint_schedule.csv">Joint schedule</a> · <a href="component_inventory.csv">Component explanations</a> · <a href="assembly_manifest.json">Assembly transforms</a> · <a href="transfer_validation.json">Reimport evidence</a></p><h2>What was tested</h2><p>All 28 exported link files were reimported with FreeCAD/OpenCascade. Solid counts, positive volume, geometry validity, local bounds and reconstructed world centroids passed. Maximum relative volume change: MAXVOL; maximum reconstructed centroid difference: MAXCENT mm. These are CAD translation checks, not SOLIDWORKS simulation results.</p><h2>Articulated link files</h2><table><thead><tr><th>Child link</th><th>Parent link</th><th>Bodies</th><th>File</th></tr></thead><tbody>ROWS</tbody></table><h2>Import, assembly and testing handoff</h2><pre>README</pre></html>'''
page=page.replace('MAXVOL',f'{maxvol:.3g}').replace('MAXCENT',f'{maxcent:.3g}').replace('ROWS',rows).replace('README',html.escape(readme))
(OUT/'index.html').write_text(page,encoding='utf-8')
shutil.copy2(ROOT/'scripts'/'export_transfer.py',OUT/'export_transfer_source.py')
with zipfile.ZipFile(ROOT/'AnthroArm27_SOLIDWORKS_Transfer.zip','w',zipfile.ZIP_DEFLATED) as z:
    for path in sorted(OUT.rglob('*')):
        if path.is_file():z.write(path,'AnthroArm27_SOLIDWORKS_Transfer/'+path.relative_to(OUT).as_posix())
with zipfile.ZipFile(ROOT/'AnthroArm27_SOLIDWORKS_Transfer.zip') as z:
    assert z.testzip() is None, 'ZIP content CRC failure.'
print(json.dumps(dict(passed=True,package=str(ROOT/'AnthroArm27_SOLIDWORKS_Transfer.zip'),bytes=(ROOT/'AnthroArm27_SOLIDWORKS_Transfer.zip').stat().st_size,links=report['rigid_links'],bodies=report['component_solids'],max_volume_relative_error=maxvol,max_centroid_error_mm=maxcent)))
