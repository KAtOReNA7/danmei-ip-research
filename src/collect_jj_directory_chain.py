"""Continue an observed official next-page chain; keep discovery separate from qualification."""
from research import *
from urllib.parse import urlencode,urlunparse

def collect(previous,limit,partition,prefix,include_seed=False):
    seed=json.loads((ROOT/previous).read_text(encoding='utf-8'));url=seed['url'] if include_seed else seed['next_url'];result=[]
    c=connect()
    for _ in range(limit):
        parsed=urlparse(url);q=parse_qs(parsed.query,keep_blank_values=True)
        assert parsed.hostname=='www.jjwxc.net' and parsed.path=='/bookbase.php'
        page=max(1,int(q['page'][0]));cid=key('dir',partition,page);path=ROOT/'data'/f'{prefix}-page{page:03}.json'
        if path.exists():
            d=json.loads(path.read_text(encoding='utf-8'))
            if d.get('status')!='captured':break
            assert d['url']==url
        else:
            try:
                soup=fetch(url);rows=[]
                for tr in soup.select('tr'):
                    cells=tr.find_all('td',recursive=False)
                    if len(cells)!=7:continue
                    a=cells[1].find('a',href=re.compile(r'onebook\.php\?novelid='))
                    if not a:continue
                    author=cells[0].find('a')
                    rows.append([a['href'],a.get_text(' ',strip=True),author.get_text(' ',strip=True) if author else cells[0].get_text(' ',strip=True),cells[2].get_text(' ',strip=True),cells[3].get_text(' ',strip=True),cells[6].get_text(' ',strip=True)])
                assert rows and len(rows)<=100,'No valid catalog rows; authentication/access or parsing needs review'
                assert all('纯爱' in r[3] or r[3] in ('','/') for r in rows),'Unexpected category; inspect source'
                nexts={urljoin(url,a['href']) for a in soup.select('a[href]') if a.get_text(strip=True)=='下一页'}
                assert len(nexts)<=1,'Ambiguous next page'
                nxt=next(iter(nexts),None)
                if nxt:
                    p=urlparse(nxt);nq=parse_qs(p.query,keep_blank_values=True)
                    for token in ('sign','jsver','time'):nq.pop(token,None)
                    nxt=urlunparse(p._replace(query=urlencode(nq,doseq=True)))
                    assert p.hostname==parsed.hostname and p.path==parsed.path
                    assert int(nq['page'][0])==page+1,'Not the next observed page'
                    assert {k:v for k,v in nq.items() if k not in ('page','m_p')}=={k:v for k,v in q.items() if k not in ('page','m_p','sign','jsver','time')},'Catalog filters changed'
                d={'status':'captured','page':page,'url':url,'title':soup.title.get_text(strip=True),'captured_at':now(),'method':'公开HTTP；沿已观察官方下一页链接；仅目录必要元数据，不存正文/实时指标','rows':rows,'next_url':nxt,'displayed_pages_raw':re.findall(r'共\s*(\d+)\s*页',soup.get_text(' ',strip=True))}
                path.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
            except Exception as e:
                blocked={'status':'blocked_or_failed','url':url,'captured_at':now(),'error':str(e),'next_action':'暂停本来源，保留游标；不绕过，继续独立来源'}
                path.write_text(json.dumps(blocked,ensure_ascii=False,indent=2),encoding='utf-8')
                upsert(c,'coverage',dict(id=key('dir-access',partition,page),task_type='directory',partition=partition,status='访问受阻',query_scope=url,cursor=str(page),gap=str(e),last_run=now()));c.commit()
                print(json.dumps(blocked,ensure_ascii=False),flush=True);break
        if not c.execute('select 1 from coverage where id=?',(cid,)).fetchone():
            eid=evidence(c,url,d['title'],d,'晋江文学城',method=d['method'],accessed=d['captured_at']);ids=[];new=0;conflicts=[]
            for link,title,author,cat,serial,date in d['rows']:
                sid=parse_qs(urlparse(link).query)['novelid'][0];ids.append(sid)
                old=c.execute("select * from works where platform='晋江' and source_id=?",(sid,)).fetchone()
                if old:
                    if (old['title'],old['author'])!=(title,author):conflicts.append({'source_id':sid,'saved':[old['title'],old['author']],'directory':[title,author]})
                    continue
                wid=add_work(c,'晋江',sid,title,author,cat,serial,urljoin(url,link),eid,basis='官方目录候选；平台分类、原发及作品签约分别核；锁删与遮蔽记录保留')
                c.execute('update works set published_at=?,published_precision=? where id=?',(date or None,'目录原始显示；非已证首次原发日',wid));new+=1
            assert len(ids)==len(set(ids)),'Duplicate IDs within page'
            upsert(c,'coverage',dict(id=cid,task_type='directory',partition=partition,status='已采集',query_scope=url,cursor=f'显示第{page}页；下一链接已保存',displayed_total=json.dumps(d['displayed_pages_raw']),discovered=len(ids),new_unique=new,first_id=ids[0],last_id=ids[-1],evidence_id=eid,gap='当前分页快照不是完整历史；资格、原发、锁删迁移及逐作售出尚待调查；页数不当去重总体',last_run=d['captured_at']))
            c.commit();r={'page':page,'rows':len(ids),'new':new,'identity_conflicts':conflicts};result.append(r);print(json.dumps(r,ensure_ascii=False),flush=True)
        url=d['next_url']
        if not url:break
    c.close();return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--from-capture',required=True);p.add_argument('--pages',type=int,default=3);p.add_argument('--partition',required=True);p.add_argument('--prefix',required=True);p.add_argument('--include-seed',action='store_true',help='Capture the observed seed URL itself before following its next link');a=p.parse_args()
    result=collect(a.from_capture,a.pages,a.partition,a.prefix,a.include_seed)
    (ROOT/'data'/f'{a.prefix}-last-run.json').write_text(json.dumps({'at':now(),'result':result},ensure_ascii=False,indent=2),encoding='utf-8')
    export()
