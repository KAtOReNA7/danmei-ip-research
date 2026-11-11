"""Import the reviewed, private commercial-facts manifest, not search guesses."""
from research import *

def run(path):
 d=json.loads(Path(path).read_text(encoding='utf-8'));c=connect()
 w=c.execute('select * from works where platform=? and source_id=?',(d['platform'],d['source_id'])).fetchone()
 assert w and w['category_mapped']=='纯爱';wid=w['id'];evs={};sources={s['key']:s for s in d['sources']}
 for s in d['sources']:
  evs[s['key']]=evidence(c,s['url'],s['title'],{'excerpt':s['excerpt'],'facts':s['facts'],'limitations':d['limitations'],'previous_category_evidence':w['signing_evidence']},s['subject'],status=s.get('status','官方直接证据'),method='web.open 官方公告必要摘录/结构化事实；索引线索单列',published=s.get('published'),accessed=d['captured_at'])
 # Platform classification and the work-specific official original-work credit jointly establish inclusion.
 c.execute("update works set inclusion_status='已确认',inclusion_basis=?,identity_evidence=? where id=?",(f"{w['platform']}作品页纯爱分类；漫画官微明确署名长佩文学、{w['author']}原著；不推及全部媒介权利",evs['comic-update'],wid))
 products={}
 for p in d['products']:
  pid=key('p',wid,p['media'],p.get('source_id') or p['title']);products[p['key']]=pid
  row={k:v for k,v in p.items() if k not in ['key','source']}
  row.update(id=pid,evidence_id=evs[p['source']]);row.setdefault('source_url',sources[p['source']]['url'])
  upsert(c,'products',row);c.execute('INSERT OR IGNORE INTO product_works VALUES(?,?,?)',(pid,wid,evs[p['source']]))
 for e in d['events']:
  upsert(c,'events',dict(id=key('event',wid,products[e['product']],e['type'],e['date']),work_id=wid,product_id=products[e['product']],event_type=e['type'],event_time=e['date'],time_precision='day',description=sources[e['source']]['facts'],window_role='观察窗口内',confirmation='已确认',evidence_id=evs[e['source']]))
 checked(c,wid,'漫画','已确认','快看项目入口及漫画官微2024/2025/2026公告；必要日期区分',evs['comic-update'],'新确认作品归属与漫画运营；季级版本及付费/免费更新日期待分；异常聚合数不计确认指标')
 checked(c,wid,'官方周边联名','已确认','认证官微/QQ音乐/漫库官方公告：授权卡牌和联名礼盒',evs['cards'],'公告与执行分开；未核SKU、销量、收入及具体配送市场；混合礼盒收入不拆分')
 upsert(c,'exclusions',dict(id=key('exclude',sources['paper-exclude']['url']),source_url=sources['paper-exclude']['url'],title=sources['paper-exclude']['title'],reason='实体漫画出版排除；不计电子漫画或周边销售',evidence_id=evs['paper-exclude']))
 for f in sorted((ROOT/'evidence/search').glob('cp_*media.json'))+sorted((ROOT/'evidence/search').glob('cp_ebooks*.json'))+sorted((ROOT/'evidence/search').glob('cp_merchmore.json')):
  body=json.loads(f.read_text(encoding='utf-8'))
  if 'captured_at' not in body:
   body['captured_at']=now();f.write_text(json.dumps(body,ensure_ascii=False,indent=2),encoding='utf-8')
  body['timestamp_note']='查询日期精度为日；accessed_at为整理入库时间'
  evidence(c,'tool:web.search_query','商业与海外电子书补充索引核查',body,'公开索引',status='未核实线索',method='查询审计',accessed=body['captured_at'])
 # The nine newly qualified candidates were actually searched; leave every other work/media untouched.
 manifest=json.loads((ROOT/'data/p1-004.json').read_text(encoding='utf-8'))
 selected=[x for x in manifest['works'] if manifest['results'].get(x['source_id'],{}).get('inclusion')]
 assert len(selected)==9
 for i,f in enumerate(sorted((ROOT/'evidence/search').glob('p100*.json'))):
  body=json.loads(f.read_text(encoding='utf-8'))
  if 'captured_at' not in body:
   body['captured_at']=now();f.write_text(json.dumps(body,ensure_ascii=False,indent=2),encoding='utf-8')
  eid=evidence(c,'tool:web.search_query','晋江新增确认候选多媒介索引初查',body,'公开索引',status='未核实线索',method='查询审计',accessed=body['captured_at'])
  for j,work in enumerate(selected[i*4:i*4+len(body['queries'])]):
   assert work['author'] in body['queries'][j]
   for media in MEDIA[1:]:checked(c,work['id'],media,'已调查未发现','中文书名+作者+多媒介词公开索引初查',eid,'限本次索引结果；未穷尽站内、海外译名、下架和历史数据，不代表未开发或全媒介完成')
 for media,name,src in [('漫画','漫画官方认证公告','comic-update'),('官方周边联名','品牌官方认证公告','cards')]:
  upsert(c,'source_matrix',dict(id=key('source',name),media=media,source_name=name,url=sources[src]['url'],events_available='官方发布时间、企划预告与开售状态可区分',current_values='本批未确认销量或收入；不采用缓存社交互动数',historical_values='有2024/2025/2026公告；无连续销售序列',access_condition='新浪公开展示认证官微原帖',test_result='已验证目标作品关联；快看聚合页指标有异常，另存争议',evidence_id=evs[src],next_action='跟进实际执行、市场与SKU；不能以预告代替上线'))
 c.commit();c.close();export()
 print(json.dumps({'batch':d['batch'],'new_products':len(d['products']),'new_events':len(d['events']),'additional_media_initial_checks':9},ensure_ascii=False))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('path');a=p.parse_args();run(a.path)
