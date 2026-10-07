"""Validate the frozen policy and current contact-loss/lifecycle controller."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).parent))
import numpy as np
from evaluate import trial,runtime,OUT
from controller import LearnedGraspController,configure_episode

def main():
    report=json.loads((OUT/'report.json').read_text())
    sim=runtime.ArmSimulation();results=[]
    if '--lifecycle-only' in sys.argv:
        results=json.loads((OUT/'final_validation_trajectories.json').read_text())
    else:
        for case in report['heldout_results']:
            result=trial(sim,size=case['size_m'],mass=case['mass_kg'],xy=case['xy'])
            result['case_id']=case['case_id'];results.append(result)
            print(case['case_id'],result['success'],flush=True)
    configure_episode(sim)
    control=LearnedGraspController(sim)
    control.start([.4,0,.618],.036);control.step(40);control.cancel()
    hold_target=sim.targets.copy();control.step(100)
    cancel_ok=not control.active and control.phase=='idle' and np.array_equal(sim.targets,hold_target)
    configure_episode(sim,x=.57,y=.20)
    # A deliberately empty target must not be credited as a grasp.
    control.start([.4,0,.618],.036)
    for _ in range(6000):
        if not control.active:break
        control.step()
    empty_rejected=not control.active and control.phase=='failed' and 'contacts' in control.error
    final=dict(trials=len(results),successes=sum(r['success'] for r in results),all_passed=all(r['success'] for r in results),
      cancellation_holds_without_stale_commands=bool(cancel_ok),empty_target_refused_lift=bool(empty_rejected),
      empty_target_status=control.state,results=[{k:v for k,v in r.items() if k not in ('samples','stages')} for r in results])
    (OUT/'final_validation.json').write_text(json.dumps(final,indent=2))
    (OUT/'final_validation_trajectories.json').write_text(json.dumps(results,indent=2))
    print(json.dumps({k:v for k,v in final.items() if k not in ('results','empty_target_status')}),flush=True)
    sim.close()

if __name__=='__main__':main()
