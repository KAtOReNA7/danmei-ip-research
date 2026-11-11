from research import *
selected=json.loads((ROOT/'data/sample_manifest.json').read_text(encoding='utf-8'))
for pid in [w['source_id'] for w in selected if w['platform']=='晋江']:
    try:jj_detail(pid,as_sample=True)
    except Exception as e:print('DETAIL_FAILED',pid,str(e),flush=True)
    time.sleep(1.2)
