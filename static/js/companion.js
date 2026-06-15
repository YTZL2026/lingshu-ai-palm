// ============================================
// 灵枢 — 情绪伴侣引擎 V3 (JavaScript)
// PUA · 职场 · 学业 · 生活 · 通用场景
// 移植自 src/companion.py — chat_companion 完整逻辑
// ============================================

const COMPANION_SCENARIOS = {
  'pua': {
    name: 'PUA/情感操控', icon: '💔',
    desc: '被贬低、被控制、自我怀疑...你不是一个人',
    intro: '我听到了你的声音。PUA的核心是让对方怀疑自己的感受——而你的感受是真实的、有效的。我们先做一次深呼吸：吸气4秒，屏住2秒，呼气6秒。\n\n好的。现在我们一起看看：',
    steps: [
      '🔍 识别操控信号：对方是否反复贬低你？是否让你觉得自己"不够好"？是否隔离你的社交圈？',
      '💪 重建自我价值：你的价值不依赖于任何人的评价。列出你独立于这段关系之外的三个优点。',
      '🚧 设立边界："我有权保护自己的情感空间"——这句话你可以对自己说，也可以对对方说。',
      '📞 支持网络：你现在最信任的一个人是谁？如果可以，今天就和ta聊聊。',
    ],
    affirmation: '你没有做错什么。被操控不是你的弱点，是操控者的手段。你值得被尊重、被珍视。',
  },
  'workplace': {
    name: '职场冷暴力', icon: '🏢',
    desc: '被孤立、被打压、付出不被看见...',
    intro: '职场冷暴力是一种隐形伤害——它不像语言暴力那样明显，却同样伤人。\n\n先允许自己感到不舒服，这不代表你不够专业。然后我们一步步来：',
    steps: [
      '📋 客观记录：把让你不舒服的具体事件写下来（时间、地点、谁做了什么），区分事实和感受。',
      '🎯 明确诉求：你希望在什么方面被公平对待？把它具体化，而不是笼统的"被尊重"。',
      '🗣️ 策略沟通：选择一个合适的时机，用"I feel"句式表达。',
      '🌱 自我成长：这段经历让你更清楚什么是不健康的工作环境。',
    ],
    affirmation: '你的专业价值不由任何一个同事或上司来定义。冷暴力往往反映了施与者自身的问题。',
  },
  'study': {
    name: '学习压力', icon: '📚',
    desc: '考试焦虑、学习倦怠、自我怀疑...',
    intro: '学习的压力往往来自"我必须完美"的信念——但其实，学习本身就是不断试错的过程。\n\n先放下手中的书，我们一起调整状态：',
    steps: [
      '🧘 身体扫描：闭上眼睛，注意力从头顶慢慢移到脚尖，感受每一处肌肉的紧张和放松。',
      '📊 合理归因：这次没考好，具体是哪个知识点没掌握？把"我很差"换成"这个知识点我还需要加强"。',
      '⏰ 番茄工作法：25分钟专注 + 5分钟休息。不是学得越久越好，而是学得越专注越好。',
      '🏆 小成就记录：今天你完成了什么？哪怕只是背了5个单词，也值得被记录下来。',
    ],
    affirmation: '学习是一辈子的事，不是一场考试的事。你已经比昨天的自己进步了，这才是最重要的。',
  },
  'life': {
    name: '生活受挫', icon: '🌈',
    desc: '失恋、失业、迷茫、觉得人生没有方向...',
    intro: '人生如四季，有春华秋实，也有寒冬凛冽。你不是"不够坚强"，你只是正在经历一个自然的情绪过程。\n\n先接纳现在的自己：',
    steps: [
      '🕯️ 接纳当下：允许自己难过。不需要假装坚强，不需要马上"振作起来"。',
      '🔭 拉长视角：回想五年前让你痛苦的事，今天看来是什么感觉？五年后再看今天的事。',
      '🌱 微小的掌控感：今天只做一件小事——整理桌面、洗个热水澡、走10分钟路。',
      '💌 给未来的自己写信：写下你现在的心情，以及你希望三个月后的自己过什么样的生活。',
    ],
    affirmation: '人生没有白走的路，每一步都算数。此刻的低谷是你人生的深度——但光，一定会来。',
  },
  'general': {
    name: '情绪舒缓', icon: '🌿',
    desc: '说不清原因，就是不舒服、烦躁、低落...',
    intro: '有时候我们不需要一个具体的理由来觉得不开心。情绪就像天气，有晴有阴，都是自然的。\n\n我们先不急着"解决问题"，先跟自己的情绪待一会儿：',
    steps: [
      '🌬️ 4-7-8呼吸法：吸气4秒→屏息7秒→缓慢呼气8秒。重复3次。',
      '🎨 情绪命名：试着给你的情绪起个名字——是"失落"？"焦虑"？"疲惫"？命名本身就有疗愈作用。',
      '🚶 接地练习：说出你现在看到的5样东西、听到的4种声音、身体感觉到的3种触感。',
      '☕ 自我关怀仪式：给自己泡杯热茶，或者用温水洗洗脸。小小的仪式感告诉你：我在照顾自己。',
    ],
    affirmation: '情绪来，情绪也会走。你不是你的情绪——你只是正在经历它的人。此刻的你，已经足够好。',
  },
};

