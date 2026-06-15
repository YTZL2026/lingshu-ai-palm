// ============================================
// 灵枢 — 主控制器 V3
// 初始化 / Tab切换 / API调用 / 语音对话 / 打卡
// ============================================

let currentTab = 0;
let currentScenario = 'general';
let lastResult = null;

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', async () => {
  Agent.init();
  Voice.init();

  Voice.onStateChange = (s) => Agent.setState(s);

  const streak = Storage.checkIn();
  updateStreakUI(streak);
  await loadAlmanac();

  setTimeout(() => {
    const dateEl = document.getElementById('almanacDate');
    const yiEl = document.getElementById('yiList');
    const greeting = Agent.greet() + '\n今天是' +
      (dateEl?.textContent || '新的一天') +
      '，宜' + (yiEl?.textContent || '诸事') + '。';
    Agent.speak(greeting);
  }, 800);

  updateBackground();
  setInterval(updateBackground, 600000);
  initInputAutoHide();
});

// ==================== 树洞输入框快捷聚焦 ====================
function focusCompanionInput() {
  const input = document.getElementById('companionInput');
  if (input) input.focus();
  if (navigator.vibrate) navigator.vibrate(30);
}

// ==================== Tab 切换 ====================
function switchTab(idx) {
  Voice.stop();

  currentTab = idx;

  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  const tabIds = ['tab-home','tab-palm','tab-fortune','tab-companion','tab-settings'];
  if (tabIds[idx]) document.getElementById(tabIds[idx]).classList.add('active');

  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.querySelector(`[data-tab="${idx}"]`)?.classList.add('active');

  // 非首页 → 紧凑精灵区，腾出空间给内容
  const agentArea = document.getElementById('agentArea');
  const tabContent = document.getElementById('tabContent');
  if (idx === 0) {
    agentArea?.classList.remove('compact');
    if (tabContent) tabContent.style.paddingBottom = '120px';
  } else {
    agentArea?.classList.add('compact');
    if (tabContent) tabContent.style.paddingBottom = '110px';
  }

  // 掌纹Tab：固定布局，动态计算高度，确保不滚动
  if (idx === 1) {
    if (tabContent) tabContent.style.paddingBottom = '70px';
    Camera.init().then(() => Camera.start());
    setTimeout(() => fitPalmTab(), 100);
  } else {
    Camera.stop();
  }

  // 切回首页时刷新黄历
  if (idx === 0) loadAlmanac();

  // 切到设置时加载当前配置
  if (idx === 4) loadLLMConfig();

  // 切到树洞时自动激活默认场景
  if (idx === 3) {
    currentScenario = 'general';
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    document.querySelector('.chip[onclick*="general"]')?.classList.add('active');
  }
}

function fitPalmTab() {
  const palmPanel = document.getElementById('tab-palm');
  if (!palmPanel || !palmPanel.classList.contains('active')) return;
  const agentArea = document.getElementById('agentArea');
  const topbar = document.querySelector('.topbar');
  // 可用高度 = 视口 - 顶部栏 - 精灵区 - 底部导航区 - 语音栏
  const topbarH = topbar ? topbar.offsetHeight : 48;
  const agentH = agentArea ? agentArea.offsetHeight : 60;
  const bottomReserve = 100; // 底部导航 + 安全区
  const availH = window.innerHeight - topbarH - agentH - bottomReserve;
  palmPanel.style.height = Math.max(availH, 380) + 'px';
  palmPanel.style.overflowY = 'hidden';
}

// 监听 resize / orientationchange 重算掌纹Tab高度
window.addEventListener('resize', () => {
  if (typeof currentTab !== 'undefined' && currentTab === 1) fitPalmTab();
});
window.addEventListener('orientationchange', () => {
  setTimeout(() => {
    if (typeof currentTab !== 'undefined' && currentTab === 1) fitPalmTab();
  }, 300);
});

