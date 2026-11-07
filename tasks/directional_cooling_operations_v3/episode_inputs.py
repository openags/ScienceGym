"""Load explicit simulation selections without turning them into evidence."""
from pathlib import Path
import copy
import hashlib
import json
import math

HERE=Path(__file__).resolve().parent

class InputError(ValueError):pass

def require(value,message):
    if not value:raise InputError(message)

def validate(profile):
    require(profile.get('schema_version')=='sciencegym.selected_reconstruction.v1','Unknown input schema')
    require(profile.get('hardware_qualified') is False,'Selected simulation inputs are not hardware qualification')
    require(profile.get('whole_paper_physics_validated') is False,'Input cards cannot certify execution')
    require(profile.get('inferred_values_are_source_facts') is False,'Inferences must remain distinct from source facts')
    contract=json.loads((HERE/'episode_input_contract.json').read_text())
    required={c['id']:set(c['required_fields']) for c in contract['cards']}
    cards=profile.get('cards',{});require(set(cards)==set(required),'Missing or unknown input card')
    def finite(value,path):
        if isinstance(value,float):require(math.isfinite(value),'Nonfinite value: '+path)
        elif isinstance(value,dict):
            for k,v in value.items():finite(v,path+'.'+k)
        elif isinstance(value,list):
            for i,v in enumerate(value):finite(v,path+'.'+str(i))
    for name,fields in required.items():
        require(set(cards[name])==fields,'Card fields differ from contract: '+name)
        for field,row in cards[name].items():
            label=name+'.'+field
            require(isinstance(row,dict) and row.get('value') is not None,'Missing selected value: '+label)
            require(row.get('origin') in {'source','inferred_selection'},'Unknown provenance: '+label)
            require(bool(row.get('rationale')),'Missing rationale: '+label)
            if row['origin']=='source':require(bool(row.get('source_locator')),'Source fact needs a locator: '+label)
            else:require(row.get('source_locator') is None,'Inferred selection mislabeled with a source locator: '+label)
            require(row.get('status')=='selected_for_simulation' and row.get('hardware_qualified') is False,'Input qualification claim: '+label)
            finite(row['value'],label)
    values={name:{key:copy.deepcopy(row['value']) for key,row in entries.items()} for name,entries in cards.items()}
    channel=values['calibration_card']['probe_to_channel_map']
    require(set(channel)=={'TC_W','TC_B',*['TC_MAP_'+str(i) for i in range(1,7)]},'Missing probe channel')
    require(set(channel.values())==set(range(8)),'Duplicate or invalid DAQ channel')
    require(values['acquisition_card']['channel_map']==channel,'Acquisition and calibration channel identities differ')
    geometry=values['fabrication_card']['actual_dimensions']
    require(geometry['RTD_bore_mm']>6.35,'Commercial RTD cannot fit the selected bore')
    require(abs(geometry['heater_diameter_mm']-50.8)<1e-8,'Commercial heater was silently resized')
    bath=values['calibration_card']['bath_fluid_and_fill_range']
    require(bath.get('fill_reference')=='selected reservoir floor','Bath fill depth needs a physical datum')
    depth=bath['selected_reservoir_depth_m'];below=bath['manufacturer_below_rim_m'];water=bath['fill_depth_m']
    require(len(below)==2 and below==[.022,.057] and depth==.200,'Selected A25/AC150 dimensions differ from the declared manual revision')
    require(len(water)==2 and all(abs(a-b)<1e-9 for a,b in zip(water,[depth-below[1],depth-below[0]])),
            'Bath fill range contradicts the manufacturer below-rim limits')
    require(water[0]<=bath['selected_nominal_depth_m']<=water[1],'Nominal bath level lies outside the selected operating range')
    require(values['manipulation_card']['bounded_recovery_policy']['max_retries']>=0,'Negative retry limit')
    return values

def load(path=None,include_solar=True):
    path=Path(path or HERE/'selected_reconstruction.json');profile=json.loads(path.read_text());values=validate(profile)
    packet=dict(record_kind='selected_simulation_inputs_not_observations',profile_id=profile['id'],
        profile_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),selected_parameter_cards=values,
        provenance=copy.deepcopy(profile['cards']),physical_success_receipts=[],hardware_qualified=False)
    if include_solar:
        solar_path=HERE/'selected_solar_path.json';solar=json.loads(solar_path.read_text())
        require(solar['inputs_sha256']['selected_reconstruction.json']==packet['profile_sha256'],'Solar path uses stale selected inputs')
        require(solar['geometry_checks']['passed'],'Selected track fails geometric shadow checks')
        require(solar['physical_tracking_validated'] is False,'Planning artifact cannot claim physical tracking')
        packet['selected_solar_path']=solar
    return packet

if __name__=='__main__':
    result=load();print(json.dumps(dict(profile=result['profile_id'],cards=len(result['selected_parameter_cards']),
        fields=sum(map(len,result['selected_parameter_cards'].values())),solar_commands=result['selected_solar_path']['command_count'],
        hardware_qualified=False,physical_success_receipts=0),indent=2))
