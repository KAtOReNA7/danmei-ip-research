"""Persist reviewed mixed search results and explicit facts; no automatic inference from titles."""
from research import *

def ingest(c,d):
    evs={}
    for s in d['sources']:
        evs[s['key']]=evidence(c,s['url'],s['title'],s['facts'],s.get('subject'),status=s.get('status','官方直接证据'),method=s['method'],published=s.get('published'),accessed=s['captured_at'])
    for f in d.get('qualifications',[]):
        q=json.loads((ROOT/f).read_text(encoding='utf-8'));pid=parse_qs(urlparse(q['url']).query)['novelid'][0]
        w=c.execute("select * from works where platform='晋江' and source_id=?",(pid,)).fetchone();assert w
        identity=jj_identity(q['page_title'],q['author_links']);assert identity==(w['title'],w['author'])
        assert any('文章类型' in x and '纯爱' in x for x in q['metadata'])
        signed=next(x for x in q['metadata'] if '签约状态' in x);assert '已签约' in signed
        eid=evidence(c,q['url'],q['page_title'],q,'晋江文学城',method=q.get('method','HTTP资格必要元数据；无实时指标'),accessed=q['captured_at'])
        c.execute("update works set inclusion_status='已确认',inclusion_basis=?,signing_raw=?,signing_evidence=?,identity_evidence=? where id=?",('官方作品页纯爱分类及作品级已签约标记；采集时确认，签约发生日期未知，不倒填截止日',signed,eid,eid,w['id']))
    seen=set()
    for r in d['reviews']:
        wid=r['work_id'];assert wid not in seen;seen.add(wid)
        w=c.execute('select * from works where id=?',(wid,)).fetchone()
        # Search quotes delimit phrases; embedded ASCII quotes are sent as spaces.
        assert w and all(value in r['query'] or value.replace('"',' ') in r['query'] for value in (w['title'],w['author']))
        for media in r.get('checked_media',MEDIA[1:]):
            assert media in MEDIA
            status=r.get('statuses',{}).get(media,'已调查未发现')
            prior=c.execute('select status from coverage where work_id=? and media=?',(wid,media)).fetchone();assert prior and prior[0] in ['未调查',status],'Stronger or changed evidence needs explicit reconciliation'
            checked(c,wid,media,status,r['query'],evs[r['source']],r.get('gaps',{}).get(media,'仅中文书名+作者索引初查；未穷尽站内、海外译名、下架和历史；未发现不等于未开发'))
    for r in d.get('coverage_updates',[]):
        assert r['media'] in MEDIA and r['source'] in evs
        prior=c.execute('select status from coverage where work_id=? and media=?',(r['work_id'],r['media'])).fetchone()
        assert prior and prior[0] in [r['expected_status'],r['status']], 'Coverage changed since review; reconcile before writing'
        checked(c,r['work_id'],r['media'],r['status'],r['scope'],evs[r['source']],r['gap'])
    products={}
    for p in d.get('products',[]):
        wid=p['work_id'];pid=key('p',wid,p['media'],p['source_id']);products[p['key']]=pid
        row={k:v for k,v in p.items() if k not in ['key','work_id','source','parent_key']};row.update(id=pid,evidence_id=evs[p['source']])
        if p.get('parent_key'):row['parent_id']=products[p['parent_key']]
        upsert(c,'products',row);c.execute('INSERT OR IGNORE INTO product_works VALUES(?,?,?)',(pid,wid,evs[p['source']]))
    for e in d.get('events',[]):
        row={k:v for k,v in e.items() if k not in ['product','source']};row.update(id=key('event',d['batch'],e['product'],e['event_type'],e['event_time']),product_id=products[e['product']],evidence_id=evs[e['source']]);upsert(c,'events',row)
    return {'batch':d['batch'],'reviewed_works':len(seen),'products':len(products),'events':len(d.get('events',[])),'qualifications':len(d.get('qualifications',[]))}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');a=p.parse_args();d=json.loads((ROOT/a.manifest).read_text(encoding='utf-8'));c=connect();r=ingest(c,d);c.commit();c.close();export();print(json.dumps(r,ensure_ascii=False))
