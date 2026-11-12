"""Save truthful resumable progress, separating metadata checks from media searches."""
from research import *
def save(batch,cloud=None):
 c=connect();n=c.execute('select count(*) from works').fetchone()[0]
 counts={t:c.execute('select count(*) from '+t).fetchone()[0] for t in ['rights_records','products','events','observations','evidence','check_history']}
 qualified=c.execute("select count(*) from works where inclusion_status='已确认'").fetchone()[0]
 inclusion_counts=dict(c.execute('select inclusion_status,count(*) from works group by inclusion_status').fetchall())
 touched=c.execute("select count(distinct work_id) from coverage where task_type='work_media' and status!='未调查'").fetchone()[0]
 cross=c.execute("select count(distinct work_id) from coverage where task_type='work_media' and media!='电子书' and status!='未调查'").fetchone()[0]
 pending=[dict(r) for r in c.execute('select id,source_id,title,author,platform from works where '+JJ_PENDING_WHERE+' order by cast(source_id as integer)')]
 unresolved_jj=c.execute("select count(*) from works where platform='晋江' and signing_evidence is null").fetchone()[0]
 detail=c.execute("select count(*) from works where signing_evidence is not null or exists(select 1 from coverage cv where cv.work_id=works.id and cv.task_type='qualification' and cv.status='已核验')").fetchone()[0]
 cp_detail=c.execute("select count(*) from works where platform='长佩' and (signing_evidence is not null or exists(select 1 from coverage cv where cv.work_id=works.id and cv.task_type='qualification' and cv.status='已核验'))").fetchone()[0]
 blocked=c.execute("select count(*) from coverage where task_type='work_media' and media='电子书' and status='访问受阻'").fetchone()[0]
 locked=c.execute("select count(*) from coverage where task_type='work_media' and media='电子书' and status='访问受阻' and gap like '作品页显示被锁定或删除%'").fetchone()[0]
 cp_note=f'长佩{cp_detail}条有公开网页详情证据；读取器曾仅返回页脚，历史访问限制保留，不等于当前全部受阻。'
 directory_access=ROOT/'data/directory-access.json'
 directory_note=json.loads(directory_access.read_text(encoding='utf-8'))['jj_page11'] if directory_access.exists() else '晋江目录第11页需合法登录'
 backup_note='数据备份仅本地；跨设备私有备份未核验。'
 backup_status=ROOT/'data/backup-destination-status.json'
 if backup_status.exists():
  backup=json.loads(backup_status.read_text(encoding='utf-8'))
  if backup.get('cloud_uploaded'):
   backup_note='已有Google Drive私有快照，权限、父文件夹及文件大小已回读；云端下载校验尚未完成。'
   if backup.get('download_sha256_verified'):
    backup_note='Google Drive私有快照已上传并下载回读，SHA256及包内校验通过；远端快照时间与本轮本地进度分别记录，后续批次不冒充已备份。'
 runtime_file=ROOT/'data/source-runtime-status.json'
 runtime=json.loads(runtime_file.read_text(encoding='utf-8')) if runtime_file.exists() else None
 runtime_note=' 当前内置浏览器不可用，以上登录/渲染成功仅为历史状态；长佩渲染资格队列未计本轮完成，继续公开HTTP/索引等独立来源，不切Chrome。' if runtime and runtime.get('iab')=='unavailable' else ''
 stamp=now();p={'at':stamp,'batch':batch,'cutoff':'2026-11-10','status':'部分完成','candidate_source_records':n,'qualified_source_records':qualified,'touched_records':touched,'metadata_records':detail,'non_ebook_initial_search_records':cross,'no_checks_yet':n-touched,'remaining_jj_detail':len(pending),'next_jj_detail':pending[:10],'counts':counts,'cloud_validation':cloud,'global_denominator':None,'backup_status':backup_note,'source_runtime':runtime}
 (ROOT/'data/progress.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
 p['research_priority']='V1.2开发阶段连续采集整理；主线仍为窗口内已售出/已授权签约，上线不证明窗口内售出'
 p['work_eligibility_pending']=inclusion_counts.get('待核',0)
 p['excluded_source_records']=inclusion_counts.get('排除',0)
 p['remaining_jj_detail_basis']='常规队列排除已有官方锁删提示；这些候选及资格缺口仍保留，不自动排除'
 p['remaining_jj_signing_evidence_missing_including_locked']=unresolved_jj
 p['development_cadence']='本批本地落盘；仅同步变更表并回读。完整审核与私有备份留到里程碑，不代表本批已云端备份。'
 p['rights_window_summary']=[dict(r) for r in c.execute('select window_role,count(*) source_rows,count(distinct work_id) works from rights_records group by window_role')]
 p['independent_deal_count']=None
 (ROOT/'data/progress.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
 (ROOT/'data'/f'progress-{batch}.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
 text=f'''# 执行状态

保存时间：{stamp}；最近批次：{batch}。截止日北京时间2026-11-10，窗口自2024-01-01起。

P1进行中；全量目标不变，行业调查未完成。{n}条候选来源记录，{qualified}条纳入依据已确认；跨站重发身份未核完，不称去重原著总体。目录总体未知，不报全站覆盖率。

{touched}条至少有一项核查，{n-touched}条完全未查；{detail}条有作品详情证据；{cross}条进行过非电子书媒介初查。这些是不同进度口径，详情核验不等于跨媒介完成，索引初查不等于穷尽。

产品{counts['products']}条、事件{counts['events']}条、指标{counts['observations']}项、证据{counts['evidence']}条、核查历史{counts['check_history']}条。原首轮12部样本标记保留，后续批次不追加为样本。字段空白不填零，当前累计不填历史。

{directory_note}；详情电子书核查有{blocked}条访问受阻，其中{locked}条已由原响应确认显示锁定或删除提示，具体状态仍待证。未知解析失败先核对原响应，不能直接判定为账号限制。来源暂停时继续其他独立来源，不绕过。{cp_note}{runtime_note}剩余晋江详情{len(pending)}条；所有作品仍需各媒介站内、海外译名、下架及历史商业表现深查。

飞书只用CLI。开发阶段仅同步变更表，完整分页回读本批写入字段及关联；未变更表沿用既有回读，不称本轮全量核验。最新本批回读位置：{cloud or '尚待本批同步'}；真实部署位置和回执不入Git。超过2000行必须继续分页，不静默截断。

本地每批保留状态与证据；开发批次不逐轮备份上传下载，完整核验和备份留到里程碑。代码提交不含完整研究数据或凭据。既有历史备份状态：{backup_note}本批新增数据以本地进度为准。

主线V1.1：窗口内已售出/已授权签约优先，上线不证明2024年以来售出。权利披露{counts['rights_records']}行，独立合同数未知；详见exports/rights-sales-report.md。签约日期缺失及跨截止日单列，泛媒介初查不等于售出调查完成。

下一步：优先追官方签约披露的时间、地域/语言、受让方、续约追加及同合同关系，再补执行与表现。按data/progress.json及批次清单续查；未完成CLI先核实际结果，不能盲重试。无周期任务或通知。
'''
 (ROOT/'docs/STATUS.md').write_text(text,encoding='utf-8');c.close()
 from progress_brief import write_brief
 write_brief(p)
 return p
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--batch',required=True);p.add_argument('--cloud');a=p.parse_args();print(json.dumps(save(a.batch,a.cloud),ensure_ascii=False))
