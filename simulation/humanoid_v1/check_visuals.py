"""Check the recorded movie, mesh provenance and actual localhost browser UI.

Requires Playwright plus a Chromium executable; does not grant physics credit.
"""
import argparse
import json
from pathlib import Path
import imageio.v2 as imageio
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
from world import HERE, ASSET, sha


def check(base_url, chromium):
    directory = HERE / 'runs/nominal'
    manifest = json.loads((directory / 'playback_manifest.json').read_text())
    preview = json.loads((ASSET / 'preview_receipt.json').read_text())
    movie = directory / manifest['video']
    rows = []
    def record(name, passed, **values):
        rows.append(dict(name=name, passed=bool(passed), **values))
    record('movie_source_identity', sha(movie) == manifest['video_sha256']
           and sha(directory / 'result.json') == manifest['result_sha256']
           and sha(directory / 'verification.json') == manifest['verification_sha256']
           and sha(HERE / 'render_foundation.py') == manifest['renderer_sha256'])
    reader = imageio.get_reader(movie)
    metadata = reader.get_meta_data(); count = 0; last = None
    for frame in reader: count += 1; last = frame
    reader.close()
    record('all_video_frames_decode', count == manifest['frames'] == 401
           and metadata['fps'] == manifest['fps'] == 20,
           frames=count, fps=metadata['fps'], duration_s=metadata['duration'])
    terminal_error = float(np.mean(abs(last.astype(float) - np.asarray(Image.open(directory / 'playback/last.png')).astype(float))))
    with np.load(directory / 'physics_trace.npz') as trace:
        record('video_covers_initial_and_terminal_states', manifest['terminal_state_included']
               and manifest['source_frame_indices'][0] == 0
               and manifest['source_frame_indices'][-1] == len(trace['time']) - 1
               and abs(metadata['duration'] - (trace['time'][-1] + 1 / metadata['fps'])) < .001
               and terminal_error < 8., terminal_frame_mean_pixel_error=terminal_error)
    record('glb_has_exact_record_and_source', preview['trace_sha256'] == sha(directory / 'physics_trace.npz')
           and preview['result_sha256'] == sha(directory / 'result.json')
           and preview['source_sha256'] == sha(ASSET / 'SOURCE.json')
           and preview['glb_sha256'] == sha(ASSET / 'geometry/h2_settled.glb')
           and preview['visual_meshes'] == 32 and preview['hand_model_present'] is False)
    errors = []; failed_requests = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium, args=[
            '--no-sandbox', '--disable-dev-shm-usage', '--use-gl=angle',
            '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        page = browser.new_page(viewport={'width': 1440, 'height': 1100})
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('response', lambda response: failed_requests.append(dict(url=response.url, status=response.status)) if response.status >= 400 else None)
        page.goto(base_url.rstrip('/') + '/simulation/humanoid_v1/index.html')
        page.wait_for_function('document.documentElement.dataset.modelLoaded === "true" && document.documentElement.dataset.dataLoaded === "true"')
        page.wait_for_function('document.querySelector("video").readyState >= 2')
        record('status_and_scope_visible', page.locator('#suite-status').inner_text() == '通过（仅本体）'
               and page.locator('#checks tr').count() == 5 and page.locator('#missing li').count() == 5
               and '尚未取得' in page.locator('.notice').inner_text())
        video = page.locator('video')
        seeks = []
        for index, expected in [(0, 0), (2, 10), (4, 20)]:
            page.locator('#events button').nth(index).click()
            page.wait_for_function('(at) => !document.querySelector("video").seeking && Math.abs(document.querySelector("video").currentTime-at)<.01', arg=expected)
            seeks.append(video.evaluate('(v)=>v.currentTime'))
        record('event_seeking', np.allclose(seeks, [0, 10, 20], atol=.001, rtol=0), positions_s=seeks)
        video.evaluate('(v)=>{v.currentTime=10;v.muted=true;return v.play()}')
        page.wait_for_function('document.querySelector("video").currentTime>10.2')
        video.evaluate('(v)=>v.pause()')
        record('video_really_plays', video.evaluate('(v)=>v.currentTime') > 10.2)
        webgl = page.locator('#model canvas').evaluate('(c)=>({width:c.width,height:c.height,valid:!!c.getContext("webgl2")})')
        record('three_dimensional_model_renders', webgl['valid'] and webgl['width'] > 100 and webgl['height'] > 100, **webgl)
        page.locator('#reset-view').click()
        page.screenshot(path=str(HERE / 'browser_desktop.png'), full_page=True)
        page.set_viewport_size({'width': 390, 'height': 844})
        page.wait_for_timeout(200)
        overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth')
        page.screenshot(path=str(HERE / 'browser_mobile.png'), full_page=True)
        record('mobile_layout', not overflow, horizontal_overflow=overflow)
        record('browser_without_errors', not errors and not failed_requests and not page.locator('#error').inner_text(),
               javascript_errors=errors, failed_requests=failed_requests)
        browser.close()
    report = dict(passed=all(row['passed'] for row in rows), checks=rows,
                  page_sha256=sha(HERE / 'index.html'), checker_sha256=sha(Path(__file__)),
                  playback_manifest_sha256=sha(directory / 'playback_manifest.json'),
                  foundation_verification_sha256=sha(HERE / 'FOUNDATION_VERIFICATION.json'),
                  scope='Movie, source mesh and browser checks only; no manipulation acceptance')
    (HERE / 'VISUAL_VERIFICATION.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8769')
    parser.add_argument('--chromium', required=True)
    args = parser.parse_args()
    raise SystemExit(0 if check(args.base_url, args.chromium) else 1)
