"""Build a standalone, offline evidence presentation. Originals remain intact."""
from pathlib import Path
import shutil,json,html,hashlib,zipfile,re
from html.parser import HTMLParser
ROOT=Path(r'D:\RoboticArm');RES=ROOT/'results/integration';OUT=RES/'presentation'
ZIP=ROOT/'share/Simulation_Demo_2026-10-07.zip'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def copy(source,target):
    destination=OUT/target;destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,destination)

files={
 'media/mobile.webm':RES/'mobile_manipulation/mobile_camera_grasp.webm',
 'media/mobile_poster.png':RES/'mobile_manipulation/mobile_hold.png',
 'media/grasp.webm':RES/'grasping/learned_contact_grasp.webm',
 'media/grasp_poster.png':RES/'grasping/learned_grasp_hold.png',
 'media/navigation.webm':RES/'navigation/navigation_demo.webm',
 'media/navigation_poster.png':RES/'navigation/navigation_poster.png',
 'media/navigation_map.png':RES/'navigation/navigation_map.png',
 'media/vlm_scene.png':RES/'vision_language/scene_input.png',
 'media/vlm_target.png':RES/'vision_language/target_input.png',
 'evidence/grasp_training_and_heldout.json':RES/'grasping/report.json',
 'evidence/grasp_final_validation.json':RES/'grasping/final_validation.json',
 'evidence/grasp_camera_validation.json':RES/'grasping/camera_report.json',
 'evidence/grasp_video.json':RES/'grasping/video.json',
 'evidence/grasp_training_trials_summary.json':RES/'grasping/training_progress.json',
 'evidence/grasp_policy.json':ROOT/'integration/grasping/policy.json',
 'evidence/mobile_validation.json':RES/'mobile_manipulation/validation.json',
 'evidence/mobile_video_trial.json':RES/'mobile_manipulation/video_trial.json',
 'evidence/mobile_video.json':RES/'mobile_manipulation/video.json',
 'evidence/mobile_development_notes.json':RES/'mobile_manipulation/development_notes.json',
 'evidence/navigation_validation.json':RES/'navigation/navigation_validation.json',
 'evidence/navigation_ros_validation.json':RES/'navigation/ros_pipeline_validation.json',
 'evidence/navigation_media_validation.json':RES/'navigation/media_validation.json',
 'evidence/arm_ros_validation.json':RES/'runtime/arm_bridge_validation.json',
 'evidence/ros_runtime_probe.json':RES/'runtime/runtime_probe.json',
 'evidence/final_review.json':RES/'runtime/final_review.json',
 'evidence/vlm_report.json':RES/'vision_language/report.json',
 'evidence/vlm_annotated_input_experiment.json':RES/'vision_language/annotated_input_experiment.json',
 'evidence/isaac_feasibility.txt':ROOT/'integration/runtime/isaac_feasibility.txt',
}
for target,source in files.items():copy(source,target)
grasp=read(RES/'grasping/report.json');camera=read(RES/'grasping/camera_report.json')
mobile=read(RES/'mobile_manipulation/validation.json');nav=read(RES/'navigation/navigation_validation.json')
ros=read(RES/'runtime/arm_bridge_validation.json');navros=read(RES/'navigation/ros_pipeline_validation.json')
vlm=read(RES/'vision_language/report.json');review=read(RES/'runtime/final_review.json')
minimum_lift=min(r['minimum_hold_lift_m'] for r in mobile['results'])*1000
max_drift=max(r['max_base_drift_during_manipulation_m'] for r in mobile['results'])*1000
max_slip=max(r['hold_slip_m'] for r in grasp['heldout_results'])*1000
nav_goals=nav['checks']['heldout_goals']['episodes']
arm_ros_count=sum(c['passed'] for c in ros['checks']);nav_ros_count=sum(c['passed'] for c in navros['checks'].values())
scene_answer=html.escape(vlm['results'][0]['answer']);target_answer=html.escape(vlm['results'][1]['answer'])
def evidence(label,name):return f'<a href="evidence/{name}">{html.escape(label)} <span aria-hidden="true">↗</span></a>'
links=''.join('<li>'+evidence(name.replace('_',' ').replace('.json',''),name)+'</li>' for name in [
 'mobile_validation.json','mobile_video_trial.json','mobile_video.json','mobile_development_notes.json',
 'grasp_training_and_heldout.json','grasp_final_validation.json','grasp_camera_validation.json','grasp_training_trials_summary.json','grasp_policy.json','grasp_video.json',
 'navigation_validation.json','navigation_ros_validation.json','navigation_media_validation.json','arm_ros_validation.json','ros_runtime_probe.json','final_review.json','vlm_report.json','vlm_annotated_input_experiment.json','isaac_feasibility.txt'])
