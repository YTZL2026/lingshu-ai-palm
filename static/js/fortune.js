// ============================================
// 灵枢 — 传统术数引擎 (JavaScript)
// 解梦 · 八字 · 每日运势 · 名字测算
// 移植自 src/fortune.py
// ============================================

// ======================== 一、解梦引擎 ========================
const DREAM_DICT = {
  '水': {category:'肾',element:'水',meaning:'大水主财。水流清澈则运势亨通，浊水则有口舌是非。'},
  '河': {category:'肾',element:'水',meaning:'江河象征人生之流。过河顺利则困难将解。'},
  '雨': {category:'肾',element:'水',meaning:'甘霖主吉。春雨贵如油，风雨交加则需注意情绪调节。'},
  '海': {category:'肾',element:'水',meaning:'大海象征胸襟。风平浪静主安宁，波涛汹涌主心神不宁。'},
  '鱼': {category:'肾',element:'水',meaning:'鱼谐音"余"，主富贵有余。鱼游水中则财运亨通。'},
  '船': {category:'肾',element:'水',meaning:'舟行水上，一帆风顺则事情进展顺利。'},
  '游泳': {category:'肾',element:'水',meaning:'自在游弋主身心舒畅。逆流而泳则正面临挑战。'},
  '溺水': {category:'肾',element:'水',meaning:'沉溺感常反映现实压力过大，需注意肾气调养。'},
  '火': {category:'心',element:'火',meaning:'火主名声。火焰旺盛主事业兴旺，火灾则需防口舌是非。'},
  '太阳': {category:'心',element:'火',meaning:'旭日东升主新的开始。阳光普照主贵人相助。'},
  '灯': {category:'心',element:'火',meaning:'明灯主智慧开悟。灯火昏暗则心有疑虑。'},
  '红色': {category:'心',element:'火',meaning:'赤色属火，主喜庆。梦见红色预示好事将近。'},
  '战争': {category:'心',element:'火',meaning:'争斗之梦反映内心冲突。心火过旺则易怒多梦。'},
  '树': {category:'肝',element:'木',meaning:'树木象征生机。枝繁叶茂主运势昌盛。'},
  '花': {category:'肝',element:'木',meaning:'开花主喜庆。花落则需珍惜当下。肝气舒畅则梦花开。'},
  '草': {category:'肝',element:'木',meaning:'绿草如茵主健康。草枯则需注意调养。'},
  '森林': {category:'肝',element:'木',meaning:'茂林象征生机勃勃。迷路林中则暗示方向未明。'},
  '蛇': {category:'肝',element:'木',meaning:'蛇在中医属肝。蛇蜕皮主新生蜕变。'},
  '山': {category:'脾',element:'土',meaning:'登山主志向高远。山崩则需注意脾胃调养。'},
  '土': {category:'脾',element:'土',meaning:'土地主根基。沃土主财运稳固。坤土厚德载物。'},
  '房子': {category:'脾',element:'土',meaning:'房屋象征安全感。新房主新开始。'},
  '食物': {category:'脾',element:'土',meaning:'美食主满足。饥饿则需补养脾胃。'},
  '田地': {category:'脾',element:'土',meaning:'良田主收获。耕耘之梦暗示付出将有回报。'},
  '金属': {category:'肺',element:'金',meaning:'金石主坚毅。金银主财富。'},
  '钱': {category:'肺',element:'金',meaning:'钱财之梦反映现实忧虑。得财主机遇。'},
  '刀': {category:'肺',element:'金',meaning:'利器之梦主决断。持刀自卫则有底气。'},
  '白色': {category:'肺',element:'金',meaning:'素色属金。梦见白色主纯净。'},
  '飞': {category:'心',element:'火',meaning:'飞翔主自由。飞得高则志向远大。'},
  '坠落': {category:'肾',element:'水',meaning:'坠落感常见于入睡肌抽跃，中医属肾水不济。'},
  '考试': {category:'心',element:'火',meaning:'应试之梦反映焦虑。顺利通过则自信。'},
  '死亡': {category:'肾',element:'水',meaning:'梦见死亡多主"新生"——旧阶段结束，新开始。'},
  '牙齿': {category:'肾',element:'水',meaning:'齿为骨之余，肾主骨。梦见掉牙需注意肾气。'},
  '追赶': {category:'肝',element:'木',meaning:'被追之梦反映逃避心理。肝气郁结易做追逐之梦。'},
  '孩子': {category:'心',element:'火',meaning:'孩童主纯真。梦见孩子多主喜事将近。'},
  '老人': {category:'脾',element:'土',meaning:'长者主智慧。梦见已故亲人则多思念所致。'},
  '结婚': {category:'心',element:'火',meaning:'婚庆主喜。单身者梦婚主新缘。'},
  '裸体': {category:'肺',element:'金',meaning:'赤身之梦主坦诚。不自在则暗示有隐藏之事。'},
};

