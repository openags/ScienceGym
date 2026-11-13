"""Prepend executed Cary-to-FTIR witness delivery to the optical exchange.

Both witnesses begin at their existing Cary-side support poses. The same tool
travels empty to each witness, grasps its annular wall, returns with it, and
places it at the declared FTIR staging pose before any exchange begins.
Initial tool allocation, instrument access/reference setup and acquisition
remain outside this episode. No dynamics or sensor-control credit.
"""
import copy,hashlib,json
import numpy as np
from scipy.spatial.transform import Rotation
from optical_choreography import HERE,canonical,load_json
from source_geometry import fk


def main():
    original=load_json('optical_episode.json');templates={s['id']:s for s in original['segments']};pickup=load_json('previews/optical_tool_pickup_path.json')
    collections={k:load_json('previews/cary_'+k+'_collection.json') for k in ['white','black']};exchanges={k:load_json('previews/optical_'+k+'_exchange.json') for k in collections}
    walks={};walk_sources=[]
    for kind in collections:
        walks[kind]={}
        for direction,suffix in [('out','delivery_walk'),('back','return_walk')]:
            name='previews/optical_'+kind+'_'+suffix+'.json'
            if not (HERE/name).exists():name='previews/optical_white_'+suffix+'.json'
            walk=load_json(name);assert walk['passed'];index=-1 if direction=='out' else 0
            assert np.allclose(walk['rows'][index]['root'],collections[kind]['root'],rtol=0,atol=1e-9)
            assert np.allclose(walk['rows'][0 if direction=='out' else -1]['root'],pickup['root'],rtol=0,atol=1e-9)
            walks[kind][direction]=walk;walk_sources.append(name)
    postures=load_json('previews/optical_delivery_postures.json');assert postures['passed']
    caps=original['selected_joint_speed_caps_rad_s'];root=np.array(pickup['root']);palm_to_tool=np.linalg.inv(original['tool_T_palm']);tool_to_holder=np.linalg.inv(original['holder_T_tool']);tool_rest=np.array(original['tool_rest'])
    stored={k:collections[k]['initial_holder'] for k in collections};initial_stored=copy.deepcopy(stored);segments=[];clock=0.;amount=load_json('previews/specimen_tool_fit.json')['carrier_grip_closure']

    def transforms(row,tool_held,held,poses):
        palm=np.array(row['root'])@fk(row['q'])['right_palm_force_sensor'];tool=palm@palm_to_tool if tool_held else tool_rest
        holders={k:np.array(v) for k,v in poses.items()}
        if held:holders[held]=tool@tool_to_holder
        return palm,tool,holders

    def add(name,rows,base=root,tool_held=True,held=None,closure=0.,reverse=False,fixed=False,hand_override=None):
        nonlocal clock
        selected=list(reversed(rows)) if reverse else rows;result=[];elapsed=0.;previous=None
        for source in selected:
            q=canonical(source['q']);value=float(source.get('closure',closure))
            if hand_override is not None:q.update(hand_override);value=0.
            row=dict(q=q,root=source.get('root',base.tolist()),closure=value)
            palm,tool,holders=transforms(row,tool_held,held,stored)
            if previous:
                old,old_source,old_palm,old_holders=previous
                if fixed:dt=abs(source['time_s']-old_source['time_s'])
                else:
                    dt=max(.025,1.6*max(abs(q[n]-old['q'][n])/caps[n] for n in caps),1.6*np.linalg.norm(palm[:3,3]-old_palm[:3,3])/.12)
                    if held:
                        a,b=old_holders[held],holders[held]
                        dt=max(dt,1.6*np.linalg.norm(b[:3,3]-a[:3,3])/.08,1.6*np.linalg.norm(Rotation.from_matrix(a[:3,:3].T@b[:3,:3]).as_rotvec())/.8)
                elapsed+=dt
            row['time_s']=elapsed;result.append(row);previous=(row,source,palm,holders)
        segments.append(dict(id=name,start=clock,end=clock+elapsed,duration_s=elapsed,tool_held=tool_held,held_specimen=held,stored_specimens=copy.deepcopy(stored),interpolation='linear' if fixed else 'smooth',source_operation_refs=['OPT_UNLOAD','MOVE.02','MOVE.04','OPT_MOUNT.05'],rows=result));clock+=elapsed

    def template(name,new_name):
        nonlocal clock
        segment=copy.deepcopy(templates[name]);segment.update(id=new_name,start=clock,end=clock+segment['duration_s'],stored_specimens=copy.deepcopy(stored));segments.append(segment);clock=segment['end']

    open_hand=load_json('previews/tweezers_closure.json')['rows'][0]['q']
    def walk_stages(prefix,direction,walk,kind):
        held=kind if direction=='back' else None;hand_override=None if held else open_hand;closure=amount if held else 0.
        indices=postures['walks'][direction];i,j=indices['lower_after_index'],indices['raise_after_index'];rows=walk['rows']
        start_station,end_station=('ftir','cary') if direction=='out' else ('cary','ftir')
        add(prefix+'_retreat',rows[:i+1],fixed=True,held=held,closure=closure,hand_override=hand_override)
        path=postures['paths'][start_station];add(prefix+'_lower_hand',path['lower']['rows'],base=np.array(path['root']),held=held,closure=closure,hand_override=hand_override)
        low=postures['posture']['q'];middle=[{**r,'q':{**r['q'],**{n:low[n] for n in postures['joint_names']}}} for r in rows[i:j+1]]
        add(prefix+'_forward_walk',middle,fixed=True,held=held,closure=closure,hand_override=hand_override)
        path=postures['paths'][end_station];add(prefix+'_raise_hand',path['lower']['rows'],base=np.array(path['root']),reverse=True,held=held,closure=closure,hand_override=hand_override)
        add(prefix+'_approach',rows[j:],fixed=True,held=held,closure=closure,hand_override=hand_override)

    for kind in ['white','black']:
        prefix=kind+'_delivery';collection=collections[kind];exchange=exchanges[kind];walk=walks[kind]
        for suffix in ['free_entry','approach_tool','close_hand_on_tool','lift_tool']:template('white_mount_'+suffix,prefix+'_'+suffix)
        add(prefix+'_take_tool_to_carry',exchange['empty_tool_return']['rows'],reverse=True,hand_override=open_hand)
        walk_stages(prefix+'_walk_to_cary','out',walk['out'],kind)
        base=np.array(collection['root']);add(prefix+'_approach_witness',collection['incoming']['rows'],base=base)
        for stage in ['lower_open_tips','close_tweezers','lift_witness']:
            add(prefix+'_'+stage,[r for r in collection['contact'] if r['stage']==stage],base=base,held=kind if stage=='lift_witness' else None)
        add(prefix+'_to_carry',collection['outgoing']['rows'],base=base,closure=amount,held=kind)
        walk_stages(prefix+'_carry_to_ftir','back',walk['back'],kind)
        add(prefix+'_above_support',exchange['transfer']['rows'],reverse=True,closure=amount,held=kind)
        for stage in ['lift_witness','close_tweezers','lower_open_tips']:
            if stage=='close_tweezers':stored[kind]=exchange['initial_holder']
            add(prefix+'_place_'+stage,[r for r in exchange['contact'] if r['stage']==stage],reverse=True,held=kind if stage=='lift_witness' else None)
        add(prefix+'_return_tool',exchange['approach']['rows'],reverse=True,hand_override=open_hand)
        for suffix in ['reverse_lift_tool','reverse_close_hand_on_tool','reverse_approach_tool','free_exit']:template('white_mount_'+suffix,prefix+'_'+suffix)
    delivery_duration=clock
    assert stored==original['initial_specimens']
    for segment in original['segments']:
        added=copy.deepcopy(segment);added['start']+=clock;added['end']+=clock;segments.append(added)
    clock+=original['duration_s'];transitions=[]
    for a,b in zip(segments,segments[1:]):
        x,y=a['rows'][-1],b['rows'][0];_,ta,ha=transforms(x,a['tool_held'],a['held_specimen'],a['stored_specimens']);_,tb,hb=transforms(y,b['tool_held'],b['held_specimen'],b['stored_specimens'])
        transitions.append(dict(previous=a['id'],next=b['id'],maximum_joint_jump_rad=max(abs(x['q'][n]-y['q'][n]) for n in caps),maximum_root_matrix_jump=float(np.max(abs(np.array(x['root'])-np.array(y['root'])))),tool_translation_jump_m=float(np.linalg.norm(ta[:3,3]-tb[:3,3])),tool_rotation_jump_rad=float(np.linalg.norm(Rotation.from_matrix(ta[:3,:3].T@tb[:3,:3]).as_rotvec())),specimen_translation_jump_m=max(float(np.linalg.norm(ha[k][:3,3]-hb[k][:3,3])) for k in ha),specimen_rotation_jump_rad=max(float(np.linalg.norm(Rotation.from_matrix(ha[k][:3,:3].T@hb[k][:3,:3]).as_rotvec())) for k in ha)))
    bad=[t for t in transitions if max(v for k,v in t.items() if k not in ['previous','next'])>=1e-6]
    sources=['build_delivery_episode.py','optical_episode.json','previews/cary_white_collection.json','previews/cary_black_collection.json','previews/optical_white_exchange.json','previews/optical_black_exchange.json','previews/optical_tool_pickup_path.json','previews/tweezers_closure.json','previews/specimen_tool_fit.json','previews/optical_delivery_postures.json']+sorted(set(walk_sources))
    result={**original,'scope':__doc__,'status':'assembled_pending_independent_review','duration_s':clock,'delivery_duration_s':delivery_duration,'segments':segments,'transitions':transitions,'continuous_at_segment_boundaries':not bad,'initial_specimens':initial_stored,'initial_conditions':['Both identified witnesses begin at their existing Cary-side bench support poses. Cary measurement and clamp operation are not executed.','The ordinary tweezers and tray are already allocated to FTIR staging. Supply preparation is not executed.','The Nicolet access is open and its reference is capped. Background/sample acquisition and the complete paper workflow are not executed.'],'gait_reuse':{k:dict(zip(['out','back'],walk_sources[i*2:i*2+2])) for i,k in enumerate(collections)},'source_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in sources}}
    (HERE/'optical_delivery_episode.json').write_text(json.dumps(result,separators=(',',':'))+'\n');print(json.dumps(dict(duration_s=clock,delivery_duration_s=delivery_duration,segments=len(segments),continuous=not bad,bad_boundaries=bad)),flush=True)


if __name__=='__main__':main()
