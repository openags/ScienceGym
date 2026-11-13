"""Compose continuous tool pickup, mounting, retrieval and return for both witnesses.

The local episode begins with optical materials already delivered and the FTIR
access open. Scan controls and upstream delivery are not credited. Every held
tool/specimen transform is derived from the actual source palm FK; placement
changes ownership only after the carrier reaches its declared support pose.
"""
import hashlib,json
import numpy as np
from scipy.spatial.transform import Rotation
from optical_choreography import HERE,Scene,JOINTS,INDEPENDENT,canonical,load_json
from source_geometry import fk


def main():
    scene=Scene();pickup=load_json('previews/optical_tool_pickup_path.json');side=load_json('previews/optical_sidestep.json');port=load_json('previews/specimen_port_refined.json')['candidates'][0]
    exchanges={kind:load_json('previews/optical_'+kind+'_exchange.json') for kind in ['white','black']};assert pickup['passed_local_geometry'] and side['passed'] and all(v['passed_local_geometry'] for v in exchanges.values())
    work_base=np.array(pickup['root']);port_base=np.array(port['root']).reshape(4,4).T;amount=scene.fit['carrier_grip_closure'];stored={k:v['initial_holder'] for k,v in exchanges.items()};initial_stored=dict(stored)
    effective={n:j['limits']['velocity'] for n,j in JOINTS.items()}
    for name,joint in JOINTS.items():
        root=name;multiplier=1.
        while JOINTS[root].get('mimic'):
            m=JOINTS[root]['mimic'];multiplier*=float(m.get('multiplier',1.));root=m['joint']
        if multiplier:effective[root]=min(effective[root],joint['limits']['velocity']/abs(multiplier))
    caps={n:min(effective[n],.6 if n.startswith('waist') or any(s in n for s in ['index','middle','ring','little','thumb']) else 1.2) for n in INDEPENDENT};segments=[];clock=0.

    def object_poses(row,tool_held,held_specimen):
        base=np.array(row['root']);palm=base@fk(row['q'])['right_palm_force_sensor'];tool=palm@scene.palm_T_tool if tool_held else scene.tool_rest
        holders={k:np.array(v) for k,v in stored.items()}
        if held_specimen:holders[held_specimen]=tool@scene.tool_T_holder
        return palm,tool,holders

    def add(name,rows,root=work_base,tool_held=True,closure=0.,held_specimen=None,reverse=False,hand_override=None,fixed=False,refs=None):
        nonlocal clock
        selected=list(reversed(rows)) if reverse else list(rows);result=[];local_clock=0.;previous=None;previous_source=None
        for source in selected:
            q=canonical(source['q']);value=float(source.get('closure',closure))
            if hand_override is not None:q.update(scene.hand_q(hand_override));value=hand_override
            row=dict(q=q,root=np.array(source.get('root',root)).tolist(),closure=value)
            palm,tool,holders=object_poses(row,tool_held,held_specimen)
            if previous is not None:
                if fixed:delta=abs(source['time_s']-previous_source['time_s'])
                else:
                    delta=max(.025,1.6*max(abs(q[n]-previous['q'][n])/caps[n] for n in INDEPENDENT),1.6*np.linalg.norm(palm[:3,3]-previous['palm'][:3,3])/.12)
                    if held_specimen:
                        a=previous['holders'][held_specimen];b=holders[held_specimen]
                        delta=max(delta,1.6*np.linalg.norm(b[:3,3]-a[:3,3])/.08,1.6*np.linalg.norm(Rotation.from_matrix(a[:3,:3].T@b[:3,:3]).as_rotvec())/.8)
                local_clock+=delta
            row['time_s']=local_clock;result.append(row);previous={**row,'palm':palm,'tool':tool,'holders':holders};previous_source=source
        segment=dict(id=name,start=clock,end=clock+local_clock,duration_s=local_clock,tool_held=tool_held,held_specimen=held_specimen,stored_specimens=dict(stored),interpolation='linear' if fixed else 'smooth',source_operation_refs=refs or [],rows=result)
        segments.append(segment);clock+=local_clock;return segment

    def tool_pickup(prefix):
        add(prefix+'_free_entry',pickup['entry'],tool_held=False,refs=['OPT_MOUNT.05'])
        for stage in ['approach_tool','close_hand_on_tool','lift_tool']:
            add(prefix+'_'+stage,[r for r in pickup['contact'] if r['stage']==stage],tool_held=stage=='lift_tool',refs=['OPT_MOUNT.05'])

    def tool_stow(prefix):
        for stage in ['lift_tool','close_hand_on_tool','approach_tool']:
            add(prefix+'_reverse_'+stage,[r for r in pickup['contact'] if r['stage']==stage],tool_held=stage=='lift_tool',reverse=True,refs=['OPT_UNLOAD','RESET'])
        add(prefix+'_free_exit',pickup['entry'],tool_held=False,reverse=True,refs=['RESET'])

    def tool_closure(prefix,kind,a,b,root=port_base,body=None):
        body=body or port['rows'][0]['q'];rows=[]
        for u in np.linspace(0,1,41):
            c=float(a+(b-a)*u);rows.append(dict(q={**body,**scene.hand_q(c)},closure=c))
        add(prefix,rows,root=root,held_specimen=None,refs=['OPT_MOUNT.05','OPT_MOUNT.06'])

    for kind,exchange in exchanges.items():
        prefix=kind+'_mount';tool_pickup(prefix)
        add(prefix+'_to_pregrasp',exchange['approach']['rows'],refs=['OPT_MOUNT.05'])
        for stage in ['lower_open_tips','close_tweezers','lift_witness']:
            add(prefix+'_'+stage,[r for r in exchange['contact'] if r['stage']==stage],held_specimen=kind if stage=='lift_witness' else None,refs=['OPT_MOUNT.05'])
        add(prefix+'_to_carry',exchange['transfer']['rows'],closure=amount,held_specimen=kind,refs=['OPT_MOUNT.05'])
        add(prefix+'_to_port',side['rows'],closure=amount,held_specimen=kind,reverse=True,fixed=True,refs=['OPT_MOUNT.05'])
        add(prefix+'_seat',port['rows'],root=port_base,closure=amount,held_specimen=kind,reverse=True,refs=['OPT_MOUNT.05','OPT_MOUNT.06'])
        stored[kind]=scene.specimen_port.tolist();tool_closure(prefix+'_release',kind,amount,0.)
        add(prefix+'_withdraw_tool',port['rows'],root=port_base,hand_override=0.,refs=['OPT_MOUNT.06'])
        add(prefix+'_return_to_tools',side['rows'],hand_override=0.,fixed=True,refs=['OPT_MOUNT.06'])
        add(prefix+'_return_tool',exchange['empty_tool_return']['rows'],hand_override=0.,refs=['OPT_MOUNT.06'])
        tool_stow(prefix)
        resting=segments[-1]['rows'][-1]['q'];add(kind+'_mounted_hold',[dict(q=resting,time_s=0.),dict(q=resting,time_s=2.)],tool_held=False,fixed=True,refs=['OPT_MOUNT.06'])
        prefix=kind+'_retrieve';tool_pickup(prefix)
        add(prefix+'_take_tool_to_carry',exchange['empty_tool_return']['rows'],reverse=True,hand_override=0.,refs=['OPT_UNLOAD'])
        add(prefix+'_to_port',side['rows'],reverse=True,hand_override=0.,fixed=True,refs=['OPT_UNLOAD'])
        add(prefix+'_lower_open_tips',port['rows'],root=port_base,reverse=True,hand_override=0.,refs=['OPT_UNLOAD'])
        tool_closure(prefix+'_close',kind,0.,amount)
        add(prefix+'_lift',port['rows'],root=port_base,closure=amount,held_specimen=kind,refs=['OPT_UNLOAD'])
        add(prefix+'_to_staging',side['rows'],closure=amount,held_specimen=kind,fixed=True,refs=['OPT_UNLOAD'])
        add(prefix+'_above_support',exchange['transfer']['rows'],reverse=True,closure=amount,held_specimen=kind,refs=['OPT_UNLOAD'])
        lift=[r for r in exchange['contact'] if r['stage']=='lift_witness'];add(prefix+'_seat',lift,reverse=True,held_specimen=kind,refs=['OPT_UNLOAD'])
        stored[kind]=exchange['initial_holder'];tool_closure(prefix+'_release',kind,amount,0.,root=work_base,body=lift[0]['q'])
        lower=[r for r in exchange['contact'] if r['stage']=='lower_open_tips'];add(prefix+'_withdraw',lower,reverse=True,hand_override=0.,refs=['OPT_UNLOAD'])
        add(prefix+'_return_tool',exchange['approach']['rows'],reverse=True,hand_override=0.,refs=['RESET']);tool_stow(prefix)
    transitions=[]
    def snapshot(segment,row):
        saved=dict(stored);stored.clear();stored.update(segment['stored_specimens']);value=object_poses(row,segment['tool_held'],segment['held_specimen']);stored.clear();stored.update(saved);return value
    for a,b in zip(segments,segments[1:]):
        x,y=a['rows'][-1],b['rows'][0];pa,ta,ha=snapshot(a,x);pb,tb,hb=snapshot(b,y)
        transitions.append(dict(previous=a['id'],next=b['id'],maximum_joint_jump_rad=max(abs(x['q'][n]-y['q'][n]) for n in INDEPENDENT),maximum_root_matrix_jump=float(np.max(abs(np.array(x['root'])-np.array(y['root'])))),tool_translation_jump_m=float(np.linalg.norm(ta[:3,3]-tb[:3,3])),tool_rotation_jump_rad=float(np.linalg.norm(Rotation.from_matrix(ta[:3,:3].T@tb[:3,:3]).as_rotvec())),specimen_translation_jump_m=max(float(np.linalg.norm(ha[k][:3,3]-hb[k][:3,3])) for k in ha),specimen_rotation_jump_rad=max(float(np.linalg.norm(Rotation.from_matrix(ha[k][:3,:3].T@hb[k][:3,:3]).as_rotvec())) for k in ha)))
    continuous=all(max(v for k,v in t.items() if k not in ['previous','next'])<1e-6 for t in transitions)
    sources=['build_optical_episode.py','optical_choreography.py','previews/optical_tool_pickup_path.json','previews/optical_sidestep.json','previews/specimen_port_refined.json','previews/optical_white_exchange.json','previews/optical_black_exchange.json','previews/specimen_tool_fit.json']
    result=dict(scope=__doc__,status='assembled_pending_independent_review',duration_s=clock,segments=segments,transitions=transitions,continuous_at_segment_boundaries=continuous,source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in sources},initial_specimens=initial_stored,tool_rest=scene.tool_rest.tolist(),tray_matrix=scene.tray_matrix.tolist(),tool_T_palm=scene.tool_T_palm.tolist(),holder_T_tool=scene.holder_T_tool.tolist(),selected_joint_speed_caps_rad_s=caps,deformable_tool=dict(id='tweezers_white',model='symmetric_fixed_heel_cantilever_v1',length_m=.13,tip_deflection_m=.001775),initial_conditions=['The two witnesses and ordinary tools have already been delivered to the declared optical staging layout; this episode does not execute that delivery.','The Nicolet access is open and the gold reference is protected in its cap.','No background/sample acquisition, full paper branch or dynamic grasp credit is assigned.'],whole_scene_validation_pending=True)
    (HERE/'optical_episode.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(duration_s=clock,segments=len(segments),continuous=continuous,bad_boundaries=[t for t in transitions if max(v for k,v in t.items() if k not in ['previous','next'])>=1e-6])),flush=True)


if __name__=='__main__':main()
