"""V3 reference-led 27-axis humanoid arm. Run in portable FreeCAD.

CAD dimensions: millimetres. Exported articulated STL coordinates: metres.
Reference 02/03: continuous white limb fairings, exposed black round bearings.
Reference 10: recessed finger pads, visible hinge cheeks and small fasteners.
Engineering concept; placeholder motors, tendons and joint packages are explicit.
"""
from pathlib import Path
import json, math, struct, traceback
import FreeCAD as App
import FreeCADGui as Gui
import Part, MeshPart
ROOT=Path(r'D:\RoboticArm');DESIGN=ROOT/'design'/'v3';MESHES=DESIGN/'meshes';RESULTS=ROOT/'results'/'v3';STAGES=RESULTS/'design_stages'
for path in [MESHES,STAGES]:path.mkdir(parents=True,exist_ok=True)
V=App.Vector
WHITE=(.87,.89,.90);BLACK=(.075,.085,.095);RUBBER=(.13,.15,.17);METAL=(.49,.53,.57);STEEL=(.70,.73,.76);COPPER=(.58,.29,.12);WIRE=(.13,.28,.34)
spec=json.loads((DESIGN/'robot_spec.json').read_text(encoding='utf-8'));links={x['name']:x for x in spec['links']};places={}
components=[];manifest=[];groups={};locals_by_name={}
doc=App.newDocument('AnthroArm27_ReferenceV3');doc.Label='ANTHRO 27 | reference-led humanoid arm'
if hasattr(Gui.activeDocument().activeView(),'setAnimationEnabled'):Gui.activeDocument().activeView().setAnimationEnabled(False)
for name,label in [('Fixture','00 | separate shoulder mounting fixture'),('Shoulder','01 | three-axis shoulder'),('UpperArm','02 | continuous upper-arm shells'),('Elbow','03 | circular elbow and pronation'),('Forearm','04 | tapered forearm'),('Wrist','05 | compact two-axis wrist'),('Palm','06 | palm chassis and inset pads'),('Fingers','07 | four articulated fingers'),('Thumb','08 | opposable thumb'),('Internal','09 | conceptual motors, cables and skeleton'),('Reference','10 | dimensions and source notes')]:
 g=doc.addObject('App::DocumentObjectGroup',name);g.Label=label;groups[name]=g

def log(txt):
 with (RESULTS/'build_progress.txt').open('a',encoding='utf-8') as f:f.write(txt+'\n')
 print(txt)
def frame(name):
 if name in places:return places[name]
 l=links[name];parent=frame(l['parent']) if l.get('parent') else App.Placement()
 r,p,y=[math.degrees(v) for v in l.get('origin_rpy',[0,0,0])]
 rot=App.Rotation(V(0,0,1),y).multiply(App.Rotation(V(0,1,0),p)).multiply(App.Rotation(V(1,0,0),r))
 j=l.get('joint') or {};rot=rot.multiply(App.Rotation(V(*j.get('axis',[0,0,1])),math.degrees(j.get('home',0))))
 places[name]=parent.multiply(App.Placement(V(*[v*1000 for v in l.get('origin_xyz',[0,0,0])]),rot));return places[name]
def ellipse(z,rx,ry,cx=0,cy=0):
 e=Part.Ellipse(V(),max(rx,ry),min(rx,ry)).toShape()
 if ry>rx:e.rotate(V(),V(0,0,1),90)
 e.translate(V(cx,cy,z));return Part.Wire([e])
def loft(sections):return Part.makeLoft([ellipse(*s) for s in sections],True,False)
def ellipsoid(rx,ry,rz,pos=(0,0,0)):
 m=App.Matrix();m.A11=rx;m.A22=ry;m.A33=rz
 s=Part.makeSphere(1).transformGeometry(m);s.translate(V(*pos));return s
def cyl(r,L,pos=(0,0,0),axis=(0,0,1)):return Part.makeCylinder(r,L,V(*pos),V(*axis))
def ring(ro,ri,L,pos=(0,0,0),axis=(0,0,1)):
 p=V(*pos);v=V(*axis);return cyl(ro,L,pos,axis).cut(cyl(ri,L+2,tuple(p-v),axis))
