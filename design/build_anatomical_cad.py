"""Humanoid revision 2. FreeCAD millimetres; articulated STL exports in metres.

Run the paired FCMacro in portable FreeCAD. Smooth solid oval-section lofts
retain the canonical robot_spec.json frames and actuator pivots.
"""
from pathlib import Path
import json, math, struct, traceback
import FreeCAD as App
import FreeCADGui as Gui
import Part, MeshPart

ROOT = Path(r'D:\RoboticArm')
DESIGN = ROOT/'design'
MESHES = DESIGN/'meshes'/'humanoid'
STAGES = ROOT/'results'/'design_stages'
MESHES.mkdir(parents=True, exist_ok=True)
STAGES.mkdir(parents=True, exist_ok=True)
V=App.Vector
WHITE=(.89,.91,.92)
SOFT=(.31,.34,.36)
SILVER=(.63,.67,.71)
DARK=(.13,.16,.18)
spec=json.loads((DESIGN/'robot_spec.json').read_text(encoding='utf-8'))
links=spec['links']
by_name={x['name']:x for x in links}
placements={}
manifest=[]
components=[]
shapes={}

def progress(message):
    with (ROOT/'results'/'anatomical_build_progress.txt').open('a',encoding='utf-8') as f:
        f.write(message+'\n')
    print(message)

def placement(name):
    if name in placements: return placements[name]
    l=by_name[name]
    p=placement(l['parent']) if l.get('parent') else App.Placement()
    r,pi,y=[math.degrees(q) for q in l.get('origin_rpy',[0,0,0])]
    rot=App.Rotation(V(0,0,1),y).multiply(App.Rotation(V(0,1,0),pi)).multiply(App.Rotation(V(1,0,0),r))
    j=l.get('joint') or {}
    rot=rot.multiply(App.Rotation(V(*j.get('axis',[0,0,1])),math.degrees(j.get('home',0))))
    q=p.multiply(App.Placement(V(*[v*1000 for v in l.get('origin_xyz',[0,0,0])]),rot))
    placements[name]=q
    return q

def ellipse(z,rx,ry,cx=0,cy=0):
    e=Part.Ellipse(V(0,0,0),max(rx,ry),min(rx,ry)).toShape()
    if ry>rx: e.rotate(V(),V(0,0,1),90)
    e.translate(V(cx,cy,z))
    return Part.Wire([e])

def loft(sections):
    # Smooth (non-ruled) closed solid loft through anatomically tapered ovals.
    s=Part.makeLoft([ellipse(*row) for row in sections],True,False)
    if not s.isValid(): raise ValueError('Invalid smooth loft')
    return s

def ellipsoid(rx,ry,rz,pos=(0,0,0)):
    m=App.Matrix()
    m.A11=rx; m.A22=ry; m.A33=rz
    s=Part.makeSphere(1).transformGeometry(m)
    s.translate(V(*pos))
    return s

def cylinder(radius,length,pos=(0,0,0),axis=(0,0,1)):
    return Part.makeCylinder(radius,length,V(*pos),V(*axis))

def stl_binary(shape,path):
    mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.06,AngularDeflection=.12,Relative=False)
    # Explicit little-endian binary STL avoids reader ambiguity and fixes unit scale.
    with path.open('wb') as f:
        f.write(b'ANTHRO25 humanoid local-body coordinates METRES'.ljust(80,b' '))
        f.write(struct.pack('<I',mesh.CountFacets))
        for facet in mesh.Facets:
            n=facet.Normal
            points=[c*.001 for p in facet.Points for c in p]
            f.write(struct.pack('<12fH',n.x,n.y,n.z,*points,0))
    return mesh.CountFacets

old=App.openDocument(str(DESIGN/'AnthroArm25.FCStd'))
doc=App.newDocument('AnthroArm25_Humanoid')
doc.Label='ANTHRO 25 | anatomical humanoid hand'
App.setActiveDocument(doc.Name)
groups={}
for name,label in [('Arm','01 | arm and wrist'),('Palm','02 | contoured palm'),('Fingers','03 | four articulated fingers'),('Thumb','04 | opposable thumb'),('Reference','05 | dimensions and notes')]:
    g=doc.addObject('App::DocumentObjectGroup',name);g.Label=label;groups[name]=g

