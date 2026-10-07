"""Build the articulated concept CAD from the simulation's canonical robot_spec.json.

Run inside portable FreeCAD using scripts/build_cad.ps1. Millimetres in CAD,
metres and radians in robot_spec.json. No hardware dimensions are certified.
"""
from pathlib import Path
import json
import math
import os
import sys

ROOT = Path(r"D:\RoboticArm")
DESIGN = ROOT / "design"
sys.path.insert(0, str(DESIGN))
import FreeCAD as App
import Part
import MeshPart

V = App.Vector
BLUE = (0.11, 0.24, 0.34)
SILVER = (0.76, 0.81, 0.85)
DARK = (0.08, 0.105, 0.13)
ORANGE = (0.98, 0.50, 0.16)
RUBBER = (0.12, 0.15, 0.17)
WHITE = (0.91, 0.94, 0.96)


def rounded_box(x, y, z, pos, radius=2):
    s = Part.makeBox(x, y, z, V(*pos))
    if radius:
        try:
            candidate = s.makeFillet(min(radius, min(x, y, z) / 2 - 0.05), s.Edges)
            if not candidate.isNull() and candidate.isValid():
                return candidate
        except Exception:
            pass
    return s


def cylinder(radius, length, pos=(0, 0, 0), direction=(0, 0, 1)):
    return Part.makeCylinder(radius, length, V(*pos), V(*direction))


def fuse(shapes):
    result = shapes[0]
    for s in shapes[1:]:
        result = result.fuse(s)
    return result.removeSplitter()


def capsule_bar(length, radius, width):
    """A sagittal capsule profile, extruded across the hinge axis Y."""
    return fuse([
        cylinder(radius, width, (0, -width/2, 0), (0, 1, 0)),
        cylinder(radius, width, (0, -width/2, length), (0, 1, 0)),
        Part.makeBox(2*radius, width, length, V(-radius, -width/2, 0)),
    ])


def base_shape(radius=120, height=80):
    s = cylinder(radius, height)
    # Four M8 clearance mounting holes on a 180 mm bolt circle.
    for a in [45, 135, 225, 315]:
        x, y = 90*math.cos(math.radians(a)), 90*math.sin(math.radians(a))
        s = s.cut(cylinder(4.5, height+2, (x, y, -1)))
        s = s.cut(cylinder(8, 8, (x, y, height-7)))
    # Rear cable service port and central bearing pilot.
    s = s.cut(rounded_box(40, 25, 18, (-20, -126, 12), 3))
    s = s.cut(cylinder(14, height+2, (0, 0, -1)))
    trim_seat = cylinder(108.2, 2.2, (0, 0, height-2)).cut(cylinder(97.8, 3, (0, 0, height-2.3)))
    s = s.cut(trim_seat)
    return s


def arm_shell(length, radius, width):
    outer = capsule_bar(length, radius, width)
    inner = capsule_bar(length-2*radius, radius-5, width-8)
    inner.translate(V(0, 0, radius))
    s = outer.cut(inner)
    for z in (0, length):
        s = s.cut(cylinder(8, width+2, (0, -width/2-1, z), (0, 1, 0)))
    # Shallow service recess on the palmar/front (+X) side.
    s = s.cut(rounded_box(12, width-14, length-2*radius-8,
                          (radius-8, -(width-14)/2, radius+4), 3))
    return s


def phalanx(length, width, depth, distal=False):
    r = depth/2
    tongue_width = width*0.43
    body = rounded_box(depth, width, length-r-2, (-r, -width/2, r), 2.8)
    root = cylinder(r, tongue_width, (0, -tongue_width/2, 0), (0, 1, 0))
    bridge = rounded_box(depth-1, tongue_width, r+2,
                         (-r+0.5, -tongue_width/2, 0), 1)
    # Unite the overlapping bridge before the root: body/root alone are tangent.
    s = fuse([body, bridge, root])
    if distal:
        cap = cylinder(r, width, (0, -width/2, length-r), (0, 1, 0))
        s = s.fuse(cap)
    else:
        # Two clevis ears with a 0.45 mm clearance on either side of tongue.
        gap = tongue_width+0.9
        ear = (width-gap)/2
        s = s.fuse(cylinder(r, ear, (0, -width/2, length), (0, 1, 0)))
        s = s.fuse(cylinder(r, ear, (0, gap/2, length), (0, 1, 0)))
        s = s.cut(Part.makeBox(depth+2, gap, r+2, V(-r-1, -gap/2, length-r)))
        s = s.cut(cylinder(1.05, width+2, (0, -width/2-1, length), (0, 1, 0)))
    s = s.cut(cylinder(1.05, width+2, (0, -width/2-1, 0), (0, 1, 0)))
    # Straight tendon guide bores in segment body: routing over joints unresolved.
    for x in (-depth*0.30, depth*0.30):
        s = s.cut(cylinder(0.7, max(2, length-2*r), (x, 0, r)))
    return s.removeSplitter()


