"""Import reviewed official success listings without inventing deals or launches."""
from research import *
from rights_rules import sale_window,rights_media

def ingest(c,docs,batch):
    result={'source_rows':0,'pure_love_rows':0,'new_works':0,'identity_differences':[]}
    for d in docs:
        assert d['status']=='captured' and d['displayed_rows']==4658
        cid=key('dir',batch,d['page'])
        if c.execute('select 1 from coverage where id=?',(cid,)).fetchone():continue
        eid=evidence(c,d['url'],d['title'],d,'晋江文学城',method=d['scope'],accessed=d['captured_at'])
        added=0;pure=[]
        for r in d['rows']:
            result['source_rows']+=1
            if '纯爱' not in r['category']:continue
            pure.append(r);result['pure_love_rows']+=1
            old=c.execute("select * from works where platform='晋江' and source_id=?",(r['source_id'],)).fetchone()
            if old:
                wid=old['id']
                if old['title']!=r['title'] or old['author']!=r['author']:
                    result['identity_differences'].append({'id':wid,'existing':[old['title'],old['author']],'gallery':[r['title'],r['author']]})
            else:
                wid=add_work(c,'晋江',r['source_id'],r['title'],r['author'],r['category'],None,r['url'],eid,basis='官方成功签约清单的作品ID、作者及纯爱分类；原发关系与作品级平台签约另核，不以衍生授权替代纳入资格')
                added+=1;result['new_works']+=1
            timing=sale_window(r['contract_month_raw']);media=rights_media(r['rights_type'])
            market=re.search(r'[（(]([^()（）]+)[）)]',r['rights_type'])
            gap='清单证明官方披露成功签约；不证明上线、当前可售、独立合同数、费用、受让方或授权年限。空日期不继承相邻行；月跨截止日不纳入窗口内确认。作品资格单列。'
            if old and (old['title']!=r['title'] or old['author']!=r['author']):gap+=' 同官方ID展示名/作者存在差异，未改写原作品身份，详见原始行证据。'
            if not media:gap+=' 音乐/综艺等原文暂未映射9类媒介，保留权利记录，不强行归类。'
            upsert(c,'rights_records',dict(id=key('rights',batch,d['page'],r['ordinal']),work_id=wid,rights_type_raw=r['rights_type'],media=media,market_raw=market[1] if market else None,language=None,grantor=None,licensee=None,agent=None,contract_time_raw=r['contract_month_raw'] or None,contract_start=timing['start'],contract_end=timing['end'],time_precision=timing['precision'],announcement_time=None,window_role=timing['window_role'],sale_status='官方成功签约披露；非合同原件',deal_id=None,amount=None,currency=None,source_url=d['url'],source_locator=f"第{d['page']}页本页编号{r['ordinal']}；原作品ID{r['source_id']}",evidence_id=eid,gap=gap))
            if media:
                prior=c.execute('select status from coverage where work_id=? and media=?',(wid,media)).fetchone()[0]
                scope=f"晋江官方成功签约清单，作品ID{r['source_id']}，权利类型{r['rights_type']}；签约披露非上线证据"
                if prior in ('未调查','已调查未发现'):checked(c,wid,media,'发现待核',scope,eid,gap)
                else:
                    upsert(c,'check_history',dict(id=key('check',wid,media,scope,eid),work_id=wid,media=media,status=prior,query_scope=scope,evidence_id=eid,checked_at=d['captured_at'],gap='新增官方签约证据，既有更强或不同来源状态保持不变；'+gap))
        upsert(c,'coverage',dict(id=cid,task_type='directory',partition='jj-success-rights',query_scope='晋江影音推介成功签约，完整公开分页；筛平台纯爱；不含实体出版',cursor=f"第{d['page']}页；下一URL见证据",status='已采集',displayed_total='4658条/10页：权利披露行，非原著或合同总数',discovered=len(pure),new_unique=added,first_id=pure[0]['source_id'] if pure else None,last_id=pure[-1]['source_id'] if pure else None,evidence_id=eid,gap='多数记录签约日期空白；全站未售出、历史锁删迁移未覆盖；分页可能变动，不能据清单推行业比例',last_run=d['captured_at']))
        upsert(c,'source_matrix',dict(id=key('source','jj-success-rights'),media='多媒介权利售出/授权签约',source_name='晋江官方影音推介成功签约',url='https://www.jjwxc.net/videoIntroduction.php',events_available='官方成功签约披露，部分月精度；不是上线日期',current_values='不采实时热度；表中行数是披露范围',historical_values='多数签约月份缺失；不能从排序或上线反推',access_condition='公开HTTP，10页；沿实际下一页链接，有限传输/解析恢复，无认证绕过',test_result='可采；非完整历史交易台账，合同身份/范围和日期仍缺',evidence_id=eid,next_action='逐作追签约时间、受让方、地区语言、续约追加及同合同关系，先核官方披露，不以泛媒介初查完成售出调查'))
    return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--batch',default='jj-rights001');a=p.parse_args()
    docs=[json.loads((ROOT/f'data/{a.batch}-page{i:02}.json').read_text(encoding='utf-8')) for i in range(1,11)]
    assert sum(len(d['rows']) for d in docs)==4658
    c=connect();r=ingest(c,docs,a.batch);c.commit();c.close();export();print(json.dumps(r,ensure_ascii=False))
