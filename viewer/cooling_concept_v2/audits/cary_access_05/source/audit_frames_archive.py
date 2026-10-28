"""Package large exact frame exports in GitHub-sized, lossless binary chunks."""
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
        assert Path(part['file']).name==part['file']
        path=folder/part['file'];assert path.stat().st_size==part['size_bytes']
        assert digest(path)==part['sha256'],path
        with path.open('rb') as stream:
            for data in iter(lambda:stream.read(1024*1024),b''):
                total.update(data);size+=len(data)
                if output is not None:output.write(data)
    assert size==manifest['size_bytes'] and total.hexdigest()==manifest['sha256']


def main():
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path)
    parser.add_argument('--restore',action='store_true')
    parser.add_argument('--chunk-mib',type=int,default=48);args=parser.parse_args()
    folder=args.folder;source=folder/'frames.jsonl.gz';archive=folder/'frames_archive.json'
    if args.restore:
        manifest=json.loads(archive.read_text())
        if source.exists():
            assert digest(source)==manifest['sha256'];verify(folder,manifest)
        else:
            temporary=source.with_name(source.name+'.restoring')
            with temporary.open('xb') as stream:verify(folder,manifest,stream)
            temporary.replace(source)
        print('Exact frame archive verified:',source,flush=True);return
    expected=json.loads((folder/'export.json').read_text())['compressed_frames_sha256']
    assert digest(source)==expected
    assert 1<=args.chunk_mib<=90
    chunks=[]
    with source.open('rb') as stream:
        while data:=stream.read(args.chunk_mib*1024*1024):
            path=folder/(source.name+f'.part{len(chunks):03d}')
            if path.exists():assert path.read_bytes()==data
            else:path.write_bytes(data)
            chunks.append(dict(file=path.name,size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    manifest=dict(scope=__doc__,source_file=source.name,size_bytes=source.stat().st_size,
        sha256=expected,chunks=chunks,restore_command='python viewer/cooling_concept_v2/audit_frames_archive.py '+str(folder)+' --restore')
    verify(folder,manifest)
    archive.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(chunks=len(chunks),bytes=manifest['size_bytes'],exact_combined_sha256=expected)),flush=True)


if __name__=='__main__':main()
