// ============================================
// 灵枢 — 中医体质推理引擎 (JavaScript)
// 九种体质 · 周易八卦 · 五脏评分 · 身体年龄
// 移植自 src/constitution_engine.py
// ============================================

// ======================== 九种体质定义 ========================
const CONSTITUTION_TYPES = {
  'balanced': {
    name:'平和质', mythic_name:'苍龙质', icon:'🐉', color:'#27ae60',
    description:'阴阳调和，气血充盈，五脏平衡', population_pct:32.8,
    traits:['精力充沛','适应力强','睡眠良好','面色红润'],
    strength_organs:['心','肺'], watch_organs:[],
  },
  'qi_deficient': {
    name:'气虚质', mythic_name:'玄龟质', icon:'🐢', color:'#7f8c8d',
    description:'元气不足，疲乏无力，气短懒言', population_pct:13.4,
    traits:['容易疲劳','气短懒言','自汗','易感冒'],
    strength_organs:[], watch_organs:['肺','脾'],
  },
  'yang_deficient': {
    name:'阳虚质', mythic_name:'玄冥质', icon:'🌙', color:'#5d6d7e',
    description:'阳气不足，畏寒怕冷，手足不温', population_pct:9.0,
    traits:['畏寒怕冷','手足不温','喜热饮食','精神不振'],
    strength_organs:[], watch_organs:['肾','脾'],
  },
  'yin_deficient': {
    name:'阴虚质', mythic_name:'朱雀质', icon:'🔥', color:'#e74c3c',
    description:'阴液不足，口干咽燥，手足心热', population_pct:8.9,
    traits:['口干咽燥','手足心热','失眠多梦','大便干燥'],
    strength_organs:['肝'], watch_organs:['肾','肺'],
  },
  'phlegm_damp': {
    name:'痰湿质', mythic_name:'饕餮质', icon:'🍖', color:'#d4a017',
    description:'痰湿凝聚，形体肥胖，腹部肥满', population_pct:8.7,
    traits:['腹部肥满','面部油腻','痰多胸闷','身体沉重'],
    strength_organs:[], watch_organs:['脾','肺'],
  },
  'damp_heat': {
    name:'湿热质', mythic_name:'应龙质', icon:'🌧', color:'#e67e22',
    description:'湿热内蕴，面垢油光，口苦口干', population_pct:7.9,
    traits:['面垢油光','口苦口干','大便黏滞','易生痤疮'],
    strength_organs:[], watch_organs:['肝','胆','脾'],
  },
  'blood_stasis': {
    name:'血瘀质', mythic_name:'麒麟质', icon:'🦄', color:'#8e44ad',
    description:'血行不畅，肤色晦暗，唇色偏暗', population_pct:7.6,
    traits:['肤色晦暗','容易出现瘀斑','疼痛固定','面色暗沉'],
    strength_organs:[], watch_organs:['心','肝'],
  },
  'qi_stagnation': {
    name:'气郁质', mythic_name:'白虎质', icon:'🐅', color:'#2c3e50',
    description:'气机郁滞，神情抑郁，忧虑脆弱', population_pct:7.1,
    traits:['神情抑郁','情感脆弱','烦闷不乐','胁肋胀痛'],
    strength_organs:[], watch_organs:['肝','心'],
  },
  'allergic': {
    name:'特禀质', mythic_name:'灵狐质', icon:'🦊', color:'#3498db',
    description:'先天失常，过敏体质，对外界适应力差', population_pct:4.6,
    traits:['容易过敏','对季节变化敏感','皮肤易出疹','鼻塞流涕'],
    strength_organs:[], watch_organs:['肺','脾'],
  },
};