// ==================== 输入时自动隐藏底部导航 ====================
function initInputAutoHide() {
  const bottomNav = document.querySelector('.bottom-nav');
  let hideTimer = null;

  function hide() {
    if (hideTimer) clearTimeout(hideTimer);
    bottomNav?.classList.add('hidden');
  }
  function show() {
    hideTimer = setTimeout(() => {
      bottomNav?.classList.remove('hidden');
    }, 200);
  }

  document.addEventListener('focusin', (e) => {
    const tag = e.target.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA') hide();
  });
  document.addEventListener('focusout', (e) => {
    const tag = e.target.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA') show();
  });
}

// ==================== 掌纹分析 ====================
async function capturePalm() {
  const captured = Camera.capture();
  const dataUrl = typeof captured === 'string' ? captured : captured.dataUrl;
  const imageStats = (typeof captured === 'object' && captured.stats) ? captured.stats : Camera.getLastImageStats();
  const age = parseFloat(document.getElementById('ageInput')?.value) || 30;

  showLoading('灵枢正在分析你的掌纹...');

  try {
    // 尝试服务端 API（完整分析引擎）
    const res = await fetch(dataUrl);
    const blob = await res.blob();
    const form = new FormData();
    form.append('image', blob, 'palm.jpg');
    form.append('age', String(age));

    const resp = await fetch('/api/analyze', { method: 'POST', body: form });
    const data = await resp.json();

    hideLoading();

    if (!data.success) {
      Agent.speak(data.guidance || '未检测到手掌，请重试');
      alert(data.guidance || data.error || '分析失败');
      return;
    }

    showPalmResult(data);

  } catch (e) {
    console.error('Server analysis error, using browser fallback:', e);
    // 降级：浏览器端体质分析
    try {
      const landmarks = Camera._lastLandmarks || null;
      const features = extractPalmFeatures(landmarks, 640, 480, imageStats);
      const result = inferConstitution(features, age);
      hideLoading();

      // 构建与服务端一致的数据结构
      const data = {
        success: true,
        ...result,
        diet: result.diet || [],
        exercise: result.exercise || [],
        lifestyle: result.lifestyle || [],
        integrated: {
          one_liner: `${result.mythic_name}（${result.constitution_name}）· 身体年龄${result.body_age}岁`,
          wuxing_synthesis: result.description,
          emotional_care: [],
        },
        references: [],
        _offline: true,
      };
      showPalmResult(data);
    } catch (e2) {
      hideLoading();
      Agent.speak('分析出错了，请检查网络后重试');
      console.error(e2);
    }
  }
}

function showPalmResult(data) {
  lastResult = data;
  Storage.addPalmResult(data);
  updateStreakUI(Storage.getStreak());

  const ageDiff = Math.round(data.age_diff);
  let summary = `${data.mythic_name}，${data.constitution_name}。`;
  summary += `身体年龄${Math.round(data.body_age)}岁，`;
  if (ageDiff < -2) {
    summary += `比身份证年轻${Math.abs(ageDiff)}岁。`;
  } else if (ageDiff > 2) {
    summary += `需要关注调理了。`;
  } else {
    summary += `与年龄相符。`;
  }

  if (data.description) summary += data.description + '。';

  if (data.zhouyi && data.zhouyi.trigram) {
    summary += `对应周易${data.zhouyi.primary_bagua}卦${data.zhouyi.trigram}。`;
  }

  if (data.integrated?.one_liner) summary += data.integrated.one_liner + '。';
  if (data.diet?.[0]) summary += `饮食上：${data.diet[0]}。`;

  Agent.speak(summary);

  setTimeout(() => {
    if (confirm('想看你的掌纹体质卡片吗？可以保存分享哦~')) {
      ShareCard.generate(data);
    }
  }, 3000);
}

// 从文件选择
document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById('fileInput');
  if (fileInput) {
    fileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const age = document.getElementById('ageInput')?.value || '30';
      showLoading('灵枢正在分析...');
      try {
        const form = new FormData();
        form.append('image', file);
        form.append('age', age);
        const resp = await fetch('/api/analyze', { method: 'POST', body: form });
        const data = await resp.json();
        hideLoading();
        if (data.success) {
          lastResult = data;
          Storage.addPalmResult(data);
          const summary = `${data.mythic_name}——${data.constitution_name}。` +
            (data.integrated?.one_liner || data.description || '');
          Agent.speak(summary);
          setTimeout(() => { if (confirm('查看分享卡片？')) ShareCard.generate(data); }, 2000);
        } else {
          Agent.speak(data.guidance || '未检测到手掌');
        }
      } catch (e) {
        hideLoading();
        console.error(e);
      }
    });
  }
});

