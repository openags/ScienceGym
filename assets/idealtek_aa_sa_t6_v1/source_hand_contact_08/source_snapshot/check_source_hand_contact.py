"""Contact characterization with the actual Inspire hand and a free tweezer.

The source terminal wrist housing is mounted to a stationary test stand. The
tool retains its free joint and gravity, and rests on the declared plane or
ordinary free tray. Only six source
hand motors actuate. This is a closure/release diagnostic, not whole-body
pickup, perception qualification, arm reach, or a laboratory task receipt.
"""
import argparse
from copy import deepcopy
import hashlib
import itertools
import json
from pathlib import Path
import shutil
import sys
import time
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[2]
ROBOT = ROOT/'assets/unitree_g1_inspire_v1'
RUNTIME = ROOT/'simulation/g1_cooling_demo'
sys.path.insert(0, str(RUNTIME))
sys.path.insert(0, str(ROOT/'viewer/cooling_concept_v2'))
from source_geometry import fk
from hand_touch import attach as attach_touch, read as read_touch, TOUCH_PADS
from thumb_contacts import attach as attach_thumb
from distal_contacts import attach as attach_distal


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def numbers(values):
    return ' '.join(format(float(v), '.17g') for v in values)


def pose(position, quaternion):
    result = np.eye(4)
    result[:3, :3] = Rotation.from_quat(np.r_[quaternion[1:], quaternion[0]]).as_matrix()
    result[:3, 3] = position
    return result


