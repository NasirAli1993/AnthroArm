from pathlib import Path
p=Path(r'D:\RoboticArm\dashboard\index.html')
s=p.read_text(encoding='utf-8')
needle='<div class="note">The orange object is a free physics body.'
insert='<div class="section"><h3>Virtual sensor readings</h3><div id="sensors" class="sub">Waiting for physics…</div><p class="sub">Local palm-frame IMU and wrist reaction sensors. Values come from the rigid-body model.</p></div>'
if 'id="sensors"' not in s: s=s.replace(needle,insert+needle)
needle="$('group').onchange=makeSliders;"
insert="""setInterval(()=>{if(!state.sensors)return;const norm=v=>Math.hypot(...(v||[0,0,0])).toFixed(2);$('sensors').textContent='Acceleration: '+norm(state.sensors.palm_accelerometer)+' m/s² · Angular speed: '+norm(state.sensors.palm_gyro)+' rad/s · Wrist force: '+norm(state.sensors.wrist_force)+' N · Wrist torque: '+norm(state.sensors.wrist_torque)+' N·m';},250);\n"""
if 'Acceleration: ' not in s:s=s.replace(needle,insert+needle)
p.write_text(s,encoding='utf-8')
