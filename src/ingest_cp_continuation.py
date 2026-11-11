"""Import a reviewed private DOM capture after the other writer has finished."""
from research import *

def run(path):
 data=json.loads(Path(path).read_text(encoding='utf-8'));c=connect();ids=[]
 for row in data['rows']:
  w=dict(zip(data['columns'],row));pid=w['source_id']
  old=c.execute("select * from works where platform='长佩' and source_id=?",(pid,)).fetchone()
  assert old and old['title']==w['title'] and old['author']==w['author']
  assert '纯爱' in w['category'] and w['title'] and w['intro_date']
  stamp=datetime.fromisoformat(w['accessed_utc'].replace('Z','+00:00')).astimezone(TZ).isoformat()
  body={'capture':w,'limitations':data['limitations'],'batch':data['batch']}
  eid=evidence(c,old['source_url'],w['title']+'_'+w['author']+'著_长佩文学网',body,'长佩文学',method=data['method'],accessed=stamp)
  wid=add_work(c,'长佩',pid,w['title'],w['author'],w['category'],w['serial'],old['source_url'],eid)
  c.execute('update works set signing_raw=?,signing_evidence=? where id=?',('本次详情未显示作品签约字段；原发也待证',eid,wid))
  for label in ['人阅读','人气','海星']:
   raw=w[label];val=float(raw.replace(',','').replace('万',''))*(10000 if '万' in raw else 1) if raw is not None else None
   upsert(c,'observations',dict(id=key('obs',wid,label,eid),work_id=wid,metric_raw=label,metric_standard='长佩'+label,raw_value=raw,value=val,unit='平台原单位',temporal_type='当前显示值_累计属性待核',observed_at=stamp,precision='rounded_display' if raw and '万' in raw else ('displayed_integer' if raw is not None else 'missing'),missing_reason=None if raw is not None else '完整加载页面未显示该指标；不填零',comparison_version='gongzicp:'+label+':v1',evidence_id=eid))
  checked(c,wid,'电子书','发现待核','长佩官方公开网页完整渲染：题材、状态、当前显示指标；未打开正文',eid,'读取器受阻已由公开网页元数据补充；原发/作品签约及付费方式仍待证；简介栏日期不等于开更日')
  product=key('p','长佩电子连载',pid)
  upsert(c,'products',dict(id=product,title=w['title']+'（长佩电子连载）',media='电子书',language='简体中文',platform='长佩',source_id=pid,source_url=old['source_url'],status='当前可见',confirmation='发现待核',evidence_id=eid))
  c.execute('INSERT OR IGNORE INTO product_works VALUES(?,?,?)',(product,wid,eid));ids.append(wid)
 for f in sorted((ROOT/'evidence/search').glob(data['batch']+'-deep*.json')):
  body=json.loads(f.read_text(encoding='utf-8'))
  if 'captured_at' not in body:
   body['captured_at']=now();f.write_text(json.dumps(body,ensure_ascii=False,indent=2),encoding='utf-8')
  body['timestamp_note']='查询日期为2026-11-10；秒级查询时间未保存，accessed_at为整理入库时间'
  evidence(c,'tool:web.search_query','长佩候选分媒介补充检索',body,'公开索引',method='查询审计；结果经人工辨别，不构成未开发证明',status='未核实线索',accessed=body['captured_at'])
 upsert(c,'source_matrix',dict(id=key('source','长佩公开网页详情'),media='电子书',source_name='长佩官方公开网页（完整渲染）',url='https://www.gongzicp.com/',events_available='作品状态可见；简介栏日期含义不能直接等同开更日',current_values='27部可读人气/海星；4部不显示人阅读，保留null',historical_values='仅本次显示值，无连续历史',access_condition='无登录的公开网页；不打开正文',test_result='公开网页可行；读取器4例限制仍保留历史审计',evidence_id=eid,next_action='补作品原发/签约和收费模式；作者签约不推及作品'))
 c.commit();c.close();export()
 print(json.dumps({'batch':data['batch'],'works':len(ids),'observations':len(ids)*3,'new_confirmed_commercial':0},ensure_ascii=False))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('path');a=p.parse_args();run(a.path)
