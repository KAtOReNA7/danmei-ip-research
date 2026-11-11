"""Persist finite, resumable metadata batches. A batch does not redefine full scope."""
from research import *
def run(batch,size):
 path=ROOT/'data'/f'{batch}.json';c=connect()
 if path.exists(): state=json.loads(path.read_text(encoding='utf-8'))
 else:
  rows=[dict(r) for r in c.execute('select * from works where '+JJ_PENDING_WHERE+' order by cast(source_id as integer) limit ?',(size,))]
  state={'batch':batch,'started_at':now(),'cutoff':'2026-11-10','selection':'所有待详情核验晋江候选按真实来源ID升序；不以热度筛选','works':rows,'results':{}}
 c.close()
 def save():path.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
 save()
 for w in state['works']:
  pid=w['source_id']
  if pid in state['results']:continue
  try:
   r=jj_detail(pid,quiet=True);state['results'][pid]={'status':'已采集','at':now(),'evidence_id':r['evidence_id'],'inclusion':r['inclusion'],'title':r['title']}
   print(json.dumps({'batch':batch,'source_id':pid,'title':r['title'],'confirmed':r['inclusion']},ensure_ascii=False),flush=True)
  except (requests.RequestException,RuntimeError) as e:
   state['results'][pid]={'status':'访问受阻','at':now(),'error':str(e)}
   c=connect();eid=evidence(c,w['source_url'],'作品详情访问失败',{'error':str(e),'batch':batch},w['platform'],status='未核实线索',method='HTTP访问审计')
   checked(c,w['id'],'电子书','访问受阻','作品详情页公开访问',eid,str(e));c.commit();c.close()
   save()
   if isinstance(e,WorkUnavailable):
    print('WORK_UNAVAILABLE',str(e),flush=True);time.sleep(1.5);continue
   print('STOP_SOURCE',str(e),flush=True);break
  save();time.sleep(1.5)
 state['saved_at']=now();save();export()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--batch',required=True);p.add_argument('--size',type=int,default=30);a=p.parse_args();run(a.batch,a.size)
