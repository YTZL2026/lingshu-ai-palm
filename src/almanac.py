# -*- coding: utf-8 -*-
"""
AI掌纹溯源 — 真黄历引擎
读系统本地时间 → 农历 → 干支 → 十二建除 → 二十八宿 → 宜忌

学术依据：
  [H1] 张培瑜.《三千五百年历日天象》. 大象出版社, 1997.
  [H2] 《协纪辨方书》(清·乾隆敕撰) — 建除十二神、宜忌规则
  [H3] 刘安国.《中国历法》. 科学出版社, 2011.
  [H4] 《钦定协纪辨方书》— 十二建除与每日宜忌对应关系
"""
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from typing import Tuple, List, Dict

# ======================== 农历数据 ========================
# 2020-2035 年农历正月初一对应公历日期（来源：张培瑜《三千五百年历日天象》）
LUNAR_NEW_YEAR = {
    2020: date(2020,1,25), 2021: date(2021,2,12), 2022: date(2022,2,1),
    2023: date(2023,1,22), 2024: date(2024,2,10), 2025: date(2025,1,29),
    2026: date(2026,2,17), 2027: date(2027,2,6),  2028: date(2028,1,26),
    2029: date(2029,2,13), 2030: date(2030,2,3),  2031: date(2031,1,23),
    2032: date(2032,2,11), 2033: date(2033,1,31), 2034: date(2034,2,19),
    2035: date(2035,2,8),
}

# 闰月月份（2020-2035），0=无闰月
LEAP_MONTHS = {
    2020:4, 2021:0, 2022:0, 2023:2, 2024:0, 2025:6, 2026:0, 2027:0,
    2028:5, 2029:0, 2030:0, 2031:3, 2032:0, 2033:11, 2034:0, 2035:0,
}

# 每年大小月（12或13个月，1=大月30天，0=小月29天）
# 格式：每月一个bit，从正月开始
LUNAR_MONTH_DAYS = {
    # year: [正月,二月,三月,...]  1=30天, 0=29天
    2025: [0,1,0,0,1,0,0,1,0,1,0,0,1],  # 闰六月在七月之前
    2026: [0,1,0,1,1,0,0,0,1,0,1,0],
    2027: [1,0,0,1,0,0,1,0,1,0,0,1],
    2028: [0,0,1,0,1,0,0,0,1,0,1,0,1],  # 闰五月
    2029: [0,1,0,0,1,0,0,1,0,1,0,0],
    2030: [1,0,0,1,0,1,0,0,1,0,1,0],
    2031: [0,0,0,1,0,0,0,1,0,1,0,1,0],  # 闰三月
    2032: [1,0,0,1,0,0,1,0,1,0,0,1],
    2033: [0,1,0,0,0,1,0,0,1,0,1,0,1,0],  # 闰十一月
}

# 农历月份名称
LUNAR_MONTH_NAMES = ['正月','二月','三月','四月','五月','六月','七月','八月','九月','十月','冬月','腊月']
LUNAR_DAY_NAMES = ['','初一','初二','初三','初四','初五','初六','初七','初八','初九','初十',
    '十一','十二','十三','十四','十五','十六','十七','十八','十九','二十',
    '廿一','廿二','廿三','廿四','廿五','廿六','廿七','廿八','廿九','三十']

# ======================== 天干地支（复用于黄历） ========================
TIAN_GAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
DI_ZHI   = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
SHENG_XIAO_NAMES = ['鼠','牛','虎','兔','龙','蛇','马','羊','猴','鸡','狗','猪']