// ======================== 周易八卦系统 ========================
const BAGUA_MOUNDS = {
  'qian':  {name:'乾',trigram:'☰',mound:'小鱼际',element:'金',organ:'肺',virtue:'健',direction:'西北',nature:'天',hexagram_num:1},
  'kun':   {name:'坤',trigram:'☷',mound:'无名指根',element:'土',organ:'脾',virtue:'顺',direction:'西南',nature:'地',hexagram_num:2},
  'zhen':  {name:'震',trigram:'☳',mound:'大鱼际上',element:'木',organ:'肝',virtue:'动',direction:'东',nature:'雷',hexagram_num:51},
  'xun':   {name:'巽',trigram:'☴',mound:'大鱼际下',element:'木',organ:'胆',virtue:'入',direction:'东南',nature:'风',hexagram_num:57},
  'kan':   {name:'坎',trigram:'☵',mound:'腕部',element:'水',organ:'肾',virtue:'陷',direction:'北',nature:'水',hexagram_num:29},
  'li':    {name:'离',trigram:'☲',mound:'中指根',element:'火',organ:'心',virtue:'丽',direction:'南',nature:'火',hexagram_num:30},
  'gen':   {name:'艮',trigram:'☶',mound:'食指根',element:'土',organ:'胃',virtue:'止',direction:'东北',nature:'山',hexagram_num:52},
  'dui':   {name:'兑',trigram:'☱',mound:'小指根',element:'金',organ:'肺',virtue:'说',direction:'西',nature:'泽',hexagram_num:58},
};

const BAGUA_GUIDANCE = {
  'qian': '乾卦·天行健：君子以自强不息。顺应天时，作息有序，阳气充沛则百病不侵。',
  'kun':  '坤卦·地势坤：君子以厚德载物。脾胃为后天之本，厚土能纳万物，包容即是养生。',
  'zhen': '震卦·洊雷震：君子以恐惧修省。肝气调达则生机勃发，遇变不惊，动中求静。',
  'xun':  '巽卦·随风巽：君子以申命行事。胆气舒畅则决断明快，柔顺不争，风过无痕。',
  'kan':  '坎卦·水洊至：君子以常德行。肾藏精为先天之本，水滴石穿，贵在坚持。',
  'li':   '离卦·明两作：君子以继明照于四方。心火明亮则神清气爽，虚明不燥。',
  'gen':  '艮卦·兼山艮：君子以思不出其位。知止不殆，适可而止，胃气和则五脏安。',
  'dui':  '兑卦·丽泽兑：君子以朋友讲习。肺气宣畅则呼吸调匀，悦而不过，和而不纵。',
};

const CONSTITUTION_BAGUA = {
  'balanced':'qian','qi_deficient':'kun','yang_deficient':'kan',
  'yin_deficient':'li','phlegm_damp':'kun','damp_heat':'zhen',
  'blood_stasis':'gen','qi_stagnation':'xun','allergic':'dui',
};

const DIET_RECOMMENDATIONS = {
  'balanced':      ['保持饮食均衡，五谷杂粮搭配','时令蔬果，不偏嗜','适量饮水'],
  'qi_deficient':  ['多食益气食物：山药、莲子、小米','常饮黄芪红枣茶','忌食生冷寒凉'],
  'yang_deficient':['多食温阳食物：羊肉、韭菜、核桃','生姜红糖水晨饮','忌食寒凉生冷'],
  'yin_deficient': ['多食滋阴食物：银耳、百合、鸭肉','枸杞菊花茶常饮','忌食辛辣燥热'],
  'phlegm_damp':   ['多食健脾化湿：薏米、冬瓜、赤小豆','荷叶山楂茶','少食肥甘厚腻'],
  'damp_heat':     ['多食清热利湿：绿豆、苦瓜、芹菜','菊花金银花茶','忌食辛辣油腻'],
  'blood_stasis':  ['多食活血化瘀：山楂、黑木耳、醋','玫瑰花茶','忌食寒凉收涩'],
  'qi_stagnation': ['多食理气解郁：柑橘、佛手、玫瑰花','陈皮茶','少食涩味食物'],
  'allergic':      ['避免已知过敏食物','多食益气固表：黄芪、白术','清淡饮食为主'],
};

const EXERCISE_RECOMMENDATIONS = {
  'balanced':      ['每周150分钟中等强度运动','跑步、游泳、球类皆宜','保持运动习惯'],
  'qi_deficient':  ['温和运动为主：太极拳、八段锦','散步30分钟/天','避免剧烈运动大汗'],
  'yang_deficient':['阳光下运动：快走、太极','上午运动最佳','注意保暖避风寒'],
  'yin_deficient': ['避免高温运动','游泳、瑜伽、太极','傍晚运动为宜'],
  'phlegm_damp':   ['中等强度有氧：慢跑、骑车','每周≥5次，每次40分钟','循序渐进加量'],
  'damp_heat':     ['大强度运动排汗：跑步、健身','运动后及时清洁','避免潮湿环境运动'],
  'blood_stasis':  ['促进循环：快走、舞蹈、太极','避免久坐久站','运动前充分热身'],
  'qi_stagnation': ['团体运动：集体舞、球类','户外运动舒展心情','配合深呼吸'],
  'allergic':      ['室内运动为主','避免花粉季节户外运动','运动前充分热身'],
};

