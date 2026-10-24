"""Transport tests for complete physics records, including damaged downloads."""
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from trace_store import pack,load_trace,sha


class TraceTransport(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.root=Path(self.temporary.name)
        self.arrays=dict(time=np.arange(113)*.005,qpos=np.random.default_rng(1).normal(size=(113,27)),
                         qvel=np.random.default_rng(2).normal(size=(113,25)),ctrl=np.zeros((113,8)))
        np.savez_compressed(self.root/'physics_trace.npz',**self.arrays)
        self.digest=sha(self.root/'physics_trace.npz')
        (self.root/'result.json').write_text(json.dumps(dict(artifacts_sha256={'physics_trace.npz':self.digest})))
        self.manifest=pack(self.root,1024)
        (self.root/'physics_trace.npz').unlink()

    def tearDown(self):self.temporary.cleanup()

    def test_checkout_restores_all_values_exactly(self):
        restored=load_trace(self.root,self.digest)
        self.assertGreater(len(self.manifest['parts']),1)
        for name,values in self.arrays.items():np.testing.assert_array_equal(restored[name],values)

    def test_wrong_execution_cannot_borrow_trace(self):
        with self.assertRaisesRegex(ValueError,'different execution'):load_trace(self.root,'0'*64)

    def test_corrupt_download_rejected(self):
        p=self.root/self.manifest['parts'][1]['path'];content=bytearray(p.read_bytes());content[10]^=1;p.write_bytes(content)
        with self.assertRaisesRegex(ValueError,'damaged'):load_trace(self.root,self.digest)

    def test_missing_shard_rejected(self):
        (self.root/self.manifest['parts'][0]['path']).unlink()
        with self.assertRaises(FileNotFoundError):load_trace(self.root,self.digest)


if __name__=='__main__':unittest.main()
