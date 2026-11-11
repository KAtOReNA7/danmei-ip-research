"""Recompute sale-disclosure units, eligibility and timing without counting deals."""
from research import *
from ingest_cp_rights import gallery_coverage

def main():
    c=connect()
    roles=[dict(r) for r in c.execute('select window_role,count(*) source_rows,count(distinct work_id) works from rights_records group by window_role')]
    groups=[dict(r) for r in c.execute("select contract_time_raw,media,count(*) source_rows,count(distinct work_id) works from rights_records where window_role in ('窗口内签约月份','窗口内签约年份') group by contract_time_raw,media")]
    source_scope=[dict(r) for r in c.execute("select w.platform,coalesce(w.category_mapped,case when w.category_raw like '言情%' or w.category_raw like '百合%' then '非纯爱类别' else '题材待核' end) category_scope,count(*) source_rows,count(distinct rr.work_id) works from rights_records rr join works w on w.id=rr.work_id group by w.platform,coalesce(w.category_mapped,case when w.category_raw like '言情%' or w.category_raw like '百合%' then '非纯爱类别' else '题材待核' end)")]
    qualified=[dict(r) for r in c.execute("select rr.window_role,count(*) source_rows,count(distinct rr.work_id) works from rights_records rr join works w on w.id=rr.work_id where w.inclusion_status='已确认' group by rr.window_role")]
    cp=gallery_coverage(c)
    cp_missing=sorted(set(range(1,42))-set(cp['改编']['pages']))
    cp_scope=f"长佩改编显示41页，已采{len(cp['改编']['pages'])}页{cp['改编']['source_rows']}行；海外当前已采{cp['海外改编']['source_rows']}行；未采改编页码{cp_missing}。这是当前分区快照，不证明全历史或全站覆盖。"
    result={'at':now(),'priority':'窗口内已售出/已授权签约，非上线统计','cutoff':'2026-11-10','global_denominator':None,'rights_source_rows':c.execute('select count(*) from rights_records').fetchone()[0],'works':c.execute('select count(distinct work_id) from rights_records').fetchone()[0],'window_roles':roles,'qualified_works_subset':qualified,'month_media':groups,'independent_deals':None,'deal_gap':'同合同/追加/续约关系不明，清单多行不计多笔合同','fees':None,'fee_gap':'无可核授权金额；非0','signed_without_launch_kept':True,'launch_dates_used_as_sale_dates':False,'source_scope':source_scope,'cp_gallery_coverage':cp,'scope':'晋江成功签约及长佩版权信息已采分页的当前快照；长佩题材未核者单列，非两站全历史总体'}
    (ROOT/'receipts/rights-sales-analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 权利售出与授权签约阶段报告','',f'截止日北京时间2026-11-10；生成时间{result["at"]}。V1.1主线为窗口内卖出的权利，上线和表现为执行背景。调查仍部分完成。','',f'本阶段已保存权利披露{result["rights_source_rows"]}行，涉及{result["works"]}条平台作品记录；跨站原著未去重完，清单行不当独立合同，不代表全站总体。', '\n按来源平台及题材证据分层：', json.dumps(source_scope,ensure_ascii=False), '\n晋江清单10页原始4658行，其中纯爱1497行；'+cp_scope+'长佩清单不显示题材与日期；非纯爱类别单列排除，题材或资格未核者不能混入确认纯爱或窗口内新售。','','|签约时间归属|披露行数|涉及作品ID数|','|---|---:|---:|']
    lines += [f'|{r["window_role"]}|{r["source_rows"]}|{r["works"]}|' for r in roles]
    lines += ['','同一作品可跨上述类别，作品数不能跨行相加。日期空白不继承相邻行；2026-11不整月计入截止日前。排序、采集日期和上线日期均未用于补造签约日期。','','|签约时间原文|媒介|披露行数|涉及作品ID数|','|---|---|---:|---:|']
    lines += [f'|{r["contract_time_raw"]}|{r["media"] or "未映射原文另存"}|{r["source_rows"]}|{r["works"]}|' for r in groups]
    lines += ['','上表为有窗口内年月证据的来源披露范围；平台题材与作品原发或作品级平台签约资格尚未全部复核，不能直接称为全部符合条件的窗口内成交汇总。资格确认子集如下：',json.dumps(qualified,ensure_ascii=False),'','同一作品同媒介可有不同交易、续约或追加；受让方、代理方、费用、语言和年限缺失，独立交易数与金额均留空。括号中的地域按原文保存，未从公司所在地或地区反推语言。音乐、综艺原文保留，未强行塞入9媒介。','','没有把该清单转为已经上线产品；已签约未上线保留。已有产品、事件和观测作为执行背景，不能证明2024年以来新售，也不反推授权费或当前可售权利。','','主要缺口：签约时间缺失的数量见上表；历史目录完整性未知；月精度横跨截止日；清单重复披露及同合同关系；新增候选资格；长佩成功签约披露与其他年份历史；官方公告/受让方交叉证据。','','来源：[晋江官方成功签约清单](https://www.jjwxc.net/videoIntroduction.php)、[长佩官方版权信息](https://www.gongzicp.com/home/indexCopyright/search)。每条私有导出rights_records含具体分页、页内编号、真实作品ID与证据键；保存每批原始必要元数据与分区游标，支持重算。']
    cases=ROOT/'data/rights-report-cases.json'
    if cases.exists():
        lines += ['']+json.loads(cases.read_text(encoding='utf-8'))
    (ROOT/'exports/rights-sales-report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');c.close();print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
