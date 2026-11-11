import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from rights_rules import sale_window,rights_media

class RightsRules(unittest.TestCase):
    def test_sale_window_never_inherits_or_uses_launch(self):
        self.assertEqual(sale_window(None)['window_role'],'签约时间待核')
        self.assertEqual(sale_window('2024')['window_role'],'窗口内签约年份')
        self.assertEqual(sale_window('2026')['window_role'],'跨截止日待核')
        self.assertEqual(sale_window('2023')['window_role'],'窗口前背景')
        self.assertEqual(sale_window('2024')['end'],'2024-12-31T23:59:59+08:00')
        self.assertEqual(sale_window('2023-12')['window_role'],'窗口前背景')
        self.assertEqual(sale_window('2024-01')['window_role'],'窗口内签约月份')
        self.assertEqual(sale_window('2026-10')['window_role'],'窗口内签约月份')
        self.assertEqual(sale_window('2026-11')['window_role'],'跨截止日待核')
        self.assertEqual(sale_window('2026-12')['window_role'],'窗口后')
    def test_derived_merch_is_not_another_broadcast(self):
        self.assertEqual(rights_media('广播剧周边衍生品'),'官方周边联名')
        self.assertEqual(rights_media('广播剧周边'),'官方周边联名')
        self.assertEqual(rights_media('有声书周边'),'官方周边联名')
        self.assertEqual(rights_media('周边衍生'),'官方周边联名')
        self.assertEqual(rights_media('有声读物'),'有声书')
        self.assertEqual(rights_media('影视'),'影视短剧')
        self.assertEqual(rights_media('漫画线下活动'),'舞台线下')
        self.assertEqual(rights_media('外文广播剧(日本)'),'广播剧')
        self.assertIsNone(rights_media('音乐'))
