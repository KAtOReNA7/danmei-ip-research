"""Import reviewed signing-source evidence without inventing contract identities.

Input contains necessary metadata only. Day precision requires an explicit
signing event, never an announcement or a programme release date.
"""
from research import *
from rights_rules import sale_window,completed_signing_period


def ingest(document):
    c=connect(); report={'batch':document['batch'],'evidence':0,'rights_rows':0,'products':0,'events':0,'reviewed_works':0}
    for item in document['items']:
        w=c.execute('select * from works where id=?',(item['work_id'],)).fetchone()
        assert w and (w['title'],w['author'])==(item['title'],item['author'])
        eid=item.get('evidence_id')
        if eid:
            saved=c.execute('select * from evidence where id=?',(eid,)).fetchone()
            assert saved and saved['url']==item['url']
            assert json.loads((ROOT/saved['file_path']).read_text(encoding='utf-8'))['necessary_metadata']==item['facts']
        else:
            eid=evidence(c,item['url'],item['source_title'],item['facts'],item['source_owner'],
                         status=item['source_status'],method=item.get('method','公开网页直接核验必要元数据；无音频、正文或实时指标'),
                         published=item.get('published_at'),accessed=document['reviewed_at'])
        report['evidence']+=1; gap=item['gap']
        if item.get('signing_day'):
            assert item['facts']['explicit_signing_event'] is True
            timing=sale_window(item['signing_day'])
            rid=key('rights','signing-event',w['id'],item['url'],item['signing_day'],item['rights_type_raw'])
            report['rights_rows']+=int(not c.execute('select 1 from rights_records where id=?',(rid,)).fetchone())
            upsert(c,'rights_records',dict(id=rid,work_id=w['id'],rights_type_raw=item['rights_type_raw'],media=item['media'],
                market_raw=item.get('market_raw'),contract_time_raw=item['signing_day'],contract_start=timing['start'],
                contract_end=timing['end'],time_precision=timing['precision']+'；公开现场签约日，法律生效日未核',
                announcement_time=item.get('published_at'),window_role=timing['window_role'],
                sale_status='官方报道明确现场签约；非合同原件',source_url=item['url'],
                source_locator=item['source_locator'],evidence_id=eid,gap=gap))
            pid=key('p','public-signing-project',w['id'],item['rights_type_raw'],item.get('market_raw'))
            report['products']+=int(not c.execute('select 1 from products where id=?',(pid,)).fetchone())
            upsert(c,'products',dict(id=pid,title=item['project_title'],media=item['media'],markets=item.get('market_raw'),
                source_url=item['url'],status='官方已签约；执行状态未核',confirmation='公开现场签约直接证据',evidence_id=eid))
            c.execute('insert into product_works(product_id,work_id,evidence_id) values(?,?,?) on conflict(product_id,work_id) do update set evidence_id=excluded.evidence_id',(pid,w['id'],eid))
            eventid=key('event','signing-event',rid)
            report['events']+=int(not c.execute('select 1 from events where id=?',(eventid,)).fetchone())
            upsert(c,'events',dict(id=eventid,work_id=w['id'],product_id=pid,event_type='公开现场签约',
                event_time=timing['start'],time_end=timing['end'],time_precision='日；活动签约日，非合同法律生效日',
                description=item['event_description'],window_role=timing['window_role'],confirmation='官方明确披露',evidence_id=eid))
        elif item.get('completed_signing_period'):
            assert item['facts'].get('explicit_completed_signing') is True
            period=item['completed_signing_period']
            timing=(completed_signing_period(period,item['announcement_day'],explicit_completed=True)
                    if item.get('announcement_day') else sale_window(period))
            assert timing['start'], 'Contradictory or missing actual signing period'
            rid=key('rights','completed-period',w['id'],item['url'],period,item['rights_type_raw'])
            report['rights_rows']+=int(not c.execute('select 1 from rights_records where id=?',(rid,)).fetchone())
            upsert(c,'rights_records',dict(id=rid,work_id=w['id'],rights_type_raw=item['rights_type_raw'],media=item['media'],
                contract_time_raw=period,contract_start=timing['start'],contract_end=timing['end'],time_precision=timing['precision']+item.get('time_precision_note',''),
                announcement_time=item.get('announcement_day'),window_role=timing['window_role'],sale_status='第一方明确已签约/已获授权及发生期；非合同原件',
                source_url=item['url'],source_locator=item['source_locator'],evidence_id=eid,gap=gap))
        elif item.get('rights_type_raw'):
            assert item['facts'].get('explicit_rights_scope_update') is True
            rid=key('rights','scope-update',w['id'],item['url'],item['rights_type_raw'])
            report['rights_rows']+=int(not c.execute('select 1 from rights_records where id=?',(rid,)).fetchone())
            upsert(c,'rights_records',dict(id=rid,work_id=w['id'],rights_type_raw=item['rights_type_raw'],media=item['media'],
                market_raw=item.get('market_raw'),language=item.get('language'),
                time_precision='未知；当前授权范围更新未标发生日期或截止前状态',window_role='签约时间待核',
                sale_status='合作方明确授权范围更新；签署期及合同角色未核',
                source_url=item['url'],source_locator=item['source_locator'],evidence_id=eid,gap=gap))
        for original_id in item.get('related_source_rows',[]):
            prior=c.execute('select * from rights_records where id=?',(original_id,)).fetchone()
            assert prior and prior['work_id']==w['id']
            note=' 深查关联证据：'+eid+'；'+gap
            if note not in (prior['gap'] or ''):c.execute('update rights_records set gap=? where id=?',((prior['gap'] or '')+note,original_id))
        prior=c.execute("select * from coverage where id=?",(key('cov',w['id'],item['media']),)).fetchone()
        if prior and prior['status']=='已确认' and item['coverage_status']!='已确认':
            # A weaker new lead cannot replace the existing confirmation source.
            stamp=now();hid=key('check',w['id'],item['media'],item['query_scope'],eid)
            upsert(c,'check_history',dict(id=hid,work_id=w['id'],media=item['media'],status=item['coverage_status'],
                query_scope=item['query_scope'],evidence_id=eid,checked_at=stamp,gap=gap))
            note=' 补查待核证据：'+eid+'；'+gap
            saved_gap=prior['gap'] or ''
            c.execute('update coverage set gap=?,last_run=? where id=?',
                (saved_gap if note in saved_gap else saved_gap+note,stamp,prior['id']))
        else:
            checked(c,w['id'],item['media'],item['coverage_status'],item['query_scope'],eid,gap)
        report['reviewed_works']+=1
    c.commit();c.close()
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('reviewed');a=p.parse_args()
    d=json.loads((ROOT/a.reviewed).read_text(encoding='utf-8'))
    r=ingest(d)
    (ROOT/'receipts'/f'{d["batch"]}-ingest.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(r,ensure_ascii=False))
