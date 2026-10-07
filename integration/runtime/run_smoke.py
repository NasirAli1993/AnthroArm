"""Launch two independent ROS 2 processes and record observed test results."""
from pathlib import Path
import json
import os
import subprocess
import sys
import time
import uuid

ROOT=Path('D:/RoboticArm')
SCRIPT=ROOT/'integration/runtime/smoke_node.py'
OUT=ROOT/'results/integration/runtime'


def main():
    token=uuid.uuid4().hex[:12]
    directory=OUT/('smoke_'+token)
    directory.mkdir(parents=True,exist_ok=True)
    common=['--token',token,'--topic','/anthroarm/runtime_'+token,'--output',str(directory)]
    creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)
    children=[]
    handles=[]
    report={'passed':False,'token':token,'directory':str(directory)}
    try:
        for role in ['server','client']:
            log=(directory/(role+'.log')).open('w',encoding='utf-8')
            handles.append(log)
            process=subprocess.Popen([sys.executable,'-B',str(SCRIPT),role]+common,stdout=log,stderr=subprocess.STDOUT,
                                     cwd=str(ROOT),env=os.environ.copy(),creationflags=creationflags)
            children.append(process)
            if role=='server':
                deadline=time.monotonic()+120
                while not (directory/'server_ready.json').exists() and time.monotonic()<deadline:
                    if process.poll() is not None:
                        raise RuntimeError('ROS server process exited during startup')
                    time.sleep(.1)
                if not (directory/'server_ready.json').exists():
                    raise RuntimeError('ROS server did not reach ready state')
        client_code=children[1].wait(timeout=30)
        server_code=children[0].wait(timeout=10)
        client=json.loads((directory/'client.json').read_text())
        server=json.loads((directory/'server.json').read_text())
        report.update(client=client,server=server,client_exit=client_code,server_exit=server_code,
                      separate_processes=client['pid']!=server['pid'])
        report['passed']=bool(client['passed'] and server['passed'] and client_code==0 and server_code==0 and report['separate_processes'])
    except Exception as exc:
        report['error']=repr(exc)
    finally:
        for process in children:
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=3)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=3)
        for handle in handles:handle.close()
        report['remaining_child_processes']=sum(p.poll() is None for p in children)
        (OUT/'ros2_smoke.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report,indent=2),flush=True)
    return report


if __name__=='__main__':
    raise SystemExit(0 if main()['passed'] else 1)