// ==================== 运势 ====================
async function getFortune() {
  const weather = document.getElementById('weatherInput')?.value?.trim();
  const activity = document.getElementById('activityInput')?.value?.trim();
  if (!weather || !activity) {
    Agent.speak('请告诉我天气和你计划要做的事~');
    return;
  }

  showLoading('灵枢在推演卦象...');

  let f = null;
  try {
    const form = new FormData();
    form.append('weather', weather);
    form.append('activity', activity);
    const resp = await fetch('/api/daily', { method: 'POST', body: form });
    if (resp.ok) {
      const data = await resp.json();
      if (data.fortune) { f = data.fortune; }
    }
  } catch (e) {
    console.log('运势API不可用，使用本地引擎');
  }

  if (!f) {
    f = dailyFortune(weather, activity, new Date());
  }

  hideLoading();
  showFortune(f);
}

function showFortune(f) {
  const display = document.getElementById('fortuneResult');
  display.style.display = 'block';

  const name = f.hexagram?.name || f.hexagram_name || '';
  const symbol = f.hexagram?.symbol || f.hexagram_symbol || '';
  const meaning = f.hexagram?.meaning || f.hexagram_meaning || '';
  const advice = f.advice || '';
  const caution = f.caution || '';
  const dir = f.lucky_direction || '';
  const elem = f.lucky_element || '';
  const emotion = f.emotional_message || '';

  document.getElementById('hexagramDisplay').innerHTML =
    `<div class="hexagram">${symbol} ${name}</div>
     <div class="hexagram-meaning">${meaning}</div>`;
  document.getElementById('fortuneAdvice').innerHTML =
    `<p>${typeof advice === 'string' ? '🎯 ' + advice : advice.map(a => '🎯 ' + a).join('<br>')}</p>
     <p>⚠️ ${typeof caution === 'string' ? caution : caution.join('；')}</p>
     <p>🧭 吉方：${dir} ｜ 幸运元素：${elem}</p>
     <p class="emotional-msg">${emotion}</p>`;

  Agent.speak(`${name}。${typeof advice === 'string' ? advice : advice[0]}。${typeof caution === 'string' ? caution : caution[0]}`);
}

// ==================== 情绪伴侣 ====================
function setScenario(s) {
  currentScenario = s;
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  document.querySelector(`.chip[onclick*="${s}"]`)?.classList.add('active');

  // 切换场景时给个提示
  const scene = getCompanionResponse(s, '');
  const reply = scene.reply || `已切换到${s}场景~ 跟我说说吧`;
  document.getElementById('companionResponse').style.display = 'block';
  document.getElementById('companionResponse').innerHTML = `
    <div class="companion-bubble">
      <p style="white-space:pre-line">${reply}</p>
    </div>`;
}