def add(name,label,shape,link,explanation,color=WHITE,group='Fingers',collision=False,dimensions=None):
    if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1 or shape.Volume<=0:
        raise ValueError('Invalid single solid: '+name)
    obj=doc.addObject('Part::Feature',name)
    obj.Label=label;obj.Shape=shape;obj.Placement=placement(link).multiply(shape.Placement)
    for prop,value in [('Explanation',explanation),('RobotLink',link),('ParametricSource',str(DESIGN/'build_anatomical_cad.py')),('CoordinateFrame','Local +Z to fingertip; +X palmar; +Y flexion hinge. CAD mm; exported meshes m.'),('DesignStatus','Digital concept: dimensions and articulation are specified; hardware actuation, strength, fits and soft material are not validated.')]:
        obj.addProperty('App::PropertyString',prop,'Component');setattr(obj,prop,value)
    j=by_name[link].get('joint') or {}
    obj.addProperty('App::PropertyString','JointName','Kinematics').JointName=j.get('name','fixed')
    obj.addProperty('App::PropertyVector','JointAxis','Kinematics').JointAxis=V(*j.get('axis',[0,0,0]))
    obj.addProperty('App::PropertyString','JointRangeRad','Kinematics').JointRangeRad=str(j.get('range',[]))
    obj.addProperty('App::PropertyAngle','HomeAngle','Kinematics').HomeAngle=math.degrees(j.get('home',0))
    for key,val in (dimensions or {}).items():
        obj.addProperty('App::PropertyLength',key,'Design dimensions');setattr(obj,key,val)
    obj.ViewObject.ShapeColor=color;obj.ViewObject.LineColor=(.20,.22,.24)
    # No edge overlay: continuous surfaces show the actual organic loft.
    obj.ViewObject.DisplayMode='Shaded'
    obj.ViewObject.LineWidth=1.0
    obj.ViewObject.Deviation=.12
    obj.ViewObject.AngularDeflection=10
    obj.ViewObject.Visibility=True
    groups[group].addObject(obj);components.append(obj);shapes[name]=shape
    file=Path('meshes')/'humanoid'/(name+'.stl')
    facets=stl_binary(shape,DESIGN/file)
    b=shape.BoundBox
    manifest.append(dict(name=name,label=label,link=link,file=file.as_posix(),rgba=list(color[:3])+[1],explanation=explanation,collision_candidate=collision,valid=True,solid_count=1,volume_mm3=shape.Volume,facets=facets,bounds_m=[b.XMin*.001,b.YMin*.001,b.ZMin*.001,b.XMax*.001,b.YMax*.001,b.ZMax*.001],dimensions_mm=dimensions or {}))
    return obj

# Keep existing arm solids and exact canonical placements. New visual pipeline
# exports every part, allowing CAD and simulator to use the identical geometry.
for o in old.Objects:
    link=getattr(o,'RobotLink','')
    if link not in ['base_link','waist_link','upper_arm','forearm','wrist_link']: continue
    local=o.Shape.copy()
    local.Placement=App.Placement()
    add(o.Name,o.Label,local,link,getattr(o,'Explanation','Arm component from original design.'),tuple(o.ViewObject.ShapeColor),'Arm',False)
App.closeDocument(old.Name)
App.setActiveDocument(doc.Name)
add('WristFlexionBoot','Wrist | rounded flexion joint cover',ellipsoid(33,31,33),'wrist_link','Smooth rounded external joint cover encloses the inherited forearm-to-wrist shell intersection. This visual cover represents a future flexible boot; it is excluded from rigid collision response and does not change the validated wrist articulation.',DARK,'Arm',False,{'CoverWidth':62,'CoverDepth':66,'CoverHeight':66})

progress('01 dimensions and canonical joint frames retained: 190 mm hand; 84 mm palm; 20 hand axes.')

# A solid palm broadens gradually from the wrist and subtly arches dorsally.
palm=loft([(0,10.5,24,0,0),(8,12,26,0,0),(27,14,33,.5,1),(53,14.5,39,.5,0),(78,12.8,41,0,0),(92,10.5,39.5,0,0),(98,8.0,36,0,0)])
add('AnatomicalPalm','Palm | tapered metacarpal shell',palm,'palm_base','Smooth oval-section palm widens from a 48 mm wrist to an 82–84 mm metacarpal span. Four rounded knuckle lobes meet the finger roots. This surface defines the human-like palm envelope; internal actuation remains conceptual.',WHITE,'Palm',True,{'PalmLength':100,'PalmWidth':84,'WristWidth':48})
for digit,y,z,w in [('Index',30,96,9),('Middle',10,97,9),('Ring',-10,97,9),('Pinky',-30,92,8.5)]:
    add(digit+'MetacarpalLobe',digit+' | rounded metacarpal lobe',ellipsoid(8.5,w,7,(0,y,z)),'palm_base','Rounded palm-side knuckle transition joins the broad metacarpal contour to the corresponding articulated MCP carrier.',WHITE,'Palm',False)