document='''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AnthroArm | Simulation results</title>
<style>
:root{color-scheme:dark;--bg:#101a22;--panel:#182832;--line:#344b58;--text:#eef5f7;--muted:#b8cbd5;--mint:#8ce4c7;--gold:#ffc785}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font:17px/1.65 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:var(--mint);text-underline-offset:4px}a:hover{color:#fff}header{border-bottom:1px solid var(--line);background:#13212b}nav{max-width:1200px;margin:auto;display:flex;align-items:center;justify-content:space-between;padding:18px 28px;gap:20px;flex-wrap:wrap}.brand{font-weight:750;letter-spacing:.12em;font-size:15px;color:var(--text)}nav div{display:flex;gap:20px;flex-wrap:wrap}nav a{text-decoration:none;font-size:14px}main{max-width:1200px;margin:auto;padding:0 28px 64px}.hero{padding:66px 0 40px;max-width:1030px}.eyebrow{color:var(--mint);text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:700}h1{font-size:clamp(34px,5vw,56px);line-height:1.14;letter-spacing:-.035em;margin:16px 0 22px;font-weight:720}h2{font-size:29px;line-height:1.2;letter-spacing:-.02em;margin:0 0 14px}h3{font-size:20px;line-height:1.35;margin:0 0 12px}.intro{font-size:21px;max-width:930px;color:var(--muted);margin:0}.badge{display:inline-block;border:1px solid #3a625b;border-radius:30px;padding:4px 12px;margin:22px 8px 0 0;font-size:13px;color:var(--mint)}.metrics{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin:0 0 56px}.metric{padding:22px;background:var(--panel);border-right:1px solid var(--line)}.metric:last-child{border:0}.metric strong{display:block;font-size:31px;font-weight:730;line-height:1.2;color:var(--mint)}.metric span{display:block;color:var(--muted);font-size:14px;margin-top:8px}section{scroll-margin-top:24px;margin:0 0 58px}.sectionhead{display:flex;justify-content:space-between;gap:25px;align-items:start;margin-bottom:22px}.sectionhead p{max-width:765px;color:var(--muted);margin:0}.number{font:700 15px/1.4 ui-monospace,monospace;color:var(--mint);white-space:nowrap;border:1px solid var(--line);border-radius:8px;padding:9px 13px}.video{border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#0a1015}video{width:100%;height:auto;display:block;background:#0a1015}.caption{padding:12px 17px;background:var(--panel);color:var(--muted);font-size:13px;display:flex;gap:20px;justify-content:space-between;flex-wrap:wrap}.facts{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:18px 0}.card{padding:21px 22px;background:var(--panel);border:1px solid var(--line);border-radius:10px}.card p{margin:0;color:var(--muted);font-size:15px}.card strong{color:var(--text)}.factvalue{font-size:27px;line-height:1.25;font-weight:700;display:block;margin-bottom:8px}.note{border-left:3px solid var(--gold);padding:15px 20px;background:#202b30;border-radius:0 8px 8px 0;font-size:15px;color:var(--muted);margin:20px 0}.note strong{color:var(--gold)}.links{display:flex;gap:20px;flex-wrap:wrap;font-size:14px;margin-top:17px}.two{display:grid;grid-template-columns:1fr 1fr;gap:22px}.panel{padding:25px;background:var(--panel);border:1px solid var(--line);border-radius:12px}.panel p{color:var(--muted);font-size:15px}.panel p:last-child{margin-bottom:0}ol,ul{padding-left:22px}li{margin:7px 0;color:var(--muted)}.steps{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;padding:0;list-style:none;margin:20px 0}.steps li{border:1px solid var(--line);border-radius:8px;padding:12px 10px;color:var(--mint);text-align:center;font-size:13px}.scope{width:100%;border-collapse:collapse;font-size:15px;margin-top:20px}.scope th,.scope td{border-bottom:1px solid var(--line);padding:17px 13px;text-align:left;vertical-align:top}.scope th{color:var(--mint);font-weight:650}.scope td{color:var(--muted)}.scope td:first-child{color:var(--text);font-weight:600;min-width:155px}.scope th:first-child{width:20%}.scope th:nth-child(2){width:42%}blockquote{margin:16px 0;padding:15px 18px;background:#101e28;border-left:3px solid var(--gold);color:var(--text);font-size:16px}.vlm-image{width:100%;height:auto;border:1px solid var(--line);border-radius:8px;display:block}.tiny-target{image-rendering:auto;max-width:180px;max-height:150px;margin:16px auto;display:block}.small{font-size:13px;color:var(--muted)}details{border:1px solid var(--line);border-radius:10px;margin:17px 0;background:var(--panel)}summary{padding:17px 20px;cursor:pointer;color:var(--mint);font-weight:600}details>div{padding:0 20px 20px}.evidence{columns:2;column-gap:40px;list-style:none;padding:0;font-size:14px}.evidence li{break-inside:avoid;padding:4px 0}footer{border-top:1px solid var(--line);padding-top:22px;color:var(--muted);font-size:13px}code{font-family:ui-monospace,Consolas,monospace;font-size:.9em;color:var(--mint)}
@media(max-width:760px){main{padding:0 18px 40px}nav{padding:16px 18px}.hero{padding-top:38px}.intro{font-size:18px}.metrics{grid-template-columns:1fr 1fr;margin-bottom:38px}.metric:nth-child(2){border-right:0}.metric:nth-child(-n+2){border-bottom:1px solid var(--line)}.facts,.two{grid-template-columns:1fr}.steps{grid-template-columns:1fr 1fr}.sectionhead{display:block}.number{display:inline-block;margin-bottom:14px}.scope{font-size:13px}.scope th,.scope td{padding:13px 7px}.scope td:first-child{min-width:80px}.evidence{columns:1}.sectionhead h2{font-size:25px}}
@media print{nav,.video,.links{display:none}body{background:white;color:black}.panel,.card,.metric{background:white;color:black}.scope td,p,li{color:#333!important}section{break-inside:avoid}}
</style></head><body>
<header><nav aria-label="Presentation sections"><a class="brand" href="#top">ANTHROARM / 27</a><div><a href="#mobile">Complete mission</a><a href="#grasp">Grasp</a><a href="#navigation">Navigation</a><a href="#evidence">Evidence</a></div></nav></header>
<main id="top"><div class="hero"><div class="eyebrow">Measured simulation results · 7 October 2026</div><h1>A humanoid arm that reaches,<br>grasps, lifts, and releases.</h1><p class="intro">Watch the articulated CAD hand working through actual simulated contact, then see the same arm operate from a wheeled base. These recordings show the executed software results and the limits of the tested system.</p><span class="badge">Simulation only</span><span class="badge">Offline presentation</span><span class="badge">Three recorded demonstrations</span></div>
<div class="metrics" aria-label="Validation overview"><div class="metric"><strong>@@MOBILE@@/3</strong><span>combined docking + pickup trials</span></div><div class="metric"><strong>@@GRASP@@/10</strong><span>held-out learned grasp trials</span></div><div class="metric"><strong>@@CAMERA@@/6</strong><span>RGB-D-guided grasp trials</span></div><div class="metric"><strong>3/3</strong><span>held-out navigation goals</span></div></div>

<section id="mobile"><div class="sectionhead"><span class="number">01 / COMPLETE MISSION</span><div><h2>Drive to the table. Park. Pick up the cube.</h2><p>One continuous MuJoCo simulation carries the humanoid arm on a free wheeled base. A camera locates the cube after docking; the learned grasp then lifts, holds, sets down, and releases it.</p></div></div>
<div class="video"><video controls preload="none" poster="media/mobile_poster.png" aria-label="Complete mobile manipulation physics recording"><source src="media/mobile.webm" type="video/webm">Open <a href="media/mobile.webm">the mobile mission video</a>.</video><div class="caption"><span>28.9 seconds · full mission at recorded simulation timing</span><span>289 / 289 frames decoded during verification</span></div></div>
<ol class="steps"><li>Wheel drive + lidar map</li><li>Motor-braked parking</li><li>RGB-D cube estimate</li><li>Learned contact grasp</li><li>Lift, hold, release</li></ol>
<div class="facts"><div class="card"><span class="factvalue">@@MOBILELIFT@@ mm</span><p>Minimum retained cube lift across the three combined trials.</p></div><div class="card"><span class="factvalue">@@DRIFT@@ mm</span><p>Largest measured parked-base drift during manipulation.</p></div><div class="card"><span class="factvalue">29 bounded motors</span><p>27 arm/hand actuators and two physical wheel motors.</p></div></div>
<div class="note"><strong>Test scope:</strong> an unobstructed straight docking lane, a deliberately heavy 80 kg chassis, a fixed calibrated external camera, and a known upright 36 mm cube. Docking uses lidar-map estimates. Arm IK uses ideal simulated base pose and joint proprioception. This is a recorded combined experiment; the live standalone navigation benchmark is a separate test.</div>
<div class="links">@@MOBILELINKS@@</div></section>

<section id="grasp"><div class="sectionhead"><span class="number">02 / CONTACT + LEARNING</span><div><h2>Moving fingers produce a real contact grasp.</h2><p>The exact anatomical CAD surfaces are visible while MuJoCo integrates the arm, fingers, and free object. The recorded 37 mm cube is located from RGB and depth pixels before the approach.</p></div></div>
<div class="video"><video controls preload="none" poster="media/grasp_poster.png" aria-label="Learned grasp actual physics recording"><source src="media/grasp.webm" type="video/webm">Open <a href="media/grasp.webm">the contact grasp video</a>.</video><div class="caption"><span>18.6 seconds · approach through release</span><span>372 / 372 frames decoded during verification</span></div></div>
<div class="facts"><div class="card"><span class="factvalue">@@MINLIFT@@ mm</span><p>Minimum held-out lift; all ten trials also released onto the table.</p></div><div class="card"><span class="factvalue">@@SLIP@@ mm</span><p>Largest translational slip relative to the palm during the hold.</p></div><div class="card"><span class="factvalue">@@CAMERROR@@ mm</span><p>Largest initial RGB-D centre error across six camera trials.</p></div></div>
<div class="two"><div class="panel"><h3>Why this is contact physics</h3><p>The object remains a free rigid body. Finger contacts and friction retain it as the arm lifts. There is no object weld, mid-pickup teleport, or applied body-force assistance. Joint targets drive rate-limited, effort-bounded actuators; contacts, height, slip, and release are logged.</p><p>Rigid convex collision hulls approximate the CAD parts. Contact compliance allows small penetration and joint-limit overshoot; the reports measure these effects. This is not a deformation model of human skin.</p></div><div class="panel"><h3>What was actually learned</h3><p>An affine regression was fitted to <strong>six successful optimized demonstrations</strong> chosen from <strong>42 contact trials</strong>. Thirty-six candidates succeeded; six failed. Cube size predicts ten grasp parameters, including palm offset and finger closure.</p><p>Approach/lift/release stages and numerical IK are scripted. This is a narrow supervised policy for upright 32–42 mm cubes, not reinforcement learning, a general grasp network, or an end-to-end vision-language-action policy.</p></div></div>
<div class="links">@@GRASPLINKS@@</div></section>

<section id="navigation"><div class="sectionhead"><span class="number">03 / SENSORS + NAVIGATION</span><div><h2>Map the room, then navigate to new goals.</h2><p>The separate differential-drive base uses noisy wheel odometry and actual simulated range rays. Incremental scan matching builds an occupancy map; an inflated-grid A* planner and feedback controller drive the wheels.</p></div></div>
<div class="video"><video controls preload="none" poster="media/navigation_poster.png" aria-label="Navigation and mapping recording"><source src="media/navigation.webm" type="video/webm">Open <a href="media/navigation.webm">the navigation video</a>.</video><div class="caption"><span>24.3-second recording of the longer mission</span><span>243 frames · first, middle, and last verified in source report</span></div></div>
<div class="facts"><div class="card"><span class="factvalue">@@NAVRMSE@@ mm</span><p>Measured position RMSE over the mapping and navigation mission.</p></div><div class="card"><span class="factvalue">0 obstacle contacts</span><p>Four mapping goals and three held-out navigation goals completed.</p></div><div class="card"><span class="factvalue">@@NAVGOAL@@ mm</span><p>Largest true final error among the held-out goals; stopping tolerance is coarse.</p></div></div>
<div class="note"><strong>Implementation:</strong> custom scan-to-map ICP, wheel odometry, log-odds mapping, and A*. ROS Nav2, global pose-graph optimization, and general loop closure were not executed. This standalone base is lighter than the combined mobile-arm chassis.</div>
<div class="links">@@NAVLINKS@@<a href="media/navigation_map.png">Measured map ↗</a></div></section>

<section id="interfaces"><h2>ROS 2 messages reached the running simulation.</h2><p class="intro">The interfaces were exercised through actual rclpy / DDS processes, not only inspected as source code.</p><div class="two" style="margin-top:22px"><div class="panel"><h3>Arm interface · @@ARMROS@@ checks passed</h3><p>The tests received 27 joint states, RGB JPEG, metric depth, camera calibration, simulation clock, and TF. A trajectory action moved a simulated joint, reported feedback, and handled cancellation. A ROS service triggered the complete learned grasp with measured lift and continuous opposing contacts.</p><div class="links">@@ARMROSLINK@@</div></div><div class="panel"><h3>Navigation interface · @@NAVROS@@ groups passed</h3><p>LaserScan, odometry, map, and status messages were received. Velocity commands drove the simulated wheels; the watchdog stopped them. Mission and pose-goal commands reached the physics process, and the navigation TF tree was checked.</p><div class="links">@@NAVROSLINK@@</div></div></div><p class="small">The installed Windows ROS runtime is a pinned RoboStack community distribution. Full MoveIt and Nav2 stacks were not installed. A later focused review covered 17 backend/ROS fixture checks and parsed five launch scripts; it is separate from the earlier native end-to-end tests.</p></section>

<section id="vlm"><h2>A real vision-language run—with its mistakes preserved.</h2><p class="intro">SmolVLM-256M-Instruct ran locally on CPU using the simulated camera image. Its text output had no authority to command motors.</p><div class="two" style="margin-top:22px"><div class="panel"><h3>Full scene</h3><img class="vlm-image" src="media/vlm_scene.png" alt="Actual simulated camera image of the humanoid arm and orange cube"><blockquote>@@SCENEANSWER@@</blockquote><p><strong>Review:</strong> the image shows an articulated arm over a table with an orange cube. The model missed the arm and made unsupported marker/paper claims.</p></div><div class="panel"><h3>Segmented target crop</h3><img class="tiny-target" src="media/vlm_target.png" alt="Actual orange cube crop supplied to the vision-language model"><blockquote>@@TARGETANSWER@@</blockquote><p><strong>Review:</strong> cube shape was identified correctly, but the requested color was omitted. This one crop does not establish reliable scene understanding.</p><p>A separate annotated-input experiment also produced inaccurate descriptions. Both raw result files are included.</p><div class="links">@@VLMLINKS@@</div><p class="small">Model revision: <code>7e3e67edbbed1bf9888184d9df282b700a323964</code>. The manipulation controller uses deterministic RGB-D segmentation and the fitted grasp policy, not VLM-generated motor actions.</p></div></div></section>

<section id="scope"><h2>What these results establish</h2><table class="scope"><thead><tr><th>Area</th><th>Executed and evidenced</th><th>Boundary</th></tr></thead><tbody><tr><td>Humanoid arm</td><td>Seven arm axes, twenty hand axes, smooth CAD geometry, articulated physics and camera-guided contact pickup.</td><td>Simulated rigid mechanisms; no physical assembly or hardware calibration.</td></tr><tr><td>Learning</td><td>A fitted size-conditioned regression, training failures retained, held-out tests recorded.</td><td>Known upright cubes and fixed motion stages; no general VLA or reinforcement policy.</td></tr><tr><td>Mobile mission</td><td>Wheel dynamics, lidar-map docking, motor braking, then mounted-arm pickup in one continuous model.</td><td>Heavy base, clear docking lane, ideal base pose for IK; no manipulation while driving.</td></tr><tr><td>Isaac Sim / Lab</td><td>Feasibility reviewed against official requirements.</td><td>Not installed or executed: GTX 1660 Ti, 6 GB VRAM, about 15.9 GB RAM, and no RT cores are outside the supported requirements.</td></tr><tr><td>Jetson / hardware</td><td>The requested software-only results run on the available computer.</td><td>No physical Jetson or robot is required for this simulation; hardware deployment was not tested.</td></tr></tbody></table><div class="links">@@SCOPELINKS@@</div></section>

<section id="evidence"><h2>Inspect the evidence offline.</h2><p class="intro">Every linked file below is included in this folder. The presentation requires no local server, API, internet connection, software installation, or model weights.</p><details open><summary>Measured reports and original model answers</summary><div><ul class="evidence">@@EVIDENCELINKS@@</ul></div></details><p class="small">This package is a portable presentation and selected evidence set. The editable CAD, simulation code, ROS runtime, and training environment remain in the main project on D:. The videos are recordings; their playback controls do not operate a live robot or simulator.</p><div class="links"><a href="package_validation.json">Package checks and hashes ↗</a><a href="README.txt">How to open this package ↗</a></div></section>
<footer>Prepared 7 October 2026 · AnthroArm simulation project · Open this index.html after extracting the ZIP. Original project files were preserved.</footer></main></body></html>'''
replacements={
 '@@MOBILE@@':str(mobile['successes']),'@@GRASP@@':str(grasp['heldout_successes']),'@@CAMERA@@':str(camera['successes']),
 '@@MOBILELIFT@@':f'{minimum_lift:.1f}','@@DRIFT@@':f'{max_drift:.3f}','@@SLIP@@':f'{max_slip:.2f}',
 '@@MINLIFT@@':f"{min(r['minimum_hold_lift_m'] for r in grasp['heldout_results'])*1000:.1f}",
 '@@CAMERROR@@':f"{camera['max_camera_estimate_error_m']*1000:.2f}",
 '@@NAVRMSE@@':f"{nav['checks']['localization']['position_rmse_m']*1000:.1f}",
 '@@NAVGOAL@@':f"{max(r['goal_error_true_m'] for r in nav_goals)*1000:.1f}",
 '@@ARMROS@@':str(arm_ros_count),'@@NAVROS@@':str(nav_ros_count),
 '@@SCENEANSWER@@':scene_answer,'@@TARGETANSWER@@':target_answer,
 '@@MOBILELINKS@@':evidence('Three-case validation','mobile_validation.json')+evidence('Recorded mission data','mobile_video_trial.json'),
 '@@GRASPLINKS@@':evidence('Training and held-out results','grasp_training_and_heldout.json')+evidence('Camera trials','grasp_camera_validation.json')+evidence('Fitted policy coefficients','grasp_policy.json'),
 '@@NAVLINKS@@':evidence('Navigation validation','navigation_validation.json'),
 '@@ARMROSLINK@@':evidence('Native arm ROS evidence','arm_ros_validation.json'),
 '@@NAVROSLINK@@':evidence('Native navigation ROS evidence','navigation_ros_validation.json'),
 '@@VLMLINKS@@':evidence('Raw camera model answers','vlm_report.json')+evidence('Annotated-input experiment','vlm_annotated_input_experiment.json'),
 '@@SCOPELINKS@@':evidence('Isaac feasibility and official sources','isaac_feasibility.txt')+evidence('Focused final review','final_review.json'),
 '@@EVIDENCELINKS@@':links,
}
for key,value in replacements.items():document=document.replace(key,value)
assert not re.search(r'@@[A-Z]+@@',document),'Unfilled template value'
(OUT/'index.html').write_text(document,encoding='utf-8')
(OUT/'README.txt').write_text('ANTHROARM SIMULATION PRESENTATION — 7 OCTOBER 2026\n\nExtract the complete ZIP, then double-click index.html. Keep media and evidence beside it.\nThe static page opens directly from a file in a WebM-capable browser. No server, internet,\ninstallation, model weights, physical robot, or Jetson is needed to view this package.\n\nThree videos show recorded MuJoCo physics. Their player controls do not run a live simulator.\nSelected JSON reports, original VLM answers, and feasibility notes are included.\nThe full editable project and installed runtimes remain separately on D:\\RoboticArm.\n\nRead the scope notes in index.html before interpreting success counts.\nThe standalone navigation benchmark and combined clear-lane docking test are different experiments.\n',encoding='utf-8')

