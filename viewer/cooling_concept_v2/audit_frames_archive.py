"""Package exact exports or trajectories in GitHub-sized binary chunks."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):value.update(data)
    return value.hexdigest()


def verify(folder,manifest,output=None):
    total=hashlib.sha256();size=0
    for part in manifest['chunks']:
        if Path(part['file']).name!=part['file']:raise ValueError('Unsafe chunk filename')
        path=folder/part['file']
        if path.stat().st_size!=part['size_bytes']:raise ValueError('Chunk size mismatch: '+str(path))
        if digest(path)!=part['sha256']:raise ValueError('Chunk hash mismatch: '+str(path))
        with path.open('rb') as stream:
            for data in iter(lambda:stream.read(1024*1024),b''):
                total.update(data);size+=len(data)
                if output is not None:output.write(data)
    if size!=manifest['size_bytes'] or total.hexdigest()!=manifest['sha256']:
        raise ValueError('Combined artifact does not match its manifest')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path)
    parser.add_argument('--restore',action='store_true')
    parser.add_argument('--source-file',default='frames.jsonl.gz')
    parser.add_argument('--manifest-file',default='frames_archive.json')
    parser.add_argument('--expected-sha256')
    parser.add_argument('--chunk-mib',type=int,default=48);args=parser.parse_args()
    for name in [args.source_file,args.manifest_file]:
        if Path(name).name!=name or name in {'','.','..'}:raise ValueError('Archive names must be plain filenames')
    folder=args.folder;source=folder/args.source_file;archive=folder/args.manifest_file
    if args.restore:
        manifest=json.loads(archive.read_text())
        if manifest['source_file']!=source.name:raise ValueError('Manifest names a different artifact')
        if source.exists():
            if digest(source)!=manifest['sha256']:raise ValueError('Existing artifact hash mismatch')
            verify(folder,manifest)
        else:
            temporary=source.with_name(source.name+'.restoring')
            with temporary.open('xb') as stream:verify(folder,manifest,stream)
            temporary.replace(source)
        print('Exact archive verified:',source,flush=True);return
    expected=args.expected_sha256
    if expected is None:
        if args.source_file!='frames.jsonl.gz':raise ValueError('An expected SHA-256 is required for a generic artifact')
        expected=json.loads((folder/'export.json').read_text())['compressed_frames_sha256']
    if len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected):raise ValueError('Invalid SHA-256')
    if digest(source)!=expected:raise ValueError('Source does not match the expected SHA-256')
    if not 1<=args.chunk_mib<=90:raise ValueError('Chunk size must be 1–90 MiB')
    chunks=[]
    with source.open('rb') as stream:
        while data:=stream.read(args.chunk_mib*1024*1024):
            path=folder/(source.name+f'.part{len(chunks):03d}')
            if path.exists():
                if path.read_bytes()!=data:raise ValueError('Existing chunk differs: '+str(path))
            else:path.write_bytes(data)
            chunks.append(dict(file=path.name,size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    command=['python','viewer/cooling_concept_v2/audit_frames_archive.py',str(folder),'--restore']
    if args.source_file!='frames.jsonl.gz':command.extend(['--source-file',args.source_file])
    if args.manifest_file!='frames_archive.json':command.extend(['--manifest-file',args.manifest_file])
    import shlex
    manifest=dict(scope=__doc__,source_file=source.name,size_bytes=source.stat().st_size,
        sha256=expected,chunks=chunks,restore_command=shlex.join(command),restore_argv=command)
    verify(folder,manifest)
    archive.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(chunks=len(chunks),bytes=manifest['size_bytes'],exact_combined_sha256=expected)),flush=True)


if __name__=='__main__':main()
