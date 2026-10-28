"""Optical device registry without modifying archived device loaders."""
from extended_device_assets import ASSETS,DEVICES,export,visuals,load
DEVICES['nicolet_6700']=ASSETS/'nicolet_6700_v1'
if __name__=='__main__':print('Nicolet exported parts',len(export('nicolet_6700')['parts']))