async function talkToCompanion() {
  const msg = document.getElementById('companionInput')?.value?.trim();
  if (!msg) {
    Agent.speak('跟我说点什么吧~');
    return;
  }

  // 同音词归一化
  const normalized = msg.replace(/林叔|灵书|零书|凌舒|领书/gi, '灵枢');
  // 树洞里打招呼/功能询问 → 本地快速回复，不走 LLM
  if (/你好|嗨|hi|hello|在吗|灵枢|你是谁|叫什么|能做什么|会什么|功能/.test(normalized)) {
    document.getElementById('companionInput').value = '';
    const reply = '你好呀！我是灵枢，你的掌纹体质管家~ 想拍掌纹看体质、查运势、还是聊聊心事？直接点底部按钮就可以啦。';
    const display = document.getElementById('companionResponse');
    display.style.display = 'block';
    display.innerHTML = `<div class="companion-bubble"><p>${reply}</p></div>`;
    Agent.speak(reply, 'gentle');
    return;
  }

  showLoading('灵枢正在倾听...');

  let data = null;
  try {
    // 直接调用情绪伴侣专用端点（LLM 驱动，豆包/DS 级对话质量）
    const form = new FormData();
    form.append('message', msg);
    form.append('scenario', currentScenario || 'general');
    form.append('history', JSON.stringify(Agent.chatHistory));

    const resp = await fetch('/api/companion/chat', { method: 'POST', body: form });
    data = await resp.json();
  } catch (e) {
    console.error('Companion API error:', e);
  }

  hideLoading();

  if (!data || data.error) {
    // 降级：走通用 Agent 处理
    data = await Agent.processInput(msg);
  }

  // 更新精灵聊天历史
  Agent.chatHistory.push({ role: 'user', content: msg });
  Agent.chatHistory.push({ role: 'assistant', content: data.reply || '' });
  if (Agent.chatHistory.length > 10) Agent.chatHistory = Agent.chatHistory.slice(-10);

  const display = document.getElementById('companionResponse');
  display.style.display = 'block';
  const affirmation = data.affirmation ? `<p class="affirmation">💫 ${data.affirmation}</p>` : '';
  const sourceTag = data.source === 'local' ? '' : '';
  display.innerHTML = `
    <div class="companion-bubble">
      <p style="white-space:pre-line">${data.reply || ''}</p>
      ${affirmation}
    </div>`;
  document.getElementById('companionInput').value = '';

  // 精灵说话 → 说完自动聚焦输入框，形成对话循环
  const emotion = data.emotion || 'gentle';
  Agent.speak(data.reply || '', emotion).then(() => {
    if (currentTab === 3) {
      document.getElementById('companionInput')?.focus();
    }
  });

  if (data.action) {
    setTimeout(() => Agent._executeAction(data.action), 1500);
  }
}

// ==================== 黄历加载 ====================
async function loadAlmanac() {
  try {
    const resp = await fetch('/api/daily');
    if (resp.ok) {
      const data = await resp.json();
      if (data.almanac) {
        renderAlmanac(data.almanac);
        return;
      }
    }
  } catch (e) {
    console.log('黄历API不可用，使用本地引擎');
  }

  const a = getAlmanac(new Date());
  renderAlmanac(a);
}

function renderAlmanac(a) {
  document.getElementById('topbarDate').textContent = a.lunar_date;
  document.getElementById('almanacDate').textContent =
    `${a.lunar_date} · ${a.shengxiao}年`;
  document.getElementById('almanacJianchu').textContent =
    `${a.jianchu || a.jian_chu}日 · ${a.xiu28 || a.xiu_28}（${(a.xiu_meaning || '').split('·')[0] || ''}）`;
  document.getElementById('yiList').textContent = (a.yi || []).join('·') || '—';
  document.getElementById('jiList').textContent = (a.ji || []).join('·') || '—';
}

// ==================== UI 辅助 ====================
function updateStreakUI(streak) {
  document.getElementById('topbarStreak').textContent = '🔥 ' + streak + '天';
  document.getElementById('streakCount').textContent = streak;
  document.getElementById('scanCount').textContent = Storage.getScanCount();
  document.getElementById('weeklyChange').textContent = Storage.getWeeklyChange();
}

function updateBackground() {
  const hour = new Date().getHours();
  const bg = document.getElementById('bgGradient');
  if (hour < 8) {
    bg.style.background = 'linear-gradient(180deg, #0a1628, #1a2a40, #2a3a50)';
  } else if (hour < 17) {
    bg.style.background = 'linear-gradient(180deg, #1a3a50, #2a5a40, #3a6a30)';
  } else {
    bg.style.background = 'linear-gradient(180deg, #0a1628, #1a2840, #2a1a30)';
  }
}

function showLoading(text) {
  document.getElementById('loadingText').textContent = text || '灵枢正在分析...';
  document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
  document.getElementById('loadingOverlay').style.display = 'none';
}

