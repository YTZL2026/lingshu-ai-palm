<div align="center">

<img src="https://img.shields.io/badge/灵枢-AI 掌纹溯源精灵-8B5CF6?style=for-the-badge" alt="LingShu">

# LingShu · 灵枢

<p>
  <strong>AI 驱动的中医体质分析精灵 — 拍照知体质，对话懂健康</strong>
</p>

<p>
  <a href="https://github.com/YTZL2026/lingshu-ai-palm/stargazers"><img src="https://img.shields.io/github/stars/86132/lingshu-ai-palm?style=flat-square" alt="Stars"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/86132/lingshu-ai-palm?style=flat-square&color=blue" alt="AGPL-3.0"></a>
  <a href="#"><img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python" alt="Python"></a>
  <a href="#"><img src="https://img.shields.io/badge/Flask-3.0-green?style=flat-square&logo=flask" alt="Flask"></a>
  <a href="#"><img src="https://img.shields.io/badge/PRs-Welcome-green?style=flat-square" alt="PRs Welcome"></a>
</p>

<p>
  <a href="#-核心功能">功能</a> ·
  <a href="#-快速开始">快速开始</a> ·
  <a href="#-技术架构">架构</a> ·
  <a href="#-路线图">路线图</a> ·
  <a href="#-开源协议">开源协议</a>
</p>

</div>

---

## 简介

灵枢（LingShu）是一个**本地优先**的 AI 中医体质分析应用。拍照上传掌纹图片，系统通过计算机视觉和深度学习模型，自动识别您的**九种中医体质类型**，给出个性化的饮食、运动和生活调理建议。

> 名字取自《灵枢经》——中医经典《黄帝内经》的"灵枢"篇。不是算命，是 AI + 中医体质学。

## 核心功能

| 功能 | 说明 |
| :---: | :--- |
|  🔬 **掌纹分析** | 拍照/上传掌纹 → OpenCV + MediaPipe 21个关键点检测 → 掌型分类 + 纹路分析 |
|  🩺 **体质判定** | 基于《中医体质分类与判定》标准，9种体质倾向评分 + 脏腑功能评估 |
|  💬 **AI 对话** | DeepSeek LLM 驱动，支持中医问答、体质解读、健康咨询 |
|  🎙️ **语音 TTS** | Edge-TTS 神经网络语音合成，6种情绪音色（温柔/沉稳/说书/温暖/活泼/柔和） |
|  📱 **多端支持** | 桌面 Web + PWA 移动端 + Android APK（Buildozer打包） |
|  🔒 **隐私安全** | 纯本地运行，数据不上传云端（AI 对话除外，可配置） |

## 快速开始

### 环境要求

- Python 3.10+
- Windows / macOS / Linux
- 摄像头（可选，用于拍照分析）

### 安装

```bash
git clone https://github.com/YTZL2026/lingshu-ai-palm.git
cd lingshu-ai-palm

# 安装依赖
pip install -r requirements.txt

# 下载手部关键点模型
python download_model.py
```

### 运行

```bash
python main.py
```

打开浏览器访问 `https://localhost:8080`

### 配置 AI 对话

编辑 `config.json`：
```json
{
  "llm": {
    "provider": "deepseek",
    "api_key": "你的 DeepSeek API Key",
    "model": "deepseek-chat",
    "temperature": 0.7
  }
}
```

## 技术架构

```
灵枢 LingShu v2
├── 前端 (Static/)
│   ├── index.html        # 4 Tab 主界面
│   ├── app.js            # 核心交互逻辑
│   ├── agent.js          # 精灵动画引擎（4状态）
│   ├── voice.js          # TTS 语音模块
│   ├── camera.js         # 摄像头拍照
│   ├── constitution.js   # 体质分析结果页
│   └── companion.js      # AI 情感陪伴模块
├── 后端 (main.py)
│   ├── /analyze          # 掌纹分析 API
│   ├── /chat             # LLM 对话 API
│   ├── /tts              # 语音合成 API
│   ├── /companion        # 精灵陪伴 API
│   └── /config/llm       # 动态配置 API
└── AI 核心
    ├── palm_detector.py       # MediaPipe 21点手部检测
    ├── feature_extractor.py   # 掌纹特征提取
    ├── constitution_engine.py # 9种体质判定引擎
    └── companion.py           # AI 人格系统
```

## 路线图

| 状态 | 计划 |
| :---: | :--- |
| ✅ | 掌纹分析 + 体质判定核心引擎 |
| ✅ | Flask Web 应用 + PWA 前端 |
| ✅ | AI 对话 + TTS 语音 |
| ✅ | Windows EXE 一键打包 |
| 🚧 | Android APK（Buildozer 打包中） |
| 📋 | iOS 支持（Capacitor.js 适配） |
| 📋 | 舌诊 + 面诊多模态融合 |
| 📋 | WeChat 小程序版本 |

## 开源协议

本项目采用 [GNU AGPL-3.0](LICENSE) 许可证。

**为什么用 AGPL-3.0 而不是 MIT？** 我们希望保护 AI 模型不被云厂商直接打包成付费 SaaS 服务。如果你只是个人/医院内部使用，完全自由。如果你要基于灵枢做商业化服务，请同样开源。

---

<p align="center">
  <sub>Built with ❤️ by <a href="https://github.com/86132">86132</a> · Inspired by 《黄帝内经·灵枢》</sub>
</p>