function interpretDream(dreamText) {
  const matched = [];
  for (const [keyword, info] of Object.entries(DREAM_DICT)) {
    if (dreamText.includes(keyword)) {
      matched.push({keyword, ...info});
    }
  }

  if (matched.length === 0) {
    return {
      dream_text: dreamText,
      matched_keywords: [],
      dominant_element: '—',
      dominant_organ: '—',
      interpretation: '此梦境意象独特，建议关注近期情绪变化。《灵枢》云：正邪从外袭内，未有定舍，反淫于脏，不得定处，与营卫俱行，而与魂魄飞扬，使人卧不得安而喜梦。'
    };
  }

  const elemCount = {}, organCount = {};
  for (const m of matched) {
    elemCount[m.element] = (elemCount[m.element]||0) + 1;
    organCount[m.organ] = (organCount[m.organ]||0) + 1;
  }
  const dominantElem = Object.keys(elemCount).sort((a,b)=>elemCount[b]-elemCount[a])[0];
  const dominantOrgan = Object.keys(organCount).sort((a,b)=>organCount[b]-organCount[a])[0];

  const elemNames = {木:'肝木',火:'心火',土:'脾土',金:'肺金',水:'肾水'};
  const parts = [`梦境共匹配到${matched.length}个传统意象：`];
  for (const m of matched.slice(0,5)) {
    parts.push(`·「${m.keyword}」— ${m.meaning}`);
  }
  parts.push('');
  parts.push(`五行倾向：${dominantElem}（${elemNames[dominantElem]||''}），建议关注${dominantOrgan}经调养。`);

  return {
    dream_text: dreamText,
    matched_keywords: matched,
    dominant_element: dominantElem,
    dominant_organ: dominantOrgan,
    interpretation: parts.join('\n'),
  };
}

// ======================== 二、八字排盘 ========================
const GAN_WUXING = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'};
const ZHI_WUXING = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'};
const GAN_YINYANG = {'甲':'阳','乙':'阴','丙':'阳','丁':'阴','戊':'阳','己':'阴','庚':'阳','辛':'阴','壬':'阳','癸':'阴'};

function calcYearGanzhi(year) {
  const offset = (year - 4) % 60;
  return { gan: TIAN_GAN[offset%10], zhi: DI_ZHI[offset%12] };
}

function calcMonthGanzhi(yearGan, month) {
  const startMap = {'甲':'丙','己':'丙','乙':'戊','庚':'戊','丙':'庚','辛':'庚','丁':'壬','壬':'壬','戊':'甲','癸':'甲'};
  const startGan = startMap[yearGan] || '甲';
  const gan = TIAN_GAN[(TIAN_GAN.indexOf(startGan) + month - 1) % 10];
  const zhi = DI_ZHI[(month + 1) % 12];
  return { gan, zhi };
}

function calcDayGanzhi(y, m, d) {
  const base = new Date(1900, 0, 1);
  const target = new Date(y, m - 1, d);
  const days = Math.round((target - base) / 86400000);
  const offset = (days + 10) % 60;
  return { gan: TIAN_GAN[offset%10], zhi: DI_ZHI[offset%12] };
}

