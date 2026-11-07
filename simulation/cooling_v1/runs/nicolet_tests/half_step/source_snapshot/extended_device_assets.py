"""Additional source assets without changing frozen earlier device episodes.

New workcells import this registry before constructing their controllers and
archive both this file and device_assets.py. Existing episodes retain their
original loader bytes and original asset inventories.
"""
from device_assets import ASSETS,DEVICES,export,visuals,load

DEVICES.update(omega_khr_2_2_p=ASSETS/'omega_khr_2_2_p_v1',
               keithley_2425=ASSETS/'keithley_2425_v1',
               mcc_usb_tc=ASSETS/'mcc_usb_tc_v1')

if __name__=='__main__':
    for name in ['omega_khr_2_2_p','keithley_2425','mcc_usb_tc']:print(name,len(export(name)['parts']))
