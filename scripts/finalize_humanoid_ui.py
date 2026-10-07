from pathlib import Path
p=Path(__file__).resolve().parents[1]/'dashboard'/'index.html'
s=p.read_text(encoding='utf-8')
s=s.replace("forEach(e=>e.onchange=()=>{const value=Number(e.value)","forEach(e=>e.oninput=()=>{const value=Number(e.value)")
s=s.replace('grid-template-columns:minmax(550px,1fr) 355px','grid-template-columns:minmax(420px,1fr) 340px')
s=s.replace('@media(max-width:1000px)','@media(max-width:820px)')
s=s.replace('min-height:430px','min-height:330px')
s=s.replace('MuJoCo · gravity + joint dynamics + contact','MuJoCo · gravity + bounded motor control + contact')
s=s.replace('Errors compare measured joint angles with requested targets. Motion and contacts can increase these values.', 'Measured versus requested targets in an ideal model. Motion and contacts increase error; hardware precision remains unverified.')
p.write_text(s,encoding='utf-8')