def rounded_box(dx,dy,dz,pos,r=1):
 s=Part.makeBox(dx,dy,dz,V(*pos))
 if r:
  try:s=s.makeFillet(min(r,min(dx,dy,dz)/2-.05),s.Edges)
  except Exception:pass
 return s
def line_cylinder(a,b,r):
 a=V(*a);b=V(*b);return Part.makeCylinder(r,(b-a).Length,a,b-a)
def stl(shape,path,scale=.001):
 mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.07,AngularDeflection=.13,Relative=False)
 with path.open('wb') as f:
  f.write(('ANTHRO27 V3 '+('METRES' if scale==.001 else 'MILLIMETRES')).encode().ljust(80,b' '));f.write(struct.pack('<I',mesh.CountFacets))
  for fac in mesh.Facets:
   n=fac.Normal;pts=[c*scale for p in fac.Points for c in p];f.write(struct.pack('<12fH',n.x,n.y,n.z,*pts,0))
 return mesh.CountFacets
def add(name,label,shape,link,explanation,color=WHITE,group='Fingers',collision=False,category='exterior',dims=None):
 if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1 or shape.Volume<=0:raise ValueError('Invalid single solid '+name+' solids='+str(len(shape.Solids)))
 o=doc.addObject('Part::Feature',name);o.Label=label;o.Shape=shape;o.Placement=frame(link).multiply(shape.Placement)
 for p,value in [('Explanation',explanation),('RobotLink',link),('Category',category),('ParametricSource',str(DESIGN/'build_reference_arm.py')),('CoordinateFrame','Local +Z along limb to fingertips; +X palmar. CAD mm; mesh m.'),('DesignStatus','Digital concept. Joint packages, motors, cable routing, tolerances and strength require prototype validation.')]:
  o.addProperty('App::PropertyString',p,'Component');setattr(o,p,value)
 j=links[link].get('joint') or {}
 o.addProperty('App::PropertyString','JointName','Kinematics').JointName=j.get('name','fixed')
 o.addProperty('App::PropertyVector','JointAxis','Kinematics').JointAxis=V(*j.get('axis',[0,0,0]))
 o.addProperty('App::PropertyString','JointRangeRad','Kinematics').JointRangeRad=str(j.get('range',[]))
 for p,v in (dims or {}).items():o.addProperty('App::PropertyLength',p,'Design dimensions');setattr(o,p,v)
 o.ViewObject.ShapeColor=color;o.ViewObject.DisplayMode='Shaded';o.ViewObject.Deviation=.07;o.ViewObject.AngularDeflection=8
 groups[group].addObject(o);components.append(o);locals_by_name[name]=shape.copy()
 path=Path('meshes')/(name+'.stl');facets=stl(shape,DESIGN/path);b=shape.BoundBox
 manifest.append(dict(name=name,cad_name=o.Name,label=label,link=link,file=path.as_posix(),rgba=list(color[:3])+[1],explanation=explanation,collision_candidate=collision,category=category,valid=True,solid_count=1,volume_mm3=shape.Volume,facets=facets,bounds_m=[b.XMin*.001,b.YMin*.001,b.ZMin*.001,b.XMax*.001,b.YMax*.001,b.ZMax*.001],dimensions_mm=dims or {}))
 return o
def screw(name,link,pos,r=1.5,axis=(1,0,0),group='Fingers'):
 h=cyl(r,.75,pos,axis);a=V(*axis);p=V(*pos)
 # Small recessed socket makes this a mechanical fastener, not a painted dot.
 socket=cyl(r*.40,.5,tuple(p+a*.40),axis);h=h.cut(socket)
 return add(name,'Fastener | '+name,h,link,'Recessed-head panel fastener envelope. Thread engagement and retention are not yet specified.',BLACK,group,False,'fastener',{'HeadDiameter':r*2})
