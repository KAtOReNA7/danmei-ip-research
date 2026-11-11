"""CLI-only, scoped to the explicitly created project Base. No credential handling."""
import subprocess, json, argparse
from research import ROOT,connect,now,MEDIA
CONFIG=ROOT/'config/feishu.local.json'
def pending_rows(rows,existing):
 keyname='后台键' if rows and '后台键' in rows[0] else '项目'
 old={r[keyname]:r for r in existing}
 assert len(old)==len(existing),'Duplicate remote keys; investigate before write'
 assert len({r[keyname] for r in rows})==len(rows),'Duplicate local keys'
 pending=[]
 for row in rows:
  found=old.get(row[keyname])
  if found:
   assert all((found.get(k) or None)==(v or None) for k,v in row.items()),'Changed remote/local row requires reviewed update: '+row[keyname]
  else: pending.append(row)
 return pending
def cli(args,label):
 cfg=json.loads(CONFIG.read_text(encoding='utf-8'))
 p=subprocess.run([cfg['cli_executable'],'base',*args,'--as','user'],capture_output=True,encoding='utf-8',cwd=ROOT,timeout=90)
 path=ROOT/'receipts'/('cli-'+label+'.json');path.write_text(p.stdout or p.stderr,encoding='utf-8')
 try:r=json.loads(p.stdout)
 except Exception:raise RuntimeError('CLI output unavailable; inspect receipt before retry: '+str(path))
 if p.returncode or not r.get('ok',True):raise RuntimeError('CLI failed; inspect receipt before retry: '+str(path)+' '+p.stderr[:200])
 return r
