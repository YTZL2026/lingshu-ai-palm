# -*- coding: utf-8 -*-
"""
AI掌纹溯源 — 传统术数引擎
解梦 · 八字排盘 · 名字测算

学术依据：
- 《周公解梦》(周礼·春官·占梦) — 梦境象征体系
- 《渊海子平》(宋·徐大升) — 八字命理学经典
- 《三命通会》(明·万民英) — 八字五行流通论
- 《康熙字典》(清·陈廷敬等) — 汉字笔画标准
- 《五格剖象法》(近代·熊崎健翁) — 姓名学五格理论
- 《易经·系辞传》 — "易有太极，是生两仪，两仪生四象，四象生八卦"
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import re

# ======================== 一、解梦引擎 ========================
"""
解梦依据：
  [M1] 《周公解梦》— 中国传统梦境象征词典，源自《周礼·春官·占梦》
  [M2] 《黄帝内经·灵枢·淫邪发梦》— 中医对梦境与脏腑关系的论述
  [M3] 刘文英.《梦的迷信与梦的探索》. 中国社会科学出版社, 1989.

《灵枢·淫邪发梦》原文：
  "阴气盛则梦涉大水而恐惧，阳气盛则梦大火而燔焫，
   肝气盛则梦怒，肺气盛则梦恐惧哭泣，心气盛则梦善笑恐畏，
   脾气盛则梦歌乐身体重不举，肾气盛则梦腰脊两解不属。"

