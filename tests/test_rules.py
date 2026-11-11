import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from research import key,connect,add_work
from rules import *
from feishu_sync import pending_rows
from feishu_incremental import diff_rows
class Rules(unittest.TestCase):
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
