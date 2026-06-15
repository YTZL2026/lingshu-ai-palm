# -*- coding: utf-8 -*-
"""
AI掌纹溯源 — 多模态融合报告引擎
掌纹为核心，融合八字五行、梦境意象、黄历宜忌、周易卦象、情志关怀

每个维度都关联回掌纹发现，不再各自独立。
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

from .constitution_engine import ConstitutionResult, CONSTITUTION_TYPES, derive_zhouyi
from .almanac import get_almanac
from .fortune import interpret_dream, calculate_bazi

# TCM 五行情志映射（《素问·阴阳应象大论》）
FIVE_EMOTIONS = {
    '心': {'emotion':'喜','excess':'过喜伤心，神气涣散','deficiency':'心气不足，易惊善忘','advice':'心主神明。听舒缓音乐、闭目养神、避免过度兴奋。'},
    '肝': {'emotion':'怒','excess':'怒则气上，肝阳上亢','deficiency':'肝气不足，郁郁不舒','advice':'肝主疏泄。适当运动排解、拍打两胁、玫瑰花茶疏肝。'},
    '脾': {'emotion':'思','excess':'思则气结，脾失健运','deficiency':'脾气不足，思虑伤脾','advice':'脾主运化。规律饮食、少思少虑、饭后散步助消化。'},
    '肺': {'emotion':'悲','excess':'悲则气消，肺气耗散','deficiency':'肺气不足，易感外邪','advice':'肺主气。深呼吸练习、笑口常开、白色食物润肺。'},
    '肾': {'emotion':'恐','excess':'恐则气下，肾气不固','deficiency':'肾气不足，腰膝酸软','advice':'肾藏精。早睡养肾、温水泡脚、黑色食物补肾。'},
}

# 体质→五行倾向
CONSTITUTION_WUXING = {
    'balanced':       {'dominant':'土','secondary':'金','note':'五行均衡，中和为贵'},
    'qi_deficient':   {'dominant':'土','secondary':'金','note':'土生金，补脾肺之气'},
    'yang_deficient': {'dominant':'水','secondary':'火','note':'水中求火，温补肾阳'},
    'yin_deficient':  {'dominant':'火','secondary':'水','note':'火中补水，滋阴降火'},
    'phlegm_damp':    {'dominant':'土','secondary':'水','note':'土克水，健脾利湿'},
    'damp_heat':      {'dominant':'火','secondary':'土','note':'火生土，清热化湿'},
    'blood_stasis':   {'dominant':'火','secondary':'木','note':'火木相生，活血化瘀'},
    'qi_stagnation':  {'dominant':'木','secondary':'火','note':'木生火，疏肝理气'},
    'allergic':       {'dominant':'金','secondary':'土','note':'土生金，固表御邪'},
}

@dataclass
class IntegratedReport:
    # 掌纹核心结果
    constitution: dict
    zhouyi: dict
    organ_scores: dict
    body_age: float
    chronological_age: float
    age_diff: float

    # 八字关联（可选）
    bazi_connection: Optional[str] = None

    # 梦境关联（可选）
    dream_connection: Optional[str] = None

    # 黄历关联
    almanac_connection: str = ''

    # 情志关怀
    emotional_care: List[dict] = field(default_factory=list)

    # 综合五行分析
    wuxing_synthesis: str = ''

    # 一句话总结
    one_liner: str = ''


def generate_report(
    constitution: ConstitutionResult,
    dream_text: str = '',
    bazi_year: int = None,
    bazi_month: int = None,
    bazi_day: int = None,
    bazi_hour: int = None,
) -> IntegratedReport:
    """
    生成多模态融合报告

    所有维度围绕掌纹体质展开互相关联：
    - 八字五行与掌纹体质五行对比
    - 梦境脏腑关联与掌纹弱势器官印证
    - 黄历宜忌结合体质建议
    - 情志关怀基于最弱脏腑
    """

    cid = constitution.constitution_id
    ct = CONSTITUTION_TYPES.get(cid, CONSTITUTION_TYPES['balanced'])

    # ===== 基础掌纹数据 =====
    palm_wuxing = CONSTITUTION_WUXING.get(cid, CONSTITUTION_WUXING['balanced'])

    # ===== 1. 八字五行关联 =====
    bazi_conn = None
    bazi_wuxing_dominant = None
    if bazi_year and bazi_month and bazi_day:
        try:
            bazi = calculate_bazi(bazi_year, bazi_month, bazi_day, bazi_hour or 12)
            bazi_wuxing_dominant = bazi.dominant_wuxing

            # 五行生克关系
            sheng = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
            ke   = {'木':'土','土':'水','水':'火','火':'金','金':'木'}

            p_dom = palm_wuxing['dominant']
            b_dom = bazi_wuxing_dominant

            if p_dom == b_dom:
                relation = '掌纹五行与八字五行同属，内外相应'
            elif sheng.get(b_dom) == p_dom:
                relation = f'八字{b_dom}生掌纹{p_dom}——先天禀赋滋养后天体质，顺势而为'
            elif sheng.get(p_dom) == b_dom:
                relation = f'掌纹{p_dom}生八字{b_dom}——后天调养可改善先天不足'
            elif ke.get(b_dom) == p_dom:
                relation = f'八字{b_dom}克掌纹{p_dom}——需注意后天调养以平衡先天制约'
            elif ke.get(p_dom) == b_dom:
                relation = f'掌纹{p_dom}克八字{b_dom}——体质有克服先天弱势的潜力'
            else:
                relation = f'掌纹{p_dom}与八字{b_dom}，五行互动中求平衡'

            bazi_conn = (
                f'你的八字主导五行为「{b_dom}」（日主{bazi.day_gan}{bazi.day_zhi}），'
                f'掌纹体质倾向「{p_dom}」。{relation}。\n'
                f'建议：日常养生中以{p_dom}行食物和运动为主，兼顾{b_dom}行的补益。'
            )
        except:
            pass

    # ===== 2. 梦境关联 =====
    dream_conn = None
    if dream_text and dream_text.strip():
        dream = interpret_dream(dream_text)
        if dream.matched_keywords:
            dream_organ = dream.dominant_organ
            weak_organs = sorted(constitution.organ_scores, key=constitution.organ_scores.get)[:2]

            if dream_organ != '—':
                if dream_organ in weak_organs:
                    dream_conn = (
                        f'你描述的梦境中，「{dream.matched_keywords[0]["keyword"]}」意象突出，'
                        f'梦境五行倾向「{dream.dominant_element}」，关联脏腑「{dream_organ}」。\n'
                        f'值得注意的是——你的掌纹分析也显示{dream_organ}经功能评分偏低（{constitution.organ_scores.get(dream_organ, "?")}分），'
                        f'梦境与掌纹相互印证，建议重点关注{dream_organ}经调养。\n'
                        f'《灵枢·淫邪发梦》云："{dream_organ}气盛则梦{dream.matched_keywords[0]["keyword"]}"，'
                        f'你的梦境正反映了{dream_organ}经的状态。'
                    )
                else:
                    dream_conn = (
                        f'你描述的梦境五行倾向「{dream.dominant_element}」，关联「{dream_organ}」经。\n'
                        f'掌纹分析显示你的{dream_organ}经功能评分{constitution.organ_scores.get(dream_organ, "?")}分——'
                        f'梦境可能在提示你关注{dream_organ}方面的调养，即使掌纹还未明显反映出来。'
                    )

    # ===== 3. 黄历关联 =====
    almanac = get_almanac()
    al_yi = almanac.yi[:3] if almanac.yi else []
    al_ji = almanac.ji[:3] if almanac.ji else []
    watch_organs = ct.get('watch_organs', [])

    almanac_parts = [
        f'今日{almanac.lunar_date}，建除「{almanac.jianchu}」，{almanac.xiu28}宿值日。',
        f'黄历宜：{"、".join(al_yi) if al_yi else "诸事平稳"}。',
    ]
    if al_ji:
        almanac_parts.append(f'忌：{"、".join(al_ji)}。')

    # 结合体质给今日建议
    if watch_organs:
        almanac_parts.append(
            f'结合你的掌纹体质（{ct["name"]}，需关注{"、".join(watch_organs)}），'
            f'今日宜选择温和的调理方式，避免过度消耗{watch_organs[0]}经。'
        )

    almanac_conn = '\n'.join(almanac_parts)

    # ===== 4. 情志关怀 =====
    emotional_care = []
    sorted_organs = sorted(constitution.organ_scores, key=constitution.organ_scores.get)
    # 最弱的两个脏腑
    for organ in sorted_organs[:2]:
        score = constitution.organ_scores[organ]
        if score < 65:
            emo = FIVE_EMOTIONS.get(organ)
            if emo:
                emotional_care.append({
                    'organ': organ,
                    'score': score,
                    'emotion': emo['emotion'],
                    'concern': emo['excess'] if score < 55 else emo['deficiency'],
                    'advice': emo['advice'],
                })

    # ===== 5. 综合五行分析 =====
    zhouyi_data = constitution.zhouyi if hasattr(constitution, 'zhouyi') and constitution.zhouyi else derive_zhouyi(cid)

    parts = [
        f'你的掌纹体质为「{ct["name"]}」——五行属{palm_wuxing["dominant"]}为主，{palm_wuxing["note"]}。'
    ]
    if zhouyi_data:
        parts.append(
            f'对应周易{palm_wuxing["dominant"]}行，主卦为「{zhouyi_data.get("primary_bagua","")}卦」'
            f'（{zhouyi_data.get("trigram","")}），卦德为"{zhouyi_data.get("virtue","")}"。'
        )
    if bazi_wuxing_dominant:
        parts.append(
            f'八字五行以「{bazi_wuxing_dominant}」为主，与掌纹「{palm_wuxing["dominant"]}」'
            f'形成{palm_wuxing["dominant"]}_{bazi_wuxing_dominant}互动格局。'
        )
    parts.append(f'今日黄历建除「{almanac.jianchu}」，宜结合体质安排活动。')

    wuxing_synthesis = '\n'.join(parts)

    # ===== 6. 一句话总结 =====
    one_liner = (
        f'{ct["mythic_name"]}（{ct["name"]}）· '
        f'五行属{palm_wuxing["dominant"]} · '
        f'身体年龄{constitution.body_age}岁'
    )
    if bazi_wuxing_dominant:
        one_liner += f' · 八字{bazi_wuxing_dominant}命'
    if dream_conn:
        one_liner += f' · 梦境印证'

    return IntegratedReport(
        constitution={
            'id': cid, 'name': ct['name'], 'mythic_name': ct['mythic_name'],
            'icon': ct['icon'], 'color': ct['color'],
            'confidence': constitution.confidence,
            'description': ct['description'],
            'traits': ct['traits'],
        },
        zhouyi=zhouyi_data,
        organ_scores=constitution.organ_scores,
        body_age=constitution.body_age,
        chronological_age=constitution.chronological_age,
        age_diff=constitution.age_diff,
        bazi_connection=bazi_conn,
        dream_connection=dream_conn,
        almanac_connection=almanac_conn,
        emotional_care=emotional_care,
        wuxing_synthesis=wuxing_synthesis,
        one_liner=one_liner,
    )