thenar=ellipsoid(11,19.5,27,(2.5,31,34))
add('ThenarEminence','Palm | rounded thenar eminence',thenar,'palm_base','The rounded muscular mound at the thumb base creates the asymmetric human palm silhouette and bridges the wrist to the thumb CMC socket. It is a rigid visual/collision envelope, not simulated muscle.',WHITE,'Palm',True)
add('HypothenarEminence','Palm | hypothenar contour',ellipsoid(7,11,27,(7,-29,40)),'palm_base','A smaller rounded mound on the little-finger side completes the palm contour and provides a curved support surface.',WHITE,'Palm',True)
add('CentralPalmPad','Palm | curved compliant contact insert',ellipsoid(2.8,22,26,(13,0,64)),'palm_base','Oval, softly domed palmar contact insert. Frictional contact is modeled in physics; real elastomer compliance, durometer and attachment are not yet engineered.',SOFT,'Palm',True)
add('ThenarPad','Palm | curved thenar contact insert',ellipsoid(2.3,10.5,18.5,(12,27,35)),'palm_base','Curved thumb-base contact insert follows the thenar mound, helping the palm support objects during opposition.',SOFT,'Palm',True)
add('DorsalPalmPanel','Palm | smooth dorsal service cover',ellipsoid(1.6,31,37,(-13,0,52)),'palm_base','A thin rounded dorsal service panel follows the back-of-hand contour. Production fasteners and sealing remain to be selected.',SILVER,'Palm',False)
add('WristSoftSeal','Wrist | soft annular transition',loft([(-3,10.5,23),(0,11,24),(3,11.3,24.4)]),'palm_base','Narrow soft transition at the wrist preserves the natural palm taper while making the roll boundary visible.',DARK,'Palm',False)
progress('02 smooth palm, thenar, hypothenar and curved palmar inserts built.')

def length(link):
    children=[v for v in links if v.get('parent')==link and v['origin_xyz'][2]>.001]
    if children: return max(v['origin_xyz'][2]*1000 for v in children)
    return {'index':18,'middle':20,'ring':18,'pinky':17,'thumb':15}[link.split('_')[0]]

def finger_segment(link,width,depth):
    L=length(link);distal=link.endswith('distal');group='Thumb' if link.startswith('thumb') else 'Fingers'
    rx=depth/2;ry=width/2
    if distal:
        sec=[(.65,rx*.82,ry*.91),(3,rx*.98,ry),(L*.43,rx,ry*.97),(L*.70,rx*.86,ry*.83),(L*.89,rx*.55,ry*.56),(L*.98,rx*.18,ry*.20),(L,.04,.06)]
    else:
        sec=[(.7,rx*.91,ry*.97),(L*.12,rx,ry*1.02),(L*.38,rx*.99,ry*.99),(L*.66,rx*.96,ry*.96),(L*.88,rx*.95,ry*.98),(L-.65,rx*.89,ry*.93)]
    body=loft(sec)
    add(link+'Shell',link.replace('_',' ').title()+' | smooth tapered shell',body,link,f'{L:g} mm joint spacing / terminal tip length. Smooth oval cross sections create a rounded knuckle, narrowed shaft and '+('fully rounded fingertip.' if distal else 'rounded distal knuckle.')+' The shell follows its actual articulation frame; it is a solid digital envelope, not a fabrication-ready tendon housing.',WHITE,group,True,{'JointSpacing':L,'NominalWidth':width,'NominalDepth':depth})
    # A short organic crease covers the root seam without changing axis position.
    seal=loft([(-.55,rx*.76,ry*.82),(0,rx*.83,ry*.89),(.6,rx*.80,ry*.87)])
    add(link+'Crease',link.replace('_',' ').title()+' | soft joint crease',seal,link,'Short oval soft seam marks the flexion boundary and conceals the hinge interior. Rotation remains about the exact canonical Y hinge; soft deformation is not simulated.',DARK,group,False)
    pin=cylinder(1.05,width+.1,(0,-width/2-.05,0),(0,1,0))
    add(link+'Pin',link.replace('_',' ').title()+' | hinge axis pin',pin,link,'Brushed-metal 2.1 mm reference pin makes the anatomical hinge axis visible. Pin fits, bearings and retention are conceptual.',SILVER,group,False,{'PinDiameter':2.1})
    # Contact surfaces are oval domes, never box stickers.
    pz=L*.51;prz=L*(.34 if distal else .30)
    pad=ellipsoid(1.45,ry*.70,prz,(rx*.86,0,pz))
    add(link+'Pad',link.replace('_',' ').title()+' | soft curved pad',pad,link,'Rounded oval palmar pad with domed contact surface. The contact shape and hinge follow the CAD mesh; friction is idealized and no tactile electronics are yet specified.',SOFT,group,True)
    if distal:
        nail=ellipsoid(.75,ry*.62,L*.25,(-rx*1.02,0,L*.53))
        add(link+'Nail',link.split('_')[0].title()+' | dorsal fingertip shield',nail,link,'A thin rounded dorsal fingertip shield echoes a human nail and protects the terminal shell; it is rigid and moves with the distal phalanx.',SILVER,group,False)