def palm_shell():
    outer = rounded_box(29, 84, 100, (-13, -42, 0), 5)
    cavity = rounded_box(30, 76, 91, (-17, -38, 4), 3)
    s = outer.cut(cavity)
    for y in [-33, 33]:
        for z in [12, 87]:
            s = s.fuse(cylinder(4, 26, (-13, y, z), (1, 0, 0)))
            s = s.cut(cylinder(1.6, 32, (-16, y, z), (1, 0, 0)))
    s = s.cut(cylinder(6, 15, (0, 0, -2)))
    # Lateral service connector slot.
    s = s.cut(rounded_box(10, 12, 12, (-5, -45, 20), 2))
    return s.removeSplitter()


def spec_path():
    path = DESIGN / "robot_spec.json"
    if not path.exists():
        raise RuntimeError("robot_spec.json has not been generated yet")
    return path


spec = json.loads(spec_path().read_text(encoding="utf-8"))
links = spec["links"]
if isinstance(links, dict):
    links = [dict(value, name=key) for key, value in links.items()]
by_name = {a["name"]: a for a in links}
doc = App.newDocument("AnthroArm25_Concept")
doc.Label = "ANTHRO / 25 — Arm + dexterous hand"
part_dir = DESIGN / "parts"
part_dir.mkdir(exist_ok=True)
assembly_objects = []
manifest = []
placements = {}


def rpy_rotation(rpy):
    r, p, y = [math.degrees(v) for v in rpy]
    return App.Rotation(V(0, 0, 1), y).multiply(App.Rotation(V(0, 1, 0), p)).multiply(App.Rotation(V(1, 0, 0), r))


def link_placement(link):
    name = link["name"]
    if name in placements:
        return placements[name]
    parent = link.get("parent")
    parent_place = link_placement(by_name[parent]) if parent and parent in by_name else App.Placement()
    p = [1000*v for v in link.get("origin_xyz", [0, 0, 0])]
    rotation = rpy_rotation(link.get("origin_rpy", [0, 0, 0]))
    joint = link.get("joint") or {}
    axis = joint.get("axis", [0, 0, 1])
    q = joint.get("home", 0)
    rotation = rotation.multiply(App.Rotation(V(*axis), math.degrees(q)))
    result = parent_place.multiply(App.Placement(V(*p), rotation))
    placements[name] = result
    return result


groups = {}
for group_name, label in [("FixedBase", "01 · Table fixture"), ("Arm", "02 · Five-axis arm"),
                          ("WristPalm", "03 · Wrist and palm"), ("Fingers", "04 · Articulated fingers"),
                          ("Reference", "05 · Reference and design notes")]:
    group = doc.addObject("App::DocumentObjectGroup", group_name)
    group.Label = label
    groups[group_name] = group


