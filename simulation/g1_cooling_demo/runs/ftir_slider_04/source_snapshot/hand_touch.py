"""Ideal normal-force sensing on the existing source index/thumb pad bodies.

FTP tactile sensing is documented by Inspire. These per-mesh scalar channels
are an inferred simulation abstraction, not its calibrated hardware taxels.
They expose no contacted-object identity, pose, or device joint state.
"""
TOUCH_PADS = ['right_index_force_sensor_' + str(i) for i in range(1, 4)] + [
             'right_thumb_force_sensor_' + str(i) for i in range(1, 5)]


def attach(xml, robot_root, out):
    import hashlib
    import json
    import xml.etree.ElementTree as ET
    import numpy as np
    import trimesh

    rows = []
    for name in TOUCH_PADS:
        body = xml.find(f'.//body[@name="{name}"]')
        geom = body.find(f'geom[@name="{name}_collision_0"]')
        assert geom.get('pos') == '0 0 0' and geom.get('quat') == '1 0 0 0'
        mesh = xml.find(f'asset/mesh[@name="{geom.get("mesh")}"]')
        path = robot_root / mesh.get('file')
        vertices = np.asarray(trimesh.load(path, force='mesh', process=False).vertices)
        lo, hi = vertices.min(axis=0), vertices.max(axis=0)
        center, half = (lo + hi) / 2, (hi - lo) / 2 + .0001
        site = name + '_touch_region'
        ET.SubElement(body, 'site', name=site, type='box',
                      pos=' '.join(map(str, center)), size=' '.join(map(str, half)),
                      group='5', rgba='0 0 0 0')
        ET.SubElement(xml.find('sensor'), 'touch', name=name + '_touch', site=site)
        rows.append(dict(body=name, source_mesh=str(path.relative_to(robot_root)),
                         source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         site_center_m=center.tolist(), site_halfsize_m=half.tolist()))
    report = dict(scope=__doc__, channels=rows, units='N', extra_sensor_volume_margin_m=.0001,
                  hardware_calibrated=False, noise_model='ideal',
                  source='https://en.inspire-robots.com/news/5508.html',
                  limitations=['Per-source-pad scalar normal force; not a reconstruction of the vendor tactile array.',
                               'No object-specific contact filtering. Self contact is sensed as well.'])
    (out / 'hand_touch_profile.json').write_text(json.dumps(report, indent=2) + '\n')


def read(data):
    import numpy as np
    return np.array([data.sensor(name + '_touch').data[0] for name in TOUCH_PADS])
