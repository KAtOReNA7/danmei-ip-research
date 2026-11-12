"""Persist manually reviewed official work-page rights labels as dated-unknown disclosures.

Never create products, infer contracts, promote eligibility, or infer a cutoff state.
Generic publication labels do not establish an ebook license; ambiguous media labels stay raw.
"""
from research import *
from rights_rules import rights_media


def ingest_labels(c,reviewed_files):
    report={'reviewed_files':len(reviewed_files),'works_with_nonpublication_labels':0,
            'source_label_rows':0,'new_source_label_rows':0,'ambiguous_media_rows':0,'unmapped_media_rows':0,
            'coverage_confirmations':0,'preserved_existing_confirmations':0,
            'products_created':0,'events_created':0,'new_window_sale_proofs':0}
    first_evidence=None
    for path in reviewed_files:
        q=json.loads((ROOT/path).read_text(encoding='utf-8'))
        w=c.execute("select * from works where platform='晋江' and source_id=?",(q['source_id'],)).fetchone()
        assert w and jj_identity(q['page_title'],q['author_links'])==(w['title'],w['author'])
        labels=list(dict.fromkeys(label.strip() for hint in q.get('rights_hints',[]) for label in hint.get('labels',[])
                                  if label.strip().endswith('签约') and ('出版' not in label
                                      or any(word in label for word in ('电子书','电子出版','数字出版')))))
        if not labels:continue
        eid=evidence(c,q['url'],q['page_title'],q,'晋江文学城',
            status='官方当前作品页签约标签；发生时间及截止前状态待核',
            method='同ID身份/作品签约/版权转化标签必要元数据；无正文、实时表现或日期推定',accessed=q['captured_at'])
        first_evidence=first_evidence or eid
        report['works_with_nonpublication_labels']+=1
        by_media={}
        base_gap='当前官方标记不证明截止日前已存在；实际签署日、项目/季/版本、主体、地域/语言、金额、期限及续约/追加关系未知。可能与成功签约清单或其他公告为同一合同，不计独立交易或窗口内新售。'
        for label in labels:
            raw=label.removesuffix('签约')
            media='电子书' if '电子书' in raw else rights_media(raw)  # 动漫 / generic digital publishing stay unresolved.
            rid=key('rights','jj-work-tag',w['id'],label)
            exists=c.execute('select 1 from rights_records where id=?',(rid,)).fetchone()
            gap=base_gap
            if media is None:
                gap+=(' 动漫标签含义未明，不自动归动画或漫画。' if '动漫' in raw
                      else ' 该标签尚无现有九类媒介映射，保留原文另核，不强归其他类型。')
            upsert(c,'rights_records',dict(id=rid,work_id=w['id'],rights_type_raw=label,media=media,
                contract_time_raw=None,contract_start=None,contract_end=None,
                time_precision='未知；当前作品页标签，未证截止前已存在',announcement_time=None,
                window_role='签约时间待核',sale_status='官方作品页明确签约标签；非上线或可售推荐',
                source_url=q['url'],source_locator='版权转化图片文字标签：'+label,evidence_id=eid,gap=gap))
            report['source_label_rows']+=1;report['new_source_label_rows']+=int(not exists)
            if media is None:
                report['unmapped_media_rows']+=1
                report['ambiguous_media_rows']+=int('动漫' in raw)
            else:by_media.setdefault(media,[]).append(label)
        for media,media_labels in by_media.items():
            gap=base_gap
            scope='官方作品页版权转化标签：'+'、'.join(media_labels)
            prior=c.execute('select status from coverage where work_id=? and media=?',(w['id'],media)).fetchone()
            assert prior
            if prior['status']=='已确认':
                upsert(c,'check_history',dict(id=key('check',w['id'],media,scope,eid),work_id=w['id'],media=media,
                    status='已确认',query_scope=scope,evidence_id=eid,checked_at=q['captured_at'],gap=gap))
                report['preserved_existing_confirmations']+=1
            else:
                checked(c,w['id'],media,'已确认',scope,eid,gap)
                report['coverage_confirmations']+=1
    if first_evidence:
        upsert(c,'source_matrix',dict(id=key('source','jj-work-rights-labels'),media='多媒介',
            source_name='晋江官方作品页版权转化签约标签',url='https://www.jjwxc.net/onebook.php',
            events_available='当前官方签约标签；无事件日，不生成官宣/签署事件',
            current_values='同ID身份、作品级签约、版权标签；不采实时表现',
            historical_values='截止日前状态及发生时间须对应历史官方来源另证',access_condition='公开HTTP必要元数据',
            test_result=f"本批实际审阅{report['reviewed_files']}页，{report['works_with_nonpublication_labels']}作有非出版签约标签，{report['source_label_rows']}标签；{report['unmapped_media_rows']}标签未映射，动漫歧义保留、独立音乐等不强归其他类",
            evidence_id=first_evidence,next_action='逐标签追成功签约页及官方项目的签署发生期/主体/范围；出版不推电子，不与清单自动并为同合同'))
    return report
