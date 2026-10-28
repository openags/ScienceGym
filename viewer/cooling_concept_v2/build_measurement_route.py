"""Extract the player map from the poses of the published video frames."""
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def build():
    delivery = json.loads((HERE / 'measurement_delivery.json').read_text())
    audit = HERE / delivery['capture_receipt']
    receipt = json.loads(audit.read_text())
    export = json.loads((audit.parent / 'export.json').read_text())
    assert delivery['reviewed']
    assert hashlib.sha256(audit.read_bytes()).hexdigest() == delivery['capture_receipt_sha256']
    assert hashlib.sha256((HERE / delivery['video']).read_bytes()).hexdigest() == delivery['video_sha256']
    assert hashlib.sha256((HERE / 'runtime_scene.json').read_bytes()).hexdigest() == delivery['renderer_sources']['runtime_scene.json']
    assert hashlib.sha256((HERE / 'single_measurement_episode.json').read_bytes()).hexdigest() == delivery['renderer_sources']['single_measurement_episode.json']
    episode = json.loads((HERE / 'single_measurement_episode.json').read_text())
    titles = {s['id']: s['title'] for s in episode['segments']}
    scene = json.loads((HERE / 'runtime_scene.json').read_text())
    samples, last_phase, count = [], None, 0
    digest = hashlib.sha256()
    with gzip.open(audit.parent / 'frames.jsonl.gz', 'rb') as stream:
        for index, line in enumerate(stream):
            digest.update(line)
            # The prefix is the original JSON object before large mesh arrays.
            # No pose is reconstructed from waypoints or an assumed itinerary.
            prefix = line.split(b',"groups":', 1)
            assert len(prefix) == 2
            frame = json.loads(prefix[0] + b'}')
            count += 1
            if index % 4 == 0 or frame['phase'] != last_phase or index == delivery['frames'] - 1:
                optical = json.loads(line.rsplit(b',"optical_state":', 1)[1].split(b',"measurement_state":', 1)[0])
                samples.append([frame['time_s'], *frame['robot_position'][:2],
                                frame['robot_yaw'], frame['phase'],
                                optical['tool_held'], optical['held_specimen']])
            last_phase = frame['phase']
    assert count == delivery['frames'] == receipt['frames']
    assert digest.hexdigest() == export['frames_sha256']
    out = {
        'schema_version': 1,
        'scope': 'Video navigation only; these are authored display poses, not a sensor or dynamics trajectory.',
        'source_video': delivery['video'], 'video_sha256': delivery['video_sha256'],
        'source_frames_sha256': digest.hexdigest(), 'video_frames': count,
        'duration_s': delivery['scene_duration_s'],
        'columns': ['time_s', 'lab_x_m', 'lab_y_m', 'yaw_rad', 'phase', 'tool_held', 'held_specimen'],
        'samples': samples, 'phase_titles': titles,
        'zones': scene['zones'], 'surfaces': scene['support_surfaces'],
        'floors': [p['bounds_m'] for p in scene['architecture']['part_records'] if p['role'] == 'floor'],
        'walls': [p['bounds_m'] for p in scene['architecture']['part_records'] if p['role'] == 'wall_lower'],
        'stations': [
            {'id': 'materials', 'label': '备料 / 取样', 'position_m': [2.9, 8.7], 'time_s': next(s['start'] for s in episode['segments'] if s['id'] == 'white_delivery_approach_witness')},
            {'id': 'ftir', 'label': 'FTIR / 测量与归位', 'position_m': [9.5, 8.7], 'time_s': next(s['start'] for s in episode['segments'] if s['id'] == 'install_gold_reference')},
        ],
    }
    target = HERE / 'measurement_route.json'
    target.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')) + '\n')
    print(json.dumps({'route_samples': len(samples), 'source_video_frames': count, 'bytes': target.stat().st_size}))


if __name__ == '__main__':
    build()
