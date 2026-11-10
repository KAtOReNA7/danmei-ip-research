"""Link known records and hide audit columns; no permission or workflow changes."""
from feishu_sync import *
def run():
 cfg=json.loads(CONFIG.read_text(encoding='utf-8'));base=cfg['base_token'];data=datasets()
 def read(name,label):
  path='receipts/'+label+'-'+name+'.ndjson'
  r=cli(['+record-list','--base-token',base,'--table-id',cfg['tables'][name],'--output',path,'--minimal-stdout','--overwrite'],label+'-'+name)
  assert not r['has_more']
  return [json.loads(x) for x in (ROOT/path).read_text(encoding='utf-8').splitlines() if x]
 workrows=read('作品目录','present-source');workmap={r['后台键']:r['record_id'] for r in workrows}
 results={}
 for name,rows in data.items():
  tid=cfg['tables'][name];schema=cli(['+field-list','--base-token',base,'--table-id',tid],'present-schema-'+name)['data']['fields']
  old=read(name,'present-before');bykey={r.get('后台键',r.get('项目')):r for r in old}
  linked=bool(rows and '关联作品键' in rows[0])
  if linked and not any(f['name']=='关联作品' for f in schema):
   args=['+field-create','--base-token',base,'--table-id',tid,'--json',json.dumps({'name':'关联作品','type':'link','link_table':cfg['tables']['作品目录']},ensure_ascii=False)]
   cli(args+['--dry-run'],'link-plan-'+name);cli(args,'link-create-'+name)
   schema=cli(['+field-list','--base-token',base,'--table-id',tid],'linked-schema-'+name)['data']['fields']
  updates={}
  for row in rows:
   prev=bykey[row.get('后台键',row.get('项目'))]
   delta={k:v for k,v in row.items() if (prev.get(k) or None)!=(v or None)}
   if linked:
    ids=[workmap[k] for k in row['关联作品键'].split('|') if k]
    delta['关联作品']=[{'id':x} for x in ids]
   if delta:updates[prev['record_id']]=delta
  items=list(updates.items())
  for i in range(0,len(items),100):
   (ROOT/'receipts/present-payload.json').write_text(json.dumps({'update_records':dict(items[i:i+100])},ensure_ascii=False),encoding='utf-8')
   args=['+record-batch-update','--base-token',base,'--table-id',tid,'--json','@receipts/present-payload.json']
   cli(args+['--dry-run'],f'present-preview-{name}-{i}');cli(args,f'present-write-{name}-{i}')
  after=read(name,'present-after');assert len(after)==len(rows);assert not pending_rows(rows,after)
  if linked:
   for r in after:
    actual=r.get('关联作品') or []
    if isinstance(actual,str):raise RuntimeError('Unexpected link normalization')
    assert set(x.get('id',x.get('record_id')) for x in actual)==set(workmap[k] for k in r['关联作品键'].split('|') if k),r
  views=cli(['+view-list','--base-token',base,'--table-id',tid],'present-views-'+name)['data']['views']
  if views:
   vid=views[0]['id'];cli(['+view-get-visible-fields','--base-token',base,'--table-id',tid,'--view-id',vid],'view-before-'+name)
   visible=[f['name'] for f in schema if not (f['name'].startswith('后台') or f['name'] in ['关联作品键','证据键'])]
   args=['+view-set-visible-fields','--base-token',base,'--table-id',tid,'--view-id',vid,'--json',json.dumps({'visible_fields':visible},ensure_ascii=False)]
   cli(args+['--dry-run'],'view-preview-'+name);cli(args,'view-write-'+name)
   cli(['+view-get-visible-fields','--base-token',base,'--table-id',tid,'--view-id',vid],'view-after-'+name)
  results[name]={'rows':len(after),'all_values_match':True,'links_verified':linked,'has_more':False}
  (ROOT/'receipts/presentation-validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
  print(name,len(after),'verified',flush=True)
if __name__=='__main__':run()
