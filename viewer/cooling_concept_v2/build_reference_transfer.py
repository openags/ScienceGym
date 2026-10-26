"""Assemble screened reference handling segments for scene-level review.

Assembly is not acceptance. The complete forward and reverse sequence must
be checked after integration, including its phase boundaries and actual assets.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from source_geometry import KIN, ASSETS, fk
from plan_reference_storage import HERE, translation


def main():
    names=['previews/reference_storage_endpoints.json','previews/reference_port_entry_path.json','previews/reference_cap_exit_path.json','previews/reference_carry_path.json','previews/reference_contact_review.json','reference_sidestep.json','reference_lift_path.json','optical_setup.json','build_reference_transfer.py']
    pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names}
    values={n:json.loads((HERE/n).read_text()) for n in names if n.endswith('.json')}
    endpoints=values[names[0]];entry=values[names[1]];exit_path=values[names[2]];carry=values[names[3]];contact=values[names[4]];step=values[names[5]];lift=values[names[6]];setup=values[names[7]]
    assert entry['passed_planner_edges'] and exit_path['passed_planner_edges'] and carry['passed_planner_edges'] and contact['passed'] and step['passed_kinematics']
    joints={j['name']:j for j in KIN['joints'] if j['type']=='revolute'};effective={n:j['limits']['velocity'] for n,j in joints.items()}
    for name,j in joints.items():
        root=name;multiplier=1.
        while joints[root].get('mimic'):
            m=joints[root]['mimic'];multiplier*=float(m.get('multiplier',1));root=m['joint']
        if multiplier:effective[root]=min(effective[root],j['limits']['velocity']/abs(multiplier))
    independent=[n for n,j in joints.items() if not j.get('mimic')]
    caps={n:min(effective[n],.6 if n=='waist_pitch_joint' else .6 if any(f in n for f in ['index','middle','ring','little','thumb']) else 1.2) for n in independent}
    port=np.array(setup['ports']['ftir_sample']['position_m']);palm=np.array(lift['grasp']['palm_matrix']);initial=translation(port)
    segments=[];clock=0.

    def canonical(q):return {n:float(q.get(n,0.)) for n in independent}

    def add(name,rows,root=None,reference_offset=None,reverse=False,fixed=False,mode='cartesian',closed=0.):
        nonlocal clock
        rows=[dict(r) for r in rows]
        if reverse:rows=rows[::-1]
        previous=None;local_clock=0.;result=[]
        for r in rows:
            q=canonical(r['q']);base=np.array(r.get('root',root))
            ref_offset=np.array(r.get('reference_offset',reference_offset if reference_offset is not None else r.get('offset',[0,0,0])))
            if previous is not None:
                if fixed:delta=abs(r['time_s']-previous['source_time_s'])
                else:
                    delta=max(.025,1.6*max(abs(q[n]-previous['q'][n])/caps[n] for n in independent),1.6*np.linalg.norm(ref_offset-previous['reference_offset'])/.10)
                local_clock+=delta
            row=dict(time_s=local_clock,q=q,root=base.tolist(),reference_offset=ref_offset.tolist(),closed=r.get('closed',closed))
            if 'offset' in r:row['hand_target']=(translation(port+np.array(r['offset']))@palm).tolist()
            result.append(row);previous={**row,'source_time_s':r.get('time_s')}
        segment=dict(id=name,start=clock,end=clock+local_clock,duration_s=local_clock,interpolation='linear' if name=='sidestep' else 'smooth',mode=mode,rows=result)
        segments.append(segment);clock+=local_clock
        return segment

    rows=endpoints['rows'];by_stage=lambda name:[r for r in rows if r['stage']==name]
    add('free_entry',entry['rows'],entry['root'],[0,0,0],fixed=True,mode='free')
    add('lower_open_hand',by_stage('lower_open_hand'),reference_offset=[0,0,0])
    add('close_grip',by_stage('close_reference_grip'),reference_offset=[0,0,0])
    add('settle_grasp',[dict(by_stage('close_reference_grip')[-1],time_s=0.),dict(by_stage('lift_reference')[0],time_s=.25)],reference_offset=[0,0,0],fixed=True)
    add('lift',by_stage('lift_reference'))
    add('sidestep',step['rows'],fixed=True)
    cap_rows=by_stage('seat_reference_in_cap');goal=min(range(len(cap_rows)),key=lambda i:abs(cap_rows[i]['offset'][2]-endpoints['final_offset'][2]-.03));preplacement=np.array(cap_rows[goal]['offset'])
    segment=add('held_transfer',carry['rows'],carry['root'],fixed=True,mode='held_fk',closed=1.)
    reference_in_palm=np.linalg.inv(initial@palm)@initial
    corrections=[]
    for row,offset in [(segment['rows'][0],np.array(step['rows'][-1]['reference_offset'])),(segment['rows'][-1],preplacement)]:
        actual=np.array(row['root'])@fk(row['q'])['left_palm_force_sensor']@reference_in_palm
        corrections.append((translation(port+offset)@np.linalg.inv(actual)).tolist())
    segment['endpoint_reference_corrections']=corrections
    add('seat_in_cap',cap_rows[goal:])
    add('release_grip',by_stage('release_reference'),reference_offset=endpoints['final_offset'])
    add('withdraw_open_hand',by_stage('withdraw_open_hand'),reference_offset=endpoints['final_offset'])
    add('free_exit',exit_path['rows'],exit_path['root'],endpoints['final_offset'],reverse=True,fixed=True,mode='free')
    transitions=[]
    for a,b in zip(segments,segments[1:]):
        error=max(abs(a['rows'][-1]['q'][n]-b['rows'][0]['q'][n]) for n in independent)
        transitions.append(dict(previous=a['id'],next=b['id'],maximum_joint_difference_rad=error))
    result=dict(scope=__doc__,source_sha256=pins,duration_s=clock,segments=segments,transitions=transitions,
                reference_port_m=port.tolist(),reference_in_palm=reference_in_palm.tolist(),grasp=lift['grasp'],cap_floor_m=endpoints['cap_floor_m'],storage_offset_m=endpoints['final_offset'],
                source_asset_sha256={n:ASSETS[n]['geometry_sha256'] for n in ['g1','pike','nicolet']},whole_scene_validation_pending=True)
    (HERE/'reference_transfer.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(duration_s=clock,segments=[dict(id=s['id'],duration_s=s['duration_s'],rows=len(s['rows'])) for s in segments],transitions=transitions)),flush=True)


if __name__=='__main__':main()
