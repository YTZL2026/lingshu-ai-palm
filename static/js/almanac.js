// ============================================
// 灵枢 — 黄历引擎 (JavaScript)
// 农历 · 干支 · 十二建除 · 二十八宿 · 宜忌
// 移植自 src/almanac.py
// ============================================

const TIAN_GAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'];
const DI_ZHI   = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];
const SHENG_XIAO = ['鼠','牛','虎','兔','龙','蛇','马','羊','猴','鸡','狗','猪'];

// 2020-2035 农历正月初一对应公历
const LUNAR_NEW_YEAR = {
  2020: [2020,1,25], 2021: [2021,2,12], 2022: [2022,2,1],
  2023: [2023,1,22], 2024: [2024,2,10], 2025: [2025,1,29],
  2026: [2026,2,17], 2027: [2027,2,6],  2028: [2028,1,26],
  2029: [2029,2,13], 2030: [2030,2,3],  2031: [2031,1,23],
  2032: [2032,2,11], 2033: [2033,1,31], 2034: [2034,2,19],
  2035: [2035,2,8],
};

// 闰月月份
const LEAP_MONTHS = {
  2020:4, 2021:0, 2022:0, 2023:2, 2024:0, 2025:6, 2026:0, 2027:0,
  2028:5, 2029:0, 2030:0, 2031:3, 2032:0, 2033:11, 2034:0, 2035:0,
};

// 农历大小月: 1=大月30天, 0=小月29天
const LUNAR_MONTH_DAYS = {
  2025: [0,1,0,0,1,0,0,1,0,1,0,0,1],
  2026: [0,1,0,1,1,0,0,0,1,0,1,0],
  2027: [1,0,0,1,0,0,1,0,1,0,0,1],
  2028: [0,0,1,0,1,0,0,0,1,0,1,0,1],
  2029: [0,1,0,0,1,0,0,1,0,1,0,0],
  2030: [1,0,0,1,0,1,0,0,1,0,1,0],
  2031: [0,0,0,1,0,0,0,1,0,1,0,1,0],
  2032: [1,0,0,1,0,0,1,0,1,0,0,1],
  2033: [0,1,0,0,0,1,0,0,1,0,1,0,1,0],
};

const LUNAR_MONTH_NAMES = ['正月','二月','三月','四月','五月','六月','七月','八月','九月','十月','冬月','腊月'];
const LUNAR_DAY_NAMES = ['','初一','初二','初三','初四','初五','初六','初七','初八','初九','初十',
  '十一','十二','十三','十四','十五','十六','十七','十八','十九','二十',
  '廿一','廿二','廿三','廿四','廿五','廿六','廿七','廿八','廿九','三十'];

const JIANCHU_NAMES = ['建','除','满','平','定','执','破','危','成','收','开','闭'];

const XIU_28 = ['角','亢','氐','房','心','尾','箕','斗','牛','女','虚','危','室','壁',
  '奎','娄','胃','昴','毕','觜','参','井','鬼','柳','星','张','翼','轸'];

const XIU_MEANING = {
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
};

const JIANCHU_YIJI = {
  '建': {yi:['出行','上任','会友','上书'], ji:['动土','开仓']},
  '除': {yi:['扫除','药疗','治病','去旧迎新'], ji:['嫁娶','入宅']},
  '满': {yi:['祭祀','祈福','开业'], ji:['动土','迁徙','上任']},
  '平': {yi:['修造','装修','泥饰','平治道涂'], ji:['开渠','穿井']},
  '定': {yi:['祭祀','签约','订婚','入学'], ji:['诉讼','出行','治病']},
  '执': {yi:['捕捉','狩猎','讨债'], ji:['开业','交易','嫁娶']},
  '破': {yi:['拆屋','破土','求医'], ji:['多所不宜','大事勿用']},
  '危': {yi:['祭祀','祈福'], ji:['出行','迁徙','嫁娶']},
  '成': {yi:['嫁娶','开市','签约','入宅','出行','入学','上任'], ji:['诉讼']},
  '收': {yi:['祭祀','收藏','入仓','讨债'], ji:['出行','嫁娶','安葬']},
  '开': {yi:['嫁娶','开业','出行','入宅','交易','签约'], ji:['安葬']},
  '闭': {yi:['祭祀','祈福','安葬','补垣塞穴'], ji:['开业','出行','嫁娶','手术']},
};

// 年天干→月天干起始（五虎遁）
const YUE_START_MAP = { '甲':'丙','己':'丙', '乙':'戊','庚':'戊', '丙':'庚','辛':'庚', '丁':'壬','壬':'壬', '戊':'甲','癸':'甲' };

function dateDiff(baseY, baseM, baseD, y, m, d) {
  const b = new Date(baseY, baseM - 1, baseD);
  const t = new Date(y, m - 1, d);
  return Math.round((t - b) / 86400000);
}

