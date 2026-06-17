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

  <strong>AI 椹卞姩鐨勪腑鍖讳綋璐ㄥ垎鏋愮簿鐏?鈥?鎷嶇収鐭ヤ綋璐紝瀵硅瘽鎳傚仴搴?/strong>
  <a href="https://github.com/YTZL2026/lingshu-ai-palm/stargazers"><img src="https://img.shields.io/github/stars/YTZL2026/lingshu-ai-palm?style=flat-square" alt="Stars"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/YTZL2026/lingshu-ai-palm?style=flat-square&color=blue" alt="AGPL-3.0"></a>
  <a href="#-蹇€熷紑濮?>蹇€熷紑濮?/a> 路
  <a href="#-鎶€鏈灦鏋?>鏋舵瀯</a> 路
  <a href="#-璺嚎鍥?>璺嚎鍥?/a> 路
  <a href="#-寮€婧愬崗璁?>寮€婧愬崗璁?/a>
## 绠€浠?
鐏垫灑锛圠ingShu锛夋槸涓€涓?*鏈湴浼樺厛**鐨?AI 涓尰浣撹川鍒嗘瀽搴旂敤銆傛媿鐓т笂浼犳帉绾瑰浘鐗囷紝绯荤粺閫氳繃璁＄畻鏈鸿瑙夊拰娣卞害瀛︿範妯″瀷锛岃嚜鍔ㄨ瘑鍒偍鐨?*涔濈涓尰浣撹川绫诲瀷**锛岀粰鍑轰釜鎬у寲鐨勯ギ椋熴€佽繍鍔ㄥ拰鐢熸椿璋冪悊寤鸿銆?
> 鍚嶅瓧鍙栬嚜銆婄伒鏋㈢粡銆嬧€斺€斾腑鍖荤粡鍏搞€婇粍甯濆唴缁忋€嬬殑"鐏垫灑"绡囥€備笉鏄畻鍛斤紝鏄?AI + 涓尰浣撹川瀛︺€?
|  馃敩 **鎺岀汗鍒嗘瀽** | 鎷嶇収/涓婁紶鎺岀汗 鈫?OpenCV + MediaPipe 21涓叧閿偣妫€娴?鈫?鎺屽瀷鍒嗙被 + 绾硅矾鍒嗘瀽 |
|  馃挰 **AI 瀵硅瘽** | DeepSeek LLM 椹卞姩锛屾敮鎸佷腑鍖婚棶绛斻€佷綋璐ㄨВ璇汇€佸仴搴峰挩璇?|
|  馃帣锔?**璇煶 TTS** | Edge-TTS 绁炵粡缃戠粶璇煶鍚堟垚锛?绉嶆儏缁煶鑹诧紙娓╂煍/娌夌ǔ/璇翠功/娓╂殩/娲绘臣/鏌斿拰锛?|
|  馃摫 **澶氱鏀寔** | 妗岄潰 Web + PWA 绉诲姩绔?+ Android APK锛圔uildozer鎵撳寘锛?|
|  馃敀 **闅愮瀹夊叏** | 绾湰鍦拌繍琛岋紝鏁版嵁涓嶄笂浼犱簯绔紙AI 瀵硅瘽闄ゅ锛屽彲閰嶇疆锛?|
## 蹇€熷紑濮?
- 鎽勫儚澶达紙鍙€夛紝鐢ㄤ簬鎷嶇収鍒嗘瀽锛?
git clone https://github.com/YTZL2026/lingshu-ai-palm.git
# 涓嬭浇鎵嬮儴鍏抽敭鐐规ā鍨?python download_model.py
鎵撳紑娴忚鍣ㄨ闂?`https://localhost:8080`
缂栬緫 `config.json`锛?```json
## 鎶€鏈灦鏋?
鈹?  鈹溾攢鈹€ index.html        # 4 Tab 涓荤晫闈?鈹?  鈹溾攢鈹€ app.js            # 鏍稿績浜や簰閫昏緫
鈹?  鈹溾攢鈹€ agent.js          # 绮剧伒鍔ㄧ敾寮曟搸锛?鐘舵€侊級
鈹?  鈹溾攢鈹€ voice.js          # TTS 璇煶妯″潡
鈹?  鈹溾攢鈹€ camera.js         # 鎽勫儚澶存媿鐓?鈹?  鈹溾攢鈹€ constitution.js   # 浣撹川鍒嗘瀽缁撴灉椤?鈹?  鈹斺攢鈹€ companion.js      # AI 鎯呮劅闄即妯″潡
鈹?  鈹溾攢鈹€ /analyze          # 鎺岀汗鍒嗘瀽 API
鈹?  鈹溾攢鈹€ /chat             # LLM 瀵硅瘽 API
鈹?  鈹溾攢鈹€ /tts              # 璇煶鍚堟垚 API
鈹?  鈹溾攢鈹€ /companion        # 绮剧伒闄即 API
鈹?  鈹斺攢鈹€ /config/llm       # 鍔ㄦ€侀厤缃?API
    鈹溾攢鈹€ palm_detector.py       # MediaPipe 21鐐规墜閮ㄦ娴?    鈹溾攢鈹€ feature_extractor.py   # 鎺岀汗鐗瑰緛鎻愬彇
    鈹溾攢鈹€ constitution_engine.py # 9绉嶄綋璐ㄥ垽瀹氬紩鎿?    鈹斺攢鈹€ companion.py           # AI 浜烘牸绯荤粺
## 璺嚎鍥?
| 鐘舵€?| 璁″垝 |
| 鉁?| 鎺岀汗鍒嗘瀽 + 浣撹川鍒ゅ畾鏍稿績寮曟搸 |
| 鉁?| Flask Web 搴旂敤 + PWA 鍓嶇 |
| 鉁?| AI 瀵硅瘽 + TTS 璇煶 |
| 鉁?| Windows EXE 涓€閿墦鍖?|
| 馃毀 | Android APK锛圔uildozer 鎵撳寘涓級 |
| 馃搵 | iOS 鏀寔锛圕apacitor.js 閫傞厤锛?|
| 馃搵 | 鑸岃瘖 + 闈㈣瘖澶氭ā鎬佽瀺鍚?|
| 馃搵 | WeChat 灏忕▼搴忕増鏈?|
## 寮€婧愬崗璁?
鏈」鐩噰鐢?[GNU AGPL-3.0](LICENSE) 璁稿彲璇併€?
**涓轰粈涔堢敤 AGPL-3.0 鑰屼笉鏄?MIT锛?* 鎴戜滑甯屾湜淇濇姢 AI 妯″瀷涓嶈浜戝巶鍟嗙洿鎺ユ墦鍖呮垚浠樿垂 SaaS 鏈嶅姟銆傚鏋滀綘鍙槸涓汉/鍖婚櫌鍐呴儴浣跨敤锛屽畬鍏ㄨ嚜鐢便€傚鏋滀綘瑕佸熀浜庣伒鏋㈠仛鍟嗕笟鍖栨湇鍔★紝璇峰悓鏍峰紑婧愩€?
  <sub>Built with 鉂わ笍 by <a href="https://github.com/YTZL2026">YTZL2026</a> 路 Inspired by 銆婇粍甯濆唴缁徛风伒鏋€?/sub>