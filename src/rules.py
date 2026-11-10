from datetime import date
def in_window(day):
 return day is not None and date(2024,1,1)<=date.fromisoformat(day)<=date(2026,11,10)
def comparable(a,b):
 keys=('object','metric','unit','currency','temporal_type','period_start','period_end','version')
 return all(a.get(k)==b.get(k) for k in keys) and a.get('temporal_type')!='未知' and a.get('version') is not None
def distinct_projects(rows):return len({r.get('parent_id') or r['id'] for r in rows})
def merchandise_amount(amount,bundled,allocated=None):return allocated if bundled else amount
