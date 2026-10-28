"""Depth confirmation at a commanded slider position, without joint truth.

The target is a work-order distance along the public device-local slider axis.
It recenters the bounded CAD fit, without changing its image acceptance tests.
This is a development observer; it is not integrated into the push actor yet.
"""
import numpy as np

from ftir_slider_vision import SliderObservation


class SliderTargetObservation(SliderObservation):
    def __init__(self, model, data, prior_path, shape_path, target_m):
        if not np.isfinite(target_m) or not 0 <= target_m <= .104:
            raise ValueError('Slider observation target outside declared travel')
        super().__init__(model, data, prior_path, shape_path)
        self.target = float(target_m)
        self.center[1] += self.target
        self.bounds[:, 1] += self.target

    def observe(self, depth, key_observation):
        result = super().observe(depth, key_observation)
        result['target_slider_position_m'] = self.target
        if 'estimated_slider_offset_m' in result:
            result['estimated_slider_position_m'] = self.target+result['estimated_slider_offset_m']
            result['residual_to_target_m'] = result.pop('estimated_slider_offset_m')
        if result.get('reason') == 'grip_fit_or_closed_position_rejected':
            result['reason'] = 'grip_fit_or_target_position_rejected'
        return result


class SliderRangeObservation(SliderTargetObservation):
    """Development-only range check with closed-view bias and grip coverage.

    A cropped vertical grip edge alone cannot establish its sliding position.
    Require observed axial extent of at least half the public CAD grip width.
    The 1 mm interior guard does not alter the physical 65--75 mm requirement.
    """
    def __init__(self, model, data, prior_path, shape_path, closed_observations):
        if len(closed_observations) < 8:
            raise ValueError('At least eight accepted closed-grip observations required')
        recent = closed_observations[-8:]
        offsets = np.array([o.get('estimated_slider_offset_m', np.nan) for o in recent])
        if (not all(o.get('accepted') for o in recent) or not np.isfinite(offsets).all()
                or np.max(abs(offsets)) >= .002 or np.ptp(offsets) > .002):
            raise ValueError('Closed-grip observation baseline is inconsistent')
        super().__init__(model, data, prior_path, shape_path, .070)
        self.baseline = float(np.median(offsets))
        self.minimum_axial_span = float(.5*np.ptp(self.bounds[:, 1]))

    def observe(self, depth, key_observation):
        result = super().observe(depth, key_observation)
        result['original_target_gate_accepted'] = result['accepted']
        result['closed_observation_baseline_m'] = self.baseline
        result['minimum_observed_axial_span_m'] = self.minimum_axial_span
        result['development_guard_band_m'] = [.066, .074]
        if 'estimated_slider_position_m' not in result:
            return result
        corrected = result['estimated_slider_position_m']-self.baseline
        singular = result['fit_singular_values']
        geometry = (result['inliers'] >= 16 and result['inliers']/result['points'] >= .8
                    and result['observed_span_m'][0] > .030
                    and singular[-1] > .05*max(singular[0], 1e-12)
                    and abs(result['height_residual_m']) < .0008)
        coverage = result['observed_span_m'][1] >= self.minimum_axial_span
        position = .066 <= corrected <= .074
        result['baseline_corrected_position_m'] = corrected
        result['geometry_quality_accepted'] = bool(geometry)
        result['axial_coverage_accepted'] = bool(coverage)
        result['accepted'] = bool(geometry and coverage and position)
        result['reason'] = (None if result['accepted'] else 'insufficient_grip_axial_coverage'
                            if not coverage else 'grip_geometry_or_guard_band_rejected')
        return result