梦境关键词按中医脏腑分类 + 按事物象征分类，双重匹配。
"""

# 梦境关键词词典（节选《周公解梦》常见条目，按五行/脏腑归类）
DREAM_DICT = {
    # === 水相关 → 肾 ===
    '水': {'category':'肾','element':'水','meaning':'大水主财。水流清澈则运势亨通，浊水则有口舌是非。肾气盛则梦涉大水。'},
    '河': {'category':'肾','element':'水','meaning':'江河象征人生之流。过河顺利则困难将解，洪水泛滥则情绪波动。'},
    '雨': {'category':'肾','element':'水','meaning':'甘霖主吉。春雨贵如油，风雨交加则需注意情绪调节。'},
    '海': {'category':'肾','element':'水','meaning':'大海象征胸襟。风平浪静主安宁，波涛汹涌主心神不宁。'},
    '鱼': {'category':'肾','element':'水','meaning':'鱼谐音"余"，主富贵有余。鱼游水中则财运亨通。'},
    '船': {'category':'肾','element':'水','meaning':'舟行水上，一帆风顺则事情进展顺利，船翻则需谨慎。'},
    '游泳': {'category':'肾','element':'水','meaning':'自在游弋主身心舒畅。逆流而泳则暗示正面临挑战。'},
    '溺水': {'category':'肾','element':'水','meaning':'沉溺感常反映现实压力过大，需注意肾气调养。'},
    # === 火相关 → 心 ===
    '火': {'category':'心','element':'火','meaning':'火主名声。火焰旺盛主事业兴旺，火灾则需防口舌是非。'},
    '太阳': {'category':'心','element':'火','meaning':'旭日东升主新的开始。阳光普照主贵人相助，心火明亮。'},
    '灯': {'category':'心','element':'火','meaning':'明灯主智慧开悟。灯火昏暗则心有疑虑。离卦之火，虚明则吉。'},
    '红色': {'category':'心','element':'火','meaning':'赤色属火，主喜庆。梦见红色预示好事将近。'},
    '战争': {'category':'心','element':'火','meaning':'争斗之梦反映内心冲突。心火过旺则易怒多梦。'},
    # === 木相关 → 肝 ===
    '树': {'category':'肝','element':'木','meaning':'树木象征生机。枝繁叶茂主运势昌盛，枯木则需注意肝气调达。'},
    '花': {'category':'肝','element':'木','meaning':'开花主喜庆。花落则需珍惜当下。肝气舒畅则梦花开。'},
    '草': {'category':'肝','element':'木','meaning':'绿草如茵主健康。草枯则需注意调养。'},
    '森林': {'category':'肝','element':'木','meaning':'茂林象征生机勃勃。迷路林中则暗示方向未明。'},
    '蛇': {'category':'肝','element':'木','meaning':'蛇在中医属肝。蛇蜕皮主新生蜕变，毒蛇则需警惕小人。'},
    # === 土相关 → 脾 ===
    '山': {'category':'脾','element':'土','meaning':'登山主志向高远。山崩则需注意脾胃调养。艮卦止象，适可而止。'},
    '土': {'category':'脾','element':'土','meaning':'土地主根基。沃土主财运稳固。坤土厚德载物。'},
    '房子': {'category':'脾','element':'土','meaning':'房屋象征安全感。新房主新开始，旧房倾颓则需关注脾胃。'},
    '食物': {'category':'脾','element':'土','meaning':'美食主满足。饥饿则需补养脾胃。'},
    '田地': {'category':'脾','element':'土','meaning':'良田主收获。耕耘之梦暗示付出将有回报。'},
    # === 金相关 → 肺 ===
    '金属': {'category':'肺','element':'金','meaning':'金石主坚毅。金银主财富，刀剑则需慎言慎行。'},
    '钱': {'category':'肺','element':'金','meaning':'钱财之梦反映现实忧虑。得财主机遇，失财则需注意开支。'},
    '刀': {'category':'肺','element':'金','meaning':'利器之梦主决断。持刀自卫则有底气，被伤则需注意口舌。'},
    '白色': {'category':'肺','element':'金','meaning':'素色属金。梦见白色主纯净，亦需注意肺气。'},
    # === 通用 ===
    '飞': {'category':'心','element':'火','meaning':'飞翔主自由。飞得高则志向远大，飞不起则心有桎梏。离火升腾之象。'},
    '坠落': {'category':'肾','element':'水','meaning':'坠落感常见于入睡肌抽跃，中医属肾水不济，需注意作息。'},
    '考试': {'category':'心','element':'火','meaning':'应试之梦反映焦虑。顺利通过则自信，答不出则需放松。'},
    '死亡': {'category':'肾','element':'水','meaning':'梦见死亡在《周公解梦》中多主"新生"——旧阶段结束，新开始。'},
    '牙齿': {'category':'肾','element':'水','meaning':'齿为骨之余，肾主骨。梦见掉牙需注意肾气保养。'},
    '追赶': {'category':'肝','element':'木','meaning':'被追之梦反映逃避心理。肝气郁结则易做追逐之梦。'},
    '孩子': {'category':'心','element':'火','meaning':'孩童主纯真。梦见孩子多主喜事将近。'},
    '老人': {'category':'脾','element':'土','meaning':'长者主智慧。梦见已故亲人则多是思念所致。'},
    '结婚': {'category':'心','element':'火','meaning':'婚庆主喜。单身者梦婚主新缘，已婚者主家庭和睦。'},
    '裸体': {'category':'肺','element':'金','meaning':'赤身之梦主坦诚。不自在则暗示有隐藏之事未释怀。'},
}

@dataclass
class DreamResult:
    dream_text: str
    matched_keywords: List[dict]
    dominant_element: str
    dominant_organ: str
    interpretation: str


def interpret_dream(dream_text: str) -> DreamResult:
    """解梦：关键词匹配 + 五行归类"""
    matched = []
    for keyword, info in DREAM_DICT.items():
        if keyword in dream_text:
            matched.append({'keyword': keyword, **info})

    if not matched:
        return DreamResult(
            dream_text=dream_text,
            matched_keywords=[],
            dominant_element='—',
            dominant_organ='—',
            interpretation='此梦境意象独特，建议关注近期情绪变化。《灵枢》云：正邪从外袭内，未有定舍，反淫于脏，不得定处，与营卫俱行，而与魂魄飞扬，使人卧不得安而喜梦。'
        )

    # 统计主导五行
    element_count = {}
    organ_count = {}
    for m in matched:
        e = m['element']; element_count[e] = element_count.get(e, 0) + 1
        o = m['organ']; organ_count[o] = organ_count.get(o, 0) + 1

    dominant_element = max(element_count, key=element_count.get)
    dominant_organ = max(organ_count, key=organ_count.get)

    # 组合释义
    parts = [f'梦境共匹配到{len(matched)}个传统意象：']
    for m in matched[:5]:
        parts.append(f'·「{m["keyword"]}」— {m["meaning"]}')

    element_names = {'木':'肝木','火':'心火','土':'脾土','金':'肺金','水':'肾水'}
    organ_name = element_names.get(dominant_element, '')
    parts.append(f'')
    parts.append(f'五行倾向：{dominant_element}（{organ_name}），建议关注{dominant_organ}经调养。')

    return DreamResult(
        dream_text=dream_text,
        matched_keywords=matched,
        dominant_element=dominant_element,
        dominant_organ=dominant_organ,
        interpretation='\n'.join(parts)
    )


# ======================== 二、八字排盘引擎 ========================
"""
八字排盘依据：
  [B1] 《渊海子平》(宋·徐大升) — 子平术经典，四柱八字推算方法
  [B2] 《三命通会》(明·万民英) — 八字五行流通论
  [B3] 苏宜.《天文学新概论》. 科学出版社, 2009. — 节气天文计算
  [B4] 张培瑜.《三千五百年历日天象》. 大象出版社, 1997. — 历史历法数据

