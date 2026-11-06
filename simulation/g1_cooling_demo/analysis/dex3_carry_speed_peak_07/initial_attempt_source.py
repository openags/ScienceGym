"""Locate a recorded source-speed violation without changing runtime or limits."""
import hashlib,json,zipfile,time
from pathlib import Path
import mujoco,numpy as np
BASE=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
RUN=BASE/'runs/dex3_visual_carry_07';JOINT='right_hand_thumb_2_joint'
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
started=time.monotonic();review=json.loads((RUN/'source_limit_review.json').read_text())
result=json.loads((RUN/'result.json').read_text());assert review['trace_sha256']==result['trace_sha256']
assert sha(RUN/'trace.npz')==result['trace_sha256']
model=mujoco.MjModel.from_xml_path(str(RUN/'world.xml'));column=int(model.joint(JOINT).dofadr[0])
peak=0.;peak_index=None;speed=None;count=0;first=None
limit=next(r['source_velocity_rad_s'] for r in review['rows'] if r['joint']==JOINT)
with zipfile.ZipFile(RUN/'trace.npz') as archive:
    with archive.open('qvel.npy') as f:
        version=np.lib.format.read_magic(f)
        shape,fortran,dtype=np.lib.format._read_array_header(f,version)
        assert len(shape)==2 and not fortran and dtype.kind=='f'
        width=shape[1];row_bytes=width*dtype.itemsize;offset=0
        while offset<shape[0]:
            size=min(4096,shape[0]-offset);raw=f.read(size*row_bytes);assert len(raw)==size*row_bytes
            values=np.frombuffer(raw,dtype=dtype).reshape(size,width)[:,column]
            index=int(np.argmax(abs(values)));magnitude=float(abs(values[index]))
            if magnitude>peak:peak=magnitude;peak_index=offset+index;speed=float(values[index])
            bad=np.flatnonzero(abs(values)>limit+review['velocity_tolerance_rad_s']);count+=len(bad)
            if len(bad) and first is None:first=offset+int(bad[0])
            offset+=size
with np.load(RUN/'trace.npz') as trace:times=trace['time'].copy()
events=[e for e in json.loads((RUN/'events.json').read_text()) if 'phase' in e]
phase=lambda t:next((e['phase'] for e in reversed(events) if e['time_s']<=t),'initial')
expected=next(r['maximum_recorded_speed_rad_s'] for r in review['rows'] if r['joint']==JOINT)
assert abs(peak-expected)<1e-12
record=dict(scope=__doc__,joint=JOINT,source_limit_rad_s=limit,maximum_absolute_speed_rad_s=peak,
    signed_peak_speed_rad_s=speed,peak_time_s=float(times[peak_index]),peak_phase=phase(times[peak_index]),
    first_violation_time_s=None if first is None else float(times[first]),
    first_violation_phase=None if first is None else phase(times[first]),violating_native_samples=count,
    native_sample_period_s=float(np.median(np.diff(times))),source_result_sha256=sha(RUN/'result.json'),
    trace_sha256=result['trace_sha256'],source_limit_review_sha256=sha(RUN/'source_limit_review.json'),
    script_sha256=sha(__file__),seconds=time.monotonic()-started,qualified_carry=False)
(OUT/'review.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