def pair_shell(prefix,link,sections,group,wall=3.5):
 outer=loft(sections)
 inner=[]
 for i,row in enumerate(sections):
  z,rx,ry,*center=row;z=z-1 if i==0 else z+1 if i==len(sections)-1 else z
  inner.append((z,rx-wall,ry-wall,*center))
 hollow=outer.cut(loft(inner))
 front=hollow.common(Part.makeBox(200,300,500,V(.7,-150,-60)))
 back=hollow.common(Part.makeBox(200,300,500,V(-200.7,-150,-60)))
 add(prefix+'AnteriorShell',prefix+' | anterior hollow fairing',front,link,'Hollow smooth oval-section fairing with a 1.4 mm longitudinal service seam. The broad proximal contour tapers toward the distal joint, following references 02/03.',WHITE,group,True,'removable_shell',{'NominalWall':wall})
 add(prefix+'PosteriorShell',prefix+' | posterior hollow fairing',back,link,'Matching rear fairing closes the human-like limb silhouette. Remove this panel in the cutaway to inspect the conceptual internal skeleton and actuators.',WHITE,group,True,'removable_shell',{'NominalWall':wall})
 return outer

log('01 | shoulder and human arm frame contract: 7 arm + 20 hand axes.')
# Shoulder flange is a detachable fixture, not part of the anatomical limb.
mount=cyl(43,12,(0,-72,0),(0,1,0)).cut(cyl(17,14,(0,-73,0),(0,1,0)))
for x,z in [(26,26),(-26,26),(26,-26),(-26,-26)]:mount=mount.cut(cyl(3.3,14,(x,-73,z),(0,1,0)))
add('ShoulderMountFlange','Fixture | removable shoulder flange',mount,'base_link','Separate four-bolt shoulder attachment flange. It is a fixture interface, not an industrial arm pedestal or a human limb segment. Mounting structure/load rating still require engineering.',METAL,'Fixture',False,'fixture',{'BoltHoleDiameter':6.6,'FlangeDiameter':86})
add('ShoulderSocket','Shoulder | black spherical socket',ellipsoid(49,54,49),'shoulder_abduction','Rounded shoulder socket establishes the proximal human silhouette. The three shoulder axes are co-located kinematically; internal bearing packaging remains conceptual.',BLACK,'Shoulder',True)
for s in [-1,1]:
 add('ShoulderBearing'+str(s),'Shoulder | circular abduction bearing',ring(28,18,5,(s*45,0,0),(1,0,0)),'shoulder_abduction','Exposed circular bearing cover marks the shoulder abduction axis, matching the black mechanical joint language of the references.',METAL,'Shoulder',False)
 add('ShoulderCap'+str(s),'Shoulder | recessed axis cap',cyl(17,5,(s*46,0,0),(1,0,0)),'shoulder_abduction','Recessed shoulder-axis cover; bearing seats, seals and shaft interfaces remain conceptual.',BLACK,'Shoulder',False)
add('ShoulderFlexionGimbal','Shoulder | flexion gimbal ring',ring(41,34,13,(0,-6.5,0),(0,1,0)),'shoulder_flexion','Second shoulder axis carrier inside the spherical joint envelope. This visible internal ring is a packaging concept, not a validated three-axis transmission.',STEEL,'Internal',False,'internal')
add('ShoulderRotationCoupler','Shoulder | humeral rotation coupling',ring(31,19,24,(0,0,15)),'upper_arm','Axial coupling for humeral rotation. Separates shoulder orientation from elbow flexion while continuing the limb silhouette.',BLACK,'Shoulder',False)
upper_sections=[(34,30,34),(58,41,46),(112,43,49),(172,38,44),(226,30,35),(264,24,28)]
pair_shell('UpperArm','upper_arm',upper_sections,'UpperArm',3.5)
for z,rx,ry in [(75,42,47),(220,31,36)]:
 for side in [-1,1]:screw('UpperPanelScrew_'+str(z)+'_'+str(side),'upper_arm',(rx*.81,side*ry*.56,z),2.1,group='UpperArm')