def build(source, fit, output, candidate_index=0, pregrasp_index=None):
    source, fit, output = map(lambda p: Path(p).resolve(), [source, fit, output])
    output.mkdir(parents=True, exist_ok=False)
    (output/'source_snapshot').mkdir()
    for path in [Path(__file__), RUNTIME/'hand_touch.py', RUNTIME/'thumb_contacts.py',
                 RUNTIME/'distal_contacts.py']:
        shutil.copyfile(path, output/'source_snapshot'/path.name)
    fit_review = json.loads(fit.read_text())
    if pregrasp_index is None:
        assert fit_review['passed_local_pad_geometry']
    assert sha(fit.parent/'contract.json') == fit_review['contract_sha256']
    fit_contract = json.loads((fit.parent/'contract.json').read_text())
    assert sha(source/'rest_geometry.glb') == fit_contract['source_hashes'][str((source/'rest_geometry.glb').relative_to(ROOT))]
    support_path = ROOT/fit_contract['support_review']
    assert sha(support_path) == fit_contract['support_review_sha256']
    support = json.loads(support_path.read_text())
    assert support['passed']
    if pregrasp_index is None:
        candidate = fit_review['candidates'][candidate_index]
    else:
        if pregrasp_index < 0:
            raise ValueError('Negative pregrasp index')
        candidate = fit_review['nearest_candidates'][pregrasp_index]
        # A noncontact start is not an accepted static pinch. It must have
        # checked source geometry and inward finger motion; actual contact,
        # force, tool closure, slip and release are judged by this new run.
        required = ['no_tool_intersections', 'no_nonadjacent_self_intersections',
                    'no_support_obstacle_intersections', 'support_obstacle_clearance',
                    'support_clearance', 'source_joint_limits', 'opposed_closure_directions']
        if not all(candidate['checks'].get(k) is True for k in required):
            raise ValueError('Pregrasp lacks required source geometry and direction checks')
    initial_tool = np.asarray(support['tool_final_qpos'] if 'tool_final_qpos' in support else support['final_qpos'])
    world_from_source = pose(initial_tool[:3], initial_tool[3:7])
    world_from_source[:3, 3] -= world_from_source[:3, :3]@np.array([.13, 0, .00575])
    world_from_palm = world_from_source@np.asarray(candidate['source_tool_from_palm'])
    source_fk = fk(candidate['q'])
    wrist_pose = world_from_palm@np.linalg.inv(source_fk['right_palm_force_sensor'])@source_fk['right_wrist_yaw_link']

    robot = ET.parse(ROBOT/'simulation/robot.xml').getroot()
    attach_thumb(robot, output)
    attach_touch(robot, ROBOT, output)
    attach_distal(robot, output)
    hand = deepcopy(robot.find(".//body[@name='right_wrist_yaw_link']"))
    for node in hand.findall('joint'):
        hand.remove(node)
    hand.set('pos', numbers(wrist_pose[:3, 3]))
    quat = Rotation.from_matrix(wrist_pose[:3, :3]).as_quat()
    hand.set('quat', numbers(np.r_[quat[3], quat[:3]]))
    joints = {n.get('name') for n in hand.iter('joint')}
    bodies = {n.get('name') for n in hand.iter('body')}
    sites = {n.get('name') for n in hand.iter('site')}
    meshes = {n.get('mesh') for n in hand.iter('geom') if n.get('mesh')}
    # Retain explicit manufacturer-derived inertials. Only the tool computes
    # mass from its declared material and meshes.
    root = ET.Element('mujoco', model='Source Inspire free-tool contact diagnostic')
    ET.SubElement(root, 'compiler', angle='radian', autolimits='true', inertiafromgeom='auto', fusestatic='false')
    tool_xml = ET.parse(source/'tool.xml').getroot()
    option = deepcopy(tool_xml.find('option'))
    option.set('gravity', '0 0 -9.81')
    root.append(option)
    defaults = ET.SubElement(root, 'default')
    tool_defaults = ET.SubElement(defaults, 'default', {'class':'passive_tweezer'})
    for node in tool_xml.find('default'):
        tool_defaults.append(deepcopy(node))
    assets = ET.SubElement(root, 'asset')
    for node in robot.find('asset'):
        if node.get('name') in meshes:
            copied = deepcopy(node)
            if copied.get('file'):
                copied.set('file', str((ROBOT/copied.get('file')).resolve()))
            assets.append(copied)
    world = ET.SubElement(root, 'worldbody')
    world.append(hand)
    ET.SubElement(world, 'geom', name='support_plane', type='plane', size='.3 .3 .01',
                  rgba='.5 .52 .54 1', friction='.7 .005 .0001', solref='.001 1', solimp='.9999 .9999 .00001')
    ET.SubElement(world, 'light', pos='0 -.3 .5', dir='0 .2 -1')
    contact = ET.SubElement(root, 'contact')
    for node in robot.findall('contact/*'):
        if node.get('body1') in bodies and node.get('body2') in bodies:
            contact.append(deepcopy(node))
    # Anchoring the wrist changes its weld group to the world, for which
    # MuJoCo deliberately does not filter parent/child contact. Restore only
    # the pairs already filtered by the original whole robot. Tool/support
    # contact is never excluded. This preserves the source joint assemblies.
    original = mujoco.MjModel.from_xml_path(str(ROBOT/'simulation/robot.xml'))
    wrist_weld = int(original.body_weldid[original.body('right_wrist_yaw_link').id])
    restored_filters = []
    for a,b in itertools.combinations(sorted(bodies),2):
        wa,wb = [int(original.body_weldid[original.body(n).id]) for n in [a,b]]
        if wa == wb or wrist_weld not in [wa,wb]:
            continue
        child = wb if wa == wrist_weld else wa
        source_parent = int(original.body_weldid[original.body_parentid[child]])
        if source_parent == wrist_weld:
            ET.SubElement(contact,'exclude',body1=a,body2=b)
            restored_filters.append([a,b])
    (output/'source_parent_filter.json').write_text(json.dumps(dict(
        scope='Preserve original whole-robot parent filtering after a diagnostic wrist mount.',
        original_model_sha256=sha(ROBOT/'simulation/robot.xml'),pairs=restored_filters,
        tool_or_support_pairs_excluded=False,
        reference='https://mujoco.readthedocs.io/en/stable/computation/index.html#collision-detection'),indent=2)+'\n')
    equalities = ET.SubElement(root, 'equality')
    for node in robot.find('equality'):
        if node.get('joint1') in joints and node.get('joint2') in joints:
            equalities.append(deepcopy(node))
    actuator = ET.SubElement(root, 'actuator')
    for node in robot.find('actuator'):
        if node.get('joint') in joints:
            actuator.append(deepcopy(node))
    sensor = ET.SubElement(root, 'sensor')
    for node in robot.find('sensor'):
        if node.get('joint') in joints or node.get('site') in sites:
            sensor.append(deepcopy(node))
    ET.SubElement(root, 'visual')
    root.find('visual').append(ET.Element('global', offwidth='1280', offheight='720'))
    # The internal predictor has only the mounted hand. Its gravity calculation
    # receives measured encoders and velocities, not the plant's tool state.
    predictor = deepcopy(root)
    predictor.find('worldbody').remove(predictor.find("worldbody/geom[@name='support_plane']"))
    ET.SubElement(predictor.find('option'), 'flag', contact='disable')
    ET.indent(predictor)
    ET.ElementTree(predictor).write(output/'hand_predictor.xml', encoding='unicode')
    for node in tool_xml.find('asset'):
        copied = deepcopy(node)
        copied.set('file', str(source/'meshes'/node.get('file')))
        assets.append(copied)
    tool = deepcopy(tool_xml.find("worldbody/body[@name='tweezer']"))
    tool.set('childclass', 'passive_tweezer')
    tool.set('pos', numbers(initial_tool[:3]))
    tool.set('quat', numbers(initial_tool[3:7]))
    world.append(tool)
    tray_reference=None
    if 'tray_final_qpos' in support:
        support_contract=json.loads((support_path.parent/'contract.json').read_text())
        support_xml=support_path.parent/'support.xml'
        assert sha(support_xml)==support_contract['plant_sha256']
        for name,expected in support_contract['source_hashes'].items():assert sha(ROOT/name)==expected
        support_tree=ET.parse(support_xml).getroot()
        tray=deepcopy(support_tree.find(".//body[@name='carrier_tray']"))
        assert tray is not None and tray.find('freejoint') is not None
        tray_meshes={n.get('mesh') for n in tray.iter('geom')}
        for node in support_tree.find('asset'):
            if node.get('name') in tray_meshes:
                copied=deepcopy(node)
                assert Path(copied.get('file')).is_absolute()
                assets.append(copied)
        world.append(tray)
        tray_reference=mujoco.MjModel.from_xml_path(str(support_xml))
    ET.indent(root)
    ET.ElementTree(root).write(output/'contact.xml', encoding='unicode')
    model = mujoco.MjModel.from_xml_path(str(output/'contact.xml'))
    data = mujoco.MjData(model)
    tool_reference = mujoco.MjModel.from_xml_path(str(source/'tool.xml'))
    for joint in range(tool_reference.njnt):
        original = tool_reference.joint(joint)
        width = 7 if tool_reference.jnt_type[joint] == mujoco.mjtJoint.mjJNT_FREE else 1
        start = int(tool_reference.jnt_qposadr[joint])
        data.joint(original.name).qpos[:] = initial_tool[start:start+width]
    for name, value in candidate['q'].items():
        data.joint(name).qpos[0] = value
    if tray_reference is not None:
        data.joint('tray_free').qpos[:]=support['tray_final_qpos']
        preservation={}
        for node in tray.iter('geom'):
            name=node.get('name');before=tray_reference.geom(name).id;after=model.geom(name).id
            preservation[name]={attr:bool(np.array_equal(getattr(tray_reference,attr)[before],getattr(model,attr)[after]))
                for attr in ['geom_priority','geom_condim','geom_friction','geom_solref','geom_solimp','geom_contype','geom_conaffinity']}
        (output/'tray_parameter_preservation.json').write_text(json.dumps(preservation,indent=2)+'\n')
        assert all(all(v.values()) for v in preservation.values()),'Tray contact parameters changed during hand integration'
    for i in range(model.neq):
        a,b = model.eq_obj1id[i],model.eq_obj2id[i]
        data.qpos[model.jnt_qposadr[a]] = model.eq_data[i,0]+model.eq_data[i,1]*data.qpos[model.jnt_qposadr[b]]
    mujoco.mj_forward(model, data)
    assert model.nu == 6 and model.neq == 6
    actual_palm = pose(data.body('right_palm_force_sensor').xpos, data.body('right_palm_force_sensor').xquat)
    assert np.max(abs(actual_palm-world_from_palm)) < 1e-8
    return model, data, candidate, support_path


