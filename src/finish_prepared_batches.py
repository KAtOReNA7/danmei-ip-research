"""Run already reviewed local batches sequentially, with complete CLI readback."""
import contextlib,traceback
from research import *
from ingest_cp_continuation import run as cp
from ingest_commercial_continuation import run as commercial
from ingest_media_reviews import run as media
from feishu_evidence_fields import main as fields
from feishu_incremental import run as sync
from save_progress import save
from validate import main as validate

def main():
 qpath=ROOT/'data/queued-batches.json';queue=json.loads(qpath.read_text(encoding='utf-8'))
 # The caller must first observe termination of the other writer; no scheduled or detached continuation.
 fields()
 tasks=[('cp-detail-002',lambda:cp(ROOT/'data/cp-detail-continuation.json')),('commercial-002',lambda:commercial(ROOT/'data/commercial-continuation.json')),('media-003',lambda:media('media-003'))]
 for batch,ingest in tasks:
  print(json.dumps({'batch':batch,'started':now()},ensure_ascii=False),flush=True)
  log=ROOT/'receipts'/f'{batch}-execution.log'
  try:
   with log.open('a',encoding='utf-8') as out,contextlib.redirect_stdout(out):
    ingest();validate();save(batch);sync(batch);save(batch,f'receipts/{batch}/validation.json')
    for b in queue['batches']:
     if b['id']==batch:b.update(status='入库/导出/CLI全量回读完成',completed_at=now(),validation=f'receipts/{batch}/validation.json')
    qpath.write_text(json.dumps(queue,ensure_ascii=False,indent=2),encoding='utf-8');backup()
   print(json.dumps({'batch':batch,'status':'saved_and_readback_verified','at':now()},ensure_ascii=False),flush=True)
  except Exception:
   with log.open('a',encoding='utf-8') as out:traceback.print_exc(file=out)
   save(batch);raise
 queue['status']='三批已完成入库、导出、CLI完整回读和本地快照；行业调查仍部分完成'
 qpath.write_text(json.dumps(queue,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
