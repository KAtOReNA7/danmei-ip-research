"""Export every saved disclosure's remaining work without treating rows as deals."""
from collections import Counter
from research import *

WINDOW_ROLES={'窗口内签约日期','窗口内签约月份','窗口内签约年份'}


def build():
    c=connect()
    rows=[dict(r) for r in c.execute('select rr.*,w.title,w.author,w.platform,w.source_id,w.inclusion_status from rights_records rr join works w on w.id=rr.work_id order by w.platform,w.title,rr.media,rr.id')]
    c.close();counts=Counter()
    for r in rows:
        if r['inclusion_status']=='排除':partition='已排除作品范围'
        elif r['window_role'] in WINDOW_ROLES:
            partition='窗口内资格确认_交易细项待补' if r['inclusion_status']=='已确认' else '窗口内发生期明确_资格待核'
        elif r['window_role'] in {'签约时间待核','跨截止日待核'}:partition='发生期或截止边界待核'
        else:partition='窗口外背景'
        r['followup_partition']=partition
        r['missing_fields']='|'.join(k for k in ['licensee','grantor','language','market_raw','deal_id','amount'] if r.get(k) in (None,''))
        r['missing_fields_limit']='缺金额可如实披露，不表示必须取得私密合同才能结束单项；字段缺失不填零，主体署名不能自动推完整法律链。'
        r['research_state']='已排除保留证据' if partition=='已排除作品范围' else '背景保留，非窗口成交' if partition=='窗口外背景' else '部分完成，参见逐行缺口'
        counts[partition]+=1
    out=ROOT/'exports/rights-followups.csv'
    if rows:
        with out.open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    summary={'at':now(),'cutoff':'2026-11-10','disclosure_rows':len(rows),'partition_counts':dict(counts),
        'distinct_work_ids':len({r['work_id'] for r in rows}),'independent_contracts':None,
        'global_denominator':None,'global_complete':False,
        'limits':'覆盖的是已保存来源披露，不是全部原著/合同；30条优先队列仅首次追证，不能替代剩余来源或全量目录。',
        'rows_csv':'exports/rights-followups.csv'}
    (ROOT/'data/rights-followup-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 剩余商业调查台账','',f"保存：{summary['at']}；窗口2024-01-01至2026-11-10。",'',
        '每行是来源披露，可能重复同一合同；不是交易笔数。字段空白不填零。','','|分区|已保存来源行|','|---|---:|']
    lines += [f'|{name}|{n}|' for name,n in counts.items()]
    lines += ['',summary['limits'],'','优先补2024/2025实际签约发生期与窗口内待核作品资格；随后按来源与媒介追主体、范围、追加/续约及对应执行。未公开费用保留缺口，不为每条索取私密合同或反复审核。',
        '', 'CSV逐行保留作品ID、签约原文、时间精度、资格、来源、缺失字段与原始缺口，可继续固定批次；作品数和来源行数不可当全站分母。','']
    (ROOT/'exports/rights-followup-summary.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':build()
