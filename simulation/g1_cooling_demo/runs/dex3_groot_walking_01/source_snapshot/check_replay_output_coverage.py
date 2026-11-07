"""Regression for a sensor replay interrupted by a missing runtime dependency.

Zero error on a valid prefix must not certify the unexecuted suffix. Also reject
NaN/Inf and shape errors rather than allowing Python's max to hide invalid data.
"""
import json
import numpy as np
from verify_ftir_approach import motor_difference, all_motor_outputs_reproduced


def main():
    checks = {}
    for count in [0, 1, 67250, 116800]:
        checks[f'interrupted_after_{count}_rejected'] = not all_motor_outputs_reproduced(count, 116801, 0.)
    checks['empty_record_rejected'] = not all_motor_outputs_reproduced(0, 0, 0.)
    checks['complete_matching_record_accepted'] = bool(all_motor_outputs_reproduced(116801, 116801, 0.))
    checks['complete_mismatch_rejected'] = not all_motor_outputs_reproduced(116801, 116801, .001)
    checks['nan_error_rejected'] = not all_motor_outputs_reproduced(116801, 116801, float('nan'))
    for name, actual in [('nan', [0., np.nan]), ('infinite', [0., np.inf]),
                         ('short', [0.]), ('broadcast', [[0., 0.]])]:
        try:
            motor_difference(actual, [0., 0.])
        except ValueError:
            checks[name+'_output_rejected'] = True
        else:
            checks[name+'_output_rejected'] = False
    checks['finite_difference_preserved'] = abs(motor_difference([.1, -.3], [.1, -.2])-.1) < 1e-12
    result = dict(passed=all(checks.values()), checks=checks,
                  scope='Evaluator bookkeeping and malformed-output regression; no physical execution credit')
    print(json.dumps(result, indent=2))
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