def component(name, label, shape, link_name, explanation, color=SILVER,
              group="Arm", material="Concept polymer / metal; not selected", export=True):
    if shape.isNull() or not shape.isValid() or shape.Volume <= 0:
        raise ValueError("Invalid or empty CAD component: " + name)
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    obj.Placement = link_placement(by_name[link_name])
    obj.addProperty("App::PropertyString", "Explanation", "Component").Explanation = explanation
    obj.addProperty("App::PropertyString", "RobotLink", "Component").RobotLink = link_name
    j = by_name[link_name].get("joint") or {}
    obj.addProperty("App::PropertyString", "JointName", "Kinematics").JointName = j.get("name", "fixed")
    obj.addProperty("App::PropertyVector", "JointAxis", "Kinematics").JointAxis = V(*j.get("axis", [0, 0, 0]))
    obj.addProperty("App::PropertyAngle", "HomeAngle", "Kinematics").HomeAngle = math.degrees(j.get("home", 0))
    obj.addProperty("App::PropertyString", "AngleLimits", "Kinematics").AngleLimits = str(j.get("range", [])) + " rad"
    obj.addProperty("App::PropertyString", "MaterialIntent", "Component").MaterialIntent = material
    obj.addProperty("App::PropertyString", "DesignStatus", "Component").DesignStatus = "Engineering concept: validate fit, load, actuation and fabrication before building."
    obj.addProperty("App::PropertyString", "ParametricSource", "Component").ParametricSource = str(DESIGN / "build_freecad.py")
    obj.addProperty("App::PropertyString", "CoordinateFrame", "Component").CoordinateFrame = "Millimetres; local +Z outward; finger +Y flexion; palmar side +X."
    if obj.ViewObject:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.LineColor = (0.10, 0.12, 0.15)
        obj.ViewObject.DisplayMode = "Flat Lines"
    groups[group].addObject(obj)
    assembly_objects.append(obj)
    entry = {"name": name, "label": label, "link": link_name, "explanation": explanation,
             "solid_count": len(shape.Solids), "valid": bool(shape.isValid()),
             "volume_mm3": shape.Volume}
    if export:
        # Export in its own local frame, suitable for inspection of individual parts.
        filename = part_dir / (name + ".stl")
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.12, AngularDeflection=0.20, Relative=False)
        mesh.write(str(filename))
        entry["stl"] = str(filename)
    manifest.append(entry)
    return obj


def role(name):
    n = name.lower()
    if n in ("world",):
        return "world"
    if "tabletop" in n or n in ("base", "base_link"):
        return "base"
    if n in ("arm_link_1", "waist", "waist_link"):
        return "waist"
    if "upper_arm" in n or n == "arm_link_2":
        return "upper"
    if "forearm" in n or n == "arm_link_3":
        return "forearm"
    if "wrist" in n or n == "arm_link_4":
        return "wrist"
    if "palm" in n:
        return "palm"
    if any(f in n for f in ("index", "middle", "ring", "pinky", "thumb")):
        if "abduction" in n or "opposition" in n or "abduct" in n or "knuckle" in n:
            return "yoke"
        return "phalanx"
    return "other"


def infer_length(link):
    children = [x for x in links if x.get("parent") == link["name"]]
    lengths = [x.get("origin_xyz", [0, 0, 0])[2]*1000 for x in children]
    positive = [a for a in lengths if a > 1]
    if positive:
        return max(positive)
    name = link["name"]
    lengths = {"index": 18, "middle": 20, "ring": 18, "pinky": 17, "thumb": 15}
    for f, length in lengths.items():
        if f in name:
            return length
    return 30


