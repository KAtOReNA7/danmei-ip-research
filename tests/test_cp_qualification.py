import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from research import connect,add_work
from ingest_cp_qualification_metadata import ingest

class CPQualification(unittest.TestCase):
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
