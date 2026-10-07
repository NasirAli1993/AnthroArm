AnthroArm27: full native static geometry import V4

STAGED SOURCE: this V4 has not been executed natively. This package performs
28 multibody STEP imports, expects 293 solids and zero sheets, saves each
SLDPRT, validates native MathPoint transforms and creates a fixed 28-component
SLDASM. It does not implement joint mates, Motion Analysis or FEA.

The existing V3 native run imported and saved 28 parts according to the operator
report, then stopped at the Transform2 setter. V4 corrects the setter to plain
comp.Transform2 = transform, matching the official SOLIDWORKS VBA example:
https://help.solidworks.com/2021/english/api/sldworksapi/Align_Assembly_Component_to_Assembly_Origin_and_Planes_Example_VB.htm
The explicit-False Boolean checks from V3 remain in place.

Use AutoFullArmRecoverV1 instead if the 28 native parts remain in the observed
20261006_091441_33281078 provider folder; do not repeat imports unnecessarily.

For a fresh session upload all 28 STEP files and V4 macro source FLAT in one
folder. Import the BAS into a native SOLIDWORKS VBA macro project, enable the
SOLIDWORKS type and constants references, save its SWP beside the STEP files,
and run main. A unique output folder and progressive log preserve old files.
The BAS/SWB source files are not a precompiled binary SWP.

Review native log and output files before claiming a successful assembly.
All components are deliberately fixed. This is a static geometry checkpoint.