for link in links:
    name = link["name"]
    kind = role(name)
    if kind in ("world", "other"):
        continue
    if kind == "base":
        height = 80
        waist_children = [x for x in links if x.get("parent") == name]
        if waist_children:
            height = waist_children[0].get("origin_xyz", [0, 0, .08])[2]*1000
        component("BaseFixture", "Base · M8 table mounting plate", base_shape(height=height), name,
                  "Anchors the arm to a rigid bench. Four 9 mm clearance holes on 180 mm PCD; rear service port; central cable passage. Anchoring, mass and bolt selection require structural validation.", DARK, "FixedBase")
        ring = cylinder(108, 3, (0, 0, height-1.95)).cut(cylinder(98, 5, (0, 0, height-2.95)))
        component("BaseAccent", "Base · removable trim ring", ring, name,
                  "Visual trim and cover seam around the waist stage. Does not carry the arm load.", ORANGE, "FixedBase")
    elif kind == "waist":
        s = cylinder(46, 52).cut(cylinder(15, 54, (0, 0, -1)))
        component("WaistHousing", "J1 · waist actuator enclosure", s, name,
                  "Rotating waist enclosure and central cable route. Its local Z axis follows the first arm joint; bearing and actuator interfaces remain conceptual.", BLUE)
        for sign in [-1, 1]:
            s = rounded_box(50, 9, 35, (-25, sign*31-4.5, 27), 4)
            s = s.cut(cylinder(8, 12, (0, sign*31-6, 60), (0, 1, 0)))
            component("ShoulderYoke" + ("L" if sign < 0 else "R"), "J2 · shoulder yoke " + ("L" if sign < 0 else "R"), s, name,
                      "Support cheek for shoulder pivot. Bore is a placeholder for a bearing-supported output shaft; bearing seat tolerance must be designed.", SILVER)
    elif kind in ("upper", "forearm"):
        length = infer_length(link)
        radius, width = (29, 48) if kind == "upper" else (24, 40)
        title = "Upper arm" if kind == "upper" else "Forearm"
        component(kind + "Shell", title + " · hollow structural shell", arm_shell(length, radius, width), name,
                  f"{length:.0f} mm pivot spacing. Hollow concept housing with 16 mm pivot passages and a front service recess. Wall sizing and torque load paths require analysis.", WHITE)
        strip = rounded_box(3, width-17, length-2*radius-16,
                            (radius-5, -(width-17)/2, radius+8), 1)
        component(kind + "Cover", title + " · service cover", strip, name,
                  "Removable front cover identifies cable and actuator service area. Fasteners, cable strain relief and a complete tendon spool package are not yet detailed.", BLUE)
        for end, z in [("Root", 0), ("Tip", length)]:
            cap = cylinder(radius-6, 4, (0, -width/2-4, z), (0, 1, 0)).cut(cylinder(5, 6, (0, -width/2-5, z), (0, 1, 0)))
            component(kind + end + "BearingCover", title + " · " + end.lower() + " bearing cover", cap, name,
                      "External bearing cover and joint-axis marker. The orange bore ring is a visual reference, not a selected commercial bearing.", BLUE)
            badge = cylinder(9, 1.5, (0, -width/2-5.5, z), (0, 1, 0)).cut(cylinder(5, 3, (0, -width/2-6, z), (0, 1, 0)))
            component(kind + end + "HubRing", title + " · " + end.lower() + " hub ring", badge, name,
                      "High-contrast marker makes the simulated hinge axis visible when inspecting the mechanism.", ORANGE)
    elif kind == "wrist":
        s = cylinder(29, 60).cut(cylinder(13, 62, (0, 0, -1)))
        s = s.cut(cylinder(6, 64, (0, -32, 0), (0, 1, 0)))
        component("WristPitchHousing", "J4 · wrist pitch housing", s, name,
                  "60 mm wrist stage. Pitch follows the local Y axis; a through-bore reserves cable space for the hand.", BLUE, "WristPalm")
        ring = cylinder(32, 6, (0, 0, 53)).cut(cylinder(29.2, 8, (0, 0, 52)))
        component("WristRollCollar", "J5 · wrist roll collar", ring, name,
                  "Visual collar at the hand roll interface. Rotation is around the palm Z axis; a slip ring and cable turn limit must be resolved for physical construction.", ORANGE, "WristPalm")
    elif kind == "palm":
        component("PalmShell", "Palm · 100 × 84 × 32 mm shell", palm_shell(), name,
                  "Adult-scale palm with dorsal access, screw bosses and wrist cable inlet. The 100 mm palm plus 90 mm middle finger establishes the 190 mm hand scale.", WHITE, "WristPalm")
        lid = rounded_box(3, 78, 94, (-16, -39, 3), 1.4)
        for y in [-33, 33]:
            for z in [12, 87]:
                lid = lid.cut(cylinder(1.8, 5, (-17, y, z), (1, 0, 0)))
        component("PalmDorsalLid", "Palm · removable dorsal cover", lid, name,
                  "Dorsal service lid. Four M3 clearance holes align with internal bosses; threaded inserts and screw lengths need selection.", BLUE, "WristPalm")
        pad = rounded_box(2, 53, 64, (16, -26.5, 19), .8)
        component("PalmContactPad", "Palm · compliant contact pad concept", pad, name,
                  "Reserved palmar contact surface. Simulation uses idealized friction; elastomer durometer, attachment and tactile sensing are unvalidated.", RUBBER, "WristPalm")
    elif kind == "yoke":
        if "thumb" in name:
            s = cylinder(6.8, 10, (0, 0, -5)).cut(cylinder(1.6, 12, (0, 0, -6)))
        else:
            s = cylinder(6.8, 10, (-5, 0, 0), (1, 0, 0)).cut(cylinder(1.6, 12, (-6, 0, 0), (1, 0, 0)))
        component(name + "Yoke", name.replace("_", " ") + " · lateral joint", s, name,
                  "Base axis enables finger spread or thumb opposition. The crossing-axis articulation is kinematically modeled; a complete miniature bearing and transmission package remains to be engineered.", BLUE, "Fingers")
    elif kind == "phalanx":
        length = infer_length(link)
        distal = "distal" in name
        width = 14.5 if "thumb" not in name else 17
        if "middle" in name:
            width = 15.5
        if "pinky" in name:
            width = 13
        depth = 13 if not distal else 11.5
        s = phalanx(length, width, depth, distal)
        component(name + "Body", name.replace("_", " ") + f" · {length:.0f} mm", s, name,
                  f"{length:.0f} mm joint spacing / tip length; 2.1 mm hinge bores, 1.4 mm tendon guide bores, root tongue and distal clevis where applicable. Cable routing around moving joints and fatigue behavior are not verified.", WHITE, "Fingers")
        pin = cylinder(.98, width+1.4, (0, -width/2-.7, 0), (0, 1, 0))
        component(name + "Pin", name.replace("_", " ") + " · hinge pin", pin, name,
                  "Nominal 1.96 mm pin reference for the 2.1 mm CAD bore. Actual pin tolerance, retention and bearing wear need physical testing.", ORANGE, "Fingers", "Steel pin reference")
        if distal:
            pad = rounded_box(2, width-2, max(5, length-8), (depth/2-0.3, -(width-2)/2, 5), .8)
            component(name + "Pad", name.replace("_", " ") + " · fingertip pad", pad, name,
                      "Palmar fingertip contact insert. Placeholder for soft material and optional tactile sensing; no physical sensor has been selected.", RUBBER, "Fingers")

