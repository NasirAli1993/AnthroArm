"""Independent RGB-D-pixel-to-contact-pickup validation."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).parent))
import cv2,numpy as np
from evaluate import trial,runtime,OUT
from vision import KnownSizeRGBDCamera

def main():
    sim=runtime.ArmSimulation();results=[]
    cases=[(.036,.4,0),(.033,.385,-.017),(.035,.405,.016),(.037,.395,-.021),(.039,.41,.021),(.041,.395,.013)]
    for i,(size,x,y) in enumerate(cases):
        detection={}
        def estimate(sim,size):
            camera=KnownSizeRGBDCamera(sim,size)
            try:
                detection.update(camera.capture())
                if not detection['detected']:raise RuntimeError('RGB-D did not detect cube')
                cv2.imwrite(str(OUT/f'camera_detection_{i}.png'),cv2.cvtColor(camera.latest_rgb,cv2.COLOR_RGB2BGR))
                return detection['center_world_m']
            finally:camera.close()
        result=trial(sim,size=size,xy=(x,y),estimate_provider=estimate)
        result['detection']=detection
        result['estimate_error_norm_m']=float(np.linalg.norm(result['measured_initial_estimate_error_m']))
        results.append(result)
        print(json.dumps(dict(case=i,success=result['success'],camera_error_mm=1000*result['estimate_error_norm_m'],error=result['error'])),flush=True)
        (OUT/'camera_trials.json').write_text(json.dumps(results,indent=2))
    report=dict(trials=len(results),successes=sum(r['success'] for r in results),all_passed=all(r['success'] for r in results),ground_truth_used_for_control=False,known_size_assumption=True,
      max_camera_estimate_error_m=max(r['estimate_error_norm_m'] for r in results),
      results=[{k:v for k,v in r.items() if k not in ('samples','stages')} for r in results])
    (OUT/'camera_report.json').write_text(json.dumps(report,indent=2));sim.close()
    print(json.dumps(dict(complete=True,passed=report['all_passed'],successes=report['successes'])),flush=True)

if __name__=='__main__':main()