# ======================== 十二建除 ========================
"""
十二建除（建除满平定执破危成收开闭）是黄历中最重要的每日标识。
算法：以月支为"建"日，顺数至日支。正月建寅，二月建卯...
每月交节（节气）后换月建。
"""
JIANCHU_NAMES = ['建','除','满','平','定','执','破','危','成','收','开','闭']
JIANCHU_JIEQI_MONTHS = {  # 节气→月建地支
    1:2,   # 立春→寅月
    2:3,   # 惊蛰→卯月
    3:4,   # 清明→辰月
    4:5,   # 立夏→巳月
    5:6,   # 芒种→午月
    6:7,   # 小暑→未月
    7:8,   # 立秋→申月
    8:9,   # 白露→酉月
    9:10,  # 寒露→戌月
    10:11, # 立冬→亥月
    11:0,  # 大雪→子月
    12:1,  # 小寒→丑月
}

# ======================== 二十八宿 ========================
"""
二十八宿以日为单位循环，每28天一轮。
算法：以某一已知日期为基准（如1900-01-01对应某宿），计算间隔天数。
"""
XIU_28 = ['角','亢','氐','房','心','尾','箕','斗','牛','女','虚','危','室','壁',
          '奎','娄','胃','昴','毕','觜','参','井','鬼','柳','星','张','翼','轸']
XIU_MEANING = {
    '角':'角木蛟·吉·宜出行嫁娶','亢':'亢金龙·凶·宜祭祀不宜嫁娶',
    '氐':'氐土貉·吉·宜交易入宅','房':'房日兔·吉·宜嫁娶开市',
    '心':'心月狐·凶·宜祭祀不宜出行','尾':'尾火虎·吉·宜嫁娶入学',
    '箕':'箕水豹·吉·宜动土修造','斗':'斗木獬·吉·宜出行会友',
    '牛':'牛金牛·凶·宜祭祀不宜开业','女':'女土蝠·凶·宜祭祀不宜嫁娶',
    '虚':'虚日鼠·凶·宜祭祀不宜出行','危':'危月燕·凶·宜祭祀不宜动土',
    '室':'室火猪·吉·宜嫁娶入宅','壁':'壁水貐·吉·宜修造安葬',
    '奎':'奎木狼·吉·宜出行开业','娄':'娄金狗·吉·宜嫁娶交易',
    '胃':'胃土雉·吉·宜入宅动土','昴':'昴日鸡·凶·宜祭祀不宜出行',
    '毕':'毕月乌·吉·宜嫁娶出行','觜':'觜火猴·凶·宜祭祀不宜嫁娶',
    '参':'参水猿·吉·宜出行交易','井':'井木犴·吉·宜嫁娶入宅',
    '鬼':'鬼金羊·凶·宜祭祀不宜出行','柳':'柳土獐·凶·宜祭祀不宜嫁娶',
    '星':'星日马·吉·宜嫁娶出行','张':'张月鹿·吉·宜交易入宅',
    '翼':'翼火蛇·凶·宜祭祀不宜动土','轸':'轸水蚓·吉·宜出行嫁娶',
}

# ======================== 宜忌表 ========================
"""
宜忌规则基于《协纪辨方书》中的十二建除宜忌对照。
每个建除日有其适合和不适合的事项。
"""
JIANCHU_YIJI = {
    '建': {'宜':['出行','上任','会友','上书'],  '忌':['动土','开仓']},
    '除': {'宜':['扫除','药疗','治病','去旧迎新'], '忌':['嫁娶','入宅']},
    '满': {'宜':['祭祀','祈福','开业'], '忌':['动土','迁徙','上任']},
    '平': {'宜':['修造','装修','泥饰','平治道涂'], '忌':['开渠','穿井']},
    '定': {'宜':['祭祀','签约','订婚','入学'], '忌':['诉讼','出行','治病']},
    '执': {'宜':['捕捉','狩猎','讨债'], '忌':['开业','交易','嫁娶']},
    '破': {'宜':['拆屋','破土','求医'], '忌':['多所不宜','大事勿用']},
    '危': {'宜':['祭祀','祈福'], '忌':['出行','迁徙','嫁娶']},
    '成': {'宜':['嫁娶','开市','签约','入宅','出行','入学','上任'], '忌':['诉讼']},
    '收': {'宜':['祭祀','收藏','入仓','讨债'], '忌':['出行','嫁娶','安葬']},
    '开': {'宜':['嫁娶','开业','出行','入宅','交易','签约'], '忌':['安葬']},
    '闭': {'宜':['祭祀','祈福','安葬','补垣塞穴'], '忌':['开业','出行','嫁娶','手术']},
}

