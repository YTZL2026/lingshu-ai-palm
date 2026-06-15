// ============================================
// 灵枢 — Canvas 分享卡片生成
// 前端纯 Canvas 绘制，不依赖后端
// ============================================

const ShareCard = {

  async generate(result) {
    const canvas = document.getElementById('shareCanvas');
    const ctx = canvas.getContext('2d');
    const W = 800, H = 1200;

    // 背景
    const bgGrad = ctx.createLinearGradient(0, 0, 0, H);
    bgGrad.addColorStop(0, '#0a1628');
    bgGrad.addColorStop(0.5, '#0f1f38');
    bgGrad.addColorStop(1, '#0a1628');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, W, H);

    // 顶部装饰线
    ctx.fillStyle = result.color || '#c9a84c';
    ctx.fillRect(0, 0, W, 4);

    // 中央图标
    ctx.font = '80px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(result.icon || '🖐️', W / 2, 140);

    // 体质名称
    ctx.fillStyle = result.color || '#c9a84c';
    ctx.font = 'bold 48px "Microsoft YaHei", sans-serif';
    ctx.fillText(result.mythic_name || '', W / 2, 240);

    ctx.fillStyle = '#8899aa';
    ctx.font = '24px "Microsoft YaHei", sans-serif';
    ctx.fillText(result.constitution_name || '', W / 2, 290);

    // 分隔线
    ctx.strokeStyle = result.color || '#c9a84c';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(200, 340);
    ctx.lineTo(600, 340);
    ctx.stroke();

    // 身体年龄区
    const yAge = 390;
    ctx.fillStyle = '#1a2a3a';
    ctx.beginPath();
    this._roundRect(ctx, 100, yAge, 600, 180, 20);
    ctx.fill();

    ctx.fillStyle = result.color || '#c9a84c';
    ctx.font = 'bold 56px "Microsoft YaHei", sans-serif';
    ctx.fillText(Math.round(result.body_age || 30) + '岁', W / 2 - 80, yAge + 65);

    ctx.fillStyle = '#8899aa';
    ctx.font = '20px "Microsoft YaHei", sans-serif';
    ctx.fillText('身体年龄', W / 2 - 80, yAge + 110);

    ctx.fillStyle = '#5a6a7a';
    ctx.font = '28px "Microsoft YaHei", sans-serif';
    ctx.fillText('VS', W / 2, yAge + 85);

    ctx.fillStyle = '#8899aa';
    ctx.font = 'bold 56px "Microsoft YaHei", sans-serif';
    ctx.fillText(Math.round(result.chronological_age || 30) + '岁', W / 2 + 80, yAge + 65);

    ctx.font = '20px "Microsoft YaHei", sans-serif';
    ctx.fillText('身份证年龄', W / 2 + 80, yAge + 110);

    // 年龄差异
    const ageDiff = result.age_diff || 0;
    let diffText, diffColor;
    if (ageDiff < -2) {
      diffText = `比实际年轻 ${Math.abs(Math.round(ageDiff))} 岁 🎉`;
      diffColor = '#27ae60';
    } else if (ageDiff > 2) {
      diffText = `比实际大 ${Math.round(ageDiff)} 岁`;
      diffColor = '#f39c12';
    } else {
      diffText = '与身份证年龄相符';
      diffColor = '#8899aa';
    }
    ctx.fillStyle = diffColor;
    ctx.font = '20px "Microsoft YaHei", sans-serif';
    ctx.fillText(diffText, W / 2, yAge + 150);

    // 描述
    if (result.description) {
      ctx.fillStyle = '#8899aa';
      ctx.font = '18px "Microsoft YaHei", sans-serif';
      const desc = result.description.length > 60
        ? result.description.slice(0, 57) + '...' : result.description;
      ctx.fillText(desc, W / 2, 620);
    }

    // 底部
    ctx.fillStyle = '#c9a84c';
    ctx.font = 'bold 28px "Microsoft YaHei", sans-serif';
    ctx.fillText('🖐️ AI 掌纹溯源 · 灵枢', W / 2, 700);

    ctx.fillStyle = '#8899aa';
    ctx.font = '18px "Microsoft YaHei", sans-serif';
    ctx.fillText('拍一张手掌 · 了解你的身体出厂设置', W / 2, 740);

    // 底部装饰
    ctx.fillStyle = result.color || '#c9a84c';
    ctx.fillRect(0, H - 4, W, 4);

    // 水印
    ctx.fillStyle = '#3a4a5a';
    ctx.font = '16px "Microsoft YaHei", sans-serif';
    ctx.fillText('中医体质分析仅供参考，不构成医疗诊断', W / 2, H - 50);

    // 显示弹窗
    document.getElementById('shareModal').style.display = 'flex';
  },

  _roundRect(ctx, x, y, w, h, r) {
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  },
};

function downloadShareCard() {
  const canvas = document.getElementById('shareCanvas');
  const link = document.createElement('a');
  link.download = '灵枢_掌纹体质卡.png';
  link.href = canvas.toDataURL('image/png');
  link.click();
}

function closeShareModal() {
  document.getElementById('shareModal').style.display = 'none';
}