class HandController:
    """Encoder PD with tactile or encoder-derived load feedback."""
    def __init__(self, predictor_path, initial_q, feedback='tactile', detect_grip_loss=False):
        self.m = mujoco.MjModel.from_xml_path(str(predictor_path))
        self.d = mujoco.MjData(self.m)
        self.names = [self.m.joint(i).name for i in range(self.m.njnt)]
        self.qa = self.m.jnt_qposadr
        self.va = self.m.jnt_dofadr
        self.driver_names = [self.m.joint(j).name for j in self.m.actuator_trnid[:,0]]
        self.driver_joints = self.m.actuator_trnid[:,0]
        self.driver_qa = self.m.jnt_qposadr[self.driver_joints]
        self.driver_va = self.m.jnt_dofadr[self.driver_joints]
        self.initial = np.array([initial_q[n] for n in self.driver_names])
        self.command_lower = np.maximum(self.initial-.02, self.m.jnt_range[self.driver_joints, 0])
        self.command_upper = np.minimum(self.initial+.08, self.m.jnt_range[self.driver_joints, 1])
        if np.any(self.initial < self.command_lower) or np.any(self.initial > self.command_upper):
            raise ValueError('Initial hand drivers exceed their source joint ranges')
        self.command = self.initial.copy()
        self.coupling = np.zeros((self.m.nv, self.m.nu))
        self.coupling[self.driver_va, np.arange(self.m.nu)] = 1
        for i in range(self.m.neq):
            a,b = self.m.eq_obj1id[i],self.m.eq_obj2id[i]
            self.coupling[self.m.jnt_dofadr[a]] = self.m.eq_data[i,1]*self.coupling[self.m.jnt_dofadr[b]]
        self.closed = None
        self.filtered = np.zeros(2)
        self.targets = [(self.driver_names.index('right_index_1_joint'),1),
                        (self.driver_names.index('right_thumb_2_joint'),6)]
        if feedback not in {'tactile','encoder_load'}:
            raise ValueError('Unknown hand feedback mode')
        self.feedback=feedback
        self.previous_velocity=None
        self.previous_torque=np.zeros(self.m.nu)
        self.filtered_effort=np.zeros(self.m.nu)
        self.bilateral_since=None
        self.gripping=False
        self.detect_grip_loss=detect_grip_loss
        self.lost_since=None
        self.safe_release_started=None
        self.abort_reason=None

    def update(self, obs):
        if set(obs) != {'time_s','joint_position','joint_velocity','touch_n'}:
            raise ValueError('Non-sensor field in hand controller input')
        q,v,touch = map(np.asarray, [obs['joint_position'],obs['joint_velocity'],obs['touch_n']])
        if q.shape != (len(self.names),) or v.shape != q.shape or touch.shape != (7,):
            raise ValueError('Malformed hand observation')
        if not np.isfinite(np.r_[q,v,touch]).all() or np.any(touch<0):
            raise ValueError('Nonfinite hand observation')
        self.d.qpos[self.qa] = q
        self.d.qvel[self.va] = v
        mujoco.mj_forward(self.m,self.d)
        t = float(obs['time_s'])
        gravity = self.coupling.T@(self.d.qfrc_bias-self.d.qfrc_passive)
        if self.previous_velocity is not None:
            mass=np.empty((self.m.nv,self.m.nv));mujoco.mj_fullM(self.m,self.d,mass)
            acceleration=(self.d.qvel-self.previous_velocity)/.001
            predicted=self.coupling.T@(mass@acceleration)+gravity
            residual=self.previous_torque-predicted
            self.filtered_effort+=(1-np.exp(-.001/.03))*(residual-self.filtered_effort)
        self.previous_velocity=self.d.qvel.copy()
        self.filtered += (1-np.exp(-.001/.03))*(touch[[1,6]]-self.filtered)
        if np.max(touch)>4.:
            raise RuntimeError('Tactile overload above the preregistered 4 N bound')
        efforts=np.array([self.filtered_effort[driver] for driver,_ in self.targets])
        if self.detect_grip_loss and self.feedback=='encoder_load' and self.gripping and 1. <= t < 7.:
            if np.min(efforts)<.003:
                if self.lost_since is None:self.lost_since=t
                if t-self.lost_since>=.15 and self.safe_release_started is None:
                    self.safe_release_started=t
                    self.closed=self.command.copy()
                    self.abort_reason='Observed loss of previously established opposing finger load'
            else:self.lost_since=None
        if 1. <= t < 7. and self.safe_release_started is None:
            if self.feedback=='encoder_load':
                if np.max(abs(efforts))>.12:
                    raise RuntimeError('Estimated finger effort exceeds the preregistered 0.12 Nm bound')
                if np.min(efforts)>.005:
                    if self.bilateral_since is None:self.bilateral_since=t
                    if t-self.bilateral_since>=.05:self.gripping=True
                else:self.bilateral_since=None
            for i,(driver,_) in enumerate(self.targets):
                if self.feedback=='tactile':
                    increment = np.clip(1.-self.filtered[i],-.5,1.)*.015*.001
                else:
                    speed=[.004,.014][i]
                    if self.gripping:
                        rate=np.clip([.4,1.2][i]*(.04-efforts[i]),-speed,speed)
                    elif efforts[i]>.005:
                        # Keep first contact light until the opposite finger
                        # arrives; equal angular rates move unequal surfaces.
                        rate=np.clip([.4,1.2][i]*(.004-efforts[i]),-speed,0.)
                    else:
                        rate=speed
                    increment=rate*.001
                self.command[driver] = np.clip(self.command[driver]+increment,
                                               self.command_lower[driver],self.command_upper[driver])
        elif t >= 7. or self.safe_release_started is not None:
            if self.closed is None:
                self.closed = self.command.copy()
            release_start=7. if self.safe_release_started is None else self.safe_release_started
            u = np.clip((t-release_start)/2.,0,1)
            s = u*u*(3-2*u)
            self.command = self.closed+s*(self.initial-self.closed)
        torque = gravity+3.*(self.command-self.d.qpos[self.driver_qa])-.08*self.d.qvel[self.driver_va]
        torque = np.clip(torque,self.m.actuator_ctrlrange[:,0],self.m.actuator_ctrlrange[:,1])
        self.previous_torque=torque.copy()
        return dict(torque=torque, requested_joint_position=self.command.copy(), filtered_touch_n=self.filtered.copy(),
                    estimated_motor_load_nm=self.filtered_effort.copy())


