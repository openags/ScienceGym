"""Schema-sized metadata cleanup for this authored Blender 4.3 scene; no geometry edits.
Requires zstandard. Fixed character-field classes were inspected as C strings.
All post-NUL bytes are zeroed; unused UI path/search/asset selectors are cleared.
No raw buffer values or private paths are written to the public report.
"""
import pathlib,zstandard,io,struct,re,json,hashlib
P=pathlib.Path(__file__).resolve().parents[1]
KNOWN_STRING_FIELDS = {('Curve', 'family'), ('SpaceText', 'replacestr'), ('Image', 'name'), ('ToolSettings', 'uvcalc_weight_group'), ('ViewLayer', 'name'), ('bNodeSocket', 'name'), ('View3DShading', 'aov_name'), ('IDProperty', 'name'), ('FileSelectParams', 'dir'), ('SceneRenderView', 'suffix'), ('SpaceNode', 'tree_idname'), ('bNodeSocket', 'idname'), ('LineStyleModifier', 'name'), ('uiList', 'filter_byname'), ('FileSelectParams', 'title'), ('SpaceConsole', 'language'), ('RenderData', 'pic'), ('ColorManagedColorspaceSettings', 'name'), ('SpaceConsole', 'prompt'), ('CustomDataLayer', 'name'), ('VFont', 'name'), ('Object', 'parsubstr'), ('RenderData', 'engine'), ('uiList', 'list_id'), ('CameraDOFSettings', 'focus_subtarget'), ('FreestyleLineSet', 'name'), ('WorkSpaceLayout', 'name'), ('View3D', 'ob_centre_bone'), ('ColorManagedViewSettings', 'view_transform'), ('bNode', 'label'), ('bNodeSocket', 'description'), ('bDopeSheet', 'searchstr'), ('View3DShading', 'matcap'), ('FileSelectParams', 'filter_glob'), ('RenderData', 'stamp_udata'), ('FileSelectParams', 'filter_search'), ('BakeData', 'filepath'), ('SpaceOops', 'search_string'), ('bNodeTree', 'idname'), ('SpaceText', 'findstr'), ('bNodeSocket', 'label'), ('FileGlobal', 'filename'), ('bNodeSocket', 'short_label'), ('wmWindow', 'view_layer_name'), ('SeqTimelineChannel', 'name'), ('FileSelectParams', 'file'), ('ImageTile', 'label'), ('ID', 'name'), ('View3DShading', 'studio_light'), ('FileSelectParams', 'renamefile'), ('ColorManagedDisplaySettings', 'display_device'), ('Editing', 'proxy_dir'), ('RenderSlot', 'name'), ('ColorManagedViewSettings', 'look'), ('Editing', 'act_imagedir'), ('bNodeSocket', 'identifier'), ('View3DShading', 'lookdev_light'), ('SceneRenderView', 'name'), ('bNode', 'idname'), ('Editing', 'act_sounddir'), ('bNode', 'name')}
def parse(raw):
 assert raw[:12]==b'BLENDER-v403','Unsupported Blender layout'
 pos=12;blocks=[]
 while pos+24<=len(raw):
  code,n,old,sdna,count=struct.unpack_from('<4sIQII',raw,pos);blocks.append({'start':pos,'data_start':pos+24,'code':code,'size':n,'sdna':sdna,'count':count});pos+=24+n
  if code==b'ENDB':break
 q=next(x for x in blocks if x['code']==b'DNA1');d=raw[q['data_start']:q['data_start']+q['size']];pos=4;assert d[pos:pos+4]==b'NAME';pos+=4;n=struct.unpack_from('<I',d,pos)[0];pos+=4;names=[]
 for _ in range(n):j=d.index(0,pos);names.append(d[pos:j].decode());pos=j+1
 pos=(pos+3)&~3;assert d[pos:pos+4]==b'TYPE';pos+=4;n=struct.unpack_from('<I',d,pos)[0];pos+=4;types=[]
 for _ in range(n):j=d.index(0,pos);types.append(d[pos:j].decode());pos=j+1
 pos=(pos+3)&~3;assert d[pos:pos+4]==b'TLEN';pos+=4;sizes=list(struct.unpack_from('<'+'H'*len(types),d,pos));pos+=2*len(types);pos=(pos+3)&~3;assert d[pos:pos+4]==b'STRC';pos+=4;n=struct.unpack_from('<I',d,pos)[0];pos+=4;structs=[]
 for _ in range(n):
  typ,num=struct.unpack_from('<HH',d,pos);pos+=4;fields=[];off=0
  for j in range(num):
   t,f=struct.unpack_from('<HH',d,pos);pos+=4;name=names[f];count=1
   for dim in re.findall(r'\[(\d+)\]',name):count*=int(dim)
   size=(8 if '*' in name else sizes[t])*count;fields.append({'type':types[t],'name':name,'offset':off,'size':size,'pointer':'*' in name,'count':count});off+=size
  assert off==sizes[typ],('Unsupported SDNA struct padding',types[typ]);structs.append({'name':types[typ],'size':sizes[typ],'fields':fields})
 bytype={s['name']:s for s in structs}
 def walk(s,base):
  for f in s['fields']:
   if f['pointer']:continue
   start=base+f['offset']
   if f['type']=='char' and '[' in f['name'] and f['size']>=32:
    name=f['name'].split('[')[0];assert (s['name'],name) in KNOWN_STRING_FIELDS,('Unreviewed fixed character field',s['name'],name)
    yield {'structure':s['name'],'field':name,'offset':start,'size':f['size']}
   elif f['type'] in bytype:
    child=bytype[f['type']]
    for i in range(f['count']):yield from walk(child,start+i*child['size'])
 fields=[]
 for bl in blocks:
  if bl['code'] in [b'DNA1',b'ENDB',b'REND',b'TEST']:continue
  s=structs[bl['sdna']]
  if not s['size'] or bl['count']*s['size']>bl['size']:continue
  for i in range(bl['count']):fields+=list(walk(s,bl['data_start']+i*s['size']))
 return blocks,fields
