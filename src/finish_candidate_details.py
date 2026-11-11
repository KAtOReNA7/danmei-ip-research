"""Finite continuation for the existing JJ candidate queue; never a scheduled job."""
import contextlib,traceback
from research import *
from continue_batch import run as collect
from feishu_incremental import run as sync
from save_progress import save
from validate import main as validate
def main(start,size):
 for index in range(start,start+20):
  c=connect();remaining=c.execute('select count(*) from works where '+JJ_PENDING_WHERE).fetchone()[0];c.close()
  if not remaining:print('ACCESSIBLE_JJ_DETAIL_QUEUE_COMPLETE; work-specific blocked records remain in coverage',flush=True);return
  batch=f'p1-{index:03d}';log=ROOT/'receipts'/f'{batch}-execution.log'
  print(json.dumps({'batch':batch,'remaining':remaining,'started':now()},ensure_ascii=False),flush=True)
  try:
   with log.open('a',encoding='utf-8') as out,contextlib.redirect_stdout(out):
    collect(batch,size);save(batch);validate()
    state=json.loads((ROOT/'data'/f'{batch}.json').read_text(encoding='utf-8'))
    sync(batch);save(batch,f'receipts/{batch}/validation.json');backup()
   blocked=any(x['status']!='已采集' and not x.get('error','').startswith('作品页显示被锁定或删除') for x in state['results'].values())
   print(json.dumps({'batch':batch,'attempted':len(state['results']),'collected':sum(x['status']=='已采集' for x in state['results'].values()),'blocked':blocked,'cloud_readback':'complete','saved':now()},ensure_ascii=False),flush=True)
   if blocked:return
  except Exception:
   with log.open('a',encoding='utf-8') as out:traceback.print_exc(file=out)
   save(batch);raise
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=4);p.add_argument('--size',type=int,default=100);a=p.parse_args();main(a.start,a.size)