def datasets():
 c=connect();works=[dict(r) for r in c.execute('select * from works order by platform,source_id')]
 names={w['id']:w['title']+' / '+str(w['author']) for w in works}
 data={}
 data['调查说明']=[{'项目':k,'内容':v} for k,v in [('状态','部分完成；全量目标未变。候选来源记录不等于去重原著总数。'),('范围','晋江/长佩全部符合原发或作品签约及纯爱分类条件的作品；2024-01-01至2026-11-10；国内外；电子书保留，实体出版排除。'),('进度','1021条候选来源记录，12部试采；大部分媒介未调查。目录分母未知，不报告全站覆盖率。'),('使用','作品目录看候选身份；覆盖与缺口看9媒介状态；产品事件的公告不等于实际执行。游戏2020记录为窗口外背景。'),('数字限制','当前收藏/人气不是销量；缓存数字的采样时间未知，不作当前或历史增量。2026未满全年不能与全年直接比。'),('数据备份','完整证据和SQLite保存独立本地项目，GitHub仅代码；云表为本轮快照。'),('身份缺口','同名异作者不合并；跨站和重发版本待核。未确认作品不进入确认统计。')]]
 touched=c.execute("select count(distinct work_id) from coverage where task_type='work_media' and status!='未调查'").fetchone()[0]
 detail=c.execute("select count(*) from works where signing_evidence is not null or exists(select 1 from coverage cv where cv.work_id=works.id and cv.task_type='qualification' and cv.status='已核验')").fetchone()[0]
 media_checked=c.execute("select count(distinct work_id) from coverage where task_type='work_media' and media!='电子书' and status!='未调查'").fetchone()[0]
 data['调查说明'][2]['内容']=f'{len(works)}条候选来源记录；{touched}条至少进行一项初查，{detail}条有详情证据，{media_checked}条有非电子书初查。初查不等于全媒介完成，目录分母未知，不报告全站覆盖率。'
 data['调查说明'].append({'项目':'目录覆盖限制','内容':'最新发表目录偏向近期作品，不能据此推断全行业开发率；历史锁删、迁移及其他年份目录仍有缺口。'})
 data['调查说明'][0]['内容']='部分完成；V1.1主线为2024年以来已售出/已授权签约的权利，全量目标未变。上线不证明窗口内售出。'
 data['调查说明'][3]['内容']='先看授权签约明细及签约时间；未上线的已售保留。签约月份横跨截止日或日期缺失时不计窗口内确认；产品与表现单列。'
 data['调查说明'].append({'项目':'售出统计口径','内容':'官方清单行数、去重作品数、权利组合及独立交易数分别计；同合同范围不明不把多行当多笔。当前披露/采集时间不代替签约时间，未确认作品另列。'})
 evidence_urls={r['id']:r['url'] for r in c.execute('select id,url from evidence')}
 product_names={r['id']:r['title'] for r in c.execute('select id,title from products')}
 data['作品目录']=[];data['覆盖与缺口']=[]
 for w in works:
  data['作品目录'].append({'书名':w['title'],'作者':w['author'],'来源平台':w['platform'],'题材原文':w['category_raw'],'连载状态':w['serial_status'],'纳入状态':w['inclusion_status'],'纳入依据':w['inclusion_basis'],'签约原文':w['signing_raw'],'来源':w['source_url'],'样本':str(w['sample']),'后台键':w['id']})
  cov=list(c.execute("select * from coverage where work_id=? and task_type='work_media'",(w['id'],)))
  qualification=list(c.execute("select * from coverage where work_id=? and task_type='qualification'",(w['id'],)))
  notes=cov+qualification
  row={'作品':names[w['id']],'后台键':w['id'],'关联作品键':w['id'],**{r['media']:r['status'] for r in cov},'核查范围':' | '.join(sorted(set(r['query_scope'] or '' for r in notes))),'缺口':' | '.join(sorted(set(r['gap'] or '' for r in notes)))}
  data['覆盖与缺口'].append(row)
 specs={'products':('产品与版本',{'title':'产品','media':'媒介','language':'语言','markets':'发行市场','platform':'平台','source_url':'来源','producer':'参与方','status':'状态','confirmation':'确认状态','id':'后台键'}),'events':('事件时间线',{'event_type':'事件','event_time':'发生日期','time_end':'结束日期','time_precision':'时间精度','description':'事实与限制','window_role':'窗口归属','confirmation':'确认状态','id':'后台键','work_id':'关联作品键','evidence_id':'证据键'}),'observations':('指标观测',{'metric_raw':'指标原文','raw_value':'显示原文','value':'解析值','unit':'单位','temporal_type':'时间类型','observed_at':'观测时间','period_start':'期间开始','period_end':'期间结束','missing_reason':'缺失原因','comparison_version':'可比口径','id':'后台键','work_id':'关联作品键','evidence_id':'证据键'}),'evidence':('证据索引',{'title':'证据','url':'来源','subject':'主体','published_at':'来源发布时间','accessed_at':'采集时间','status':'可信状态','method':'获取方式','id':'后台键','file_path':'后台文件','sha256':'后台校验'}),'source_matrix':('来源可行性',{'media':'媒介','source_name':'来源名称','url':'来源','events_available':'事件可得性','current_values':'当前值可得性','historical_values':'历史值可得性','access_condition':'访问条件','test_result':'结论','next_action':'下一步','id':'后台键'}),'exclusions':('排除边界',{'title':'对象','source_url':'来源','reason':'排除原因','id':'后台键'})}
 for t,(name,fields) in specs.items():
  data[name]=[]
  for r in c.execute('select * from '+t):
   row={label:None if r[col] is None else str(r[col]) for col,label in fields.items()}
   if 'work_id' in r.keys():row['作品']=names.get(r['work_id'])
   if t in ['events','observations']:
    row['来源']=evidence_urls.get(r['evidence_id'])
    row['产品键']=r['product_id'];row['对应产品']=product_names.get(r['product_id'])
   if t=='observations':
    row['显示精度']={'rounded_display':'近似展示（万）','displayed_integer':'页面整数','missing':'缺失'}.get(r['precision'],r['precision']);row['标准指标']=r['metric_standard']
    row['下界']=None if r['lower_bound'] is None else str(r['lower_bound']);row['上界']=None if r['upper_bound'] is None else str(r['upper_bound'])
   if t=='products':
    row.update({'父项目键':r['parent_id'],'父项目':product_names.get(r['parent_id']),'季卷':r['season'],'来源标识':r['source_id'],'商业模式':r['pay_model'],'发行方':r['distributor'],'证据键':r['evidence_id'],'记录层级':'季/卷/版本子记录' if r['parent_id'] else '根记录（含项目、待核或窗口外，结合状态判断）'})
    ids=[x[0] for x in c.execute('select work_id from product_works where product_id=?',(r['id'],))]
    row['关联作品键']='|'.join(ids);row['作品']='；'.join(names.get(x,x) for x in ids)
   data[name].append(row)
 rights_fields={'id':'后台键','work_id':'关联作品键','rights_type_raw':'权利类型原文','media':'媒介','market_raw':'授权地域原文','language':'语言','grantor':'授权方','licensee':'受让方','agent':'代理方','contract_time_raw':'签约时间原文','contract_start':'签约区间开始','contract_end':'签约区间结束','time_precision':'时间精度','announcement_time':'官宣时间','window_role':'窗口归属','sale_status':'售出证据状态','deal_id':'独立交易键','amount':'授权金额','currency':'币种','source_url':'来源','source_locator':'来源定位','evidence_id':'证据键','gap':'缺口'}
 data['授权签约']=[{**{label:None if r[col] is None else str(r[col]) for col,label in rights_fields.items()},'作品':names[r['work_id']]} for r in c.execute('select * from rights_records order by id')]
 data['目录批次']=[{'分区':r['partition'],'游标':r['cursor'],'状态':r['status'],'查询范围':r['query_scope'],'发现行数':str(r['discovered']) if r['discovered'] is not None else None,'新候选数':str(r['new_unique']) if r['new_unique'] is not None else None,'缺口':r['gap'],'后台键':r['id']} for r in c.execute("select * from coverage where task_type='directory'")]
 c.close();return data
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['plan','sync']);p.add_argument('--only');a=p.parse_args()
 data=datasets();cfg=json.loads(CONFIG.read_text(encoding='utf-8'));base=cfg['base_token']
 plan={name:{'records':len(rows),'fields':list(rows[0]) if rows else [],'unique_keys':len({r.get('后台键',r.get('项目')) for r in rows})} for name,rows in data.items()}
 (ROOT/'receipts/feishu-import-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
 if a.action=='plan':print(json.dumps(plan,ensure_ascii=False,indent=2));return
 for name,rows in data.items():
  if a.only and a.only!=name:continue
  table=cfg['tables'].get(name)
  if not table:
   fields=[{'name':k,'type':'text'} for k in rows[0]]
   args=['+table-create','--base-token',base,'--name',name,'--fields',json.dumps(fields,ensure_ascii=False)]
   cli(args+['--dry-run'],'table-plan-'+name)
   r=cli(args,'table-create-'+name)
   table=r['data']['table']['id'];cfg['tables'][name]=table;CONFIG.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
  schema=cli(['+field-list','--base-token',base,'--table-id',table],'schema-'+name)
  assert set(rows[0])<=set(f['name'] for f in schema['data']['fields'])
  # Every table projection is under 2000 rows. Full readback is explicitly required by the PRD.
  path='receipts/before-'+name+'.ndjson'
  cli(['+record-list','--base-token',base,'--table-id',table,'--output',path,'--minimal-stdout','--overwrite'],'before-'+name)
  existing=[json.loads(line) for line in (ROOT/path).read_text(encoding='utf-8').splitlines() if line]
  assert not json.loads((ROOT/path.replace('.ndjson','.manifest.json')).read_text(encoding='utf-8'))['has_more']
  pending=pending_rows(rows,existing)
  for i in range(0,len(pending),100):
   batch=[{k:v for k,v in r.items() if v is not None} for r in pending[i:i+100]]
   payload=ROOT/'receipts/payload.json';payload.write_text(json.dumps({'create_records':batch},ensure_ascii=False),encoding='utf-8')
   args=['+record-batch-create','--base-token',base,'--table-id',table,'--json','@receipts/payload.json']
   cli(args+['--dry-run'],f'preview-{name}-{i}')
   cli(args,f'write-{name}-{i}')
  path='receipts/after-'+name+'.ndjson'
  r=cli(['+record-list','--base-token',base,'--table-id',table,'--output',path,'--minimal-stdout','--overwrite'],'after-'+name)
  actual=[json.loads(line) for line in (ROOT/path).read_text(encoding='utf-8').splitlines() if line]
  assert not r['has_more'] and len(actual)==len(rows)
  assert not pending_rows(rows,actual)
  (ROOT/('receipts/verified-'+name+'.json')).write_text(json.dumps({'at':now(),'rows':len(actual),'all_values_match':True,'remaining_create':0},ensure_ascii=False),encoding='utf-8')
  print(json.dumps({'table':name,'new':len(pending),'verified':len(actual),'has_more':r['has_more']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
