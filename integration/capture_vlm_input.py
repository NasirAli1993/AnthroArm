"""Save unannotated virtual-camera pixels and an image-derived target crop."""
from pathlib import Path
import sys,os,json
ROOT=Path(__file__).resolve().parents[1]
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
sys.path[:0]=[str(ROOT/'simulation/v3'),str(ROOT/'integration/grasping')]
from model import ArmSimulation
from controller import configure_episode
from vision import KnownSizeRGBDCamera
from PIL import Image
out=ROOT/'results/integration/vision_language';out.mkdir(parents=True,exist_ok=True)
sim=ArmSimulation();configure_episode(sim,size=.036,mass=.06,x=.4,y=0.)
camera=KnownSizeRGBDCamera(sim,.036,width=1280,height=960)
try:
    detection=camera.capture()
    # RGB renderer output precedes OpenCV annotation. No ground-truth object pose.
    raw=camera.renderer.render().copy()
    Image.fromarray(raw).save(out/'raw_camera.png')
    (out/'raw_camera_detection.json').write_text(json.dumps(detection,indent=2))
    print(json.dumps(detection))
finally:camera.close();sim.close()
