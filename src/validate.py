"""Validate persisted facts and exports, without contacting external services."""
import json,hashlib
from research import *
def main():
 c=connect();assert c.execute('pragma integrity_check').fetchone()[0]=='ok';assert not c.execute('pragma foreign_key_check').fetchall()
 errors=[]
 for ev in c.execute('select * from evidence'):
  p=ROOT/ev['file_path']
  if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=ev['sha256']:errors.append(ev['id'])
 assert not errors,errors
 assert not c.execute('select platform,source_id,count(*) from works group by platform,source_id having count(*)>1').fetchall()
 n=c.execute('select count(*) from works').fetchone()[0]
 assert c.execute("select count(*) from coverage where task_type='work_media'").fetchone()[0]==n*len(MEDIA)
 placeholders=','.join('?' for _ in MEDIA_STATUSES)
 assert not c.execute(f"select id,status from coverage where task_type='work_media' and (status is null or status not in ({placeholders}))",MEDIA_STATUSES).fetchall(), 'Noncanonical work/media state'
 assert not c.execute(f"select id,status from check_history where status is null or status not in ({placeholders})",MEDIA_STATUSES).fetchall(), 'Noncanonical work/media history state'
 assert not c.execute("select id from works where inclusion_status='已确认' and (identity_evidence is null or category_mapped!='纯爱')").fetchall()
 from rights_rules import sale_window
 for row in c.execute('select * from rights_records'):
  expected=sale_window(row['contract_time_raw'])
  assert row['window_role']==expected['window_role'] and row['contract_start']==expected['start'] and row['contract_end']==expected['end'], row['id']
  assert row['deal_id'] is None and row['amount'] is None, 'Independent contract and fee require dedicated evidence review'
 counts={}
 for path in (ROOT/'exports').glob('*.jsonl'):
  t=path.stem;rows=[json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x]
  actual=[dict(r) for r in c.execute('select * from '+t)]
  assert rows==actual,t;counts[t]=len(rows)
 result={'at':now(),'integrity':'ok','foreign_key_errors':[],'evidence_checksums':'all_match','exports':'all_rows_all_columns_match','counts':counts,'denominator':None,'status':'部分完成'}
 (ROOT/'receipts/validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False));c.close()
if __name__=='__main__':main()