// 自由对话关键词→场景匹配
const COMPANION_KEYWORDS = {
  'pua': ['pua','操控','控制','贬低','打压','不值得','配不上','煤气灯','自恋','情感虐待','分手','被抛弃'],
  'workplace': ['职场','同事','领导','老板','排挤','孤立','冷暴力','穿小鞋','降薪','裁员','加班','背锅'],
  'study': ['考试','学习','成绩','挂科','考研','高考','复习','论文','毕业','厌学','做题','没考好'],
  'life': ['失恋','分手','失业','迷茫','没方向','无聊','孤独','空虚','失败','失去','痛苦','绝望'],
};

// ======================== V3: 智能对话引擎 ========================

function _extractTopic(msg) {
  // 移除常见语气词
  for (const filler of ['就是','感觉','觉得','好像','可能','吧','啊','呀','呢','了','的','很','有点','特别','非常','一直','总是','老是','真的','完全','根本']) {
    msg = msg.replace(new RegExp(filler, 'g'), ' ');
  }
  const words = msg.split(/\s+/).filter(w => w.length >= 2);
  if (words.length >= 3) return words.slice(0, 6).join(' ');
  return msg.substring(0, 40);
}

function _detectEmotion(msg) {
  let anger = 0, sad = 0, fear = 0, confused = 0;
  for (const w of ['气','怒','恨','烦','火','操','妈的','过分','凭什么','不公平','针对','委屈']) {
    if (msg.includes(w)) anger++;
  }
  for (const w of ['难过','哭','伤心','失落','累','疲惫','绝望','抑郁','孤单','孤独','想死','崩溃']) {
    if (msg.includes(w)) sad++;
  }
  for (const w of ['怕','害怕','担心','焦虑','紧张','慌','不安','恐惧','压力']) {
    if (msg.includes(w)) fear++;
  }
  for (const w of ['迷茫','不知道','怎么办','困惑','纠结','犹豫','矛盾','选择']) {
    if (msg.includes(w)) confused++;
  }
  if (anger > sad && anger > fear && anger > confused) return 'anger';
  if (sad > anger && sad > fear && sad > confused) return 'sadness';
  if (fear > sad && fear > anger && fear > confused) return 'anxiety';
  if (confused > 0) return 'confused';
  return 'general';
}