for digit,basew in [('index',17.8),('middle',18.2),('ring',17.2),('pinky',15.2)]:
    add(digit+'MCPBall',digit.title()+' | rounded MCP carrier',ellipsoid(7.2,basew/2,6.4),digit+'_knuckle','Rounded two-axis knuckle carrier supports independent finger spread and flexion at the same MCP center. Bearing/transmission hardware remains conceptual.',SILVER,'Fingers',False)
    for seg,factor,depth in [('proximal',1,14),('intermediate',.89,12.6),('distal',.82,11.8)]:
        finger_segment(digit+'_'+seg,basew*factor,depth if digit!='pinky' else depth*.90)
progress('03 four digits built from smooth oval-section phalanges, crease rings and rounded tips.')
add('ThumbCMCSocket','Thumb | rounded opposition socket',ellipsoid(9,10,9),'thumb_opposition','Saddle-joint-inspired spherical envelope at the canonical CMC opposition axis. Together with the metacarpal flexion axis this turns the thumb across the palm.',SILVER,'Thumb',False)
for seg,w,d in [('metacarpal',20,16),('proximal',18,14.4),('distal',17,13.8)]: finger_segment('thumb_'+seg,w,d)
progress('04 four-axis opposable thumb built with thenar integration.')

note=doc.addObject('App::FeaturePython','DesignReadMe');note.Label='READ ME | anatomical geometry and limitations'
note.addProperty('App::PropertyStringList','DesignNotes','Project').DesignNotes=[
    'Revision 2: smooth humanoid shells, rounded knuckles, thumb mound, oval pads and dorsal fingertip shields.',
    '25 independently commanded axes: 5 arm, 20 hand. Dimensions/frames remain robot_spec.json.',
    '190 mm wrist-to-middle-tip scale; CAD mm, simulation meshes m.',
    'Select any component and read Component > Explanation or Design dimensions.',
    'Every visible solid is exported into simulation in the identical local body frame.',
    'Collision envelopes and physical compliance are approximations; see simulation validation.',
    'Digital concept only. Motors, tendons, structural capacity, production tolerances and safety still require hardware engineering.'
]
groups['Reference'].addObject(note)
doc.recompute()
# FreeCAD Shaded renders smooth faces without tessellation or seam edge overlays.
for o in components: o.ViewObject.DisplayMode='Shaded'
Gui.activeDocument().activeView().setAnimationEnabled(False) if hasattr(Gui.activeDocument().activeView(),'setAnimationEnabled') else None

def show_links(predicate):
    for o in components: o.ViewObject.Visibility=predicate(o.RobotLink,o.Name)
    Gui.updateGui()

def camera(palmar=True,tilt=0):
    p=placement('palm_base').Rotation
    # Right-handed camera basis: right=+Y, up=+Z, viewer=+X for palmar view.
    r=App.Rotation(V(0,1 if palmar else -1,0),V(0,0,1),V(1 if palmar else -1,0,0),'ZXY')
    if tilt: r=App.Rotation(V(0,0,1),tilt).multiply(r)
    Gui.activeDocument().activeView().setCameraOrientation(p.multiply(r).Q)
    Gui.activeDocument().activeView().fitAll()

def image(name):
    Gui.updateGui()
    Gui.activeDocument().activeView().saveImage(str(STAGES/name),1600,1200,'White')
    progress('Rendered '+name)

