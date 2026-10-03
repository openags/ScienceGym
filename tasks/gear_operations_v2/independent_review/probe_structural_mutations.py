#!/usr/bin/env python3
"""Read-only generated deletion and handling-order probes over all physical branches."""
import copy,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
import record_contract as rc

def run():
 p=rc.load_packet();results={'baseline_branch_acceptance':0,'single_event_deletions':0,'adjacent_handling_swaps':0,'unexpected_acceptances':[]}
 for b in p['branches']['branches']:
  baseline=rc.fixture(b['id'],p);rc.validate_record(baseline,p);results['baseline_branch_acceptance']+=1
  for i,event in enumerate(baseline['events']):
   r=copy.deepcopy(baseline);r['events'].pop(i)
   try:rc.validate_record(r,p)
   except (ValueError,TypeError,KeyError):results['single_event_deletions']+=1
   else:results['unexpected_acceptances'].append({'branch':b['id'],'mutation':'event_deletion','index':i,'op_id':event['op_id']})
  handling=[i for i,e in enumerate(baseline['events']) if e['op_id']!='IMAGE' and not e['op_id'].startswith('ANALYZE_')]
  for i,j in zip(handling,handling[1:]):
   if (baseline['events'][i]['op_id'],baseline['events'][i].get('destination_station'))==(baseline['events'][j]['op_id'],baseline['events'][j].get('destination_station')):continue
   r=copy.deepcopy(baseline);r['events'][i],r['events'][j]=r['events'][j],r['events'][i]
   try:rc.validate_record(r,p)
   except (ValueError,TypeError,KeyError):results['adjacent_handling_swaps']+=1
   else:results['unexpected_acceptances'].append({'branch':b['id'],'mutation':'adjacent_handling_swap','indices':[i,j],'op_ids':[baseline['events'][i]['op_id'],baseline['events'][j]['op_id']]})
 results['rejected_mutations']=results['single_event_deletions']+results['adjacent_handling_swaps']
 results['scope']='Synthetic canonical-recipe completeness and order only; not physical validation or a proof for arbitrary alternate routes'
 return results
if __name__=='__main__':
 r=run();print(json.dumps(r,indent=2));raise SystemExit(bool(r['unexpected_acceptances']))
