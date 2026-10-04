"""Exact original-file and ZIP-envelope integrity; not authentication."""
from pathlib import Path,PurePosixPath
import hashlib,json,stat,struct,zipfile,zlib
from verify_package import read
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_FILES=tuple('''EXPORT_SCOPE.md README.md RELEASE_BOUNDARY.json STATUS.json TASK_DESIGN.md VERIFICATION.json adversarial_cases.json agent_visible.json analysis_contracts.json asset_binding_plan.json branches.json control_packages.json coverage_matrix.json design_assumptions.json episode_input_contract.json evaluator_reference.json evidence_map.json lifecycle_contract.json lineage_contract.json material_cards.json mock_contract.json nonmanual_scope.json operations.json preparation_routes.json provenance.json source_access_audit.json source_conflicts.json source_outcomes.json station_contracts.json transport_routes.json unknown_parameters.json tests/contract.py tests/test_contract.py tests/test_export.py tests/verify_export.py tests/verify_package.py review/INDEPENDENT_REVIEW.json review/INDEPENDENT_REVIEW.md review/test_independent_contract.py review/test_independent_export.py'''.split())
def sha(data):return hashlib.sha256(data).hexdigest()
def allowed_name(name):
    if type(name) is not str or not name:return False
    p=PurePosixPath(name);return not p.is_absolute() and str(p)==name and '..' not in p.parts and not any(x.startswith('.') for x in p.parts) and '\\' not in name and ':' not in name

def envelope_errors(data,z,expected_sizes):
    """Reject bytes outside exact local records, central records and bare EOCD."""
    errors=[];infos=z.infolist()
    if z.comment or any(i.comment or i.extra for i in infos):errors.append('ZIP comments/extra fields forbidden')
    cursor=0
    try:
        for info in sorted(infos,key=lambda x:x.header_offset):
            if info.header_offset!=cursor:errors.append('ZIP prefix/gap/overlap')
            h=struct.unpack_from('<4s5H3I2H',data,info.header_offset)
            sig,version,flags,method,tm,dt,crc,packed,unpacked,nlen,xlen=h
            if sig!=b'PK\x03\x04' or flags!=0 or xlen!=0 or method not in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED):errors.append('noncanonical local ZIP header')
            if (method,crc,packed,unpacked)!=(info.compress_type,info.CRC,info.compress_size,info.file_size):errors.append('local/central ZIP mismatch')
            name=data[info.header_offset+30:info.header_offset+30+nlen]
            if name!=info.filename.encode('utf-8'):errors.append('local ZIP filename mismatch')
            payload_start=info.header_offset+30+nlen+xlen
            cursor=payload_start+packed
            if info.filename not in expected_sizes or unpacked!=expected_sizes[info.filename]:
                errors.append('ZIP declared decoded size differs from allowed file')
            elif method==zipfile.ZIP_DEFLATED:
                decoder=zlib.decompressobj(-15)
                decoded=decoder.decompress(data[payload_start:cursor],unpacked+1)
                if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail or len(decoded)!=unpacked:
                    errors.append('ZIP DEFLATE stream has unused, incomplete or excess payload')
            elif method==zipfile.ZIP_STORED and packed!=unpacked:
                errors.append('stored ZIP size mismatch')
        if cursor!=z.start_dir:errors.append('ZIP bytes before central directory')
        start=cursor
        for info in infos:
            h=struct.unpack_from('<4s6H3I5H2I',data,cursor)
            if h[0]!=b'PK\x01\x02':errors.append('central ZIP signature')
            nlen,xlen,clen=h[10:13]
            if xlen or clen or h[3]!=0 or h[13]!=0:errors.append('central ZIP extra/comment/flags/disk')
            if data[cursor+46:cursor+46+nlen]!=info.filename.encode('utf-8') or h[16]!=info.header_offset:errors.append('central ZIP identity mismatch')
            cursor+=46+nlen+xlen+clen
        central_size=cursor-start
        end=struct.unpack_from('<4s4H2IH',data,cursor)
        if end!=(b'PK\x05\x06',0,0,len(infos),len(infos),central_size,start,0):errors.append('ZIP EOCD mismatch/comment')
        if cursor+22!=len(data):errors.append('ZIP trailing data')
    except (struct.error,UnicodeError,OverflowError,zlib.error):errors.append('invalid ZIP envelope')
    return errors