add('HumerusCore','Upper arm | hollow structural spine',ring(16,11,224,(0,0,38)),'upper_arm','Hollow central structural spine reserves a cable passage. This skeleton is a conceptual load path; tube section and bearings must be sized from loads.',METAL,'Internal',False,'internal',{'OuterDiameter':32,'InnerDiameter':22})
add('ShoulderMotorEnvelope','Upper arm | shoulder-drive envelope',cyl(23,58,(0,0,47)),'upper_arm','Placeholder motor/reducer packaging envelope. No supplier, torque rating or verified reducer has been selected.',BLACK,'Internal',False,'internal',{'EnvelopeDiameter':46,'EnvelopeLength':58})
add('ShoulderMotorBand','Upper arm | winding envelope',ring(23.3,22.8,22,(0,0,64)),'upper_arm','Copper-colored band distinguishes the conceptual electric motor region in the cutaway.',COPPER,'Internal',False,'internal')
add('ElbowDriveEnvelope','Upper arm | elbow-drive envelope',cyl(19,65,(0,0,170)),'upper_arm','Conceptual elbow drive inside the upper arm. Reduction, brake, thermal behavior and output torque remain to be engineered.',BLACK,'Internal',False,'internal')
for y in [-12,12]:add('UpperHarness'+str(y),'Upper arm | internal harness',line_cylinder((17,y,105),(14,y,260),1.4),'upper_arm','Illustrative electrical harness route inside the removable fairing. Cable flex loops through the joints are not solved.',WIRE,'Internal',False,'internal')

log('02 | hollow upper-arm fairings and exposed circular elbow built.')
add('ElbowBearingBarrel','Elbow | black circular hinge barrel',cyl(31,64,(0,-32,0),(0,1,0)),'elbow_link','Exposed circular elbow hinge connects the upper-arm and forearm fairings with a recognizably human elbow silhouette. Canonical flexion axis is local Y.',BLACK,'Elbow',True, dims={'BearingEnvelopeDiameter':62})
for side in [-1,1]:
 y=side*32
 add('ElbowRace'+str(side),'Elbow | concentric metal bearing race',ring(26,21,2.5,(0,y,0),(0,1,0)),'elbow_link','Concentric ring makes the circular elbow axis legible; this is an external bearing cover, not a selected bearing.',METAL,'Elbow',False)
 add('ElbowHub'+str(side),'Elbow | inset output hub',cyl(17,3,(0,y+side*.8,0),(0,1,0)),'elbow_link','Black inset elbow output hub with a circular service cap.',BLACK,'Elbow',False)
 for ang in [0,120,240]:
  a=math.radians(ang);screw('ElbowBolt_'+str(side)+'_'+str(ang),'elbow_link',(22*math.cos(a),y+side*2,22*math.sin(a)),1.5,(0,1,0),'Elbow')
add('PronationBearing','Forearm | axial pronation bearing',ring(27,18,23,(0,0,21)),'forearm','Axial bearing permits forearm pronation independently of elbow flexion. The forearm and hand roll together, as in human anatomy.',BLACK,'Elbow',False)
fore_sections=[(34,26,29),(58,31,35),(99,30,34),(151,26,30),(201,21,25),(238,17,21)]
pair_shell('Forearm','forearm',fore_sections,'Forearm',3.0)
for z,rx,ry in [(65,31,35),(206,20.5,24.5)]:
 for side in [-1,1]:screw('ForePanelScrew_'+str(z)+'_'+str(side),'forearm',(rx*.81,side*ry*.56,z),1.7,group='Forearm')
