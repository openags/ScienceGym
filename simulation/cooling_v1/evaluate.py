"""Goal checks independent of the command executor's success messages."""
import numpy as np


def assess(scene, robot):
    d,m=robot.data,robot.model
    goals=[]
    def position(name,target,tolerance):
        error=float(np.linalg.norm(d.body(name).xpos-target))
        goals.append(dict(predicate='pose',object=name,error_m=error,tolerance_m=tolerance,passed=error<tolerance))
    def supported(name,support):
        force=sum(c['force_n'] for c in robot.contacts(name) if c['other']==support)
        threshold=float(m.body(name).mass[0])*9.81*.5
        speed=float(np.linalg.norm(d.body(name).cvel))
        goals.append(dict(predicate='retained_support',object=name,support=support,force_n=force,minimum_force_n=threshold,speed=speed,passed=force>threshold and speed<.03))
    def visited(name,target,tolerance):
        adr=int(m.joint(name+'_free').qposadr[0])
        closest=min((np.linalg.norm(row[1][adr:adr+3]-target) for row in robot.trace),default=999)
        goals.append(dict(predicate='visited_pose',object=name,closest_error_m=float(closest),passed=bool(closest<tolerance)))
    if scene=='assembly':
        for name,z,support in [('foam_lower',.7765,'assembly_base'),('foam_upper',.8015,'foam_lower'),('emitter',.81425,'foam_upper')]:
            position(name,np.array([.51,.13,z]),.003);supported(name,support)
        adr=int(m.joint('button_travel').qposadr[0])
        peak=max((row[1][adr] for row in robot.trace),default=0)
        goals.append(dict(predicate='button_travel',peak_m=float(peak),minimum_m=.003,passed=bool(peak>.003)))
    elif scene=='probe':
        position('probe',np.array([.45,-.22,.804]),.003);supported('probe','probe_stand')
        visited('probe',np.array([.53,.12,.804]),.002)
    elif scene=='lid':
        position('baseline_lid',np.array([.48,-.23,.752]),.004);supported('baseline_lid','lid_stand')
        visited('baseline_lid',np.array([.51,.13,.808]),.004)
    elif scene=='door':
        adr=int(m.joint('access_hinge').qposadr[0])
        peak=max((row[1][adr] for row in robot.trace),default=0);final=float(d.qpos[adr])
        goals.append(dict(predicate='open_then_close',peak_rad=float(peak),final_rad=final,passed=bool(peak>1 and abs(final-.02)<.03)))
    return dict(passed=bool(goals) and all(g['passed'] for g in goals),goals=goals)