def clear_ui(f):
 st,k=f['structure'],f['field']
 return st=='FileGlobal' or (st=='FileSelectParams' and k!='title') or (st=='Editing' and k in {'act_imagedir','act_sounddir','proxy_dir'}) or (st=='View3DShading' and k in {'studio_light','lookdev_light','matcap'}) or (st=='SpaceOops' and k=='search_string') or (st=='SpaceText' and k in {'findstr','replacestr'})
def is_path(f):
 return bool(re.search(r'path|(?<!pro)file|dir|pic',f['field'],re.I)) or (f['structure'],f['field']) in {('Image','name'),('VFont','name')} or (f['structure']=='View3DShading' and f['field'] in {'studio_light','lookdev_light','matcap'})
def main():
 p=P/'geometry/thermalmeta_lab.blend';old=p.read_bytes();raw=zstandard.ZstdDecompressor().stream_reader(io.BytesIO(old)).read();blocks,fields=parse(raw);new=bytearray(raw);changed=[];tails=0;pathaudit=[]
 for f in fields:
  start,size=f['offset'],f['size'];v=raw[start:start+size];nul=v.find(b'\0');assert nul>=0,('Unterminated reviewed string field',f['structure'],f['field']);active=v[:nul];nz=sum(x!=0 for x in v[nul+1:]);tails+=bool(nz)
  clean=b'\0'*size if clear_ui(f) else active+b'\0'*(size-len(active))
  if is_path(f):
   a=clean.split(b'\0',1)[0]
   permitted={b'',b'//',b'//../previews/preview_01_overview.png',b'<builtin>'}
   assert a in permitted,('Unapproved active path selector',f['structure'],f['field'])
   pathaudit.append({'structure':f['structure'],'field':f['field'],'buffer_bytes':size,'active_value_class':'empty' if not a else 'builtin_font' if a==b'<builtin>' else 'intentional_relative_path','post_nul_bytes_all_zero':True})
  if clean!=v:
   new[start:start+size]=clean;changed.append({'structure':f['structure'],'field':f['field'],'buffer_bytes':size,'action':'clear_unused_ui_buffer' if clear_ui(f) else 'zero_post_nul_padding','previous_nonzero_tail_count':nz})
 maskbefore=bytearray(raw);maskafter=bytearray(new)
 for f in fields:
  a=f['offset'];n=f['size'];maskbefore[a:a+n]=b'\0'*n;maskafter[a:a+n]=b'\0'*n
 assert maskbefore==maskafter
 for f in fields:
  a=f['offset'];n=f['size'];v=new[a:a+n];nul=v.index(0);assert not any(v[nul+1:])
  if not clear_ui(f):assert raw[a:a+n].split(b'\0',1)[0]==v.split(b'\0',1)[0]
 out=zstandard.ZstdCompressor(level=9).compress(bytes(new));p.write_bytes(out)
 h=lambda x:hashlib.sha256(x).hexdigest()
 report={'schema':'sciencegym.native_fixed_buffer_sanitization.v1','scope':'All SDNA fixed character arrays of at least 32 bytes in this scene, with semantics-reviewed field classes; all path-related buffers include their full post-NUL width','passed':True,'fixed_char_array_instances_checked':len(fields),'reviewed_field_class_count':len(KNOWN_STRING_FIELDS),'unsupported_layouts':[],'fields_with_nonzero_tail_before':tails,'fields_with_nonzero_tail_after':0,'cleared_or_canonicalized_buffers':changed,'all_path_buffer_audit':pathaudit,'non_metadata_bytes_identical':True,'non_ui_active_strings_identical':True,'masked_content_sha256_before':h(maskbefore),'masked_content_sha256_after':h(maskafter),'before_native_sha256':h(old),'after_native_sha256':h(out),'before_decompressed_sha256':h(raw),'after_decompressed_sha256':h(new),'changed_byte_count':sum(a!=b for a,b in zip(raw,new)),'render_geometry_materials_lights_cameras_unchanged':True,'source_previews_pixels_unchanged':True,'compression':'native-compatible zstd, no uncompressed export','raw_private_fragments_in_report':False}
 (P/'review/native_buffer_sanitization.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'buffers':len(fields),'tail_fields_before':tails,'tail_fields_after':0,'changed_bytes':report['changed_byte_count'],'native_sha256':h(out)}))
if __name__=='__main__':main()
