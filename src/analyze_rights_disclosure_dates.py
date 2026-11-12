"""A disclosure-date appendix; the sale window remains the actual signing window."""
from research import *
from datetime import date
from collections import defaultdict,Counter


def build(silent=False):
    c=connect()
    rows=[dict(r) for r in c.execute('select rr.*,w.title,w.author,w.platform,w.inclusion_status,e.status evidence_status,e.method evidence_method from rights_records rr join works w on w.id=rr.work_id join evidence e on e.id=rr.evidence_id order by rr.id')]
    c.close();groups=defaultdict(list);partitions=Counter()
    for r in rows:
        raw=(r['announcement_time'] or '').strip()
        try:
            if not re.match(r'^\d{4}-\d{2}-\d{2}(?:$|[ T])',raw):raise ValueError
            day=date.fromisoformat(raw[:10])
        except ValueError:
            day=None
        partition='披露日未核' if day is None else '窗口前披露' if day<date(2024,1,1) else '截止后披露' if day>date(2026,11,10) else '窗口内披露'
        r['disclosure_date_partition']=partition
        r['disclosure_year']=str(day.year) if day else None
        r['disclosure_unit_limit']='公开披露日期分布，不是实际签约年份、首次公开日或独立合同数；原始签约发生期另列，不能相互回填。'
        partitions[partition]+=1
        if partition=='窗口内披露' and r['inclusion_status']!='排除':groups[(r['disclosure_year'],r['media'] or '原始范围待分类')].append(r)
    table=[]
    for (year,media),group in sorted(groups.items()):
        table.append({'disclosure_year':year,'media':media,'source_rows':len(group),'work_ids':len({r['work_id'] for r in group}),'source_urls':len({r['source_url'] for r in group}),'qualified_source_rows':sum(r['inclusion_status']=='已确认' for r in group),'actual_occurrence_unknown_rows':sum(r['window_role'] in ('签约时间待核','跨截止日待核') for r in group)})
    with (ROOT/'exports/rights-disclosure-dates.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=list(rows[0]) if rows else ['id','work_id','rights_type_raw','media','announcement_time','contract_time_raw','window_role','disclosure_date_partition','disclosure_year']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    summary={'at':now(),'cutoff':'2026-11-10','source_rows':len(rows),'date_partitions':dict(partitions),'table':table,'independent_contracts':None,'global_denominator':None,'scope':'只按已保存且明确的公告/公开披露日期形成附表；不是窗口内成交统计，不保证首次公开或全历史完整。实际签署发生期仍是主统计。'}
    (ROOT/'data/rights-disclosure-dates-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 权利公开披露日期附表','',f"生成：{summary['at']}；截止日2026-11-10。",'',summary['scope'],'','统计分母为当前已保存的权利披露行。下表只纳披露日完整落在窗口且作品未排除的记录；资格待核来源单独保留，不混称全部符合条件的市场交易。每行保留实际签署原文/区间、资格、证据层级与来源链接供复核。','',
           '|公开披露年份|媒介|来源行|作品ID|不同来源URL|其中资格确认行|其中实际发生期仍待核行|','|---|---|---:|---:|---:|---:|---:|']
    lines += [f"|{r['disclosure_year']}|{r['media']}|{r['source_rows']}|{r['work_ids']}|{r['source_urls']}|{r['qualified_source_rows']}|{r['actual_occurrence_unknown_rows']}|" for r in table]
    lines += ['', '日期分区（含保留的已排除来源）：'+json.dumps(dict(partitions),ensure_ascii=False)+'。', '',
              '一个公告可披露多部作品或多个媒介范围；同一合同也可能有多次公告。不同来源URL、披露行及作品数不能作为合同数，跨媒介/年份作品数不能直接相加。收录不代表证据层级全部相同，CSV保留逐行来源状态。', '',
              '取得授权的官方公告可确认授权事实；实际签署发生期缺失时仍留空。公告日期不填签约日期，上线、采集和作品创建日期也不填公告日期。截止后补披露的历史签约仍须按其实际发生期判断，不能用本附表排除该历史事实。', '',
              '当前来源和年份覆盖不完整，不按本表计算市场增长或年成交规模。主统计继续见rights-sales-report.md，本表仅帮助定位公开披露、主体/渠道与实际发生期缺口。','']
    (ROOT/'exports/rights-disclosure-dates.md').write_text('\n'.join(lines),encoding='utf-8')
    if not silent:print(json.dumps(summary,ensure_ascii=False))
    return summary


if __name__=='__main__':build()
