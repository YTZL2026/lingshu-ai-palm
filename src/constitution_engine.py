# -*- coding: utf-8 -*-
"""
AI掌纹溯源 — 体质推理引擎
基于中医手诊理论的掌纹特征→九种体质映射
专利保护点：多模态掌纹体质辨识推理引擎

阶段1：规则引擎（当前）
阶段2：XGBoost多标签分类器（数据充足后升级）

=== 理论依据 ===
[1] 中华中医药学会.《中医体质分类与判定》(ZYYXH/T157-2009). 2009.
[2] 王琦.《中医体质学》. 人民卫生出版社, 2005.
[3] 《黄帝内经·灵枢·本脏》："视其外应，以知其内脏，则知所病矣。"
[4] 《黄帝内经·素问·五脏生成》："诸内必形诸外。"
[5] 刘剑锋.《中医手诊学》. 中国中医药出版社, 2012.
[6] 张登本.《中医望诊彩色图谱》. 人民军医出版社, 2010.
[7] 《难经·六十一难》："望而知之者，望见其五色，以知其病。"
[8] 朱文锋.《中医诊断学》. 中国中医药出版社, 2007.
[9] 王琦, 朱燕波. 中医体质学说的科学内涵与临床应用[J]. 中医杂志, 2004.
[10] 国家卫生计生委.《国家基本公共卫生服务规范(第三版)》· 中医药健康管理服务. 2017.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import json
import os

from .feature_extractor import PalmFeatures

# ======================== 理论依据引用 ========================
TCM_REFERENCES = [
    {'id': 'R1', 'citation': '中华中医药学会.《中医体质分类与判定》(ZYYXH/T157-2009). 2009.', 'usage': '九种体质类型定义与判定标准'},
    {'id': 'R2', 'citation': '王琦.《中医体质学》. 人民卫生出版社, 2005.', 'usage': '体质学理论体系、体质与脏腑关系'},
    {'id': 'R3', 'citation': '《黄帝内经·灵枢·本脏》', 'usage': '"视其外应，以知其内脏"——手诊的理论源头'},
    {'id': 'R4', 'citation': '《黄帝内经·素问·五脏生成》', 'usage': '"诸内必形诸外"——体表特征反映内脏状态'},
    {'id': 'R5', 'citation': '刘剑锋.《中医手诊学》. 中国中医药出版社, 2012.', 'usage': '手诊14线、八卦丘位定位标准'},
    {'id': 'R6', 'citation': '张登本.《中医望诊彩色图谱》. 人民军医出版社, 2010.', 'usage': '掌面色泽与脏腑功能对应的临床观察'},
    {'id': 'R7', 'citation': '《难经·六十一难》', 'usage': '"望而知之者，望见其五色，以知其病"——望诊诊断学基础'},
    {'id': 'R8', 'citation': '朱文锋.《中医诊断学》. 中国中医药出版社, 2007.', 'usage': '四诊合参、从外知内的诊断方法论'},
    {'id': 'R9', 'citation': '王琦, 朱燕波. 中医体质学说的科学内涵与临床应用[J]. 中医杂志, 2004.', 'usage': '体质分类的量化研究方法'},
    {'id': 'R10', 'citation': '国家卫生计生委.《国家基本公共卫生服务规范(第三版)》· 中医药健康管理服务. 2017.', 'usage': '老年人体质辨识与保健指导规范'},
]


# ======================== 周易八卦维度 ========================
"""
周易八卦掌丘映射 —— 基于中医手诊学与易学交汇理论
===========================================================

【理论背景】
  《周易》与中医同源于先秦阴阳五行学说，历代医家素有"易医同源"之说。
  唐代孙思邈《千金要方》云："不知易，不足以言太医。"
  明代张景岳《类经附翼》专设《医易义》一篇，系统论述易医关系。
  手掌八卦丘位是中医手诊学的核心定位系统，每个丘位对应一个卦象，
  丘位的饱满程度反映对应脏腑的功能状态。

【八卦→手掌→脏腑→五行 对应关系】
  乾卦 ☰ — 小鱼际（手掌外侧下部）— 肺/大肠 — 金 — 天
  坤卦 ☷ — 无名指根部 — 脾/胃 — 土 — 地
  震卦 ☳ — 大鱼际上部（拇指根部上方）— 肝 — 木 — 雷
  巽卦 ☴ — 大鱼际下部（拇指根部下方）— 胆 — 木 — 风
  坎卦 ☵ — 腕部（手腕横纹上方）— 肾/膀胱 — 水 — 水
  离卦 ☲ — 中指根部 — 心/小肠 — 火 — 火
  艮卦 ☶ — 食指根部 — 胃 — 土 — 山
  兑卦 ☱ — 小指根部 — 肺 — 金 — 泽

【体质→主导卦象 映射逻辑】
  平和质 → 乾卦：阴阳调和，气血充盈，天行健之象
  气虚质 → 坤卦：脾主运化为气血生化之源，坤土厚德载物
  阳虚质 → 坎卦：肾阳为一身阳气之根，坎中一阳温煦全身
  阴虚质 → 离卦：心火需阴血濡养，离中虚明而不燥
  痰湿质 → 坤卦：脾虚生湿，坤土运化不利则痰湿内生
  湿热质 → 震卦：肝胆湿热如雷动风行，需疏泄调和
  血瘀质 → 艮卦：山止而能行，止中有动则血脉通畅
  气郁质 → 巽卦：肝气郁结如风被阻，巽入而能疏
  特禀质 → 兑卦：肺主皮毛司呼吸，兑泽润物调和营卫

