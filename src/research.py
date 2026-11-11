"""One-off evidence-backed research. Public metadata only; no chapter fetches."""
from __future__ import annotations
import argparse, csv, hashlib, json, re, sqlite3, time, zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
TZ=timezone(timedelta(hours=8))
MEDIA=['电子书','有声书','广播剧','漫画','动画','影视短剧','游戏','官方周边联名','舞台线下']
JJ_PENDING_WHERE="platform='晋江' and signing_evidence is null and not exists (select 1 from coverage cv where cv.work_id=works.id and cv.media='电子书' and cv.status='访问受阻' and cv.gap like '作品页显示被锁定或删除%')"

class WorkUnavailable(RuntimeError):
    """A specific work is locked/deleted; other public works remain independent."""
    pass

def jj_identity(page_title,author_links=None):
    # The site's outer book brackets may contain another pair in the actual title.
    # Anchor the author at the site suffix rather than the first underscore.
    if author_links:
        pairs=set()
        for link in author_links:
            author=link['text']
            match=re.match(r'^《(.*)》'+re.escape(author)+r'(?:_|$)',page_title)
            if match:pairs.add((match.group(1),author))
        return next(iter(pairs)) if len(pairs)==1 else None
    match=re.match(r'^《(.*)》(.+?)_晋江文学城(?:_|$)',page_title)
    return (match.group(1),match.group(2)) if match else None