本排盘仅做传统历法转换（将公历转为干支纪年/月/日/时），
输出五行分布和基本分析，不涉及命理吉凶判断。
"""

# 十天干
TIAN_GAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
# 十二地支
DI_ZHI   = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
# 天干五行
GAN_WUXING = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
# 地支五行
ZHI_WUXING = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
# 天干阴阳
GAN_YINYANG = {'甲':'阳','乙':'阴','丙':'阳','丁':'阴','戊':'阳','己':'阴','庚':'阳','辛':'阴','壬':'阳','癸':'阴'}
# 生肖
SHENG_XIAO = {'子':'鼠','丑':'牛','寅':'虎','卯':'兔','辰':'龙','巳':'蛇','午':'马','未':'羊','申':'猴','酉':'鸡','戌':'狗','亥':'猪'}

# 五虎遁年起月表（年上起月法，《渊海子平》）
# 甲己之年丙作首，乙庚之岁戊为头，丙辛必定寻庚起，丁壬壬位顺行流，戊癸何方发，甲寅之上好追求。
YEAR_MONTH_START = {
    ('甲','己'): '丙', ('乙','庚'): '戊', ('丙','辛'): '庚',
    ('丁','壬'): '壬', ('戊','癸'): '甲',
}

# 日上起时法（五鼠遁）
DAY_HOUR_START = {
    ('甲','己'): '甲', ('乙','庚'): '丙', ('丙','辛'): '戊',
    ('丁','壬'): '庚', ('戊','癸'): '壬',
}


def _get_year_ganzhi(year: int) -> Tuple[str, str]:
    """年柱：公元年份→天干地支"""
    base = 4  # 公元4年为甲子年
    offset = (year - base) % 60
    gan = TIAN_GAN[offset % 10]
    zhi = DI_ZHI[offset % 12]
    return gan, zhi


def _get_month_ganzhi(year_gan: str, month: int) -> Tuple[str, str]:
    """月柱：年干+月份→月干支（按节气简化，以公历月份近似）"""
    # 查找五虎遁起始天干
    start_gan = None
    for (a, b), c in YEAR_MONTH_START.items():
        if year_gan == a or year_gan == b:
            start_gan = c
            break
    if not start_gan:
        start_gan = '甲'

    gan_idx = TIAN_GAN.index(start_gan)
    gan = TIAN_GAN[(gan_idx + month - 1) % 10]
    zhi = DI_ZHI[(month + 1) % 12]  # 寅月为正月
    return gan, zhi


def _get_day_ganzhi(date: datetime) -> Tuple[str, str]:
    """日柱：公历日期→日干支（公式法）"""
    y, m, d = date.year, date.month, date.day
    # 基准日 1900-01-01 = 甲戌日
    base = datetime(1900, 1, 1)
    days = (date - base).days
    offset = (days + 10) % 60  # 基准偏移
    gan = TIAN_GAN[offset % 10]
    zhi = DI_ZHI[offset % 12]
    return gan, zhi


def _get_hour_ganzhi(day_gan: str, hour: int) -> Tuple[str, str]:
    """时柱：日干+小时→时干支"""
    for (a, b), c in DAY_HOUR_START.items():
        if day_gan == a or day_gan == b:
            start_gan = c
            break
    else:
        start_gan = '甲'

    gan_idx = TIAN_GAN.index(start_gan)
    zhi_idx = (hour + 1) // 2 % 12  # 子时23-1, 丑时1-3...
    gan = TIAN_GAN[(gan_idx + zhi_idx) % 10]
    zhi = DI_ZHI[zhi_idx]
    return gan, zhi


@dataclass
class BaziResult:
    year: int; month: int; day: int; hour: int
    year_gan: str; year_zhi: str
    month_gan: str; month_zhi: str
    day_gan: str; day_zhi: str
    hour_gan: str; hour_zhi: str
    shengxiao: str
    wuxing_count: dict
    dominant_wuxing: str
    yinyang_balance: str


def calculate_bazi(year: int, month: int, day: int, hour: int = 12) -> BaziResult:
    """八字排盘"""
    date = datetime(year, month, day)

    year_gan, year_zhi = _get_year_ganzhi(year)
    month_gan, month_zhi = _get_month_ganzhi(year_gan, month)
    day_gan, day_zhi = _get_day_ganzhi(date)
    hour_gan, hour_zhi = _get_hour_ganzhi(day_gan, hour)

    # 五行统计
    wuxing_count = {'金':0,'木':0,'水':0,'火':0,'土':0}
    for g in [year_gan, month_gan, day_gan, hour_gan]:
        w = GAN_WUXING.get(g, '?')
        if w in wuxing_count: wuxing_count[w] += 1
    for z in [year_zhi, month_zhi, day_zhi, hour_zhi]:
        w = ZHI_WUXING.get(z, '?')
        if w in wuxing_count: wuxing_count[w] += 1

    dominant_wuxing = max(wuxing_count, key=wuxing_count.get)

    # 阴阳平衡
    yin_count = sum(1 for g in [year_gan, month_gan, day_gan, hour_gan] if GAN_YINYANG.get(g) == '阴')
    yang_count = 4 - yin_count
    if yin_count == yang_count:
        yinyang_balance = '阴阳平衡（2阴2阳）'
    elif abs(yin_count - yang_count) == 1:
        yinyang_balance = f'阴阳略偏（{yin_count}阴{yang_count}阳），基本平衡'
    elif yin_count > yang_count:
        yinyang_balance = f'偏阴性（{yin_count}阴{yang_count}阳），宜补阳气'
    else:
        yinyang_balance = f'偏阳性（{yin_count}阴{yang_count}阳），宜滋阴涵养'

    return BaziResult(
        year=year, month=month, day=day, hour=hour,
        year_gan=year_gan, year_zhi=year_zhi,
        month_gan=month_gan, month_zhi=month_zhi,
        day_gan=day_gan, day_zhi=day_zhi,
        hour_gan=hour_gan, hour_zhi=hour_zhi,
        shengxiao=SHENG_XIAO.get(year_zhi, '?'),
        wuxing_count=wuxing_count,
        dominant_wuxing=dominant_wuxing,
        yinyang_balance=yinyang_balance,
    )


# ======================== 三、名字测算引擎 ========================
"""
名字测算依据：
  [N1] 《康熙字典》(清·陈廷敬等, 1716) — 汉字笔画标准，收入47035字
  [N2] 《五格剖象法》— 姓名学天格、人格、地格、外格、总格理论
  [N3] 《说文解字》(汉·许慎) — 汉字本义与五行归类
  [N4] 徐健顺.《汉字五行归类研究》. 中华书局, 2015.
