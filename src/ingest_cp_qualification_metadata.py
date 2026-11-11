"""Review official detail metadata without importing metrics or inferring signing."""
from research import *


def ingest(c,d,batch):
    result={'checked':0,'pure':0,'excluded':0,'unavailable':0,'reused':0}
    for r in d['rows']:
        sid=r['expected_id'];cid=key('qual',batch,sid)
        if c.execute('select 1 from coverage where id=?',(cid,)).fetchone():
            result['reused']+=1;continue
        w=c.execute("select * from works where platform='长佩' and source_id=?",(sid,)).fetchone()
        assert w and r['url']==w['source_url'],sid
        gap='仅核身份及平台分类；不采实时指标，原发／作品级平台签约和衍生签约日期仍需独立证据。'
        if r.get('result'):
            assert r['result']=='作品不存在！'
            result['unavailable']+=1;status='访问受阻'
            gap='官方详情返回作品不存在；保留版权清单候选及历史签约线索，不导入空标题、零值和尚未签约占位。'
            c.execute('update works set inclusion_basis=? where id=?',((w['inclusion_basis'] or '')+'；'+gap,w['id']))
        else:
            assert r['source_id']=='CP'+sid and r['title']==w['title']
            author,meta=r['status_metadata'].split(' 著',1)
            assert author==w['author'] and all(a['author']==author for a in r['author_links'])
            match=re.fullmatch(r'(纯爱|言情|百合)([^·]+)·(完结|连载)',meta)
            assert match,meta
            category=match[1]+match[2];pure=match[1]=='纯爱'
            assert not w['category_raw'] or w['category_raw']==category,'Category conflict requires review'
            assert pure or w['inclusion_status']!='已确认','Confirmed eligibility conflict'
            result['pure' if pure else 'excluded']+=1;status='已核验'
            gap=gap if pure else '官方分类为'+category+'，不纳入纯爱统计；原始清单记录保留，不改判题材。'
        eid=evidence(c,r['url'],'长佩作品资格元数据：'+w['title'],r,'长佩文学',method=d['method'],accessed=r['captured_at'])
        if not r.get('result'):
            basis=w['inclusion_basis'] if pure and w['inclusion_status']=='已确认' else gap
            inclusion=w['inclusion_status'] if pure else '排除'
            c.execute('update works set category_raw=?,category_mapped=?,serial_status=?,identity_evidence=?,inclusion_status=?,inclusion_basis=?,last_seen=? where id=?',(category,'纯爱' if pure else None,match[3],eid,inclusion,basis,r['captured_at'],w['id']))
            if not pure:upsert(c,'exclusions',dict(id=key('exclude','cp-category',sid),source_url=r['url'],title=w['title'],reason=gap,evidence_id=eid))
        upsert(c,'coverage',dict(id=cid,task_type='qualification',work_id=w['id'],partition='cp-work-qualification',query_scope='官方作品详情必要身份及题材；非媒介售出核验',cursor=sid,status=status,discovered=1,new_unique=0,first_id=sid,last_id=sid,evidence_id=eid,gap=gap,last_run=r['captured_at']))
        result['checked']+=1
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--capture',required=True);p.add_argument('--batch',required=True);a=p.parse_args()
    d=json.loads((ROOT/a.capture).read_text(encoding='utf-8'));c=connect();r=ingest(c,d,a.batch);c.commit();c.close();export();print(json.dumps(r,ensure_ascii=False))