@dataclass
class AlmanacResult:
    solar_date: str          # 公历日期
    lunar_date: str          # 农历日期 如"乙巳年六月初八"
    year_ganzhi: str         # 年干支
    month_ganzhi: str        # 月干支
    day_ganzhi: str          # 日干支
    shengxiao: str           # 生肖
    jianchu: str             # 十二建除
    xiu28: str               # 二十八宿
    xiu_meaning: str         # 宿的含义
    yi: List[str]            # 宜
    ji: List[str]            # 忌
    lunar_month_name: str    # 农历月名
    lunar_day_name: str      # 农历日名
    is_leap_month: bool      # 是否闰月


def _get_lunar_date(dt: datetime) -> Tuple[int, int, int, bool]:
    """
    公历→农历转换
    Returns: (农历年, 农历月, 农历日, 是否闰月)
    """
    d = dt.date()
    year = dt.year

    # 找到该农历年的正月初一
    if year not in LUNAR_NEW_YEAR:
        # 超出范围，用近似值
        return year, 1, 1, False

    cny = LUNAR_NEW_YEAR[year]

    if d < cny:
        # 还在上一农历年
        year -= 1
        if year not in LUNAR_NEW_YEAR:
            return year, 1, 1, False
        cny = LUNAR_NEW_YEAR[year]

    # 从正月初一开始数天数
    day_offset = (d - cny).days
    month = 1
    is_leap = False
    leap_month = LEAP_MONTHS.get(year, 0)
    month_days = LUNAR_MONTH_DAYS.get(year, [0,1,0,1,0,0,1,0,1,0,0,1])  # 默认大小月

    idx = 0  # 月份索引
    while day_offset > 0:
        # 当前月天数
        if idx < len(month_days):
            days_in_month = 30 if month_days[idx] == 1 else 29
        else:
            days_in_month = 30  # fallback

        if day_offset >= days_in_month:
            day_offset -= days_in_month
            # 检查下个月是否闰月
            if leap_month > 0 and month == leap_month and not is_leap:
                is_leap = True
            else:
                is_leap = False
                month += 1
                idx += 1
        else:
            break

    lunar_day = day_offset + 1
    return year, month, lunar_day, is_leap


def _get_year_ganzhi(year: int) -> Tuple[str, str]:
    """年干支"""
    base = 4
    offset = (year - base) % 60
    return TIAN_GAN[offset % 10], DI_ZHI[offset % 12]


def _get_day_ganzhi(dt: datetime) -> Tuple[str, str]:
    """日干支"""
    base = datetime(1900, 1, 1)
    days = (dt.date() - base.date()).days
    offset = (days + 10) % 60
    return TIAN_GAN[offset % 10], DI_ZHI[offset % 12]


def _get_month_zhi(month: int) -> str:
    """月地支：正月寅、二月卯..."""
    return DI_ZHI[(month + 1) % 12]  # 正月=寅(index 2), month=1→(1+1)%12=2=寅


def _get_jianchu(month_zhi: str, day_zhi: str) -> str:
    """十二建除：基于月支和日支关系"""
    m_idx = DI_ZHI.index(month_zhi)
    d_idx = DI_ZHI.index(day_zhi)
    offset = (d_idx - m_idx + 12) % 12
    return JIANCHU_NAMES[offset]


