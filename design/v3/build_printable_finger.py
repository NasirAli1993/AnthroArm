"""Separate fit-test finger demonstrator, not production-ready arm hardware.
All printable STL files use millimetres. Generic cradle requires actual-servo fit check.
"""
from pathlib import Path
import ast,json,math,struct,traceback
import FreeCAD as App
import FreeCADGui as Gui
import Part,MeshPart
ROOT=Path(r'D:\RoboticArm');DESIGN=ROOT/'design'/'v3';OUT=DESIGN/'printable_finger';RESULTS=ROOT/'results'/'v3';V=App.Vector
OUT.mkdir(parents=True,exist_ok=True);(OUT/'stl_mm').mkdir(exist_ok=True)
source=ast.parse((DESIGN/'build_reference_arm.py').read_text(encoding='utf-8'))
for node in source.body:
 if isinstance(node,ast.FunctionDef) and node.name in ['ellipse','loft','ellipsoid','cyl','ring','rounded_box','line_cylinder','stl']:exec(compile(ast.Module(body=[node],type_ignores=[]),'geometry_helpers','exec'))
doc=App.newDocument('TendonFinger_FitTest');doc.Label='Single tendon finger | fit-test prototype'
if hasattr(Gui.activeDocument().activeView(),'setAnimationEnabled'):Gui.activeDocument().activeView().setAnimationEnabled(False)
parts=[];printable=[];rows=[]
WHITE=(.86,.88,.89);DARK=(.10,.12,.14);STEEL=(.62,.66,.69);BLUE=(.15,.38,.46);ORANGE=(.79,.38,.12)
def add(name,label,shape,explanation,pos=(0,0,0),color=WHITE,printing=True):
 if not shape.isValid() or len(shape.Solids)!=1 or shape.Volume<=0:raise ValueError('Invalid demonstrator solid: '+name)
 o=doc.addObject('Part::Feature',name);o.Label=label;o.Shape=shape;o.Placement=App.Placement(V(*pos),App.Rotation()).multiply(shape.Placement)
 o.addProperty('App::PropertyString','Explanation','Component').Explanation=explanation
 o.addProperty('App::PropertyString','Status','Component').Status='Fit-test prototype: print one joint coupon first; manually verify free motion before adding a motor.'
 o.addProperty('App::PropertyBool','Printable','Component').Printable=printing
 o.ViewObject.ShapeColor=color;o.ViewObject.DisplayMode='Shaded';parts.append(o)
 row={'name':name,'label':label,'explanation':explanation,'printable':printing,'valid':True,'solids':1,'volume_mm3':shape.Volume}
 if printing:
  file='stl_mm/'+name+'.stl';stl(shape,OUT/file,scale=1);row['file']=file;printable.append(o)
 rows.append(row);return o
def union(shapes):
 s=shapes[0]
 for other in shapes[1:]:s=s.fuse(other)
 return s.removeSplitter()
def ear_pair(L,width=16):
 return [cyl(5,5,(0,-8,L),(0,1,0)),cyl(5,5,(0,3,L),(0,1,0))]
def stops(L):
 return [Part.makeBox(3.0,4.2,5.1,V(-6,-7.2,L-1.1)),Part.makeBox(3.0,4.2,5.1,V(-6,3,L-1.1))]
def segment(L,tip=False):
 if tip:
  body=loft([(5.5,5.6,7.6),(8,6,8),(L-5,5.5,7.4),(L-1,2.8,3.5),(L,.08,.1)])
 else:body=loft([(5.5,5.6,7.6),(L*.42,6,8),(L-3,5.3,7.5)])
 root=cyl(5,5.2,(0,-2.6,0),(0,1,0))
 bridge=Part.makeBox(7,5.2,8,V(-3.5,-2.6,0))
 s=union([body,bridge,root]+([] if tip else ear_pair(L)+stops(L)))
 if not tip:s=s.cut(Part.makeBox(20,6,14,V(-10,-3,L-5.4)))
 s=s.cut(cyl(1.15,20,(0,-10,0),(0,1,0)))
 if not tip:s=s.cut(cyl(1.15,20,(0,-10,L),(0,1,0)))
 s=s.cut(cyl(.7,(L+1.7) if tip else (L+9),(3,0,-5)))
 # Transverse dorsal elastic anchor and distal tendon knot/anchor.
 s=s.cut(cyl(.8,20,(-3,-10,max(7,L*.5)),(0,1,0)))
 if tip:s=s.cut(cyl(.8,20,(3,-10,L-4),(0,1,0)))
 return s.removeSplitter()

base=rounded_box(92,82,5,(-20,-31,0),2)
for x in [-12,64]:
 for y in [-23,43]:base=base.cut(cyl(1.75,7,(x,y,-1)))
