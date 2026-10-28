"""Cary-specific assets registered without changing earlier optical archives."""
from optical_assets import ASSETS,DEVICES,export,visuals,load
DEVICES['cary_5000']=ASSETS/'cary_5000_v1'
DEVICES['cary_internal_dra_2500']=ASSETS/'cary_internal_dra_2500_v1'
if __name__=='__main__':
 for name in ['cary_5000','cary_internal_dra_2500']:print(name,len(export(name)['parts']))
