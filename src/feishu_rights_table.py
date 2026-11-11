"""Create only the project rights disclosure table and verify schema via CLI."""
from feishu_sync import *

def main():
    cfg=json.loads(CONFIG.read_text(encoding='utf-8'));name='授权签约';rows=datasets()[name];assert rows
    tid=cfg['tables'].get(name)
    if not tid:
        args=['+table-create','--base-token',cfg['base_token'],'--name',name,'--fields',json.dumps([{'name':k,'type':'text'} for k in rows[0]],ensure_ascii=False)]
        cli(args+['--dry-run'],'rights-table-preview')
        r=cli(args,'rights-table-create');tid=r['data']['table']['id']
        cfg['tables'][name]=tid;CONFIG.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
    args=['--base-token',cfg['base_token'],'--table-id',tid]
    fields=cli(['+field-list',*args],'rights-schema-before')['data']['fields']
    assert set(rows[0])<={f['name'] for f in fields}
    if '关联作品' not in {f['name'] for f in fields}:
        cmd=['+field-create',*args,'--json',json.dumps({'name':'关联作品','type':'link','link_table':cfg['tables']['作品目录']},ensure_ascii=False)]
        cli(cmd+['--dry-run'],'rights-link-preview');cli(cmd,'rights-link-create')
    fields=cli(['+field-list',*args],'rights-schema-after')['data']['fields']
    assert set(rows[0])|{'关联作品'}<={f['name'] for f in fields}
    (ROOT/'receipts/rights-table-schema-validation.json').write_text(json.dumps({'schema_readback':True,'relation_schema_verified':True,'rows_to_sync':len(rows),'data_sync_complete':False},indent=2),encoding='utf-8')
    print('Rights schema verified; separate incremental sync and full readback required')

if __name__=='__main__':main()