function calcHourGanzhi(dayGan, hour) {
  const startMap = {'甲':'甲','己':'甲','乙':'丙','庚':'丙','丙':'戊','辛':'戊','丁':'庚','壬':'庚','戊':'壬','癸':'壬'};
  const startGan = startMap[dayGan] || '甲';
  const zhiIdx = Math.floor((hour + 1) / 2) % 12;
  const gan = TIAN_GAN[(TIAN_GAN.indexOf(startGan) + zhiIdx) % 10];
  return { gan, zhi: DI_ZHI[zhiIdx] };
}

function calculateBazi(year, month, day, hour) {
  if (!hour) hour = 12;
  const yGz = calcYearGanzhi(year);
  const mGz = calcMonthGanzhi(yGz.gan, month);
  const dGz = calcDayGanzhi(year, month, day);
  const hGz = calcHourGanzhi(dGz.gan, hour);

  const wxCount = {金:0,木:0,水:0,火:0,土:0};
  for (const g of [yGz.gan, mGz.gan, dGz.gan, hGz.gan]) {
    const w = GAN_WUXING[g]; if (w in wxCount) wxCount[w]++;
  }
  for (const z of [yGz.zhi, mGz.zhi, dGz.zhi, hGz.zhi]) {
    const w = ZHI_WUXING[z]; if (w in wxCount) wxCount[w]++;
  }
  const dominantWx = Object.keys(wxCount).sort((a,b)=>wxCount[b]-wxCount[a])[0];

  let yinCount = 0;
  for (const g of [yGz.gan, mGz.gan, dGz.gan, hGz.gan]) {
    if (GAN_YINYANG[g] === '阴') yinCount++;
  }
  const yangCount = 4 - yinCount;
  let yinyangBal;
  if (yinCount === yangCount) yinyangBal = '阴阳平衡（2阴2阳）';
  else if (Math.abs(yinCount - yangCount) === 1) yinyangBal = `阴阳略偏（${yinCount}阴${yangCount}阳），基本平衡`;
  else if (yinCount > yangCount) yinyangBal = `偏阴性（${yinCount}阴${yangCount}阳），宜补阳气`;
  else yinyangBal = `偏阳性（${yinCount}阴${yangCount}阳），宜滋阴涵养`;

  return {
    year_gan: yGz.gan, year_zhi: yGz.zhi,
    month_gan: mGz.gan, month_zhi: mGz.zhi,
    day_gan: dGz.gan, day_zhi: dGz.zhi,
    hour_gan: hGz.gan, hour_zhi: hGz.zhi,
    shengxiao: SHENG_XIAO[DI_ZHI.indexOf(yGz.zhi)],
    wuxing_count: wxCount,
    dominant_wuxing: dominantWx,
    yinyang_balance: yinyangBal,
  };
}