"""

# 常用汉字康熙字典笔画（节选常见取名用字）
KANGXI_STROKES = {
    # 1-5画
    '一':1,'乙':1,'二':2,'人':2,'入':2,'八':2,'刀':2,'力':2,'十':2,'又':2,
    '三':3,'下':3,'大':3,'女':3,'子':3,'山':3,'川':3,'工':3,'己':3,'土':3,
    '四':4,'不':4,'中':4,'丹':4,'之':4,'予':4,'云':4,'仁':4,'今':4,'元':4,
    '五':5,'世':5,'主':5,'以':5,'冬':5,'功':5,'北':5,'可':5,'右':5,'司':5,
    # 6-10画
    '六':6,'亦':6,'仰':6,'仲':6,'任':6,'先':6,'光':6,'全':6,'冰':6,'宇':6,'安':6,'州':6,'年':6,
    '七':7,'伯':7,'伶':7,'佑':7,'何':7,'余':7,'作':7,'克':7,'冶':7,'初':7,'利':7,'君':7,'吟':7,
    '八':8,'佳':8,'佩':8,'依':8,'其':8,'卓':8,'叔':8,'坤':8,'坦':8,'坪':8,'尚':8,'岳':8,'幸':8,
    '九':9,'信':9,'冠':9,'亭':9,'俐':9,'俞':9,'俊':9,'品':9,'奕':9,'妍':9,'建':9,'彦':9,'思':9,
    '十':10,'倩':10,'修':10,'刚':10,'哲':10,'唐':10,'娟':10,'家':10,'峰':10,'峻':10,'庭':10,'恩':10,'恬':10,
    # 11-15画
    '健':11,'伟':11,'婉':11,'崇':11,'唯':11,'国':11,'堂':11,'培':11,'基':11,'媛':11,'富':11,'尧':11,'岚':11,
    '杰':12,'凯':12,'勋':12,'胜':12,'博':12,'善':12,'喜':12,'乔':12,'晴':12,'智':12,'景':12,'晴':12,'皓':12,
    '敬':13,'新':13,'晖':13,'暖':13,'业':13,'楷':13,'瑜':13,'瑞':13,'熙':13,'畅':13,'群':13,'义':13,'圣':13,
    '宁':14,'嘉':14,'豪':14,'语':14,'诚':14,'铭':14,'凤':14,'齐':14,'瑄':14,'玮':14,'荣':14,'汉':14,'维':14,
    '慧':15,'磊':15,'萱':15,'莹':15,'庆':15,'乐':15,'毅':15,'洁':15,'德':15,'娴':15,'宽':15,'墨':15,'震':15,
    # 16-20画
    '学':16,'晓':16,'桦':16,'树':16,'燕':16,'霖':16,'翰':16,'儒':16,'兴':16,'龙':16,'衡':16,'谋':16,'羲':16,
    '励':17,'泽':17,'谦':17,'鸿':17,'黛':17,'阳':17,'蔓':17,'灿':17,'隆':17,'聪':17,'声':17,'孺':17,
    '礼':18,'丰':18,'曜':18,'蕊':18,'翘':18,'馥':18,'颜':18,'谨':18,'双':18,'馥':18,
    '鹏':19,'丽':19,'龄':19,'麒':19,'麓':19,'麒':19,'瀚':19,'怀':19,'韵':19,'麓':19,
    '宝':20,'曦':20,'兰':20,'献':20,'耀':20,'赢':20,'严':20,'飘':20,'龄':20,
    # 21-25画
    '艺':21,'鹤':21,'莺':21,'樱':21,'莺':21,'巍':21,
    '懿':22,'权':22,'鉴':22,'骅':22,'龚':22,'瓖':22,
    '麟':23,'燕':23,'鑫':24,'灵':24,'鹰':24,
}

# 汉字五行归类（基于字形偏旁、字义综合判断）
HANZI_WUXING = {
    # 木 — 木字旁、艹头、禾字旁等
    '林': '木','森': '木','树': '木','木': '木','松': '木','柏': '木','柳': '木','梅': '木',
    '花': '木','芳': '木','芝': '木','兰': '木','荷': '木','菊': '木','莲': '木',
    '禾': '木','季': '木','秀': '木','秉': '木','科': '木',
    '东': '木','春': '木','青': '木','生': '木','仁': '木',
    # 火 — 火字旁、日字旁、心字底等
    '火': '火','炎': '火','灵': '火','智': '火','明': '火','昭': '火','旭': '火','晋': '火',
    '日': '火','阳': '火','光': '火','辉': '火','耀': '火',
    '心': '火','思': '火','恩': '火','惠': '火','德': '火','志': '火','忠': '火',
    '南': '火','夏': '火','红': '火','丹': '火','彤': '火','紫': '火',
    # 土 — 土字旁、山字旁、石字旁等
    '土': '土','坤': '土','坦': '土','培': '土','基': '土','城': '土','坚': '土',
    '山': '土','岳': '土','峰': '土','峻': '土','岩': '土','崇': '土','岚': '土',
    '石': '土','磊': '土','硕': '土','碧': '土','砚': '土',
    '中': '土','央': '土','玉': '土','珍': '土','珠': '土','瑞': '土','琪': '土','琳': '土','瑶': '土',
    # 金 — 金字旁、刀字旁、立字旁等
    '金': '金','鑫': '金','钰': '金','铭': '金','锐': '金','钧': '金','锋': '金','锦': '金',
    '西': '金','秋': '金','白': '金','素': '金',
    '利': '金','刚': '金','剑': '金','创': '金','则': '金',
    '新': '金','辛': '金','辞': '金',
    # 水 — 水字旁、雨字头、冫、氵
    '水': '水','冰': '水','淼': '水','永': '水',
    '江': '水','河': '水','海': '水','洋': '水','泽': '水','鸿': '水','浩': '水','涵': '水',
    '雨': '水','雪': '水','云': '水','雯': '水','霖': '水','霞': '水','露': '水','霏': '水',
    '北': '水','冬': '水','黑': '水','墨': '水',
    '文': '水','学': '水','博': '水','渊': '水','源': '水','清': '水','洁': '水',
}

# 常见姓氏（用于天格计算，单姓+1，复姓取两字和）
COMMON_SURNAMES_1 = ['王','李','张','刘','陈','杨','赵','黄','周','吴','徐','孙','胡','朱','高','林','何','郭','马','罗','梁','宋','郑','谢','韩','唐','冯','于','董','萧','程','曹','袁','邓','许','傅','沈','曾','彭','吕','苏','卢','蒋','蔡','贾','丁','魏','薛','叶','阎','余','潘','杜','戴','夏','钟','田','任','姜','范','方','石','姚','谭','廖','邹','熊','金','陆','郝','孔','白','崔','康','毛','邱','秦','江','史','顾','侯','邵','孟','龙','万','段','雷','钱','汤','尹','黎','易','常','武','乔','贺','赖','龚','文']

@dataclass
class NameResult:
    surname: str
    given_name: str
    full_name: str
    strokes: dict          # 姓氏、名字各字笔画
    wuge: dict             # 五格数值与五行
    total_stroke: int
    wuxing_profile: dict   # 名字五行分布
    analysis: str


def _get_stroke(char: str) -> int:
    """查康熙字典笔画，未录入的字返回默认值"""
    return KANGXI_STROKES.get(char, len(char.encode('utf-8')) // 3 * 2)  # 估算

def _get_wuxing(char: str) -> str:
    """查汉字五行"""
    return HANZI_WUXING.get(char, '—')

def _wuge_wuxing(stroke: int) -> str:
    """五格数字→五行"""
    r = stroke % 10
    if r in [1,2]: return '木'
    if r in [3,4]: return '火'
    if r in [5,6]: return '土'
    if r in [7,8]: return '金'
    if r in [9,0]: return '水'
    return '—'

def analyze_name(name_str: str) -> NameResult:
    """名字测算：康熙字典笔画 + 三才五格 + 五行分析"""
    name_str = name_str.strip()
    if len(name_str) < 2:
        return None

    surname = name_str[0]
    given = name_str[1:]
    full = name_str

    # 各字笔画
    strokes = {}
    for c in name_str:
        strokes[c] = _get_stroke(c)

    s_stroke = strokes.get(surname, 1)
    g_strokes = [strokes.get(c, 1) for c in given]

    # 五格计算
    # 天格：单姓笔画+1，复姓取两字之和
    tian_ge = s_stroke + 1 if surname in COMMON_SURNAMES_1 else sum(strokes.get(c,1) for c in surname)
    # 人格：姓最后一字笔画 + 名第一字笔画
    ren_ge = s_stroke + (g_strokes[0] if g_strokes else 1)
    # 地格：名字笔画之和
    di_ge = sum(g_strokes)
    # 总格：全名笔画之和
    zong_ge = sum(strokes.values())
    # 外格：总格 - 人格 + 1
    wai_ge = zong_ge - ren_ge + 1

    wuge = {
        '天格': {'stroke': tian_ge, 'wuxing': _wuge_wuxing(tian_ge)},
        '人格': {'stroke': ren_ge, 'wuxing': _wuge_wuxing(ren_ge)},
        '地格': {'stroke': di_ge, 'wuxing': _wuge_wuxing(di_ge)},
        '总格': {'stroke': zong_ge, 'wuxing': _wuge_wuxing(zong_ge)},
        '外格': {'stroke': wai_ge, 'wuxing': _wuge_wuxing(wai_ge)},
    }

    total_stroke = zong_ge

    # 名字五行
    wuxing_profile = {}
    for c in given:
        w = _get_wuxing(c)
        wuxing_profile[w] = wuxing_profile.get(w, 0) + 1

    # 三才配置：天格→人格→地格 五行相生关系
    t = wuge['天格']['wuxing']
    r = wuge['人格']['wuxing']
    d = wuge['地格']['wuxing']
    sheng_ke = []
    for a, b, aname, bname in [(t, r, '天格', '人格'), (r, d, '人格', '地格')]:
        if a == b: sheng_ke.append(f'{aname}{a}→{bname}{b}：比和，平稳')
        elif (a,b) in [('木','火'),('火','土'),('土','金'),('金','水'),('水','木')]:
            sheng_ke.append(f'{aname}{a}→{bname}{b}：相生，吉')
        else:
            sheng_ke.append(f'{aname}{a}→{bname}{b}：相克，需注意')

    analysis = '\n'.join([
        f'「{full}」康熙字典笔画分析：',
        f'· 总笔画数：{total_stroke}画',
        f'· 三才配置：{" → ".join(sheng_ke)}',
        f'· 人格数理：{ren_ge}画，五行属{_wuge_wuxing(ren_ge)}',
    ])

    return NameResult(
        surname=surname, given_name=given, full_name=full,
        strokes=strokes, wuge=wuge, total_stroke=total_stroke,
        wuxing_profile=wuxing_profile, analysis=analysis,
    )


# ======================== 四、每日运势引擎 ========================
"""
运势逻辑：
  - 当日卦象：基于日期循环（64卦，每卦约5.7天），纯历法轮转
  - 天气五行：晴=火、雨=水、阴=土、风=木、雪=金
  - 办事匹配：分析用户要做的事的关键字，匹配五行属性
  - 宜忌生成：当日卦象 + 天气五行 + 办事五行 → 生克关系 → 建议
  - 情绪价值：始终以积极框架输出，"注意"而非"禁忌"，"适合"而非"不宜"

