from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).parent))
from mission import mission,OUT
results=[]
for i,(x,y,start) in enumerate([(.4,0,-.6),(.395,-.015,-.55),(.405,.015,-.65)]):
    result=mission(object_xy=(x,y),start_x=start,report_name=f'trial_{i}.json')
    if i==0:(OUT/'report.json').write_text(json.dumps(result,indent=2))
    results.append({k:v for k,v in result.items() if k not in ('route','samples')})
report=dict(trials=len(results),successes=sum(r['success'] for r in results),all_passed=all(r['success'] for r in results),results=results)
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(trials=len(results),successes=report['successes'])),flush=True)
