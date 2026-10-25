"""Separate, uncut stock candidates; no completed apparatus or robot fixture."""
from geometry_tools import Geometry


def plates(specs, color, metal=0):
    g=Geometry();z=0;units=[]
    for name,size in specs:
        g.box(name,size,[0,0,z+size[2]/2],color,role='uncut_stock',metal=metal)
        units.append(dict(id=name,parts=[name],dimensions_m=size));z+=size[2]
    return g,dict(units=units,form='Uncut plates stacked in direct contact; cut plan is a separate review artifact')


def tubes(kind,inner,outer,count,color):
    g=Geometry();units=[]
    centers=[[-.06,0],[.06,0],[0,.12]] if count==3 else [[-.09,0],[.09,0]]
    for i,(x,y) in enumerate(centers,1):
        name='raw_'+kind+'_tube_'+str(i)
        g.ring(name,inner,outer,.100,[x,y,.050],color,role='uncut_stock',metal=.75 if kind=='aluminum' else 0)
        units.append(dict(id=name,parts=[name],outer_diameter_m=outer*2,inner_diameter_m=inner*2,length_m=.100))
    return g,dict(units=units,form='Selected 100 mm raw lengths; final 57 mm sections still require cutting and finishing')


def models():
    return [
        ('copper_sheet_stock',lambda:plates([('raw_copper_sheet',[.300,.250,.0005])],[181,105,67],.8),{}),
        ('aluminum_sheet_stock',lambda:plates([('raw_aluminum_1mm',[.400,.300,.001]),('raw_aluminum_1_5mm',[.400,.300,.0015]),('raw_aluminum_6_4mm',[.300,.160,.0064])],[175,184,192],.8),{}),
        ('foam_stock',lambda:plates([('raw_foam_sheet',[.300,.250,.025])],[202,145,162]),{}),
        ('acrylic_stock',lambda:plates([('raw_acrylic_sheet_1',[.350,.300,.006]),('raw_acrylic_sheet_2',[.350,.300,.006])],[178,201,205]),{}),
        ('pe_tube_stock',lambda:tubes('pe',.038,.051,3,[221,221,201]),{}),
        ('aluminum_tube_stock',lambda:tubes('aluminum',.070,.076,2,[175,184,192]),{}),
    ]