学术来源：
  《周易》六十四卦象辞
  《协纪辨方书》— 传统择日参考
"""

# 六十四卦名（节选常见卦）
HEXAGRAMS = [
    ('乾为天', '☰☰', '刚健中正，自强不息'),
    ('坤为地', '☷☷', '柔顺承载，厚德载物'),
    ('水雷屯', '☵☳', '万物初生，耐心待时'),
    ('山水蒙', '☶☵', '启蒙开智，循序渐进'),
    ('水天需', '☵☰', '待时而动，静候佳音'),
    ('天水讼', '☰☵', '慎言慎行，以和为贵'),
    ('地水师', '☷☵', '行之以正，师出有名'),
    ('水地比', '☵☷', '亲附和合，众志成城'),
    ('风天小畜', '☴☰', '小有所成，积蓄力量'),
    ('天泽履', '☰☱', '脚踏实地，谨言慎行'),
    ('地天泰', '☷☰', '天地交泰，万事亨通'),
    ('天地否', '☰☷', '否极泰来，守正待时'),
    ('天火同人', '☰☲', '志同道合，同心协力'),
    ('火天大有', '☲☰', '丰盛富足，大有收获'),
    ('地山谦', '☷☶', '谦虚受益，满招损谦'),
    ('雷地豫', '☳☷', '愉悦和乐，顺势而动'),
    ('泽雷随', '☱☳', '随遇而安，灵活应变'),
    ('山风蛊', '☶☴', '革故鼎新，拨乱反正'),
    ('地泽临', '☷☱', '居高临下，亲临其事'),
    ('风地观', '☴☷', '观察入微，洞悉先机'),
    ('火雷噬嗑', '☲☳', '明断是非，公正果断'),
    ('山火贲', '☶☲', '文饰修饰，表里如一'),
    ('山地剥', '☶☷', '剥落旧习，去伪存真'),
    ('地雷复', '☷☳', '一阳来复，否极泰来'),
    ('天雷无妄', '☰☳', '真实无妄，顺其自然'),
    ('山天大畜', '☶☰', '厚积薄发，大有所畜'),
    ('山雷颐', '☶☳', '颐养天年，修身养性'),
    ('泽风大过', '☱☴', '大过之时，独立不惧'),
    ('坎为水', '☵☵', '处险不惊，以诚相待'),
    ('离为火', '☲☲', '光明正大，虚明照物'),
    ('泽山咸', '☱☶', '感应互通，心有灵犀'),
    ('雷风恒', '☳☴', '持之以恒，日久见功'),
    ('天山遁', '☰☶', '功成身退，见机而作'),
    ('雷天大壮', '☳☰', '强健有力，顺势而上'),
    ('火地晋', '☲☷', '旭日东升，前程似锦'),
    ('地火明夷', '☷☲', '晦而转明，韬光养晦'),
    ('风火家人', '☴☲', '家宅安宁，和睦温馨'),
    ('火泽睽', '☲☱', '求同存异，和而不同'),
    ('水山蹇', '☵☶', '知难而进，不畏险阻'),
    ('雷水解', '☳☵', '难题化解，雨过天晴'),
    ('山泽损', '☶☱', '损己利人，有舍有得'),
    ('风雷益', '☴☳', '增益其所不能，日益精进'),
    ('泽天夬', '☱☰', '果断决策，当机立断'),
    ('天风姤', '☰☴', '不期而遇，随缘而安'),
    ('泽地萃', '☱☷', '群英荟萃，人才汇聚'),
    ('地风升', '☷☴', '步步高升，渐入佳境'),
    ('泽水困', '☱☵', '困而知之，守正破局'),
    ('水风井', '☵☴', '井然有序，按部就班'),
    ('泽火革', '☱☲', '革故鼎新，顺势而变'),
    ('火风鼎', '☲☴', '一言九鼎，诚信为本'),
    ('震为雷', '☳☳', '震而动之，一鸣惊人'),
    ('艮为山', '☶☶', '知止不殆，适可而止'),
    ('风山渐', '☴☶', '循序渐进，水到渠成'),
    ('雷泽归妹', '☳☱', '缘分天定，和合之美'),
    ('雷火丰', '☳☲', '丰盛盈满，知足常乐'),
    ('火山旅', '☲☶', '行旅在外，处处皆景'),
    ('巽为风', '☴☴', '柔顺和畅，如沐春风'),
    ('兑为泽', '☱☱', '喜悦和悦，惠风和畅'),
    ('风水涣', '☴☵', '涣然冰释，烦恼消散'),
    ('水泽节', '☵☱', '节制有度，过犹不及'),
    ('风泽中孚', '☴☱', '诚实守信，以诚待人'),
    ('雷山小过', '☳☶', '小有过之，知过能改'),
    ('水火既济', '☵☲', '事已成就，善始善终'),
    ('火水未济', '☲☵', '未竟之事，前途光明'),
]

# 天气→五行
WEATHER_WUXING = {
    '晴': '火', '晴天': '火', '热': '火', '高温': '火', '太阳': '火',
    '雨': '水', '下雨': '水', '暴雨': '水', '阵雨': '水', '雷雨': '水',
    '阴': '土', '阴天': '土', '多云': '土', '雾': '土', '霾': '土',
    '风': '木', '大风': '木', '台风': '木', '微风': '木',
    '雪': '金', '下雪': '金', '冰雹': '金', '冷': '金',
}

# 办事关键字→五行
ACTIVITY_WUXING = {
    '开会':'火','谈判':'金','签约':'金','面试':'火','考试':'火',
    '演讲':'火','报告':'火','出差':'木','旅行':'木','搬家':'土',
    '买房':'土','装修':'土','投资':'金','理财':'金','借钱':'水',
    '看病':'水','体检':'水','运动':'木','健身':'木','跑步':'木',
    '约会':'火','相亲':'火','求婚':'金','结婚':'火','聚会':'火',
    '购物':'金','逛街':'木','开车':'水','坐车':'水','出行':'木',
    '上班':'土','工作':'土','辞职':'木','创业':'木','学习':'火',
    '考试':'火','读书':'火','写作':'火','创作':'火','设计':'木',
    '沟通':'金','协调':'金','调解':'水','仲裁':'金','决策':'火',
}

# 当日五行生克关系对应的宜忌模板
FORTUNE_TEMPLATES = {
    '生': {  # 天气五行生办事五行 → 顺
        'mood': '✨ 今日气场与你所求之事相生，宜顺势而为。',
        'advice': [
            '此事能量充沛，上午精力最佳时推进核心步骤',
            '顺势而为，不必强求，水到自然渠成',
            '与人合作时多倾听，贵人运正在路上',
        ],
        'caution': [
            '不要因为太顺利而掉以轻心',
            '注意细节——顺境中反而容易忽略小事',
        ],
    },
    '克': {  # 天气五行克办事五行 → 需谨慎
        'mood': '💪 今日虽有小阻，正是你展现韧性的好时机。',
        'advice': [
            '把关注点放在你能控制的部分，而非结果',
            '多准备一个备选方案，有备无患',
            '遇到阻力时深呼吸——山重水复疑无路，柳暗花明又一村',
        ],
        'caution': [
            '重要决策可推迟到明天再拍板',
            '出行提前出发，给自己多留些时间余地',
            '说话放缓语速，沟通时多确认理解一致',
        ],
    },
    '比': {  # 同五行 → 平稳
        'mood': '🌿 今日能量平和，正是稳步推进的好日子。',
        'advice': [
            '按部就班，把计划中的事一件件完成',
            '适合做需要耐心和细致的工作',
            '午间稍作休息，保持节奏稳定',
        ],
        'caution': [
            '避免贪多——今天适合聚焦在一两件重要的事上',
            '注意身体信号，累了就歇一下',
        ],
    },
}

@dataclass
class FortuneResult:
    date: str
    weather: str
    weather_wuxing: str
    activity: str
    activity_wuxing: str
    hexagram_name: str
    hexagram_symbol: str
    hexagram_meaning: str
    mood: str
    advice: list
    caution: list
    lucky_direction: str
    lucky_element: str
    emotional_message: str


def daily_fortune(weather: str, activity: str, date: datetime = None) -> FortuneResult:
    """
    每日运势

    算法：
    1. 当日卦象 = 六十四卦[年积日 % 64]（纯历法循环，非随机）
    2. 天气 → 五行
    3. 办事 → 五行（关键字匹配）
    4. 生克关系 → 宜忌模板
    5. 生成情绪价值文案
    """
    if date is None:
        date = datetime.now()

    # 当日卦象
    day_of_year = date.timetuple().tm_yday
    hex_idx = day_of_year % 64
    hex_name, hex_sym, hex_meaning = HEXAGRAMS[hex_idx]

    # 天气→五行
    weather_wx = '—'
    for kw, wx in WEATHER_WUXING.items():
        if kw in weather:
            weather_wx = wx
            break

    # 办事→五行
    activity_wx = '—'
    for kw, wx in ACTIVITY_WUXING.items():
        if kw in activity:
            activity_wx = wx
            break

    # 生克关系（五行相生：木火土金水）
    sheng_order = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
    ke_order    = {'木':'土','土':'水','水':'火','火':'金','金':'木'}

    relation = '比'
    if weather_wx != '—' and activity_wx != '—':
        if sheng_order.get(weather_wx) == activity_wx:
            relation = '生'
        elif ke_order.get(weather_wx) == activity_wx:
            relation = '克'
        elif weather_wx == activity_wx:
            relation = '比'

    template = FORTUNE_TEMPLATES.get(relation, FORTUNE_TEMPLATES['比'])

    # 幸运方位（基于卦象爻位）
    directions = ['正东','东南','正南','西南','正西','西北','正北','东北']
    lucky_direction = directions[hex_idx % 8]
    lucky_elements = ['木','火','土','金','水']
    lucky_element = lucky_elements[hex_idx % 5]

    # 情绪价值文案
    emotional_msgs = [
        f'🌅 {hex_name}：{hex_meaning}。今天你做的事，正在为未来铺路。每一步都算数。',
        f'⭐ {hex_name}：{hex_meaning}。相信自己的直觉——你比想象中更有力量。',
        f'🍀 {hex_name}：{hex_meaning}。好的开始是成功的一半，今天就是那个开始。',
        f'🔮 {hex_name}：{hex_meaning}。机会藏在每一个微小的选择里，你今天会看到它。',
        f'💫 {hex_name}：{hex_meaning}。宇宙不会辜负认真生活的人，你今天的努力都值得。',
    ]
    emotional = emotional_msgs[hex_idx % len(emotional_msgs)]

    return FortuneResult(
        date=date.strftime('%Y年%m月%d日'),
        weather=weather, weather_wuxing=weather_wx,
        activity=activity, activity_wuxing=activity_wx,
        hexagram_name=hex_name, hexagram_symbol=hex_sym, hexagram_meaning=hex_meaning,
        mood=template['mood'],
        advice=template['advice'],
        caution=template['caution'],
        lucky_direction=lucky_direction,
        lucky_element=lucky_element,
        emotional_message=emotional,
    )


# ======================== 测试 ========================
if __name__ == '__main__':
    print('=== 解梦测试 ===')
    r = interpret_dream('我梦见在大海里游泳，看到一条大鱼跳出来')
    print(r.interpretation)

    print('\n=== 八字测试 ===')
    b = calculate_bazi(1990, 5, 20, 8)
    print(f'{b.year}年{b.month}月{b.day}日{b.hour}时')
    print(f'年柱：{b.year_gan}{b.year_zhi}  月柱：{b.month_gan}{b.month_zhi}')
    print(f'日柱：{b.day_gan}{b.day_zhi}  时柱：{b.hour_gan}{b.hour_zhi}')
    print(f'生肖：{b.shengxiao}  主导五行：{b.dominant_wuxing}  {b.yinyang_balance}')

    print('\n=== 名字测试 ===')
    n = analyze_name('王浩然')
    if n: print(n.analysis)
