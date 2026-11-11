"""Import reviewed digital editions; group volumes, keep source-day timezone."""
from research import *

def run(path):
 d=json.loads(Path(path).read_text(encoding='utf-8'));c=connect()
 w=c.execute('select * from works where platform=? and source_id=?',(d['platform'],d['source_id'])).fetchone()
 assert w and w['author']==d['author'] and w['inclusion_status']=='已确认'
 wid=w['id'];stamp=d['captured_at'];limits=d['limitations']
 def ev(url,title,facts,subject,published=None):
  return evidence(c,url,title,{'facts':facts,'limitations':limits,'timestamp_note':d['timestamp_note']},subject,method='公开官方页面必要元数据；未打开正文或试读',published=published,accessed=stamp)
 parent_ev=ev(d['series_url'],d['english_title']+' 数字系列',d['series_facts'],'BookWalker')
 ev(d['publisher_url'],d['english_title']+' 授权及数字版背景公告',d['publisher_facts'],'Seven Seas Entertainment',d['publisher_date'])
 ev(d['library_url'],d['english_title']+' 卷1电子版交叉核验',d['library_facts'],'eLibrary NJ / OverDrive')
 parent=key('p','ebook_series','BookWalker',d['series_id'])
 upsert(c,'products',dict(id=parent,title=d['english_title']+'（英文电子书项目；卷级版本另列）',media='电子书',language='英语',markets=None,platform='BookWalker',source_id=d['series_id'],source_url=d['series_url'],producer='Seven Seas Entertainment',pay_model='数字电子书零售；各卷分别付费',status='项目层级；不与卷级版本相加计数',confirmation='已确认',evidence_id=parent_ev))
 c.execute('INSERT OR IGNORE INTO product_works VALUES(?,?,?)',(parent,wid,parent_ev))
 aliases=set(json.loads(w['aliases'] or '[]'));aliases.add(d['english_title']);c.execute('update works set aliases=? where id=?',(json.dumps(sorted(aliases),ensure_ascii=False),wid))
 for v in d['volumes']:
  assert v['format']=='Digital E-Book' and v['tz'] in ['PDT','PST']
  assert '2024-01-01'<=v['date']<='2026-11-10'
  title=d['english_title']+f" Vol. {v['volume']}（英文电子书）"
  eid=ev(v['url'],title,v,'BookWalker')
  pid=key('p','ebook_isbn',v['isbn'])
  upsert(c,'products',dict(id=pid,parent_id=parent,title=title,media='电子书',season=f"卷{v['volume']}",language='英语',markets=None,platform='BookWalker',source_id=v['source_id'],source_url=v['url'],producer=v['publisher'],pay_model='数字电子书单卷零售；未采实时价格',status='平台历史数字发行日期已核',confirmation='已确认',evidence_id=eid))
  c.execute('INSERT OR IGNORE INTO product_works VALUES(?,?,?)',(pid,wid,eid))
  end=(datetime.fromisoformat(v['date'])+timedelta(days=1)).date().isoformat()
  description=f"BookWalker卷{v['volume']}数字版，ISBN {v['isbn']}；Publication Date原文日期为{v['date']} {v['tz']}，无小时；北京时间日历范围为{v['date']}至{end}，不是持续两天的活动。按平台数字发行口径记录，不推为全球发行日。"
  upsert(c,'events',dict(id=key('event',pid,'BookWalker数字发行',v['date']),work_id=wid,product_id=pid,event_type='数字电子书发行（平台日期）',event_time=v['date'],time_end=end,time_precision='北京时间日期范围；来源日精度',description=description,window_role='观察窗口内；截止日后回溯核验',confirmation='已确认',evidence_id=eid))
 checked(c,wid,'电子书','已确认','原有电子连载证据及BookWalker英文数字系列8卷；卷1OverDrive交叉核验',parent_ev,'仅核数字发行项目与版本；其他语种、发行市场和历史销售待查；未采用实时价格/馆藏数')
 upsert(c,'source_matrix',dict(id=key('source','BookWalker数字版元数据'),media='电子书',source_name='BookWalker官方数字商品页',url=d['series_url'],events_available='卷级数字发行日期、来源时区、ISBN可查',current_values='零售页面有价格但本批不采，非销量',historical_values='可回溯各卷发行日期；没有销售序列',access_condition='无需登录的公开商品元数据；不打开试读正文',test_result='8卷数字类型及作者匹配；项目/卷/渠道分别计数',evidence_id=parent_ev,next_action='其他作品/语种/实际市场及历史表现；跨渠道同ISBN不重复计卷'))
 c.commit();c.close();export();print(json.dumps({'batch':d['batch'],'projects':1,'digital_volumes':len(d['volumes']),'release_events':len(d['volumes']),'new_metrics':0},ensure_ascii=False))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('path');a=p.parse_args();run(a.path)