# Stage 01 shows canonical skeleton and dimension guides, not an illustrative mock-up.
refs=[]
def ref_shape(name,shape,color=(.08,.45,.62)):
    o=doc.addObject('Part::Feature',name);o.Shape=shape;o.Placement=placement('palm_base');o.ViewObject.ShapeColor=color;o.ViewObject.LineColor=color;o.ViewObject.LineWidth=2;groups['Reference'].addObject(o);refs.append(o);return o
for digit in ['index','middle','ring','pinky']:
    l=by_name[digit+'_knuckle'];y=l['origin_xyz'][1]*1000;z=l['origin_xyz'][2]*1000
    zpos=z
    for seg in ['proximal','intermediate','distal']:
        L=length(digit+'_'+seg)
        ref_shape('DimensionBone_'+digit+'_'+seg,cylinder(1.15,L,(0,y,zpos)))
        ref_shape('DimensionPivot_'+digit+'_'+seg,Part.makeSphere(2.6,V(0,y,zpos)))
        zpos+=L
for seg in ['metacarpal','proximal','distal']:
    link='thumb_'+seg;L=length(link)
    rp=placement('palm_base').inverse().multiply(placement(link))
    a=rp.multVec(V());b=rp.multVec(V(0,0,L))
    ref_shape('DimensionBone_thumb_'+seg,Part.makeCylinder(1.15,L,a,rp.Rotation.multVec(V(0,0,1))))
    ref_shape('DimensionPivot_thumb_'+seg,Part.makeSphere(2.6,a))
ref_shape('PalmDimensionOutline',Part.makePolygon([V(0,-24,0),V(0,24,0),V(0,42,90),V(0,42,100),V(0,-42,100),V(0,-42,90),V(0,-24,0)]))
ref_shape('LengthDimension',Part.makePolygon([V(0,-53,0),V(0,-61,0),V(0,-57,0),V(0,-57,190),V(0,-61,190),V(0,-53,190)]))
ref_shape('WidthDimension',Part.makePolygon([V(0,-42,102),V(0,-42,111),V(0,42,111),V(0,42,102)]))
def annotation(name,txt,pos):
    o=doc.addObject('App::Annotation',name);o.LabelText=[txt];o.Position=placement('palm_base').multVec(V(*pos));o.ViewObject.FontSize=16;o.ViewObject.TextColor=(.07,.20,.30);groups['Reference'].addObject(o);refs.append(o)
annotation('Length190','190 mm | wrist to middle tip',(0,-88,94))
annotation('Width84','84 mm palm',(0,18,116))
annotation('JointCount','20 hand axes | 4 per digit',(0,38,-12))
show_links(lambda link,name:False)
camera(True);image('01_dimensions.png')
for o in refs:o.ViewObject.Visibility=False
show_links(lambda link,name:link=='palm_base')
camera(True,18);image('02_palm.png')
show_links(lambda link,name:link.startswith('index'))
camera(False,20);image('03_finger.png')
show_links(lambda link,name:link=='palm_base' or link.startswith('thumb'))
camera(True,18);image('04_thumb.png')
show_links(lambda link,name:link=='palm_base' or any(link.startswith(d) for d in ['index','middle','ring','pinky','thumb']))
camera(True,8);image('05_assembly.png')
camera(False,-12);image('06_dorsal.png')
show_links(lambda link,name:True)
Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll();image('07_full_arm.png')

# Save with the hand shown prominently for design review; arm remains in tree.
show_links(lambda link,name:link=='palm_base' or any(link.startswith(d) for d in ['index','middle','ring','pinky','thumb']))
camera(True,8)
doc.recompute();doc.saveAs(str(DESIGN/'AnthroArm25_Humanoid.FCStd'))
Part.export(components,str(DESIGN/'AnthroArm25_Humanoid.step'))
payload={'schema_version':2,'mesh_units':'m','cad_units':'mm','spec':'robot_spec.json','components':manifest,'count':len(manifest),'valid':all(x['valid'] for x in manifest),'geometry':'smooth solid oval-section lofts and ellipsoids; all exported in canonical local body coordinates','hand_scale_mm':190,'limitations':'Digital concept; geometry validity does not establish hardware tolerances, structural capacity, compliance or manufacturability.'}
(DESIGN/'anatomical_manifest.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
(ROOT/'docs'/'humanoid_components.txt').write_text('ANTHRO 25 HUMANOID COMPONENT GUIDE\n\n'+'\n\n'.join(f"{x['label']}\nLink: {x['link']}\n{x['explanation']}" for x in manifest),encoding='utf-8')
progress('ANATOMICAL_BUILD_COMPLETE '+str(len(manifest))+' valid single-solid components.')
