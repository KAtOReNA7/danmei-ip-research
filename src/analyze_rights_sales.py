"""Recompute sale-disclosure units, eligibility and timing without counting deals."""
from research import *
from ingest_cp_rights import gallery_coverage

def main():
    from analyze_rights_disclosure_dates import build as disclosure_dates
    appendix=disclosure_dates(silent=True)
    c=connect()
    roles=[dict(r) for r in c.execute('select window_role,count(*) source_rows,count(distinct work_id) works from rights_records group by window_role')]
    groups=[dict(r) for r in c.execute("select contract_time_raw,media,count(*) source_rows,count(distinct work_id) works from rights_records where window_role in ('窗口内签约月份','窗口内签约年份','窗口内签约日期') group by contract_time_raw,media")]
    source_scope=[dict(r) for r in c.execute("select w.platform,coalesce(w.category_mapped,case when w.category_raw like '言情%' or w.category_raw like '百合%' then '非纯爱类别' else '题材待核' end) category_scope,count(*) source_rows,count(distinct rr.work_id) works from rights_records rr join works w on w.id=rr.work_id group by w.platform,coalesce(w.category_mapped,case when w.category_raw like '言情%' or w.category_raw like '百合%' then '非纯爱类别' else '题材待核' end)")]
    qualified=[dict(r) for r in c.execute("select rr.window_role,count(*) source_rows,count(distinct rr.work_id) works from rights_records rr join works w on w.id=rr.work_id where w.inclusion_status='已确认' group by rr.window_role")]
    year_rows={r['year']:dict(r) for r in c.execute("select substr(rr.contract_start,1,4) year,count(*) source_rows,count(distinct rr.work_id) works,sum(case when w.inclusion_status='已确认' then 1 else 0 end) qualified_source_rows,count(distinct case when w.inclusion_status='已确认' then rr.work_id end) qualified_works from rights_records rr join works w on w.id=rr.work_id where rr.window_role in ('窗口内签约月份','窗口内签约年份','窗口内签约日期') group by substr(rr.contract_start,1,4)")}
    annual=[year_rows.get(str(year),dict(year=str(year),source_rows=0,works=0,qualified_source_rows=0,qualified_works=0)) for year in range(2024,2027)]
    confirmed_window=dict(c.execute("select count(*) source_rows,count(distinct rr.work_id) works from rights_records rr join works w on w.id=rr.work_id where w.inclusion_status='已确认' and rr.window_role in ('窗口内签约月份','窗口内签约年份','窗口内签约日期')").fetchone())
    cp=gallery_coverage(c)
    cp_missing=sorted(set(range(1,42))-set(cp['改编']['pages']))
    cp_scope=f"长佩改编显示41页，已采{len(cp['改编']['pages'])}页{cp['改编']['source_rows']}行；海外当前已采{cp['海外改编']['source_rows']}行；未采改编页码{cp_missing}。这是当前分区快照，不证明全历史或全站覆盖。"
    result={'at':now(),'priority':'窗口内已售出/已授权签约，非上线统计','cutoff':'2026-11-10','global_denominator':None,'rights_source_rows':c.execute('select count(*) from rights_records').fetchone()[0],'works':c.execute('select count(distinct work_id) from rights_records').fetchone()[0],'window_roles':roles,'qualified_works_subset':qualified,'qualified_window_combined':confirmed_window,'month_media':groups,'independent_deals':None,'deal_gap':'同合同/追加/续约关系不明，清单多行不计多笔合同','fees':None,'fee_gap':'无可核授权金额；非0','signed_without_launch_kept':True,'launch_dates_used_as_sale_dates':False,'source_scope':source_scope,'cp_gallery_coverage':cp,'scope':'晋江成功签约、长佩版权信息当前分页及已直接核的官方授权署名；候选锚点平台不等于授权来源或版本归属，非两站全历史总体'}
    result['annual_saved_disclosures']=annual
    result['annual_coverage_limit']='仅已保存且发生期明确的来源；0表示当前无可纳来源，不表示市场无授权。2026截至11月10日，不与完整年份直接比较增长。年份按原北京时间区间取值，不用UTC换日。'
    result['disclosure_date_appendix']={'report':'exports/rights-disclosure-dates.md','csv':'exports/rights-disclosure-dates.csv','scope':appendix['scope'],'date_partitions':appendix['date_partitions']}
    (ROOT/'receipts/rights-sales-analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 权利售出与授权签约阶段报告','',f'截止日北京时间2026-11-10；生成时间{result["at"]}。V1.2开发阶段沿用窗口内卖出的权利主线，上线和表现为执行背景。调查仍部分完成。','',f'本阶段已保存权利披露{result["rights_source_rows"]}行，涉及{result["works"]}条平台作品记录；跨站原著未去重完，清单行不当独立合同，不代表全站总体。', '\n按候选锚点平台及题材证据分层（不等于售出平台归属）：', json.dumps(source_scope,ensure_ascii=False), '\n晋江清单10页原始4658行，其中纯爱1497行；'+cp_scope+'长佩清单不显示题材与日期；非纯爱类别单列排除，题材或资格未核者不能混入确认纯爱或窗口内新售。','','|签约时间归属|披露行数|涉及作品ID数|','|---|---:|---:|']
    lines += [f'|{r["window_role"]}|{r["source_rows"]}|{r["works"]}|' for r in roles]
    lines += ['','按发生年份查看当前保存的窗口来源（含资格待核与确认分层，不是年度市场规模）：','','|年份|来源行数|涉及作品ID|资格确认来源行|资格确认作品ID|','|---|---:|---:|---:|---:|']
    lines += [f'|{r["year"]}|{r["source_rows"]}|{r["works"]}|{r["qualified_source_rows"]}|{r["qualified_works"]}|' for r in annual]
    lines += ['',result['annual_coverage_limit'],'当前可纳来源集中于2026年，2024—2025缺口必须继续补证，不据此宣称商业增长或市场规模变化。']
    lines += ['','同一作品可跨上述类别，作品数不能跨行相加。日期空白不继承相邻行；2026-11不整月计入截止日前。排序、采集日期和上线日期均未用于补造签约日期。','','|签约时间原文|媒介|披露行数|涉及作品ID数|','|---|---|---:|---:|']
    lines += [f'|{r["contract_time_raw"]}|{r["media"] or "未映射原文另存"}|{r["source_rows"]}|{r["works"]}|' for r in groups]
    lines += ['','上表为有窗口内发生期（日/月/年）证据的来源披露范围；平台题材与作品原发或作品级平台签约资格尚未全部复核，不能直接称为全部符合条件的窗口内成交汇总。资格确认子集如下：',json.dumps(qualified,ensure_ascii=False),'','资格已确认且发生期完整落入窗口的合并来源行与去重作品ID数：'+json.dumps(confirmed_window,ensure_ascii=False)+'。跨日期精度去重；不是独立合同数。','','同一作品同媒介可有不同交易、续约或追加；受让方、代理方、费用、语言和年限缺失，独立交易数与金额均留空。括号中的地域按原文保存，未从公司所在地或地区反推语言。音乐、综艺原文保留，未强行塞入9媒介。','','没有把该清单转为已经上线产品；已签约未上线保留。已有产品、事件和观测作为执行背景，不能证明2024年以来新售，也不反推授权费或当前可售权利。','','主要缺口：签约时间缺失的数量见上表；历史目录完整性未知；月精度横跨截止日；清单重复披露及同合同关系；新增候选资格；长佩成功签约披露与其他年份历史；官方公告/受让方交叉证据。','','来源：[晋江官方成功签约清单](https://www.jjwxc.net/videoIntroduction.php)、[长佩官方版权信息](https://www.gongzicp.com/home/indexCopyright/search)。每条私有导出rights_records含具体分页、页内编号、真实作品ID与证据键；保存每批原始必要元数据与分区游标，支持重算。']
    lines += ['','[权利公开披露日期附表](rights-disclosure-dates.md)单列公告日期及实际发生期缺口，不作为成交年份或市场增长统计；逐行CSV保留两套日期和证据层级。']
    cases=ROOT/'data/rights-report-cases.json'
    if cases.exists():
        lines += ['']+json.loads(cases.read_text(encoding='utf-8'))
    (ROOT/'exports/rights-sales-report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');c.close();print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