const LIFESTYLE_BASE = {
  'balanced':       ['保持规律的作息，晚11点前入睡','保持平和心态，勿大喜大怒','定期体检，关注身体变化'],
  'qi_deficient':   ['早睡早起，避免熬夜耗气','午休20-30分钟','说话放慢语速，节省气力'],
  'yang_deficient': ['日光浴15-30分钟/天（上午最佳）','冬季注意腰腹和足部保暖','睡前热水泡脚20分钟'],
  'yin_deficient':  ['保证充足睡眠，晚上11点前入睡','避免炎热环境和桑拿','保持情绪平和，勿急躁动怒'],
  'phlegm_damp':    ['保持居住环境干燥通风','控制体重，避免久坐','饮食定时定量，勿暴饮暴食'],
  'damp_heat':      ['保持个人卫生，勤换衣物','避免居住潮湿环境','戒烟限酒'],
  'blood_stasis':   ['保持心情愉快，避免情绪压抑','寒冷季节注意保暖','适当按摩促进血循环'],
  'qi_stagnation':  ['培养兴趣爱好转移注意力','多与朋友交流，避免独处','练习腹式深呼吸放松'],
  'allergic':       ['保持居住环境清洁，减少尘螨','换季时注意防护','随身携带必要的抗敏药物'],
};

// ======================== 特征提取（简化版，浏览器端） ========================
// 基于 MediaPipe 手部关键点 + 图像基本信息
function extractPalmFeatures(landmarks, imgWidth, imgHeight, imageData) {
  // landmarks: 21 MediaPipe hand landmarks [{x,y,z},...]
  // imageData: basic image stats {redness, brightness, contrast}

  if (!landmarks || landmarks.length < 21) {
    return generatePlaceholderFeatures();
  }

  const w = imgWidth || 640;
  const h = imgHeight || 480;
  const stats = imageData || {};

  // 手指张开度
  const tips = [4, 8, 12, 16, 20];
  const bases = [2, 5, 9, 13, 17];
  let spreadDist = 0;
  for (let i = 0; i < tips.length; i++) {
    const t = landmarks[tips[i]];
    const b = landmarks[bases[i]];
    spreadDist += Math.sqrt((t.x-b.x)**2 + (t.y-b.y)**2);
  }
  spreadDist /= tips.length;

  // 大鱼际饱满度（拇指根部区域面积）
  const thumbBase = landmarks[2];
  const wrist = landmarks[0];
  const thumbMCP = landmarks[2];
  const thenarArea = Math.abs((thumbBase.x - wrist.x) * (thumbBase.y - wrist.y)) * w * h * 0.01;

  // 手掌中心深度（掌心凹陷程度）
  const palmPoints = [0, 5, 9, 13, 17];
  let avgZ = 0;
  for (const idx of palmPoints) avgZ += landmarks[idx].z || 0;
  avgZ /= palmPoints.length;

  // 纹理密度（基于图像局部对比度估算）
  const textureDensity = stats.contrast || 50;

  // 线条复杂度（基于手指间距方差）
  const finX = landmarks[tips[0]].x;
  const finSpreads = tips.slice(1).map(i => Math.abs(landmarks[i].x - finX));
  const lineComplexity = Math.min(100, 40 + (Math.max(...finSpreads) - Math.min(...finSpreads)) * 200);

  // 手掌色泽（基于图像RGB均值和方差）
  const overallRedness = stats.redness || 50;
  const luster = stats.brightness || 50;
  const colorUniformity = 100 - (stats.stdDev || 30);
  const skinColorStd = stats.stdDev || 30;

  // 静脉可见度（亮度方差）
  const veinVisibility = Math.min(50, stats.stdDev || 15);

  return {
    line_density: textureDensity,
    line_complexity: lineComplexity,
    life_line_depth: 35 + spreadDist * 200,
    head_line_depth: 35 + spreadDist * 150,
    heart_line_depth: 30 + spreadDist * 180,
    thenar_fullness: Math.min(90, Math.max(10, thenarArea)),
    hypothenar_fullness: 40 + spreadDist * 100,
    overall_redness: overallRedness,
    luster,
    color_uniformity: colorUniformity,
    skin_color_std: skinColorStd,
    texture_density: textureDensity,
    vein_visibility: veinVisibility,
    center_depth: avgZ * 100 + 50,
    finger_spread: spreadDist * 1000,
    fingerprint_count: 10,
    palm_width: w * 0.3,
    palm_height: h * 0.3,
    finger_length_ratio: 0.7 + spreadDist * 0.5,
    root_angle: 30 + Math.random() * 10,
  };
}

