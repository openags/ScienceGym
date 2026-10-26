"""Independent sensor-input actor. No plant object poses or evaluator data."""
import argparse,pickle,sys
import numpy as np
import mujoco
from scipy.spatial.transform import Rotation
from robot_state import initialize
from balance import Balance
from observations import StateEstimate


def main(path):
    model=mujoco.MjModel.from_xml_path(path);data=initialize(model);estimate=StateEstimate(model,data);controller=Balance(model,data)
    zero=mujoco.MjData(model);mujoco.mj_forward(model,zero)
    controller.palm_rotations={s:Rotation.from_euler('x',-45 if s=='left' else 45,degrees=True).as_matrix()@zero.site(s+'_wrist_reference').xmat.reshape(3,3) for s in ['left','right']}
    begin={s:data.site(s+'_wrist_reference').xpos.copy() for s in ['left','right']};observed=[];target=None
    while True:
        try:obs=pickle.load(sys.stdin.buffer)
        except EOFError:break
        try:
            estimate.update(obs);now=obs['time_s']
            if now<2 and obs['depth'] is not None:
                detection=estimate.tray(obs['depth'])
                if detection is not None:observed.append(detection)
            if now>=2 and target is None:
                if not observed:raise RuntimeError('Tray not localized in native head depth image')
                target=np.median([x['center_m'] for x in observed],axis=0)
            def ramp(a,b):
                t=np.clip((now-a)/(b-a),0,1);return t*t*(3-2*t)
            lift=ramp(2,5);forward=ramp(6,9);down=ramp(10,13);close=ramp(14,16);up=ramp(18,21);transfer=ramp(22,25);release_down=ramp(26,29);open_hand=ramp(30,32);retreat=ramp(33,36)
            targets=None;forces=None
            if target is not None:
                # Catalog tray size and inferred approach offset are policy
                # parameters. The tray centre itself comes only from depth.
                x=target[0]-.02;y=target[1]
                targets={s:begin[s]+np.array([(x-begin[s][0])*forward-.025*transfer-(x-begin[s][0])*retreat,
                    ((.20-abs(begin[s][1]))*lift-.052*close+.055*open_hand)*(1 if s=='left' else -1)+y*forward+.06*transfer,
                    (1.04-begin[s][2])*lift-.110*down+.18*up-.18*release_down+.10*retreat]) for s in begin}
                forces={s:[0,(-1 if s=='left' else 1)*15*close*(1-open_hand),0] for s in begin}
            torque=controller.torque(targets=targets,forces=forces)
            result=dict(torque=torque,observed_target=None if target is None else target.tolist(),depth_detections=len(observed),maximum_qp_iterations=controller.max_iter,error=None)
        except Exception as e:result=dict(torque=np.zeros(model.nu),error=str(e))
        pickle.dump(result,sys.stdout.buffer,protocol=5);sys.stdout.buffer.flush()
        if result['error']:break


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);a=p.parse_args();main(a.model)
