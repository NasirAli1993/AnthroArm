"""Known-size RGB-D cube adapter; image/depth input only, no object-pose read."""
from pathlib import Path
import importlib.util
import cv2

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('grasp_rgbd_baseline',ROOT/'simulation/v3/vision_reach.py')
baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)

class KnownSizeRGBDCamera(baseline.RGDBCamera):
    def __init__(self,sim,object_size_m=.036,width=640,height=480):
        if not .032<=object_size_m<=.042:
            raise ValueError('Supported upright cube edge length: 32..42 mm')
        super().__init__(sim,width,height)
        self.object_size_m=float(object_size_m)

    def capture(self):
        result=super().capture()
        if result['detected']:
            # Baseline uses the same calibrated camera and backprojected top
            # surface but subtracts its known 25 mm half-height. Replace only
            # that prior with this experiment's declared edge length.
            result['center_world_m'][2]=result['top_surface_z_m']-self.object_size_m/2
            result['assumptions']=f'Known upright {self.object_size_m*1000:g} mm orange cube; visible top surface; calibrated RGB-D camera.'
            result['known_object_size_m']=self.object_size_m
            result['ground_truth_object_pose_used']=False
            cv2.rectangle(self.latest_rgb,(0,0),(self.width,37),(15,24,30),-1)
            label='RGB-D centre (m): %.3f %.3f %.3f'%tuple(result['center_world_m'])
            cv2.putText(self.latest_rgb,label,(12,25),cv2.FONT_HERSHEY_SIMPLEX,.52,(220,255,240),1,cv2.LINE_AA)
        self.last_detection=result
        return result