function generatePlaceholderFeatures() {
  return {
    line_density: 50, line_complexity: 50,
    life_line_depth: 35, head_line_depth: 35, heart_line_depth: 35,
    thenar_fullness: 45, hypothenar_fullness: 45,
    overall_redness: 50, luster: 50, color_uniformity: 70, skin_color_std: 25,
    texture_density: 50, vein_visibility: 20, center_depth: 50,
    finger_spread: 40, fingerprint_count: 10,
    palm_width: 200, palm_height: 150, finger_length_ratio: 0.75, root_angle: 35,
  };
}

// ======================== 体质推理引擎 ========================
function inferConstitution(features, chronologicalAge) {
  if (!chronologicalAge) chronologicalAge = 30;
  const f = features || generatePlaceholderFeatures();

  // 计算9种体质得分
  const scores = {};
  scores['balanced'] = scoreBalanced(f);
  scores['qi_deficient'] = scoreQiDeficient(f);
  scores['yang_deficient'] = scoreYangDeficient(f);
  scores['yin_deficient'] = scoreYinDeficient(f);
  scores['phlegm_damp'] = scorePhlegmDamp(f);
  scores['damp_heat'] = scoreDampHeat(f);
  scores['blood_stasis'] = scoreBloodStasis(f);
  scores['qi_stagnation'] = scoreQiStagnation(f);
  scores['allergic'] = scoreAllergic(f);

  // 归一化
  const maxScore = Math.max(...Object.values(scores));
  const expScores = {};
  for (const [k, v] of Object.entries(scores)) {
    expScores[k] = Math.exp(v - maxScore);
  }
  const total = Object.values(expScores).reduce((a,b)=>a+b, 0);
  const scoreDict = {};
  for (const [k, v] of Object.entries(expScores)) {
    scoreDict[k] = Math.round(v / total * 10000) / 10000;
  }

  // 确定主要体质
  const primaryId = Object.keys(scoreDict).reduce((a,b)=>scoreDict[a]>scoreDict[b]?a:b);
  const primaryConf = scoreDict[primaryId];
  const ctype = CONSTITUTION_TYPES[primaryId];

  // 五脏评分
  const organScores = estimateOrganScores(f, primaryId);

  // 身体年龄
  const bodyAge = estimateBodyAge(f, chronologicalAge);

  // 周易卦象
  const baguaKey = CONSTITUTION_BAGUA[primaryId];
  const bagua = BAGUA_MOUNDS[baguaKey];
  const guidance = BAGUA_GUIDANCE[baguaKey];

  const diet = DIET_RECOMMENDATIONS[primaryId] || DIET_RECOMMENDATIONS['balanced'];
  const exercise = EXERCISE_RECOMMENDATIONS[primaryId] || EXERCISE_RECOMMENDATIONS['balanced'];
  const lifestyle = LIFESTYLE_BASE[primaryId] || LIFESTYLE_BASE['balanced'];

  const shareText = generateShareText(primaryId, primaryConf, bodyAge, chronologicalAge);

  return {
    constitution_id: primaryId,
    constitution_name: ctype.name,
    mythic_name: ctype.mythic_name,
    icon: ctype.icon,
    color: ctype.color,
    confidence: primaryConf,
    all_scores: scoreDict,
    description: ctype.description,
    traits: ctype.traits || [],
    organ_scores: organScores,
    body_age: bodyAge,
    chronological_age: chronologicalAge,
    age_diff: Math.round((bodyAge - chronologicalAge) * 10) / 10,
    percentile: Math.round((1 - primaryConf) * 1000) / 10,
    population_pct: ctype.population_pct || 0,
    diet, exercise, lifestyle,
    share_text: shareText,
    zhouyi: {
      primary_bagua: bagua.name,
      trigram: bagua.trigram,
      mound: bagua.mound,
      element: bagua.element,
      organ: bagua.organ,
      virtue: bagua.virtue,
      nature: bagua.nature,
      guidance,
    },
  };
}

