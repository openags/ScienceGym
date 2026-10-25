"""Fetch pinned official CAD into an ignored local cache; never execute it."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import ssl
import urllib.request

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(path, entry):
    if path.stat().st_size != entry['bytes'] or sha(path) != entry['sha256']:
        raise ValueError('Pinned source mismatch; no version substitution: ' + str(path))


def fetch(entry, source_directory=None):
    target = HERE / entry['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        verify(target, entry)
        return 'verified cache'
    temporary = target.with_suffix(target.suffix + '.part')
    if source_directory:
        source = source_directory / target.name
        verify(source, entry)
        shutil.copyfile(source, temporary)
    else:
        # Interrupted downloads can be resumed. A changed upstream file is never
        # accepted just because the server returns a successful HTTP status.
        offset = temporary.stat().st_size if temporary.exists() else 0
        headers = {'User-Agent': 'ScienceGym asset source retrieval'}
        if offset:
            headers['Range'] = f'bytes={offset}-'
        context = ssl.create_default_context(cafile='/etc/ssl/certs/ca-certificates.crt')
        request = urllib.request.Request(entry['url'], headers=headers)
        with urllib.request.urlopen(request, context=context, timeout=30) as response:
            if response.status == 206:
                if not response.headers.get('Content-Range', '').startswith(f'bytes {offset}-'):
                    raise ValueError('Unexpected source download range')
                mode = 'ab'
            else:
                mode = 'wb'
            with temporary.open(mode) as output:
                while chunk := response.read(128 * 1024):
                    output.write(chunk)
    verify(temporary, entry)
    temporary.replace(target)
    return 'downloaded and verified' if source_directory is None else 'copied verified source'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--from-directory', type=Path, help='Reuse already inspected exact source files')
    args = parser.parse_args()
    source = json.loads((HERE / 'sources.json').read_text())
    for entry in source['files']:
        print(entry['path'] + ': ' + fetch(entry, args.from_directory), flush=True)


if __name__ == '__main__':
    main()
