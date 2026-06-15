// ============================================
// 灵枢 — 本地存储模块
// LocalStorage 封装：打卡 / 掌纹历史 / 设置
// ============================================

const Storage = {

  // ---- 打卡 ----
  checkIn() {
    const today = new Date().toDateString();
    const lastDate = localStorage.getItem('ling_lastDate');
    let streak = parseInt(localStorage.getItem('ling_streak') || '0');

    if (lastDate === today) {
      return streak; // 今天已打卡
    }

    const yesterday = new Date(Date.now() - 86400000).toDateString();
    if (lastDate === yesterday) {
      streak += 1; // 连续
    } else {
      streak = 1;  // 断了，重来
    }

    localStorage.setItem('ling_lastDate', today);
    localStorage.setItem('ling_streak', String(streak));
    return streak;
  },

  getStreak() {
    return parseInt(localStorage.getItem('ling_streak') || '0');
  },

  // ---- 掌纹历史（最多7条） ----
  addPalmResult(result) {
    let history = this.getPalmHistory();
    history.unshift({
      date: new Date().toISOString(),
      constitution_name: result.constitution_name,
      constitution_id: result.constitution_id,
      mythic_name: result.mythic_name,
      body_age: result.body_age,
      chronological_age: result.chronological_age,
      icon: result.icon,
      color: result.color,
      confidence: result.confidence,
    });
    if (history.length > 7) history = history.slice(0, 7);
    localStorage.setItem('ling_palmHistory', JSON.stringify(history));

    // 更新扫描计数
    const count = parseInt(localStorage.getItem('ling_scanCount') || '0');
    localStorage.setItem('ling_scanCount', String(count + 1));
  },

  getPalmHistory() {
    try {
      return JSON.parse(localStorage.getItem('ling_palmHistory') || '[]');
    } catch { return []; }
  },

  getScanCount() {
    return parseInt(localStorage.getItem('ling_scanCount') || '0');
  },

  // ---- 本周变化 ----
  getWeeklyChange() {
    const history = this.getPalmHistory();
    if (history.length < 2) return '—';
    const latest = history[0];
    const oldest = history[history.length - 1];
    if (latest.constitution_id === oldest.constitution_id) return '稳定';
    return '有变';
  },

  // ---- 设置 ----
  get(key, def) {
    try { return JSON.parse(localStorage.getItem('ling_' + key)); }
    catch { return def; }
  },

  set(key, val) {
    localStorage.setItem('ling_' + key, JSON.stringify(val));
  },
};