// ======================== 九种体质评分函数 ========================
function scoreBalanced(f) {
  // 所有指标均衡（偏离50越远分越低）
  const ideal = [50,50,50,0.5,0.5,0.5,0,0,50,50,50,50,50,50,10,50,50,10,10,50];
  const actual = [f.line_density,f.line_complexity,f.life_line_depth,f.thenar_fullness/100,
    f.hypothenar_fullness/100,f.overall_redness/100,f.finger_spread/100,f.fingerprint_count/100,
    f.texture_density,f.palm_width*0.2,f.palm_height*0.3,f.luster,f.color_uniformity,
    f.skin_color_std,f.vein_visibility,f.center_depth,f.heart_line_depth,f.head_line_depth*0.5,f.life_line_depth*0.5,f.root_angle];
  let diff = 0;
  for (let i = 0; i < Math.min(ideal.length, actual.length); i++) {
    diff += Math.abs(actual[i] - ideal[i]);
  }
  return 100 - (diff / Math.min(ideal.length, actual.length)) * 1.5;
}

function scoreQiDeficient(f) {
  let s = 50;
  s += (35 - f.life_line_depth) * 0.5;
  s += (35 - f.head_line_depth) * 0.3;
  s += (35 - f.thenar_fullness) * 0.6;
  s += (35 - f.overall_redness) * 0.4;
  s += (f.vein_visibility - 20) * 0.3;
  return Math.max(0, s);
}

function scoreYangDeficient(f) {
  let s = 50;
  s += (25 - f.overall_redness) * 0.6;
  s += (30 - f.life_line_depth) * 0.4;
  s += (40 - f.luster) * 0.4;
  s += (40 - f.thenar_fullness) * 0.3;
  s += (f.vein_visibility - 10) * 0.4;
  return Math.max(0, s);
}

function scoreYinDeficient(f) {
  let s = 50;
  s += (f.overall_redness - 55) * 0.6;
  s += (f.texture_density - 50) * 0.4;
  s += (f.luster - 55) * 0.3;
  s += (60 - f.skin_color_std) * 0.3;
  s += (55 - f.center_depth) * 0.2;
  return Math.max(0, s);
}

function scorePhlegmDamp(f) {
  let s = 50;
  s += (f.thenar_fullness - 55) * 0.6;
  s += (f.luster - 50) * 0.5;
  s += (50 - f.line_complexity) * 0.3;
  s += (60 - f.texture_density) * 0.3;
  s += (f.hypothenar_fullness - 50) * 0.2;
  return Math.max(0, s);
}

function scoreDampHeat(f) {
  let s = 50;
  s += (f.overall_redness - 55) * 0.5;
  s += (f.luster - 55) * 0.5;
  s += (f.vein_visibility - 20) * 0.3;
  s += (f.texture_density - 45) * 0.3;
  s += (60 - f.color_uniformity) * 0.2;
  return Math.max(0, s);
}

function scoreBloodStasis(f) {
  let s = 50;
  s += (f.overall_redness - 50) * 0.3;
  s += (f.texture_density - 50) * 0.5;
  s += (f.line_complexity - 50) * 0.5;
  s += (55 - f.color_uniformity) * 0.5;
  s += (f.vein_visibility - 15) * 0.4;
  return Math.max(0, s);
}

function scoreQiStagnation(f) {
  let s = 50;
  s += (f.line_complexity - 50) * 0.6;
  s += (50 - f.color_uniformity) * 0.4;
  s += (f.texture_density - 45) * 0.4;
  s += (50 - f.center_depth) * 0.3;
  s += (f.hypothenar_fullness - 45) * 0.2;
  return Math.max(0, s);
}