// ======================== 三、每日运势 ========================
const HEXAGRAMS = [
  ['乾为天','☰☰','刚健中正，自强不息'],['坤为地','☷☷','柔顺承载，厚德载物'],
  ['水雷屯','☵☳','万物初生，耐心待时'],['山水蒙','☶☵','启蒙开智，循序渐进'],
  ['水天需','☵☰','待时而动，静候佳音'],['天水讼','☰☵','慎言慎行，以和为贵'],
  ['地水师','☷☵','行之以正，师出有名'],['水地比','☵☷','亲附和合，众志成城'],
  ['风天小畜','☴☰','小有所成，积蓄力量'],['天泽履','☰☱','脚踏实地，谨言慎行'],
  ['地天泰','☷☰','天地交泰，万事亨通'],['天地否','☰☷','否极泰来，守正待时'],
  ['天火同人','☰☲','志同道合，同心协力'],['火天大有','☲☰','丰盛富足，大有收获'],
  ['地山谦','☷☶','谦虚受益，满招损谦'],['雷地豫','☳☷','愉悦和乐，顺势而动'],
  ['泽雷随','☱☳','随遇而安，灵活应变'],['山风蛊','☶☴','革故鼎新，拨乱反正'],
  ['地泽临','☷☱','居高临下，亲临其事'],['风地观','☴☷','观察入微，洞悉先机'],
  ['火雷噬嗑','☲☳','明断是非，公正果断'],['山火贲','☶☲','文饰修饰，表里如一'],
  ['山地剥','☶☷','剥落旧习，去伪存真'],['地雷复','☷☳','一阳来复，否极泰来'],
  ['天雷无妄','☰☳','真实无妄，顺其自然'],['山天大畜','☶☰','厚积薄发，大有所畜'],
  ['山雷颐','☶☳','颐养天年，修身养性'],['泽风大过','☱☴','大过之时，独立不惧'],
  ['坎为水','☵☵','处险不惊，以诚相待'],['离为火','☲☲','光明正大，虚明照物'],
  ['泽山咸','☱☶','感应互通，心有灵犀'],['雷风恒','☳☴','持之以恒，日久见功'],
  ['天山遁','☰☶','功成身退，见机而作'],['雷天大壮','☳☰','强健有力，顺势而上'],
  ['火地晋','☲☷','旭日东升，前程似锦'],['地火明夷','☷☲','晦而转明，韬光养晦'],
  ['风火家人','☴☲','家宅安宁，和睦温馨'],['火泽睽','☲☱','求同存异，和而不同'],
  ['水山蹇','☵☶','知难而进，不畏险阻'],['雷水解','☳☵','难题化解，雨过天晴'],
  ['山泽损','☶☱','损己利人，有舍有得'],['风雷益','☴☳','增益其所不能，日益精进'],
  ['泽天夬','☱☰','果断决策，当机立断'],['天风姤','☰☴','不期而遇，随缘而安'],
  ['泽地萃','☱☷','群英荟萃，人才汇聚'],['地风升','☷☴','步步高升，渐入佳境'],
  ['泽水困','☱☵','困而知之，守正破局'],['水风井','☵☴','井然有序，按部就班'],
  ['泽火革','☱☲','革故鼎新，顺势而变'],['火风鼎','☲☴','一言九鼎，诚信为本'],
  ['震为雷','☳☳','震而动之，一鸣惊人'],['艮为山','☶☶','知止不殆，适可而止'],
  ['风山渐','☴☶','循序渐进，水到渠成'],['雷泽归妹','☳☱','缘分天定，和合之美'],
  ['雷火丰','☳☲','丰盛盈满，知足常乐'],['火山旅','☲☶','行旅在外，处处皆景'],
  ['巽为风','☴☴','柔顺和畅，如沐春风'],['兑为泽','☱☱','喜悦和悦，惠风和畅'],
  ['风水涣','☴☵','涣然冰释，烦恼消散'],['水泽节','☵☱','节制有度，过犹不及'],
  ['风泽中孚','☴☱','诚实守信，以诚待人'],['雷山小过','☳☶','小有过之，知过能改'],
  ['水火既济','☵☲','事已成就，善始善终'],['火水未济','☲☵','未竟之事，前途光明'],
];

const WEATHER_WUXING = {
  '晴':'火','晴天':'火','热':'火','高温':'火','太阳':'火',
  '雨':'水','下雨':'水','暴雨':'水','阵雨':'水','雷雨':'水',
  '阴':'土','阴天':'土','多云':'土','雾':'土','霾':'土',
  '风':'木','大风':'木','台风':'木','微风':'木',
  '雪':'金','下雪':'金','冰雹':'金','冷':'金',
};

const ACTIVITY_WUXING = {
  '开会':'火','谈判':'金','签约':'金','面试':'火','考试':'火',
  '演讲':'火','报告':'火','出差':'木','旅行':'木','搬家':'土',
  '买房':'土','装修':'土','投资':'金','理财':'金','借钱':'水',
  '看病':'水','体检':'水','运动':'木','健身':'木','跑步':'木',
  '约会':'火','相亲':'火','求婚':'金','结婚':'火','聚会':'火',
  '购物':'金','逛街':'木','开车':'水','坐车':'水','出行':'木',
  '上班':'土','工作':'土','辞职':'木','创业':'木','学习':'火',
  '读书':'火','写作':'火','创作':'火','设计':'木',
  '沟通':'金','协调':'金','调解':'水','仲裁':'金','决策':'火',
};

