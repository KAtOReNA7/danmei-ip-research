"""Recompute sale-disclosure units, eligibility and timing without counting deals."""
from research import *

def main():
    c=connect()
    roles=[dict(r) for r in c.execute('select window_role,count(*) source_rows,count(distinct work_id) works from rights_records group by window_role')]
    groups=[dict(r) for r in c.execute("select contract_time_raw,media,count(*) source_rows,count(distinct work_id) works from rights_records where window_role='窗口内签约月份' group by contract_time_raw,media")]
    qualified=[dict(r) for r in c.execute("select rr.window_role,count(*) source_rows,count(distinct rr.work_id) works from rights_records rr join works w on w.id=rr.work_id where w.inclusion_status='已确认' group by rr.window_role")]
    result={'at':now(),'priority':'窗口内已售出/已授权签约，非上线统计','cutoff':'2026-11-10','global_denominator':None,'rights_source_rows':c.execute('select count(*) from rights_records').fetchone()[0],'works':c.execute('select count(distinct work_id) from rights_records').fetchone()[0],'window_roles':roles,'qualified_works_subset':qualified,'month_media':groups,'independent_deals':None,'deal_gap':'同合同/追加/续约关系不明，清单多行不计多笔合同','fees':None,'fee_gap':'无可核授权金额；非0','signed_without_launch_kept':True,'launch_dates_used_as_sale_dates':False,'scope':'本批晋江官方成功签约清单当前快照；非两站或全历史总体'}
    (ROOT/'receipts/rights-sales-analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 权利售出与授权签约阶段报告','',f'截止日北京时间2026-11-10；生成时间{result["at"]}。V1.1主线为窗口内卖出的权利，上线和表现为执行背景。调查仍部分完成。','',f'本批晋江官方成功签约清单10页，原披露4658行；平台纯爱分类{result["rights_source_rows"]}行，涉及{result["works"]}个官方作品ID。不是1497笔合同，也不是全站原著总体。','','|签约时间归属|披露行数|涉及作品ID数|','|---|---:|---:|']
    lines += [f'|{r["window_role"]}|{r["source_rows"]}|{r["works"]}|' for r in roles]
    lines += ['','同一作品可跨上述类别，作品数不能跨行相加。日期空白不继承相邻行；2026-11不整月计入截止日前。排序、采集日期和上线日期均未用于补造签约日期。','','|签约月份|媒介|披露行数|涉及作品ID数|','|---|---|---:|---:|']
    lines += [f'|{r["contract_time_raw"]}|{r["media"] or "未映射原文另存"}|{r["source_rows"]}|{r["works"]}|' for r in groups]
    lines += ['','上表为官方平台纯爱披露范围；作品原发或作品级平台签约资格尚未全部复核，不能直接称为全部符合条件的窗口内成交汇总。资格确认子集如下：',json.dumps(qualified,ensure_ascii=False),'','同一作品同媒介可有不同交易、续约或追加；受让方、代理方、费用、语言和年限缺失，独立交易数与金额均留空。括号中的地域按原文保存，未从公司所在地或地区反推语言。音乐、综艺原文保留，未强行塞入9媒介。','','没有把该清单转为已经上线产品；已签约未上线保留。已有产品、事件和观测作为执行背景，不能证明2024年以来新售，也不反推授权费或当前可售权利。','','主要缺口：1464行签约时间缺失；月精度横跨截止日；清单重复披露及同合同关系；新增候选资格；长佩成功签约披露与其他年份历史；官方公告/受让方交叉证据。','','来源：[晋江官方成功签约清单](https://www.jjwxc.net/videoIntroduction.php)。每条私有导出rights_records含具体分页、页内编号、真实作品ID与证据键；保存10页原始必要元数据，支持重算。']
    (ROOT/'exports/rights-sales-report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');c.close();print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
