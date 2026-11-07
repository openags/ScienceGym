"""Publish a clean measurement film only after both independent reviews pass."""
import argparse,hashlib,json,math,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--dense',required=True);p.add_argument('--capture',required=True);p.add_argument('--name',default='ftir_measurement_01');args=p.parse_args()
 dense=Path(args.dense).resolve();folder=Path(args.capture).resolve()
 reports=[json.loads((f/'sampled_interaction_review.json').read_text()) for f in [dense,folder]]
 capture=json.loads((folder/'capture.json').read_text());export=json.loads((folder/'export.json').read_text())
 assert all(r['passed'] and r['covers_entire_episode'] for r in reports)
 assert reports[1]['every_video_frame'] and reports[1]['frames']==capture['frames']
 assert export['parent_export_sha256']==sha(dense/'export.json')
 for f,r in zip([dense,folder],reports):
  for name,value in r['evidence_sha256'].items():assert sha(f/name)==value,name
 for name,value in capture['source_sha256'].items():assert sha(HERE/name)==value,name
 for name,value in capture['asset_sources'].items():assert sha(HERE.parents[1]/name)==value,name
 assert sha(folder/'export.json')==capture['export_sha256']
 video=folder/'measurement.pending.mp4';assert sha(video)==capture['video_sha256']
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
 stream=next(s for s in probe['streams'] if s['codec_type']=='video')
 assert int(stream['nb_frames'])==capture['frames'] and [stream['width'],stream['height']]==capture['resolution']
 assert abs(float(probe['format']['duration'])-capture['video_duration_s'])<.002
 destination=HERE/'media'/(args.name+'.mp4');assert not destination.exists();destination.parent.mkdir(exist_ok=True)
 shutil.copy2(video,destination);assert sha(destination)==capture['video_sha256']
 episode=json.loads((folder/'source/single_measurement_episode.json').read_text());segments={s['id']:s for s in episode['segments']}
 labels=[('initial_open','开舱与工具准备'),('white_delivery_walk_to_cary_forward_walk','走向备料台'),
         ('white_delivery_lift_witness','取出白色样片'),('white_delivery_carry_to_ftir_forward_walk','携样返回 FTIR'),
         ('install_gold_reference','安装金参考片'),('background_select_touch_and_press','背景采集'),
         ('store_gold_reference','保护存放参考片'),('white_mount_seat','安装待测样片'),
         ('sample_select_touch_and_press','样品采集'),('white_retrieve_seat','取样、归还与关舱')]
 delivery=dict(reviewed=True,scope='One complete authored FTIR manipulation procedure across workstations in the existing laboratory.',
   video=str(destination.relative_to(HERE)),video_sha256=sha(destination),scene_duration_s=capture['scene_duration_s'],
   video_duration_s=capture['video_duration_s'],frames=capture['frames'],fps=capture['fps'],resolution=capture['resolution'],
   review=str((folder/'sampled_interaction_review.json').relative_to(HERE)),
   review_sha256=sha(folder/'sampled_interaction_review.json'),dense_review=str((dense/'sampled_interaction_review.json').relative_to(HERE)),
   capture_receipt=str((folder/'capture.json').relative_to(HERE)),capture_receipt_sha256=sha(folder/'capture.json'),
   clean_video=True,robot_count=1,chapters=[dict(id=n,title=title,time_s=segments[n]['start']) for n,title in labels],
   full_paper_complete=False,physics_qualified=False,scientific_spectra_generated=False,
   renderer_sources=capture['source_sha256'],publisher_sha256=sha(Path(__file__)),
   initial_conditions=episode['initial_conditions'])
 (HERE/'measurement_delivery.json').write_text(json.dumps(delivery,indent=2,ensure_ascii=False)+'\n')
 destination.with_suffix('.json').write_text(json.dumps(delivery,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps(dict(published=str(destination),duration_s=delivery['video_duration_s'],frames=delivery['frames'],bytes=destination.stat().st_size)),flush=True)

if __name__=='__main__':main()