add('BenchPlate','01 | bench plate',base,'Separate bench plate with four 3.5 mm holes. Clamp securely for manual and low-power fit testing; no load rating is claimed.')
pillar=rounded_box(16,22,24.6,(-8,-11,5),1.2)
bridges=[Part.makeBox(9,5,10,V(-4.5,-8,25)),Part.makeBox(9,5,10,V(-4.5,3,25))]
pulley_ears=[cyl(5,5,(8,-10,15),(0,1,0)),cyl(5,5,(8,5,15),(0,1,0))]
clevis=union([pillar]+bridges+ear_pair(35)+stops(35)+pulley_ears)
clevis=clevis.cut(Part.makeBox(12,6.6,24,V(2,-3.3,6)))
clevis=clevis.cut(cyl(1.15,24,(0,-12,35),(0,1,0))).cut(cyl(.7,42,(3,0,0))).cut(cyl(1.15,24,(8,-12,15),(0,1,0)))
clevis=clevis.cut(cyl(.8,24,(-4,-12,18),(0,1,0)))
add('FingerRootClevis','02 | root clevis and guide',clevis,'5.2 mm moving tongue fits a 6.0 mm clevis gap (0.4 mm nominal per side). Real 2.3 mm M2 pin bores, 1.4 mm flexor guide and rear stop tabs. Printed fit and actual stop angle require hand testing.')
z=35
for name,L in [('Proximal',40),('Middle',24),('Distal',18)]:
 add(name+'Phalanx','Finger | '+name.lower()+' phalanx',segment(L,name=='Distal'),f'{L} mm nominal joint spacing/tip length. 2.3 mm transverse M2 pin bore; 1.4 mm flexor channel at x=3 mm; 1.6 mm dorsal elastic anchor. Clevis stop tabs limit hyperextension after fit testing.',(0,0,z))
 add(name+'ReferencePin','Hardware | M2 pin at '+name.lower()+' joint',cyl(1,20,(0,-10,0),(0,1,0)),'Unprinted M2 smooth-shank pin or screw reference. Select length and retain both ends without squeezing the hinge; do not use printed pins.',(0,0,z),STEEL,False)
 z+=L
# Side-mounted, slotted generic cradle: body envelope is a verified size only,
# flange/horn offsets are deliberately not asserted compatible.
cradle=union([Part.makeBox(48,46,3,V(25,4,5)),Part.makeBox(3,46,23,V(25,4,5)),Part.makeBox(3,46,23,V(70,4,5))])
# Elongated slots accommodate adjustable clamps/straps after measuring hardware.
for x in [30,66]:
 for y in [10,44]:cradle=cradle.cut(rounded_box(3.6,10,8,(x-1.8,y-5,3),1.5))
add('GenericServoCradle','03 | generic slotted servo cradle',cradle,'Generic side-mounted cradle with 42 mm clear body length and adjustable strap/bolt slots. Hitec D645MW official body envelope is 40.8 x 20.0 x 37.8 mm; flange span and output offset are NOT modeled as a verified fit. Measure the actual servo/horn before printing or drilling.')
servo=rounded_box(40.8,37.8,20,(28.6,8,8),1)
add('ServoEnvelope','Reference | D645MW body envelope',servo,'Unprinted reference envelope from official Hitec drawing: 40.8 x 20.0 x 37.8 mm, shown on its side. Output/horn position here is illustrative, not verified.',color=DARK,printing=False)
# Drum is bolted to an actual purchased horn. No printed spline is supplied.
drum=union([cyl(7,8,(50,-4,17.5),(0,1,0)),cyl(9,1.2,(50,-5.2,17.5),(0,1,0)),cyl(9,1.2,(50,4,17.5),(0,1,0))])
drum=drum.cut(cyl(2,14,(50,-7,17.5),(0,1,0)))
for x in [45,55]:drum=drum.cut(cyl(1.15,14,(x,-7,17.5),(0,1,0)))
drum=drum.cut(cyl(.8,20,(50,-10,24),(0,1,0)))
add('HornMountedDrum','04 | 7 mm-radius tendon drum',drum,'7 mm effective winding radius, 9 mm flanges, center clearance and two 2.3 mm generic horn fixing holes on 10 mm spacing. This is NOT a printed 25T spline. Drill/match the purchased horn and verify fastener clearance before assembly.',color=ORANGE)
pulley=ring(4.5,1.15,5,(8,-2.5,15),(0,1,0))
add('RedirectPulley','05 | flexor redirect pulley',pulley,'Small unpowered redirect pulley with 2.3 mm bore. The flexor passes from the vertical x=3 mm finger channel around this pulley toward the drum. A smooth bushing/bearing may be required after fit testing.',color=BLUE)
add('RedirectAxle','Hardware | redirect axle',cyl(1,20,(8,-10,15),(0,1,0)),'Unprinted M2 smooth-shank axle reference. Add retained supports/washer stack after a dry-fit check.',color=STEEL,printing=False)
# Redirect axle is supported by bores in the integrated root-clevis ears.
# Visible routing is illustrative and is omitted from printable exports.
for i,(a,b) in enumerate([((3,0,113),(3,0,18)),((3,0,18),(3.5,0,15)),((3.5,0,15),(8,0,10.5)),((8,0,10.5),(50,0,10.5))]):
 add('FlexorRoute'+str(i),'Route | single flexor tendon',line_cylinder(a,b,.38),'Illustrative 0.5–0.8 mm cord route; actual joint wrap and knot position must be fitted by hand.',color=ORANGE,printing=False)