for y in [-9,9]:add('RadiusUlnaRail'+str(y),'Forearm | structural rail',rounded_box(8,5,198,(-4,y-2.5,37),1.3),'forearm','One of two internal longitudinal rails supporting the actuator trays and wrist. Conceptual radius/ulna-inspired structure; no load qualification.',METAL,'Internal',False,'internal')
for row,z in enumerate([54,86,118,150,182]):
 for col,y in enumerate([-18,-6,6,18]):
  i=row*4+col
  add('HandActuator%02d'%i,'Forearm | hand actuator envelope %02d'%(i+1),rounded_box(15,9.5,24,(-7.5,y-4.75,z),1.0),'forearm','One of twenty small actuator packaging envelopes for the independently controlled hand axes. This is an arrangement study; actual motors, transmissions, tendons and heat rejection are unselected.',BLACK,'Internal',False,'internal',{'EnvelopeDepth':15,'EnvelopeWidth':9.5,'EnvelopeLength':24})
  add('TendonSpool%02d'%i,'Forearm | conceptual tendon spool %02d'%(i+1),cyl(3.5,8.5,(8,y-4.25,z+20),(0,1,0)),'forearm','Conceptual spool marks the motor-to-tendon conversion. Twenty independent simulation actuators are not claimed to be a fabricated tendon drive.',COPPER,'Internal',False,'internal')
  add('TendonGuide%02d'%i,'Forearm | tendon route %02d'%(i+1),line_cylinder((10,y,z+20),(10,y*.55,233),.45),'forearm','Illustrative tendon route to the wrist guide. Joint-crossing pulley geometry, antagonistic routing and pretension still require design.',WIRE,'Internal',False,'internal')

log('03 | tapered hollow forearm, internal drive bank and slim two-axis wrist built.')
add('WristFlexionBall','Wrist | compact flexion joint',ellipsoid(19,22,19),'wrist_pitch','Compact black wrist articulation keeps the forearm-to-palm transition slim. Flexion occurs about local Y.',BLACK,'Wrist',True)
add('WristCarpalCoupler','Wrist | tapered carpal coupling',loft([(9,15,18),(18,13,19),(30,11,22),(39,10.5,24)]),'wrist_pitch','Slim coupling transitions from the forearm to the wider, flattened palm. The next co-located hand-side axis provides radial/ulnar deviation.',METAL,'Wrist',False)
for side in [-1,1]:add('WristFlexionCap'+str(side),'Wrist | recessed flexion-axis cap',cyl(6,2,(0,side*22,0),(0,1,0)),'wrist_pitch','Small circular wrist cap exposes the local Y flexion axis without a bulky industrial wrist drum.',BLACK,'Wrist',False)
add('WristDeviationSeal','Wrist | palm deviation seal',loft([(-3,10.5,23),(0,11.1,24),(3,11.4,24.5)]),'palm_base','Dark oval seam marks the radial/ulnar deviation boundary at the palm base. Soft deformation is not simulated.',BLACK,'Wrist',False)

def rounded_prism(dx,dy,dz,pos,r=1.2):return rounded_box(dx,dy,dz,pos,r)
def inset(body,pocket,recess=.22):
 pad=body.common(pocket);rest=body.cut(pocket)
 pad.translate(V(-recess,0,0))
 return rest,pad

palm_outer=loft([(0,10.5,24,0,0),(12,12.5,28,0,2),(31,14,35,0,5),(59,14,40,0,1),(84,12,41,0,0),(98,8.5,37,0,0)])
# A true internal cavity, plus real pad pocket and a split dorsal access panel.
palm_cavity=loft([(8,7.3,21,0,0),(30,10.3,29,0,3),(59,10.3,34,0,0),(85,8.4,34,0,0),(92,5,30,0,0)])
palm_hollow=palm_outer.cut(palm_cavity)
pocket=rounded_prism(12,55,54,(7.5,-29,36),6)
palm_cut,palm_pad=inset(palm_hollow,pocket,.25)
front=palm_cut.common(Part.makeBox(100,160,130,V(.5,-80,-10)))
back=palm_cut.common(Part.makeBox(100,160,130,V(-100.5,-80,-10)))
add('PalmAnteriorChassis','Palm | hollow front chassis with pad recess',front,'palm_base','Asymmetric smooth palm fairing with a genuine internal cavity and recessed contact-pad pocket. The thumb-side flare integrates the thenar region into the palm body instead of using separate oval mounds.',WHITE,'Palm',True,'removable_shell',{'PalmLength':100,'PalmWidth':84,'NominalWall':3.5})
add('PalmDorsalCover','Palm | removable sculpted dorsal cover',back,'palm_base','Sculpted white rear cover follows the palm outline and closes the internal cavity. Small perimeter fasteners distinguish the mechanical construction.',WHITE,'Palm',True,'removable_shell')
add('PalmInsetPad','Palm | recessed continuous flexor pad',palm_pad,'palm_base','Dark flexor pad is seated 0.25 mm below a matching CAD pocket, sharing the palm contour. Elastomer material, tactile sensing and attachment are placeholders.',RUBBER,'Palm',True)
add('PalmInternalPlate','Palm | internal actuator routing plate',rounded_box(3,54,71,(-1.5,-27,17),3),'palm_base','Internal routing/chassis plate visible in the cutaway. Tendon terminations and electronics placement are conceptual.',METAL,'Internal',False,'internal')
for side in [-1,1]:
 for z in [18,79]:screw('PalmCoverScrew_'+str(side)+'_'+str(z),'palm_base',(-11,side*25,z),1.1,(-1,0,0),'Palm')