def verify(root=ROOT,archive=None):
    root=Path(root);errors=[]
    try:
        entries=list(root.rglob('*'))
        if root.is_symlink() or any(p.is_symlink() for p in entries):return ['symlink forbidden']
        if any(not (stat.S_ISREG(p.lstat().st_mode) or stat.S_ISDIR(p.lstat().st_mode)) for p in entries):return ['nonregular filesystem entry forbidden']
    except OSError as exc:return ['filesystem unreadable: '+str(exc)]
    try:m=read(root/'EXPORT_ALLOWLIST.json')
    except Exception as exc:return ['manifest unreadable: '+str(exc)]
    if type(m) is not dict or set(m)!={'schema_version','files','member_count_including_manifest','actor_visible_allowlist','all_other_files_are_evaluator_audit_only'} or m['schema_version']!='woven_material_export.v1':return ['manifest schema']
    rows=m['files']
    if type(rows) is not list or not all(type(r) is dict and set(r)=={'path','bytes','sha256'} for r in rows):return ['manifest row schema']
    names=[r['path'] for r in rows]
    if not names or not all(allowed_name(n) for n in names) or len(names)!=len(set(names)):return ['invalid allowlist names']
    if set(names)!=set(EXPECTED_FILES):errors.append('manifest differs from fixed original-file allowlist')
    if m['actor_visible_allowlist']!=['agent_visible.json'] or m['all_other_files_are_evaluator_audit_only'] is not True:errors.append('actor projection invalid')
    if type(m['member_count_including_manifest']) is not int or m['member_count_including_manifest']!=len(EXPECTED_FILES)+1:errors.append('manifest member count')
    expected=set(EXPECTED_FILES)|{'EXPORT_ALLOWLIST.json'};actual={p.relative_to(root).as_posix() for p in entries if p.is_file() and '__pycache__' not in p.parts}
    if actual!=expected:errors.append('package inventory differs: '+repr(sorted(actual^expected)))
    for row in rows:
        name=row['path']
        if name not in EXPECTED_FILES:continue
        if type(row['bytes']) is not int or row['bytes']<0 or type(row['sha256']) is not str or len(row['sha256'])!=64 or any(c not in '0123456789abcdef' for c in row['sha256']):errors.append('invalid manifest row '+name);continue
        p=root/name
        if not p.is_file():errors.append('missing '+name);continue
        data=p.read_bytes()
        if len(data)!=row['bytes'] or sha(data)!=row['sha256']:errors.append('content mismatch '+name)
        try:data.decode('utf-8')
        except UnicodeDecodeError:errors.append('non-UTF8 original file '+name)
    if archive is not None:
        try:
            data=Path(archive).read_bytes()
            with zipfile.ZipFile(archive) as z:
                zi=z.infolist();zn=[i.filename for i in zi]
                if len(zn)!=len(set(zn)) or set(zn)!=expected:errors.append('archive exact-member mismatch')
                errors.extend(envelope_errors(data,z,{name:(root/name).stat().st_size for name in expected if (root/name).is_file()}))
                for i in zi:
                    name=i.filename
                    if not allowed_name(name):errors.append('unsafe archive member');continue
                    mode=(i.external_attr>>16)&0o170000
                    if mode not in (0,stat.S_IFREG):errors.append('nonregular archive member '+name);continue
                    if name in expected:
                        expected_data=(root/name).read_bytes()
                        if i.file_size!=len(expected_data):errors.append('archive decoded size differs '+name)
                        elif z.read(i)!=expected_data:errors.append('archive bytes differ '+name)
        except (OSError,ValueError,KeyError,RuntimeError,zipfile.BadZipFile) as exc:errors.append('archive unreadable: '+str(exc))
    return errors
if __name__=='__main__':
    import sys
    errors=verify(archive=sys.argv[1] if len(sys.argv)>1 else None);print(json.dumps(dict(passed=not errors,errors=errors,expected_member_count=len(EXPECTED_FILES)+1),indent=2));raise SystemExit(bool(errors))
