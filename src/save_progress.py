"""Save truthful resumable progress, separating metadata checks from media searches."""
from research import *
def save(batch,cloud=None):
 c=connect();n=c.execute('select count(*) from works').fetchone()[0]
 counts={t:c.execute('select count(*) from '+t).fetchone()[0] for t in ['products','events','observations','evidence','check_history']}
 qualified=c.execute("select count(*) from works where inclusion_status='已确认'").fetchone()[0]
 touched=c.execute("select count(distinct work_id) from coverage where task_type='work_media' and status!='未调查'").fetchone()[0]
 cross=c.execute("select count(distinct work_id) from coverage where task_type='work_media' and media!='电子书' and status!='未调查'").fetchone()[0]
 pending=[dict(r) for r in c.execute("select id,source_id,title,author,platform from works where platform='晋江' and signing_evidence is null order by cast(source_id as integer)")]
 detail=c.execute('select count(*) from works where signing_evidence is not null').fetchone()[0]
 cp_detail=c.execute("select count(*) from works where platform='长佩' and signing_evidence is not null").fetchone()[0]
 blocked=c.execute("select count(*) from coverage where task_type='work_media' and media='电子书' and status='访问受阻'").fetchone()[0]
 locked=c.execute("select count(*) from coverage where task_type='work_media' and media='电子书' and status='访问受阻' and gap like '作品页显示被锁定或删除%'").fetchone()[0]
 cp_note=f'长佩{cp_detail}条有公开网页详情证据；读取器曾仅返回页脚，历史访问限制保留，不等于当前全部受阻。'
 stamp=now();p={'at':stamp,'batch':batch,'cutoff':'2026-11-10','status':'部分完成','candidate_source_records':n,'qualified_source_records':qualified,'touched_records':touched,'metadata_records':detail,'non_ebook_initial_search_records':cross,'no_checks_yet':n-touched,'remaining_jj_detail':len(pending),'next_jj_detail':pending[:10],'counts':counts,'cloud_validation':cloud,'global_denominator':None}
 (ROOT/'data/progress.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
 (ROOT/'data'/f'progress-{batch}.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
 text=f'''# 执行状态

保存时间：{stamp}；最近批次：{batch}。截止日北京时间2026-11-10，窗口自2024-01-01起。

P1进行中；全量目标不变，行业调查未完成。{n}条候选来源记录，{qualified}条纳入依据已确认；跨站重发身份未核完，不称去重原著总体。目录总体未知，不报全站覆盖率。

{touched}条至少有一项核查，{n-touched}条完全未查；{detail}条有作品详情证据；{cross}条进行过非电子书媒介初查。这些是不同进度口径，详情核验不等于跨媒介完成，索引初查不等于穷尽。

产品{counts['products']}条、事件{counts['events']}条、指标{counts['observations']}项、证据{counts['evidence']}条、核查历史{counts['check_history']}条。原首轮12部样本标记保留，后续批次不追加为样本。字段空白不填零，当前累计不填历史。

晋江目录第11页需合法登录；详情电子书核查有{blocked}条访问受阻，其中{locked}条已由原响应确认显示锁定或删除提示，具体状态仍待证。未知解析失败先核对原响应，不能直接判定为账号限制。来源暂停时继续其他独立来源，不绕过。{cp_note}剩余晋江详情{len(pending)}条；所有作品仍需各媒介站内、海外译名、下架及历史商业表现深查。

飞书只用CLI。每批差异预览、幂等写入、完整分页回读和关联核验。最新云端核验位置：{cloud or '尚待本批同步'}；真实部署位置和回执不入Git。超过2000行必须继续分页，不静默截断。

本地每批保留状态与证据，快照有SHA256清单。代码提交不含完整研究数据或凭据。未有安全跨设备目的地前，数据备份仅本地。

下一步：按data/progress.json及批次清单续查；先核对未完成CLI写入实际结果，再恢复，不能盲重试。原发/签约、跨站版本及已发现线索分别复核。无周期任务或通知。
'''
 (ROOT/'docs/STATUS.md').write_text(text,encoding='utf-8');c.close();return p
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--batch',required=True);p.add_argument('--cloud');a=p.parse_args();print(json.dumps(save(a.batch,a.cloud),ensure_ascii=False))
