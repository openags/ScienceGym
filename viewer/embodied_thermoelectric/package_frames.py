#!/usr/bin/env python3
"""Package verified illustrated task frames as a self-contained offline viewer."""
import argparse
import base64
import hashlib
import json
import mimetypes
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    source = args.manifest.resolve()
    data = json.loads(source.read_text())
    frames = data.get('frames', [])
    if not frames:
        raise ValueError('No verified frames supplied; an empty viewer is not a deliverable')
    seen = set()
    receipt = []
    for frame in frames:
        frame_id = frame.get('id')
        if not frame_id or frame_id in seen:
            raise ValueError('Missing or duplicate illustrated step ID')
        seen.add(frame_id)
        path = (source.parent / frame['image']).resolve()
        if not path.is_relative_to(source.parent):
            raise ValueError('Frame is outside its source package')
        mime = mimetypes.guess_type(path.name)[0]
        if mime not in {'image/png', 'image/jpeg', 'image/webp'}:
            raise ValueError('Unsupported frame image format')
        content = path.read_bytes()
        receipt.append({'id':frame_id,'file':str(path.relative_to(source.parent)),
                        'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
        frame['image'] = 'data:' + mime + ';base64,' + base64.b64encode(content).decode('ascii')
    def safe_js(value):
        return value.replace('</script', '<\\/script').replace('</SCRIPT', '<\\/SCRIPT')
    html = (ROOT / 'index.html').read_text()
    html = html.replace('<link rel="stylesheet" href="style.css">', '<style>' + (ROOT/'style.css').read_text() + '</style>')
    payload = 'window.EMBODIED_TASK=' + json.dumps(data, ensure_ascii=False) + ';'
    html = html.replace('<script src="manifest.js"></script>', '<script>' + safe_js(payload) + '</script>')
    html = html.replace('<script src="player.js"></script>', '<script>' + safe_js((ROOT/'player.js').read_text()) + '</script>')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html)
    report = {'frames':len(frames),'image_integrity':receipt,'output_bytes':args.output.stat().st_size,
              'output_sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),
              'validation':'Packaging and file existence only; not browser, physics or robot validation'}
    args.output.with_suffix('.receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'frames':len(frames),'bytes':report['output_bytes']}))

if __name__ == '__main__':
    main()
