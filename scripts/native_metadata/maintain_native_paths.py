"""Bounded SDNA path-buffer cleanup; never modifies the source.

Uses the independently reviewed QHA SDNA parser. Only the four declared field
classes below can change. Other character arrays, including name tails, remain
byte-identical. Reports disclose offsets and hashes, not recovered raw contents.
A later Blender save invalidates this receipt and requires a fresh cleanup.
"""
from pathlib import Path
import argparse, hashlib, json, os, tempfile
import zstandard
from sdna_buffers import decoded, arrays, parse, sha

ALLOWLIST = frozenset({('FileSelectParams', 'dir'), ('FileSelectParams', 'file'),
                      ('Editing', 'act_imagedir'), ('RenderData', 'pic')})
UI_FIELDS = ALLOWLIST - {('RenderData', 'pic')}

def rewrite(data, render_replacements=None):
    fields, dna_sha = arrays(data)
    replacements = render_replacements or {}
    mutable = bytearray(data)
    changes, audited = [], []
    for f in fields:
        key = (f['declaring_struct'], f['base_name'])
        if key not in ALLOWLIST:
            continue
        v = data[f['start']:f['end']]
        nul = v.find(b'\0')
        if nul < 0:
            raise ValueError('Unterminated allowlisted C string: ' + f['field'])
        active = v[:nul]
        replacement = active
        reason = 'zero_post_nul_tail'
        if key in UI_FIELDS:
            replacement = b'' if key[1] == 'file' or not active else b'//'
            if replacement != active:
                reason = 'reset_inactive_ui_path'
        elif sha(active) in replacements:
            replacement = replacements[sha(active)].encode('utf-8')
            reason = 'portable_render_output_path'
        if key == ('RenderData', 'pic') and replacement and not replacement.startswith(b'//'):
            raise ValueError('Unapproved non-portable render output path: ' + f['field'])
        if len(replacement) >= f['size'] or b'\0' in replacement:
            raise ValueError('Invalid fixed-buffer replacement')
        canonical = replacement + bytes(f['size'] - len(replacement))
        audit = {'field': f['field'], 'declaring_struct': key[0], 'base_name': key[1],
                 'start': f['start'], 'end': f['end'], 'size': f['size'],
                 'before_buffer_sha256': sha(v), 'after_buffer_sha256': sha(canonical),
                 'before_active_sha256': sha(active), 'after_active_sha256': sha(replacement),
                 'active_value_unchanged': replacement == active,
                 'post_nul_bytes_all_zero': True}
        audited.append(audit)
        if canonical != v:
            mutable[f['start']:f['end']] = canonical
            changes.append(dict(audit, action=reason,
                                previous_nonzero_tail_count=sum(x != 0 for x in v[nul + 1:]),
                                changed_byte_count=sum(a != b for a, b in zip(v, canonical)),
                                complete_fixed_width_buffer_written=True))
    output = bytes(mutable)
    masked_before, masked_after = bytearray(data), bytearray(output)
    for f in changes:
        masked_before[f['start']:f['end']] = bytes(f['size'])
        masked_after[f['start']:f['end']] = bytes(f['size'])
    if masked_before != masked_after:
        raise AssertionError('Bytes outside changed allowlisted buffers differ')
    if parse(output)[2] != dna_sha:
        raise AssertionError('SDNA changed')
    return output, {'fixed_char_arrays_scanned': len(fields), 'sdna_sha256': dna_sha,
                    'audited_path_buffers': audited, 'changed_fixed_buffers': changes,
                    'changed_buffer_count': len(changes),
                    'changed_byte_count': sum(f['changed_byte_count'] for f in changes),
                    'bytes_outside_changed_allowlisted_buffers_identical': True,
                    'masked_bytes_sha256': sha(masked_after), 'decompressed_bytes_preserved': True}

def clean(source, destination, expected_sha256, render_replacements=None):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError('Source and destination must be different')
    if destination.exists():
        raise FileExistsError('Refusing to overwrite existing candidate output')
    raw, data = decoded(source)
    if sha(raw) != expected_sha256:
        raise ValueError('Source hash does not match reviewed baseline')
    output, report = rewrite(data, render_replacements)
    twice, check = rewrite(output)
    if twice != output or check['changed_buffer_count']:
        raise AssertionError('Cleanup is not idempotent')
    encoded = zstandard.ZstdCompressor(level=19, write_checksum=True).compress(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, prefix='.metadata-', delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(encoded)
    try:
        if decoded(temporary)[1] != output:
            raise AssertionError('Native-compatible encoded bytes do not round trip')
        # Atomic no-clobber publication within the same destination directory.
        os.link(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    if source.read_bytes() != raw:
        raise AssertionError('Source changed during cleanup')
    return dict(report, schema='sciencegym.native_path_maintenance.v1', passed=True,
                source_sha256=sha(raw), destination_sha256=sha(encoded),
                source_bytes=len(raw), destination_bytes=len(encoded),
                source_decompressed_sha256=sha(data), destination_decompressed_sha256=sha(output),
                raw_buffer_contents_disclosed=False, idempotence_passed=True,
                compression='native-compatible zstd, deterministic level 19 with checksum',
                qualification_changed=False,
                scope='Four schema-identified path-buffer classes only; other string and opaque buffers untouched')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source'); p.add_argument('destination'); p.add_argument('--expected-sha256', required=True)
    p.add_argument('--policy'); p.add_argument('--report', required=True)
    a = p.parse_args()
    source, destination, report_path = Path(a.source), Path(a.destination), Path(a.report)
    if report_path.resolve() in {source.resolve(), destination.resolve()}:
        raise ValueError('Report must not alias source or destination')
    if report_path.exists() or report_path.is_symlink():
        raise FileExistsError('Refusing to overwrite an existing report or symlink')
    if not report_path.parent.is_dir():
        raise ValueError('Report parent directory must already exist')
    policy = json.loads(Path(a.policy).read_text()) if a.policy else {}
    result = clean(source, destination, a.expected_sha256, policy.get('render_replacements', {}))
    # Exclusive creation also prevents a late-created report from being replaced.
    with report_path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('passed', 'changed_buffer_count', 'changed_byte_count', 'destination_sha256')}))

if __name__ == '__main__':
    main()
