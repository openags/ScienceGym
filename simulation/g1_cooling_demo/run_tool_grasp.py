"""Run an isolated full-G1 tool pickup attempt in the existing laboratory.

Starts at an explicitly authored posture. An observed-approach station enables
native cameras and a separate visual actor. Neither execution mode grants
task-branch or repeated-reliability qualification by itself.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pickle
import shutil
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from hand_touch import read as read_touch
from isolation import prepare
from observations import robot_joints

HERE = Path(__file__).resolve().parent


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def plain(value):
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, np.generic): return value.item()
    raise TypeError(type(value).__name__)


def run(station, output, duration, close_timeout=6., thumb_force=.6, lift_force=.5, approach_feedforward=False, carry_distance=None, carry_thumb_force=None, prepare_only=False, carry_load_abort=None, carry_preload_before_lift=False, carry_command_excursion=None, carry_finger_load_compensation=False, carry_body_joint_damper=False, carry_prelift_dwell=None, carry_body_withdrawal=False, carry_support_inset=0., carry_proximal_preshape=0., contact_cone=None, contact_impratio=None, release_extra_opening=.04, release_driver_openings=None, release_load_feedback=False, observe_optical_coupon=False, release_clearance_height=0., release_preserve_posture=False, tool_lift_height=.03, register_optical_map=False, return_base_after_release=False, grip_force_deadband=0., loaded_hand_damping_scale=1., hand_contact_impedance=None, tool_squeeze_force=None, grasp_proximal_preshape=0.):
    station, output = Path(station).resolve(), Path(output).resolve()
    review = json.loads((station/'review.json').read_text())
    assert review['passed_initial_scene_checks']
    contract = json.loads((station/'contract.json').read_text())
    dex3 = contract.get('hand_kind') == 'unitree_three_finger'
    if hand_contact_impedance is not None and (not dex3 or not .95<=hand_contact_impedance<=.9999):
        raise ValueError('Fingertip/tool compliance trial requires Dex3 and impedance 0.95 to 0.9999')
    if not abs(grasp_proximal_preshape)<=.08 or (grasp_proximal_preshape and (not dex3 or carry_distance is not None)):
        raise ValueError('Supported grasp preshape requires a non-carry Dex3 task and at most 0.08 rad')
    if tool_squeeze_force is not None and (not dex3 or carry_distance is not None or not thumb_force<tool_squeeze_force<4.):
        raise ValueError('Free-tool stroke requires Dex3, no carrying, and a larger force target below 4 N')
    visual = bool(contract.get('observed_approach',False))
    if visual: assert dex3
    if observe_optical_coupon and (not visual or not contract.get('optical_scene_binding')):
        raise ValueError('Coupon observation requires the bound visual optical station')
    if return_base_after_release and carry_distance is None:
        raise ValueError('Base return after release requires a carrying route')
    if register_optical_map and not observe_optical_coupon:
        raise ValueError('Static-map registration requires optical coupon observation')
    if approach_feedforward and not visual:raise ValueError('Approach feedforward requires a visual approach station')
    if carry_distance is not None and (not visual or not .02<=carry_distance<=.30):
        raise ValueError('Loaded stepping requires a visual station and 0.02 to 0.30 m distance')
    if carry_thumb_force is not None and (carry_distance is None or not thumb_force<=carry_thumb_force<4.):
        raise ValueError('Carrying force must be at least the pickup force and below the unchanged 4 N bound')
    if carry_load_abort is not None and (carry_distance is None or not .15<=carry_load_abort<=.7):
        raise ValueError('Carrying load observer bound must be 0.15 to 0.7 Nm; source motor bounds remain unchanged')
    if carry_preload_before_lift and carry_distance is None:
        raise ValueError('Pre-lift carrying force requires a loaded route')
    if carry_command_excursion is not None and (carry_distance is None or not .15<=carry_command_excursion<=.30):
        raise ValueError('Carrying driver reference excursion must be 0.15 to 0.30 rad, inside source limits')
    if (carry_finger_load_compensation or carry_body_joint_damper or carry_body_withdrawal) and carry_distance is None:
        raise ValueError('Carrying feedback options require a loaded route')
    if carry_prelift_dwell is not None and (not carry_preload_before_lift or not .5<=carry_prelift_dwell<=2.):
        raise ValueError('Carrying pre-lift proxy dwell requires preloading and 0.5 to 2 seconds')
    if not 0.<=carry_support_inset<=.01 or (carry_support_inset and carry_distance is None):
        raise ValueError('Support inset requires a carrying route and 0 to 10 mm')
    if not abs(carry_proximal_preshape)<=.08 or (carry_proximal_preshape and not carry_preload_before_lift):
        raise ValueError('Finger preshape requires supported preload and magnitude at most 0.08 rad')
    if contact_cone not in (None,'elliptic','pyramidal'):
        raise ValueError('Unknown contact cone')
    if contact_impratio is not None and (contact_cone!='elliptic' or not 1.<=contact_impratio<=10.):
        raise ValueError('Contact impedance ratio experiment requires elliptic cones and ratio 1 to 10')
    if not 0. <= release_extra_opening <= .08:
        raise ValueError('Release opening must remain within the existing 0 to 0.08 rad controller range')
    if release_driver_openings is not None:
        release_driver_openings=np.asarray(release_driver_openings,dtype=float)
        if (not dex3 or release_driver_openings.shape!=(3,) or
                not np.isfinite(release_driver_openings).all() or
                np.any(release_driver_openings<0) or np.any(release_driver_openings>.08)):
            raise ValueError('Dex3 release requires three driver openings, each within 0 to 0.08 rad')
    if not .02<=tool_lift_height<=.06 or (tool_lift_height!=.03 and not dex3):
        raise ValueError('Requested Dex3 tool lift must be between 20 and 60 mm')
    if not 0<=grip_force_deadband<=.1 or (grip_force_deadband and not dex3):
        raise ValueError('Dex3 force-feedback deadband must be 0 to 0.1 N')
    if not 1<=loaded_hand_damping_scale<=2 or (loaded_hand_damping_scale!=1. and not dex3):
        raise ValueError('Loaded Dex3 hand damping scale must be 1 to 2')
    if dex3: assert 0 < lift_force < thumb_force < 4.
    if release_load_feedback and not dex3:
        raise ValueError('Release motor-load feedback is implemented only for the Dex3 actor')
    if release_preserve_posture and not dex3:
        raise ValueError('Preserving release posture requires the Dex3 actor')
    if not 0<=release_clearance_height<=.004 or (release_clearance_height and not dex3):
        raise ValueError('Dex3 release clearance height must be 0 to 4 mm')
    actor_module = 'dex3_tool_actor' if dex3 else 'tool_grasp_actor'
    if visual: actor_module='visual_tool_actor'
    if carry_distance is not None:actor_module='carry_tool_actor'
    assert sha(station/'contract.json') == review['contract_sha256']
    assert sha(station/'world.xml') == contract['plant_sha256']
    assert sha(station/'robot_predictor.xml') == contract['predictor_sha256']
    inputs = json.loads((station/'model_inputs.json').read_text())
    assert sha(station/'model_inputs.json') == contract['inputs_sha256']
    for name, digest in inputs.items(): assert sha(name) == digest
    output.mkdir(parents=True, exist_ok=False)
    snapshot = output/'source_snapshot'; snapshot.mkdir()
    extra_modules=[actor_module+'.py','conic_balance.py']
    if visual:extra_modules.extend(['dex3_tool_actor.py','tool_observation.py','tool_pose.py','tool_approach_planning.py',
        'ftir_hand.py','joint_rrt.py','robot_source_meshes.py','source_proximity.py','tool_cameras.py','sensor_rendering.py'])
    if carry_distance is not None:extra_modules.extend(['visual_tool_actor.py','quasistatic_walking.py'])
    if observe_optical_coupon:extra_modules.append('optical_coupon_observation.py')
    if register_optical_map:extra_modules.append('map_localization.py')
    plugins = contract.get('collision_plugins', [])
    plant_modules = ['frozen_collision_plugins.py','process_tool_grasp_plugins.py',
                     'render_tool_grasp.py','verify_dex3_limits.py'] if plugins else []
    if hand_contact_impedance is not None:plant_modules.append('hand_tool_contact_compliance.py')
    for name in sorted(set(['run_tool_grasp.py','verify_tool_grasp.py','balance.py','observations.py','hand_touch.py','isolation.py','isolation_probe.py',*extra_modules,*plant_modules])):
        shutil.copyfile(HERE/name, snapshot/name)
    if plugins:
        source_urdf = HERE/'analysis/g1_dex3_comparison_01/g1_29dof_with_hand_rev_1_0.urdf'
        shutil.copyfile(source_urdf, snapshot/source_urdf.name)
    for name in ['world.xml', 'model_inputs.json']:
        shutil.copyfile(station/name, output/name)
    solver_revision=None
    if contact_cone is not None:
        xml=ET.parse(output/'world.xml');option=xml.getroot().find('option')
        before=dict(option.attrib)
        option.set('cone',contact_cone)
        if contact_impratio is not None:option.set('impratio',str(contact_impratio))
        xml.write(output/'world.xml',encoding='unicode')
        solver_revision=dict(source_model_sha256=contract['plant_sha256'],
            source_option_attributes=before,selected_option_attributes=dict(option.attrib),
            documentation='https://mujoco.readthedocs.io/en/stable/modeling.html#preventing-slip',
            purpose='Closed-loop contact-model sensitivity trial; friction, geometry, mass, controller and acceptance limits are retained',
            qualification_transfer_allowed=False)
    shutil.copyfile(HERE/'runs/ftir_approach_11/laboratory_import.json', output/'laboratory_import.json')
    (output/'controller_model').mkdir()
    shutil.copyfile(station/'robot_predictor.xml', output/'controller_model/world.xml')
    if plugins:
        from frozen_collision_plugins import load, require_stateless
        load(plugins, sha(snapshot/'frozen_collision_plugins.py'))
    compliance_revision=None
    if hand_contact_impedance is not None:
        from hand_tool_contact_compliance import bind
        compliance_revision=bind(output/'world.xml',[r['body'] for r in contract['robot_contact_features']],hand_contact_impedance)
    model = mujoco.MjModel.from_xml_path(str(output/'world.xml')); data = mujoco.MjData(model)
    if plugins: require_stateless(model)
    data.qpos[:] = contract['initial_qpos']; data.qvel[:] = contract['initial_qvel']
    mujoco.mj_forward(model, data)
    robot = mujoco.MjModel.from_xml_path(str(output/'controller_model/world.xml'))
    rd = mujoco.MjData(robot)
    for j in range(robot.njnt): rd.joint(robot.joint(j).name).qpos[:] = data.joint(robot.joint(j).name).qpos
    assert model.nu == robot.nu == (43 if dex3 else 41)
    prior_dir = output/'policy_source'; prior_dir.mkdir()
    prior_path = prior_dir/'tool_prior.json'
    prior = dict(initial_robot_qpos=rd.qpos.tolist(), close_timeout_s=close_timeout,
        scope='Authored robot initial posture and map origin only; no tool pose or plant object state',
        vision_and_approach_qualified=False)
    if dex3:
        prior.update({k: contract[k] for k in ['robot_contact_features','closing_drivers','closing_signs']})
        prior['hold_force_proxy_n']=[thumb_force,thumb_force/2,thumb_force/2]
        prior['lift_force_proxy_threshold_n']=[lift_force,lift_force/2,lift_force/2]
        prior['release_extra_opening_rad']=release_extra_opening
        if release_driver_openings is not None:
            prior['release_driver_openings_rad']=release_driver_openings.tolist()
        if release_load_feedback:
            prior['release_load_feedback']=True
        if release_preserve_posture:
            prior['release_preserve_posture']=True
        if release_clearance_height:
            prior['release_clearance_height_m']=release_clearance_height
        prior['tool_lift_height_m']=tool_lift_height
        if grip_force_deadband:prior['grip_force_deadband_n']=grip_force_deadband
        if loaded_hand_damping_scale!=1.:prior['loaded_hand_damping_scale']=loaded_hand_damping_scale
        if tool_squeeze_force is not None:
            prior['tool_squeeze_force_proxy_n']=[tool_squeeze_force,tool_squeeze_force/2,tool_squeeze_force/2]
        if grasp_proximal_preshape:
            prior['grasp_proximal_preshape_rad']=grasp_proximal_preshape
        prior['post_release_withdrawal_m']=.02
        prior['scope'] += '; source material points on the robot hand, not object/contact observations'
    shapes=[]
    if visual:
        shape_dir=output/'object_shape_source';shape_dir.mkdir()
        shape=shape_dir/'tool_shape.glb'
        shutil.copyfile(HERE.parents[1]/'assets/idealtek_aa_sa_t6_v1/revisions/passive_07/rest_geometry.glb',shape)
        shapes=[shape]
        prior.update(grasp_geometry=contract['grasp_geometry'],tool_shape_sha256=sha(shape),appearance_threshold_uint8=24.,
            scope='Authored initial robot posture, public architecture and unposed tool/grasp geometry; no tool placement or arm path')
        if approach_feedforward:prior['approach_velocity_feedforward']=True
        if observe_optical_coupon:prior['observe_optical_coupon']=True
        if register_optical_map:prior['register_optical_static_map']=True
    if carry_distance is not None:prior['carry_distance_m']=carry_distance
    if return_base_after_release:prior['return_base_after_release']=True
    if carry_thumb_force is not None:prior['carry_hold_force_proxy_n']=[carry_thumb_force,carry_thumb_force/2,carry_thumb_force/2]
    if carry_load_abort is not None:prior['carry_motor_load_abort_nm']=carry_load_abort
    if carry_preload_before_lift:prior['carry_preload_before_lift']=True
    if carry_command_excursion is not None:prior['carry_driver_command_excursion_rad']=carry_command_excursion
    if carry_finger_load_compensation:prior['carry_finger_load_compensation']=True
    if carry_body_joint_damper:prior['carry_body_joint_damper']=True
    if carry_body_withdrawal:prior['carry_body_withdrawal']=True
    if carry_support_inset:prior['carry_support_inset_m']=carry_support_inset
    if carry_proximal_preshape:prior['carry_proximal_preshape_rad']=carry_proximal_preshape
    if carry_prelift_dwell is not None:prior['carry_prelift_proxy_dwell_s']=carry_prelift_dwell
    prior_path.write_text(json.dumps(prior, indent=2)+'\n')
    command = [sys.executable, str(HERE/(actor_module+'.py')), '--model', str(output/'controller_model/world.xml')]
    command, environment, isolation = prepare(output, output/'controller_model/world.xml', command,
        extra_modules=extra_modules, policy_files=[prior_path],shape_files=shapes)
    dt = float(model.opt.timestep); stride = round(.001/dt)
    assert abs(stride*dt-.001) < 1e-12
    run_contract = dict(scope=__doc__, station_review_sha256=sha(station/'review.json'),
        station_contract_sha256=sha(station/'contract.json'), model_sha256=sha(output/'world.xml'),
        model_inputs_sha256=sha(output/'model_inputs.json'), duration_limit_s=duration,
        laboratory_import_sha256=sha(output/'laboratory_import.json'),
        physics_period_s=dt, control_period_s=.001, balance_period_s=.01,
        initial_qpos=data.qpos.tolist(), initial_qvel=data.qvel.tolist(),
        actor_access_isolated=isolation['passed'], controller_fields=sorted(__import__(actor_module).ToolActor.fields),
        actor_isolation_sha256=sha(output/'actor_isolation.json'), controller_prior_sha256=sha(prior_path),
        source_snapshot_sha256={p.name: sha(p) for p in snapshot.iterdir()},
        actor_module=actor_module, hand_kind='unitree_three_finger' if dex3 else 'inspire_ftp',
        task='pickup_hold_replace_release' if dex3 else 'pickup_closure_replace_release',
        actuator_count=model.nu,
        contact_solver_revision=solver_revision,
        hand_tool_compliance_revision=compliance_revision,
        inferred_control=dict(release_extra_opening_rad=release_extra_opening, closure_speed_m_s=.0005, hold_force_proxy_n=.6, close_timeout_s=close_timeout,
            first_contact_force_proxy_n=.04, contact_entry_force_proxy_n=.05,
            lift_height_m=tool_lift_height, grip_force_deadband_n=grip_force_deadband, pinch_center_correction_limit_m=.02,
            pad_geometry_is_not_measured_pressure_centroid=True, hardware_force_calibration_claimed=False),
        physical_acceptance=dict(minimum_actual_tool_lift_m=.02, minimum_lift_hold_s=.5,
            minimum_bilateral_finger_load_n=.2, minimum_bilateral_contact_s=1.,
            maximum_hand_tool_penetration_m=.00025, maximum_passive_support_penetration_m=.00025,
            maximum_other_penetration_m=.00002, maximum_sole_penetration_m=.001,
            maximum_source_joint_limit_excess_rad=.001, minimum_pelvis_height_m=.6,
            minimum_upright_cosine=.85, maximum_normal_force_n=4., maximum_unintended_hand_tool_load_n=.05,
            minimum_loaded_tip_closure_m=.001, released_tip_gap_target_m=.008,
            released_tip_gap_tolerance_m=.0001, maximum_replay_error=1e-10,
            final_released_support_hold_s=1., minimum_final_tool_support_force_n=.15,
            maximum_released_finger_force_n=.02, maximum_final_tool_speed_m_s=.005),
        allowed_tool_contact_bodies=['right_index_force_sensor_2', 'right_index_force_sensor_3',
            'right_thumb_force_sensor_3', 'right_thumb_force_sensor_4', 'right_index_2', 'right_thumb_4'],
        qualified_grasp=False, qualified_paper_branch=False)
    if grasp_proximal_preshape:
        run_contract['supported_grasp_preshape']=dict(
            index_and_middle_proximal_offset_rad=grasp_proximal_preshape,
            ramp_duration_s=12.,source_joint_margin_rad=.01,
            lift_requires_preshape_finished_and_fresh_load_dwell=True,
            nonclosing_joint_motor_residual_compensation=True,
            scope='Authored supported grasp adjustment; no grasp or tool-use qualification')
    if tool_squeeze_force is not None:
        run_contract['tool_actuation_contract']=dict(
            scope='Operate the free passive tweezer while maintaining the robot grasp; no specimen pickup credit',
            squeeze_force_proxy_n=prior['tool_squeeze_force_proxy_n'],
            reopen_force_proxy_n=prior['hold_force_proxy_n'],
            actor_inputs='Own encoders, IMU and inferred motor loads; no simulator tool pose or tip gap',
            minimum_open_tip_gap_m=.003,maximum_squeezed_tip_gap_m=.0005,
            maximum_tool_wrist_translation_drift_m=.01,
            force_target_relative_band=.15,force_target_dwell_s=.75,phase_timeout_s=20.,
            driver_command_excursion_rad=.25,source_joint_margin_rad=.01,
            physical_contact_and_motor_limits_unchanged=True,qualified_tool_actuation=False)
    if plugins:
        run_contract['collision_plugins'] = plugins
    if contract.get('optical_scene_binding'):
        run_contract['optical_scene_binding']=contract['optical_scene_binding']
        optical_records=['optical_scene_binding.json','optical_scene_support_review.json']
        if contract['optical_scene_binding'].get('support_velocity_review_sha256'):
            assert sha(station/'optical_support_velocity_review.json') == contract['optical_scene_binding']['support_velocity_review_sha256']
            optical_records.append('optical_support_velocity_review.json')
        for name in optical_records:
            shutil.copyfile(station/name,output/name)
        run_contract['optical_scene_records_sha256']={name:sha(output/name) for name in
            optical_records}
        run_contract['observed_optical_coupon_required_before_approach']=observe_optical_coupon
    if visual:
        run_contract.update(observed_approach=True,
            camera_contract=dict(names=['head_rgb','head_depth'],width=640,height=480,period_s=.2,
                depth_multisampling=False,capture_phase='observe',renderer_sha256=sha(snapshot/'tool_cameras.py'),
                depth_helper_sha256=sha(snapshot/'sensor_rendering.py')),
            tool_shape_sha256=sha(shapes[0]),qualified_approach=False)
        if approach_feedforward:
            run_contract['inferred_control']['approach_velocity_feedforward']='Mean commanded wrist translation and world rotation velocity over each 10 ms balance period; approach phase only'
    if dex3:
        run_contract['allowed_tool_contact_bodies']=[r['body'] for r in contract['robot_contact_features']]
        run_contract['inferred_control'].update(hold_force_proxy_n=prior['hold_force_proxy_n'],first_contact_force_proxy_n=.03,
            pickup_motor_load_observer_abort_nm=.15,
            lift_force_proxy_threshold_n=prior['lift_force_proxy_threshold_n'],lift_load_hold_s=.5,
            release_extra_opening_rad=prior['release_extra_opening_rad'],
            post_release_withdrawal_m=prior['post_release_withdrawal_m'],
            release_motor_load_gate_n=.015,release_clear_dwell_s=.1,
            hand_feedback_rule='Inertia eigenmodes: kp=min(3,0.25*I/dt^2); kd=min(2*sqrt(kp*I),0.4*scale*I/dt); scale applies only after load entry in loaded phases',
            loaded_hand_damping_scale=loaded_hand_damping_scale,
            startup_com_shift='Two-second smooth movement from initial COM toward support center',
            robot_contact_features=contract['robot_contact_features'])
        if release_driver_openings is not None:
            run_contract['inferred_control']['release_driver_openings_rad']=dict(
                zip(prior['closing_drivers'],prior['release_driver_openings_rad']))
        if release_load_feedback:
            run_contract['inferred_control']['release_load_feedback']=dict(
                inputs='Signed own-motor load estimates only', opening_rate_rad_s=.01,
                opening_bounds_rad=[0.,.08], enabled_after_initial_ramp_s=2.,
                release_gate_dwell_and_timeout_unchanged=True)
        if release_preserve_posture:
            run_contract['inferred_control']['release_preserve_posture']=dict(
                inputs='Own commanded non-closing hand joint angles at release entry',
                basis='Retain the supported grasp preshape while opening distal drivers; restoring proximal angles can push the fingertip into the tool',
                joint_limits_and_release_acceptance_unchanged=True)
        if release_clearance_height:
            run_contract['inferred_control']['release_clearance_motion']=dict(
                upward_height_m=release_clearance_height,ramp_duration_s=.5,
                start_after_opening_ramp_s=2.,maximum_initial_force_proxy_n=.05,
                basis='Authored small upward retreat after opening and low motor loads; actual passive support and release remain independently evaluated',
                release_gate_dwell_and_timeout_unchanged=True)
        run_contract['physical_acceptance'].update(minimum_each_opposing_finger_load_n=.1,
            minimum_thumb_load_n=.2,minimum_three_finger_contact_s=1.,require_loaded_tool_closure=False)
    if carry_distance is not None:
        run_contract.update(task='visual_pickup_loaded_out_and_back_release',qualified_carry=False,
            carry_contract=dict(commanded_local_distance_m=carry_distance,
                minimum_actual_base_excursion_m=carry_distance*.75,
                minimum_each_sole_lift_m=.025,maximum_final_base_xy_error_m=.02,
                maximum_final_tool_position_error_m=.01,maximum_contiguous_lost_load_s=.20,
                maximum_tool_wrist_position_drift_m=.015,
                additional_raise_m=.05,arm_withdrawal_m=0. if carry_body_withdrawal else .10,
                scope='Local loaded stepping and return to observed source; no cross-station or paper-branch qualification',
                collision_guard_scope='Right arm and rigid grasp hypothesis versus public map and observed surfaces; full plant assessed independently',
                online_slip_pose_observed=False))
        run_contract['carry_contract'].update(
            hold_force_proxy_n=prior.get('carry_hold_force_proxy_n',prior['hold_force_proxy_n']),
            preload_force_increase=bool(carry_thumb_force is not None and carry_thumb_force>thumb_force),
            motor_load_observer_abort_nm=prior.get('carry_motor_load_abort_nm',.15),
            motor_load_observer_bound_basis='Authored controller stop bound, at most half the unchanged source driver effort; not a physical acceptance limit',
            endpoint_arm_joint_margin_rad=.08)
        run_contract['carry_contract']['driver_command_excursion_rad']=prior.get('carry_driver_command_excursion_rad',.15)
        run_contract['carry_contract'].update(
            finger_posture_load_compensation=carry_finger_load_compensation,
            body_joint_boundary_damping=carry_body_joint_damper,
            prelift_proxy_dwell_s=prior.get('carry_prelift_proxy_dwell_s',.5))
        run_contract['carry_contract']['stance_target_inset_m']=carry_support_inset
        run_contract['carry_contract'].update(proximal_preshape_rad=carry_proximal_preshape,
            proximal_preshape_duration_s=12. if carry_proximal_preshape else 0.,
            proximal_preshape_basis='Authored signed index/middle proximal offset while supported; existing distal force feedback, material friction and physical acceptance bounds retained')
        if carry_body_withdrawal:
            run_contract['carry_contract'].update(withdrawal_mode='body_translation',
                maximum_wrist_rotation_change_rad=.04,
                body_route_scope='Same physical out-and-back distance, two-foot stepping, retention and return requirements; no rotated arm withdrawal stage')
        if carry_preload_before_lift:
            run_contract['carry_contract'].update(preload_before_lift=True,
                lift_force_proxy_threshold_n=(.85*np.asarray(run_contract['carry_contract']['hold_force_proxy_n'])).tolist(),
                minimum_native_loaded_before_lift_s=.5,
                prelift_native_load_thresholds='Same independently measured thumb/opposing contact thresholds as physical_acceptance')
    if return_base_after_release:
        run_contract['carry_contract']['empty_hand_base_return']=dict(
            target='Original declared initial base XY; proprioceptive robot estimate',
            commanded_transition_s=4.,observed_position_tolerance_m=.008,
            clearance='Observed arm/source meshes plus native source self-contact at the released encoder-derived finger pose',
            maximum_wait_s=12.,initial_pose_reset=False,physical_acceptance_unchanged=True)
    if register_optical_map:
        run_contract['static_map_registration']=dict(pixel_center=.5,depth_correspondence_gate_m=.004,
            huber_scale_m=.0002,inputs='Native depth, encoders, IMU and public static controller map',
            pose_truth_available_to_actor=False,qualified_localization=False)
    (output/'contract.json').write_text(json.dumps(run_contract, indent=2)+'\n')
    if prepare_only:
        prepared=dict(status='prepared_not_executed',contract_sha256=sha(output/'contract.json'),
            actor_access_isolated=isolation['passed'],qualified_grasp=False,qualified_paper_branch=False)
        (output/'preparation.json').write_text(json.dumps(prepared,indent=2)+'\n')
        print(json.dumps(prepared),flush=True);return prepared
    names = [model.joint(j).name for j in robot_joints(model)]
    records, sensors, responses = [], [], []
    cameras=None;frame_index=[]
    if visual:
        from tool_cameras import ToolCameras
        cameras=ToolCameras(model);(output/'camera_frames').mkdir()
    failure = None; response = {}; started = time.monotonic()
    stop = {'signal': None}
    previous_handlers = {}
    for signum in [signal.SIGINT, signal.SIGTERM]:
        previous_handlers[signum] = signal.signal(signum, lambda number, frame: stop.update(signal=number))
    tool_body = model.body('tweezer').id
    tool_bodies = {tool_body}
    for b in range(model.nbody):
        if model.body_parentid[b] in tool_bodies: tool_bodies.add(b)
    allowed_tool_bodies = {model.body(n).id for n in run_contract['allowed_tool_contact_bodies']}
    with (output/'actor_stderr.log').open('wb') as log, (output/'monitor.jsonl').open('w') as monitor, \
         (output/'physics_monitor.jsonl').open('w') as physics_monitor:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, env=environment)
        try:
            for i in range(round(duration/dt)):
                if stop['signal'] is not None: raise RuntimeError('Run interrupted by signal '+str(stop['signal'])+'; partial trace retained')
                if i % stride == 0:
                    packet = dict(time_s=float(data.time),
                        joint_position=np.array([data.sensor(n+'_encoder').data[0] for n in names]),
                        joint_velocity=np.array([data.sensor(n+'_velocity').data[0] for n in names]),
                        imu_quaternion=data.sensor('imu_orientation').data.copy(),
                        imu_gyro=data.sensor('imu_angular_velocity').data.copy())
                    if not dex3: packet['right_touch_n']=read_touch(data)
                    retained=dict(packet)
                    if visual:
                        frame_id=-1
                        if i % (stride*200)==0 and response.get('phase','observe')=='observe':
                            frames=cameras.read(data);frame_id=len(frame_index)
                            path=output/'camera_frames'/f'{frame_id:05d}.npz'
                            np.savez_compressed(path,**frames)
                            frame_index.append(dict(id=frame_id,time_s=float(data.time),file=str(path.relative_to(output)),sha256=sha(path)))
                        else:frames=dict(head_rgb=None,head_depth=None)
                        packet.update(frames);retained['camera_frame_id']=frame_id
                    sensors.append(retained)
                    pickle.dump(packet, process.stdin, protocol=5); process.stdin.flush()
                    response = pickle.load(process.stdout)
                    responses.append({k: v for k, v in response.items() if k != 'events'})
                    if response['error']: raise RuntimeError(response['error'])
                    data.ctrl[:] = response['torque']
                    if i % (stride*10) == 0:
                        monitor.write(json.dumps(dict(time_s=float(data.time), **{k: v for k, v in response.items()
                            if k not in {'torque', 'requested_joint_position', 'events'}}), default=plain)+'\n'); monitor.flush()
                records.append((float(data.time), data.qpos.copy(), data.qvel.copy(), data.ctrl.copy(), data.qacc_warmstart.copy()))
                if response.get('complete'): break
                mujoco.mj_step(model, data)
                if i % (stride*10) == 0:
                    forces = {'index': 0., 'thumb': 0., **({'middle': 0.} if dex3 else {})}; tool_support = 0.
                    for ci, contact in enumerate(data.contact):
                        bodies = [int(model.geom_bodyid[g]) for g in contact.geom]
                        if sum(b in tool_bodies for b in bodies) != 1: continue
                        other = next(b for b in bodies if b not in tool_bodies)
                        wrench = np.zeros(6); mujoco.mj_contactForce(model, data, ci, wrench)
                        if other in allowed_tool_bodies:
                            finger = next(f for f in forces if f in model.body(other).name)
                            forces[finger] += max(0., float(wrench[0]))
                        elif other == model.body('carrier_tray').id: tool_support += max(0., float(wrench[0]))
                    # mj_step's geometry and contact forces refer to the
                    # pre-integration time; keep this out of the actor bundle.
                    physics_monitor.write(json.dumps(dict(time_s=float(data.time-dt),
                        tool_position_m=data.body('tweezer').xpos.tolist(),
                        finger_normal_force_n=forces, tray_support_force_n=tool_support))+'\n'); physics_monitor.flush()
                if not np.isfinite(data.qpos).all() or np.any(data.warning.number): raise RuntimeError('Physics numerical failure')
                if data.qpos[2] < .6 or data.body('pelvis').xmat.reshape(3, 3)[2, 2] < .85: raise RuntimeError('Body support lost')
                if np.any(data.xfrc_applied) or np.any(data.qfrc_applied): raise RuntimeError('Unexpected external applied force')
                if i % round(.5/dt) == 0:
                    print('tool', round(float(data.time), 3), response.get('phase'),
                          'wall_s', round(time.monotonic()-started, 1), flush=True)
            if not response.get('complete'): failure = 'Duration exhausted before the attempt ended'
            elif response.get('failure'): failure = response['failure']
        except Exception as error:
            failure = str(error); print('failed', failure, flush=True)
        finally:
            process.stdin.close()
            try: process.wait(timeout=15)
            except subprocess.TimeoutExpired: process.kill(); process.wait()
    for signum, handler in previous_handlers.items(): signal.signal(signum, handler)
    if cameras is not None:cameras.close()
    if not records or abs(records[-1][0]-data.time) > 1e-12:
        records.append((float(data.time), data.qpos.copy(), data.qvel.copy(), data.ctrl.copy(), data.qacc_warmstart.copy()))
    np.savez_compressed(output/'trace.npz', **{k: np.asarray([r[i] for r in records])
        for i, k in enumerate(['time', 'qpos', 'qvel', 'ctrl', 'qacc_warmstart'])})
    if sensors: np.savez_compressed(output/'sensors.npz', **{k: np.asarray([r[k] for r in sensors]) for k in sensors[0]})
    (output/'responses.pkl').write_bytes(pickle.dumps(responses, protocol=5))
    (output/'events.json').write_text(json.dumps(response.get('events', []), indent=2)+'\n')
    if visual:(output/'camera_index.json').write_text(json.dumps(frame_index,indent=2)+'\n')
    result = dict(scope=__doc__, status='failed' if failure else 'attempt_finished_pending_independent_verification',
        failure=failure, simulated_seconds=float(data.time), wall_seconds=time.monotonic()-started,
        environment='existing_complete_laboratory', contract_sha256=sha(output/'contract.json'),
        trace_sha256=sha(output/'trace.npz'), sensors_sha256=sha(output/'sensors.npz') if sensors else None,
        responses_sha256=sha(output/'responses.pkl'), actor_access_isolated=isolation['passed'],
        physics_warning_counts=data.warning.number.tolist(), qualified_grasp=False, qualified_paper_branch=False)
    if visual:result.update(camera_index_sha256=sha(output/'camera_index.json'),camera_frames=len(frame_index),qualified_approach=False)
    if carry_distance is not None:result['qualified_carry']=False
    (output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('station'); p.add_argument('output')
    p.add_argument('--duration', type=float, default=20.)
    p.add_argument('--close-timeout', type=float, default=6.)
    p.add_argument('--thumb-force', type=float, default=.6);p.add_argument('--lift-force',type=float,default=.5)
    p.add_argument('--approach-feedforward',action='store_true')
    p.add_argument('--carry-distance',type=float)
    p.add_argument('--carry-thumb-force',type=float)
    p.add_argument('--prepare-only',action='store_true')
    p.add_argument('--carry-load-abort',type=float)
    p.add_argument('--carry-preload-before-lift',action='store_true')
    p.add_argument('--carry-command-excursion',type=float)
    p.add_argument('--carry-finger-load-compensation',action='store_true')
    p.add_argument('--carry-body-joint-damper',action='store_true')
    p.add_argument('--carry-prelift-dwell',type=float)
    p.add_argument('--carry-body-withdrawal',action='store_true')
    p.add_argument('--carry-support-inset',type=float,default=0.)
    p.add_argument('--carry-proximal-preshape',type=float,default=0.)
    p.add_argument('--contact-cone',choices=['pyramidal','elliptic'])
    p.add_argument('--contact-impratio',type=float)
    p.add_argument('--hand-contact-impedance',type=float,
        help='Uncalibrated fingertip/tool compliance sensitivity trial; physical bounds remain unchanged')
    p.add_argument('--tool-squeeze-force',type=float,
        help='After lifting, squeeze and reopen the passive tool using own-motor feedback')
    p.add_argument('--release-extra-opening',type=float,default=.04,
                   help='Additional driver opening at release, inside the existing 0.08 rad bound')
    p.add_argument('--release-driver-openings',type=float,nargs=3,
                   metavar=('THUMB','INDEX','MIDDLE'),
                   help='Optional per-driver release opening in rad; same 0.08 rad bound and release-load gate')
    p.add_argument('--release-load-feedback',action='store_true',
                   help='Adjust release opening from signed motor loads inside the unchanged opening envelope')
    p.add_argument('--observe-optical-coupon',action='store_true',
                   help='Require four stable native RGB-D coupon observations before tool approach')
    p.add_argument('--release-clearance-height',type=float,default=0.,
                   help='Small upward retreat during release after low motor loads, at most 4 mm')
    p.add_argument('--release-preserve-posture',action='store_true',
                   help='Keep non-closing finger joint references at their release-entry posture')
    p.add_argument('--tool-lift-height',type=float,default=.03,
                   help='Commanded tool lift in metres; 20 to 60 mm, unchanged physical acceptance')
    p.add_argument('--register-optical-map',action='store_true',
                   help='Register native depth to the static map before optical/tool observation')
    p.add_argument('--return-base-after-release',action='store_true',
                   help='Return the empty-handed robot to its original base position using motor control')
    p.add_argument('--grip-force-deadband',type=float,default=0.,
                   help='Stop position-reference integration within this observed force error (0 to 0.1 N)')
    p.add_argument('--loaded-hand-damping-scale',type=float,default=1.,
                   help='Increase own-velocity feedback during loaded phases (1 to 2); unchanged physical limits')
    p.add_argument('--grasp-proximal-preshape',type=float,default=0.,
                   help='Ramp index/middle proximal references while the tool is supported; at most 0.08 rad')
    a = p.parse_args()
    if run(a.station, a.output, a.duration, a.close_timeout,a.thumb_force,a.lift_force,a.approach_feedforward,a.carry_distance,a.carry_thumb_force,a.prepare_only,a.carry_load_abort,a.carry_preload_before_lift,a.carry_command_excursion,a.carry_finger_load_compensation,a.carry_body_joint_damper,a.carry_prelift_dwell,a.carry_body_withdrawal,a.carry_support_inset,a.carry_proximal_preshape,a.contact_cone,a.contact_impratio,a.release_extra_opening,a.release_driver_openings,a.release_load_feedback,a.observe_optical_coupon,a.release_clearance_height,a.release_preserve_posture,a.tool_lift_height,a.register_optical_map,a.return_base_after_release,a.grip_force_deadband,a.loaded_hand_damping_scale,a.hand_contact_impedance,a.tool_squeeze_force,a.grasp_proximal_preshape)['status'] == 'failed': raise SystemExit(1)