const FORTUNE_TEMPLATES = {
  '生': {
    mood: '✨ 今日气场与你所求之事相生，宜顺势而为。',
    advice: ['此事能量充沛，上午精力最佳时推进核心步骤','顺势而为，不必强求，水到自然渠成','与人合作时多倾听，贵人运正在路上'],
    caution: ['不要因为太顺利而掉以轻心','注意细节——顺境中反而容易忽略小事'],
  },
  '克': {
    mood: '💪 今日虽有小阻，正是你展现韧性的好时机。',
    advice: ['把关注点放在你能控制的部分，而非结果','多准备一个备选方案，有备无患','遇到阻力时深呼吸——山重水复疑无路，柳暗花明又一村'],
    caution: ['重要决策可推迟到明天再拍板','出行提前出发，给自己多留些时间余地','说话放缓语速，沟通时多确认理解一致'],
  },
  '比': {
    mood: '🌿 今日能量平和，正是稳步推进的好日子。',
    advice: ['按部就班，把计划中的事一件件完成','适合做需要耐心和细致的工作','午间稍作休息，保持节奏稳定'],
    caution: ['避免贪多——今天适合聚焦在一两件重要的事上','注意身体信号，累了就歇一下'],
  },
};

function dailyFortune(weather, activity, date) {
  if (!date) date = new Date();

  const dayOfYear = Math.floor((date - new Date(date.getFullYear(), 0, 0)) / 86400000);
  const hexIdx = dayOfYear % 64;
  const [hexName, hexSym, hexMeaning] = HEXAGRAMS[hexIdx];

  let weatherWx = '—';
  for (const [kw, wx] of Object.entries(WEATHER_WUXING)) {
    if (weather.includes(kw)) { weatherWx = wx; break; }
  }

  let activityWx = '—';
  for (const [kw, wx] of Object.entries(ACTIVITY_WUXING)) {
    if (activity.includes(kw)) { activityWx = wx; break; }
  }

  const shengOrder = {木:'火',火:'土',土:'金',金:'水',水:'木'};
  const keOrder = {木:'土',土:'水',水:'火',火:'金',金:'木'};
  let relation = '比';
  if (weatherWx !== '—' && activityWx !== '—') {
    if (shengOrder[weatherWx] === activityWx) relation = '生';
    else if (keOrder[weatherWx] === activityWx) relation = '克';
    else if (weatherWx === activityWx) relation = '比';
  }

  const template = FORTUNE_TEMPLATES[relation] || FORTUNE_TEMPLATES['比'];
  const directions = ['正东','东南','正南','西南','正西','西北','正北','东北'];
  const elements = ['木','火','土','金','水'];

  const emotionalMsgs = [
    `🌅 ${hexName}：${hexMeaning}。今天你做的事，正在为未来铺路。每一步都算数。`,
    `⭐ ${hexName}：${hexMeaning}。相信自己的直觉——你比想象中更有力量。`,
    `🍀 ${hexName}：${hexMeaning}。好的开始是成功的一半，今天就是那个开始。`,
    `🔮 ${hexName}：${hexMeaning}。机会藏在每一个微小的选择里，你今天会看到它。`,
    `💫 ${hexName}：${hexMeaning}。宇宙不会辜负认真生活的人，你今天的努力都值得。`,
  ];

  return {
    date: `${date.getFullYear()}年${date.getMonth()+1}月${date.getDate()}日`,
    weather, weather_wuxing: weatherWx,
    activity, activity_wuxing: activityWx,
    hexagram_name: hexName, hexagram_symbol: hexSym, hexagram_meaning: hexMeaning,
    mood: template.mood,
    advice: template.advice,
    caution: template.caution,
    lucky_direction: directions[hexIdx % 8],
    lucky_element: elements[hexIdx % 5],
    emotional_message: emotionalMsgs[hexIdx % emotionalMsgs.length],
  };
}