def now(): return datetime.now(TZ).isoformat(timespec='seconds')
def key(prefix,*parts): return prefix+'_'+hashlib.sha256(json.dumps(parts,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:20]
def connect(path=None):
    for d in ['data','evidence/http','exports','receipts','backups']: (ROOT/d).mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(path or ROOT/'data/research.sqlite'); c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.executescript((ROOT/'src/schema.sql').read_text(encoding='utf-8'))
    return c
def upsert(c,table,row):
    cols=list(row); q=','.join('?' for _ in cols)
    c.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({q}) ON CONFLICT(id) DO UPDATE SET "+','.join(f'{x}=excluded.{x}' for x in cols if x!='id'),[json.dumps(row[x],ensure_ascii=False) if isinstance(row[x],(dict,list)) else row[x] for x in cols])
def evidence(c,url,title,body,subject=None,status='官方直接证据',method='HTTP',published=None,accessed=None):
    stamp=accessed or now(); eid=key('ev',url,body,stamp)
    rel=f'evidence/http/{eid}.json'
    doc={'url':url,'title':title,'subject':subject,'published_at':published,'accessed_at':stamp,'method':method,'necessary_metadata':body}
    raw=json.dumps(doc,ensure_ascii=False,indent=2).encode(); (ROOT/rel).write_bytes(raw)
    upsert(c,'evidence',dict(id=eid,url=url,title=title,subject=subject,published_at=published,accessed_at=stamp,file_path=rel,sha256=hashlib.sha256(raw).hexdigest(),status=status,method=method))
    return eid
def add_work(c,platform,pid,title,author,category,status,url,eid,basis='平台作品页/分类目录收录；原发与签约细项待核',inclusion='待核'):
    wid=key('w',platform,str(pid))
    existing=c.execute('select * from works where id=?',(wid,)).fetchone()
    if existing and existing['inclusion_status']=='已确认' and inclusion!='已确认':
        inclusion=existing['inclusion_status']; basis=existing['inclusion_basis']; eid=existing['identity_evidence']
    aliases=json.loads(existing['aliases']) if existing and existing['aliases'] else []
    upsert(c,'works',dict(id=wid,title=title,aliases=aliases,author=author,platform=platform,source_id=str(pid),source_url=url,category_raw=category,category_mapped='纯爱' if category and '纯爱' in category else None,serial_status=status,inclusion_status=inclusion,inclusion_basis=basis,identity_evidence=eid,first_seen=existing['first_seen'] if existing else now(),last_seen=now()))
    for media in MEDIA:
        cid=key('cov',wid,media)
        c.execute('INSERT OR IGNORE INTO coverage(id,task_type,work_id,media,status,query_scope,last_run) VALUES(?,?,?,?,?,?,?)',(cid,'work_media',wid,media,'未调查','尚未执行',now()))
    return wid
def checked(c,wid,media,status,scope,eid=None,gap=None):
    upsert(c,'coverage',dict(id=key('cov',wid,media),task_type='work_media',work_id=wid,media=media,status=status,query_scope=scope,evidence_id=eid,gap=gap,last_run=now()))
    upsert(c,'check_history',dict(id=key('check',wid,media,scope,eid),work_id=wid,media=media,status=status,query_scope=scope,evidence_id=eid,checked_at=now(),gap=gap))
def fetch(url):
    # One request, no auth and no anti-bot workarounds. Cache at caller's batch boundary.
    r=requests.get(url,timeout=25,headers={'User-Agent':'danmei-ip-research/0.1 (one-off public metadata research)'})
    r.raise_for_status()
    encoding='gb18030' if 'jjwxc' in url else 'utf-8'
    text=r.content.decode(encoding,errors='replace')
    if any(x in text[:3000] for x in ['访问过于频繁','请完成验证','Access Denied','Just a moment...']): raise RuntimeError('access challenge; stop, do not bypass')
    return BeautifulSoup(text,'html.parser')
def jj_directory(start=1,pages=1,params=None,batch='jj-latest'):
    c=connect(); base='https://www.jjwxc.net/bookbase.php'
    params=params or {'fw':'0','yc':'0','xx':'2','mainview':'0','sd':'0','lx':'0','bq':'0','sortType':'3','isfinish':'0'}
    from urllib.parse import urlencode
    for page in range(start,start+pages):
        cid=key('dir',batch,page)
        if c.execute('select 1 from coverage where id=? and status=?',(cid,'已采集')).fetchone(): continue
        url=base+'?'+urlencode({**params,'page':page})
        try:
            s=fetch(url); rows=[]
            for tr in s.select('tr'):
                cells=tr.find_all('td',recursive=False)
                if len(cells)!=7: continue
                a=cells[1].find('a',href=re.compile('onebook.php'))
                if not a: continue
                t=[x.get_text(' ',strip=True) for x in cells]
                if '纯爱' not in t[2]: continue
                u=urljoin(base,a.get('href')); pid=parse_qs(urlparse(u).query).get('novelid',[None])[0]
                if not pid: continue
                rows.append(dict(source_id=pid,title=a.get_text(strip=True),author=t[0],category=t[2],status=t[3],words=t[4],points=t[5],published_raw=t[6],url=u))
            txt=s.get_text(' ',strip=True); totals=re.findall(r'共\s*(\d+)\s*页',txt)
            body={'query':params,'page':page,'displayed_pages':totals,'rows':rows,'next_links':[(a.get_text(strip=True),urljoin(base,a.get('href',''))) for a in s.find_all('a') if a.get_text(strip=True) in ['下一页','末页']]}
            eid=evidence(c,url,'晋江作品库：纯爱目录',body,'晋江文学城')
            if not rows: raise RuntimeError('zero parsed rows; inspect evidence '+eid)
            before=c.execute('select count(*) from works').fetchone()[0]
            for w in rows:
                # Directory establishes platform/category, but not original-publication or per-work signing.
                wid=add_work(c,'晋江',w['source_id'],w['title'],w['author'],w['category'],w['status'],w['url'],eid)
                c.execute('update works set published_at=?,published_precision=? where id=?',(w['published_raw'],'second',wid))
            after=c.execute('select count(*) from works').fetchone()[0]
            upsert(c,'coverage',dict(id=cid,task_type='directory',partition=batch,status='已采集',query_scope=params,cursor=str(page),displayed_total=totals[0] if totals else None,discovered=len(rows),new_unique=after-before,first_id=rows[0]['source_id'],last_id=rows[-1]['source_id'],evidence_id=eid,gap='当前可见目录；历史锁删/迁移及原发/签约待核；总页数不是全量作品分母',last_run=now()))
            c.commit(); print(json.dumps({'page':page,'rows':len(rows),'new':after-before,'pages_displayed':totals},ensure_ascii=False),flush=True)
        except Exception as e:
            upsert(c,'coverage',dict(id=cid,task_type='directory',partition=batch,status='访问受阻',query_scope=url,cursor=str(page),gap=str(e),last_run=now())); c.commit(); print(str(e),flush=True); break
        time.sleep(1.2)
    c.close()
def jj_detail(pid,as_sample=False,quiet=False):
    c=connect(); url=f'https://www.jjwxc.net/onebook.php?novelid={pid}'
    s=fetch(url); text=s.get_text(' ',strip=True)
    title=s.title.get_text() if s.title else ''
    meta=[]
    for li in s.select('li'):
        t=li.get_text(' ',strip=True)
        if any(x in t for x in ['文章类型','文章进度','签约状态','全文字数','作品视角']): meta.append(t)
    metrics={}
    for label in ['总书评数','当前被收藏数','营养液数','文章积分']:
        m=re.search(label+r'[:：]\s*([\d,]+)',text)
        metrics[label]=m.group(1) if m else None
    imgs=[i.get('title') or i.get('alt') for i in s.select('img') if any(x in str(i) for x in ['签约','出版','动漫','广播','有声','衍生'])]
    author=s.select_one('[itemprop=author]'); name=s.select_one('[itemprop=articleSection]')
    a=[{'text':a.get_text(' ',strip=True),'url':urljoin(url,a['href'])} for a in s.select('a[href]') if 'authorid=' in a['href']]
    source={'page_title':title,'metadata':meta,'metrics':metrics,'rights_badges':imgs,'author_links':a[:3], 'vip_present':'[VIP]' in text}
    eid=evidence(c,url,title,source,'晋江文学城')
    cat=next((x.split('：',1)[-1].strip() for x in meta if '文章类型' in x),None)
    serial=next((x.split('：',1)[-1].strip() for x in meta if '文章进度' in x),None)
    identity=jj_identity(title,a)
    signed=next((x for x in meta if '签约状态' in x),None)
    if not identity or not cat or not signed:
        if any('被锁定或删除文章' in link['text'] for link in a):
            c.commit();c.close()
            raise WorkUnavailable('作品页显示被锁定或删除文章的作者专栏；具体锁定或删除状态不明；证据='+eid)
        c.close()
        raise RuntimeError('作品身份/分类/签约元数据未完整返回；保留原记录，不覆盖为零或猜测标题')
    wtitle,wauthor=identity
    confirmed=bool(cat and '纯爱' in cat and signed and '未签约' not in signed and '签约' in signed)
    wid=add_work(c,'晋江',pid,wtitle,wauthor,cat,serial,url,eid,'作品页题材；'+str(signed),'已确认' if confirmed else '待核')
    c.execute('update works set signing_raw=?,signing_evidence=?,sample=max(sample,?) where id=?',(signed,eid,int(as_sample),wid))
    for label,val in metrics.items():
        upsert(c,'observations',dict(id=key('obs',wid,label,eid),work_id=wid,metric_raw=label,metric_standard={'当前被收藏数':'作品收藏','总书评数':'评论','文章积分':'平台积分','营养液数':'营养液'}[label],raw_value=val,value=float(val.replace(',','')) if val is not None else None,unit='平台原单位',temporal_type='当前显示累计',observed_at=now(),period_start=None,period_end=None,precision='displayed_integer' if val else 'missing',missing_reason=None if val else '页面未返回可解析数值',comparison_version='jjwxc:'+label+':v1',evidence_id=eid))
    if '[VIP]' in text:
        p=key('p','晋江电子连载',pid)
        upsert(c,'products',dict(id=p,title=wtitle+'（晋江电子连载）',media='电子书',language='简体中文',markets=None,platform='晋江',source_id=str(pid),source_url=url,pay_model='VIP章节付费；不采集正文',status='当前可见',confirmation='已确认' if confirmed else '发现待核',evidence_id=eid))
        c.execute('INSERT OR IGNORE INTO product_works VALUES(?,?,?)',(p,wid,eid))
        checked(c,wid,'电子书','已确认' if confirmed else '发现待核','晋江作品页：VIP标识、身份及题材',eid,'未核实销售、订阅人数与发行市场')
    else:
        checked(c,wid,'电子书','发现待核','晋江作品页：在线连载元数据；未发现本页VIP标识',eid,'原发资格或付费商业模式待核；无VIP不代表没有站外电子版')
    c.commit()
    result={'id':wid,'title':wtitle,'source':source,'inclusion':confirmed,'evidence_id':eid}
    if not quiet: print(json.dumps(result,ensure_ascii=False))
    c.close();return result
def export():
    c=connect(); counts={}
    for t in ['works','products','product_works','events','observations','evidence','coverage','check_history','source_matrix','exclusions']:
        rows=[dict(r) for r in c.execute('select * from '+t)]; counts[t]=len(rows)
        (ROOT/f'exports/{t}.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
        cols=[r[1] for r in c.execute('pragma table_info('+t+')')]
        with (ROOT/f'exports/{t}.csv').open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(rows)
    summary={'generated_at':now(),'cutoff':'2026-11-10','counts':counts,'denominator':None,'inclusion':dict(c.execute('select inclusion_status,count(*) from works group by inclusion_status').fetchall()),'media':{},'directory_partitions':[dict(r) for r in c.execute("select partition,status,count(*) pages,sum(discovered) rows,sum(new_unique) new_unique from coverage where task_type='directory' group by partition,status")], 'sample_by_platform':dict(c.execute('select platform,count(*) from works where sample=1 group by platform').fetchall())}
    for m in MEDIA: summary['media'][m]=dict(c.execute('select status,count(*) from coverage where media=? group by status',(m,)).fetchall())
    (ROOT/'exports/coverage_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'receipts/validation.json').write_text(json.dumps({'at':now(),'integrity':c.execute('pragma integrity_check').fetchone()[0],'foreign_key_errors':[list(r) for r in c.execute('pragma foreign_key_check')],'counts':counts},ensure_ascii=False,indent=2),encoding='utf-8'); c.close(); print(json.dumps(summary,ensure_ascii=False,indent=2))
def backup():
    c=connect(); stamp=datetime.now(TZ).strftime('%Y%m%d-%H%M%S'); dest=ROOT/'backups'/stamp;dest.mkdir()
    with sqlite3.connect(dest/'research.sqlite') as b:c.backup(b)
    c.close(); files=[*sorted((ROOT/'evidence').rglob('*')),*sorted((ROOT/'exports').rglob('*')),*sorted((ROOT/'data').glob('*.json')),*sorted((ROOT/'data').glob('*.py')),*sorted((ROOT/'receipts').rglob('*'))]
    manifest={}
    with zipfile.ZipFile(dest/'research-evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
        z.write(dest/'research.sqlite','data/research.sqlite');manifest['data/research.sqlite']=hashlib.sha256((dest/'research.sqlite').read_bytes()).hexdigest()
        for f in files:
            if f.is_file():
                n=f.relative_to(ROOT).as_posix();z.write(f,n);manifest[n]=hashlib.sha256(f.read_bytes()).hexdigest()
        z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(dest/'research-evidence.zip') as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(k)).hexdigest()==v for k,v in manifest.items())
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print(dest)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['init','jj-directory','jj-detail','export','backup']);p.add_argument('--start',type=int,default=1);p.add_argument('--pages',type=int,default=1);p.add_argument('--id');a=p.parse_args()
    if a.action=='init':connect().close()
    elif a.action=='jj-directory':jj_directory(a.start,a.pages)
    elif a.action=='jj-detail':jj_detail(a.id)
    elif a.action=='export':export()
    elif a.action=='backup':backup()
