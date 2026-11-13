"""A25 registry extension, isolated from pinned earlier device executions."""
from extended_device_assets import ASSETS,DEVICES,export,visuals,load
DEVICES['thermo_a25_ac150']=ASSETS/'thermo_a25_ac150_v1'
if __name__=='__main__':print('A25 exported parts',len(export('thermo_a25_ac150')['parts']))
