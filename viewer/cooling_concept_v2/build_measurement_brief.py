"""Export a shorter presentation without cutting any operation or walking leg.

This retimes the reviewed authored movie, not a physical trajectory. Movement
and short contact actions retain every source frame. Every output frame comes
from the original movie; no interpolation or synthesized motion is introduced.
"""
import bisect
import hashlib
import json
import math
import subprocess
from pathlib import Path

import cv2

HERE = Path(__file__).resolve().parent
FPS = 24


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def write(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main():
    delivery = read('measurement_delivery.json')
    episode = read('single_measurement_episode.json')
    route = read('measurement_route.json')
    source = HERE / delivery['video']
    assert delivery['reviewed'] and delivery['fps'] == FPS
    assert sha(source) == delivery['video_sha256'] == route['video_sha256']
    assert sha(HERE / delivery['review']) == delivery['review_sha256']
    assert sha(HERE / 'single_measurement_episode.json') == delivery['renderer_sources']['single_measurement_episode.json']
    review = read(delivery['review'])
    assert review['passed'] and review['covers_entire_episode'] and review['every_video_frame']

    indices, ranges = [], []
    segments = episode['segments']
    for n, segment in enumerate(segments):
        first = math.ceil(segment['start'] * FPS - 1e-8)
        last = (math.ceil(segment['end'] * FPS - 1e-8)
                if n < len(segments) - 1 else delivery['frames'])
        rate = (4 if segment['kind'] == 'wait' else
                1 if segment['kind'] == 'move' or segment['duration_s'] <= 1.25 else 2.5)
        count = last - first
        output_count = count if rate == 1 else max(2, math.ceil(count / rate))
        selected = [first + round(i * (count - 1) / (output_count - 1))
                    for i in range(output_count)]
        ranges.append(dict(id=segment['id'], title=segment['title'], kind=segment['kind'],
                           presentation_speed=rate, source_frames=[first, last],
                           output_frames=[len(indices), len(indices) + output_count]))
        indices.extend(selected)
    assert indices[0] == 0 and indices[-1] == delivery['frames'] - 1
    assert all(a < b for a, b in zip(indices, indices[1:]))
    assert all(a['source_frames'][1] == b['source_frames'][0] for a, b in zip(ranges, ranges[1:]))
    for row in ranges:
        if row['presentation_speed'] == 1:
            a, b = row['output_frames']
            assert indices[a:b] == list(range(*row['source_frames']))

    target = HERE / 'media/ftir_measurement_brief_01.mp4'
    if target.exists():
        raise FileExistsError(target)
    pending = target.with_suffix('.pending.mp4')
    width, height = delivery['resolution']
    cap = cv2.VideoCapture(str(source))
    assert cap.isOpened()
    encoder = subprocess.Popen([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo',
        '-pix_fmt', 'bgr24', '-s', f'{width}x{height}', '-r', str(FPS), '-i', '-',
        '-an', '-c:v', 'libx264', '-threads', '4', '-preset', 'fast', '-crf', '19',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(pending)], stdin=subprocess.PIPE)
    j = 0
    try:
        for i in range(delivery['frames']):
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError(f'Source decoding failed at frame {i}')
            if j < len(indices) and indices[j] == i:
                encoder.stdin.write(frame.tobytes())
                j += 1
            if i % 2400 == 0:
                print(json.dumps(dict(source_frame=i, output_frames=j)), flush=True)
        assert j == len(indices)
        assert not cap.read()[0]
    finally:
        cap.release()
        encoder.stdin.close()
        code = encoder.wait()
    assert code == 0
    probe = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(pending)]))
    stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    assert int(stream['nb_frames']) == len(indices)
    assert [stream['width'], stream['height']] == [width, height]
    assert abs(float(probe['format']['duration']) - len(indices) / FPS) < .002
    pending.rename(target)

    def output_time(source_seconds):
        frame = min(indices[-1], max(0, source_seconds * FPS))
        right = bisect.bisect_right(indices, frame)
        if right == len(indices):
            return (len(indices) - 1) / FPS
        left = max(0, right - 1)
        return (left + (frame - indices[left]) / (indices[right] - indices[left])) / FPS

    mapping = dict(schema_version=1, scope='Presentation frame selection only; no physics qualification.',
                   source_video=delivery['video'], source_video_sha256=delivery['video_sha256'],
                   video=str(target.relative_to(HERE)), video_sha256=sha(target), fps=FPS,
                   source_frame_count=delivery['frames'], output_frame_count=len(indices),
                   source_frame_per_output_frame=indices, segments=ranges,
                   complete_source_time_span=True, all_103_operations_retained=len(ranges) == 103,
                   all_movement_and_short_contact_frames_retained=True,
                   interpolation=False, overlays=False, builder_sha256=sha(Path(__file__)))
    write('media/ftir_measurement_brief_01_frames.json', mapping)
    route['scope'] = 'Video navigation for the shorter authored presentation; not a sensor or dynamics trajectory.'
    route['source_video'] = mapping['video']
    route['video_sha256'] = mapping['video_sha256']
    route['parent_route_sha256'] = sha(HERE / 'measurement_route.json')
    route['parent_video_sha256'] = delivery['video_sha256']
    route['video_frames'] = len(indices)
    route['duration_s'] = len(indices) / FPS
    for sample in route['samples']:
        sample[0] = output_time(sample[0])
    for station in route['stations']:
        station['time_s'] = output_time(station['time_s'])
    write('measurement_brief_route.json', route)
    brief = dict(delivery)
    brief.update(scope='Shorter presentation of the complete authored FTIR procedure; all operations and walking retained.',
                 video=mapping['video'], video_sha256=mapping['video_sha256'],
                 video_duration_s=len(indices) / FPS, frames=len(indices),
                 source_video=delivery['video'], source_video_sha256=delivery['video_sha256'],
                 source_delivery='measurement_delivery.json', source_delivery_sha256=sha(HERE / 'measurement_delivery.json'),
                 route='measurement_brief_route.json',
                 frame_mapping='media/ftir_measurement_brief_01_frames.json',
                 frame_mapping_sha256=sha(HERE / 'media/ftir_measurement_brief_01_frames.json'),
                 presentation_note='完整保留操作顺序；行走及短时接触原速，其余动作 2.5×，采集等待 4×。',
                 chapters=[dict(c, time_s=output_time(c['time_s'])) for c in delivery['chapters']])
    write('measurement_brief_delivery.json', brief)
    write('media/ftir_measurement_brief_01.json', brief)
    print(json.dumps(dict(video=brief['video'], seconds=brief['video_duration_s'], frames=len(indices),
                          movement_seconds=sum((r['output_frames'][1]-r['output_frames'][0])/FPS
                                               for r in ranges if r['kind'] == 'move'))), flush=True)


if __name__ == '__main__':
    main()
