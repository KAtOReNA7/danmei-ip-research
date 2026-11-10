from research import *
for f in sorted((ROOT/'evidence/search').glob('*.json')):
    d=json.loads(f.read_text(encoding='utf-8')); blocks=re.split(r'-{10,}',d['response'])
    print(d['source_id'],d['title'],d['group'])
    print('\n'.join(b.strip().split('\n')[0][:200] for b in blocks[:4]))
