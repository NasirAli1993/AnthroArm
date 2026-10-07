AutoFullArmStaticV2: staged source, not compiled/executed yet.
V1 compiled and reached import preference setup in native SOLIDWORKS;
it stopped because SolidandSurface toggle readback was False despite
previous visible UI checkbox. Exact cause/version applicability unknown.
V2 logs this preference readback mismatch as a warning; does not call
this setting verified. ALL actual Part type, exact solid count, zero-sheet,
source-mm scale and transform/save checks remain mandatory and unchanged.
Upload SWB (or import BAS) beside all 28 STEP files, save running SWP beside
those inputs, add SOLIDWORKS core + constants references and compile.
Run main. Save all generated native parts, assembly and log together on D:.
All components are fixed static geometry; no mates, Motion, FEA performed.
