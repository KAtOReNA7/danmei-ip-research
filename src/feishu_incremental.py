"""Reviewed delta sync via CLI, paginated full readback, append-only run receipts."""
from feishu_sync import *
import time
def norm(v):return None if v is None or v=='' else v
def diff_rows(rows,existing,baseline=None):
 keyname='后台键' if rows and '后台键' in rows[0] else '项目'
 old={r[keyname]:r for r in existing};assert len(old)==len(existing),'Duplicate remote keys'
 assert len({r[keyname] for r in rows})==len(rows),'Duplicate local keys'
 base={r[keyname]:r for r in baseline or []};creates=[];updates={}
 for row in rows:
  prev=old.get(row[keyname])
  if prev is None:creates.append(row);continue
  delta={k:v for k,v in row.items() if norm(prev.get(k))!=norm(v)}
  if delta and baseline is not None:
   assert row[keyname] in base,'No baseline for changed remote row'
   for k in delta:assert norm(prev.get(k))==norm(base[row[keyname]].get(k)),'Concurrent edit: '+row[keyname]+' '+k
  if delta:updates[prev['record_id']]=delta
 return creates,updates
def run(runid):
 cfg=json.loads(CONFIG.read_text(encoding='utf-8'));base=cfg['base_token'];root=ROOT/'receipts'/runid;root.mkdir(exist_ok=True)
 data=datasets();workmap={};report={}
 def call(args,label):return cli(args,runid+'/'+label)
 # cli label includes a folder below receipts; create it before any requests.
 (ROOT/'receipts'/('cli-'+runid)).mkdir(exist_ok=True)
 def read(name,phase):
  rows=[];offset=0
  while True:
   path=f'receipts/{runid}/{phase}-{name}-{offset}.ndjson'
   result=call(['+record-list','--base-token',base,'--table-id',cfg['tables'][name],'--offset',str(offset),'--limit','2000','--output',path,'--minimal-stdout','--overwrite'],f'{phase}-{name}-{offset}')
   page=[json.loads(x) for x in (ROOT/path).read_text(encoding='utf-8').splitlines() if x]
   rows+=page
   if not result['has_more']:break
   assert page,'Empty page while has_more';offset+=len(page)
  return rows
 for name,rows in data.items():
  tid=cfg['tables'][name]
  schema=call(['+field-list','--base-token',base,'--table-id',tid],'schema-'+name)['data']['fields']
  fields={f['name'] for f in schema}
  assert all(set(row)<=fields for row in rows),'Every projected row must use this table schema'
  before=read(name,'before');baseline=None
  prior=ROOT/'receipts'/('latest-'+name+'.json')
  if prior.exists():baseline=json.loads(prior.read_text(encoding='utf-8'))
  else:
   p=ROOT/'receipts'/('present-after-'+name+'.ndjson')
   if p.exists():baseline=[json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x]
  creates,updates=diff_rows(rows,before,baseline)
  plan={'table':name,'before_count':len(before),'create':creates,'update':updates,'deletes':0}
  (root/('plan-'+name+'.json')).write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
  for typ,items in [('create',creates),('update',list(updates.items()))]:
   for i in range(0,len(items),100):
    payload={'create_records':[{k:v for k,v in r.items() if v is not None} for r in items[i:i+100]]} if typ=='create' else {'update_records':dict(items[i:i+100])}
    p=root/f'{typ}-{name}-{i}.json';p.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
    args=['+record-batch-'+typ,'--base-token',base,'--table-id',tid,'--json','@'+p.relative_to(ROOT).as_posix()]
    call(args+['--dry-run'],f'preview-{typ}-{name}-{i}');call(args,f'write-{typ}-{name}-{i}')
  after=read(name,'after')
  # The service can acknowledge updates before record-list reflects every row.
  # Recheck reads only; never replay a write because of a stale readback.
  for attempt in range(3):
   try:
    assert len(after)==len(rows);assert not pending_rows(rows,after);break
   except AssertionError:
    if attempt==2:raise
    time.sleep(2*(attempt+1));after=read(name,f'after-recheck-{attempt+1}')
  if name=='作品目录':workmap={r['后台键']:r['record_id'] for r in after}
  if '关联作品' in fields:
   assert workmap
   links={}
   for r in after:
    expected=set(workmap[k] for k in (r.get('关联作品键') or '').split('|') if k)
    actual=set(x.get('id',x.get('record_id')) for x in (r.get('关联作品') or []))
    if expected!=actual:links[r['record_id']]={'关联作品':[{'id':x} for x in sorted(expected)]}
   items=list(links.items())
   for i in range(0,len(items),100):
    p=root/f'links-{name}-{i}.json';p.write_text(json.dumps({'update_records':dict(items[i:i+100])},ensure_ascii=False),encoding='utf-8')
    args=['+record-batch-update','--base-token',base,'--table-id',tid,'--json','@'+p.relative_to(ROOT).as_posix()]
    call(args+['--dry-run'],f'preview-links-{name}-{i}');call(args,f'write-links-{name}-{i}')
   if links:after=read(name,'after-links')
   for r in after:assert set(x.get('id',x.get('record_id')) for x in (r.get('关联作品') or []))==set(workmap[k] for k in r['关联作品键'].split('|') if k)
   assert not pending_rows(rows,after)
  prior.write_text(json.dumps(after,ensure_ascii=False),encoding='utf-8')
  report[name]={'rows':len(after),'created':len(creates),'updated':len(updates),'all_fields_match':True,'all_pages_read':True,'links_verified':'关联作品' in fields,'remaining_create':0}
  (root/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
  print(json.dumps({name:report[name]},ensure_ascii=False),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args();run(a.run)
