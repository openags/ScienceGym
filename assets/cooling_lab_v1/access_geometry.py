"""Obstacle boxes for stationary access; routes retain whole furniture volumes.

An open rack is represented by every shelf and upright, rather than a filled
storage envelope. Stock already on those shelves remains a separate obstacle.
The target device itself is excluded by the caller, as in other instrument
access checks; this does not qualify hand contact inside the device.
"""
import numpy as np


def access_obstacles(scene):
    result=[]
    floor_assets={a['station']:a['id'] for a in scene['assets']}
    parts=scene['architecture']['part_records']
    for obstacle in scene['obstacles']:
        identity=obstacle['id']
        if obstacle['role']=='storage':
            structure=[p for p in parts if p['id'].startswith(identity+'_upright_') or p['id'].startswith(identity+'_shelf_')]
            assert len(structure)==9,identity
            result.extend((p['id'],np.array(p['bounds_m'])) for p in structure)
        elif obstacle['role'] in ['ordinary_movable_floor_asset','selected_machine_occupied_volume']:
            result.append((floor_assets[identity],np.array(obstacle['bounds_m'])))
        else:
            result.append((identity,np.array(obstacle['bounds_m'])))
    result.extend((c['id'],np.array(c['bounds_m'])) for c in scene['authored_components'] if c.get('check_separation'))
    return result
