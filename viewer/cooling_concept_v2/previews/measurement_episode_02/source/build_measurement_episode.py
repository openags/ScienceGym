"""Compose a complete cross-station, single-witness FTIR demonstration.

The robot opens the prepared instrument, collects the ordinary tool, walks to
the material bench, brings back the identified witness, performs the gold
background and sample-acquisition action sequence, and returns the objects.
This is an authored demonstration timeline, pending independent scene review;
button events and acquisition waits do not represent measured spectra.
"""
import argparse
import copy
import hashlib
import json
import numpy as np
from optical_choreography import HERE, canonical, JOINTS
from source_geometry import fk


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--trial',default='01')
    parser.add_argument('--connections',default='previews/measurement_connections_01/plan.json')
    parser.add_argument('--actions',default='previews/measurement_actions_03/actions.json')
    parser.add_argument('--buttons',default='previews/ftir_button_paths_01/plan.json')
    parser.add_argument('--button-transfers')
    parser.add_argument('--motion-speed',type=float,default=1.)
    parser.add_argument('--no-install',action='store_true')
    args=parser.parse_args();out=HERE/'previews'/('measurement_episode_'+args.trial);out.mkdir(exist_ok=False)
    assert 0.<args.motion_speed<=2.
    sources=['build_measurement_episode.py','measurement_episode.js','measurement_source_actions.js',
             'optical_episode.json','optical_delivery_episode.json','single_measurement_demo.json',
             'reference_transfer.json',args.connections,args.actions,args.buttons]
    if args.button_transfers:sources.append(args.button_transfers)
    pins={}
    for name in sources:
        data=(HERE/name).read_bytes();dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
    load=lambda name:json.loads((HERE/name).read_text())
    optical,delivery=load('optical_episode.json'),load('optical_delivery_episode.json')
    connection,button_report=load(args.connections),load(args.buttons)
    assert connection['passed'] and button_report['passed']
    actions=load(args.actions)['actions'];routes={r['id']:r for r in connection['routes']}
    buttons={r['button']:r for r in button_report['candidates'][0]['strokes']}
    button_transfers={}
    if args.button_transfers:
        transfers=load(args.button_transfers);assert transfers['passed']
        button_transfers={r['start']:r for r in transfers['routes']}
    caps=optical['selected_joint_speed_caps_rad_s']
    effective={n:j['limits']['velocity'] for n,j in JOINTS.items()}
    for name,joint in JOINTS.items():
        root=name;multiple=1.
        while JOINTS[root].get('mimic'):
            mimic=JOINTS[root]['mimic'];multiple*=float(mimic.get('multiplier',1.));root=mimic['joint']
        if multiple:effective[root]=min(effective[root],joint['limits']['velocity']/abs(multiple))
    stored=copy.deepcopy(delivery['initial_specimens']);reference=actions['reference_restore']['first']['reference_delta'];cover=0.
    segments=[];clock=0.

    def add(segment):
        nonlocal clock,reference,cover
        segment=copy.deepcopy(segment)
        segment.update(start=clock,end=clock+segment['duration_s'],reference_delta=copy.deepcopy(reference),
                       cover_angle_rad=cover,stored_specimens=copy.deepcopy(stored))
        segment.setdefault('tool_held',False);segment.setdefault('held_specimen',None)
        if 'rows' in segment:
            for row in segment['rows']:
                row['q']=canonical(row['q']);row.setdefault('closure',0.)
        if segment.get('source_action'):
            endpoint=actions[segment['source_action']]['last']
            cover=endpoint.get('cover_angle_rad',cover);reference=endpoint.get('reference_delta',reference)
        segments.append(segment);clock=segment['end']

    def source_action(identity,action,title):
        descriptor=actions[action]
        critical=[2.,6.,8.2,11.2,11.4,13.4,17.4,19.4] if action.startswith('ftir_') else []
        if action.startswith('reference_'):
            ref=load('reference_transfer.json')
            critical=sorted({(ref['duration_s']-t if action=='reference_restore' else t)
                             for s in ref['segments'] for t in [s['start'],s['end']]})
        add(dict(id=identity,title=title,source_action=action,source_duration_s=descriptor['duration_s'],
                 duration_s=descriptor['duration_s'],kind='work',critical_local_times_s=critical,
                 source_operation_refs=['OPT_REFERENCE' if 'reference' in identity else 'OPT_MOUNT']))

    def walk(identity,route_id,reverse=False,title='转移到下一操作位置'):
        route=routes[route_id];duration=route['duration_s'];rows=copy.deepcopy(route['rows'])
        if reverse:
            rows.reverse()
            for row in rows:row['time_s']=duration-row['time_s']
        add(dict(id=identity,title=title,duration_s=duration,rows=rows,interpolation='linear',kind='move',
                 planned_route=route_id,route_reversed=reverse,source_operation_refs=['MOVE.02','MOVE.04']))

    def reuse(prefix,source,title):
        nonlocal stored
        for segment in source['segments']:
            if not segment['id'].startswith(prefix):continue
            stored['white']=copy.deepcopy(segment['stored_specimens']['white'])
            value=copy.deepcopy(segment);value['title']=title
            value['kind']='move' if segment['interpolation']=='linear' and segment['duration_s']>2 else 'work'
            add(value)

    def timed_rows(rows,minimum=.05):
        result=[];elapsed=0.;previous=None
        for source in rows:
            row=copy.deepcopy(source);row['q']=canonical(row['q']);root=np.array(row['root'])
            palm=root@fk(row['q'])['right_palm_force_sensor']
            if previous:
                before,old_palm=previous
                elapsed+=max(minimum,1.6*max(abs(row['q'][n]-before['q'][n])/caps[n] for n in caps),
                             1.6*np.linalg.norm(palm[:3,3]-old_palm[:3,3])/.12)
            row['time_s']=elapsed;row.setdefault('button_travel_m',0.);result.append(row);previous=(row,palm)
        assert elapsed>0.
        return result,elapsed

    def press(prefix,identity,title,entry=True,exit=True):
        stroke=buttons[identity]
        parts=([('approach',stroke['entry'])] if entry else [])
        parts += [('touch_and_press',stroke['rows']),('release_and_retract',list(reversed(stroke['rows'])))]
        if exit:parts.append(('withdraw',list(reversed(stroke['entry']))))
        for suffix,rows in parts:
            rows,duration=timed_rows(rows)
            add(dict(id=prefix+'_'+suffix,title=title,rows=rows,duration_s=duration,interpolation='smooth',
                     kind='work',button=identity,source_operation_refs=['OPT_REFERENCE.09' if prefix.startswith('background') else 'OPT_SCAN']))

    def acquisition(kind):
        identity='scan_1' if kind=='background' else 'scan_0'
        transfer=button_transfers.get(identity)
        press(kind+'_select',identity,
              '按下背景采集键' if kind=='background' else '按下样品采集键',exit=not transfer)
        if transfer:
            rows,duration=timed_rows(transfer['rows'])
            add(dict(id=kind+'_move_to_confirm',title='移至确认按键',rows=rows,duration_s=duration,
                     interpolation='smooth',kind='work',button='scan_2',source_operation_refs=['OPT_SCAN']))
        press(kind+'_confirm','scan_2','确认采集',entry=not transfer)
        row=copy.deepcopy(buttons['scan_2']['entry'][0]);row.update(time_s=0.,closure=0.)
        end=copy.deepcopy(row);end['time_s']=12.
        add(dict(id=kind+'_acquisition',title='背景采集' if kind=='background' else '样品采集',
                 rows=[row,end],duration_s=12.,interpolation='linear',kind='wait',
                 acquisition=dict(kind=kind,representation='authored acquisition interval; no measured spectrum',
                                  presentation_duration_s=12.,inferred_instrument_interval_s=60.),
                 source_operation_refs=['OPT_REFERENCE.10' if kind=='background' else 'OPT_SCAN']))

    source_action('initial_open','ftir_open','打开光谱仪样品舱')
    walk('to_tool_staging','staging_to_cover',reverse=True,title='前往工具位置')
    reuse('white_delivery_',delivery,'取样并携样返回红外工位')
    walk('to_gold_storage','staging_to_reference_cap',title='前往金参考片收纳位')
    source_action('install_gold_reference','reference_restore','将金参考片放到测量端口')
    walk('reference_to_handle','reference_port_to_cover',title='返回舱盖把手')
    source_action('background_close','ftir_close','关闭舱盖准备背景测量')
    walk('to_background_controls','cover_to_controls',title='前往采集按键')
    acquisition('background')
    walk('background_controls_to_handle','cover_to_controls',reverse=True,title='返回舱盖把手')
    source_action('background_open','ftir_open','打开舱盖准备换样')
    walk('to_gold_reference','reference_port_to_cover',reverse=True,title='前往参考片端口')
    source_action('store_gold_reference','reference_store','取出金参考片并放入保护帽')
    walk('reference_to_sample_staging','staging_to_reference_cap',reverse=True,title='前往样品与工具位置')
    reuse('white_mount_',optical,'安装白色试片')
    walk('sample_to_handle','staging_to_cover',title='返回舱盖把手')
    source_action('sample_close','ftir_close','关闭舱盖准备样品测量')
    walk('to_sample_controls','cover_to_controls',title='前往采集按键')
    acquisition('sample')
    walk('sample_controls_to_handle','cover_to_controls',reverse=True,title='返回舱盖把手')
    source_action('sample_open','ftir_open','打开舱盖取回样品')
    walk('to_sample_retrieval','staging_to_cover',reverse=True,title='前往工具位置')
    reuse('white_retrieve_',optical,'取回样品并归还工具')
    walk('final_return_to_handle','staging_to_cover',title='返回舱盖把手')
    source_action('final_close','ftir_close','关闭样品舱并完成收纳')

    # Shorten motion only within the exact source-joint velocity bounds.
    # Preserve source-action timing and the explicit acquisition intervals.
    # Smoothstep's maximum derivative is 1.5; mimic-joint limits are included.
    clock=0.
    for segment in segments:
        factor=1.
        if segment.get('rows') and segment.get('kind')!='wait':
            allowed=args.motion_speed
            derivative=1.5 if segment['interpolation']=='smooth' else 1.
            for a,b in zip(segment['rows'],segment['rows'][1:]):
                dt=b['time_s']-a['time_s'];assert dt>0.
                for name in caps:
                    speed=derivative*abs(b['q'][name]-a['q'][name])/dt
                    if speed>1e-12:allowed=min(allowed,.98*effective[name]/speed)
            factor=allowed
            for row in segment['rows']:row['time_s']/=factor
            segment['duration_s']/=factor
        segment['motion_time_scale']=factor;segment['start']=clock
        clock+=segment['duration_s'];segment['end']=clock

    palm_to_tool=np.linalg.inv(optical['tool_T_palm']);tool_to_holder=np.linalg.inv(optical['holder_T_tool'])
    def endpoint(segment,last):
        if segment.get('source_action'):
            state=actions[segment['source_action']]['last' if last else 'first']
        else:state=segment['rows'][-1 if last else 0]
        q=canonical(state['q']);root=np.array(state['root'])
        tool=root@fk(q)['right_palm_force_sensor']@palm_to_tool if segment['tool_held'] else np.array(optical['tool_rest'])
        holders={k:np.array(v) for k,v in segment['stored_specimens'].items()}
        if segment['held_specimen']:holders[segment['held_specimen']]=tool@tool_to_holder
        return dict(q=q,root=root,tool=tool,holders=holders,
                    reference=np.array(state.get('reference_delta',segment['reference_delta'])),
                    cover=state.get('cover_angle_rad',segment['cover_angle_rad']),
                    key=state.get('button_travel_m',0.))
    transitions=[]
    for a,b in zip(segments,segments[1:]):
        x,y=endpoint(a,True),endpoint(b,False)
        errors=dict(joints_rad=max(abs(x['q'][n]-y['q'][n]) for n in x['q']),
                    root_matrix=float(np.max(abs(x['root']-y['root']))),
                    tool_matrix=float(np.max(abs(x['tool']-y['tool']))),
                    specimen_matrix=max(float(np.max(abs(x['holders'][k]-y['holders'][k]))) for k in x['holders']),
                    reference_matrix=float(np.max(abs(x['reference']-y['reference']))),
                    cover_rad=abs(x['cover']-y['cover']),button_travel_m=abs(x['key']-y['key']))
        transitions.append(dict(previous=a['id'],next=b['id'],**errors,passed=max(errors.values())<1e-6))
    result={k:copy.deepcopy(optical[k]) for k in ['tool_rest','tray_matrix','tool_T_palm','holder_T_tool','deformable_tool','selected_joint_speed_caps_rad_s']}
    result.update(scope=__doc__,status='composed_pending_independent_review',duration_s=clock,segments=segments,
                  transitions=transitions,continuous_at_segment_boundaries=all(v['passed'] for v in transitions),
                  source_sha256=pins,source_action_file=args.actions,initial_specimens=delivery['initial_specimens'],
                  initial_conditions=load('single_measurement_demo.json')['initial_conditions'],
                  whole_scene_validation_pending=True,dynamics_qualified=False,scientific_spectra_generated=False,
                  acquisition_configuration=dict(confirm_start=True,selector='SAMPLE',controller='OMNIC already running',
                      calibration_and_detector_setup='Prepared before the demo; not executed here.'),
                  final_conditions=load('single_measurement_demo.json')['final_conditions'])
    result['requested_motion_time_scale']=args.motion_speed
    (out/'episode.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    if result['continuous_at_segment_boundaries'] and not args.no_install:
        (HERE/'single_measurement_episode.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps(dict(duration_s=clock,segments=len(segments),continuous=result['continuous_at_segment_boundaries'],
                          bad_boundaries=[t for t in transitions if not t['passed']])),flush=True)


if __name__=='__main__':main()