def run(source, fit, output, candidate_index=0, feedback='tactile', pregrasp_index=None, detect_grip_loss=False):
    output = Path(output).resolve()
    model,data,candidate,support_path = build(source,fit,output,candidate_index,pregrasp_index)
    controller = HandController(output/'hand_predictor.xml',candidate['q'],feedback,detect_grip_loss)
    dt = float(model.opt.timestep)
    stride = round(.001/dt)
    assert abs(stride*dt-.001) < 1e-12
    initial = data.qpos.copy()
    tool = model.joint('tweezer_free').qposadr[0]
    contract = dict(scope=__doc__, duration_s=11., control_period_s=.001,
        integrator='discrete', timestep_s=dt, tactile_target_n=1., tactile_abort_n=4.,
        hand_gains=dict(kp_nm_rad=3.,kd_nms_rad=.08,maximum_closure_rad=.08),
        checks=dict(minimum_bilateral_contact_duration_s=1.,maximum_hand_tool_penetration_m=.00025,
                    maximum_unexpected_penetration_m=.00002,maximum_tool_support_penetration_m=.00025,
                    maximum_horizontal_tool_motion_m=.005,maximum_tool_translation_m=.005,minimum_tip_closure_m=.001,
                    maximum_released_tip_gap_error_m=.0001,maximum_source_joint_limit_excess_rad=.001),
        candidate_index=candidate_index,fit_review_sha256=sha(fit),support_review_sha256=sha(support_path),
        source_model_sha256=sha(Path(source)/'tool.xml'),plant_sha256=sha(output/'contact.xml'),
        controller_model_sha256=sha(output/'hand_predictor.xml'),
        script_sha256=sha(output/'source_snapshot'/Path(__file__).name),
        parent_filter_sha256=sha(output/'source_parent_filter.json'),
        initial_qpos=initial.tolist(),controller_fields=['time_s','joint_position','joint_velocity','touch_n'],
        controller_os_isolated=False,qualified_robot_grasp=False,qualified_paper_branch=False)
    contract['grip_loss_response']=dict(enabled=detect_grip_loss,observation='Encoder-derived motor loads only',
        maximum_remaining_opposing_load_nm=.003,persistence_s=.15,release_duration_s=2.,
        action='Stop advancing the fingers, return to the initial open posture, retain a failed-grasp verdict',
        inferred_control_thresholds=True)
    contract['closure_attribution']='Tip closure must occur while both allowed fingers exert more than 0.2 N; support impact alone never counts'
    contract['initial_pose'] = dict(kind='noncontact_pregrasp' if pregrasp_index is not None else 'accepted_local_pad_geometry',
        pregrasp_index=pregrasp_index, static_pinch_acceptance_claimed=pregrasp_index is None,
        source_candidate_checks=candidate.get('checks'),
        rationale='Start clear of the tool and let the sensor-driven closure establish contact; all dynamic pass thresholds are unchanged')
    contract['requested_driver_position_limits_rad'] = dict(
        names=controller.driver_names, lower=controller.command_lower.tolist(),
        upper=controller.command_upper.tolist(), basis='Source driver limits intersected with bounded closure excursion')
    contract['free_support_tray_present']=bool((output/'tray_parameter_preservation.json').exists())
    if contract['free_support_tray_present']:
        contract['tray_parameter_preservation_sha256']=sha(output/'tray_parameter_preservation.json')
    contract.update(feedback_mode=feedback,allowed_contact_bodies=[
        'right_index_force_sensor_2','right_index_force_sensor_3','right_thumb_force_sensor_3','right_thumb_force_sensor_4'])
    if feedback=='encoder_load':
        contract['allowed_contact_bodies']+=['right_index_2','right_thumb_4']
        contract['encoder_load_control']=dict(
            observation='Encoder positions/velocities and previous commanded motor torques only; no simulator contact force input',
            estimate='Previous motor torque minus robot-only inverse-dynamics prediction with finite-difference acceleration',
            inferred_filter_time_s=.03,contact_effort_nm=.005,first_contact_target_nm=.004,
            hold_effort_nm=.04,maximum_effort_nm=.12,maximum_joint_rates_rad_s=[.004,.014],
            policy='Establish both contacts before increasing the load; release to the original posture',
            hardware_force_or_current_calibration_claimed=False,
            contact_choice='Distal index and thumb phalanges adjacent to the tactile pads; the retained failed trial contacted these surfaces before the pads',
            manufacturer_context='Retained RH56DFTP manual sections 2.6.12 and 2.6.16 describe non-tip grasp lever-arm dependence and per-driver force feedback; this observer does not claim to emulate those calibrated registers')
        contract['checks']['maximum_allowed_finger_normal_force_n']=4.
    if candidate.get('middle_brace'):
        brace=candidate['middle_brace']
        assert brace['body'].startswith('right_middle_')
        contract['allowed_contact_bodies'].append(brace['body'])
        contract['middle_finger_support']=dict(source_contact=brace,
            driver_angle_rad=candidate['q']['right_middle_1_joint'],
            actuation='The existing source middle-finger motor holds its declared initial angle; no weld or fixture',
            minimum_engaged_duration_s=1.,minimum_normal_load_n=.05)
    contract['checks']['maximum_unexpected_hand_tool_normal_force_n']=.05
    assert model.opt.integrator == mujoco.mjtIntegrator.mjINT_DISCRETE
    (output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    names = controller.names
    def observations():
        return dict(time_s=float(data.time),joint_position=np.array([data.joint(n).qpos[0] for n in names]),
                    joint_velocity=np.array([data.joint(n).qvel[0] for n in names]),touch_n=read_touch(data))
    tool_body = model.body('tweezer').id
    tool_bodies = {tool_body}
    for b in range(model.nbody):
        if model.body_parentid[b] in tool_bodies:tool_bodies.add(b)
    support_geom = model.geom('support_plane').id
    support_geoms={support_geom}
    if contract['free_support_tray_present']:
        tray_body=model.body('carrier_tray').id
        support_geoms.update(g for g in range(model.ngeom) if model.geom_bodyid[g]==tray_body)
    pad_names = set(contract['allowed_contact_bodies'])
    allowed_hand_bodies = {model.body(n).id for n in pad_names}
    tips = {}
    for label, sign in [('negative',-1),('positive',1)]:
        body_id = max((b for b in tool_bodies if model.body(b).name.startswith(label+'_beam_')),
                      key=lambda b:model.body(b).name)
        # Nominal endpoint in the tool root frame, retained as a material point.
        root_pose = pose(data.body('tweezer').xpos,data.body('tweezer').xquat)
        point = root_pose[:3,:3]@np.array([-.130,sign*.004,0.])+root_pose[:3,3]
        tips[label]=(body_id,data.xmat[body_id].reshape(3,3).T@(point-data.xpos[body_id]))
    records=[]; sensor_rows=[]; commands=[]; touch_rows=[]; gaps=[]
    max_contact=0.;max_support=0.;max_xy=0.;max_translation=0.;joint_excess=0.;bilateral=0.;unintended=[];failure=None
    minimum_loaded_gap=float('inf');loaded_gap_samples=[]
    force_peak=0.;unexpected_force_peak=0.;middle_engaged=0.;middle_force_peak=0.
    started=time.monotonic()
    def save_state():
        records.append((float(data.time),data.qpos.copy(),data.qvel.copy(),data.ctrl.copy(),data.qacc_warmstart.copy()))
    initial_contacts=[]
    for c in data.contact:
        bodies=[int(model.geom_bodyid[g]) for g in c.geom]
        touches_hand=any(model.body(b).name.startswith('right_') for b in bodies)
        passive_support=not touches_hand and any(int(g) in support_geoms for g in c.geom)
        tolerance=.00025 if passive_support else .00002
        if c.dist < -tolerance:
            initial_contacts.append(dict(parts=[model.geom(int(g)).name for g in c.geom],distance_m=float(c.dist)))
    (output/'initial_contacts.json').write_text(json.dumps(initial_contacts,indent=2)+'\n')
    if initial_contacts:failure='Initial source-hand/tool geometry has unexpected physical-model penetration'
    for step in range(round(11./dt)) if failure is None else []:
        if step%stride == 0:
            obs=observations();sensor_rows.append(obs)
            try:
                command=controller.update(obs);data.ctrl[:]=command['torque'];commands.append(command)
            except Exception as exc:
                failure=str(exc);break
        save_state()
        t=float(data.time)
        mujoco.mj_step(model,data)
        force_by_finger={'index':0.,'thumb':0.,'middle':0.}
        for index,c in enumerate(data.contact):
            pair=list(map(int,c.geom));bodies=[int(model.geom_bodyid[g]) for g in pair]
            tool_side=[b in tool_bodies for b in bodies]
            if any(tool_side) and any(g in support_geoms for g in pair):
                max_support=max(max_support,-float(c.dist))
            elif sum(tool_side)==1 and any(b in allowed_hand_bodies for b in bodies):
                max_contact=max(max_contact,-float(c.dist))
                pad=next(model.body(b).name for b in bodies if b in allowed_hand_bodies)
                wrench=np.zeros(6);mujoco.mj_contactForce(model,data,index,wrench)
                finger='index' if 'index' in pad else 'middle' if 'middle' in pad else 'thumb'
                force_by_finger[finger]+=max(0.,float(wrench[0]))
            else:
                unexpected_force=0.
                if sum(tool_side)==1 and any(model.body(b).name.startswith('right_') for b in bodies):
                    wrench=np.zeros(6);mujoco.mj_contactForce(model,data,index,wrench)
                    unexpected_force=max(0.,float(wrench[0]))
                    unexpected_force_peak=max(unexpected_force_peak,unexpected_force)
                if (c.dist < -.00002 or unexpected_force>.05) and len(unintended)<30:
                    unintended.append(dict(time_s=t,parts=[model.geom(g).name for g in pair],distance_m=float(c.dist),normal_force_n=unexpected_force))
        force_peak=max(force_peak,max(force_by_finger.values()))
        opposing_load=min(force_by_finger['index'],force_by_finger['thumb'])
        if opposing_load>.2:bilateral+=dt
        if force_by_finger['middle']>.05:middle_engaged+=dt
        middle_force_peak=max(middle_force_peak,force_by_finger['middle'])
        max_xy=max(max_xy,float(np.linalg.norm(data.qpos[tool:tool+2]-initial[tool:tool+2])))
        max_translation=max(max_translation,float(np.linalg.norm(data.qpos[tool:tool+3]-initial[tool:tool+3])))
        for j in range(model.njnt):
            if model.jnt_limited[j]:
                value=float(data.qpos[model.jnt_qposadr[j]])
                joint_excess=max(joint_excess,model.jnt_range[j,0]-value,value-model.jnt_range[j,1])
        points={k:data.xpos[b]+data.xmat[b].reshape(3,3)@p for k,(b,p) in tips.items()}
        gap=float(np.linalg.norm(points['positive']-points['negative']))
        if opposing_load>.2:
            minimum_loaded_gap=min(minimum_loaded_gap,gap)
            if step%stride==0:loaded_gap_samples.append([t,gap,force_by_finger['index'],force_by_finger['thumb']])
        if step%stride==0:
            # mj_step's kinematics, contact and sensor arrays describe the
            # pre-integration state; qpos/time have already advanced.
            gaps.append([t,gap]);touch_rows.append([t,*read_touch(data)])
        if np.any(data.warning.number):failure='MuJoCo numerical warning';break
        if step%10000==0:print('source_hand_contact',round(data.time,4), '/',11.,flush=True)
    save_state()
    trace={key:np.array([r[i] for r in records]) for i,key in enumerate(['time','qpos','qvel','ctrl','qacc_warmstart'])}
    np.savez_compressed(output/'trace.npz',**trace)
    np.savez_compressed(output/'sensors.npz',time=np.array([r['time_s'] for r in sensor_rows]),
        joint_position=np.array([r['joint_position'] for r in sensor_rows]),
        joint_velocity=np.array([r['joint_velocity'] for r in sensor_rows]),
        touch_n=np.array([r['touch_n'] for r in sensor_rows]))
    np.savez_compressed(output/'commands.npz',**{key:np.array([r[key] for r in commands])
        for key in ['torque','requested_joint_position','filtered_touch_n','estimated_motor_load_nm']})
    replay=mujoco.MjData(model);replay.qpos[:]=initial;replay.qvel[:]=trace['qvel'][0]
    mujoco.mj_forward(model,replay);replay.qacc_warmstart[:]=trace['qacc_warmstart'][0]
    q_error=v_error=0.
    for index in range(len(records)-1):
        replay.ctrl[:]=trace['ctrl'][index];mujoco.mj_step(model,replay)
        q_error=max(q_error,float(np.max(abs(replay.qpos-trace['qpos'][index+1]))))
        v_error=max(v_error,float(np.max(abs(replay.qvel-trace['qvel'][index+1]))))
    repeated=HandController(output/'hand_predictor.xml',candidate['q'],feedback,detect_grip_loss);torque_error=0.
    for obs,command in zip(sensor_rows,commands):
        result=repeated.update(obs)
        torque_error=max(torque_error,float(np.max(abs(result['torque']-command['torque']))))
    released=[gap for t,gap in gaps if t>10.]
    checks=dict(attempt_completed=failure is None and data.time>=11.-1e-7,
        no_controller_abort=controller.abort_reason is None,
        controller_abort_replayed=controller.abort_reason==repeated.abort_reason and controller.safe_release_started==repeated.safe_release_started,
        initial_geometry_accepted=not initial_contacts,no_numerical_warnings=not np.any(data.warning.number),
        finite_trajectory=all(np.isfinite(v).all() for v in trace.values()),
        exact_physics_replay=len(records)>1 and q_error<1e-9 and v_error<1e-8,
        complete_controller_replay=len(commands)==len(sensor_rows) and len(commands)==11000 and torque_error<1e-10,
        free_tool_and_source_mimics_only=model.neq==6 and model.nu==6,
        no_external_forces=not np.any(data.xfrc_applied) and not np.any(data.qfrc_applied),
        bilateral_contact=bilateral>=1.,intended_penetration=max_contact<=.00025,
        tool_support_penetration=max_support<=.00025,no_unintended_penetration=not unintended,
        no_unexpected_hand_tool_load=unexpected_force_peak<=.05,
        bounded_tool_displacement=max_xy<=.005,bounded_tool_translation=max_translation<=.005,source_joint_limits=joint_excess<=.001,
        measurable_tip_closure=minimum_loaded_gap<=.007,
        released_gap_recovers=bool(released) and max(abs(g-.008) for g in released)<.0001)
    if feedback=='encoder_load':checks['bounded_finger_normal_force']=force_peak<=4.
    if candidate.get('middle_brace'):checks['middle_support_engaged']=middle_engaged>=1.
    result=dict(passed=all(checks.values()),checks={k:bool(v) for k,v in checks.items()},failure=failure,
        scope=__doc__,duration_s=float(data.time),seconds=time.monotonic()-started,
        bilateral_contact_s=bilateral,maximum_hand_tool_penetration_m=max_contact,
        maximum_tool_support_penetration_m=max_support,maximum_horizontal_tool_motion_m=max_xy,
        maximum_tool_translation_m=max_translation,
        minimum_bilaterally_loaded_tip_gap_m=None if not np.isfinite(minimum_loaded_gap) else minimum_loaded_gap,
        controller_abort_reason=controller.abort_reason,controller_safe_release_started_s=controller.safe_release_started,
        maximum_allowed_finger_normal_force_n=force_peak,maximum_unexpected_hand_tool_normal_force_n=unexpected_force_peak,
        middle_support_engaged_s=middle_engaged,maximum_middle_support_normal_force_n=middle_force_peak,
        maximum_source_joint_limit_excess_rad=float(joint_excess),unintended_contacts=unintended,
        maximum_replay_q_error=q_error,maximum_replay_v_error=v_error,maximum_motor_replay_error=torque_error,
        gap_samples=gaps,touch_samples=touch_rows,loaded_gap_samples=loaded_gap_samples,trace_sha256=sha(output/'trace.npz'),
        contract_sha256=sha(output/'contract.json'),qualified_robot_grasp=False,qualified_paper_branch=False)
    (output/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['gap_samples','touch_samples','loaded_gap_samples']}),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('fit');p.add_argument('output')
    p.add_argument('--candidate-index',type=int,default=0)
    p.add_argument('--pregrasp-index',type=int)
    p.add_argument('--detect-grip-loss',action='store_true')
    p.add_argument('--feedback',choices=['tactile','encoder_load'],default='tactile');a=p.parse_args()
    if not run(a.source,a.fit,a.output,a.candidate_index,a.feedback,a.pregrasp_index,a.detect_grip_loss)['passed']:raise SystemExit(1)
