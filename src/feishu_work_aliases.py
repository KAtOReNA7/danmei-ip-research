"""Create the work alias display column through the project CLI, then read back."""
from feishu_sync import *

def main():
    cfg=json.loads(CONFIG.read_text(encoding='utf-8'))
    args=['--base-token',cfg['base_token'],'--table-id',cfg['tables']['作品目录']]
    fields=cli(['+field-list',*args],'work-aliases-before')['data']['fields']
    missing='别名' not in {f['name'] for f in fields}
    if missing:
        path=ROOT/'receipts/work-alias-field.json';path.write_text(json.dumps([{'name':'别名','type':'text'}],ensure_ascii=False),encoding='utf-8')
        command=['+field-create',*args,'--json','@receipts/work-alias-field.json']
        cli(command+['--dry-run'],'work-aliases-preview');cli(command,'work-aliases-write')
    fields=cli(['+field-list',*args],'work-aliases-after')['data']['fields']
    assert '别名' in {f['name'] for f in fields}
    receipt={'created':int(missing),'schema_readback_match':True,'data_sync':'required separately; schema creation is not field backfill'}
    (ROOT/'receipts/work-aliases-schema-validation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()
