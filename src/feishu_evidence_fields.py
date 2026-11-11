"""Add source and precision columns through the CLI, without altering records."""
from feishu_sync import *

def main():
 cfg=json.loads(CONFIG.read_text(encoding='utf-8'));report={}
 for name,wanted in [('事件时间线',['来源']),('指标观测',['来源','显示精度','标准指标'])]:
  args=['--base-token',cfg['base_token'],'--table-id',cfg['tables'][name]]
  schema=cli(['+field-list',*args],'evidence-fields-before-'+name)['data']['fields']
  existing={f['name'] for f in schema};missing=[{'name':x,'type':'text'} for x in wanted if x not in existing]
  if missing:
   path=ROOT/'receipts'/('evidence-fields-'+name+'.json');path.write_text(json.dumps(missing,ensure_ascii=False),encoding='utf-8')
   command=['+field-create',*args,'--json','@'+path.relative_to(ROOT).as_posix()]
   cli(command+['--dry-run'],'evidence-fields-preview-'+name);cli(command,'evidence-fields-write-'+name)
  after=cli(['+field-list',*args],'evidence-fields-after-'+name)['data']['fields']
  assert set(wanted)<={f['name'] for f in after}
  report[name]={'created':len(missing),'field_readback_match':True}
 (ROOT/'receipts/evidence-fields-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
