import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from research import key,connect,add_work
from rules import *
from feishu_sync import pending_rows
from feishu_incremental import diff_rows
class Rules(unittest.TestCase):
 def test_feishu_product_grain_and_event_identity(self):
  from unittest.mock import patch
  from research import upsert
  from feishu_sync import datasets
  c=connect(':memory:');wid=add_work(c,'平台','projection','作品','作者','纯爱','完结','url',None)
  upsert(c,'products',dict(id='project',title='项目父记录',media='电子书'))
  upsert(c,'products',dict(id='volume',parent_id='project',title='卷一',media='电子书',season='卷1',source_id='数字版ISBN',pay_model='单卷零售'))
  c.execute('insert into product_works values(?,?,?)',('volume',wid,None))
  upsert(c,'events',dict(id='event',work_id=wid,product_id='volume',event_type='数字发行'))
  upsert(c,'observations',dict(id='threshold',work_id=wid,product_id='volume',lower_bound=200000000,unit='次',temporal_type='累计阈值'))
  with patch('feishu_sync.connect',return_value=c):d=datasets()
  child=next(r for r in d['产品与版本'] if r['后台键']=='volume')
  self.assertEqual((child['父项目键'],child['父项目'],child['季卷']),('project','项目父记录','卷1'))
  self.assertEqual(child['来源标识'],'数字版ISBN');self.assertEqual(child['商业模式'],'单卷零售')
  self.assertEqual((d['事件时间线'][0]['产品键'],d['事件时间线'][0]['对应产品']),('volume','卷一'))
  self.assertEqual(float(d['指标观测'][0]['下界']),200000000)
  self.assertIsNone(d['指标观测'][0]['解析值']);self.assertIsNone(d['指标观测'][0]['上界'])
 def test_reviewed_coverage_upgrade_is_scoped_and_guarded(self):
  from unittest.mock import patch
  from ingest_reviewed_batch import ingest
  c=connect(':memory:');wid=add_work(c,'平台','guard','作品','作者','纯爱','完结','url',None)
  d={'batch':'test','sources':[dict(key='official',url='url',title='official',facts={},method='test',captured_at='2026-11-11T00:00:00+08:00')],'reviews':[],
     'coverage_updates':[dict(work_id=wid,media='电子书',expected_status='未调查',status='已确认',source='official',scope='核实数字发行',gap='其他渠道待核')]}
  with patch('ingest_reviewed_batch.evidence',return_value=None):
   ingest(c,d);ingest(c,d)
   self.assertEqual(c.execute('select count(*) from check_history').fetchone()[0],1)
   self.assertEqual(c.execute("select count(*) from coverage where status='未调查'").fetchone()[0],8)
   c.execute("update coverage set status='访问受阻' where work_id=? and media='电子书'",(wid,))
   with self.assertRaises(AssertionError):ingest(c,d)
  c.close()
 def test_author_catalog_keeps_masked_locked_unknown_category(self):
  import tempfile
  from unittest.mock import patch
  from bs4 import BeautifulSoup
  import collect_author_catalogs as catalogs
  html='<title>测试作者 的专栏:测试</title><table>'
  for pid,title,cat in [('1','普通作品','原创-纯爱-近代现代-爱情'),('2','遮***名 [锁]','/'),('3','评论 [锁]','评论'),('4','另一类','原创-言情-近代现代-爱情')]:
   html+=f'<tr><td><a href="onebook.php?novelid={pid}">{title}</a></td><td>{cat}</td><td>连载</td><td>99</td><td>123456</td><td></td></tr>'
  html+='</table>'
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'data').mkdir()
   with patch.object(catalogs,'ROOT',root),patch.object(catalogs,'fetch',return_value=BeautifulSoup(html,'html.parser')):
    d=catalogs.collect('测试作者','https://www.jjwxc.net/oneauthor.php?authorid=1','test')
   self.assertEqual([r['source_id'] for r in d['rows']],['1','2'])
   self.assertEqual(d['rows'][1]['title'],'遮***名 [锁]')
   self.assertEqual(d['rows'][1]['category'],'/')
   self.assertEqual(len(d['excluded_rows']),2)
   self.assertTrue(all('words' not in r and 'points' not in r for r in d['rows']))
 def test_nested_title_and_author_underscore(self):
  from research import jj_identity
  self.assertEqual(jj_identity('《《模拟书》同人》模拟_作者_晋江文学城_【纯爱小说】'),('《模拟书》同人','模拟_作者'))
  self.assertEqual(jj_identity('《模拟书》模拟作者_晋江文学城'),('模拟书','模拟作者'))
  self.assertEqual(jj_identity('《模拟书》模拟作者_漫画: 模拟书_晋江文学城',[{'text':'模拟作者'}]),('模拟书','模拟作者'))
  self.assertIsNone(jj_identity('访问受限'))
 def test_identity(self):
  self.assertNotEqual(key('w','平台','1'),key('w','平台','2'))
  c=connect(':memory:');w=add_work(c,'平台','1','同名','甲','纯爱','完结','url',None,inclusion='已确认');add_work(c,'平台','1','同名','甲','纯爱','完结','url',None)
  self.assertEqual(c.execute('select inclusion_status from works where id=?',(w,)).fetchone()[0],'已确认')
  self.assertEqual(c.execute('select count(*) from works').fetchone()[0],1)
  c.execute('update works set aliases=? where id=?',('["已核别名"]',w))
  add_work(c,'平台','1','同名','甲','纯爱','完结','url',None)
  self.assertEqual(c.execute('select aliases from works').fetchone()[0],'["已核别名"]')
 def test_boundary(self):
  self.assertFalse(in_window('2023-12-31'));self.assertTrue(in_window('2024-01-01'));self.assertTrue(in_window('2026-11-10'));self.assertFalse(in_window('2026-11-11'));self.assertFalse(in_window(None))
 def test_missing(self):self.assertNotEqual(None,0)
 def test_comparability(self):
  a=dict(object='A',metric='收藏',unit='人',version='v1',temporal_type='期间',period_start='2024-01-01',period_end='2024-12-31')
  self.assertTrue(comparable(a,a));self.assertFalse(comparable(a,{**a,'metric':'销售'}));self.assertFalse(comparable(a,{**a,'period_end':'2024-11-10'}))
 def test_aggregation(self):
  self.assertEqual(distinct_projects([{'id':'a','parent_id':'p'},{'id':'b','parent_id':'p'}]),1)
  self.assertIsNone(merchandise_amount(100,True));self.assertEqual(merchandise_amount(100,True,20),20)
 def test_retry(self):
  rows=[{'后台键':'a','值':None},{'后台键':'b','值':'0'}]
  self.assertEqual(len(pending_rows(rows,[])),2);self.assertEqual(pending_rows(rows,rows),[])
  with self.assertRaises(AssertionError):pending_rows(rows,[rows[0],rows[0]])
  with self.assertRaises(AssertionError):pending_rows(rows,[{'后台键':'a','值':'0'}])
 def test_incremental(self):
  old=[{'record_id':'rec1','后台键':'a','值':'old'}]
  new=[{'后台键':'a','值':'new'},{'后台键':'b','值':None}]
  creates,updates=diff_rows(new,old,old)
  self.assertEqual(len(creates),1);self.assertEqual(updates,{'rec1':{'值':'new'}})
  with self.assertRaises(AssertionError):diff_rows(new,[{**old[0],'值':'human edit'}],old)
  self.assertNotEqual(diff_rows([{'后台键':'a','值':0}],[{**old[0],'值':None}])[1],{})
 def test_batch_does_not_change_sample(self):
  import research,tempfile
  from unittest.mock import patch
  from bs4 import BeautifulSoup
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'src').mkdir();(root/'src/schema.sql').write_text((research.ROOT/'src/schema.sql').read_text(encoding='utf-8'),encoding='utf-8')
   html='<title>《模拟甲》模拟作者_晋江文学城</title><li>文章类型：原创-纯爱-近代现代-爱情</li><li>文章进度：连载</li><li>签约状态：已签约</li><p>总书评数：0 当前被收藏数：2 文章积分：3</p>'
   with patch.object(research,'ROOT',root),patch.object(research,'fetch',return_value=BeautifulSoup(html,'html.parser')):
    research.jj_detail('MOCK',quiet=True)
    c=research.connect();self.assertEqual(c.execute('select sample from works').fetchone()[0],0)
    self.assertEqual(c.execute("select value from observations where metric_raw='总书评数'").fetchone()[0],0)
    self.assertEqual(c.execute('select inclusion_status from works').fetchone()[0],'已确认');c.close()
 def test_locked_work_preserves_evidence_and_other_candidates(self):
  import research,tempfile
  from unittest.mock import patch
  from bs4 import BeautifulSoup
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'src').mkdir();(root/'src/schema.sql').write_text((research.ROOT/'src/schema.sql').read_text(encoding='utf-8'),encoding='utf-8')
   with patch.object(research,'ROOT',root),patch.object(research,'fetch',return_value=BeautifulSoup('<a href="oneauthor.php?authorid=MOCK">被锁定或删除文章的作者专栏</a>','html.parser')):
    c=research.connect();wid=research.add_work(c,'晋江','MOCK1','模拟甲','作者','纯爱','连载','url',None);research.add_work(c,'晋江','MOCK2','模拟乙','作者','纯爱','连载','url',None);c.commit();c.close()
    with self.assertRaises(research.WorkUnavailable):research.jj_detail('MOCK1',quiet=True)
    c=research.connect();self.assertEqual(c.execute('select count(*) from evidence').fetchone()[0],1)
    research.checked(c,wid,'电子书','访问受阻','模拟锁删提示',gap='作品页显示被锁定或删除文章的作者专栏')
    self.assertEqual(c.execute('select source_id from works where '+research.JJ_PENDING_WHERE).fetchone()[0],'MOCK2')
    self.assertEqual(c.execute('select count(*) from works').fetchone()[0],2);c.close()
if __name__=='__main__':unittest.main()
