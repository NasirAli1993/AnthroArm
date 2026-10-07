"""Regenerate simulator and URDF from the edited canonical JSON (preserves JSON)."""
from pathlib import Path
import sys, json, runpy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulation'))
from generate_model import write_mjcf, write_urdf
spec=json.loads((ROOT/'design'/'robot_spec.json').read_text(encoding='utf-8'))
write_mjcf(spec)
write_urdf(spec)
runpy.run_path(str(ROOT/'design'/'generate_scad_parameters.py'),run_name='__main__')
print('Regenerated MJCF, URDF and OpenSCAD parameters from design/robot_spec.json. Restart Studio to load changes; rebuild CAD separately.')
