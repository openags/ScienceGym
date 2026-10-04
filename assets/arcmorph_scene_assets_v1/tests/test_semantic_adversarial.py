"""Independent negative spot checks; synthetic record consistency only.

Author-provided valid fixtures are reused. Mutations and assertions were authored
by the independent reviewer. No real devices, evidence, or qualification.
"""
import sys
from pathlib import Path
from dataclasses import replace
import unittest
P = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(P), str(P/'tests')]
import semantic_controls as sc
import test_semantic_controls as authored

class IndependentAdversarialTests(unittest.TestCase):
    def setUp(self): self.h = authored.SemanticControlTests()
    def held(self, fn, *args, **kwargs):
        with self.assertRaises(sc.SemanticHold): fn(*args, **kwargs)
    def test_blank_attachment_identity(self):
        for bad in ('', '  ', None):
            with self.subTest(bad=bad):
                m = sc.Mount('FIX','REV','rigid_metrology','LEASE',(bad,))
                self.held(sc.mount_candidate,self.h.baseline(),m,evidence_id='NEW',interface_qualified=True)
    def test_capture_token_requires_rigid_metrology_mount(self):
        for state in (self.h.mounted('corner'),self.h.loaded(),self.h.mounted('rigid_demo')):
            with self.subTest(kind=state.mount.kind,load=state.load_state):
                self.held(sc.token_candidate,state,self.h.calibration(),self.h.context(),**self.h.token_args())
    def test_pair_rejects_substituted_corner_membership(self):
        args=list(self.h.pair_inputs()); args[0]=replace(args[0],mount=replace(args[0].mount,kind='corner'))
        self.held(sc.pair_candidate,*args,now_tick=13)
    def test_corner_load_requires_nonempty_job_identity(self):
        for bad in (None,'','  '):
            with self.subTest(bad=bad):
                state=self.h.mounted('corner'); state=replace(state,mount=replace(state.mount,job_id=bad))
                self.held(sc.qualitative_load_candidate,state,replace(self.h.load_job(),job_id=bad))
    def test_two_cameras_require_distinct_lens_identities(self):
        ctx=self.h.context(); ctx=replace(ctx,cameras=(ctx.cameras[0],replace(ctx.cameras[1],lens_id=ctx.cameras[0].lens_id)))
        self.held(sc.check_calibration,replace(self.h.calibration(),context=ctx),ctx,10)
    def test_prepared_qualification_identity_is_immutable(self):
        for field,value in (('dimensional_spec_revision','CHANGED'),('evidence_id','CHANGED')):
            with self.subTest(field=field):
                self.held(sc.record_edge_candidate,self.h.prepared(),replace(self.h.qualification(),**{field:value}),self.h.edge())
    def test_transport_requires_literal_support_confirmation(self):
        for field in ('supported','carrier_retained'):
            for value in ('unknown',1):
                with self.subTest(field=field,value=value):
                    self.held(sc.transport_candidate,replace(self.h.baseline(),**{field:value}),source='stock',destination='inspection',carrier_id='EXAMPLE-C1',custody_receipt_id='NEW')
    def test_nonfinite_boolean_or_negative_dimensions_hold(self):
        for value in (float('nan'),float('inf'),True,-1):
            with self.subTest(value=value): self.held(self.h.fabricate,self.h.stock(),replace(self.h.qualification(),sheet_dimension_mm=value))
    def test_nonfinite_boolean_or_negative_loads_hold(self):
        for value in (float('nan'),float('inf'),True,-1):
            with self.subTest(value=value): self.held(sc.qualitative_load_candidate,self.h.mounted('corner'),replace(self.h.load_job(),magnitude=value))
    def test_invalid_uniformity_tolerance_holds(self):
        for value in (float('nan'),float('inf'),True,-1):
            with self.subTest(value=value):
                kw=self.h.token_args(); kw['tolerance']=value
                self.held(sc.token_candidate,self.h.mounted(),self.h.calibration(),self.h.context(),**kw)
    def test_unknown_quality_holds(self):
        args=list(self.h.pair_inputs()); args[4]=replace(args[4],quality_accepted=None)
        self.held(sc.pair_candidate,*args,now_tick=13)
    def test_boolean_token_expiry_holds(self):
        kw=self.h.token_args();kw['expires_at_tick']=True
        self.held(sc.token_candidate,self.h.mounted(),self.h.calibration(),self.h.context(),**kw)
    def test_actor_view_rejects_nonfinite_target(self):
        for value in (float('nan'),float('inf'),True):
            with self.subTest(value=value): self.held(sc.actor_observation,self.h.stock(),requested_target_height=value)
if __name__=='__main__': unittest.main()