for digit,y,z in [('index',30,100),('middle',10,100),('ring',-10,100),('pinky',-30,95)]:
 add(digit+'MCPMount','Palm | '+digit+' MCP bearing seat',cyl(7.6,14.5,(-7.25,y,z),(1,0,0)),'palm_base','Compact palm-side bearing seat supports lateral finger spread. Its circular opening makes the two-axis MCP mechanism visible.',BLACK,'Palm',False)

def finger_length(name):
 c=[l for l in links.values() if l.get('parent')==name and l.get('origin_xyz',[0,0,0])[2]>.001]
 if c:return max(l['origin_xyz'][2]*1000 for l in c)
 return {'index':18,'middle':20,'ring':18,'pinky':17,'thumb':15}[name.split('_')[0]]
def finger(link,width,depth):
 L=finger_length(link);rx=depth/2;ry=width/2;distal=link.endswith('distal');group='Thumb' if link.startswith('thumb') else 'Fingers'
 if distal:sections=[(1.2,rx*.86,ry*.94),(3,rx*.99,ry),(L*.42,rx,ry*.97),(L*.70,rx*.86,ry*.83),(L*.90,rx*.50,ry*.52),(L*.99,rx*.12,ry*.14),(L,.04,.05)]
 else:sections=[(1.8,rx*.88,ry*.95),(L*.15,rx,ry),(L*.42,rx*.98,ry*.97),(L*.72,rx*.94,ry*.94),(L-1.8,rx*.87,ry*.91)]
 body=loft(sections)
 # Two explicit longitudinal tendon-guide bores in every phalanx envelope.
 for x in [-2.5,2.5]:body=body.cut(cyl(.7,L+2,(x,0,-1)))
 pL=L*(.55 if distal else .59);pY=width*.60
 pocket=rounded_prism(9,pY,pL,(rx*.56,-pY/2,L*.49-pL/2),min(1.6,pL/5))
 body,pad=inset(body,pocket,.23)
 dorsal=body.common(Part.makeBox(70,70,L+10,V(-70.25,-35,-3)))
 flexor=body.common(Part.makeBox(70,70,L+10,V(.25,-35,-3)))
 for suffix,part,description in [('DorsalShell',dorsal,'Dorsal white shell panel with a central mechanical seam.'),('FlexorShell',flexor,'Flexor white shell panel with a true recessed pad opening.')]:
  add(link+suffix,link.replace('_',' ').title()+' | '+suffix,part,link,description+f' {L:g} mm nominal joint spacing/tip length; oval tapered cross sections, two 1.4 mm tendon-guide bores. Actuator packaging and joint-crossing tendons remain conceptual.',WHITE,group,True,dims={'JointSpacing':L,'Width':width,'Depth':depth,'TendonGuideDiameter':1.4})
 add(link+'InsetPad',link.replace('_',' ').title()+' | recessed flexor pad',pad,link,'Flush-contour black flexor insert seated 0.23 mm below its matching rounded rectangular pocket. Friction is modeled; soft deformation and tactile electronics are not.',RUBBER,group,True)
 add(link+'Core',link.replace('_',' ').title()+' | internal keel',cyl(2.7,max(3,L-7),(0,0,3.5)),link,'Dark internal keel is visible in the panel seam. Full internal phalanx structure and tendon pulleys require mechanical development.',BLACK,'Internal',False,'internal')
 # Exposed metallic hinge cheeks and real through bores flank the soft knuckle.
 add(link+'HingeBarrel',link.replace('_',' ').title()+' | root hinge barrel',cyl(4.0,width*.61,(0,-width*.305,0),(0,1,0)).cut(cyl(1.2,width*.7,(0,-width*.35,0),(0,1,0))),link,'Root hinge barrel has a real 2.4 mm transverse pin bore. This is a mechanical hinge envelope; complete bearing fits are not qualified.',BLACK,group,False,dims={'PinBoreDiameter':2.4})
 for side in [-1,1]:
  y=side*(width*.43)
  add(link+'Cheek'+str(side),link.replace('_',' ').title()+' | metal hinge cheek',ring(3.4,1.2,1.6,(0,y,0),(0,1,0)),link,'Exposed ring-shaped hinge cheek and pin opening echo the mechanical detail in reference 10.',METAL,group,False)
 add(link+'Pin',link.replace('_',' ').title()+' | reference hinge pin',cyl(1.05,width+2,(0,-width/2-1,0),(0,1,0)),link,'2.1 mm diameter reference pin in the 2.4 mm concept bore. Production tolerances and retention must be tested.',STEEL,group,False,dims={'PinDiameter':2.1})
 for side in [-1,1]:
  for frac in ([.32] if distal else [.24,.75]):screw(link+'Screw_'+str(side)+'_'+str(frac),link,(rx*.80,side*ry*.57,L*frac),.58,group=group)
 return body

