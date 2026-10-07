from pathlib import Path
p=Path(r'D:\RoboticArm\dashboard\index.html')
s=p.read_text(encoding='utf-8')
s=s.replace('Tracking loss holds the last command','Tracking loss holds the current pose').replace('Last command held.','Current pose held.')
s=s.replace("'Closest solution. '","'Unreachable target; no motion. '")
s=s.replace("else $('actualError').textContent='';","else {$('actualError').textContent='';if(!state.ik||state.ik.error_m===undefined)$('feedback').textContent='';}")
s=s.replace('oblique?.25:0','oblique ? .25 : 0').replace('oblique?.15:0','oblique ? .15 : 0').replace('oblique?.39:.40','oblique ? .39 : .40')
s=s.replace('dragging=true;lastX=',"dragging=true;camera={...camera,...(state.camera||{})};lastX=")
s=s.replace('Math.min(15,camera.elevation','Math.min(85,camera.elevation')
needle='<div id="feedback" role="status"></div>'
if 'id="actualError"' not in s:s=s.replace(needle,needle+'<div id="actualError" class="sub"></div>')
needle="$('group').onchange=makeSliders;"
insert="setInterval(()=>{if(state.ik?.actual_position_error_m!==undefined)$('actualError').textContent='Measured position error: '+(state.ik.actual_position_error_m*1000).toFixed(1)+' mm (under load).';else $('actualError').textContent='';},250);\n"
if 'Measured position error: ' not in s:s=s.replace(needle,insert+needle)
p.write_text(s,encoding='utf-8')