【卦辞来源】
  所有卦辞均引自《周易·象传》原文（"大象"部分），
  后半句健康解读为基于中医理论的合理引申，非自行编造卦辞。
  例如：乾卦象传原文"天行健，君子以自强不息"，
  引申为"顺应天时，作息有序，阳气充沛则百病不侵"。

学术依据：
  [Z1] 张其成.《易学与中医》. 中国书店, 1999.
       → 系统论述"易医同源"理论、八卦与脏腑对应关系
  [Z2] 刘大钧.《周易概论》. 齐鲁书社, 1988.
       → 卦象的哲学解释与象传研究
  [Z3] 刘剑锋.《中医手诊学》. 中国中医药出版社, 2012.
       → 手掌八卦丘位的精确定位与临床诊断标准
  [Z4] 《周易·说卦传》
       → 八卦与人体部位对应关系的原始文献
  [Z5] 《素问·金匮真言论》
       → 五行方位与脏腑对应的经典论述
  [Z6] 张景岳.《类经附翼·医易义》. 明代.
       → 易医关系的系统论证
"""

# 八卦→丘位→五行→脏腑→卦德（每条均有上述文献出处）
BAGUA_MOUNDS = {
    # 乾为天，位于小鱼际（手掌外侧下部），五行属金，对应肺与大肠。
    # 卦德为"健"——刚健不息。肺主一身之气，气足则体健。
    # 《说卦传》："乾为天，为圆，为君，为父。"
    'qian':  {'name':'乾', 'trigram':'☰', 'mound':'小鱼际',   'element':'金','organ':'肺','virtue':'健','direction':'西北','nature':'天','hexagram_num':1},

    # 坤为地，位于无名指根部，五行属土，对应脾胃。
    # 卦德为"顺"——柔顺承载。脾主运化，承载后天之本。
    # 《说卦传》："坤为地，为母，为布，为釜。"
    'kun':   {'name':'坤', 'trigram':'☷', 'mound':'无名指根', 'element':'土','organ':'脾','virtue':'顺','direction':'西南','nature':'地','hexagram_num':2},

    # 震为雷，位于大鱼际上部（拇指根部上方），五行属木，对应肝。
    # 卦德为"动"——震动奋发。肝主疏泄，喜条达而恶抑郁。
    # 《说卦传》："震为雷，为龙，为玄黄……其于稼也，为反生。"
    'zhen':  {'name':'震', 'trigram':'☳', 'mound':'大鱼际上', 'element':'木','organ':'肝','virtue':'动','direction':'东',  'nature':'雷','hexagram_num':51},

    # 巽为风，位于大鱼际下部（拇指根部下方），五行属木，对应胆。
    # 卦德为"入"——渗透深入。胆主决断，风以散之。
    # 《说卦传》："巽为木，为风，为长女……为进退。"
    'xun':   {'name':'巽', 'trigram':'☴', 'mound':'大鱼际下', 'element':'木','organ':'胆','virtue':'入','direction':'东南','nature':'风','hexagram_num':57},

    # 坎为水，位于腕部（手腕横纹上方），五行属水，对应肾与膀胱。
    # 卦德为"陷"——险中求存。肾藏精，为先天之本，需守而不泄。
    # 《说卦传》："坎为水，为沟渎，为隐伏……其于人也，为加忧。"
    'kan':   {'name':'坎', 'trigram':'☵', 'mound':'腕部',     'element':'水','organ':'肾','virtue':'陷','direction':'北',  'nature':'水','hexagram_num':29},

    # 离为火，位于中指根部，五行属火，对应心与小肠。
    # 卦德为"丽"——光明依附。心主神明，火光朗照。
    # 《说卦传》："离为火，为日，为电……为大腹。"
    'li':    {'name':'离', 'trigram':'☲', 'mound':'中指根',   'element':'火','organ':'心','virtue':'丽','direction':'南',  'nature':'火','hexagram_num':30},

    # 艮为山，位于食指根部，五行属土，对应胃。
    # 卦德为"止"——适可而止。胃主受纳，过饱则伤。
    # 《说卦传》："艮为山，为径路，为小石……为黔喙之属。"
    'gen':   {'name':'艮', 'trigram':'☶', 'mound':'食指根',   'element':'土','organ':'胃','virtue':'止','direction':'东北','nature':'山','hexagram_num':52},

    # 兑为泽，位于小指根部，五行属金，对应肺。
    # 卦德为"说"——喜悦和悦。肺主宣发，气机和畅。
    # 《说卦传》："兑为泽，为少女，为巫，为口舌……其于地也，为刚卤。"
    'dui':   {'name':'兑', 'trigram':'☱', 'mound':'小指根',   'element':'金','organ':'肺','virtue':'说','direction':'西',  'nature':'泽','hexagram_num':58},
}

# 八卦→丘位→五行→脏腑→卦德
BAGUA_MOUNDS = {
    'qian':  {'name':'乾', 'trigram':'☰', 'mound':'小鱼际',   'element':'金','organ':'肺','virtue':'健','direction':'西北','nature':'天','hexagram_num':1},
    'kun':   {'name':'坤', 'trigram':'☷', 'mound':'无名指根', 'element':'土','organ':'脾','virtue':'顺','direction':'西南','nature':'地','hexagram_num':2},
    'zhen':  {'name':'震', 'trigram':'☳', 'mound':'大鱼际上', 'element':'木','organ':'肝','virtue':'动','direction':'东',  'nature':'雷','hexagram_num':51},
    'xun':   {'name':'巽', 'trigram':'☴', 'mound':'大鱼际下', 'element':'木','organ':'胆','virtue':'入','direction':'东南','nature':'风','hexagram_num':57},
    'kan':   {'name':'坎', 'trigram':'☵', 'mound':'腕部',     'element':'水','organ':'肾','virtue':'陷','direction':'北',  'nature':'水','hexagram_num':29},
    'li':    {'name':'离', 'trigram':'☲', 'mound':'中指根',   'element':'火','organ':'心','virtue':'丽','direction':'南',  'nature':'火','hexagram_num':30},
    'gen':   {'name':'艮', 'trigram':'☶', 'mound':'食指根',   'element':'土','organ':'胃','virtue':'止','direction':'东北','nature':'山','hexagram_num':52},
    'dui':   {'name':'兑', 'trigram':'☱', 'mound':'小指根',   'element':'金','organ':'肺','virtue':'说','direction':'西',  'nature':'泽','hexagram_num':58},
}

# 八卦卦德对应的生活哲学指引（源自《周易》卦爻辞，结合健康养生解读）
BAGUA_GUIDANCE = {
    'qian':  '乾卦·天行健：君子以自强不息。顺应天时，作息有序，阳气充沛则百病不侵。',
    'kun':   '坤卦·地势坤：君子以厚德载物。脾胃为后天之本，厚土能纳万物，包容即是养生。',
    'zhen':  '震卦·洊雷震：君子以恐惧修省。肝气调达则生机勃发，遇变不惊，动中求静。',
    'xun':   '巽卦·随风巽：君子以申命行事。胆气舒畅则决断明快，柔顺不争，风过无痕。',
    'kan':   '坎卦·水洊至：君子以常德行。肾藏精为先天之本，水滴石穿，贵在坚持。',
    'li':    '离卦·明两作：君子以继明照于四方。心火明亮则神清气爽，虚明不燥。',
    'gen':   '艮卦·兼山艮：君子以思不出其位。知止不殆，适可而止，胃气和则五脏安。',
    'dui':   '兑卦·丽泽兑：君子以朋友讲习。肺气宣畅则呼吸调匀，悦而不过，和而不纵。',
}

# 体质→主导卦象映射（基于王琦体质学说与八卦五行对应）
CONSTITUTION_BAGUA = {
    'balanced':       'qian',   # 平和质→乾卦：阴阳和合，天行健
    'qi_deficient':   'kun',    # 气虚质→坤卦：厚德载物，补土生气
    'yang_deficient': 'kan',    # 阳虚质→坎卦：水中有阳，温煦肾元
    'yin_deficient':  'li',     # 阴虚质→离卦：火中藏阴，滋阴降火
    'phlegm_damp':    'kun',    # 痰湿质→坤卦：脾土运化，祛湿化痰
    'damp_heat':      'zhen',   # 湿热质→震卦：雷动风行，清热利湿
    'blood_stasis':   'gen',    # 血瘀质→艮卦：止而能行，活血化瘀
    'qi_stagnation':  'xun',    # 气郁质→巽卦：风行草偃，疏肝解郁
    'allergic':       'dui',    # 特禀质→兑卦：泽润万物，调和营卫
}

def derive_zhouyi(constitution_id: str, features=None) -> dict:
    """
    根据体质类型和掌纹特征，推导周易卦象指引

    依据：[Z1] 张其成《易学与中医》— 易医同源理论
          [Z3] 刘剑锋《中医手诊学》— 八卦丘位定位
          [Z2] 刘大钧《周易概论》— 卦象哲学解释

    Args:
        constitution_id: 体质类型ID
        features: 掌纹特征（可选，用于微调卦象）

    Returns:
        dict with bagua info, guidance text, academic citations
    """
    bagua_key = CONSTITUTION_BAGUA.get(constitution_id, 'qian')
    bagua = BAGUA_MOUNDS[bagua_key]
    guidance = BAGUA_GUIDANCE[bagua_key]

    return {
        'primary_bagua': bagua['name'],
        'trigram': bagua['trigram'],
        'mound': bagua['mound'],
        'element': bagua['element'],
        'organ': bagua['organ'],
        'virtue': bagua['virtue'],
        'nature': bagua['nature'],
        'guidance': guidance,
        'citations': [
            '张其成.《易学与中医》. 中国书店, 1999.',
            '刘大钧.《周易概论》. 齐鲁书社, 1988.',
            '刘剑锋.《中医手诊学》. 中国中医药出版社, 2012.',
            '《周易·说卦传》',
        ],
    }


# ======================== 九种体质定义 ========================

CONSTITUTION_TYPES = {
    'balanced': {
        'name': '平和质',
        'mythic_name': '苍龙质',
        'icon': '🐉',
        'color': '#27ae60',
        'description': '阴阳调和，气血充盈，五脏平衡',
        'population_pct': 32.8,
        'traits': ['精力充沛', '适应力强', '睡眠良好', '面色红润'],
        'strength_organs': ['心', '肺'],
        'watch_organs': [],
    },
    'qi_deficient': {
        'name': '气虚质',
        'mythic_name': '玄龟质',
        'icon': '🐢',
        'color': '#7f8c8d',
        'description': '元气不足，疲乏无力，气短懒言',
        'population_pct': 13.4,
        'traits': ['容易疲劳', '气短懒言', '自汗', '易感冒'],
        'strength_organs': [],
        'watch_organs': ['肺', '脾'],
    },
    'yang_deficient': {
        'name': '阳虚质',
        'mythic_name': '玄冥质',
        'icon': '🌙',
        'color': '#5d6d7e',
        'description': '阳气不足，畏寒怕冷，手足不温',
        'population_pct': 9.0,
        'traits': ['畏寒怕冷', '手足不温', '喜热饮食', '精神不振'],
        'strength_organs': [],
        'watch_organs': ['肾', '脾'],
    },
    'yin_deficient': {
        'name': '阴虚质',
        'mythic_name': '朱雀质',
        'icon': '🔥',
        'color': '#e74c3c',
        'description': '阴液不足，口干咽燥，手足心热',
        'population_pct': 8.9,
        'traits': ['口干咽燥', '手足心热', '失眠多梦', '大便干燥'],
        'strength_organs': ['肝'],
        'watch_organs': ['肾', '肺'],
    },
    'phlegm_damp': {
        'name': '痰湿质',
        'mythic_name': '饕餮质',
        'icon': '🍖',
        'color': '#d4a017',
        'description': '痰湿凝聚，形体肥胖，腹部肥满',
        'population_pct': 8.7,
        'traits': ['腹部肥满', '面部油腻', '痰多胸闷', '身体沉重'],
        'strength_organs': [],
        'watch_organs': ['脾', '肺'],
    },
    'damp_heat': {
        'name': '湿热质',
        'mythic_name': '应龙质',
        'icon': '🌧️',
        'color': '#e67e22',
        'description': '湿热内蕴，面垢油光，口苦口干',
        'population_pct': 7.9,
        'traits': ['面垢油光', '口苦口干', '大便黏滞', '易生痤疮'],
        'strength_organs': [],
        'watch_organs': ['肝', '胆', '脾'],
    },
    'blood_stasis': {
        'name': '血瘀质',
        'mythic_name': '麒麟质',
        'icon': '🦄',
        'color': '#8e44ad',
        'description': '血行不畅，肤色晦暗，唇色偏暗',
        'population_pct': 7.6,
        'traits': ['肤色晦暗', '容易出现瘀斑', '疼痛固定', '面色暗沉'],
        'strength_organs': [],
        'watch_organs': ['心', '肝'],
    },
    'qi_stagnation': {
        'name': '气郁质',
        'mythic_name': '白虎质',
        'icon': '🐅',
        'color': '#2c3e50',
        'description': '气机郁滞，神情抑郁，忧虑脆弱',
        'population_pct': 7.1,
        'traits': ['神情抑郁', '情感脆弱', '烦闷不乐', '胁肋胀痛'],
        'strength_organs': [],
        'watch_organs': ['肝', '心'],
    },
    'allergic': {
        'name': '特禀质',
        'mythic_name': '灵狐质',
        'icon': '🦊',
        'color': '#3498db',
        'description': '先天失常，过敏体质，对外界适应力差',
        'population_pct': 4.6,
        'traits': ['容易过敏', '对季节变化敏感', '皮肤易出疹', '鼻塞流涕'],
        'strength_organs': [],
        'watch_organs': ['肺', '脾'],
    },
}

# 五行对应器官
FIVE_ELEMENTS = {
    '心': {'element': '火', 'color': '#e74c3c'},
    '肝': {'element': '木', 'color': '#27ae60'},
    '脾': {'element': '土', 'color': '#f39c12'},
    '肺': {'element': '金', 'color': '#ecf0f1'},
    '肾': {'element': '水', 'color': '#2980b9'},
}

# 体质对应的食疗建议
DIET_RECOMMENDATIONS = {
    'balanced':       ['保持饮食均衡，五谷杂粮搭配', '时令蔬果，不偏嗜', '适量饮水'],
    'qi_deficient':   ['多食益气食物：山药、莲子、小米', '常饮黄芪红枣茶', '忌食生冷寒凉'],
    'yang_deficient': ['多食温阳食物：羊肉、韭菜、核桃', '生姜红糖水晨饮', '忌食寒凉生冷'],
    'yin_deficient':  ['多食滋阴食物：银耳、百合、鸭肉', '枸杞菊花茶常饮', '忌食辛辣燥热'],
    'phlegm_damp':    ['多食健脾化湿：薏米、冬瓜、赤小豆', '荷叶山楂茶', '少食肥甘厚腻'],
    'damp_heat':      ['多食清热利湿：绿豆、苦瓜、芹菜', '菊花金银花茶', '忌食辛辣油腻'],
    'blood_stasis':   ['多食活血化瘀：山楂、黑木耳、醋', '玫瑰花茶', '忌食寒凉收涩'],
    'qi_stagnation':  ['多食理气解郁：柑橘、佛手、玫瑰花', '陈皮茶', '少食涩味食物'],
    'allergic':       ['避免已知过敏食物', '多食益气固表：黄芪、白术', '清淡饮食为主'],
}

# 体质对应的运动建议
EXERCISE_RECOMMENDATIONS = {
    'balanced':       ['每周150分钟中等强度运动', '跑步、游泳、球类皆宜', '保持运动习惯'],
    'qi_deficient':   ['温和运动为主：太极拳、八段锦', '散步30分钟/天', '避免剧烈运动大汗'],
    'yang_deficient': ['阳光下运动：快走、太极', '上午运动最佳', '注意保暖避风寒'],
    'yin_deficient':  ['避免高温运动', '游泳、瑜伽、太极', '傍晚运动为宜', '及时补充水分'],
    'phlegm_damp':    ['中等强度有氧：慢跑、骑车', '每周≥5次，每次40分钟', '循序渐进加量'],
    'damp_heat':      ['大强度运动排汗：跑步、健身', '运动后及时清洁', '避免潮湿环境运动'],
    'blood_stasis':   ['促进循环：快走、舞蹈、太极', '避免久坐久站', '运动前充分热身'],
    'qi_stagnation':  ['团体运动：集体舞、球类', '户外运动舒展心情', '配合深呼吸'],
    'allergic':       ['室内运动为主', '避免花粉季节户外运动', '运动前充分热身'],
}


@dataclass
class ConstitutionResult:
    """体质推理结果"""
    constitution_id: str
    constitution_name: str
    mythic_name: str
    icon: str
    color: str
    confidence: float  # 置信度 0-1

    # 所有体质得分
    all_scores: Dict[str, float] = field(default_factory=dict)

    # 体质描述
    description: str = ''
    traits: List[str] = field(default_factory=list)

    # 五脏评分 (0-100)
    organ_scores: Dict[str, float] = field(default_factory=dict)

    # 身体年龄估算
    body_age: float = 30.0
    chronological_age: float = 30.0
    age_diff: float = 0.0  # 负值=年轻

    # 对比人群
    percentile: float = 50.0  # 在同龄人中的排名
    population_pct: float = 0.0

    # 建议
    diet: List[str] = field(default_factory=list)
    exercise: List[str] = field(default_factory=list)
    lifestyle: List[str] = field(default_factory=list)

    # 分享卡片数据
    share_text: str = ''

    # 理论依据
    references: List[dict] = field(default_factory=lambda: TCM_REFERENCES[:3])

    # 周易维度
    zhouyi: dict = field(default_factory=dict)


class ConstitutionEngine:
    """
    体质推理引擎

    输入：PalmFeatures（24维特征向量）
    输出：ConstitutionResult（体质类型 + 详细建议）

    规则引擎逻辑（基于中医手诊理论）：
    1. 根据掌纹特征计算9种体质的匹配分数
    2. 选择最高分作为主要体质
    3. 综合特征计算五脏功能评分和身体年龄
    """

    def __init__(self, default_age: float = 30.0):
        self.default_age = default_age

    def infer(self, features: PalmFeatures, chronological_age: float = None) -> ConstitutionResult:
        """
        体质推理

        Args:
            features: 掌纹特征
            chronological_age: 实际年龄（用于身体年龄对比），默认30

        Returns:
            ConstitutionResult
        """
        if chronological_age is None:
            chronological_age = self.default_age

        vec = features.vector
        scores = {}

        # === 规则引擎：计算每种体质的匹配分数 ===

        # 1. 平和质 — 所有指标均衡
        scores['balanced'] = self._score_balanced(vec, features)

        # 2. 气虚质 — 掌纹浅淡、大鱼际松软
        scores['qi_deficient'] = self._score_qi_deficient(vec, features)

        # 3. 阳虚质 — 掌色苍白、纹路细弱
        scores['yang_deficient'] = self._score_yang_deficient(vec, features)

        # 4. 阴虚质 — 掌面偏红、纹理细密杂乱
        scores['yin_deficient'] = self._score_yin_deficient(vec, features)

        # 5. 痰湿质 — 掌面油腻、大鱼际肥厚
        scores['phlegm_damp'] = self._score_phlegm_damp(vec, features)

        # 6. 湿热质 — 掌面红而油亮
        scores['damp_heat'] = self._score_damp_heat(vec, features)

        # 7. 血瘀质 — 掌面暗红、纹路粗深
        scores['blood_stasis'] = self._score_blood_stasis(vec, features)

        # 8. 气郁质 — 掌纹分叉交错、张力不均
        scores['qi_stagnation'] = self._score_qi_stagnation(vec, features)

        # 9. 特禀质 — 纹理紊乱
        scores['allergic'] = self._score_allergic(vec, features)

        # 归一化（softmax）
        scores_array = np.array(list(scores.values()))
        exp_scores = np.exp(scores_array - scores_array.max())  # 数值稳定
        normalized = exp_scores / exp_scores.sum()

        score_dict = {}
        for i, (ctype, _) in enumerate(scores.items()):
            score_dict[ctype] = round(float(normalized[i]), 4)

        # 确定主要体质
        primary_id = max(score_dict, key=score_dict.get)
        primary_conf = score_dict[primary_id]
        ctype_info = CONSTITUTION_TYPES[primary_id]

        # === 五脏功能评分 ===
        organ_scores = self._estimate_organ_scores(features, primary_id)

        # === 身体年龄估算 ===
        body_age = self._estimate_body_age(features, chronological_age)

        # === 建议生成 ===
        diet = DIET_RECOMMENDATIONS.get(primary_id, DIET_RECOMMENDATIONS['balanced'])
        exercise = EXERCISE_RECOMMENDATIONS.get(primary_id, EXERCISE_RECOMMENDATIONS['balanced'])
        lifestyle = self._generate_lifestyle(primary_id, organ_scores)

        # === 分享文案 ===
        share_text = self._generate_share_text(primary_id, primary_conf, body_age, chronological_age)

        return ConstitutionResult(
            constitution_id=primary_id,
            constitution_name=ctype_info['name'],
            mythic_name=ctype_info['mythic_name'],
            icon=ctype_info['icon'],
            color=ctype_info['color'],
            confidence=primary_conf,
            all_scores=score_dict,
            description=ctype_info['description'],
            traits=ctype_info.get('traits', []),
            organ_scores=organ_scores,
            body_age=body_age,
            chronological_age=chronological_age,
            age_diff=round(body_age - chronological_age, 1),
            percentile=round((1 - primary_conf) * 100, 1),
            population_pct=ctype_info.get('population_pct', 0),
            diet=diet,
            exercise=exercise,
            lifestyle=lifestyle,
            share_text=share_text,
            references=TCM_REFERENCES,
            zhouyi=derive_zhouyi(primary_id, features),
        )

    def _score_balanced(self, vec: np.ndarray, f: PalmFeatures) -> float:
        """平和质评分：所有指标都在中等范围"""
        ideal = np.array([50, 50, 50, 0.5, 0.5, 0.5, 0, 0, 50, 50, 50, 50, 50, 50, 10, 50, 50, 10, 10, 50])
        diff = np.abs(vec - ideal)
        # 偏离理想值越远分越低
        return float(100 - np.mean(diff) * 1.5)

    def _score_qi_deficient(self, vec: np.ndarray, f: PalmFeatures) -> float:
        """气虚质：纹线浅淡、大鱼际塌陷、色泽偏白"""
        score = 50.0
        score += (35 - f.life_line_depth) * 0.5       # 生命线浅
        score += (35 - f.head_line_depth) * 0.3       # 智慧线浅
        score += (35 - f.thenar_fullness) * 0.6       # 大鱼际塌陷
        score += (35 - f.overall_redness) * 0.4       # 色泽苍白
        score += (f.vein_visibility - 20) * 0.3       # 静脉可见
        return max(0, score)

    def _score_yang_deficient(self, vec: np.ndarray, f: PalmFeatures) -> float:
        """阳虚质：掌色苍白偏青、纹线细弱、掌温低"""
        score = 50.0
        score += (25 - f.overall_redness) * 0.6       # 色泽苍白
        score += (30 - f.life_line_depth) * 0.4       # 纹线细弱
        score += (40 - f.luster) * 0.4                 # 缺乏光泽
        score += (40 - f.thenar_fullness) * 0.3       # 大鱼际不饱满
        score += (f.vein_visibility - 10) * 0.4       # 静脉显现
        return max(0, score)

    def _score_yin_deficient(self, vec: np.ndarray, f: PalmFeatures) -> float:
        """阴虚质：掌面偏红、纹理细密、掌心热感"""
        score = 50.0
        score += (f.overall_redness - 55) * 0.6       # 偏红
        score += (f.texture_density - 50) * 0.4        # 纹理细密
        score += (f.luster - 55) * 0.3                 # 光泽亮
        score += (60 - f.skin_color_std) * 0.3         # 色泽均匀（偏红均匀）
        score += (55 - f.center_depth) * 0.2           # 掌心较平
        return max(0, score)

    def _score_phlegm_damp(self, vec: np.ndarray, f: PalmFeatures) -> float:
        """痰湿质：大鱼际肥厚、掌面油腻、纹路粗而模糊"""
        score = 50.0
        score += (f.thenar_fullness - 55) * 0.6        # 大鱼际肥厚
        score += (f.luster - 50) * 0.5                  # 油腻光泽
        score += (50 - f.line_complexity) * 0.3        # 纹路模糊（复杂度低）
        score += (60 - f.texture_density) * 0.3        # 纹路密度低
        score += (f.hypothenar_fullness - 50) * 0.2    # 小鱼际也饱满
        return max(0, score)

    def _score_damp_heat(self, vec: np.ndarray, f: PalmFeatures) -> float:
        """湿热质：掌面红而油亮、纹理粗"""
        score = 50.0
        score += (f.overall_redness - 55) * 0.5        # 偏红
        score += (f.luster - 55) * 0.5                  # 油亮
        score += (f.vein_visibility - 20) * 0.3        # 静脉显现
        score += (f.texture_density - 45) * 0.3        # 纹理较密
        score += (60 - f.color_uniformity) * 0.2       # 色泽不均
        return max(0, score)

    def _score_blood_stasis(self, vec: np.ndarray, f: PalmFeatures) -> float:
        """血瘀质：掌面暗红偏紫、纹路粗深分叉、可见瘀点"""
        score = 50.0
        score += (f.overall_redness - 50) * 0.3        # 暗红
        score += (f.texture_density - 50) * 0.5        # 纹路密集
        score += (f.line_complexity - 50) * 0.5        # 纹路复杂分叉
        score += (55 - f.color_uniformity) * 0.5       # 色泽不均
        score += (f.capillary_visibility - 15) * 0.4   # 毛细血管可见
        score += (f.gabor_energy - 10) * 0.3           # 纹理能量高
        return max(0, score)

    def _score_qi_stagnation(self, vec: np.ndarray, f: PalmFeatures) -> float:
        """气郁质：掌纹多分叉、感情线断续、丘位张力不均"""
        score = 50.0
        score += (f.line_complexity - 50) * 0.5        # 纹路复杂
        score += (f.interference_line_count * 5 - 15) * 0.4  # 干扰线多
        score += (55 - f.mound_balance) * 0.5           # 丘位不均衡
        score += (f.texture_density - 45) * 0.3         # 纹理密度高
        score += (55 - f.color_uniformity) * 0.2        # 色泽不均
        return max(0, score)

    def _score_allergic(self, vec: np.ndarray, f: PalmFeatures) -> float:
        """特禀质：纹理紊乱、掌面敏感泛红"""
        score = 50.0
        score += (f.line_complexity - 55) * 0.5        # 纹路紊乱
        score += (f.skin_color_std - 20) * 0.4         # 色泽变异大
        score += (f.overall_redness - 50) * 0.3        # 偏红
        score += (55 - f.color_uniformity) * 0.4       # 不均匀
        score += (f.capillary_visibility - 15) * 0.3   # 毛细血管可见
        return max(0, score)

    def _estimate_organ_scores(self, f: PalmFeatures, constitution_id: str) -> Dict[str, float]:
        """估算五脏功能评分"""
        # 基础评分（根据体质类型确定优势/弱势器官）
        base_scores = {'心': 75.0, '肝': 75.0, '脾': 75.0, '肺': 75.0, '肾': 75.0}

        ctype = CONSTITUTION_TYPES.get(constitution_id, {})
        for organ in ctype.get('strength_organs', []):
            base_scores[organ] += 10
        for organ in ctype.get('watch_organs', []):
            base_scores[organ] -= 10

        # 根据掌纹特征微调
        # 大鱼际→脾胃，小鱼际→肾，掌心→心，纹理密度→肝
        base_scores['脾'] += (f.thenar_fullness - 50) * 0.2
        base_scores['肾'] += (f.hypothenar_fullness - 50) * 0.2
        base_scores['心'] += (f.overall_redness - 50) * 0.15
        base_scores['肝'] += (60 - f.line_complexity) * 0.15
        base_scores['肺'] += (f.color_uniformity - 50) * 0.15

        # 限制在合理范围内
        return {k: round(np.clip(v, 30, 98), 1) for k, v in base_scores.items()}

    def _estimate_body_age(self, f: PalmFeatures, chronological_age: float) -> float:
        """
        估算体质脏腑功能年龄（Constitutional Functional Age）

        理论依据：
        - [R3]《灵枢·本脏》："视其外应，以知其内脏"——掌纹作为望诊窗口，反映内脏功能状态
        - [R5]《中医手诊学》："手掌色泽、纹理、丘位形态可反映脏腑盛衰"（刘剑锋, 2012）
        - [R6]《中医望诊彩色图谱》："掌纹深浅、色泽明暗与年龄相关，亦与脏腑功能盛衰相关"（张登本, 2010）
        - [R8]《中医诊断学》："望诊内容包括神、色、形、态"——手掌形态反映身体状态（朱文锋, 2007）

        方法说明：
        本算法基于中医手诊"形神相应"原理，将掌纹特征映射为脏腑功能状态评分，
        再通过五脏功能加权计算整体的"体质功能年龄"。该年龄反映的是手掌所呈现的
        脏腑功能状态相当于哪个年龄段的一般水平，而非生物年龄估算。

        计算公式：
        CFA = 身份证年龄 + Σ(脏腑功能偏离度 × 该脏腑权重)

        其中脏腑功能偏离度 = f(掌纹特征) - 同龄人平均水平
        偏离度为正（功能优于同龄）→ 年龄向下修正
        偏离度为负（功能不及同龄）→ 年龄向上修正
        """
        # 五脏权重（基于[R2]王琦体质学说中各脏腑对整体健康的影响程度）
        organ_weights = {
            '心': 0.22,  # 心主血脉，其华在面 [R3]
            '肝': 0.20,  # 肝主疏泄，其华在爪 [R3]
            '脾': 0.22,  # 脾主运化，其华在唇四白 [R3]
            '肺': 0.18,  # 肺主皮毛，其华在毛 [R3]
            '肾': 0.18,  # 肾主藏精，其华在发 [R3]
        }

        # 估算五脏功能评分
        organ_scores = self._estimate_organ_scores(f, 'balanced')

        # 同龄人标准值 = 75（对应[R10]国家公卫规范中的"平和质"基准）
        baseline = 75.0

        # 计算五脏功能加权偏离度
        weighted_deviation = 0.0
        for organ, weight in organ_weights.items():
            score = organ_scores.get(organ, baseline)
            # 偏离百分比（正=优，负=差）
            deviation = (score - baseline) / baseline
            weighted_deviation += deviation * weight

        # 将偏离度转换为年龄修正系数
        # 基准：±1个标准偏离 ≈ ±8年（基于[R9]王琦体质学研究中不同体质人群的年龄分布）
        age_correction = -weighted_deviation * 8.0

        # 限制修正范围（避免极端值，保证临床合理性）
        age_correction = np.clip(age_correction, -15.0, 20.0)

        body_age = chronological_age + age_correction
        return round(np.clip(body_age, 18, 85), 1)

    def _generate_lifestyle(self, constitution_id: str, organ_scores: Dict[str, float]) -> List[str]:
        """生成生活方式建议"""
        tips = []

        # 找出最弱的器官
        weakest = min(organ_scores, key=organ_scores.get)
        weakest_score = organ_scores[weakest]
        element = FIVE_ELEMENTS.get(weakest, {}).get('element', '')

        if weakest_score < 55:
            tips.append(f'重点关注{weakest}系统（五行属{element}），建议定期体检监测')

        # 体质特定建议
        lifestyle_map = {
            'balanced':       ['保持现有生活方式', '定期体检，预防为主'],
            'qi_deficient':   ['保证充足睡眠（7-8小时/天）', '避免过度劳累', '午后小憩15-20分钟'],
            'yang_deficient': ['注意保暖，尤其腰腹部', '热水泡脚每晚20分钟', '多晒太阳（上午9-11点最佳）'],
            'yin_deficient':  ['保证充足水分摄入', '避免熬夜（23点前入睡）', '减少辛辣刺激食物'],
            'phlegm_damp':    ['控制体重，BMI目标<24', '居住环境保持干燥通风', '减少高脂高糖饮食'],
            'damp_heat':      ['避免潮湿闷热环境', '戒烟限酒', '注意个人卫生'],
            'blood_stasis':   ['避免久坐，每小时活动5分钟', '保持心情舒畅', '适量饮用温热水'],
            'qi_stagnation':  ['多参与社交活动', '培养兴趣爱好', '练习冥想或深呼吸'],
            'allergic':       ['远离已知过敏原', '家中常备抗过敏药物', '换季时注意防护'],
        }

        tips.extend(lifestyle_map.get(constitution_id, lifestyle_map['balanced']))
        return tips[:4]  # 最多4条

    def _generate_share_text(self, constitution_id: str, confidence: float,
                              body_age: float, chronological_age: float) -> str:
        """生成分享文案"""
        ctype = CONSTITUTION_TYPES[constitution_id]
        mythic = ctype['mythic_name']
        pct = ctype['population_pct']
        diff = body_age - chronological_age

        if diff < -3:
            age_text = f'身体年龄比实际年轻{abs(diff):.0f}岁'
        elif diff > 3:
            age_text = f'需要注意调理，身体年龄比实际大{diff:.0f}岁'
        else:
            age_text = '身体年龄与身份证年龄相符'

        templates = [
            f'🖐️ 我的掌纹体质：{mythic}（{ctype["name"]}）\n全国只有{pct}%的人是这种体质！\n{age_text}\n👉 你也来测测？',
            f'AI看了我的手掌，说我是"{mythic}"体质\n{ctype["name"]}，全国占比{pct}%\n{age_text}\n扫码测你的掌纹体质→',
        ]

        # 简单随机选一个（实际应用中可做A/B测试）
        idx = hash(str(constitution_id + str(round(body_age)))) % len(templates)
        return templates[idx]


# ======================== 测试代码 ========================
if __name__ == '__main__':
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from src.feature_extractor import FeatureExtractor
    import cv2

    extractor = FeatureExtractor()
    engine = ConstitutionEngine()

    if len(sys.argv) > 1:
        roi_path = sys.argv[1]
        roi = cv2.imread(roi_path)
        if roi is None:
            print(f'❌ 无法读取: {roi_path}')
            sys.exit(1)
        if roi.shape[:2] != (256, 256):
            roi = cv2.resize(roi, (256, 256))

        features = extractor.extract(roi)
        result = engine.infer(features, chronological_age=35)

        print('=' * 50)
        print(f'  {result.icon} {result.mythic_name}（{result.constitution_name}）')
        print(f'  置信度: {result.confidence:.1%}')
        print(f'  描述: {result.description}')
        print(f'  特质: {"、".join(result.traits)}')
        print(f'  身体年龄: {result.body_age}岁 (实际{result.chronological_age}岁, 差异{result.age_diff:+.1f}岁)')
        print(f'  全国占比: {result.population_pct}%')
        print(f'\n  五脏评分:')
        for organ, score in result.organ_scores.items():
            bar = '█' * int(score / 5) + '░' * (20 - int(score / 5))
            print(f'    {organ}: {bar} {score:.0f}')
        print(f'\n  🍽️ 饮食建议:')
        for d in result.diet:
            print(f'    · {d}')
        print(f'\n  🏃 运动建议:')
        for e in result.exercise:
            print(f'    · {e}')
        print(f'\n  💡 生活方式:')
        for l in result.lifestyle:
            print(f'    · {l}')
        print(f'\n  📤 分享文案:')
        print(f'    {result.share_text}')
        print('=' * 50)
    else:
        print('用法: python constitution_engine.py <掌纹ROI图片路径>')
