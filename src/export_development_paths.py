"""Export sourced product/edition paths without counting editions as IP deals."""
from research import *
from collections import Counter


def build():
    c=connect()
    products=[dict(r) for r in c.execute('select p.*,e.published_at source_published_at from products p left join evidence e on e.id=p.evidence_id order by p.title,p.id')]
    parents={r['parent_id'] for r in products if r['parent_id']}
    rows=[]
    for p in products:
        works=[dict(r) for r in c.execute('select w.id,w.title,w.author,w.platform,w.source_id,w.inclusion_status from works w join product_works pw on w.id=pw.work_id where pw.product_id=? order by w.id',(p['id'],))]
        events=[dict(r) for r in c.execute('select event_type,event_time,time_end,time_precision,description,window_role,evidence_id from events where product_id=? order by event_time,id',(p['id'],))]
        grain='系列父记录' if p['id'] in parents else '季/篇/卷子记录' if p['parent_id'] else '项目或粒度未细分条目'
        rows.append(dict(product_id=p['id'],title=p['title'],grain=grain,parent_id=p['parent_id'],media=p['media'],season=p['season'],language=p['language'],markets=p['markets'],producer_as_credited=p['producer'],distributor_as_credited=p['distributor'],platform=p['platform'],source_product_id=p['source_id'],pay_model=p['pay_model'],status=p['status'],confirmation=p['confirmation'],source_published_at=p['source_published_at'],source_url=p['source_url'],evidence_id=p['evidence_id'],linked_works=json.dumps(works,ensure_ascii=False),timeline=json.dumps(events,ensure_ascii=False),contract_assignment='本导出未将同作品/媒介披露自动分配到该产品合同；签署期及独立合同关系见权利台账'))
    c.close()
    path=ROOT/'exports/development-paths.csv'
    if rows:
        with path.open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    summary={'at':now(),'cutoff':'2026-11-10','rows':len(rows),'structural_grain_counts':dict(Counter(r['grain'] for r in rows)),'independent_contracts':None,'global_denominator':None,'limits':'全部已保存产品/版本条目，含系列父记录、历史背景、未来计划及授权待核条目；不是2024年以来新增成交分母。公司按原署名保留，出品/制作/发行/技术服务不自动转为版权受让方。','csv':'exports/development-paths.csv'}
    (ROOT/'data/development-paths-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 项目与版本开发路径','',f"保存：{summary['at']}；成交观察窗口：2024-01-01至2026-11-10。",'',summary['limits'],'',f"当前导出{len(rows)}条项目/版本记录；结构粒度："+json.dumps(summary['structural_grain_counts'],ensure_ascii=False)+'。不将篇章、活动期次、城市或渠道数当作合同数。','',
           '逐条CSV保留原著身份/资格、父子项目、媒介、季篇、地域语言、制作/发行署名、渠道、来源及事件日期精度。时间轴同时含公告、计划、执行披露和历史背景，须按事件类型解释，不能把最早上线或公告日视为签署日。',
           '', '已补的可复核路径示例：','',
           '- 日本《魔道祖师》舞台：2024-11-01共同开发公告 → 2025邂逅篇 → 2026遡洄篇 → 截止前已宣布第三篇（当前页列2027计划，细节不倒填）。Marvelous和Sony Music Solutions共同开发；Tixplus是票务服务角色。实际IP签署期和篇章合同关系未公开，不能计为三笔窗口成交。[公司开发公告](https://corp.marv.jp/img/20241101_mdzs.pdf)、[第二篇资料](https://www.marv.jp/titles/st/11009/)、[票务服务公告](https://m-upholdings.co.jp/ir_financer/news/pdf/20250227_mdzs_stage_l3g09al3hosie.pdf)。',
           '- 《某某》木灵主题餐厅：2026-08-21官方称杭州/广州第三期已开启；这是运营披露，实际开业日和主题餐厅签署期未知。原著周边2023签约信息不能移用于餐厅。[官方运营披露](https://www.sina.cn/news/detail/5334412539724736.html)。',
           '- 《我在无限游戏里封神》广播剧：猫耳官方2025-06-10“破亿”宣传与线下大屏打卡公告，署名风音Studio制作。该阈值未明确定义，不与销量/订阅/其他产品播放作可比变化，不推授权费。[官方公告](https://www.sina.cn/news/detail/5176024698454886.html)。',
           '- 《论救错反派的下场》：Seven Seas英文电子授权与OverDrive的Indy Pub条目分开。后者只确认渠道元数据，授权链及语言未核；页面列示2025发行不能当2025授权销售。[官方英文授权](https://sevenseasentertainment.com/2024/10/23/seven-seas-licenses-twelve-new-danmei/)、[待核渠道条目](https://www.overdrive.com/media/11725985/)。',
           '', '仍需补：对应签署发生期、交易主体与再授权/续约/追加关系、实际逐期执行、口径可比的历史表现；未确认的字段继续为空。该文件是行业分析的可核实底稿，不替代最终全量行业报告。','']
    (ROOT/'exports/development-paths.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))
    return summary


if __name__=='__main__':build()