add('ElasticReturnRoute','Route | external elastic return',line_cylinder((-6.5,0,24),(-6.5,0,110),.7),'Illustrative external elastic return path along the dorsal side. Lace/anchor to transverse dorsal holes; choose only enough pretension to reopen the unloaded finger.',color=BLUE,printing=False)

doc.recompute()
Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll();Gui.updateGui()
Gui.activeDocument().activeView().saveImage(str(RESULTS/'printable_finger_assembled.png'),1800,1400,'White')
original={o.Name:o.Placement for o in parts}
for o in parts:
 if 'Phalanx' in o.Name:
  p=o.Placement;p.Base=p.Base+V(0,0,10 if o.Name.startswith('Proximal') else 22 if o.Name.startswith('Middle') else 34);o.Placement=p
 elif 'ReferencePin' in o.Name:
  p=o.Placement;p.Base=p.Base+V(0,-24,0);o.Placement=p
 elif o.Name=='ServoEnvelope':o.ViewObject.Visibility=False
 elif o.Name=='HornMountedDrum':
  p=o.Placement;p.Base=p.Base+V(0,-32,0);o.Placement=p
 elif 'Route' in o.Name:o.ViewObject.Visibility=False
Gui.activeDocument().activeView().fitAll();Gui.updateGui();Gui.activeDocument().activeView().saveImage(str(RESULTS/'printable_finger_exploded.png'),1800,1400,'White')
for o in parts:o.Placement=original[o.Name];o.ViewObject.Visibility=True
Gui.activeDocument().activeView().fitAll();doc.recompute();doc.saveAs(str(OUT/'TendonFinger_FitTest.FCStd'));Part.export(parts,str(OUT/'TendonFinger_FitTest.step'))
report={'units':'mm','status':'FIT-TEST PROTOTYPE; not proven motor-compatible or ready for powered operation','parts':rows,'printable_count':len(printable),'hinge_pin_diameter_mm':2.0,'hinge_bore_mm':2.3,'clevis_gap_mm':6.0,'tongue_width_mm':5.2,'tendon_guide_diameter_mm':1.4,'drum_effective_radius_mm':7.0,'servo_body_envelope_mm':[40.8,20.0,37.8],'servo_source':'https://www.hiteccs.com/public/uploads/data_sheet/HCS_D645MW_Specsheetv2.2_102-1729815560.pdf','unvalidated':['Printed fit and supports','Servo flange and output-shaft offsets','Purchased horn fixing holes','Tendon joint wrap and knots','Elastic return anchors and pretension','Stop angle and range','Loads and fatigue']}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(OUT/'READ_ME_FIRST.txt').write_text('SINGLE TENDON FINGER: FIT-TEST PROTOTYPE\n\nUnits are millimetres. These are separate mechanical test parts, not the visual full-arm shells.\n\n1. First print one proximal/middle hinge fit coupon or the two parts. Use an M2 smooth-shank reference pin. Clear/ream the 2.3 mm bores only as needed. The 5.2 mm tongue has 0.4 mm nominal clearance per side in the 6 mm clevis.\n2. Dry-fit the full finger manually. Check that all three joints move freely, the rear stop tabs arrest hyperextension, and no pin/screw head rubs a neighbor. Actual stop angle is unvalidated.\n3. Thread a flexible 0.5–0.8 mm cord through the 1.4 mm flexor channels and distal transverse anchor; keep the path smooth across each hinge. Add a lightly tensioned external elastic return through the dorsal anchor holes.\n4. Measure the actual servo, supplied horn, flange span and output offset. The cradle is generic and slotted. The 40.8 x 20.0 x 37.8 mm Hitec body envelope is verified from its official drawing; complete mount compatibility is NOT verified.\n5. Attach the 7 mm-radius drum to an actual compatible purchased horn. No printed spline is supplied. Drill/match horn fastening as required; keep screws clear of the servo case.\n6. Clamp the base. Test by pulling the tendon by hand before attaching or powering a motor. Use the separate prototype electrical guide and conservative firmware only after manual travel/return tests pass.\n\nThis design has not been printed, assembled, load-tested or powered. Additional shims, retained fasteners, supports and fit adjustments may be required.\n',encoding='utf-8')
(RESULTS/'printable_finger_build.json').write_text(json.dumps({'passed_geometry':True,'printable_parts':len(printable),'total_reference_parts':len(parts),'output':str(OUT)},indent=2),encoding='utf-8')