// ======================== 四、名字测算 ========================
const KANGXI_STROKES = {
  '一':1,'乙':1,'二':2,'人':2,'入':2,'八':2,'刀':2,'力':2,'十':2,'又':2,
  '三':3,'下':3,'大':3,'女':3,'子':3,'山':3,'川':3,'工':3,'己':3,'土':3,
  '四':4,'不':4,'中':4,'丹':4,'之':4,'予':4,'云':4,'仁':4,'今':4,'元':4,
  '五':5,'世':5,'主':5,'以':5,'冬':5,'功':5,'北':5,'可':5,'右':5,'司':5,
  '六':6,'亦':6,'仰':6,'仲':6,'任':6,'先':6,'光':6,'全':6,'冰':6,'宇':6,'安':6,'州':6,'年':6,
  '七':7,'伯':7,'伶':7,'佑':7,'何':7,'余':7,'作':7,'克':7,'冶':7,'初':7,'利':7,'君':7,'吟':7,
  '八':8,'佳':8,'佩':8,'依':8,'其':8,'卓':8,'叔':8,'坤':8,'坦':8,'坪':8,'尚':8,'岳':8,'幸':8,
  '九':9,'信':9,'冠':9,'亭':9,'俐':9,'俞':9,'俊':9,'品':9,'奕':9,'妍':9,'建':9,'彦':9,'思':9,
  '十':10,'倩':10,'修':10,'刚':10,'哲':10,'唐':10,'娟':10,'家':10,'峰':10,'峻':10,'庭':10,'恩':10,'恬':10,
  '健':11,'伟':11,'婉':11,'崇':11,'唯':11,'国':11,'堂':11,'培':11,'基':11,'媛':11,'富':11,'尧':11,'岚':11,
  '杰':12,'凯':12,'勋':12,'胜':12,'博':12,'善':12,'喜':12,'乔':12,'晴':12,'智':12,'景':12,'皓':12,
  '敬':13,'新':13,'晖':13,'暖':13,'业':13,'楷':13,'瑜':13,'瑞':13,'熙':13,'畅':13,'群':13,'义':13,'圣':13,
  '宁':14,'嘉':14,'豪':14,'语':14,'诚':14,'铭':14,'凤':14,'齐':14,'瑄':14,'玮':14,'荣':14,'汉':14,'维':14,
  '慧':15,'磊':15,'萱':15,'莹':15,'庆':15,'乐':15,'毅':15,'洁':15,'德':15,'娴':15,'宽':15,'墨':15,'震':15,
  '学':16,'晓':16,'桦':16,'树':16,'燕':16,'霖':16,'翰':16,'儒':16,'兴':16,'龙':16,'衡':16,'谋':16,'羲':16,
  '励':17,'泽':17,'谦':17,'鸿':17,'黛':17,'阳':17,'蔓':17,'灿':17,'隆':17,'聪':17,'声':17,'孺':17,
  '礼':18,'丰':18,'曜':18,'蕊':18,'翘':18,'馥':18,'颜':18,'谨':18,'双':18,
  '鹏':19,'丽':19,'龄':19,'麒':19,'麓':19,'瀚':19,'怀':19,'韵':19,
  '宝':20,'曦':20,'兰':20,'献':20,'耀':20,'赢':20,'严':20,'飘':20,
  '艺':21,'鹤':21,'莺':21,'樱':21,'巍':21,
  '懿':22,'权':22,'鉴':22,'骅':22,'龚':22,
  '麟':23,'燕':23,'鑫':24,'灵':24,'鹰':24,
};

