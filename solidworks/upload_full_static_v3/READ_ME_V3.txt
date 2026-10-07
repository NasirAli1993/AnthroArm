AutoFullArmStaticV3 - staged source, not yet compiled or executed.
V2 native save returned True and zero errors, but previous Check used Boolean
Not and rejected it. V3 compares Boolean condition explicitly to False,
separates native save result and error checks, and tests IsFixed explicitly
against False to avoid noncanonical COM TRUE values (+1 versus VBA -1).
Actual Part/count/sheet/scale/transform/save gates remain mandatory.
Save SWP beside 28 STEP siblings. Compile with SOLIDWORKS core and constants.
Do not rerun with same source STEP already open. Close only specifically
identified prior run documents after saving/preserving them; do not close
unrelated user work. New outputs always use unique timestamped folders.
This stage is 28 fixed parts in static native assembly, no mates/Motion/FEA.