log('04 | hollow palm, recessed pads and detailed finger shell panels built.')
for digit,w in [('index',17.8),('middle',18.2),('ring',17.2),('pinky',15.2)]:
 add(digit+'MCPUniversal','Knuckle | '+digit+' spread carrier',cyl(6.5,12,(-6,0,0),(1,0,0)),digit+'_knuckle','Cross-axis MCP carrier supplies independent spread plus flexion. Axes coincide at the anatomical knuckle center.',METAL,'Fingers',False)
 for seg,f,d in [('proximal',1,14),('intermediate',.89,12.6),('distal',.82,11.8)]:finger(digit+'_'+seg,w*f,d if digit!='pinky' else d*.90)
add('ThumbOppositionHub','Thumb | black CMC opposition hub',cyl(11,13,(0,0,-6.5)),'thumb_opposition','Circular CMC hub connects the thumb directly to the flared palm side. Opposition turns the thumb plane around the canonical local -Z axis.',BLACK,'Thumb',False)
add('ThumbOppositionRing','Thumb | recessed CMC bearing race',ring(10,7.5,1.5,(0,0,6)),'thumb_opposition','Metal CMC race identifies thumb opposition and makes the mechanical connection to the palm visible.',METAL,'Thumb',False)
for seg,w,d in [('metacarpal',20,16),('proximal',18,14.4),('distal',17,13.8)]:finger('thumb_'+seg,w,d)

note=doc.addObject('App::FeaturePython','DesignNotes');note.Label='READ ME | V3 design intent and engineering limits'
note.addProperty('App::PropertyStringList','Notes','Project').Notes=[
 '27 commanded axes: shoulder3, elbow1, forearm1, wrist2, hand20.',
 'References 02/03 guide full-limb proportions and white fairings; reference10 guides hand details.',
 'Every STL is the exact corresponding native solid in local body coordinates; CAD mm, simulation m.',
 'Hollow limb fairings, palm cavity, recessed pad pockets and tendon-guide holes are real CAD geometry.',
 'Internal motors, reducer bodies, spools and cables are packaging envelopes, not certified hardware.',
 'No strength, thermal, bearing, tendon, fabrication-fit or physical safety validation is implied.',
 'Select a component for Explanation, RobotLink, joint metadata and nominal dimensions.'
];groups['Reference'].addObject(note)
doc.recompute()
def visible(pred):
 for o in components:o.ViewObject.Visibility=pred(o)
 Gui.updateGui()
