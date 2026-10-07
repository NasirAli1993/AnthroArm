"""Read-only native / STEP / STL round-trip checks; run with FreeCADCmd."""
from pathlib import Path
import json
import traceback
import FreeCAD as App
import Part
import Mesh

ROOT = Path(r"D:\RoboticArm")
try:
    doc = App.openDocument(str(ROOT / "design" / "AnthroArm25.FCStd"))
    parts = [o for o in doc.Objects if "Shape" in o.PropertiesList and not o.Shape.isNull()]
    native = {
        "reopened": True,
        "component_count": len(parts),
        "valid_components": sum(bool(o.Shape.isValid()) for o in parts),
        "single_solid_components": sum(len(o.Shape.Solids) == 1 for o in parts),
        "positive_volume_components": sum(o.Shape.Volume > 0 for o in parts),
        "explanations_persisted": sum(bool(getattr(o, "Explanation", "").strip()) for o in parts),
        "joint_metadata_persisted": sum("JointName" in o.PropertiesList for o in parts),
    }
    step = Part.read(str(ROOT / "design" / "AnthroArm25.step"))
    step_report = {
        "reimported": True,
        "assembly_valid": bool(step.isValid()),
        "solid_count": len(step.Solids),
        "valid_solids": sum(bool(s.isValid()) for s in step.Solids),
        "positive_volume_solids": sum(s.Volume > 0 for s in step.Solids),
        "total_volume_mm3": step.Volume,
    }
    meshes = []
    for path in sorted((ROOT / "design" / "parts").glob("*.stl")):
        m = Mesh.Mesh(str(path))
        meshes.append({"file": path.name, "bytes": path.stat().st_size,
                       "facets": m.CountFacets, "points": m.CountPoints})
    expected = json.loads((ROOT / "design" / "cad_manifest.json").read_text())["count"]
    passed = (
        native["component_count"] == expected
        and all(native[k] == expected for k in ["valid_components", "single_solid_components", "positive_volume_components", "explanations_persisted", "joint_metadata_persisted"])
        and step_report["assembly_valid"]
        and all(step_report[k] == expected for k in ["solid_count", "valid_solids", "positive_volume_solids"])
        and len(meshes) == expected and all(m["bytes"] > 0 and m["facets"] > 0 and m["points"] > 0 for m in meshes)
    )
    report = {
        "passed": passed,
        "scope": "Geometry topology, positive volumes, file round trips and embedded descriptions only. This does not validate assembly interference, actuation, tolerances, strength, manufacturability or physical safety.",
        "expected_components": expected,
        "native_freecad": native,
        "step": step_report,
        "stl_count": len(meshes),
        "stls": meshes,
    }
    (ROOT / "results" / "cad_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    App.closeDocument(doc.Name)
    print("CAD_VALIDATION", "PASS" if passed else "FAIL", "components:", expected)
except Exception:
    (ROOT / "results" / "cad_validation_error.txt").write_text(traceback.format_exc(), encoding="utf-8")
    raise
