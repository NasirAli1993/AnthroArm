from pathlib import Path
import json,traceback
import FreeCAD as App
import Part
V=App.Vector
def ellipse(z,rx,ry,cx=0,cy=0):
 e=Part.Ellipse(V(),max(rx,ry),min(rx,ry)).toShape()
 if ry>rx:e.rotate(V(),V(0,0,1),90)
 e.translate(V(cx,cy,z));return Part.Wire([e])
def loft(sections):return Part.makeLoft([ellipse(*s) for s in sections],True,False)
def check(name,s):return {'name':name,'valid':s.isValid(),'solids':len(s.Solids),'volume':s.Volume}
try:
 outer=loft([(35,32,37),(60,42,47),(120,43,49),(180,37,43),(240,29,33),(272,25,28)])
 inner=loft([(34,28,33),(60,38,43),(120,39,45),(180,33,39),(240,25,29),(273,21,24)])
 shell=outer.cut(inner)
 front=shell.common(Part.makeBox(100,200,400,V(1,-100,0)))
 back=shell.common(Part.makeBox(100,200,400,V(-101,-100,0)))
 finger=loft([(.8,6.2,8.4),(5,7,8.8),(18,6.8,8.4),(30,6.5,8),(39.2,6.1,7.9)])
 pocket=Part.makeBox(9,11,25,V(3.7,-5.5,7))
 pocket=pocket.makeFillet(1.8,pocket.Edges)
 pad=finger.common(pocket)
 finger=finger.cut(pocket)
 (Path(r'D:\RoboticArm\results')/'v3_geometry_probe.json').write_text(json.dumps([check('outer',outer),check('shell',shell),check('front',front),check('back',back),check('finger',finger),check('pad',pad)],indent=2))
except Exception:
 (Path(r'D:\RoboticArm\results')/'v3_geometry_probe_error.txt').write_text(traceback.format_exc())
 raise
