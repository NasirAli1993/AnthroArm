from pathlib import Path
p = Path(__file__).resolve().parents[1]/'dashboard'/'index.html'
s=p.read_text(encoding='utf-8')
s=s.replace('step="0.005" value="${j.target}"','step="0.001745329252" value="${j.target}"')
s=s.replace('<span>${deg(j.max)}°</span></div></div>`', '<span>${deg(j.max)}°</span></div><label class="sub" for="n_${esc(j.name)}">Target ° <input id="n_${esc(j.name)}" data-numeric="${esc(j.name)}" aria-label="${esc(j.label||j.name)} target degrees" type="number" min="${j.min*180/Math.PI}" max="${j.max*180/Math.PI}" step="0.1" value="${deg(j.target)}" style="width:78px;padding:4px;margin-top:7px"></label></div>`')
s=s.replace("Number(e.value)}}))}","Number(e.value)}}));document.querySelectorAll('[data-numeric]').forEach(e=>e.onchange=()=>{const value=Number(e.value);if(Number.isFinite(value))command({action:'targets',targets:{[e.dataset.numeric]:value*Math.PI/180}})})}")
s=s.replace("if(s&&document.activeElement!==s)s.value=j.target", "if(s&&document.activeElement!==s)s.value=j.target;let n=$('n_'+j.name);if(n&&document.activeElement!==n)n.value=deg(j.target)")
p.write_text(s,encoding='utf-8')
