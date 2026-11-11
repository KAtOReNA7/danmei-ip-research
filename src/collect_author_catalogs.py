"""Expand discovery through evidenced author columns; never infer per-work signing."""
from research import *

def collect(author,url,batch):
    assert urlparse(url).hostname=='www.jjwxc.net' and urlparse(url).path=='/oneauthor.php'
    s=fetch(url);title=s.title.get_text() if s.title else ''
    assert title.startswith(author+' 的专栏:'),'Author identity differs; inspect before import'
    rows=[];excluded=[]
    for tr in s.select('tr'):
        cells=tr.find_all('td',recursive=False)
        if len(cells)!=6:continue
        a=cells[0].find('a',href=re.compile('onebook.php'))
        if not a:continue
        cat=cells[1].get_text(' ',strip=True)
        locked='锁' in cells[0].get_text(' ',strip=True)
        if '纯爱' not in cat and not (locked and cat in ['/','']):
            excluded.append({'title_raw':a.get_text(' ',strip=True),'category_raw':cat,'url':urljoin(url,a['href']),'reason':'专栏明确显示非纯爱类别；不推断锁文完整书名或改判类别'})
            continue
        u=urljoin(url,a['href']);pid=parse_qs(urlparse(u).query).get('novelid',[None])[0]
        if not pid:continue
        rows.append({'source_id':pid,'title':a.get_text(' ',strip=True),'author':author,'category':cat,'serial':cells[2].get_text(' ',strip=True),'published_raw':cells[5].get_text(' ',strip=True),'url':u})
    assert rows,'No eligible parsed rows; stop source'
    assert len(rows)==len({r['source_id'] for r in rows})
    d={'url':url,'title':title,'captured_at':now(),'method':'HTTP公开作者专栏；只存作品目录元数据，不采实时指标或正文','scope':'已发现作者专栏补充；不构成全站随机或代表性样本；作者签约不推及作品；锁文题材不可见时保留待核；历史锁删迁移仍未穷尽','rows':rows,'excluded_rows':excluded}
    (ROOT/'data'/f'{batch}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    return d

def ingest(c,d,batch):
    cid=key('dir',batch,d['url']);prior=c.execute('select * from coverage where id=?',(cid,)).fetchone()
    if prior:return {'rows':prior['discovered'],'new':prior['new_unique'],'reused':True}
    eid=evidence(c,d['url'],d['title'],d,'晋江文学城',method=d['method'],accessed=d['captured_at']);added=0
    for r in d['rows']:
        if c.execute("select 1 from works where platform='晋江' and source_id=?",(r['source_id'],)).fetchone():continue
        basis='官方作者专栏收录及纯爱分类；原发和作品签约需详情复核，不能由作者签约推及全部作品' if '纯爱' in r['category'] else '官方作者专栏锁文记录；完整书名、题材及原发或作品签约均待核，不由作者身份推断'
        wid=add_work(c,'晋江',r['source_id'],r['title'],r['author'],r['category'],r['serial'],r['url'],eid,basis=basis)
        published=r['published_raw'] or None
        precision=('second' if re.fullmatch(r'\d{4}-\d\d-\d\d \d\d:\d\d:\d\d',published) else 'raw') if published else None
        c.execute('update works set published_at=?,published_precision=? where id=?',(published,precision,wid));added+=1
    for x in d.get('excluded_rows',[]):
        upsert(c,'exclusions',dict(id=key('exclude','author-category',x['url']),source_url=x['url'],title=x['title_raw'],reason=x['reason']+'；原文类别='+x['category_raw']+'；仅按本次公开类别记录，后续若分类更正可复核',evidence_id=eid))
    upsert(c,'coverage',dict(id=cid,task_type='directory',partition='jj-author-catalog',query_scope=d['url'],cursor=d['url'].split('authorid=')[-1],status='已采集',discovered=len(d['rows']),new_unique=added,first_id=d['rows'][0]['source_id'],last_id=d['rows'][-1]['source_id'],evidence_id=eid,gap=d['scope'],last_run=now()))
    return {'rows':len(d['rows']),'new':added,'evidence_id':eid}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--author',required=True);p.add_argument('--url',required=True);p.add_argument('--batch',required=True);p.add_argument('--capture-only',action='store_true');a=p.parse_args()
    path=ROOT/'data'/f'{a.batch}.json';d=json.loads(path.read_text(encoding='utf-8')) if path.exists() else collect(a.author,a.url,a.batch)
    if a.capture_only:print(json.dumps({'rows':len(d['rows']),'capture':str(path)},ensure_ascii=False))
    else:
        c=connect();r=ingest(c,d,a.batch);c.commit();c.close();export();print(json.dumps(r,ensure_ascii=False))
