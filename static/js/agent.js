// ============================================
// 灵枢 — Agent 精灵引擎 v3
// 后端智能对话 + 前端动画 + 情绪化语音 + 形象变换
// ============================================

const Agent = {
  state: 'idle',
  orb: null, emoji: null, bubble: null, bubbleText: null, statusEl: null,
  userName: '朋友',
  chatHistory: [],
  currentEmotion: 'gentle',

  // 精灵形象映射（根据情绪变换）
  emotionIcons: {
    gentle: '🧚',
    excited: '✨',
    calm: '🧘',
    sad: '🫂',
    anger: '🛡️',
    anxiety: '💙',
    confused: '🤔',
  },

  greetings: {
    morning: ['早上好~ 新的一天，你的掌纹今天会说什么呢？', '早安！昨晚睡得好吗？要不要看看今天的运势？'],
    afternoon: ['下午好~ 忙了一天，停下来看看自己的身体状态吧。', '午后时光~ 要不要拍个掌纹？'],
    evening: ['晚上好~ 一天结束了，来树洞聊聊吧。', '夜深了，灵枢还陪着你~'],
  },

  init() {
    this.orb = document.getElementById('agentOrb');
    this.emoji = document.getElementById('agentEmoji');
    this.bubble = document.getElementById('agentBubble');
    this.bubbleText = document.getElementById('bubbleText');
    this.statusEl = document.getElementById('agentStatus');
  },

  // 根据情绪切换精灵形象
  setEmotion(emotion) {
    this.currentEmotion = emotion;
    if (this.emoji) {
      this.emoji.textContent = this.emotionIcons[emotion] || '🧚';
      this.emoji.style.transform = 'scale(1.15)';
      setTimeout(() => { if (this.emoji) this.emoji.style.transform = 'scale(1)'; }, 250);
    }
  },

  setState(s) {
    this.state = s;
    if (this.orb) this.orb.className = 'agent-orb state-' + s;
    const map = { idle:'点击话筒跟我说话', listening:'正在听...', thinking:'思考中...', speaking:'正在说...' };
    if (this.statusEl) this.statusEl.textContent = map[s] || '';
  },

  showBubble(text, dur = 4000) {
    if (this.bubbleText) this.bubbleText.textContent = text;
    if (this.bubble) this.bubble.classList.add('show');
    clearTimeout(this._bt);
    if (dur > 0) this._bt = setTimeout(() => { if (this.bubble) this.bubble.classList.remove('show'); }, dur);
  },

  hideBubble() {
    if (this.bubble) this.bubble.classList.remove('show');
  },

  async speak(text, emotion) {
    emotion = emotion || 'gentle';
    this.setEmotion(emotion);
    this.showBubble(text, 0);
    this.setState('speaking');
    await Voice.speak(text, { emotion });
    this.setState('idle');
    this._bt = setTimeout(() => this.hideBubble(), 3000);
    // 恢复默认形象
    setTimeout(() => { if (this.state === 'idle') this.setEmotion('gentle'); }, 3500);
  },

  greet() {
    const h = new Date().getHours();
    const pool = h < 10 ? this.greetings.morning : h < 17 ? this.greetings.afternoon : this.greetings.evening;
    return pool[Math.floor(Math.random() * pool.length)];
  },

  // 核心：智能对话（LLM优先，本地引擎降级）
  async processInput(text) {
    this.showBubble('"' + (text.length > 30 ? text.slice(0, 27) + '...' : text) + '"', 2000);
    this.setState('thinking');
    this.setEmotion('confused');

    try {
      const form = new FormData();
      form.append('message', text);
      form.append('name', this.userName);
      form.append('history', JSON.stringify(this.chatHistory));
      // 传递当前树洞场景，让服务端LLM给出场景化回复
      if (typeof currentScenario !== 'undefined') {
        form.append('scenario', currentScenario);
      }

      const resp = await fetch('/api/chat', { method: 'POST', body: form });
      const data = await resp.json();

      this.chatHistory.push({ role: 'user', content: text });
      this.chatHistory.push({ role: 'assistant', content: data.reply });
      if (this.chatHistory.length > 10) this.chatHistory = this.chatHistory.slice(-10);

      const emotion = data.emotion || 'gentle';
      await this.speak(data.reply, emotion);

      if (data.action) { this._executeAction(data.action); }

      return data;

    } catch (e) {
      console.error('Chat API error:', e);
      // 降级：使用本地智能引擎
      return await this._localFallback(text);
    }
  },

  // 本地智能降级引擎
  async _localFallback(text) {
    // 先做意图识别
    const intent = this._localIntent(text);
    let reply, emotion = 'gentle', action = null;

    if (intent.action) {
      action = intent.action;
    }

    // 在树洞页面或用户消息是情绪倾诉 → 用 chatCompanion
    if (typeof currentTab !== 'undefined' && currentTab === 3) {
      const history = this.chatHistory.filter(h => h.role === 'user').map(h => ({ role: 'user', text: h.content }));
      const cr = chatCompanion(text, history);
      reply = cr.reply;
      emotion = cr.suggestFollowup ? 'gentle' : 'calm';
      if (cr.affirmation) {
        // 追加肯定语句
        reply += '\n\n💫 ' + cr.affirmation;
      }
    } else if (intent.type === 'companion') {
      const cr = chatCompanion(text, []);
      reply = cr.reply;
      emotion = 'calm';
      if (cr.affirmation) reply += '\n\n💫 ' + cr.affirmation;
      action = 'switch_tab:companion';
    } else if (intent.type === 'palm') {
      reply = intent.reply || '好的，让我看看你的掌纹~ 请切换到掌纹页面，手掌平放镜头前拍照。';
      emotion = 'excited';
      action = 'switch_tab:palm';
    } else if (intent.type === 'fortune') {
      reply = intent.reply || '帮你查运势~ 切换到运势页面，告诉我天气和计划吧。';
      emotion = 'excited';
      action = 'switch_tab:fortune';
    } else if (intent.type === 'greeting') {
      reply = this.greet();
      emotion = 'gentle';
    } else if (intent.type === 'goodbye') {
      reply = '拜拜~ 明天记得来找我看掌纹哦。做个好梦！';
      emotion = 'gentle';
    } else {
      // 通用对话——走智能伴侣引擎
      const cr = chatCompanion(text, []);
      reply = cr.reply;
      emotion = 'calm';
    }

    this.chatHistory.push({ role: 'user', content: text });
    this.chatHistory.push({ role: 'assistant', content: reply });
    if (this.chatHistory.length > 10) this.chatHistory = this.chatHistory.slice(-10);

    await this.speak(reply, emotion);

    if (action) {
      setTimeout(() => this._executeAction(action), 1500);
    }

    return { reply, emotion, action, source: 'local' };
  },

  // 本地轻量意图识别
  _localIntent(msg) {
    const t = (msg || '').toLowerCase();
    if (/拍|照|掌纹|长文|藏文|扫|看手|体质|分析|测|手掌|照相|识别/.test(t)) {
      return { type: 'palm', action: 'switch_tab:palm', reply: '好的~ 切换到掌纹页面，把手掌平放在镜头前，五指自然张开，我帮你分析体质！' };
    }
    if (/运势|运气|黄历|今天.*日子|宜忌|今日|每日|好不好/.test(t)) {
      return { type: 'fortune', action: 'switch_tab:fortune', reply: '想看运势是吧？切换到运势页面，告诉我天气和你打算做的事，我帮你推演卦象~' };
    }
    if (/树洞|树冻|书洞|倾诉|聊天|陪我说|谈谈心|想找人|说说话|梦到|梦见|做梦|昨晚梦|梦里|解梦/.test(t)) {
      return { type: 'companion', action: 'switch_tab:companion', reply: '梦是身体的密语。去树洞页面，详细说说你的梦，我用中医五行帮你解读~' };
    }
    if (/难过|伤心|哭|压力|焦虑|烦|累|不开心|郁闷|失落|崩溃|绝望|失恋|分手|吵架|孤独|孤单|迷茫|痛苦|气死|委屈|想哭/.test(t)) {
      return { type: 'companion', action: 'switch_tab:companion', reply: '我听到了。你的感受是真实的。愿意多说一点吗？我在树洞等你~' };
    }
    if (/你好|嗨|hi|hello|在吗|灵枢|你是谁|叫什么|名字/.test(t)) {
      return { type: 'greeting', action: null };
    }
    if (/再见|拜拜|bye|晚安|睡了|走了/.test(t)) {
      return { type: 'goodbye', action: null };
    }
    return { type: 'chat', action: null };
  },

  _executeAction(action) {
    if (action === 'switch_tab:palm') switchTab(1);
    else if (action === 'switch_tab:fortune') switchTab(2);
    else if (action === 'switch_tab:companion') switchTab(3);
    else if (action === 'switch_tab:home') switchTab(0);
  },
};