# Save a plain-language note in the actual native CAD document.
note = doc.addObject("App::FeaturePython", "ReadMe")
note.Label = "READ ME · 25 DOF / concept validation required"
note.addProperty("App::PropertyStringList", "DesignNotes", "Project")
note.DesignNotes = [
    "Five arm axes plus 20 independently controlled hand axes (four per digit).",
    "Canonical frames, home pose and link dimensions: robot_spec.json.",
    "Select any solid in the tree and read its Component > Explanation property.",
    "Native solid assembly is editable; change parametric source and rerun to regenerate.",
    "Detailed CAD is for design review. Simulation uses simpler collision geometry.",
    "No motor, reducer, bearing, tendon network or fabrication tolerance is validated.",
    "Do not manufacture or energize hardware solely from these concept files.",
]
groups["Reference"].addObject(note)
doc.recompute()
doc.saveAs(str(DESIGN / "AnthroArm25.FCStd"))
Part.export(assembly_objects, str(DESIGN / "AnthroArm25.step"))
manifest_path = DESIGN / "cad_manifest.json"
manifest_path.write_text(json.dumps({"spec": str(spec_path()), "components": manifest,
                                     "count": len(manifest), "valid": all(x["valid"] for x in manifest)}, indent=2), encoding="utf-8")
(ROOT / "docs" / "components.txt").write_text(
    "ANTHRO / 25 — COMPONENT GUIDE\n\nEvery description is also embedded in the FreeCAD Component > Explanation property.\n\n" +
    "\n\n".join(f"{x['label']}\n  Robot link: {x['link']}\n  {x['explanation']}" for x in manifest) +
    "\n\nDESIGN STATUS\nThis is a concept CAD assembly for on-screen simulation and engineering study.\nThe CAD and physics share frames and lengths; mass and collision primitives remain approximations.\nPhysical tendon actuation, component selection, structural loads, tolerances and safety need a separate validated hardware engineering phase.\n",
    encoding="utf-8")
try:
    import FreeCADGui as Gui
    Gui.activeDocument().activeView().viewAxonometric()
    Gui.activeDocument().activeView().fitAll()
    Gui.activeDocument().activeView().saveImage(str(ROOT / "results" / "cad_assembly.png"), 1600, 1200, "White")
    doc.save()
except Exception as exc:
    print("CAD screenshot unavailable:", exc)
print("CAD_BUILD_COMPLETE", len(manifest), "components; valid =", all(x["valid"] for x in manifest))
