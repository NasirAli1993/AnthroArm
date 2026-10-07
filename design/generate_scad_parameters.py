"""Canonical robot hierarchy -> OpenSCAD include (degrees and mm)."""
from pathlib import Path
import json
import math

root = Path(r"D:\RoboticArm")
data = json.loads((root / "design" / "robot_spec.json").read_text())
links = data["links"]
indices = {link["name"]: i for i, link in enumerate(links)}
rows = []
for link in links:
    n = link["name"]
    j = link.get("joint") or {}
    children = [c for c in links if c.get("parent") == n]
    lengths = [1000*c["origin_xyz"][2] for c in children if c["origin_xyz"][2] > .001]
    length = max(lengths) if lengths else next((v for k, v in [("index",18),("middle",20),("ring",18),("pinky",17),("thumb",15)] if k in n), 0)
    role = ("base" if n == "base_link" else "waist" if n == "waist_link" else
            "arm" if n in ("upper_arm", "forearm") else "wrist" if n == "wrist_link" else
            "palm" if n == "palm_base" else "yoke" if "knuckle" in n or "opposition" in n else "finger")
    width = 15.5 if "middle" in n else 13 if "pinky" in n else 17 if "thumb" in n else 14.5
    row = [n, indices.get(link.get("parent"), -1), [1000*v for v in link.get("origin_xyz",[0,0,0])],
           [math.degrees(v) for v in link.get("origin_rpy", [0,0,0])], j.get("axis", [0,0,1]),
           math.degrees(j.get("home",0)), j.get("name", "fixed"), role, length, width,
           "distal" in n, link.get("description", "")]
    rows.append(row)
text = "// Generated from robot_spec.json. Edit canonical JSON then regenerate.\n// Row: name,parent,xyz(mm),rpy(deg),axis,home(deg),joint,role,length,width,distal,description.\n"
text += "robot_links = " + json.dumps(rows, indent=2) + ";\n"
(root / "design" / "robot_parameters.scad").write_text(text, encoding="utf-8")
print("Generated", len(rows), "CAD link frames")
