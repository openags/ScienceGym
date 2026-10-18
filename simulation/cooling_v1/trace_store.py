"""Lossless trace transport with individually GitHub-sized binary shards.

The original NPZ byte stream and its execution hash are preserved exactly.
Sharding is packaging, never resampling, quantization or a new execution.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import numpy as np


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def pack(directory,chunk_bytes=48*1024*1024):
    directory=Path(directory);source=directory/'physics_trace.npz'
    if chunk_bytes<=0:raise ValueError('Positive chunk size required')
    expected=json.loads((directory/'result.json').read_text())['artifacts_sha256']['physics_trace.npz']
    if sha(source)!=expected:raise ValueError('Execution trace hash mismatch')
    target=directory/'trace_parts';target.mkdir(exist_ok=True);rows=[];combined=hashlib.sha256()
    with source.open('rb') as stream:
        while block:=stream.read(chunk_bytes):
            name=f'trace_parts/part_{len(rows):04d}.bin';path=directory/name
            if path.exists() and path.read_bytes()!=block:raise ValueError('Refusing to replace a different trace shard')
            path.write_bytes(block);combined.update(block)
            rows.append(dict(path=name,bytes=len(block),sha256=hashlib.sha256(block).hexdigest()))
    if combined.hexdigest()!=expected:raise ValueError('Packaging changed the trace')
    manifest=dict(format='sciencegym.lossless_npz_shards.v1',original_file=source.name,
                  original_bytes=source.stat().st_size,original_sha256=expected,parts=rows,
                  lossless=True,resampled=False,packer_sha256=sha(Path(__file__)))
    (directory/'trace_parts.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def trace_bytes(directory,expected=None):
    directory=Path(directory);source=directory/'physics_trace.npz'
    if source.exists():
        content=source.read_bytes()
    else:
        manifest=json.loads((directory/'trace_parts.json').read_text())
        if manifest['format']!='sciencegym.lossless_npz_shards.v1':raise ValueError('Unknown trace archive format')
        if expected and manifest['original_sha256']!=expected:raise ValueError('Manifest is for a different execution')
        content=bytearray()
        for part in manifest['parts']:
            path=(directory/part['path']).resolve()
            if not path.is_relative_to(directory.resolve()):raise ValueError('Shard outside run directory')
            block=path.read_bytes()
            if len(block)!=part['bytes'] or hashlib.sha256(block).hexdigest()!=part['sha256']:raise ValueError('Trace shard damaged: '+part['path'])
            content.extend(block)
        if len(content)!=manifest['original_bytes']:raise ValueError('Trace archive length mismatch')
        expected=expected or manifest['original_sha256']
    if expected and hashlib.sha256(content).hexdigest()!=expected:raise ValueError('Trace content differs from execution hash')
    return content


def load_trace(directory,expected=None):
    with np.load(io.BytesIO(trace_bytes(directory,expected)),allow_pickle=False) as archive:
        return {key:archive[key] for key in archive.files}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory');parser.add_argument('--restore',action='store_true');args=parser.parse_args()
    if args.restore:
        directory=Path(args.directory);expected=json.loads((directory/'result.json').read_text())['artifacts_sha256']['physics_trace.npz']
        target=directory/'physics_trace.npz'
        if target.exists():raise ValueError('Original trace already exists')
        target.write_bytes(trace_bytes(directory,expected));print('Restored exact execution trace:',target)
    else:
        result=pack(args.directory);print('Lossless shards:',len(result['parts']),'original SHA-256:',result['original_sha256'])
