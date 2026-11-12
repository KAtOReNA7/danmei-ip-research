import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from rights_rules import sale_window,rights_media,license_disclosure_window,completed_signing_period

class RightsRules(unittest.TestCase):
    def test_completed_period_requires_independent_signing_period(self):
        r=completed_signing_period('2026','2026-06-12',explicit_completed=True)
        self.assertEqual(r['window_role'],'窗口内签约年份')
        self.assertEqual(r['start'],'2026-01-01T00:00:00+08:00')
        self.assertEqual(r['end'],'2026-06-13T23:59:59+08:00')
        self.assertEqual(completed_signing_period(None,'2026-06-12',explicit_completed=True)['window_role'],'签约时间待核')
        self.assertEqual(completed_signing_period('2026','2026-06-12',explicit_completed=False)['window_role'],'签约时间待核')
        self.assertEqual(completed_signing_period('2026','2026-11-10',explicit_completed=True)['window_role'],'跨截止日待核')
        self.assertEqual(completed_signing_period('2026','2025-12-01',explicit_completed=True)['window_role'],'签约时间待核')
        self.assertEqual(completed_signing_period('2023','2026-06-12',explicit_completed=True)['window_role'],'窗口前背景')

    def test_explicit_signing_day_boundaries(self):
        for day in ['2024-01-01','2026-08-22','2026-11-10']:
            self.assertEqual(sale_window(day)['window_role'],'窗口内签约日期')
        self.assertEqual(sale_window('2023-12-31')['window_role'],'窗口前背景')
        self.assertEqual(sale_window('2026-11-11')['window_role'],'窗口后')
        self.assertEqual(sale_window('2026-08-22')['end'],'2026-08-22T23:59:59+08:00')

    def test_license_disclosure_is_a_bound_not_a_signing_date(self):
        old=license_disclosure_window('2022-08-31',acquired=True)
        self.assertEqual(old['window_role'],'窗口前已获授权披露')
        self.assertIsNone(old['contract_time_raw']);self.assertIsNone(old['contract_start']);self.assertIsNone(old['contract_end'])
        for day in ['2023-12-31','2024-06-01','2026-11-12']:
            self.assertEqual(license_disclosure_window(day,acquired=True)['window_role'],'签约时间待核')
        self.assertEqual(license_disclosure_window('2022-08-31',acquired=False)['window_role'],'签约时间待核')

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
        self.assertIsNone(rights_media('互动小说'))
