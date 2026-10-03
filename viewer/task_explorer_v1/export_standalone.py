#!/usr/bin/env python3
"""Inline local assets; embeds SVGs too, so the export has no local-file links."""
import argparse,pathlib,re,json
ROOT=pathlib.Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=pathlib.Path,default=ROOT.parent/'ScienceGym-Task-Explorer.html')
args=parser.parse_args()
page=(ROOT/'index.html').read_text()
route_count=sum(f['routes'] for f in json.loads((ROOT/'manifest.json').read_text())['families'])
page=page.replace('<link rel="stylesheet" href="styles.css">','<style>'+(ROOT/'styles.css').read_text()+'</style>')
for name in ['README.md','docs/ADAPTERS.md']:page=page.replace('href="'+name+'"','href="#standaloneGuide"')
page=page.replace('<footer>', '<details id="standaloneGuide"><summary>Offline guide and verification boundary</summary><div><p>Choose a family and branch, then click an operation. Search highlights matches without hiding route steps. Use Dependencies &amp; choices for declared partial orders and Acceptance &amp; unknowns for evaluator contracts.</p><p>Source scientific stages and authored robot handling remain distinct. Arrows indicate reference list order. Loops are unexpanded contracts; repeated IDs retain their occurrence index. Acquisition, data, cooling, EmVP and prismatic membership obligations do not imply unspecified chronology. Prismatic material/target and thickness/target nesting remains symbolic; null counts block expansion. EmVP cage conditions retain separate source routes, and comparison coverage never converts states or sites into independent specimens.</p><p>SVG overview downloads the embedded diagram for the selected family. Every original JSON link opens its pinned public ScienceGym task snapshot. Cooling retains six symbolic loop contracts, conditional receipt gates, unknown counts and required physical transfer instances. Mechanical views preserve typed forward/adjoint bindings, physical transfers, ring concurrency and conditional preparation. Numerical training is not physical self-updating, and ring torque is semi-experimental rather than directly measured. Proposals and source-missing gates retain their source-specific status. Assembly views preserve scoped granular/thermal dependency gates, symbolic repeats, actual sample/packing lineage and separate device ownership. Beaded exclusive preparation choices and typed loop bindings remain unselected templates. Source-section navigation counts do not create new experiments. Final materials views preserve Horn matched-map and numerical distinctions, ReMM source_complete=false with unread panels/movies, and cold-shape closed qualified hazardous services. Derived fits never become independent validation. Condition schedules, loops and sample counts remain symbolic. This file has no external runtime dependencies.</p><p>Verified: source-equality and structural tests, all CURRENT_ROUTE_COUNT route views in a mocked DOM, portable SVG rendering. Not verified: actual browser rendering, touch/responsive layout or scientific/robot execution. Browser file and localhost access were blocked by the environment policy.</p></div></details><footer>')
page=page.replace('CURRENT_ROUTE_COUNT',str(route_count))
svgs={f.stem:f.read_text() for f in (ROOT/'diagrams').glob('*.svg')}
def script_escape(s):return re.sub(r'</script',r'<\\/script',s,flags=re.I)
page=page.replace('<script src="app.js"></script>','<script>window.SCIENCEGYM_SVGS='+script_escape(json.dumps(svgs,ensure_ascii=False))+';</script><script src="app.js"></script>')
page=re.sub(r'<script src="([^"]+)"></script>',lambda m:'<script>'+script_escape((ROOT/m.group(1)).read_text())+'</script>',page)
out=args.output;out.write_text(page)
assert not re.search(r'(?:src|href)="(?!https?:|#)(?!\s*$)[^"]+"',page), 'Unresolved local link'
print(out, out.stat().st_size)
