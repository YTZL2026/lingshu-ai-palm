// ============================================
// 灵枢 — 语音模块 v7 (纯 TTS)
// STT 已移除，语音输入由系统键盘自带的麦克风完成
// TTS: edge-tts → 浏览器内置降级
// ============================================

const Voice = {
  synth: window.speechSynthesis,
  onStateChange: null,
  _audioEl: null,
  _useServerTTS: true,

  init() {
    this._audioEl = new Audio();
  },

  // === TTS: edge-tts → 浏览器降级 ===
  async speak(text, opts = {}) {
    if (!text) return;
    console.log('[Voice] speak:', text.substring(0, 50));
    if (this.onStateChange) this.onStateChange('speaking');

    // 1. 服务端 edge-tts
    if (this._useServerTTS) {
      try {
        const form = new FormData();
        form.append('text', text);
        form.append('emotion', opts.emotion || 'gentle');
        form.append('rate', '+0%');
        form.append('pitch', '+0Hz');
        const resp = await fetch('/api/tts', { method: 'POST', body: form });
        if (resp.ok) {
          const blob = await resp.blob();
          if (blob.size > 100) {
            const url = URL.createObjectURL(blob);
            await new Promise((resolve) => {
              this._audioEl.src = url;
              this._audioEl.onended = () => { URL.revokeObjectURL(url); resolve(); };
              this._audioEl.onerror = () => { URL.revokeObjectURL(url); resolve(); };
              this._audioEl.play().catch(() => resolve());
            });
            if (this.onStateChange) this.onStateChange('idle');
            return;
          }
        }
      } catch (e) {
        console.warn('[Voice] server TTS error:', e.message);
      }
    }

    // 2. 浏览器内置 TTS
    if (this.synth) {
      this.synth.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = 'zh-CN';
      u.rate = 1.0;
      u.pitch = 1.0;
      await new Promise((resolve) => {
        u.onend = resolve;
        u.onerror = resolve;
        const voices = this.synth.getVoices();
        const zh = voices.find(v => v.lang.startsWith('zh-CN')) || voices[0];
        if (zh) u.voice = zh;
        this.synth.speak(u);
      });
    }
    if (this.onStateChange) this.onStateChange('idle');
  },

  stop() {
    if (this.synth) this.synth.cancel();
  },
};
