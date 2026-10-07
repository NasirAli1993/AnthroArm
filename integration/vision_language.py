"""Run a local, real vision-language model on saved simulated camera pixels.

The VLM describes objects; it never writes motor targets. No cloud inference.
"""
from pathlib import Path
import os,sys,json,time,argparse
ROOT=Path(__file__).resolve().parents[1]
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
for key,folder in [('HF_HOME','cache/huggingface'),('TORCH_HOME','cache/torch'),('TEMP','temp'),('TMP','temp')]:os.environ[key]=str(ROOT/folder)
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
sys.path.insert(0,str(ROOT/'software'/'vision_language'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--image');args=parser.parse_args()
    import torch
    from PIL import Image
    from transformers import AutoProcessor,AutoModelForVision2Seq
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    out=ROOT/'results'/'integration'/'vision_language';out.mkdir(parents=True,exist_ok=True)
    model_path=ROOT/'models'/'SmolVLM-256M-Instruct'
    start=time.monotonic();print('Loading local pinned model',flush=True)
    processor=AutoProcessor.from_pretrained(str(model_path),local_files_only=True,trust_remote_code=False,size={'longest_edge':512})
    model=AutoModelForVision2Seq.from_pretrained(str(model_path),local_files_only=True,trust_remote_code=False,torch_dtype=torch.float32,attn_implementation='eager').eval()
    load_s=time.monotonic()-start
    if args.image:
        source=Path(args.image);view=Image.open(source).convert('RGB');box=None
    else:
        source=ROOT/'results/integration/vision_language/raw_camera.png'
        view=Image.open(source).convert('RGB')
        detection=json.loads((ROOT/'results/integration/vision_language/raw_camera_detection.json').read_text())
        box=detection['bbox_pixels']
    inputs=[('scene',view,'Describe the objects visible in this image in one sentence.')]
    if box:
        x,y,w,h=box;pad=8
        crop=view.crop((max(0,x-pad),max(0,y-pad),min(view.width,x+w+pad),min(view.height,y+h+pad)))
        inputs.append(('target',crop,'What is the shape and color of the object in this image?'))
    results=[]
    for name,pixels,prompt in inputs:
        pixels.save(out/(name+'_input.png'))
        messages=[{'role':'user','content':[{'type':'image'},{'type':'text','text':prompt}]}]
        text=processor.apply_chat_template(messages,add_generation_prompt=True)
        batch=processor(text=text,images=[pixels],return_tensors='pt')
        begin=time.monotonic()
        with torch.inference_mode():tokens=model.generate(**batch,max_new_tokens=48,do_sample=False)
        answer=processor.batch_decode(tokens[:,batch['input_ids'].shape[1]:],skip_special_tokens=True)[0].strip()
        row={'view':name,'prompt':prompt,'answer':answer,'inference_seconds':time.monotonic()-begin,'input_width':pixels.width,'input_height':pixels.height}
        results.append(row);print(json.dumps(row),flush=True)
    report={'executed':True,'model':'HuggingFaceTB/SmolVLM-256M-Instruct','revision':'7e3e67edbbed1bf9888184d9df282b700a323964',
            'runtime':{'torch':torch.__version__,'device':'cpu','dtype':'float32'},'load_seconds':load_s,'source':str(source),
            'source_type':'user-selected image' if args.image else 'rendered MuJoCo RGB-D camera',
            'roi_source':'no ROI supplied' if args.image else 'image segmentation bbox, no object truth',
            'motor_control_authority':False,'scope':'Captioning experiment; output is model text, not a certified perception or VLA policy.',
            'results':results}
    if not args.image:
        report['qualitative_review']={
            'fixture_content':'Humanoid robotic arm above a table with an orange cube',
            'target_shape_named_correctly':any(r['view']=='target' and 'cube' in r['answer'].lower() for r in results),
            'scene_arm_or_hand_named':any(r['view']=='scene' and any(w in r['answer'].lower() for w in ('arm','hand','robot')) for r in results),
            'limitation':'This small model misidentified the full scene in this run. Correct crop identification does not establish reliable scene understanding. No VLM output drives motors.'}
    (out/'report.json').write_text(json.dumps(report,indent=2));print('VLM inference complete',flush=True)
if __name__=='__main__':main()
