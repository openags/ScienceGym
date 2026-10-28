"""Compose continuous G1 lid opening and hood removal in the established lab.

This is access preparation for the paper's Cary measurement workflow. It does
not execute reference/sample exchange, acquisition or the complete paper. The
lid is first opened 150 mm to clear the hood; that split is a reconstruction
inference, while complete hood removal is allowed by the manufacturer manual.
"""
import argparse,gzip,hashlib,itertools,json
import numpy as np
from scipy.spatial.transform import Rotation
from optical_choreography import HERE,canonical,load_json
from source_geometry import ROOT,fk


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--extension')
    parser.add_argument('--return-path')
    args=parser.parse_args()
    if bool(args.extension)!=bool(args.return_path):raise ValueError('Extension and return path are required together')
    files={'lid':'previews/cary_lid_operation_08.json','stance':'previews/cary_lid_to_hood_steps.json','release':'previews/cary_cover_release_01.json','carry':'previews/cary_cover_carry_03.json'}
    if args.extension:files.update(extension=args.extension,return_path=args.return_path)
    plans={k:load_json(v) for k,v in files.items()}
    assert all(d['passed_planning_geometry'] for d in plans.values())
    lid,stance,release,carry=[plans[n] for n in ['lid','stance','release','carry']]
    caps=load_json('optical_episode.json')['selected_joint_speed_caps_rad_s'];inverse_grasp=np.linalg.inv(release['grasp_palm_world']);segments=[];clock=0.
    def cover_pose(row,held):
        return np.array(row['root'])@fk(row['q'])['right_palm_force_sensor']@inverse_grasp if held else np.array(row.get('cover_matrix',np.eye(4)))
    def add(identity,rows,root,held=False,fixed=False):
        nonlocal clock
        if len(rows)<2:return
        stretch=max([1.]+[max(abs(b['q'][n]-a['q'][n])/caps[n] for n in caps)/(b['time_s']-a['time_s']) for a,b in zip(rows,rows[1:])]) if fixed else 1.
        result=[];elapsed=0.;previous=None
        for source in rows:
            row=dict(q=canonical(source['q']),root=source.get('root',root),lid_m=source.get('lid_m',.15),cover_matrix=source.get('cover_matrix',np.eye(4).tolist()))
            palm=np.array(row['root'])@fk(row['q'])['right_palm_force_sensor'];cover=cover_pose(row,held)
            if previous:
                old,old_source,old_palm,old_cover=previous
                if fixed:dt=(source['time_s']-old_source['time_s'])*stretch
                else:
                    dt=max(.025,1.6*max(abs(row['q'][n]-old['q'][n])/caps[n] for n in caps),1.6*np.linalg.norm(palm[:3,3]-old_palm[:3,3])/.12)
                    if held:dt=max(dt,1.6*np.linalg.norm(cover[:3,3]-old_cover[:3,3])/.08,1.6*np.linalg.norm(Rotation.from_matrix(old_cover[:3,:3].T@cover[:3,:3]).as_rotvec())/.8)
                assert dt>0,(identity,dt)
                elapsed+=dt
            row['time_s']=elapsed;result.append(row);previous=(row,source,palm,cover)
        segments.append(dict(id=identity,start=clock,end=clock+elapsed,duration_s=elapsed,cover_held=held,lid_held=identity in ['lid_slide','extension_step_push_lid'],interpolation='linear' if fixed else 'smooth',rows=result));clock+=elapsed
    def grouped(prefix,rows,root):
        for (stage,held),group in itertools.groupby(rows,key=lambda r:(r['stage'],r.get('held',False))):
            group=list(group);add(prefix+'_'+stage,group,root,held,all('time_s' in r for r in group))
    add('lid_free_entry',lid['entry'],lid['root'])
    grouped('lid',lid['contact'],lid['root'])
    add('lid_return_hand',lid['exit'],lid['root'])
    add('step_to_hood',stance['rows'],lid['root'],fixed=True)
    add('hood_free_entry',release['entry'],release['root'])
    grouped('hood',release['contact'],release['root'])
    grouped('hood',carry['rows'],release['root'])
    add('hood_return_hand',carry['exit'],carry['rows'][-1]['root'])
    if args.extension:
        add('return_to_lid',plans['return_path']['rows'],carry['rows'][-1]['root'],fixed=True)
        grouped('extension',plans['extension']['rows'],plans['extension']['initial_root'])
    transitions=[]
    for a,b in zip(segments,segments[1:]):
        x,y=a['rows'][-1],b['rows'][0];ca,cb=cover_pose(x,a['cover_held']),cover_pose(y,b['cover_held'])
        transitions.append(dict(previous=a['id'],next=b['id'],maximum_joint_jump_rad=max(abs(x['q'][n]-y['q'][n]) for n in caps),maximum_root_matrix_jump=float(np.max(abs(np.array(x['root'])-np.array(y['root'])))),lid_jump_m=abs(x['lid_m']-y['lid_m']),cover_translation_jump_m=float(np.linalg.norm(ca[:3,3]-cb[:3,3])),cover_rotation_jump_rad=float(np.linalg.norm(Rotation.from_matrix(ca[:3,:3].T@cb[:3,:3]).as_rotvec()))))
    bad=[t for t in transitions if max(v for k,v in t.items() if k not in ['previous','next'])>=1e-6]
    with gzip.open(HERE/'audits/optical_exchange_01/frames.jsonl.gz','rt') as stream:frame=json.loads(next(stream))
    initial_scene={k:frame[k] for k in ['groups','parts','extra_matrices']}
    geometry=release['geometry'];interfaces=json.loads((ROOT/'assets/cary_5000_v1/interfaces.json').read_text())
    sources=list(files.values())+['build_cary_access_episode.py','optical_episode.json','audits/optical_exchange_01/frames.jsonl.gz']
    report=dict(scope=__doc__,status='assembled_pending_independent_review',duration_s=clock,segments=segments,transitions=transitions,continuous_at_segment_boundaries=not bad,selected_joint_speed_caps_rad_s=caps,grasp_palm_world=release['grasp_palm_world'],geometry_override=dict(asset='cary',path=geometry,sha256=hashlib.sha256((ROOT/geometry).read_bytes()).hexdigest()),cover_parts=interfaces['extension_cover_parts'],lid_parts=interfaces['sliding_lid_parts'],initial_scene=initial_scene,whole_scene_validation_pending=True,initial_conditions=['Established complete laboratory; static tool and reference poses match optical_exchange_01 frame 0.','Cary DRA is installed and the reference is clamped at the port; installation and electrical connection are outside this access episode.','Main lid and removable hood start closed. Hood handle height and hose relief geometry are explicitly inferred operability revisions.','The instrument main lid remains partially open after this episode. Reference/sample exchange, measurement, closure and the complete paper workflow are not executed.'],source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in sources})
    (HERE/'cary_access_episode.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
    print(json.dumps(dict(duration_s=clock,segments=len(segments),continuous=not bad,bad_boundaries=bad)),flush=True)
    if bad:raise RuntimeError('Cary operation boundaries are discontinuous')


if __name__=='__main__':main()
