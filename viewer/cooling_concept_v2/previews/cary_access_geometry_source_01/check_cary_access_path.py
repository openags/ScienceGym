"""Screen cover removal and slide motion in the complete installed laboratory.

The selected complete-removal method is described in the extended-compartment
manual. Lifts, translations and the resting bench pose below are inferred;
the robot must execute them with continuous support before this is a task.
"""
import hashlib,json
import numpy as np
from cary_access_scene import CaryAccessScene,translation
from optical_choreography import HERE


def main():
    scene=CaryAccessScene();rows=[]
    for u in np.linspace(0,1,62):
        scene.set_access(lid=.305*u)
        rows.append(dict(stage='slide_open',lid_m=float(.305*u),cover_offset_m=[0,0,0],failures=scene.access_clearance('lid')))
    # Pull the released cover forward into the aisle before any sideways move.
    points=[[0,0,0],[0,0,.006],[0,-.10,.006],[0,-.25,.05],[.943,-.25,.05],[.943,.20,.05],[.943,.20,-.140]]
    for i,(a,b) in enumerate(zip(points,points[1:])):
        for u in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(np.subtract(b,a))/.004))+1)):
            offset=np.array(a)*(1-u)+np.array(b)*u;scene.set_access(lid=.305,cover=translation(offset))
            rows.append(dict(stage='cover_'+str(i),lid_m=.305,cover_offset_m=offset.tolist(),failures=scene.access_clearance('cover')))
    failed=[r for r in rows if r['failures']]
    report=dict(scope=__doc__,passed=not failed,samples=len(rows),failed_samples=len(failed),rows=rows,source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['cary_access_scene.py','check_cary_access_path.py']})
    (HERE/'previews/cary_access_geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],samples=len(rows),failed_samples=len(failed),first=failed[:2])),flush=True)


if __name__=='__main__':main()
