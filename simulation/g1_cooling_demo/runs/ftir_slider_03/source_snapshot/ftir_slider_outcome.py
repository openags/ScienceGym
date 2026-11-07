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
