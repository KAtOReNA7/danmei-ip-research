"""Build a hash-linked supplement and a local combined archive for restore checks."""
import argparse,hashlib,json,zipfile
from pathlib import Path

def sha(raw):return hashlib.sha256(raw).hexdigest()

def verified_manifest(z):
    assert z.testzip() is None
    m=json.loads(z.read('manifest.json'))
    for name,value in m.items():
        assert not name.startswith(('/', '\\')) and ':' not in name and '..' not in Path(name).parts,name
        assert sha(z.read(name))==value,name
    return m

def build(base,current,base_url,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(base) as b,zipfile.ZipFile(current) as n:
        bm=verified_manifest(b);nm=verified_manifest(n)
        if 'RECOVERY_DELTA.json' in nm:
            required=json.loads(n.read('RECOVERY_DELTA.json'))
            assert required['base_sha256']==sha(Path(base).read_bytes()),'Supplement requires a different base archive'
        updates={k:n.read(k) for k in nm if bm.get(k)!=nm[k]}
        note={'base_filename':Path(base).name,'base_sha256':sha(Path(base).read_bytes()),'base_url':base_url,'current_archive_sha256':sha(Path(current).read_bytes()),'requires_base':True,'scope':'Overlay changed/new files on the verified base. Preserve unchanged base files. Current SQLite is complete; evidence and older receipts require the base.','changed_or_new_files':len(updates),'deletions':0}
        updates['RECOVERY_DELTA.json']=json.dumps(note,ensure_ascii=False,indent=2).encode()
        merged={**bm,**{k:sha(v) for k,v in updates.items()}}
        updates['COMBINED_MANIFEST.json']=json.dumps(merged,ensure_ascii=False,indent=2).encode()
        dm={k:sha(v) for k,v in updates.items()}
        delta=output/'recovery-supplement.zip'
        with zipfile.ZipFile(delta,'w',zipfile.ZIP_DEFLATED) as z:
            for k,v in updates.items():z.writestr(k,v)
            z.writestr('manifest.json',json.dumps(dm,ensure_ascii=False,indent=2))
        combined=output/'combined-recovery-check.zip'
        final_manifest={**merged,'COMBINED_MANIFEST.json':dm['COMBINED_MANIFEST.json']}
        with zipfile.ZipFile(combined,'w',zipfile.ZIP_DEFLATED) as z:
            for k in final_manifest:z.writestr(k,updates[k] if k in updates else b.read(k))
            z.writestr('manifest.json',json.dumps(final_manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(delta) as z:verified_manifest(z)
    with zipfile.ZipFile(combined) as z:verified_manifest(z)
    return {**note,'supplement':str(delta),'supplement_bytes':delta.stat().st_size,'supplement_sha256':sha(delta.read_bytes()),'combined_archive':str(combined),'combined_files':len(final_manifest),'combined_sha256':sha(combined.read_bytes())}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--current',required=True);p.add_argument('--base-url',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    print(json.dumps(build(a.base,a.current,a.base_url,a.output),ensure_ascii=False))
