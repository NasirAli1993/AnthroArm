from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'dashboard'/'index.html').read_text(encoding='utf-8')
s=s.replace('Anthro Arm · Robotics Studio','Anthro Arm · Human arm studio')
s=s.replace('HUMANOID HAND · 02','SHOULDER TO FINGERTIPS · 03')
s=s.replace('Human-shaped. Independently articulated.','A complete human-shaped arm.')
s=s.replace('href="/design"','href="http://127.0.0.1:8765/presentation"')
s=s.replace('Design walkthrough ↗','Project presentation ↗').replace('Design stages ↗','Explained project ↗')
s=s.replace('href="/precision"','href="http://127.0.0.1:8765/v3/results"')
s=s.replace('5 + 20','7 + 20').replace('five-axis robotic arm','seven-axis human-shaped arm')
s=s.replace('<button data-layer="collision">Collision geometry</button>','<button data-layer="collision">Collision geometry</button><button data-layer="inside">Internal layout</button>')
s=s.replace('<button id="grasp">Seeded grasp &amp; lift</button>','<button id="visionStart">Camera-guided reach</button><button id="visionStop">Stop camera reach</button>')
s=s.replace('<p class="sub" id="graspStatus">Grasp test starts with a 60 g block placed in the palm, then closes and lifts using contact physics.</p>','<p class="sub" id="visionInfo">Autonomous reach: a simulated RGB-D camera detects the orange cube, then the arm approaches and stops on contact. This does not pick up the cube.</p>')
s=s.replace('<div class="section"><h3>Camera hand control</h3><button id="teleop">Enable local tracking input</button>', '<div class="section"><h3>Your webcam → virtual fingers</h3><button id="teleop">Start webcam hand control</button>')
s=s.replace('Start Webcam Control from the project folder. All five fingers map into the simulation. Tracking loss holds the current pose; camera depth is an estimate.','The local webcam detects your hand and commands the twenty virtual finger joints. Show an open hand, then bend one finger. Images remain in memory on this computer.')
s=s.replace('Position-only inverse kinematics. Five arm axes cannot independently satisfy every position and orientation.','Seven arm axes support pose control. This manual control solves a palm position; the camera task also constrains orientation.')
s=s.replace('The orange object is a free physics body. Gesture motion does not by itself prove grasping or a trained policy. Hardware is not connected.','The orange cube is a free physics object on the table. Camera-guided reaching is a programmed perception-and-control pipeline. Hardware is not connected; no learned policy is used.')
s=s.replace('let state={}, camera={azimuth:150,elevation:-12,distance:1.18}', 'let state={}, camera={azimuth:135,elevation:-10,distance:1.35}')
s=s.replace("function groupOf(j){if(j.name.startsWith('joint_'))return 'Arm';return j.name.split('_')[0].replace(/^./,c=>c.toUpperCase())}","function groupOf(j){return j.group||j.name.split('_')[0].replace(/^./,c=>c.toUpperCase())}")
s=s.replace('The base rotates the whole assembly. The shoulder and elbow position the hand using 300 mm and 250 mm links. Wrist pitch tilts the palm; wrist roll turns it about the forearm axis.','Three shoulder axes orient the upper arm. Elbow flexion bends it. Forearm rotation turns the palm, while wrist flexion and deviation angle the hand. Upper arm: 300 mm; forearm: 250 mm.')
s=s.replace("$('teleop').onclick=()=>command({action:'teleop',value:!state.teleop});","$('teleop').onclick=()=>command({action:'webcam',value:!state.webcam?.enabled});")
s=s.replace("$('grasp').onclick=()=>command({action:'grasp'});","$('visionStart').onclick=()=>command({action:'vision',value:true});$('visionStop').onclick=()=>command({action:'vision',value:false});")
s=re.sub(r"setInterval\(\(\)=>\{if\(state.ready\)\$\('graspStatus'\).*?\},180\);",'',s)
s=s.replace("lookat:[.20,0,.37],distance:1.18,azimuth:150,elevation:-12","lookat:[.25,0,.84],distance:1.35,azimuth:135,elevation:-10")
s=s.replace("state.teleop?(state.tracking_fresh?'Receiving hand landmarks.':'Waiting for tracking. Current pose held.'):'Tracking input disabled.'", "state.webcam?.error?state.webcam.error:state.webcam?.enabled?(state.tracking_fresh?'Your hand is controlling the virtual fingers.':'Camera live: show your hand in view.'):'Webcam is off.'")
s=s.replace("!!state.teleop","!!state.webcam?.enabled")
s=s.replace("state.display_layer==='joints'?'Joint axes", "state.display_layer==='inside'?'Conceptual motors, skeleton and cable layout. Packaging is not a validated transmission design.':state.display_layer==='joints'?'Joint axes")
s=s.replace('<div class="metrics">','''<div class="sensorViews" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px"><section><h3 style="font-size:13px">Robot camera · RGB-D detection</h3><img id="visionImage" alt="Actual virtual camera view with object detection" style="width:100%;border-radius:9px;background:#111a1e"><p class="sub">Pixels and depth → 3D target → joint commands.</p></section><section><h3 style="font-size:13px">Your local webcam · hand imitation</h3><img id="webcamImage" alt="Local webcam hand tracking, available when enabled" style="width:100%;border-radius:9px;background:#111a1e"><p class="sub">Your hand landmarks → twenty finger targets. No recordings.</p></section></div><div class="metrics">''')
s=s.replace('update();frame();','''update();frame();
if(new URLSearchParams(location.search).get('mode')==='vision') {
 const beginVision=setInterval(()=>{if(state.ready){clearInterval(beginVision);command({action:'reset'}).then(()=>command({action:'vision',value:true}));}},250);
}
setInterval(()=>{
 if(state.mode==='vision')$('mode').textContent='CAMERA-GUIDED REACH';
 const v=state.vision||{};
 $('visionInfo').textContent='Camera reach phase: '+(v.phase||'idle')+'. '+(v.result?.reason||'')+(v.result?.success?' Contact confirmed.':'')+' This task reaches/touches the cube; it does not perform autonomous pickup.';
 $('teleop').textContent=state.webcam?.enabled?'Stop webcam':'Start webcam hand control';
 $('visionImage').src='/vision.jpg?t='+Date.now();
 $('webcamImage').src='/webcam.jpg?t='+Date.now();
},300);
''')
s=s.replace('id="webcamImage" alt=', 'id="webcamImage" src="/webcam.jpg" alt=')
s=s.replace("'Webcam is off.'", "'Webcam is off. '+(state.webcam?.source_note||'')")
s=s.replace("' rad/s · Wrist force: '+norm(state.sensors.wrist_force)+' N · Wrist torque: '+norm(state.sensors.wrist_torque)+' N·m'", "' rad/s'")
s=s.replace('Local palm-frame IMU and wrist reaction sensors. Values come from the rigid-body model.', 'Palm-frame accelerometer and gyroscope readings from the rigid-body model.')
(ROOT/'dashboard'/'v3.html').write_text(s,encoding='utf-8')
print('V3 studio page written')
