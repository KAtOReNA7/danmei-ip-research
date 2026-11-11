"""Import rendered official rights disclosures, keeping classification unknown."""
from research import *
from rights_rules import rights_media,sale_window

def ingest(c,d,batch='cp-rights001'):
    result={'rows':0,'new_works':0,'identity_differences':[]}
    sections=[('改编',p['page'],p['rows']) for p in d['adaptation_pages']]+[('海外改编',1,d['overseas_rows'])]
    for section,page,rows in sections:
        cid=key('dir',batch,section,page)
        if c.execute('select 1 from coverage where id=?',(cid,)).fetchone():continue
        body={'batch':batch,'section':section,'page':page,'rows':rows,'displayed_pages':d['adaptation_displayed_pages'] if section=='改编' else None,'scope':d['scope'],'category':'清单未显示，逐作待核','timing':'未显示；不继承、不按排序/采集或上线推断'}
        eid=evidence(c,d['url'],'长佩版权信息：'+section+'第'+str(page)+'页',body,'长佩文学',method=d['method'],accessed=d['captured_at'])
        added=0
        for r in rows:
            old=c.execute("select * from works where platform='长佩' and source_id=?",(r['source_id'],)).fetchone()
            if old:
                wid=old['id']
                if old['title']!=r['title'] or old['author']!=r['author']:result['identity_differences'].append({'id':wid,'existing':[old['title'],old['author']],'gallery':[r['title'],r['author']]})
            else:
                wid=add_work(c,'长佩',r['source_id'],r['title'],r['author'],None,None,r['url'],eid,basis='官方版权清单作品ID及作者；平台题材、原发关系及作品级平台签约另核，不从衍生权利披露或作者名推纯爱/纳入资格')
                added+=1;result['new_works']+=1
            media=rights_media(r['rights_type']);assert media
            timing=sale_window(None)
            gap='官方版权信息清单签约类型披露；签约时间、受让方、合同身份与费用未显示。作品类别/原发或平台作品签约未补齐者仅候选；不计窗口内已售确认，不把多行当多笔合同；不推上线。'
            if section=='海外改编':gap+=' 只知海外，具体市场、语言、区域范围仍未知，不猜泰国或英语。'
            upsert(c,'rights_records',dict(id=key('rights',batch,section,page,r['ordinal']),work_id=wid,rights_type_raw=r['rights_type'],media=media,market_raw='海外（未细分）' if section=='海外改编' else None,language=None,grantor=None,licensee=None,agent=None,contract_time_raw=None,contract_start=None,contract_end=None,time_precision=timing['precision'],announcement_time=None,window_role=timing['window_role'],sale_status='官方版权清单签约类型披露；非合同原件',deal_id=None,amount=None,currency=None,source_url=d['url'],source_locator=f"{section}选中页{page}，本页第{r['ordinal']}行；作品ID{r['source_id']}",evidence_id=eid,gap=gap))
            prior=c.execute('select status from coverage where work_id=? and media=?',(wid,media)).fetchone()[0]
            scope=f"长佩官方版权信息{section}第{page}页，作品ID{r['source_id']}，签约类型{r['rights_type']}"
            if prior in ('未调查','已调查未发现'):checked(c,wid,media,'发现待核',scope,eid,gap)
            else:upsert(c,'check_history',dict(id=key('check',wid,media,scope,eid),work_id=wid,media=media,status=prior,query_scope=scope,evidence_id=eid,checked_at=d['captured_at'],gap='新增签约披露，不覆盖既有更强状态；'+gap))
            result['rows']+=1
        upsert(c,'coverage',dict(id=cid,task_type='directory',partition='cp-rights-'+section,query_scope='内置浏览器版权信息；改编/海外改编标签，按正常下一页逐页读取，不复制登录凭据',cursor=f'{section}第{page}页',status='已采集',displayed_total='改编显示41页；海外当前14行未见分页。非全站分母或独立合同总数',discovered=len(rows),new_unique=added,first_id=rows[0]['source_id'],last_id=rows[-1]['source_id'],evidence_id=eid,gap='改编仅第1—10页；剩余11—41页未采。日期、题材资格及同合同关系待核；出版及影视推荐未混入',last_run=d['captured_at']))
        upsert(c,'source_matrix',dict(id=key('source','cp-official-rights-gallery'),media='多媒介权利售出/授权签约',source_name='长佩官方版权信息改编/海外改编',url=d['url'],events_available='签约类型披露；不含签约日期、官宣日或上线日',current_values='不采实时指标，公开DOM必要元数据',historical_values='按页可续查，但日期未显示，历史年度归属未知',access_condition='读取器仅页脚，内置浏览器无登录渲染可读；普通分页，无绕过',test_result='可行：改编41页已采10页200行；海外14行已读，非历史穷尽',evidence_id=eid,next_action='从第11页续采；逐作核平台类别和资格，补官方授权/受让方公告的签约发生时间；出版格式单独核实'))
    return result

if __name__=='__main__':
    d=json.loads((ROOT/'data/cp-rights001-capture.json').read_text(encoding='utf-8'));c=connect();r=ingest(c,d);c.commit();c.close();export();print(json.dumps(r,ensure_ascii=False))
