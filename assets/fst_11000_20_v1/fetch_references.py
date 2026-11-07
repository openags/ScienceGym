"""Retrieve pinned external manufacturer references without redistributing them."""
import argparse
import hashlib
import json
from pathlib import Path
import ssl
import urllib.request


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--destination',type=Path,default=Path('/tmp/sciencegym-pilot-sources'))
    args=parser.parse_args();args.destination.mkdir(parents=True,exist_ok=True)
    revision=json.loads(Path(__file__).with_name('revision.json').read_text())
    files={'datasheet':'fst_11000_20_datasheet.pdf','photograph':'fst_11000_20_iso.jpg',
           'tip_sketch':'fst_11000_20_front.jpg'}
    certificates=Path('/etc/ssl/certs/ca-certificates.crt')
    context=ssl.create_default_context(cafile=str(certificates) if certificates.exists() else None)
    for role,name in files.items():
        path=args.destination/name;expected=revision['cached_reference_sha256'][name]
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==expected:
            print('Verified cached reference:',name);continue
        request=urllib.request.Request(revision['source_urls'][role],headers={'User-Agent':'ScienceGym source verification'})
        with urllib.request.urlopen(request,context=context,timeout=60) as response:data=response.read()
        if hashlib.sha256(data).hexdigest()!=expected:
            raise RuntimeError('Manufacturer reference changed; inspect it before updating the pin: '+name)
        path.write_bytes(data);print('Retrieved and verified:',name)


if __name__=='__main__':main()
