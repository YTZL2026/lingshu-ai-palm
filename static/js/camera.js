// ============================================
// 灵枢 — 相机 + MediaPipe Hands 模块
// 手掌检测在浏览器端完成（MediaPipe Hands WASM）
// 拍照后发给 Python 后端做特征提取+体质推理
// ============================================

const Camera = {
  video: null,
  canvas: null,
  stream: null,
  facingMode: 'environment',
  hands: null,       // MediaPipe Hands 实例
  isReady: false,

  async init() {
    this.video = document.getElementById('cameraVideo');
    this.canvas = document.getElementById('cameraCanvas');
    this.canvas.width = 640;
    this.canvas.height = 480;

    // 加载 MediaPipe Hands（CDN·8s超时）
    try {
      const { Hands } = await Promise.race([
        import('https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4/hands.js'),
        new Promise((_, reject) => setTimeout(() => reject(new Error('MediaPipe CDN 超时')), 8000))
      ]);
      this.hands = new Hands({
        locateFile: (file) =>
          `https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4/${file}`,
      });
      this.hands.setOptions({
        maxNumHands: 1,
        modelComplexity: 1,
        minDetectionConfidence: 0.7,
        minTrackingConfidence: 0.5,
      });

      this.hands.onResults((results) => {
        this._onHandResults(results);
      });

      this.isReady = true;
      console.log('✅ MediaPipe Hands 就绪');
    } catch (e) {
      console.warn('⚠️ MediaPipe 加载失败，降级为基础模式:', e.message);
      this.isReady = false;
    }
  },

  async start() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: this.facingMode,
          width: { ideal: 640 },
          height: { ideal: 480 },
        },
        audio: false,
      });
      this.video.srcObject = this.stream;
      await this.video.play();

      if (this.isReady) {
        this._detectLoop();
      }
    } catch (e) {
      console.error('相机启动失败:', e);
      alert('无法打开相机，请检查权限设置');
    }
  },

  stop() {
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.stream = null;
    }
    if (this.hands) {
      this.hands.close();
      this.hands = null;
    }
  },

  switchFacing() {
    this.facingMode = this.facingMode === 'environment' ? 'user' : 'environment';
    this.stop();
    this.start();
  },

  // 拍照 → 返回 dataUrl + 图像统计数据
  capture() {
    const vw = this.video.videoWidth || 640;
    const vh = this.video.videoHeight || 480;
    this.canvas.width = vw;
    this.canvas.height = vh;
    const ctx = this.canvas.getContext('2d');
    ctx.drawImage(this.video, 0, 0, vw, vh);

    // 提取图像统计信息（用于浏览器端体质分析）
    const imageData = ctx.getImageData(0, 0, vw, vh);
    const stats = this._computeImageStats(imageData.data, vw, vh);
    this._lastImageStats = stats;

    return {
      dataUrl: this.canvas.toDataURL('image/jpeg', 0.85),
      stats: stats,
    };
  },

  // 计算基本图像统计
  _computeImageStats(pixels, w, h) {
    let totalR = 0, totalG = 0, totalB = 0, totalBrightness = 0;
    const n = pixels.length / 4;
    // 采样（每4个像素取1个，减少计算量）
    const step = 4 * 4;
    let count = 0;
    for (let i = 0; i < pixels.length; i += step) {
      const r = pixels[i], g = pixels[i + 1], b = pixels[i + 2];
      totalR += r; totalG += g; totalB += b;
      totalBrightness += (r + g + b) / 3;
      count++;
    }
    const avgR = totalR / count;
    const avgG = totalG / count;
    const avgB = totalB / count;
    const avgBrightness = totalBrightness / count;

    // 计算标准差
    let variance = 0;
    for (let i = 0; i < pixels.length; i += step) {
      const bright = (pixels[i] + pixels[i + 1] + pixels[i + 2]) / 3;
      variance += (bright - avgBrightness) ** 2;
    }
    const stdDev = Math.sqrt(variance / count);

    // 红润度：红色通道相对强度
    const redness = Math.min(100, Math.max(10, (avgR / Math.max(1, (avgG + avgB) / 2)) * 50));

    return {
      redness: Math.round(redness),
      brightness: Math.round(Math.min(100, Math.max(10, avgBrightness / 2.55))),
      contrast: Math.round(Math.min(100, Math.max(10, stdDev / 1.28))),
      stdDev: Math.round(stdDev),
    };
  },

  getLastImageStats() {
    return this._lastImageStats || { redness: 50, brightness: 50, contrast: 50, stdDev: 30 };
  },

  // MediaPipe 检测循环
  async _detectLoop() {
    if (!this.stream || !this.hands) return;
    if (this.video.readyState >= 2) {
      await this.hands.send({ image: this.video });
    }
    requestAnimationFrame(() => this._detectLoop());
  },

  _onHandResults(results) {
    // 保存最新关键点（供浏览器端离线分析使用）
    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
      this._lastLandmarks = results.multiHandLandmarks[0];
    } else {
      this._lastLandmarks = null;
    }

    // 绘制关键点到 canvas 上
    const ctx = this.canvas.getContext('2d');
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);

    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
      const landmarks = results.multiHandLandmarks[0];
      // 绘制关键点
      ctx.fillStyle = '#4fc3f7';
      for (const lm of landmarks) {
        ctx.beginPath();
        ctx.arc(lm.x * this.canvas.width, lm.y * this.canvas.height, 3, 0, 2 * Math.PI);
        ctx.fill();
      }
      // 绘制连线
      ctx.strokeStyle = 'rgba(79,195,247,0.5)';
      ctx.lineWidth = 1;
      const connections = [[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[0,9],[9,10],[10,11],[11,12],[0,13],[13,14],[14,15],[15,16],[0,17],[17,18],[18,19],[19,20]];
      for (const [a, b] of connections) {
        ctx.beginPath();
        ctx.moveTo(landmarks[a].x * this.canvas.width, landmarks[a].y * this.canvas.height);
        ctx.lineTo(landmarks[b].x * this.canvas.width, landmarks[b].y * this.canvas.height);
        ctx.stroke();
      }
      // 更新引导提示
      const guide = document.getElementById('cameraGuide');
      if (guide) guide.querySelector('p').textContent = '✅ 手掌已检测到，点击拍摄';
    }
  },
};

// 切换到掌纹Tab时启动相机
function switchCamera() {
  Camera.switchFacing();
}
