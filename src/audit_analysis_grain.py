"""Inspect analysis limits at work, project, version, event and observation grain."""
from research import *

def audit():
    c=connect();queries={
      'works_by_inclusion':"select inclusion_status,count(*) records from works group by inclusion_status",
      'product_rows':"select media,confirmation,count(*) records,sum(parent_id is not null) child_versions,sum(markets is null) unknown_market from products group by media,confirmation",
      'events_by_year_type':"select substr(event_time,1,4) year,event_type,window_role,count(*) records from events group by year,event_type,window_role",
      'observations_by_time_type':"select temporal_type,min(observed_at) first_observation,max(observed_at) last_observation,count(*) records,sum(value is null) missing_value from observations group by temporal_type",
      'repeated_source_ids':"select platform,source_id,count(*) records from works group by platform,source_id having count(*)>1",
      'same_author_same_title':"select platform,title,author,count(*) records from works group by platform,title,author having count(*)>1",
      'missing_inclusion_evidence':"select id from works where inclusion_status='已确认' and (identity_evidence is null or category_mapped!='纯爱')",
      'post_cutoff_observations':"select id,observed_at from observations where substr(observed_at,1,10)>'2026-11-10'",
      'work_media_grain_duplicates':"select work_id,media,count(*) records from coverage where task_type='work_media' group by work_id,media having count(*)>1"
    }
    result={'at':now(),'cutoff':'2026-11-10','intended_use':'描述已核开发路径及证据缺口；不是行业开发率或采购排序','global_denominator':None,'queries':queries,'results':{k:[dict(r) for r in c.execute(q)] for k,q in queries.items()}}
    products={r['id']:dict(r) for r in c.execute('select * from products')}
    def root(pid):
        seen=set()
        while products[pid]['parent_id']:
            assert pid not in seen,'Product parent cycle';seen.add(pid);pid=products[pid]['parent_id'];assert pid in products,'Orphan parent'
        return pid
    roots={root(pid) for pid in products};result['grain']={'product_records':len(products),'root_projects_including_pending':len(roots),'child_records':sum(bool(p['parent_id']) for p in products.values()),'warning':'根项目数量仍包含待核和窗口外记录，不能直接视为观察期内确认开发项目数'}
    series=[dict(r) for r in c.execute("select work_id,product_id,metric_standard,unit,comparison_version,count(distinct observed_at) timestamps from observations where value is not null group by work_id,product_id,metric_standard,unit,comparison_version")]
    result['history']={'series_with_multiple_timestamps':sum(r['timestamps']>1 for r in series),'change_calculations_performed':0,'rule':'多时间点仍须核对象/口径/精度及原始日期；本轮没有足够已核历史序列，不计算年度增量或增长率'}
    result['risks']=[{'severity':'High','issue':'全站去重总体与资格仍有缺口','impact':'不能计算全行业开发率或把候选年份结构推广到行业','remedy':'继续目录/历史发现及原发签约身份核验'},{'severity':'High','issue':'产品表混有项目、季/卷版本、待核和窗口外背景','impact':'原始行数不能作为独立新增开发数','remedy':'按父子关系和窗口归属分组，再引用实际事件'},{'severity':'High','issue':'多数产品发行市场未知，指标主要为单日累计展示','impact':'不能按制作方所在地推地区，也不能构造2024年以来销量趋势','remedy':'进入官方发行渠道与历史记录逐条补证'}]
    for key in ['repeated_source_ids','missing_inclusion_evidence','post_cutoff_observations','work_media_grain_duplicates']:assert not result['results'][key],key
    assert not c.execute('pragma foreign_key_check').fetchall();c.close()
    (ROOT/'receipts/analysis-grain-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'grain':result['grain'],'history':result['history'],'quality_record':'receipts/analysis-grain-audit.json'},ensure_ascii=False))

if __name__=='__main__':audit()
