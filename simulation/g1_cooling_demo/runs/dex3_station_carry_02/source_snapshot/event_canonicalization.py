"""Canonicalize only the unordered collision-pair set in planning metadata.

Event order, all numbers, geometry names, duplicate entries, motion paths and
every other list remain significant. This does not normalize physical traces.
"""
from copy import deepcopy


def canonical_events(events):
    result=deepcopy(events)
    if not isinstance(result,list):raise ValueError('Events must be an ordered list')
    for event in result:
        if not isinstance(event,dict) or event.get('state')!='observed_geometry_path_planned':continue
        baseline=event.get('solution',{}).get('baseline',{})
        if 'self_intersections' not in baseline:continue
        pairs=baseline['self_intersections']
        if (not isinstance(pairs,list) or any(not isinstance(p,list) or len(p)!=2
                or not all(isinstance(n,str) for n in p) for p in pairs)):
            raise ValueError('Invalid collision-pair list')
        baseline['self_intersections']=sorted(sorted(p) for p in pairs)
    return result