// ==================== LLM 配置管理 ====================
const PROVIDER_DEFAULTS = {
  deepseek: { url: 'https://api.deepseek.com/v1/chat/completions', model: 'deepseek-chat' },
  doubao:   { url: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions', model: 'doubao-pro-32k' },
  qwen:     { url: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', model: 'qwen-turbo' },
  custom:   { url: '', model: '' },
};

function onProviderChange() {
  const p = document.getElementById('cfgProvider')?.value || 'deepseek';
  const def = PROVIDER_DEFAULTS[p];
  if (def && p !== 'custom') {
    document.getElementById('cfgApiUrl').value = def.url;
    document.getElementById('cfgModel').value = def.model;
  }
}

async function loadLLMConfig() {
  try {
    const resp = await fetch('/api/config/llm');
    const data = await resp.json();
    document.getElementById('cfgApiUrl').value = data.api_url || '';
    document.getElementById('cfgApiKey').value = data.api_key || '';
    document.getElementById('cfgModel').value = data.model || '';
    document.getElementById('cfgAgentName').value = data.agent_name || '灵枢';
    const sel = document.getElementById('cfgProvider');
    for (const opt of sel.options) {
      if (opt.value === data.provider) { sel.value = data.provider; break; }
    }
    document.getElementById('cfgStatus').textContent = '配置已加载';
  } catch (e) {
    document.getElementById('cfgStatus').textContent = '加载失败: ' + e.message;
  }
}

async function saveLLMConfig() {
  const form = new FormData();
  form.append('provider', document.getElementById('cfgProvider').value);
  form.append('api_url', document.getElementById('cfgApiUrl').value);
  form.append('api_key', document.getElementById('cfgApiKey').value);
  form.append('model', document.getElementById('cfgModel').value);
  form.append('temperature', document.getElementById('cfgTemp').value);
  form.append('agent_name', document.getElementById('cfgAgentName')?.value || '灵枢');

  try {
    const resp = await fetch('/api/config/llm', { method: 'POST', body: form });
    const data = await resp.json();
    // 更新前端 Agent 名字
    Agent.userName = document.getElementById('cfgAgentName')?.value || '灵枢';
    document.getElementById('cfgStatus').textContent = data.success ? '✅ 已保存，重启服务生效' : '❌ ' + (data.error || '保存失败');
  } catch (e) {
    document.getElementById('cfgStatus').textContent = '❌ 保存失败: ' + e.message;
  }
}

// Temperature slider
document.addEventListener('DOMContentLoaded', () => {
  const slider = document.getElementById('cfgTemp');
  if (slider) {
    slider.oninput = () => {
      document.getElementById('cfgTempVal').textContent = slider.value;
    };
  }
});

// ==================== 语音测试 ====================
async function testVoice() {
  const emotion = document.getElementById('voiceTestEmotion')?.value || 'gentle';
  const status = document.getElementById('voiceStatus');
  status.textContent = '正在生成语音...';

  const testTexts = {
    gentle: '你好，我是灵枢。你的手掌，写着你的出厂设置。今天想做什么呢？',
    calm: '你好，我是灵枢。根据中医体质学说，每个人的掌纹都反映着独特的身体状态。',
    story: '《黄帝内经》有云：视其外应，以知其内脏。手掌上的每一条纹路，都是身体发出的信号。',
    warm: '嗨！我是灵枢，你的掌纹小管家~ 来来来，拍一张手掌，我帮你看看身体状态！',
  };
  const text = testTexts[emotion] || testTexts.gentle;

  try {
    const form = new FormData();
    form.append('text', text);
    form.append('emotion', emotion);
    form.append('rate', '+0%');
    form.append('pitch', '+0Hz');

    const resp = await fetch('/api/tts', { method: 'POST', body: form });

    if (!resp.ok) {
      status.textContent = '❌ TTS API 返回错误: ' + resp.status;
      return;
    }

    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.onended = () => { URL.revokeObjectURL(url); status.textContent = '✅ 播放完成'; };
    audio.onerror = () => { URL.revokeObjectURL(url); status.textContent = '❌ 播放失败'; };
    audio.play().catch(() => status.textContent = '❌ 播放被阻止（浏览器限制）');
    status.textContent = '🔊 正在播放...（' + (blob.size/1024).toFixed(1) + 'KB）';

  } catch (e) {
    status.textContent = '❌ ' + e.message;
  }
}
