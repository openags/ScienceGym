"""Loose optional wood screws and supplied hex key, without installation credit."""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from geometry_tools import Geometry, HERE, ROOT, sha, write_json
from build_supplies import export_review, solid


def hex_key():
    # The manual supplies 0.05 inch nominal AF only. Actual AF, leg lengths and
    # bend radius below are selected fit hypotheses, not vendor tolerances.
    r=1.5
    path=cq.Wire.assembleEdges([
        cq.Edge.makeLine(cq.Vector(0,0,0),cq.Vector(0,0,12-r)),
        cq.Edge.makeThreePointArc(cq.Vector(0,0,12-r),cq.Vector(r-r/np.sqrt(2),0,12-r+r/np.sqrt(2)),cq.Vector(r,0,12)),
        cq.Edge.makeLine(cq.Vector(r,0,12),cq.Vector(35,0,12))])
    return cq.Workplane('XY').polygon(6,1.25/np.cos(np.pi/6)).sweep(path).val()


def build():
    g=Geometry()
    for i,y in enumerate([.06,.08]):
        shaft=cq.Solid.makeCylinder(3.175,70.2,cq.Vector(0,0,6)).fuse(cq.Solid.makeCone(.1,3.175,6))
        head=cq.Workplane('XY').polygon(6,11.1125/np.cos(np.pi/6)).extrude(4.5).val().translate((0,0,76.2))
        screw=shaft.fuse(head).rotate((0,0,0),(0,1,0),90).translate((0,y*1000,6.5))
        solid(g,'optional_wood_lag_'+str(i+1),screw,[180,188,195],metal=.8,role='source_kit_optional_hardware')
    pose=trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0]);pose[:3,3]=[.01,.12,.000625]
    key=hex_key().rotate((0,0,0),(1,0,0),90).translate((10,120,.625))
    solid(g,'supplied_0050_hex_key_candidate',key,[158,165,170],metal=.8,role='source_kit_tool')
    geometry=export_review(g,'weather_onset_swcf_loose_kit')
    refs=[Path(__file__),HERE/'wind_sensor_sources.json',HERE/'geometry_tools.py',HERE/'build_supplies.py']
    record=dict(schema_version=1,status='unaccepted_loose_kit_candidate',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        source_facts=dict(optional_lag_screws=2,lag_nominal_diameter_m=.00635,lag_underhead_length_m=.0762,
            supplied_hex_key_nominal_af_m=.00127),
        selected_dimensions=dict(lag_head_af_m=.0111125,lag_head_height_m=.0045,lag_tip_length_m=.006,
            key_actual_af_m=.00125,key_long_centreline_leg_m=.035,key_short_centreline_leg_m=.012,key_bend_radius_m=.0015),
        key_display_pose=pose.tolist(),
        inferences=['Wood screws use smooth major-diameter envelopes, a 6 mm tip and selected hex-head dimensions; no helical thread or wood engagement.',
            'Key is a continuous bent hexagonal bar. Leg lengths and bend are inferred; 1.25 mm actual AF is selected for the nominal 1.27 mm socket.',
            'Loose kit geometry is separate from the installed reference. It does not add laboratory inventory or claim tool reach.'],
        staged_in_lab=False,initial_stock_credit=False,installation_qualified=False,owner_acceptance=None)
    write_json(HERE/'wind_kit_assets.json',record);print(json.dumps(dict(parts=geometry['parts'])))


if __name__=='__main__':build()
