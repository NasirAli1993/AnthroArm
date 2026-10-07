"""Generate an OpenSCAD assembly using the exact anatomical CAD meshes."""
from pathlib import Path
import json, math
ROOT=Path(__file__).resolve().parents[1]
design=ROOT/'design'
spec=json.loads((design/'robot_spec.json').read_text(encoding='utf-8-sig'))
manifest=json.loads((design/'anatomical_manifest.json').read_text(encoding='utf-8-sig'))
assert manifest['valid'] and manifest['mesh_units']=='m'
links=spec['links']; indices={v['name']:i for i,v in enumerate(links)}
rows=[]; poses={n:[] for n in ('open','zero','fist','point','peace')}
for l in links:
    j=l.get('joint') or {}; name=j.get('name','fixed')
    rows.append([l['name'],indices.get(l.get('parent'),-1),[x*1000 for x in l.get('origin_xyz',[0,0,0])],[math.degrees(x) for x in l.get('origin_rpy',[0,0,0])],j.get('axis',[0,0,1]),name])
    for pose,values in poses.items():
        q=j.get('home',0) if j.get('group')=='Arm' else 0
        if pose=='zero':q=0
        close={'fist':['index','middle','ring','pinky'],'point':['middle','ring','pinky'],'peace':['ring','pinky']}.get(pose,[])
        for f in close:
            q={f+'_mcp_flexion':1.15,f+'_pip':1.35,f+'_dip':.9}.get(name,q)
        if pose in ('fist','point','peace'):
            q={'thumb_cmc_opposition':1.,'thumb_cmc_flexion':.8,'thumb_mcp_flexion':.85,'thumb_ip':.65}.get(name,q)
        if pose=='peace':q={'index_mcp_abduction':-.13,'middle_mcp_abduction':.1}.get(name,q)
        values.append(math.degrees(q))
components=[[indices[c['link']],c['file'].replace('\\','/'),c['rgba'],c['name'],c['explanation']] for c in manifest['components']]
text='''/* Humanoid revision 2. Actual FreeCAD-exported surfaces in native joint frames.
Units in this OpenSCAD assembly: mm. Source STL units: m, scaled 1000 below.
FreeCAD source: build_anatomical_cad.py. This file inspects CAD poses only;
run Robotics Studio for dynamics, contacts and measured motor tracking.
*/
/* [View] */
pose = "open"; // [open,zero,fist,point,peace]
view_hand_only = true;
// Set canonical link name, e.g. index_distal, to inspect one rigid link.
export_link = "";
'''
text+='links = '+json.dumps(rows)+';\ncomponents = '+json.dumps(components)+';\n'
for name,values in poses.items():text+='pose_'+name+' = '+json.dumps(values)+';\n'
text+='''
angles=pose=="zero"?pose_zero:pose=="fist"?pose_fist:pose=="point"?pose_point:pose=="peace"?pose_peace:pose_open;
module surfaces(i) {
  for(c=components) if(c[0]==i) color(c[2]) scale([1000,1000,1000]) import(c[1],convexity=10);
}
module body(i) {
  surfaces(i);
  for(k=[0:len(links)-1]) if(links[k][1]==i) node(k);
}
module node(i) {
  l=links[i];translate(l[2]) rotate(l[3]) rotate(a=angles[i],v=l[4]) body(i);
}
if(export_link!="") { for(i=[0:len(links)-1]) if(links[i][0]==export_link) surfaces(i); }
else if(view_hand_only) { for(i=[0:len(links)-1]) if(links[i][0]=="palm_base") body(i); }
else node(0);
'''
(design/'humanoid_hand.scad').write_text(text,encoding='utf-8')
print('OpenSCAD anatomical assembly:',len(components),'components;',len(links),'links')