// ======================== 农历转换 ========================
function getLunarDate(y, m, d) {
  const dt = new Date(y, m - 1, d);
  let ly = y, lm = 1, ld = 1, isLeap = false;

  const cnyKey = ly in LUNAR_NEW_YEAR ? ly : (ly - 1 in LUNAR_NEW_YEAR ? ly - 1 : Object.keys(LUNAR_NEW_YEAR)[0]);
  let cny = LUNAR_NEW_YEAR[cnyKey];
  let cnyDate = new Date(cny[0], cny[1] - 1, cny[2]);

  if (dt < cnyDate) {
    ly = ly - 1;
    if (ly in LUNAR_NEW_YEAR) {
      cny = LUNAR_NEW_YEAR[ly];
      cnyDate = new Date(cny[0], cny[1] - 1, cny[2]);
    }
  }

  let dayOffset = Math.floor((dt - cnyDate) / 86400000);
  let monthDays = LUNAR_MONTH_DAYS[ly] || [0,1,0,1,0,0,1,0,1,0,0,1];
  let leapMonth = LEAP_MONTHS[ly] || 0;
  let idx = 0;

  while (dayOffset > 0) {
    let dim = (idx < monthDays.length && monthDays[idx] === 1) ? 30 : 29;
    if (dayOffset >= dim) {
      dayOffset -= dim;
      if (leapMonth > 0 && lm === leapMonth && !isLeap) {
        isLeap = true;
      } else {
        isLeap = false;
        lm++;
        idx++;
      }
    } else {
      break;
    }
  }

  ld = dayOffset + 1;
  return { year: ly, month: lm, day: ld, isLeap };
}

// ======================== 干支计算 ========================
function getYearGanzhi(year) {
  const offset = (year - 4) % 60;
  return { gan: TIAN_GAN[offset % 10], zhi: DI_ZHI[offset % 12] };
}

function getDayGanzhi(y, m, d) {
  const days = dateDiff(1900, 1, 1, y, m, d);
  const offset = (days + 10) % 60;
  return { gan: TIAN_GAN[offset % 10], zhi: DI_ZHI[offset % 12] };
}

function getMonthZhi(month) {
  return DI_ZHI[(month + 1) % 12];
}

function getJianchu(monthZhi, dayZhi) {
  const mi = DI_ZHI.indexOf(monthZhi);
  const di = DI_ZHI.indexOf(dayZhi);
  return JIANCHU_NAMES[(di - mi + 12) % 12];
}

function getXiu28(y, m, d) {
  const days = dateDiff(1900, 1, 1, y, m, d);
  const xiu = XIU_28[days % 28];
  return { name: xiu, meaning: XIU_MEANING[xiu] || '' };
}

function getMonthGan(yearGan, lunarMonth) {
  const startGan = YUE_START_MAP[yearGan] || '甲';
  return TIAN_GAN[(TIAN_GAN.indexOf(startGan) + lunarMonth - 1) % 10];
}

function getWeekdayCN(y, m, d) {
  const names = ['星期日','星期一','星期二','星期三','星期四','星期五','星期六'];
  return names[new Date(y, m - 1, d).getDay()];
}

// ======================== 主入口 ========================
function getAlmanac(date) {
  if (!date) date = new Date();
  const y = date.getFullYear();
  const m = date.getMonth() + 1;
  const d = date.getDate();

  const lunar = getLunarDate(y, m, d);
  const yearGz = getYearGanzhi(lunar.year);
  const dayGz = getDayGanzhi(y, m, d);
  const monthZhi = getMonthZhi(lunar.month);
  const monthGan = getMonthGan(yearGz.gan, lunar.month);
  const jianchu = getJianchu(monthZhi, dayGz.zhi);
  const xiu = getXiu28(y, m, d);
  const yiji = JIANCHU_YIJI[jianchu] || {yi:[],ji:[]};
  const shengxiao = SHENG_XIAO[DI_ZHI.indexOf(yearGz.zhi)];

  let lunarStr = `${yearGz.gan}${yearGz.zhi}年`;
  if (lunar.isLeap) lunarStr += '闰';
  lunarStr += LUNAR_MONTH_NAMES[lunar.month - 1] || `${lunar.month}月`;
  lunarStr += LUNAR_DAY_NAMES[lunar.day] || `${lunar.day}日`;

  return {
    solar_date: `${y}年${String(m).padStart(2,'0')}月${String(d).padStart(2,'0')}日 ${getWeekdayCN(y,m,d)}`,
    lunar_date: lunarStr,
    year_ganzhi: `${yearGz.gan}${yearGz.zhi}`,
    month_ganzhi: `${monthGan}${monthZhi}`,
    day_ganzhi: `${dayGz.gan}${dayGz.zhi}`,
    shengxiao,
    jianchu,
    xiu28: xiu.name,
    xiu_meaning: xiu.meaning,
    yi: yiji.yi || [],
    ji: yiji.ji || [],
    lunar_month_name: LUNAR_MONTH_NAMES[lunar.month - 1] || '',
    lunar_day_name: LUNAR_DAY_NAMES[lunar.day] || '',
    is_leap_month: lunar.isLeap,
  };
}

// Almanac engine is ready
console.log('📅 黄历引擎就绪 (almanac.js)');
