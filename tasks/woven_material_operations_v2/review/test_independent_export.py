"""Independent adversarial export review using fresh temporary roots and ZIPs.

The fixed legal inventory is independently enumerated; no author archive-builder
or test helper supplies expected archive bytes or mutation outcomes.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import struct
import sys
import tempfile
import unittest
import warnings
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
spec=importlib.util.spec_from_file_location('woven_independent_export_verifier',ROOT/'tests/verify_export.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
INVENTORY=set('''EXPORT_SCOPE.md README.md RELEASE_BOUNDARY.json STATUS.json TASK_DESIGN.md VERIFICATION.json adversarial_cases.json agent_visible.json analysis_contracts.json asset_binding_plan.json branches.json control_packages.json coverage_matrix.json design_assumptions.json episode_input_contract.json evaluator_reference.json evidence_map.json lifecycle_contract.json lineage_contract.json material_cards.json mock_contract.json nonmanual_scope.json operations.json preparation_routes.json provenance.json source_access_audit.json source_conflicts.json source_outcomes.json station_contracts.json transport_routes.json unknown_parameters.json tests/contract.py tests/test_contract.py tests/test_export.py tests/verify_export.py tests/verify_package.py review/INDEPENDENT_REVIEW.json review/INDEPENDENT_REVIEW.md review/test_independent_contract.py review/test_independent_export.py'''.split())

class IndependentExport(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.root=self.base/'original';self.root.mkdir()
        for name in INVENTORY:
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
        if (ROOT/'EXPORT_ALLOWLIST.json').exists():self.manifest=json.loads((ROOT/'EXPORT_ALLOWLIST.json').read_text())
        else:self.manifest=dict(schema_version='woven_material_export.v1',actor_visible_allowlist=['agent_visible.json'],all_other_files_are_evaluator_audit_only=True,member_count_including_manifest=41)
        self.manifest['files']=[dict(path=name,bytes=len((self.root/name).read_bytes()),sha256=hashlib.sha256((self.root/name).read_bytes()).hexdigest()) for name in sorted(INVENTORY)]
        self.save_manifest()
    def save_manifest(self):(self.root/'EXPORT_ALLOWLIST.json').write_text(json.dumps(self.manifest,sort_keys=True,indent=2)+'\n')
    def archive(self,path=None,addition=None):
        path=path or self.base/'candidate.zip'
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for name in sorted(INVENTORY|{'EXPORT_ALLOWLIST.json'}):z.writestr(name,(self.root/name).read_bytes())
            if addition:addition(z)
        return path
    def rejected(self):self.assertTrue(v.verify(self.root))
    def test_independent_inventory_exact_root_and_archive(self):
        self.assertEqual(len(INVENTORY),40);self.assertEqual(set(v.EXPECTED_FILES),INVENTORY);self.assertEqual(v.verify(self.root),[]);self.assertEqual(v.verify(self.root,self.archive()),[])
    def test_unknown_source_or_binary_file(self):
        for name,data in [('paper.xml',b'<article>blocked</article>'),('source.pdf',b'%PDF-1.7'),('source.npy',b'\x93NUMPY\0')]:
            p=self.root/name;p.write_bytes(data)
            with self.subTest(name=name):self.rejected()
            p.unlink()
    def test_missing_or_mutated_known_file(self):
        p=self.root/'README.md';original=p.read_bytes();p.write_bytes(original+b' changed');self.rejected();p.unlink();self.rejected()
    def test_binary_known_file_rehashed_is_rejected(self):
        p=self.root/'README.md';p.write_bytes(b'\xff\x00\xfe');row=next(x for x in self.manifest['files'] if x['path']=='README.md');row.update(bytes=3,sha256=hashlib.sha256(p.read_bytes()).hexdigest());self.save_manifest();self.rejected()
    def test_symlink_known_file_and_extra_symlink(self):
        p=self.root/'README.md';p.unlink();p.symlink_to(ROOT/'README.md');self.rejected();p.unlink();shutil.copyfile(ROOT/'README.md',p);(self.root/'extra-link').symlink_to(ROOT/'README.md');self.rejected()
    def test_nonregular_fifo_rejected_without_read(self):
        os.mkfifo(self.root/'not-a-file');self.rejected()
    def test_duplicate_or_extra_manifest_row(self):
        self.manifest['files'].append(dict(self.manifest['files'][0]));self.save_manifest();self.rejected();self.manifest['files'].pop();self.manifest['files'][0]['unreviewed_text']='forbidden';self.save_manifest();self.rejected()
    def test_manifest_unsafe_paths(self):
        row=self.manifest['files'][0];old=row['path']
        for name in ('../source','/absolute','x/../secret','x//y','./README.md','x\\y','x:y','.hidden','x/.hidden','x/','',1,None):
            row['path']=name;self.save_manifest()
            with self.subTest(name=name):self.rejected()
        row['path']=old
    def test_manifest_invalid_hash_size(self):
        row=self.manifest['files'][0];original=dict(row)
        for key,value in [('bytes',True),('bytes',-1),('bytes',1.0),('sha256','0'*63),('sha256','A'*64),('sha256',None)]:
            row.clear();row.update(original);row[key]=value;self.save_manifest()
            with self.subTest(key=key,value=value):self.rejected()
    def test_manifest_actor_boundary_mutations(self):
        original=json.loads(json.dumps(self.manifest))
        for key,value in [('actor_visible_allowlist',['agent_visible.json','source_outcomes.json']),('actor_visible_allowlist',[]),('all_other_files_are_evaluator_audit_only',False),('member_count_including_manifest',True),('member_count_including_manifest',42),('schema_version','untrusted-schema')]:
            self.manifest=json.loads(json.dumps(original));self.manifest[key]=value;self.save_manifest()
            with self.subTest(key=key,value=value):self.rejected()
    def test_unknown_top_level_manifest_field_rejected(self):
        self.manifest['unreviewed_source_extract']='Unreviewed source material cannot be an extra manifest field';self.save_manifest();self.rejected()
    def test_duplicate_json_key_and_nonfinite_manifest_rejected(self):
        p=self.root/'EXPORT_ALLOWLIST.json';text=p.read_text();p.write_text(text.rstrip()[:-1]+',"actor_visible_allowlist": ["source_outcomes.json"]}');self.rejected();p.write_text(text.replace('"member_count_including_manifest": 41','"member_count_including_manifest": NaN'));self.rejected()
    def test_archive_extra_traversal_or_duplicate_rejected(self):
        for name in ('extra.xml','../source.xml','/source.xml','README.md'):
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning);z=self.archive(addition=lambda archive:archive.writestr(name,b'unreviewed'))
            with self.subTest(name=name):self.assertTrue(v.verify(self.root,z))
    def test_archive_symlink_mode_rejected(self):
        path=self.base/'symlink.zip'
        with zipfile.ZipFile(path,'w') as z:
            for name in sorted(INVENTORY|{'EXPORT_ALLOWLIST.json'}):
                entry=zipfile.ZipInfo(name);entry.create_system=3;entry.external_attr=((stat.S_IFLNK|0o777) if name=='README.md' else (stat.S_IFREG|0o644))<<16;z.writestr(entry,(self.root/name).read_bytes())
        self.assertTrue(v.verify(self.root,path))
    def test_archive_payload_mutation_and_truncation_rejected(self):
        path=self.base/'mutated.zip'
        with zipfile.ZipFile(path,'w') as z:
            for name in sorted(INVENTORY|{'EXPORT_ALLOWLIST.json'}):z.writestr(name,b'changed' if name=='README.md' else (self.root/name).read_bytes())
        self.assertTrue(v.verify(self.root,path));path.write_bytes(path.read_bytes()[:20]);self.assertTrue(v.verify(self.root,path))
    def test_actor_projection_independent_of_hidden_reference_changes(self):
        actor=(self.root/'agent_visible.json').read_bytes();(self.root/'source_outcomes.json').write_text('{"hidden_sentinel":"not actor context"}');self.assertEqual((self.root/'agent_visible.json').read_bytes(),actor)
        for filename in ('evaluator_reference.json','RELEASE_BOUNDARY.json'):self.assertEqual(json.loads((self.root/filename).read_text())['actor_projection'],['agent_visible.json'])
        self.assertEqual(self.manifest['actor_visible_allowlist'],['agent_visible.json']);self.rejected()
    def test_archive_unused_deflate_payload_bytes_rejected(self):
        path=self.archive()
        with zipfile.ZipFile(path) as z:
            infos=z.infolist();start=z.start_dir
            target=next(i for i in infos if i.filename=='README.md')
        raw=bytearray(path.read_bytes())
        nlen,xlen=struct.unpack_from('<HH',raw,target.header_offset+26)
        insert=target.header_offset+30+nlen+xlen+target.compress_size
        hidden=b'Unlisted raw source bytes';size=len(hidden)
        raw[insert:insert]=hidden
        struct.pack_into('<I',raw,target.header_offset+18,target.compress_size+size)
        cursor=start+size
        for info in infos:
            header=struct.unpack_from('<4s6H3I5H2I',raw,cursor)
            if info.filename=='README.md':struct.pack_into('<I',raw,cursor+20,info.compress_size+size)
            if info.header_offset>=insert:struct.pack_into('<I',raw,cursor+42,info.header_offset+size)
            cursor+=46+header[10]+header[11]+header[12]
        struct.pack_into('<I',raw,cursor+16,start+size)
        path.write_bytes(raw)
        self.assertTrue(v.verify(self.root,path))

    def test_archive_unlisted_envelope_bytes_rejected(self):
        for kind in ('archive_comment','prefix','suffix','member_comment','member_extra'):
            path=self.base/(kind+'.zip')
            if kind in ('member_comment','member_extra'):
                with zipfile.ZipFile(path,'w') as z:
                    for name in sorted(INVENTORY|{'EXPORT_ALLOWLIST.json'}):
                        info=zipfile.ZipInfo(name)
                        if name=='README.md':
                            if kind=='member_comment':info.comment=b'Unreviewed source bytes'
                            else:
                                data=b'Unreviewed source bytes';info.extra=struct.pack('<HH',0x1234,len(data))+data
                        z.writestr(info,(self.root/name).read_bytes())
            else:
                self.archive(path=path)
                if kind=='archive_comment':
                    with zipfile.ZipFile(path,'a') as z:z.comment=b'Unreviewed source bytes'
                elif kind=='prefix':path.write_bytes(b'Unreviewed source bytes'+path.read_bytes())
                else:path.write_bytes(path.read_bytes()+b'Unreviewed source bytes')
            with self.subTest(kind=kind):self.assertTrue(v.verify(self.root,path))
if __name__=='__main__':unittest.main()
