"""Import human-reviewed limited searches without overwriting stronger evidence."""
from research import *

def run(batch):
 c=connect();seen=set();files=list(sorted((ROOT/'evidence/search').glob(batch+'-*.json')));assert files
 for f in files:
  d=json.loads(f.read_text(encoding='utf-8'));assert d['review_status']=='已调查未发现'
  assert len(d['works'])==len(d['queries'])
  stamp=datetime.strptime(d['captured_at'],'%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=timezone.utc).astimezone(TZ).isoformat()
  eid=evidence(c,'tool:web.search_query','候选作品非电子书媒介索引初查',d,'公开索引',status='未核实线索',method='实际查询及人工辨别审计；非未开发证明',accessed=stamp)
  for w,q in zip(d['works'],d['queries']):
   assert w['id'] not in seen and w['title'] in q and w['author'] in q;seen.add(w['id'])
   actual=c.execute('select source_id,title,author from works where id=?',(w['id'],)).fetchone()
   assert actual and actual['source_id']==w['source_id'] and actual['author']==w['author']
   for media in MEDIA[1:]:
    prior=c.execute('select status from coverage where work_id=? and media=?',(w['id'],media)).fetchone()
    assert prior and prior[0] in ['未调查','已调查未发现'],'Stronger or conflicting status; review before changing'
    checked(c,w['id'],media,'已调查未发现',q,eid,'仅中文书名+作者索引初查；未穷尽站内/海外译名/下架/历史；未发现不等于未开发')
 c.commit();c.close();export();print(json.dumps({'batch':batch,'works':len(seen),'media_checks':len(seen)*8},ensure_ascii=False))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--batch',required=True);a=p.parse_args();run(a.batch)
