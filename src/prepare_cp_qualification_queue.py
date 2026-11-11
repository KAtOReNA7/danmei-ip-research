"""Queue unreviewed works across every saved official rights-gallery capture."""
from research import *

def prepare(output,limit=25):
    c=connect();seen=set();pending=[];captures=[]
    for path in sorted((ROOT/'data').glob('cp-rights*-capture.json')):
        d=json.loads(path.read_text(encoding='utf-8'));assert d['method'].startswith('内置浏览器')
        captures.append(path.relative_to(ROOT).as_posix())
        sections=[('改编',p['page'],p['rows']) for p in d.get('adaptation_pages',[])]+[('海外改编',1,d.get('overseas_rows',[]))]
        for section,page,rows in sections:
            for r in rows:
                sid=r['source_id']
                if sid in seen:continue
                seen.add(sid)
                w=c.execute("select * from works where platform='长佩' and source_id=?",(sid,)).fetchone()
                assert w,'Capture must be imported before queueing: '+sid
                if w['signing_evidence'] or c.execute("select 1 from coverage where work_id=? and task_type='qualification'",(w['id'],)).fetchone():continue
                pending.append({**r,'title':w['title'],'author':w['author'],'listed_title':r['title'],'listed_author':r['author'],'origin_section':section,'origin_page':page,'origin_capture':path.relative_to(ROOT).as_posix()})
    total=c.execute("select count(*) from works w where platform='长佩' and signing_evidence is null and not exists(select 1 from coverage cv where cv.work_id=w.id and cv.task_type='qualification')").fetchone()[0]
    result={'created_at':now(),'selection':'所有已保存官方改编及海外改编捕获文件原序；每ID一次；跳过已有作品详情/资格证据或已记失效链接','source_captures':captures,'unreviewed_gallery_works':len(pending),'unreviewed_cp_source_records':total,'unreviewed_outside_captured_gallery':total-len(pending),'works':pending[:limit],'status':'固定待实际读取；队列生成不计调查完成'}
    (ROOT/output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');c.close();return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--limit',type=int,default=25);a=p.parse_args();r=prepare(a.output,a.limit);print(json.dumps({k:v for k,v in r.items() if k!='works'},ensure_ascii=False))
