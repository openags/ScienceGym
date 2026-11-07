"""Tessellate pinned Unitree STEP solids without changing mechanical geometry."""
import importlib.metadata
import json
from pathlib import Path
import hashlib
import numpy as np
import trimesh
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.StlAPI import StlAPI_Writer
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build():
    source=json.loads((HERE/'SOURCE.json').read_text());dest=HERE/'geometry';dest.mkdir(exist_ok=True)
    items=[]
    for entry in source['files']:
        assert sha(HERE/entry['path'])==entry['sha256']
        if not entry['path'].endswith('.STEP'):continue
        path=HERE/entry['path'];reader=STEPControl_Reader();assert reader.ReadFile(str(path))==IFSelect_RetDone
        assert reader.TransferRoots()>0;shape=reader.OneShape();assert BRepCheck_Analyzer(shape).IsValid()
        BRepMesh_IncrementalMesh(shape,.05,False,.15,False).Perform()
        temp=dest/(path.stem+'_source_mm.stl');writer=StlAPI_Writer();assert writer.Write(shape,str(temp))
        mesh=trimesh.load(temp,force='mesh');mesh.apply_scale(.001);temp.unlink()
        raw_faces=len(mesh.faces)
        # Adjacent STEP faces tessellate independently. Weld only within 1 um
        # (well below the 50 um tessellation tolerance) and drop collapsed faces.
        mesh.merge_vertices(digits_vertex=6)
        mesh.update_faces(mesh.nondegenerate_faces());mesh.remove_unreferenced_vertices()
        assert mesh.is_watertight and mesh.is_volume
        target=dest/(path.stem+'.stl');mesh.export(target)
        cylinders=[];planes=[];explorer=TopExp_Explorer(shape,TopAbs_FACE)
        while explorer.More():
            face=TopoDS.Face_s(explorer.Current());surface=BRepAdaptor_Surface(face)
            if surface.GetType()==GeomAbs_Cylinder:
                c=surface.Cylinder();axis=c.Axis();p=axis.Location();v=axis.Direction()
                cylinders.append(dict(radius_m=c.Radius()*.001,axis_origin_m=[p.X()*.001,p.Y()*.001,p.Z()*.001],axis=[v.X(),v.Y(),v.Z()]))
            if surface.GetType()==GeomAbs_Plane:
                plane=surface.Plane();p=plane.Location();v=plane.Axis().Direction()
                prop=GProp_GProps();BRepGProp.SurfaceProperties_s(face,prop);center=prop.CentreOfMass()
                planes.append(dict(origin_m=[p.X()*.001,p.Y()*.001,p.Z()*.001],normal=[v.X(),v.Y(),v.Z()],area_m2=prop.Mass()*1e-6,centroid_m=[center.X()*.001,center.Y()*.001,center.Z()*.001]))
            explorer.Next()
        prop=GProp_GProps();BRepGProp.VolumeProperties_s(shape,prop)
        item=dict(id=path.stem,source_path=entry['path'],source_sha256=entry['sha256'],geometry=dict(path=str(target.relative_to(HERE)),sha256=sha(target),bounds_m=mesh.bounds.tolist(),raw_faces=raw_faces,faces=len(mesh.faces),watertight=mesh.is_watertight,mesh_volume_m3=float(mesh.volume),step_volume_m3=prop.Mass()*1e-9),cylindrical_faces=cylinders,planar_faces=planes)
        items.append(item);print(json.dumps({k:item[k] for k in ['id','geometry']}))
    result=dict(schema_version=1,source_sha256=sha(HERE/'SOURCE.json'),builder_sha256=sha(__file__),ocp_version=importlib.metadata.version('cadquery-ocp'),
      tessellation=dict(linear_deflection_mm=.05,angular_deflection_rad=.15,vertex_weld_precision_m=1e-6,unit_conversion='STEP millimetres to metres; no geometric rescaling'),items=items,
      license='Apache-2.0; derived from pinned Unitree STEP files; original solids retained',physical_compatibility_qualified=False)
    (HERE/'mount_geometry.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':build()