function scoreAllergic(f) {
  let s = 50;
  s += (f.texture_density - 50) * 0.4;
  s += (50 - f.color_uniformity) * 0.5;
  s += (f.line_complexity - 45) * 0.4;
  s += (60 - f.luster) * 0.3;
  s += (f.vein_visibility - 10) * 0.3;
  return Math.max(0, s);
}

// ======================== 五脏功能评分 ========================
function estimateOrganScores(f, constitutionId) {
  const scores = { 心: 75, 肝: 75, 脾: 75, 肺: 75, 肾: 75 };

  // 色泽→心
  scores['心'] += (f.overall_redness - 45) * 0.2;
  scores['心'] += (f.luster - 40) * 0.15;
  scores['心'] = clamp(scores['心'], 40, 95);

  // 纹理密度→肝
  scores['肝'] += (50 - f.line_complexity) * 0.2;
  scores['肝'] += (f.color_uniformity - 40) * 0.15;
  scores['肝'] = clamp(scores['肝'], 40, 95);

  // 大鱼际→脾
  scores['脾'] += (f.thenar_fullness - 40) * 0.25;
  scores['脾'] += (f.luster - 50) * 0.1;
  scores['脾'] = clamp(scores['脾'], 40, 95);

  // 小鱼际→肺
  scores['肺'] += (f.hypothenar_fullness - 40) * 0.25;
  scores['肺'] += (f.color_uniformity - 50) * 0.1;
  scores['肺'] = clamp(scores['肺'], 40, 95);

  // 掌心深度→肾
  scores['肾'] += (f.center_depth - 45) * 0.2;
  scores['肾'] += (f.life_line_depth - 35) * 0.15;
  scores['肾'] = clamp(scores['肾'], 40, 95);

  // 根据体质类型调整
  const watchOrgans = (CONSTITUTION_TYPES[constitutionId] || {}).watch_organs || [];
  const strengthOrgans = (CONSTITUTION_TYPES[constitutionId] || {}).strength_organs || [];
  for (const org of watchOrgans) {
    if (scores[org] !== undefined) scores[org] -= 10;
  }
  for (const org of strengthOrgans) {
    if (scores[org] !== undefined) scores[org] += 5;
  }

  // 确保范围
  for (const k of Object.keys(scores)) {
    scores[k] = clamp(Math.round(scores[k]), 30, 98);
  }

  return scores;
}

function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

// ======================== 身体年龄估算 ========================
function estimateBodyAge(f, chronologicalAge) {
  let bodyAge = chronologicalAge;

  // 手掌纹理密度反映代谢年龄
  bodyAge += (f.texture_density - 45) * 0.1;
  // 大鱼际饱满度反映脾胃功能→衰老速度
  bodyAge += (45 - f.thenar_fullness) * 0.08;
  // 掌心深度反映肾气
  bodyAge += (45 - f.center_depth) * 0.07;
  // 静脉可见度反映循环
  bodyAge += (f.vein_visibility - 15) * 0.06;
  // 光泽度反映气血
  bodyAge += (45 - f.luster) * 0.1;
  // 色泽均匀度
  bodyAge += (50 - f.color_uniformity) * 0.05;

  bodyAge = clamp(bodyAge, chronologicalAge - 15, chronologicalAge + 20);
  return Math.round(bodyAge);
}

// ======================== 分享文案 ========================
function generateShareText(constitutionId, confidence, bodyAge, chronologicalAge) {
  const ctype = CONSTITUTION_TYPES[constitutionId];
  const diff = bodyAge - chronologicalAge;
  const parts = [
    `🧚 灵枢AI掌纹分析报告`,
    ``,
    `体质：${ctype.name}（${ctype.mythic_name}）${ctype.icon}`,
    `描述：${ctype.description}`,
    `置信度：${Math.round(confidence * 100)}%`,
    ``,
    `身体年龄：${bodyAge}岁（实际${chronologicalAge}岁）`,
  ];
  if (diff < 0) parts.push(`✨ 身体状态比实际年龄年轻${Math.abs(diff)}岁！`);
  else if (diff <= 2) parts.push(`🌿 身体年龄与实际年龄基本相当`);
  else parts.push(`⚠️ 身体年龄偏高${Math.round(diff)}岁，需要关注调养`);
  return parts.join('\n');
}

function getConstitutionTypes() {
  return CONSTITUTION_TYPES;
}

console.log('🏥 体质引擎就绪 (constitution.js)');
