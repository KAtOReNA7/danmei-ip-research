"""Write an evidence-bounded progress brief from the saved batch snapshot.

No network, new audit, backup, or inferred whole-platform completion rate.
"""
from research import ROOT
import json


def write_brief(progress):
    p=progress
    analysis_path=ROOT/'receipts/rights-sales-analysis.json'
    rights=json.loads(analysis_path.read_text(encoding='utf-8')) if analysis_path.exists() else {}
    validation_path=ROOT/p['cloud_validation'] if p.get('cloud_validation') else None
    validation=json.loads(validation_path.read_text(encoding='utf-8')) if validation_path and validation_path.exists() else {}
    scope_path=validation_path.parent/'scope.json' if validation_path else None
    scope=json.loads(scope_path.read_text(encoding='utf-8')) if scope_path and scope_path.exists() else {}
    linked_tables={'覆盖与缺口','产品与版本','事件时间线','指标观测','授权签约'}
    verified=bool(validation) and set(validation)==set(scope.get('completed_tables',[])) and all(
        row.get('all_fields_match') and row.get('all_pages_read') and not row.get('remaining_create')
        and (name not in linked_tables or row.get('links_verified'))
        for name,row in validation.items())
    summary={
        'at':p['at'],'batch':p['batch'],'cutoff':p['cutoff'],
        'candidate_source_records':p['candidate_source_records'],
        'global_denominator':None,'remaining_total_research':None,'whole_platform_completion_percent':None,
        'qualified':p['qualified_source_records'],
        'eligibility_pending':p['work_eligibility_pending'],
        'excluded':p['excluded_source_records'],
        'with_any_media_check':p['touched_records'],'no_media_checks_yet':p['no_checks_yet'],
        'with_non_ebook_check':p['non_ebook_initial_search_records'],
        'without_non_ebook_check':p['candidate_source_records']-p['non_ebook_initial_search_records'],
        'counts':p['counts'],
        'rights_time_roles':rights.get('window_roles',[]),
        'qualified_rights_time_roles':rights.get('qualified_works_subset',[]),
        'qualified_window_combined':rights.get('qualified_window_combined'),
        'annual_saved_disclosures':rights.get('annual_saved_disclosures',[]),
        'annual_coverage_limit':rights.get('annual_coverage_limit'),
        'independent_contracts':None,
        'cloud':{'receipt':p.get('cloud_validation'),'changed_tables_readback_passed':verified,
                 'tables':list(validation),'global_readback_performed':scope.get('global_readback_performed',False)},
        'remaining_scope':[
            '两站全量目录与历史年份边界仍未证；新发现作品会增加分母',
            '待核作品资格、原发、别名、重发与跨站身份；同名不自动合并',
            '已初查仍需媒介官方深查、未上线已授权、下架及其他语种',
            '实际签署区间、权利范围、地域/语言、主体及续约追加/同合同关系',
            '口径可比的历史表现与分母、行业分析、飞书展示和最终交付',
        ],
        'limits':'初查/有核查不等于逐作完成；完全未查不是全部剩余；权利披露行、产品行和独立合同数不同；缺失不填零。',
    }
    rows=[('至少一项媒介核查',p['touched_records'],f"{p['no_checks_yet']} 条完全未查"),
          ('至少一次非电子书媒介核查／初查',p['non_ebook_initial_search_records'],f"{summary['without_non_ebook_check']} 条尚无此类核查"),
          ('作品资格',f"{p['qualified_source_records']} 条已确认、{p['excluded_source_records']} 条排除",f"{p['work_eligibility_pending']} 条待核")]
    lines=['# 研究进度摘要','',f"保存：{p['at']}；批次：{p['batch']}；截止日：{p['cutoff']}。",'',
           f"当前分母为 {p['candidate_source_records']} 条已发现的平台候选记录，跨站身份未核完，不称去重原著总体。两站全量边界未知，不报总体完成百分比。",'',
           '| 项目 | 已完成 | 尚待处理 |','|---|---:|---|']
    lines += [f'| {label} | {done} | {remaining} |' for label,done,remaining in rows]
    c=p['counts']
    combined=summary['qualified_window_combined']
    if combined:
        lines += ['',f"主线：资格已确认且售出发生期完整落入窗口的合并范围为 {combined['source_rows']} 条来源披露、{combined['works']} 条去重作品ID。已跨日／月／年精度去重；不是独立交易数。"]
    if summary['annual_saved_disclosures']:
        lines += ['','年份缺口（当前已保存来源，不是年度市场规模）：']
        lines += [f"- {r['year']}：{r['source_rows']} 条发生期明确来源，其中 {r['qualified_source_rows']} 条作品资格已确认。" for r in summary['annual_saved_disclosures']]
        lines += [summary['annual_coverage_limit']]
    lines += ['',f"权利披露 {c['rights_records']} 条，产品／版本 {c['products']} 条，事件 {c['events']} 条，证据 {c['evidence']} 条。独立合同数未知。",'',
              '资格已确认子集中，签约发生期的分布：','']
    lines += [f"- {r['window_role']}：{r['source_rows']} 条披露、{r['works']} 条作品记录。" for r in summary['qualified_rights_time_roles']]
    lines += ['',summary['limits'],'','剩余工作：','']+[f'- {s}' for s in summary['remaining_scope']]
    cloud_label='变更表完整分页回读通过' if verified else '本批回读尚未确认'
    lines += ['',f"飞书：{cloud_label}；本批回读 {len(validation)} 张表。未变更表沿用既有回读，不称全库重审。",'',
              '开发批次本地保存数据、证据、缺口和下一步；未重复备份上传下载，不代表新增数据已跨设备备份。','']
    (ROOT/'data/progress-brief.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'exports/progress-brief.md').write_text('\n'.join(lines),encoding='utf-8')
    return summary


if __name__=='__main__':
    p=json.loads((ROOT/'data/progress.json').read_text(encoding='utf-8'))
    print(json.dumps(write_brief(p),ensure_ascii=False))
