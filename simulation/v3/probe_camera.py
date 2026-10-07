"""Camera format diagnosis. Records scalar statistics only, never images."""
from pathlib import Path
import cv2,numpy as np,json,time,winreg
ROOT=Path(__file__).resolve().parents[2]
def device_names():
    names=[]
    path=r'CLSID\{860BB310-5D01-11D0-BD3B-00A0C911CE86}\Instance'
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT,path) as key:
            for i in range(winreg.QueryInfoKey(key)[0]):
                with winreg.OpenKey(key,winreg.EnumKey(key,i)) as sub:
                    try:names.append(winreg.QueryValueEx(sub,'FriendlyName')[0])
                    except OSError:pass
    except OSError:pass
    return names
def run():
    report={'registered_directshow_video_sources':device_names(),'images_saved':False,'images_transmitted':False,'hand_tracking_verified':False,'probes':[]}
    for name,backend,fourcc in [('DSHOW default',cv2.CAP_DSHOW,None),('DSHOW MJPG',cv2.CAP_DSHOW,'MJPG'),('DSHOW YUY2',cv2.CAP_DSHOW,'YUY2'),('MSMF default',cv2.CAP_MSMF,None)]:
        row={'configuration':name};cap=cv2.VideoCapture(0,backend)
        try:
            row['opened']=cap.isOpened()
            if not cap.isOpened():report['probes'].append(row);continue
            if fourcc:row['format_set_accepted']=bool(cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*fourcc)))
            row['negotiated_fourcc']=int(cap.get(cv2.CAP_PROP_FOURCC));row['fps']=cap.get(cv2.CAP_PROP_FPS)
            prior=None;changes=[];stats=[]
            for i in range(8):
                ok,frame=cap.read()
                if not ok:break
                gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY).astype(float)
                stats.append({'shape':list(frame.shape),'mean':float(gray.mean()),'std':float(gray.std()),'horizontal_spatial_std':float(gray.std(axis=1).mean()),'vertical_spatial_std':float(gray.std(axis=0).mean()),'gray_pixel_fraction':float(np.mean((frame[:,:,0]==frame[:,:,1])&(frame[:,:,1]==frame[:,:,2])))})
                if prior is not None:changes.append(float(np.abs(gray-prior).mean()))
                prior=gray;time.sleep(.04)
            row.update(frames_received=len(stats),last_frame_statistics=stats[-1] if stats else None,temporal_mean_absolute_changes=changes)
        except Exception as e:row['error']=str(e)
        finally:cap.release()
        report['probes'].append(row)
    (ROOT/'results'/'v3'/'camera_diagnosis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));return report
if __name__=='__main__':run()
