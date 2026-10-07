"""CLI: one reproducible RGB-D learned grasp experiment, simulation only."""
from pathlib import Path
import sys,json,argparse
sys.path.insert(0,str(Path(__file__).parent))
from evaluate import trial,runtime,OUT
from vision import KnownSizeRGBDCamera

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--size-mm',type=float,default=36)
    p.add_argument('--mass-g',type=float,default=60)
    p.add_argument('--x',type=float,default=.4);p.add_argument('--y',type=float,default=0.)
    args=p.parse_args();sim=runtime.ArmSimulation();detection={}
    def estimate(sim,size):
        sensor=KnownSizeRGBDCamera(sim,size)
        try:
            detection.update(sensor.capture())
            if not detection['detected']:raise RuntimeError('Camera failed to detect upright orange cube')
            return detection['center_world_m']
        finally:sensor.close()
    try:
        result=trial(sim,size=args.size_mm/1000,mass=args.mass_g/1000,xy=(args.x,args.y),estimate_provider=estimate)
        result['camera']=detection
        (OUT/'latest_cli_trial.json').write_text(json.dumps(result,indent=2))
        print(json.dumps({k:v for k,v in result.items() if k not in ('samples','stages')},indent=2))
    finally:sim.close()
    return 0 if result['success'] else 2

if __name__=='__main__':sys.exit(main())
