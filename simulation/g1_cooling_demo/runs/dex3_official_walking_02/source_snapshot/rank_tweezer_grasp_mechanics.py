"""Screen grasp leverage against the unchanged passive tool's linear stiffness.

This is a small-deflection design estimate with ideal contact loads. It neither
predicts slip nor qualifies force control, dynamic closure or specimen handling.
"""
import argparse
import json
from pathlib import Path

from evaluate_tool_actuation_recording import sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('fits', nargs='+', type=Path)
    args = parser.parse_args()
    base = Path(__file__).resolve().parents[2]
    source = base / 'assets/idealtek_aa_sa_t6_v1/revisions/passive_07/model_review.json'
    review = json.loads(source.read_text())
    modes = review['mode_discretization']
    initial_gap = review['unloaded_inner_tip_gap_m']

    def compliance(contact):
        if contact['side'] == 'heel':
            return 0.
        x = contact['point_source_m'][0]
        return sum(row['hi_m'] * max(0., row['hi_m'] - x) / row['hinge_stiffness_nm_rad']
                   for row in modes)

    candidates = []
    for path in args.fits:
        fit = json.loads(path.read_text())
        for index, candidate in enumerate(fit['candidates']):
            contacts = candidate['contacts']
            assert len(contacts) == 3
            c = [compliance(contact) for contact in contacts]
            per_thumb_force = c[0] + .5 * (c[1] + c[2])
            x = [contact['point_source_m'][0] for contact in contacts]
            candidates.append(dict(fit=str(path.resolve()), fit_sha256=sha(path), candidate_index=index,
                contact_x_m=x, contact_sides=[contact['side'] for contact in contacts],
                tip_compliance_per_finger_m_per_n=c,
                required_thumb_force_for_0p5mm_gap_n=(initial_gap - .0005) / per_thumb_force,
                estimated_gap_at_thumb_force_m={str(force): initial_gap - force * per_thumb_force
                                               for force in [1.2, 2.4, 3., 3.5]},
                opposing_force_moment_arm_error_m=x[0] - .5 * (x[1] + x[2])))
    candidates.sort(key=lambda row: row['required_thumb_force_for_0p5mm_gap_n'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    assert not args.output.exists()
    report = dict(scope=__doc__, stiffness_source_sha256=sha(source), script_sha256=sha(__file__),
        unloaded_gap_m=initial_gap, force_distribution=[1., .5, .5], candidates=candidates,
        geometry_material_and_runtime_limits_changed=False,
        qualified_grasp=False, qualified_tool_actuation=False)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    for path in args.fits:
        selected = [row for row in candidates if row['fit'] == str(path.resolve())]
        required = [row['required_thumb_force_for_0p5mm_gap_n'] for row in selected]
        print(json.dumps(dict(fit=str(path), candidates=len(selected),
            required_thumb_force_range_n=[min(required), max(required)] if required else None,
            candidates_below_4n=sum(force < 4. for force in required))), flush=True)


if __name__ == '__main__':
    main()