def view(back):
 b=V(*back);b.normalize();r=V(0,0,1).cross(b);r.normalize();u=b.cross(r)
 Gui.activeDocument().activeView().setCameraOrientation(App.Rotation(r,u,b,'ZXY').Q);Gui.activeDocument().activeView().fitAll()
def hand_view(palmar=True):
 p=frame('palm_base').Rotation;r=App.Rotation(V(0,1 if palmar else -1,0),V(0,0,1),V(1 if palmar else -1,0,0),'ZXY')
 Gui.activeDocument().activeView().setCameraOrientation(p.multiply(r).Q);Gui.activeDocument().activeView().fitAll()
def shot(filename):
 Gui.updateGui();Gui.activeDocument().activeView().saveImage(str(STAGES/filename),1800,1400,'White');log('Rendered '+filename)
external=lambda o:o.Category!='internal' and o.Category!='fixture'
visible(external);view((1.3,-2.1,.7));shot('01_full_arm_front.png')
view((-1.3,2.1,.7));shot('02_full_arm_back.png')
ishand=lambda o:o.RobotLink=='palm_base' or o.RobotLink.startswith(('index','middle','ring','pinky','thumb'))
visible(lambda o:ishand(o) and o.Category!='internal');hand_view(True);shot('03_hand_palmar.png')
hand_view(False);shot('04_hand_dorsal.png')
visible(lambda o:o.Category!='fixture' and not ('AnteriorShell' in o.Name or o.Name=='PalmAnteriorChassis' or o.Name.endswith('FlexorShell')));view((1.4,-2,.8));shot('05_cutaway.png')
original={o.Name:o.Placement for o in components}
visible(lambda o:o.Category!='fixture')
for o in components:
 if o.Category=='removable_shell':
  direction=1 if ('Anterior' in o.Name) else -1
  delta=frame(o.RobotLink).Rotation.multVec(V(85*direction,0,0));p=o.Placement;p.Base=p.Base+delta;o.Placement=p
view((1.3,-2.1,.7));shot('06_exploded.png')
for o in components:o.Placement=original[o.Name]
visible(lambda o:o.RobotLink in ['base_link','shoulder_abduction','shoulder_flexion','upper_arm'] and o.Category!='internal');view((1.4,-2,.8));shot('07_shoulder.png')
visible(lambda o:o.RobotLink in ['elbow_link','forearm'] and o.Category!='internal');view((1.4,-2,.7));shot('08_elbow_forearm.png')
visible(lambda o:o.RobotLink in ['wrist_pitch','palm_base'] and o.Category!='internal');hand_view(True);shot('09_wrist_palm.png')
visible(external);view((1.3,-2.1,.7))
doc.recompute();doc.saveAs(str(DESIGN/'AnthroArm27_ReferenceV3.FCStd'));Part.export(components,str(DESIGN/'AnthroArm27_ReferenceV3.step'))
payload={'schema_version':3,'mesh_units':'m','cad_units':'mm','spec':'robot_spec.json','components':manifest,'count':len(manifest),'valid':all(c['valid'] for c in manifest),'arm_dof':7,'hand_dof':20,'total_dof':27,'meshing':{'linear_deflection_mm':.07,'angular_deflection_rad':.13},'references':['reference_02.png','reference_03.png','reference_10.png'],'limitations':'Digital concept. Motors, tendons, transmissions and structural sizes are illustrative; not fabrication-ready or safety-certified.'}
(DESIGN/'anatomical_manifest.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
(DESIGN/'components.txt').write_text('V3 COMPONENT EXPLANATIONS\n\n'+'\n\n'.join(c['label']+'\nLink: '+c['link']+'\n'+c['explanation'] for c in manifest),encoding='utf-8')
log('V3_BUILD_COMPLETE '+str(len(manifest))+' valid solids. All files in D:\\RoboticArm\\design\\v3.')
