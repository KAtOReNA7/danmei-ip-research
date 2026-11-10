from research import *
c=connect(); data=json.loads((ROOT/'data/cp_capture.json').read_text(encoding='utf-8'))
for pg in data['directory_pages']:
    eid=evidence(c,pg['url'],'长佩纯爱分类目录',pg,'长佩文学',method='browser-visible-DOM',accessed=pg['accessed_at'])
    before=c.execute('select count(*) from works').fetchone()[0]
    for pid,title,author,status,popularity in pg['rows']:
        wid=add_work(c,'长佩',pid,title,author,'纯爱（目录筛选）',status,f'https://www.gongzicp.com/novel-{pid}.html',eid)
    new=c.execute('select count(*) from works').fetchone()[0]-before
    upsert(c,'coverage',dict(id=key('dir',pg['url']),task_type='directory',partition=pg['filter'].split(';页')[0],query_scope=pg['filter'],cursor=pg['url'].split('page=')[-1],status='已采集',discovered=len(pg['rows']),new_unique=new,first_id=pg['rows'][0][0],last_id=pg['rows'][-1][0],gap='无可见总数；原发/作品签约待核；综合排序非稳定排序',evidence_id=eid,last_run=pg['accessed_at']))
for w in data['samples']:
    url=f"https://www.gongzicp.com/novel-{w['id']}.html"
    eid=evidence(c,url,w['title']+'_'+w['author']+'著_长佩文学网',w,'长佩文学',method='browser-visible-DOM',accessed=w['accessed_at'])
    wid=add_work(c,'长佩',w['id'],w['title'],w['author'],w['category'],w['status'],url,eid)
    c.execute('update works set sample=1,stratum=?,signing_raw=?,signing_evidence=? where id=?',(w['stratum'],w['signing_raw'],eid,wid))
    for label,raw in w['metrics'].items():
        val=float(raw.replace(',','').replace('万',''))*(10000 if '万' in raw else 1) if raw else None
        upsert(c,'observations',dict(id=key('obs',wid,label,eid),work_id=wid,metric_raw=label,metric_standard='长佩'+label,raw_value=raw,value=val,unit='平台原单位',temporal_type='当前显示值_累计属性待核',observed_at=w['accessed_at'],precision='rounded_display' if raw and '万' in raw else ('displayed_integer' if raw else 'missing'),missing_reason=None if raw else '页面未显示；不填零',comparison_version='gongzicp:'+label+':v1',evidence_id=eid))
    checked(c,wid,'电子书','发现待核','长佩作品页：元数据及在线阅读入口；未打开章节正文',eid,'原发/签约细项及收费方式待证；免费或付费不可由阅读入口断言')
    upsert(c,'products',dict(id=key('p','长佩电子连载',w['id']),title=w['title']+'（长佩电子连载）',media='电子书',language='简体中文',platform='长佩',source_id=w['id'],source_url=url,pay_model=None,status='当前可见',confirmation='发现待核',evidence_id=eid))
    c.execute('INSERT OR IGNORE INTO product_works VALUES(?,?,?)',(key('p','长佩电子连载',w['id']),wid,eid))
c.commit();c.close()
