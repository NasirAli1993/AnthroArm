from pathlib import Path
root = Path(__file__).resolve().parents[1]
p = root/'dashboard'/'index.html'
s = p.read_text(encoding='utf-8')
s = s.replace('ROBOTICS STUDIO · 01', 'HUMANOID HAND · 02')
s = s.replace('<span class="pill">25 controlled joints</span>', '<a class="pill" href="/design">Design walkthrough ↗</a>')
s = s.replace('Human-scale hand. Full articulation.', 'Human-shaped. Independently articulated.')
s = s.replace('<div class="metrics">', '<div class="buttons" style="margin-top:12px" id="layers"><button data-layer="surface" class="active">Detailed surface</button><button data-layer="joints">Joint axes</button><button data-layer="collision">Collision geometry</button></div><p class="sub" id="layerNote">Detailed FreeCAD surfaces move with the simulated links.</p><div class="metrics">')
s = s.replace('<a href="/validation" target="_blank">View validation results ↗</a>', '<a href="/design">Design stages ↗</a> · <a href="/precision" target="_blank">Precision results ↗</a>')
s = s.replace('<div class="section"><h3>Individual joint control</h3>', '<div class="section"><h3>Measured tracking precision</h3><div id="precision" class="sub">Waiting for measurement…</div><p class="sub">Errors compare measured joint angles with requested targets. Motion and contacts can increase these values.</p></div><div class="section"><h3>Individual joint control</h3>')
s = s.replace("$('group').onchange=makeSliders;", """$('group').onchange=makeSliders;
$('layers').onclick=e=>{if(e.target.dataset.layer)command({action:'layer',name:e.target.dataset.layer})};
setInterval(()=>{
 const p=state.precision;
 if(p)$('precision').textContent='Arm maximum: '+p.arm_max_error_deg.toFixed(3)+'° · Hand maximum: '+p.hand_max_error_deg.toFixed(3)+'° · Palm position: '+p.palm_target_error_mm.toFixed(3)+' mm';
 document.querySelectorAll('[data-layer]').forEach(b=>b.classList.toggle('active',b.dataset.layer===(state.display_layer||'surface')));
 $('layerNote').textContent=state.display_layer==='collision'?'Convex collision envelopes used by contact physics. Markers show active contacts.':state.display_layer==='joints'?'Joint axes over the actual CAD surfaces. Each finger has independent motor targets.':'Detailed FreeCAD surfaces move with the simulated links.';
},250);
""")
p.write_text(s, encoding='utf-8')
print(p)