const HANZI_WUXING = {
  '林':'木','森':'木','树':'木','松':'木','柏':'木','柳':'木','梅':'木',
  '花':'木','芳':'木','芝':'木','兰':'木','荷':'木','菊':'木','莲':'木',
  '禾':'木','季':'木','秀':'木','秉':'木','科':'木','东':'木','春':'木','青':'木','生':'木','仁':'木',
  '火':'火','炎':'火','灵':'火','智':'火','明':'火','昭':'火','旭':'火','晋':'火',
  '日':'火','阳':'火','光':'火','辉':'火','耀':'火',
  '心':'火','思':'火','恩':'火','惠':'火','德':'火','志':'火','忠':'火',
  '南':'火','夏':'火','红':'火','丹':'火','彤':'火','紫':'火',
  '土':'土','坤':'土','坦':'土','培':'土','基':'土','城':'土','坚':'土',
  '山':'土','岳':'土','峰':'土','峻':'土','岩':'土','崇':'土','岚':'土',
  '石':'土','磊':'土','硕':'土','碧':'土','砚':'土',
  '中':'土','央':'土','玉':'土','珍':'土','珠':'土','瑞':'土','琪':'土','琳':'土','瑶':'土',
  '金':'金','鑫':'金','钰':'金','铭':'金','锐':'金','钧':'金','锋':'金','锦':'金',
  '西':'金','秋':'金','白':'金','素':'金','利':'金','刚':'金','剑':'金','创':'金','则':'金','新':'金','辛':'金','辞':'金',
  '水':'水','冰':'水','淼':'水','永':'水',
  '江':'水','河':'水','海':'水','洋':'水','泽':'水','鸿':'水','浩':'水','涵':'水',
  '雨':'水','雪':'水','云':'水','雯':'水','霖':'水','霞':'水','露':'水','霏':'水',
  '北':'水','冬':'水','黑':'水','墨':'水',
  '文':'水','学':'水','博':'水','渊':'水','源':'水','清':'水','洁':'水',
};

function getStroke(ch) {
  return KANGXI_STROKES[ch] || Math.max(1, Math.ceil(ch.length * 3));
}

function getWuxing(ch) {
  return HANZI_WUXING[ch] || '—';
}

function wugeWuxing(stroke) {
  const r = stroke % 10;
  if (r === 1 || r === 2) return '木';
  if (r === 3 || r === 4) return '火';
  if (r === 5 || r === 6) return '土';
  if (r === 7 || r === 8) return '金';
  return '水';
}

function analyzeName(nameStr) {
  if (!nameStr || nameStr.length < 2) return null;
  const surname = nameStr[0];
  const given = nameStr.slice(1);
  const sStroke = getStroke(surname);
  const gStrokes = given.split('').map(getStroke);
  const tianGe = sStroke + 1;
  const renGe = sStroke + (gStrokes[0] || 1);
  const diGe = gStrokes.reduce((a,b)=>a+b, 0);
  const zongGe = sStroke + diGe;
  const waiGe = zongGe - renGe + 1;

  const wuge = {
    天格: {stroke: tianGe, wuxing: wugeWuxing(tianGe)},
    人格: {stroke: renGe, wuxing: wugeWuxing(renGe)},
    地格: {stroke: diGe, wuxing: wugeWuxing(diGe)},
    总格: {stroke: zongGe, wuxing: wugeWuxing(zongGe)},
    外格: {stroke: waiGe, wuxing: wugeWuxing(waiGe)},
  };

  const wxProfile = {};
  for (const c of given) {
    const w = getWuxing(c);
    wxProfile[w] = (wxProfile[w]||0) + 1;
  }

  const shengPairs = [['木','火'],['火','土'],['土','金'],['金','水'],['水','木']];
  function checkRelation(a,b) {
    if (a===b) return '比和，平稳';
    for (const [x,y] of shengPairs) if (a===x && b===y) return '相生，吉';
    return '相克，需注意';
  }

  const t=wuge['天格'].wuxing, r=wuge['人格'].wuxing, d=wuge['地格'].wuxing;
  const analysis = [
    `「${nameStr}」康熙字典笔画分析：`,
    `· 总笔画数：${zongGe}画`,
    `· 三才配置：天格${t}→人格${r} ${checkRelation(t,r)}，人格${r}→地格${d} ${checkRelation(r,d)}`,
    `· 人格数理：${renGe}画，五行属${wugeWuxing(renGe)}`,
  ];

  return {
    surname, given_name: given, full_name: nameStr,
    strokes: Object.fromEntries(nameStr.split('').map(c=>[c,getStroke(c)])),
    wuge, total_stroke: zongGe,
    wuxing_profile: wxProfile,
    analysis: analysis.join('\n'),
  };
}

console.log('🔮 运势引擎就绪 (fortune.js)');