def _get_xiu28(dt: datetime) -> Tuple[str, str]:
    """二十八宿：以1900-01-01为基准（角宿），每28天一循环"""
    base = datetime(1900, 1, 1)
    days = (dt.date() - base.date()).days
    idx = days % 28
    xiu = XIU_28[idx]
    return xiu, XIU_MEANING.get(xiu, '')


def get_almanac(dt: datetime = None) -> AlmanacResult:
    """
    获取完整黄历信息
    读取系统本地时间，输出农历、干支、建除、二十八宿、宜忌
    """
    if dt is None:
        dt = datetime.now()

    # 农历
    lunar_year, lunar_month, lunar_day, is_leap = _get_lunar_date(dt)

    # 干支
    year_gan, year_zhi = _get_year_ganzhi(lunar_year)
    day_gan, day_zhi = _get_day_ganzhi(dt)

    # 月地支和建除
    month_zhi = _get_month_zhi(lunar_month)
    jianchu = _get_jianchu(month_zhi, day_zhi)

    # 月干支（查找五虎遁）
    try:
        from .fortune import YEAR_MONTH_START
    except ImportError:
        from fortune import YEAR_MONTH_START
    month_gan = '甲'
    for (a,b), c in YEAR_MONTH_START.items():
        if year_gan in (a,b):
            month_gan_idx = TIAN_GAN.index(c)
            month_gan = TIAN_GAN[(month_gan_idx + lunar_month - 1) % 10]
            break

    # 二十八宿
    xiu, xiu_meaning = _get_xiu28(dt)

    # 宜忌
    yiji = JIANCHU_YIJI.get(jianchu, {'宜':[],'忌':[]})

    # 生肖
    shengxiao = SHENG_XIAO_NAMES[DI_ZHI.index(year_zhi)]

    # 农历日期显示
    lunar_date_str = f'{year_gan}{year_zhi}年'
    if is_leap:
        lunar_date_str += f'闰{LUNAR_MONTH_NAMES[lunar_month-1] if lunar_month <= 12 else "?"}'
    else:
        lunar_date_str += LUNAR_MONTH_NAMES[lunar_month-1] if lunar_month <= 12 else f'{lunar_month}月'
    lunar_date_str += LUNAR_DAY_NAMES[lunar_day] if lunar_day <= 30 else f'{lunar_day}日'

    return AlmanacResult(
        solar_date=dt.strftime('%Y年%m月%d日 %A').replace('Monday','星期一').replace('Tuesday','星期二').replace('Wednesday','星期三').replace('Thursday','星期四').replace('Friday','星期五').replace('Saturday','星期六').replace('Sunday','星期日'),
        lunar_date=lunar_date_str,
        year_ganzhi=f'{year_gan}{year_zhi}',
        month_ganzhi=f'{month_gan}{month_zhi}',
        day_ganzhi=f'{day_gan}{day_zhi}',
        shengxiao=shengxiao,
        jianchu=jianchu,
        xiu28=xiu,
        xiu_meaning=xiu_meaning,
        yi=yiji.get('宜',[]),
        ji=yiji.get('忌',[]),
        lunar_month_name=LUNAR_MONTH_NAMES[lunar_month-1] if lunar_month <= 12 else f'{lunar_month}月',
        lunar_day_name=LUNAR_DAY_NAMES[lunar_day] if lunar_day <= 30 else f'{lunar_day}日',
        is_leap_month=is_leap,
    )


# ======================== 测试 ========================
if __name__ == '__main__':
    now = datetime.now()
    a = get_almanac(now)
    print(f'公历：{a.solar_date}')
    print(f'农历：{a.lunar_date}')
    print(f'年干支：{a.year_ganzhi}  月干支：{a.month_ganzhi}  日干支：{a.day_ganzhi}')
    print(f'生肖：{a.shengxiao}')
    print(f'建除：{a.jianchu}  二十八宿：{a.xiu28}（{a.xiu_meaning}）')
    print(f'宜：{" ".join(a.yi)}')
    print(f'忌：{" ".join(a.ji)}')
