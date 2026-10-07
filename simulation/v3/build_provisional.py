"""Development-only kinematic/sensor fixture while final V3 CAD is built.
Never used as final visual evidence; saves provisional.xml, not robot.xml.
"""
from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v3generate',Path(__file__).with_name('generate_model.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
robot=g.make_spec();old=json.loads((ROOT/'design'/'anatomical_manifest.json').read_text())
for link in robot['links']:
    link['geoms']=[]
    oldname='wrist_link' if link['name']=='wrist_pitch' else link['name']
    for c in old['components']:
        if c['link']==oldname and oldname!='base_link':link['geoms'].append(dict(name=c['name'],mesh_file='../'+c['file'],rgba=list(c['rgba'][:3])+[1],collision=bool(c.get('collision_candidate'))))
original=g.save;g.save=lambda element,path:original(element,ROOT/'simulation'/'v3'/'provisional.xml')
g.write_mjcf(robot)
print('Provisional development fixture only - final V3 CAD pending')
