"""Capture work-specific identity/category/signing only, never import post-cutoff metrics."""
from research import *

def capture(w,batch):
    url=w['source_url'];s=fetch(url);title=s.title.get_text() if s.title else ''
    meta=[x.get_text(' ',strip=True) for x in s.select('li') if any(y in x.get_text() for y in ['文章类型','文章进度','签约状态'])]
    links=[{'text':a.get_text(' ',strip=True),'url':urljoin(url,a['href'])} for a in s.select('a[href]') if 'authorid=' in a['href']]
    identity=jj_identity(title,links)
    unavailable=any('被锁定或删除文章' in a['text'] for a in links)
    d={'batch':batch,'work_id':w['id'],'source_id':w['source_id'],'expected_identity':[w['title'],w['author']],'url':url,'captured_at':now(),'page_title':title,'metadata':meta,'author_links':links[:3],'parsed_identity':identity,'status':'作品锁删提示，具体状态待核' if unavailable else '待审阅','scope':'作品资格必要元数据；无实时指标、正文或付费章节；签约日期未知，不倒填截止日'}
    if not unavailable and (not identity or not any('文章类型' in x for x in meta) or not any('签约状态' in x for x in meta)):
        d['status']='元数据未完整返回，停止本来源批次'
    (ROOT/'data'/f"{batch}-{w['source_id']}.json").write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    return d

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True);p.add_argument('--limit',type=int,default=25);p.add_argument('--retry-network',action='store_true');a=p.parse_args();c=connect()
    queue=ROOT/'data'/f'{a.batch}-candidates.json'
    if queue.exists():works=json.loads(queue.read_text(encoding='utf-8'))
    else:
        works=[dict(r) for r in c.execute('select id,source_id,title,author,source_url from works where '+JJ_PENDING_WHERE+' order by cast(source_id as integer) limit ?',(a.limit,))]
        queue.write_text(json.dumps(works,ensure_ascii=False,indent=2),encoding='utf-8')
    c.close();results=[]
    for w in works:
        path=ROOT/'data'/f"{a.batch}-{w['source_id']}.json"
        try:
            d=json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
            if d is None or (a.retry_network and d['status']=='网络连接失败，停止本来源批次'):
                d=capture(w,a.batch)
        except requests.RequestException as exc:
            d={'batch':a.batch,'work_id':w['id'],'source_id':w['source_id'],'url':w['source_url'],'captured_at':now(),'parsed_identity':None,'metadata':[],'status':'网络连接失败，停止本来源批次','error_type':type(exc).__name__,'scope':'传输失败，不等于锁文、登录失败或作品不存在；不导入空值覆盖已有元数据'}
            path.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
        results.append({'work_id':w['id'],'source_id':w['source_id'],'identity':d['parsed_identity'],'status':d['status'],'metadata':d['metadata']})
        if d['status'] in ['元数据未完整返回，停止本来源批次','网络连接失败，停止本来源批次']:break
        time.sleep(1.2)
    (ROOT/'data'/f'{a.batch}-capture-log.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(results,ensure_ascii=False))
