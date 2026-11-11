"""Import saved IAB directory metadata without exporting authentication or live metrics."""
from research import *

def ingest(c,d,batch):
    assert d['method'].startswith('内置浏览器')
    assert urlparse(d['url']).hostname=='www.jjwxc.net'
    page=parse_qs(urlparse(d['url']).query)['page'][0]
    rows=[dict(zip(d['columns'],r)) for r in d['rows']]
    assert rows and len({r['source_id'] for r in rows})==len(rows)
    assert all(r['source_id'].isdigit() and '纯爱' in r['category'] for r in rows)
    # Use a stable import identity and original evidence on reruns.
    cid=key('dir',batch,page)
    prior=c.execute('select * from coverage where id=?',(cid,)).fetchone()
    if prior:return {'page':page,'rows':len(rows),'new':prior['new_unique'],'reused':True}
    eid=evidence(c,d['url'],d['title'],d,'晋江文学城',method=d['method'])
    added=0;overlap=[];conflicts=[]
    for r in rows:
        existing=c.execute("select * from works where platform='晋江' and source_id=?",(r['source_id'],)).fetchone()
        if existing:
            overlap.append(r['source_id'])
            if (existing['title'],existing['author'])!=(r['title'],r['author']):
                conflicts.append({'source_id':r['source_id'],'saved':[existing['title'],existing['author']],'directory':[r['title'],r['author']]})
            # A directory refresh must not downgrade stronger detail/qualification evidence.
            continue
        wid=add_work(c,'晋江',r['source_id'],r['title'],r['author'],r['category'],r['serial'],d['url_template'].format(source_id=r['source_id']),eid)
        c.execute('update works set published_at=?,published_precision=? where id=?',(r['published_raw'],'second',wid));added+=1
    old=c.execute("select * from coverage where task_type='directory' and cursor=? and status='访问受阻'",(page,)).fetchall()
    for r in old:
        c.execute("update coverage set status='历史访问受阻，已恢复',gap=gap || ?,last_run=? where id=?",('；'+d['captured_date']+'用户合法登录后IAB同页已采集；原失败证据保留；恢复证据='+eid,now(),r['id']))
    upsert(c,'coverage',dict(id=cid,task_type='directory',partition=batch,status='已采集',query_scope=d['url'],cursor=page,displayed_total=str(d.get('displayed_last_page')) if d.get('displayed_last_page') else None,discovered=len(rows),new_unique=added,first_id=rows[0]['source_id'],last_id=rows[-1]['source_id'],evidence_id=eid,gap='合法登录公开目录；采集日后于截止日，未采实时指标；历史锁删/迁移及资格仍待核；总页数不是去重作品分母',last_run=now()))
    upsert(c,'source_matrix',dict(id=key('source','晋江目录IAB'),media='作品目录',source_name='晋江分类目录（内置浏览器）',url=d['url'],events_available='平台显示发表日期；不直接证明原发',current_values='本批未采实时指标',historical_values='无完整历史目录证明',access_condition='用户合法登录IAB；不导出会话',test_result='目录第11页登录阻塞已解除；当前页可读，不能推定全站覆盖',evidence_id=eid,next_action='继续可见分页、其他年份及作者专栏；保留锁删迁移及重发待核'))
    return {'page':page,'rows':len(rows),'new':added,'overlap':len(overlap),'identity_conflicts':conflicts,'evidence_id':eid,'historical_blocks_resolved':len(old)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--file',required=True);p.add_argument('--batch',required=True);a=p.parse_args()
    d=json.loads((ROOT/a.file).read_text(encoding='utf-8'));c=connect();result=ingest(c,d,a.batch);c.commit();c.close()
    (ROOT/'data'/f'{a.batch}-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'data/directory-access.json').write_text(json.dumps({'at':now(),'jj_page11':'用户合法登录后已采集；原访问阻塞已解除，历史失败保留','capture':a.file,'result':result},ensure_ascii=False,indent=2),encoding='utf-8')
    export();print(json.dumps(result,ensure_ascii=False))
