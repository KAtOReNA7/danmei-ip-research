"""Rights sale timing and type classification; launch dates never substitute."""
import calendar,re
from datetime import date,timedelta

def license_disclosure_window(announcement_day,*,acquired,window_start='2024-01-01'):
    """Explicit acquisition proves prior existence, never an exact signing date."""
    announced=date.fromisoformat(announcement_day)
    upper=announced+timedelta(days=1)  # Source timezone unspecified: calendar margin.
    return {'announcement_time':announcement_day,'contract_time_raw':None,
            'contract_start':None,'contract_end':None,
            'time_precision':'签署日未知；已获授权公告提供存在时间上界，来源时区未明',
            'window_role':'窗口前已获授权披露' if acquired and upper<date.fromisoformat(window_start) else '签约时间待核',
            'disclosure_upper_date_with_timezone_margin':upper.isoformat() if acquired else None}

def sale_window(raw,cutoff='2026-11-10'):
    raw=(raw or '').strip()
    if re.fullmatch(r'\d{4}',raw):
        year=int(raw);start=date(year,1,1);end=date(year,12,31);precision='年；按北京时间保守区间，来源未标时区'
    elif re.fullmatch(r'\d{4}-\d{2}',raw):
        year,month=map(int,raw.split('-'));start=date(year,month,1);end=date(year,month,calendar.monthrange(year,month)[1]);precision='月；按北京时间保守区间，来源未标时区'
    else:
        return {'start':None,'end':None,'precision':'未知','window_role':'签约时间待核'}
    role=('窗口内签约年份' if len(raw)==4 else '窗口内签约月份') if start>=date(2024,1,1) and end<=date.fromisoformat(cutoff) else '窗口前背景' if end<date(2024,1,1) else '窗口后' if start>date.fromisoformat(cutoff) else '跨截止日待核'
    return {'start':start.isoformat()+'T00:00:00+08:00','end':end.isoformat()+'T23:59:59+08:00','precision':precision,'window_role':role}

def rights_media(raw):
    if '线下活动' in raw or '主题店' in raw or '舞台剧' in raw:return '舞台线下'
    if any(s in raw for s in ('周边','衍生品','联名','手机主题')):return '官方周边联名'
    if any(s in raw for s in ('游戏','手游','端游')):return '游戏'
    if '广播剧' in raw:return '广播剧'
    if raw in ('有声','有声读物'):return '有声书'
    if '漫画' in raw:return '漫画'
    if '动画' in raw:return '动画'
    if any(s in raw for s in ('影视','电视剧','网络剧','电影','短剧','短视频')):return '影视短剧'
    return None