function _buildContextualReply(msg, topic, emotion, sceneId, historyLen) {
  const scene = COMPANION_SCENARIOS[sceneId] || COMPANION_SCENARIOS['general'];
  const topicEcho = topic ? `我听到你说"${topic}"——` : '';

  const emotionOpeners = {
    'anger': `${topicEcho}这件事让你很生气，这种愤怒是正常的。被不公正对待的时候，任何人都会愤怒。\n\n愤怒说明你在乎——在乎公平、在乎尊严、在乎自己的边界。`,
    'sadness': `${topicEcho}听起来你现在心里很重。难过不是软弱，难过是因为你在乎的东西受到了伤害。\n\n允许自己难过。不需要马上"好起来"。悲伤是心灵在消化痛苦。`,
    'anxiety': `${topicEcho}这种焦虑的感觉我理解——心里像是绷着一根弦。焦虑其实是你的大脑在试图保护你，只是它有时候保护得太用力了。\n\n我们先做一件事：深呼吸三次，把注意力放在呼吸上。`,
    'confused': `${topicEcho}当事情不太清晰的时候，感到迷茫是很自然的。迷茫不是没有方向，而是你正在寻找方向——这本身就是前进。\n\n有时候我们不需要马上有答案。先接纳"我现在还不确定"这件事本身。`,
    'general': randomPick([
      `${topicEcho}嗯，我听到了。`,
      `${topicEcho}继续说，我在。`,
      `${topicEcho}明白了——你接着说。`,
      `嗯，你继续说。`,
      `我听着呢。`,
    ]),
  };
  let reply = emotionOpeners[emotion] || emotionOpeners['general'];

  // 场景引导
  if (sceneId === 'pua') {
    reply += '\n\n在一段关系中感到被贬低或控制，这不是你的问题。健康的关系应该让你感到安全、被尊重、可以做自己。你现在的感受是你内心的保护机制在提醒你：有什么东西不对。相信这个信号。';
  } else if (sceneId === 'workplace') {
    reply += '\n\n职场中的不公正对待确实让人疲惫。记住：你的专业能力不取决于任何一个领导或同事的评价。给自己一些空间，区分"工作上的反馈"和"对人的不尊重"——前者可以改进，后者你有权拒绝。';
  } else if (sceneId === 'study') {
    reply += '\n\n学习的压力往往来自"我必须完美"——但成长本身就是不断试错。今天做不到不代表永远做不到。把目标从"必须考好"换成"今天比昨天多掌握一个知识点"。';
  } else if (sceneId === 'life') {
    reply += '\n\n人生有起有落，就像四季更替。此刻的低谷不是终点——它只是你人生长路上的一个转弯。很多后来让你成长最多的经历，在当时看来都是最难熬的。';
  }

  // 多轮对话
  if (historyLen >= 3) {
    reply += '\n\n聊了这么多，我想说：你愿意面对这些情绪，本身就很了不起。今天可以为自己做一件小事吗？哪怕只是好好喝一杯水、走五分钟路、或者听一首喜欢的歌。';
  }

  const affirmations = {
    'anger': '你的愤怒是正当的。它保护着你的底线。',
    'sadness': '会流泪说明你心里还有柔软的地方——那是最珍贵的地方。',
    'anxiety': '焦虑是你在乎的证明。你已经足够好了。',
    'confused': '迷茫是成长的开始。不急着有答案，答案会来找你。',
    'general': '你的感受是重要的。你值得被温柔对待。',
  };

  return { reply, affirmation: affirmations[emotion] || affirmations['general'] };
}

function chatCompanion(userMessage, history) {
  if (!userMessage || !userMessage.trim()) {
    return {
      reply: '我在这里，你想说什么都可以。不用组织语言，想到什么就说什么。我会认真听。',
      scenario: 'general', icon: '🌿', affirmation: '', suggestFollowup: true,
    };
  }

  const msg = userMessage.trim();
  const topic = _extractTopic(msg);
  const emotion = _detectEmotion(msg);
  const histLen = history ? history.length : 0;

  // 匹配场景
  let matchedScene = 'general';
  let maxMatches = 0;
  for (const [sceneId, keywords] of Object.entries(COMPANION_KEYWORDS)) {
    const matches = keywords.filter(kw => msg.includes(kw)).length;
    if (matches > maxMatches) { maxMatches = matches; matchedScene = sceneId; }
  }

  const scene = COMPANION_SCENARIOS[matchedScene] || COMPANION_SCENARIOS['general'];
  const { reply, affirmation } = _buildContextualReply(msg, topic, emotion, matchedScene, histLen);

  return {
    reply, scenario: matchedScene, icon: scene.icon, affirmation,
    suggestFollowup: msg.length < 30,
  };
}

// ======================== 快速场景获取（兼容旧接口） ========================
function getCompanionResponse(scenario, userMessage) {
  if (!scenario || !COMPANION_SCENARIOS[scenario]) scenario = 'general';
  // 如果有消息且>5字符，走智能引擎
  if (userMessage && userMessage.trim().length > 5) {
    return chatCompanion(userMessage, []);
  }
  // 否则返回场景引导
  const sc = COMPANION_SCENARIOS[scenario];
  return {
    reply: `${sc.intro}\n\n${sc.steps.join('\n')}\n\n${sc.affirmation}`,
    emotion: 'gentle', scenario, icon: sc.icon,
  };
}

function getScenarioList() { return COMPANION_SCENARIOS; }
function randomPick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

console.log('🌿 情绪伴侣 V3 就绪 (companion.js)');