class References(HTMLParser):
    def __init__(self):super().__init__();self.refs=[]
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ('href','src','poster') and value and not value.startswith('#'):self.refs.append(value)
parser=References();parser.feed(document)
missing=[r for r in parser.refs if r!='package_validation.json' and not (OUT/r).is_file()]
assert not missing,missing
assert not re.search(r'\bfetch\s*\(|https?://|<script[^>]+src=',document),'External dependency in HTML'
import cv2
video_checks=[]
for video in ('mobile','grasp','navigation'):
    capture=cv2.VideoCapture(str(OUT/'media'/f'{video}.webm'));fps=capture.get(cv2.CAP_PROP_FPS);declared=int(capture.get(cv2.CAP_PROP_FRAME_COUNT));decoded=0;shape=None
    while True:
        ok,frame=capture.read()
        if not ok:break
        decoded+=1;shape=list(frame.shape[:2])
    capture.release();assert decoded==declared and decoded>0
    video_checks.append(dict(file=f'media/{video}.webm',frames=declared,decoded_frames=decoded,fps=fps,duration_s=decoded/fps,height_width=shape))
hashes={relative:hashlib.sha256((OUT/relative).read_bytes()).hexdigest() for relative in files}
validation=dict(passed=True,relative_references_checked=len(parser.refs),missing_references=missing,external_dependencies=0,static_html_no_fetch=True,
 video_count=3,total_decoded_frames=sum(v['decoded_frames'] for v in video_checks),videos=video_checks,
 selected_evidence_files=sum(k.startswith('evidence/') for k in files),media_files=sum(k.startswith('media/') for k in files),
 metrics=dict(grasp_heldout=f"{grasp['heldout_successes']}/{grasp['heldout_trials']}",camera_grasp=f"{camera['successes']}/{camera['trials']}",mobile=f"{mobile['successes']}/{mobile['trials']}",arm_ros_checks=arm_ros_count,navigation_ros_groups=nav_ros_count),sha256=hashes)
(OUT/'package_validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
archive_files=[OUT/'index.html',OUT/'README.txt',OUT/'package_validation.json']+[OUT/name for name in files]
with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
    for path in archive_files:archive.write(path,str(path.relative_to(OUT)).replace('\\','/'))
with zipfile.ZipFile(ZIP) as archive:
    assert archive.testzip() is None
    assert len(archive.namelist())==len(archive_files)
summary=dict(index=str(OUT/'index.html'),zip=str(ZIP),zip_bytes=ZIP.stat().st_size,zip_files=len(archive_files),relative_references=len(parser.refs),videos=video_checks,total_decoded_frames=validation['total_decoded_frames'],metrics=validation['metrics'],zip_crc_passed=True)
(OUT/'build_result.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
