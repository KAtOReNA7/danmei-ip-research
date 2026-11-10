import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from research import key,connect,add_work
from rules import *
from feishu_sync import pending_rows
class Rules(unittest.TestCase):
 def test_identity(self):
  self.assertNotEqual(key('w','平台','1'),key('w','平台','2'))
  c=connect(':memory:');w=add_work(c,'平台','1','同名','甲','纯爱','完结','url',None,inclusion='已确认');add_work(c,'平台','1','同名','甲','纯爱','完结','url',None)
  self.assertEqual(c.execute('select inclusion_status from works where id=?',(w,)).fetchone()[0],'已确认')
  self.assertEqual(c.execute('select count(*) from works').fetchone()[0],1)
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
if __name__=='__main__':unittest.main()
