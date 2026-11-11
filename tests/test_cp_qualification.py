import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from research import connect,add_work
from ingest_cp_qualification_metadata import ingest

class CPQualification(unittest.TestCase):
    def test_generic_original_category_stays_pending(self):
        c=connect(':memory:');rows=[]
        for sid,category in [('generic','原创悬疑'),('explicit','百合架空')]:
            add_work(c,'长佩',sid,'测试'+sid,'作者',None,None,'https://example/'+sid,None)
            rows.append(dict(expected_id=sid,source_id='CP'+sid,title='测试'+sid,url='https://example/'+sid,status_metadata='作者 著'+category+'·完结',author_links=[{'author':'作者'}],captured_at='2026-11-11T10:00:00Z'))
        with patch('ingest_cp_qualification_metadata.evidence',return_value=None):result=ingest(c,{'rows':rows,'method':'test'},'category')
        works={r['source_id']:dict(r) for r in c.execute('select * from works')}
        self.assertEqual(works['generic']['inclusion_status'],'待核');self.assertIsNone(works['generic']['category_mapped'])
        self.assertEqual(works['explicit']['inclusion_status'],'排除')
        self.assertEqual((result['category_pending'],result['excluded']),(1,1));self.assertEqual(c.execute('select count(*) from exclusions').fetchone()[0],1)
        c.close()

    def test_loaded_work_signing_marker_is_preserved_without_inferring_from_absence(self):
        c=connect(':memory:')
        for sid in ['unsigned','signed','absent']:
            add_work(c,'长佩',sid,'测试作品'+sid,'测试作者',None,None,'https://example/'+sid,None)
        rows=[dict(expected_id=sid,source_id='CP'+sid,title='测试作品'+sid,url='https://example/'+sid,status_metadata='测试作者 著纯爱架空·完结'+suffix,author_links=[{'author':'测试作者','url':'https://example/author'}],captured_at='2026-11-11T00:00:00+08:00') for sid,suffix in [('unsigned','·尚未签约'),('signed','·已签约'),('absent','')]]
        with patch('ingest_cp_qualification_metadata.evidence',return_value=None):ingest(c,{'rows':rows,'method':'test'},'test-marker')
        works={r['source_id']:dict(r) for r in c.execute('select * from works')}
        self.assertEqual((works['unsigned']['signing_raw'],works['unsigned']['inclusion_status']),('尚未签约','待核'))
        self.assertEqual(works['signed']['inclusion_status'],'已确认')
        self.assertIsNone(works['absent']['signing_raw']);self.assertEqual(works['absent']['inclusion_status'],'待核')
        self.assertEqual(c.execute("select count(*) from coverage where task_type='work_media' and status='未调查'").fetchone()[0],27)
        c.close()

    def test_commercial_credit_does_not_promote_work_eligibility(self):
        import tempfile,json,contextlib,io
        import ingest_commercial_continuation as commercial
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'data').mkdir();(root/'evidence/search').mkdir(parents=True)
            db=root/'test.sqlite';c=connect(db)
            wid=add_work(c,'长佩','fixture','测试作品','测试作者','纯爱架空','完结','https://example/work',None);c.commit();c.close()
            items=[{'source_id':str(i),'author':'测试作者'} for i in range(9)]
            (root/'data/p1-004.json').write_text(json.dumps({'works':items,'results':{str(i):{'inclusion':True} for i in range(9)}}),encoding='utf-8')
            sources=[{'key':k,'url':'https://example/'+k,'title':'官方产品署名','subject':'制作方','excerpt':'作品署名','facts':'漫画项目关联已核'} for k in ['comic-update','cards','paper-exclude']]
            path=root/'input.json';path.write_text(json.dumps({'batch':'test-credit','platform':'长佩','source_id':'fixture','sources':sources,'limitations':[],'captured_at':'2026-11-10T00:00:00+08:00','products':[],'events':[]},ensure_ascii=False),encoding='utf-8')
            with patch.object(commercial,'ROOT',root),patch.object(commercial,'connect',side_effect=lambda:connect(db)),patch.object(commercial,'evidence',return_value=None),patch.object(commercial,'export'),contextlib.redirect_stdout(io.StringIO()):commercial.run(path)
            c=connect(db);w=c.execute('select * from works where id=?',(wid,)).fetchone()
            self.assertEqual(w['inclusion_status'],'待核');self.assertIsNone(w['identity_evidence']);self.assertIsNone(w['signing_evidence'])
            self.assertEqual(c.execute("select status from coverage where work_id=? and media='漫画'",(wid,)).fetchone()[0],'已确认')
            c.close()
