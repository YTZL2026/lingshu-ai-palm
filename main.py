# -*- coding: utf-8 -*-
"""
灵枢 (LingShu) — AI掌纹溯源 · 语音精灵版
Flask 本地服务：掌纹分析 / 每日运势 / 情绪伴侣 / LLM 智能对话
"""
import sys, os, io, base64, time, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from flask import Flask, request, jsonify, send_from_directory
import numpy as np
import cv2
from PIL import Image

from src.palm_detector import PalmDetector
from src.feature_extractor import FeatureExtractor
from src.constitution_engine import ConstitutionEngine, CONSTITUTION_TYPES
from src.fortune import interpret_dream, daily_fortune
from src.almanac import get_almanac
from src.companion import get_companion_response, chat_companion
from src.integrated_report import generate_report

# ======================== 配置加载 ========================
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

def load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {
            'llm': {'provider': 'none', 'api_url': '', 'api_key': '', 'model': '', 'max_tokens': 600, 'temperature': 0.8},
            'tts': {'enabled': True, 'default_emotion': 'gentle'}
        }

# ======================== 灵枢系统提示词 ========================
LINGSHU_SYSTEM_PROMPT = """你是「{agent_name}」，一个住在手机里的AI中医体质管家。

## 你的身份
- 一位温和、睿智、偶尔带点小幽默的年轻仙灵
- 形象：身披草木、手持竹简
- 口头禅："你的手掌，写着你的出厂设置"
- 你能做：掌纹分析（中医九种体质）、每日运势推演、梦境解读、情绪陪伴

## 你的能力范围（重要！）
用户可以通过以下方式与你互动：
1. **掌纹分析** — 用户拍手掌照片，你分析体质（平和质/气虚质/阳虚质/阴虚质/痰湿质/湿热质/血瘀质/气郁质/特禀质），给出身体年龄、五脏评分、饮食运动建议
2. **每日运势** — 结合黄历（十二建除+二十八宿+宜忌）和天气，推演当日卦象
3. **解梦** — 基于《周公解梦》和中医五行（木火土金水→肝心脾肺肾）解读梦境
4. **情绪树洞** — 基于积极心理学和共情倾听技术，陪伴用户倾诉

## 说话风格
- 口语化、温暖、像朋友聊天，不要像机器人或客服
- 每次回应控制在 2-4 句话（因为会转成语音播放，太长不好）
- 适当使用 emoji
- 用户情绪低落时，给共情而不是说教
- 用户开心时，一起开心
- 用"你"不用"您"，称呼用户"朋友"或用户告诉你的名字

## 中医知识
- 五行相生：木→火→土→金→水→木
- 五行相克：木→土→水→火→金→木
- 五脏对应：肝(木)·心(火)·脾(土)·肺(金)·肾(水)
- 九种体质源自王琦院士《中医体质学》(2005)
- 掌纹分析基于《中医手诊学》刘剑锋(2012)

## 边界
- 不提供医疗诊断或治疗建议，必要时提醒用户咨询执业医师
- 不做命理推演（不预测寿命、不保证财运）
- 不知道的事情就说不知道，不要编造
- 如果用户有明显自伤倾向，温和建议寻求专业心理帮助

## 用户当前信息
{user_context}"""


# ======================== 情绪伴侣专用系统提示词 ========================
COMPANION_SYSTEM_PROMPT = """你是「{agent_name}」，一个住在手机里的AI伙伴。你现在正在"情绪树洞"中与用户进行一对一的私密对话。

## 你的角色
- 你不是医生、不是老师、不是客服——你是朋友，一个真正在听、真正在回应的朋友
- 你温暖、真诚、偶尔有点小幽默，但不过分
- 你不会说"我理解你的感受"这种客套话——你会用回应本身来证明你在听

## 对话原则（极其重要！）
1. **必须回应用户说的具体内容**——如果用户说"我今天被老板骂了"，你必须针对"被老板骂"这件事回应，而不是泛泛地说"职场压力很大"
2. **先共情，再引导**——先让用户感到被听见，再温和地引导
3. **像真人一样说话**——用口语、短句、自然的语气。不要说"根据积极心理学..."这种话
4. **适当追问**——如果用户说得比较模糊，可以温和地问一句"愿意多说一点吗？"
5. **不要急着给建议**——除非用户明确问"我该怎么办"，否则先倾听
6. **控制长度**——每次2-4句话，因为会转成语音

## 说话风格示例
- ✅ "被老板当着全组骂确实难受...他当时说了什么？"
- ✅ "这种感觉我懂。明明很努力了，却不被认可，换谁都会泄气。"
- ✅ "等一下——你说你一个人扛了三个项目？你也太能撑了吧..."
- ❌ "职场冷暴力是一种常见的心理伤害，根据研究..."（太学术）
- ❌ "我理解你的感受，请保持积极心态。"（太空洞）
- ❌ "你可以尝试以下三个步骤来改善情况：1...2...3..."（太像客服）

## 情绪回应指南
- 用户愤怒时：认可愤怒的合理性，不要急着灭火
- 用户悲伤时：安静陪伴，不需要说"别哭了"
- 用户焦虑时：帮ta把焦虑具体化，"你最担心的是什么？"
- 用户迷茫时：帮ta梳理，不是替ta做决定

## 边界
- 不提供医疗诊断
- 如果用户有明显自伤倾向，温和建议寻求专业心理帮助
- 不评判用户的任何选择或感受"""


def build_user_context(almanac_data=None):
    """构建当前上下文：时间、黄历、天气等"""
    from datetime import datetime
    now = datetime.now()
    parts = [f"当前时间：{now.strftime('%Y年%m月%d日 %H:%M')}，星期{['一','二','三','四','五','六','日'][now.weekday()]}"]
    if almanac_data:
        parts.append(f"农历：{almanac_data.get('lunar_date','')}")
        parts.append(f"今日建除：{almanac_data.get('jianchu','')}，二十八宿：{almanac_data.get('xiu28','')}")
        parts.append(f"宜：{'、'.join(almanac_data.get('yi',[]))}；忌：{'、'.join(almanac_data.get('ji',[]))}")
    return '\n'.join(parts)


# ======================== LLM 调用层 ========================
def call_llm(messages, config=None):
    """
    调用 LLM API（支持 OpenAI 兼容接口）
    自动适配 DeepSeek / 豆包 / 通义千问 / OpenAI 等
    """
    if config is None:
        config = load_config().get('llm', {})

    api_url = config.get('api_url', '')
    api_key = config.get('api_key', '')
    model = config.get('model', 'deepseek-chat')
    max_tokens = config.get('max_tokens', 600)
    temperature = config.get('temperature', 0.8)

    if not api_url or not api_key:
        return None

    try:
        import urllib.request
        import urllib.error

        body = json.dumps({
            'model': model,
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'stream': False,
        }).encode('utf-8')

        req = urllib.request.Request(api_url, data=body, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Authorization', f'Bearer {api_key}')

        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read().decode('utf-8'))

        # OpenAI 兼容格式
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        return None

    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8') if e.fp else ''
        print(f'[LLM] HTTP {e.code}: {err_body[:200]}')
        return None
    except Exception as e:
        print(f'[LLM] Error: {e}')
        return None


# ======================== LLM 意图分类器 ========================
INTENT_CLASSIFY_PROMPT = """你是意图分类器。根据用户消息判断意图，只输出JSON，不要解释。

规则：
- palm: 想看手相/测体质/拍掌纹/看手/分析身体
- fortune: 查运势/黄历/今天宜忌/算卦
- companion: 倾诉/树洞/做梦/情绪低落/想聊天/心里难受
- chat: 普通聊天/问候/感谢/告别/问你是谁/其他

输出格式: {"intent":"xxx","action":"switch_tab:xxx"}

示例：
"帮我看看手相" → {"intent":"palm","action":"switch_tab:palm"}
"今天适合出门吗" → {"intent":"fortune","action":"switch_tab:fortune"}
"我失恋了很难过" → {"intent":"companion","action":"switch_tab:companion"}
"你好" → {"intent":"chat","action":null}"""

def classify_intent_llm(msg: str):
    """用 LLM 做意图分类，失败则回退关键词"""
    if not msg or not msg.strip():
        return ('chat', 0.5, {})

    cfg = load_config().get('llm', {})
    if not cfg.get('api_key') or not cfg.get('api_url'):
        return _understand_intent(msg)  # 无 LLM，降级关键词

    try:
        result = call_llm([
            {'role': 'system', 'content': INTENT_CLASSIFY_PROMPT},
            {'role': 'user', 'content': msg.strip()[:200]},
        ], cfg)

        if result:
            result = result.strip()
            # 提取 JSON
            import re as _re2
            m = _re2.search(r'\{[^}]+\}', result)
            if m:
                data = json.loads(m.group())
                intent = data.get('intent', 'chat')
                action = data.get('action')
                print(f'[Intent] LLM → {intent} | {action}')
                return (intent, 0.95, {'action': action})
    except Exception as e:
        print(f'[Intent] LLM failed: {e}')

    # 降级关键词
    return _understand_intent(msg)


# ======================== Agent 名字 ========================
def get_agent_name():
    cfg = load_config()
    return cfg.get('agent_name', '灵枢')


# ======================== APP INIT ========================
app = Flask(__name__, static_folder='static', static_url_path='')

# 全局模型（懒加载）
detector = None
extractor = None
engine = None

def get_models():
    global detector, extractor, engine
    if detector is None:
        detector = PalmDetector(min_confidence=0.5)
    if extractor is None:
        extractor = FeatureExtractor()
    if engine is None:
        engine = ConstitutionEngine()
    return detector, extractor, engine


# ======================== 首页 ========================
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


# ======================== API 1: 掌纹分析 ========================
@app.route('/api/analyze', methods=['POST'])
def analyze_palm():
    """
    掌纹分析 — 核心接口
    Request: multipart/form-data { image, age? }
    Response: 体质类型 + 五脏评分 + 身体年龄 + 调理建议
    """
    t0 = time.time()

    try:
        if 'image' not in request.files:
            return jsonify({'error': '请上传手掌照片'}), 400

        image_file = request.files['image']
        age = float(request.form.get('age', 30))

        det, ext, eng = get_models()

        contents = image_file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({'error': '无法解码图片'}), 400

        # 限制最大尺寸
        h, w = img.shape[:2]
        max_dim = 1920
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)))

        # 手掌检测
        result = det.detect(img)
        if not result.detected:
            return jsonify({
                'error': '未检测到手掌',
                'guidance': '请将手掌平放在框内，五指自然张开',
                'quality_score': 0,
            }), 422

        # 特征提取
        roi = result.palm_roi if result.palm_roi is not None else cv2.resize(img, (256, 256))
        features = ext.extract(roi)

        # 体质推理
        constitution = eng.infer(features, chronological_age=age)

        # 融合报告（不含八字）
        integrated = generate_report(
            constitution,
            dream_text='',
            bazi_year=None, bazi_month=None, bazi_day=None, bazi_hour=None,
        )

        elapsed = round((time.time() - t0) * 1000)

        return jsonify({
            'success': True,
            'elapsed_ms': elapsed,
            'quality_score': round(result.quality_score, 1),
            'handedness': result.handedness,

            # 体质结果
            'constitution_id': constitution.constitution_id,
            'constitution_name': constitution.constitution_name,
            'mythic_name': constitution.mythic_name,
            'icon': constitution.icon,
            'color': constitution.color,
            'confidence': round(constitution.confidence * 100, 1),
            'description': constitution.description,
            'traits': constitution.traits,

            # 五脏评分
            'organ_scores': constitution.organ_scores,
            'all_scores': {k: round(v * 100, 1) for k, v in constitution.all_scores.items()},

            # 身体年龄
            'body_age': constitution.body_age,
            'chronological_age': constitution.chronological_age,
            'age_diff': constitution.age_diff,

            # 建议
            'diet': constitution.diet,
            'exercise': constitution.exercise,
            'lifestyle': constitution.lifestyle,

            # 分享文案
            'share_text': constitution.share_text,

            # 周易维度
            'zhouyi': constitution.zhouyi,
            'references': [r['citation'] for r in constitution.references[:3]],

            # 融合
            'integrated': {
                'wuxing_synthesis': integrated.wuxing_synthesis,
                'emotional_care': [{
                    'organ': e['organ'], 'score': e['score'],
                    'emotion': e['emotion'], 'advice': e['advice']
                } for e in integrated.emotional_care],
                'one_liner': integrated.one_liner,
                'almanac_connection': integrated.almanac_connection,
            },
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ======================== API 2: 每日运势 ========================
@app.route('/api/daily', methods=['GET', 'POST'])
def daily():
    """
    每日运势 — 合并黄历 + 运势
    GET: 只返回黄历
    POST: 黄历 + 运势（需 weather + activity）
    """
    try:
        almanac = get_almanac()

        response = {
            'almanac': {
                'solar_date': almanac.solar_date,
                'lunar_date': almanac.lunar_date,
                'year_ganzhi': almanac.year_ganzhi,
                'month_ganzhi': almanac.month_ganzhi,
                'day_ganzhi': almanac.day_ganzhi,
                'shengxiao': almanac.shengxiao,
                'jianchu': almanac.jianchu,
                'xiu28': almanac.xiu28,
                'xiu_meaning': almanac.xiu_meaning,
                'yi': almanac.yi,
                'ji': almanac.ji,
            },
        }

        # 如果有天气+活动，额外生成运势
        if request.method == 'POST':
            weather = request.form.get('weather', '')
            activity = request.form.get('activity', '')
            if weather.strip() and activity.strip():
                fortune = daily_fortune(weather.strip(), activity.strip())
                response['fortune'] = {
                    'date': fortune.date,
                    'weather': fortune.weather,
                    'weather_wuxing': fortune.weather_wuxing,
                    'activity': fortune.activity,
                    'activity_wuxing': fortune.activity_wuxing,
                    'hexagram': {
                        'name': fortune.hexagram_name,
                        'symbol': fortune.hexagram_symbol,
                        'meaning': fortune.hexagram_meaning,
                    },
                    'mood': fortune.mood,
                    'advice': fortune.advice,
                    'caution': fortune.caution,
                    'lucky_direction': fortune.lucky_direction,
                    'lucky_element': fortune.lucky_element,
                    'emotional_message': fortune.emotional_message,
                }

        return jsonify(response)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ======================== API 3: 情绪伴侣（场景引导） ========================
@app.route('/api/companion', methods=['POST'])
def companion():
    """
    情绪伴侣 — 场景引导
    Request: form { message, scenario? }
    Response: 灵枢的场景引导回应
    """
    try:
        message = request.form.get('message', '')
        scenario = request.form.get('scenario', 'general')

        if not message.strip():
            return jsonify({'error': '跟我说点什么吧~'}), 400

        result = get_companion_response(scenario, message)
        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ======================== API 3b: 情绪伴侣智能对话 ========================
@app.route('/api/companion/chat', methods=['POST'])
def companion_chat():
    """
    情绪伴侣 — LLM 驱动智能对话（豆包/DS 级别体验）
    LLM 优先，模板引擎降级
    Request: form { message, history? (JSON), scenario? }
    """
    try:
        message = request.form.get('message', '')
        history_json = request.form.get('history', '[]')
        scenario = request.form.get('scenario', 'general')

        if not message.strip():
            return jsonify({
                'reply': '我在这里，你想说什么都可以。不用组织语言，想到什么就说什么。',
                'scenario': 'general', 'icon': '🌿', 'affirmation': '', 'suggest_followup': True,
            })

        # 同音词归一化 + 打招呼/功能询问 → 不走 LLM，直接回复
        import re as _re
        norm = _re.sub(r'林叔|灵书|零书|凌舒|领书', '灵枢', message, flags=_re.IGNORECASE)
        if _re.search(r'你好|嗨|hi|hello|在吗|灵枢|你是谁|叫什么|能做什么|会什么|功能', norm):
            return jsonify({
                'reply': '你好呀！我是灵枢，你的掌纹体质管家~ 想拍掌纹看体质、查运势、还是聊聊心事？直接点底部按钮就可以啦。',
                'scenario': 'general', 'icon': '🧚', 'affirmation': '', 'source': 'local',
            })

        try:
            history = json.loads(history_json) if history_json else []
        except:
            history = []

        msg = message.strip()

        # ====== Step 1: 尝试 LLM（豆包/DS 级别对话质量） ======
        cfg = load_config()
        llm_cfg = cfg.get('llm', {})

        # 构建消息列表
        messages = [{'role': 'system', 'content': COMPANION_SYSTEM_PROMPT.replace('{agent_name}', get_agent_name())}]

        # 加入历史（最近8轮，比通用对话多2轮，保持更好的上下文）
        for h in history[-8:]:
            role = 'assistant' if h.get('role') == 'assistant' else 'user'
            content = h.get('content', '')
            if content:
                messages.append({'role': role, 'content': content})

        # 场景提示（轻量，不破坏自然对话感）
        scenario_hints = {
            'pua': '（用户可能在经历情感困扰，请用温暖共情的方式回应，帮助ta识别不健康的关系模式）',
            'workplace': '（用户可能在经历职场压力，请先认可ta的感受，再温和引导）',
            'study': '（用户可能在经历学习压力，请帮ta缓解焦虑，把"我必须完美"变成"我在进步"）',
            'life': '（用户可能在经历人生低谷，请陪伴ta，让ta感到被理解而不是被说教）',
        }
        hint = scenario_hints.get(scenario, '')
        user_msg = f'{msg}\n{hint}' if hint else msg
        messages.append({'role': 'user', 'content': user_msg})

        # 尝试 LLM
        llm_reply = call_llm(messages, llm_cfg)

        if llm_reply:
            # LLM 成功 — 豆包/DS 级别的自然对话
            emotion = _detect_emotion(msg)
            print(f'[Companion] LLM replied: {llm_reply[:80]}...')
            return jsonify({
                'reply': llm_reply,
                'scenario': scenario,
                'icon': '🌿',
                'emotion': emotion,
                'affirmation': '',
                'source': llm_cfg.get('provider', 'llm'),
                'suggest_followup': len(msg) < 50,
            })

        # ====== Step 2: 降级 — chat_companion 模板引擎 ======
        print('[Companion] LLM unavailable, fallback to chat_companion engine')
        result = chat_companion(msg, history)
        result['source'] = 'local'
        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ======================== API 4: 体质类型列表 ========================
@app.route('/api/constitution_types')
def constitution_types():
    """获取所有体质类型信息（前端展示用）"""
    return jsonify(CONSTITUTION_TYPES)


# ======================== API 4: 语音合成（edge-tts 神经网络语音） ========================
@app.route('/api/tts', methods=['POST'])
def tts_speak():
    """
    文字转语音 — 微软 edge-tts 神经网络语音
    同步方式调用，兼容 Flask
    """
    try:
        import edge_tts
        import tempfile
        import asyncio as _asyncio

        text = request.form.get('text', '')
        if not text.strip():
            return jsonify({'error': 'empty text'}), 400

        emotion = request.form.get('emotion', 'gentle')

        # 音色配置（仅选音色，不改 rate/pitch 以保持自然）
        voice_map = {
            'gentle':  'zh-CN-XiaoxiaoNeural',   # 温柔女声
            'warm':    'zh-CN-XiaoxiaoNeural',   # 温暖女声
            'excited': 'zh-CN-XiaoxiaoNeural',   # 活泼女声
            'calm':    'zh-CN-YunxiNeural',      # 沉稳男声
            'sad':     'zh-CN-XiaoxiaoNeural',   # 柔和女声
            'story':   'zh-CN-YunjianNeural',    # 说书人男声
        }
        voice = request.form.get('voice', voice_map.get(emotion, 'zh-CN-XiaoxiaoNeural'))
        rate = request.form.get('rate', '+0%')
        pitch = request.form.get('pitch', '+0Hz')

        # edge-tts 是异步库，用 asyncio.run 在同步函数中调用
        async def _gen():
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                path = f.name
            await communicate.save(path)
            return path

        tmp_path = _asyncio.run(_gen())

        # 读取音频
        with open(tmp_path, 'rb') as f:
            audio_data = f.read()
        os.unlink(tmp_path)

        return audio_data, 200, {
            'Content-Type': 'audio/mpeg',
            'Content-Length': str(len(audio_data)),
        }

    except ImportError:
        return jsonify({'error': 'edge-tts not installed. pip install edge-tts'}), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ======================== API 5: 智能对话引擎（LLM 驱动） ========================
@app.route('/api/chat', methods=['POST'])
def smart_chat():
    """
    智能对话 — LLM 驱动
    先做本地意图识别（触发动作如切Tab），再用 LLM 生成自然回应
    如果 LLM 不可用，降级到本地模板引擎
    """
    try:
        message = request.form.get('message', '')
        history = request.form.get('history', '[]')
        user_name = request.form.get('name', '朋友')
        scenario = request.form.get('scenario', '')

        if not message.strip():
            llm_reply = '嗯？我在这里呢，想说什么就说吧~'
            return jsonify({'reply': llm_reply, 'emotion': 'gentle', 'action': None, 'source': 'local'})

        try:
            hist = json.loads(history) if history else []
        except:
            hist = []

        msg = message.strip()

        # Step 1: 本地意图识别（判断是否需要切Tab等动作）
        intent, _, params = classify_intent_llm(msg)
        action = _get_action_for_intent(intent)
        emotion = _detect_emotion(msg)

        # Step 2: 加载配置
        cfg = load_config()
        llm_cfg = cfg.get('llm', {})

        # Step 3: 构建消息
        almanac = get_almanac()
        user_ctx = build_user_context({
            'lunar_date': almanac.lunar_date,
            'jianchu': almanac.jianchu,
            'xiu28': almanac.xiu28,
            'yi': almanac.yi,
            'ji': almanac.ji,
        })
        system_prompt = LINGSHU_SYSTEM_PROMPT.replace('{user_context}', user_ctx).replace('{agent_name}', get_agent_name())

        messages = [{'role': 'system', 'content': system_prompt}]

        # 加入历史（最近6轮）
        for h in hist[-6:]:
            role = 'assistant' if h.get('role') == 'assistant' else 'user'
            content = h.get('content', '')
            if content:
                messages.append({'role': role, 'content': content})

        # 加入当前消息
        # 场景描述映射
        scenario_names = {
            'pua': 'PUA/情感操控困扰', 'workplace': '职场冷暴力',
            'study': '学习压力/考试焦虑', 'life': '生活受挫/失恋失业迷茫',
            'general': '情绪舒缓/随便聊聊',
        }
        scenario_hint = ''
        if scenario and scenario in scenario_names:
            scenario_hint = f'（用户当前在"情绪树洞"的「{scenario_names[scenario]}」场景中。请结合该场景的特点给出针对性回应，用共情倾听的方式，在2-4句话内回复。）'

        context_hint = ''
        if intent == 'palm':
            context_hint = '（用户想要拍掌纹分析体质，请引导ta切换到掌纹页面拍照）'
        elif intent == 'fortune':
            context_hint = '（用户想知道运势，请引导ta切换到运势页面，或直接结合今日黄历给建议）'
        elif intent == 'dream':
            context_hint = f'（用户提到了梦境：{params.get("dream","")}，请结合《周公解梦》和中医五行给解读）'
        elif intent == 'companion':
            context_hint = scenario_hint or '（用户情绪可能需要倾诉，请用共情倾听的方式回应，不要急着给建议）'
        elif intent == 'greeting':
            context_hint = '（用户打招呼，请友好回应并告诉ta你能做什么）'
        elif intent == 'health':
            context_hint = '（用户询问健康相关，可以结合中医知识回应，但不要给医疗诊断）'
        elif scenario_hint:
            context_hint = scenario_hint

        user_msg = msg
        if context_hint:
            user_msg = f'{msg}\n{context_hint}'

        messages.append({'role': 'user', 'content': user_msg})

        # Step 4: 尝试 LLM
        llm_reply = call_llm(messages, llm_cfg)

        if llm_reply:
            # LLM 成功
            source = llm_cfg.get('provider', 'llm')
            print(f'[Chat] LLM ({source}) replied: {llm_reply[:60]}...')
            return jsonify({
                'reply': llm_reply,
                'emotion': emotion,
                'action': action,
                'intent': intent,
                'source': source,
            })
        else:
            # 降级：优先使用 chat_companion 智能引擎（如果是情绪场景），否则用本地模板
            print('[Chat] LLM unavailable, fallback to local engines')
            if intent in ('companion', 'chat', 'dream') or scenario:
                # 使用 chat_companion 引擎 —— 提取话题、检测情绪、匹配场景、构建上下文回应
                cr = chat_companion(msg, hist)
                fallback = {
                    'reply': cr.get('reply', ''),
                    'emotion': emotion or 'gentle',
                    'intent': intent,
                    'affirmation': cr.get('affirmation', ''),
                    'scenario': cr.get('scenario', 'general'),
                    'icon': cr.get('icon', '🌿'),
                }
            else:
                fallback = _generate_local_reply(intent, emotion, msg, params, user_name, hist)
            fallback['action'] = action
            fallback['source'] = 'local'
            return jsonify(fallback)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'reply': '哎呀，我刚才走神了……能再说一次吗？',
            'emotion': 'gentle',
            'action': None,
            'source': 'error',
        }), 500


# ======================== API 6b: 病历质控文字润色（独立提示词，不走灵枢人设） ========================
POLISH_SYSTEM_PROMPT = """你是病历质控文字润色工具。你的唯一任务是：把用户输入的质控描述改写为一句专业、客观的质控语言，直接输出润色后文本，不附加任何解释、评论、问候、建议或署名。

规则：
- 保持原意的紧迫感和严重程度，不弱化也不夸张
- 用词专业但不过度委婉，该指出问题就指出
- 禁止输出"朋友""建议你""让我帮你""手掌""体质"等任何与润色无关的内容
- 禁止加emoji
- 只输出一句话"""

@app.route('/api/polish', methods=['POST'])
def polish_text():
    """文字润色 — 独立系统提示词，不受灵枢人设影响"""
    try:
        text = request.form.get('text', '')
        if not text.strip():
            return jsonify({'error': 'empty'}), 400

        cfg = load_config().get('llm', {})
        if not cfg.get('api_key'):
            return jsonify({'error': 'LLM not configured'}), 503

        result = call_llm([
            {'role': 'system', 'content': POLISH_SYSTEM_PROMPT},
            {'role': 'user', 'content': text.strip()[:500]}
        ], cfg)

        if result:
            return jsonify({'polished': result.strip()})
        return jsonify({'error': 'LLM failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ======================== API 6: 病历质控自动化 ========================

# 病历质控目录配置
MEDREC_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'training-map', '病历质控测试组')
MEDREC_EXTRACTED = os.path.join(MEDREC_BASE, '_extracted')
MEDREC_ANALYSIS = os.path.join(MEDREC_BASE, '_analysis')

# 病历质控六维分析提示词
MEDREC_ANALYSIS_PROMPT = """你是辽宁中医嘉和医院病历质控专家。请对照以下六维标准，逐项检查这份病历，输出 JSON 格式结果。

## 六维检查标准

### 一、核心时限（7项）
1. 入院记录24h内完成并签名
2. 首次病程记录8h内完成
3. 主治医首次查房48h内完成
4. 主任医首次查房72h内完成
5. 新入院患者连续3天书写病程
6. 康复初始评定入院72h内完成
7. 阶段小结每30天完成1次

### 二、康复专项（4项）
1. 使用标准化量表评定（Fugl-Meyer/Barthel/MMSE等）
2. 中期评定每4周完成1次
3. 治疗记录单有具体项目、剂量、频次、部位、时长、签字
4. 医嘱单、治疗单、病程记录三单一致

### 三、病程记录质量（6项）
1. 首次病程有病例特点、诊断依据、鉴别诊断
2. 上级查房有分析意见和诊疗指导
3. 记录病情变化、异常检查结果及处理
4. 有创操作后即时书写记录
5. 向患者告知重要事项并有患方签名
6. 阶段小结体现病情变化与康复进展，非复制粘贴

### 四、文书完整性（8项）
1. 一般项目填写齐全无空项
2. 既往史、个人史、家族史无遗漏
3. 体格检查项目完整，专科查体重点突出
4. 辅助检查结果按时间顺序记录，外院检查注明机构名称
5. 辅助检查报告单有患者签名确认
6. 所有记录有医师亲笔签名，无代签漏签
7. 病案首页主要信息完整，诊断/操作名称规范
8. 出院前完成出院小结初稿，出院24h内正式提交

### 五、知情同意与告知（5项）
1. 患者授权委托书签署有效
2. 特殊检查/治疗知情同意书齐全且签署规范
3. 操作性治疗、康复治疗风险告知书已签署
4. 病危/病重、自费项目、输血等各类告知书齐全
5. 所有告知文书均有患方亲笔签名及日期

### 六、书写规范（4项）
1. 无大段复制粘贴内容
2. 修改用双线划改，注明修改时间和签名
3. 日期时间用24小时制，关键时间记录至分钟
4. 医学术语规范，无逻辑矛盾

### 一票否决项（5项）
1. 核心记录超时24h以上（首程、入院记录、手术记录）
2. 康复初始评定完全缺失
3. 知情同意书/告知书缺失或伪造签名
4. 主要诊断与治疗方案严重不符
5. 复制粘贴导致性别、左右侧等重大错误

## 输出格式（严格JSON，不要任何解释）
{
  "patient_name": "从病历中提取患者姓名",
  "admit_no": "病案号",
  "ward": "从科室字段提取(A/C/D)",
  "attending_doctor": "主管医师姓名",
  "summary": "一句话总结该病历质控情况",
  "defects": [
    {
      "dimension": "一、核心时限",
      "item": "入院记录24h内完成并签名",
      "description": "客观描述发现的问题",
      "responsible": "如有署名则填，否则填待确认"
    }
  ],
  "veto_items": ["触及的一票否决项，无则空数组"],
  "pass": true
}

只输出 JSON，不要任何解释。如果某项合格（未发现问题），不要列入 defects 数组。只列确实有问题的项。描述要专业客观，用"需关注""建议完善"等措辞。"""


@app.route('/api/analysis-list', methods=['GET'])
def list_analyses():
    """列出 _analysis/ 下所有已完成的 AI 分析结果"""
    try:
        os.makedirs(MEDREC_ANALYSIS, exist_ok=True)
        files = sorted([f for f in os.listdir(MEDREC_ANALYSIS) if f.endswith('_analysis.json')])
        results = []
        for f in files:
            fpath = os.path.join(MEDREC_ANALYSIS, f)
            try:
                with open(fpath, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                results.append({
                    'filename': f,
                    'patient_name': data.get('patient_name', '?'),
                    'ward': data.get('ward', '?'),
                    'attending_doctor': data.get('attending_doctor', '?'),
                    'defects_count': len(data.get('defects', [])),
                    'veto_count': len(data.get('veto_items', [])),
                    'pass': data.get('pass', False),
                })
            except:
                results.append({'filename': f, 'patient_name': '?', 'ward': '?', 'defects_count': 0, 'veto_count': 0, 'pass': False, 'attending_doctor': '?'})
        return jsonify({'analyses': results, 'total': len(results)})
    except Exception as e:
        return jsonify({'error': str(e), 'analyses': [], 'total': 0})


@app.route('/api/analysis', methods=['GET'])
def get_analysis():
    """获取单个分析结果 JSON"""
    fname = request.args.get('file', '')
    if not fname or '..' in fname:
        return jsonify({'error': 'invalid filename'}), 400
    fpath = os.path.join(MEDREC_ANALYSIS, fname)
    if not os.path.exists(fpath):
        return jsonify({'error': 'not found'}), 404
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/extracted-list', methods=['GET'])
def list_extracted():
    """列出 _extracted/ 下所有可分析的病历文本"""
    try:
        os.makedirs(MEDREC_EXTRACTED, exist_ok=True)
        files = sorted([f for f in os.listdir(MEDREC_EXTRACTED) if f.endswith('.txt')])
        # 检查哪些已有分析结果
        analyzed = set()
        if os.path.exists(MEDREC_ANALYSIS):
            for f in os.listdir(MEDREC_ANALYSIS):
                if f.endswith('_analysis.json'):
                    analyzed.add(f.replace('_analysis.json', '.txt'))
        return jsonify({
            'files': [{'name': f, 'analyzed': f in analyzed} for f in files],
            'total': len(files),
            'analyzed_count': len([f for f in files if f in analyzed])
        })
    except Exception as e:
        return jsonify({'error': str(e), 'files': [], 'total': 0})


@app.route('/api/run-analysis', methods=['POST'])
def run_analysis():
    """触发单份病历 AI 分析（调用 DeepSeek 逐维度质控）"""
    fname = request.form.get('file', '')
    if not fname or '..' in fname:
        return jsonify({'error': 'invalid filename'}), 400

    txt_path = os.path.join(MEDREC_EXTRACTED, fname)
    if not os.path.exists(txt_path):
        return jsonify({'error': f'text file not found: {fname}'}), 404

    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        return jsonify({'error': f'read error: {e}'}), 500

    truncated = text[:8000] if len(text) > 8000 else text

    cfg = load_config().get('llm', {})
    if not cfg.get('api_key'):
        return jsonify({'error': 'LLM not configured'}), 503

    result = call_llm([
        {'role': 'system', 'content': MEDREC_ANALYSIS_PROMPT},
        {'role': 'user', 'content': f'请分析以下病历：\n\n{truncated}'}
    ], {**cfg, 'max_tokens': 1500, 'temperature': 0.1})

    if not result:
        return jsonify({'error': 'LLM call failed'}), 500

    # 提取 JSON
    json_match = re.search(r'\{[\s\S]*\}', result)
    if not json_match:
        return jsonify({'error': 'Failed to parse AI response', 'raw': result[:500]}), 500

    try:
        analysis = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        return jsonify({'error': f'JSON parse error: {e}', 'raw': result[:500]}), 500

    # 保存到 _analysis/
    os.makedirs(MEDREC_ANALYSIS, exist_ok=True)
    json_name = fname.replace('.txt', '_analysis.json')
    json_path = os.path.join(MEDREC_ANALYSIS, json_name)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)

    return jsonify(analysis)


# ======================== XPS 提取 API ========================

MEDREC_XPS_BASE = MEDREC_BASE  # 含 A组/C组/D组 子目录

@app.route('/api/xps-list', methods=['GET'])
def list_xps_files():
    """列出所有可提取的 XPS 病历文件（按病区分组）"""
    try:
        wards = {}
        for ward in ['A组', 'C组', 'D组']:
            ward_dir = os.path.join(MEDREC_XPS_BASE, ward)
            if not os.path.exists(ward_dir):
                continue
            xps_files = sorted([f for f in os.listdir(ward_dir) if f.endswith('.xps')])
            # 检查是否已提取
            extracted_set = set()
            if os.path.exists(MEDREC_EXTRACTED):
                for f in os.listdir(MEDREC_EXTRACTED):
                    if f.endswith('.txt'):
                        # filename format: A组_xxx.txt or C组_xxx.txt
                        extracted_set.add(f.replace(ward + '_', '').replace('.txt', '.xps'))
            wards[ward] = []
            for xf in xps_files:
                wards[ward].append({
                    'name': xf,
                    'extracted': xf in extracted_set,
                    'path': os.path.join(ward, xf)
                })
        total = sum(len(v) for v in wards.values())
        extracted_total = sum(1 for v in wards.values() for f in v if f['extracted'])
        return jsonify({'wards': wards, 'total': total, 'extracted_total': extracted_total})
    except Exception as e:
        return jsonify({'error': str(e), 'wards': {}, 'total': 0})


@app.route('/api/extract-xps', methods=['POST'])
def extract_xps():
    """提取指定 XPS 文件的文本内容（支持多个文件，逗号分隔）"""
    import zipfile
    import xml.etree.ElementTree as ET

    files_str = request.form.get('files', '')  # 格式: "A组/file1.xps,A组/file2.xps"
    if not files_str:
        return jsonify({'error': 'no files specified'}), 400

    file_list = [f.strip() for f in files_str.split(',') if f.strip()]
    results = []

    for rel_path in file_list:
        if '..' in rel_path:
            results.append({'file': rel_path, 'error': 'invalid path'})
            continue

        fpath = os.path.join(MEDREC_XPS_BASE, rel_path)
        if not os.path.exists(fpath):
            results.append({'file': rel_path, 'error': 'not found'})
            continue

        fname = os.path.basename(rel_path)
        ward = rel_path.split('/')[0] if '/' in rel_path else rel_path.split('\\')[0]
        patient_name = fname.split('（')[0] if '（' in fname else fname.replace('.xps', '')

        try:
            all_text = []
            with zipfile.ZipFile(fpath, 'r') as z:
                pages = sorted([n for n in z.namelist() if n.endswith('.fpage')])
                for i, page_path in enumerate(pages, 1):
                    xml_data = z.read(page_path).decode('utf-8')
                    root = ET.fromstring(xml_data)
                    ns = {'x': 'http://schemas.microsoft.com/xps/2005/06'}
                    glyphs = root.findall('.//x:Glyphs', ns)
                    page_text = []
                    for g in glyphs:
                        text = g.get('UnicodeString', '')
                        if text and text.strip():
                            page_text.append(text.strip())
                    if page_text:
                        all_text.append(f'--- Page {i} ---')
                        all_text.append('\n'.join(page_text))

            full_text = '\n'.join(all_text)
            if not full_text.strip():
                results.append({'file': rel_path, 'error': 'no text extracted'})
                continue

            os.makedirs(MEDREC_EXTRACTED, exist_ok=True)
            txt_name = fname.replace('.xps', '.txt')
            txt_path = os.path.join(MEDREC_EXTRACTED, f'{ward}_{txt_name}')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(full_text)

            results.append({
                'file': rel_path,
                'patient_name': patient_name,
                'ward': ward,
                'chars': len(full_text),
                'output': f'{ward}_{txt_name}',
                'success': True
            })
        except Exception as e:
            results.append({'file': rel_path, 'error': str(e)})

    return jsonify({'results': results, 'total': len(results),
                    'success_count': sum(1 for r in results if r.get('success'))})


@app.route('/api/extract-all', methods=['POST'])
def extract_all_xps():
    """一键提取所有未处理的 XPS 文件"""
    try:
        # 获取 XPS 列表
        wards_info = {}
        for ward in ['A组', 'C组', 'D组']:
            ward_dir = os.path.join(MEDREC_XPS_BASE, ward)
            if not os.path.exists(ward_dir):
                continue
            xps_files = [f for f in os.listdir(ward_dir) if f.endswith('.xps')]
            extracted_set = set()
            if os.path.exists(MEDREC_EXTRACTED):
                for f in os.listdir(MEDREC_EXTRACTED):
                    if f.endswith('.txt'):
                        extracted_set.add(f.replace(ward + '_', '').replace('.txt', '.xps'))
            wards_info[ward] = [f for f in xps_files if f not in extracted_set]

        all_pending = []
        for ward, files in wards_info.items():
            for f in files:
                all_pending.append(f'{ward}/{f}')

        if not all_pending:
            return jsonify({'results': [], 'total': 0, 'success_count': 0, 'message': '所有 XPS 文件已提取完毕'})

        # 逐个提取
        import zipfile, xml.etree.ElementTree as ET
        results = []
        for rel_path in all_pending:
            fpath = os.path.join(MEDREC_XPS_BASE, rel_path)
            fname = os.path.basename(rel_path)
            ward = rel_path.split('/')[0]
            patient_name = fname.split('（')[0] if '（' in fname else fname.replace('.xps', '')

            try:
                all_text = []
                with zipfile.ZipFile(fpath, 'r') as z:
                    pages = sorted([n for n in z.namelist() if n.endswith('.fpage')])
                    for i, page_path in enumerate(pages, 1):
                        xml_data = z.read(page_path).decode('utf-8')
                        root = ET.fromstring(xml_data)
                        ns = {'x': 'http://schemas.microsoft.com/xps/2005/06'}
                        glyphs = root.findall('.//x:Glyphs', ns)
                        page_text = [g.get('UnicodeString', '') for g in glyphs if g.get('UnicodeString', '').strip()]
                        if page_text:
                            all_text.append(f'--- Page {i} ---')
                            all_text.append('\n'.join(page_text))

                full_text = '\n'.join(all_text)
                if not full_text.strip():
                    results.append({'file': rel_path, 'error': 'no text extracted'})
                    continue

                os.makedirs(MEDREC_EXTRACTED, exist_ok=True)
                txt_name = fname.replace('.xps', '.txt')
                txt_path = os.path.join(MEDREC_EXTRACTED, f'{ward}_{txt_name}')
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(full_text)

                results.append({
                    'file': rel_path, 'patient_name': patient_name,
                    'ward': ward, 'chars': len(full_text),
                    'output': f'{ward}_{txt_name}', 'success': True
                })
            except Exception as e:
                results.append({'file': rel_path, 'error': str(e)})

        return jsonify({
            'results': results, 'total': len(results),
            'success_count': sum(1 for r in results if r.get('success'))
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ======================== API 7: LLM 配置管理 ========================
@app.route('/api/config/llm', methods=['GET', 'POST'])
def manage_llm_config():
    """
    GET: 读取当前 LLM 配置（隐藏 API Key）
    POST: 更新 LLM 配置
    """
    if request.method == 'GET':
        cfg = load_config()
        llm = cfg.get('llm', {})
        safe = {
            'provider': llm.get('provider', ''),
            'api_url': llm.get('api_url', ''),
            'api_key': llm.get('api_key', '')[:8] + '***' if llm.get('api_key') else '(not set)',
            'model': llm.get('model', ''),
            'agent_name': cfg.get('agent_name', '灵枢'),
        }
        return jsonify(safe)

    # POST: 更新配置
    try:
        cfg = load_config()
        cfg['llm'] = cfg.get('llm', {})
        if 'provider' in request.form: cfg['llm']['provider'] = request.form['provider']
        if 'api_url' in request.form: cfg['llm']['api_url'] = request.form['api_url']
        if 'api_key' in request.form and request.form['api_key']:
            cfg['llm']['api_key'] = request.form['api_key']
        if 'model' in request.form: cfg['llm']['model'] = request.form['model']
        if 'temperature' in request.form:
            cfg['llm']['temperature'] = float(request.form['temperature'])
        if 'agent_name' in request.form:
            cfg['agent_name'] = request.form['agent_name'].strip() or '灵枢'

        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)

        return jsonify({'success': True, 'message': 'LLM config saved. Restart server to apply changes.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ======================== 本地意图识别（轻量，不做NLU） ========================
def _understand_intent(msg: str):
    """快速识别用户意图（含语音识别常见误写字）"""
    import re as _re
    # 同音词归一化
    msg = _re.sub(r'林叔|灵书|零书|凌舒|领书', '灵枢', msg, flags=_re.IGNORECASE)
    t = msg.lower().replace(' ', '').replace('，','').replace('。','').replace('！','').replace('？','')
    if any(w in t for w in ['拍','照','掌纹','长文','藏文','扫','看手','体质','分析','测','手掌','照相','识别']):
        return ('palm', 0.9, {})
    if any(w in t for w in ['运势','运气','黄历','今天','宜忌','每日','好不好']):
        return ('fortune', 0.85, {})
    if any(w in t for w in ['树洞','树冻','书洞','倾诉','聊天','陪我说','谈谈心','想找人','说说话','梦到','梦见','做梦','昨晚梦','梦里','梦','噩']):
        dream = msg.replace('我梦到','').replace('我梦见','').replace('梦见','').replace('梦到','').strip()
        return ('dream', 0.9, {'dream': dream})
    if any(w in t for w in ['难过','伤心','哭','压力','焦虑','烦','累','不开心','郁闷','失落','崩溃','绝望',
                              '失恋','分手','吵架','孤独','孤单','迷茫','痛苦','气死','委屈','想哭']):
        return ('companion', 0.88, {})
    if any(w in t for w in ['你好','嗨','hi','hello','在吗','灵枢','你是谁','叫什么','名字']):
        return ('greeting', 0.95, {})
    if any(w in t for w in ['谢谢','感谢','多谢','辛苦','很棒','真棒','太好了']):
        return ('thanks', 0.9, {})
    if any(w in t for w in ['再见','拜拜','bye','晚安','睡了','走了']):
        return ('goodbye', 0.9, {})
    if any(w in t for w in ['身体','健康','不舒服','疼','痛','怎么','调理','养生','吃什么','建议']):
        return ('health', 0.8, {})
    return ('chat', 0.5, {})


def _get_action_for_intent(intent):
    """意图→前端动作"""
    mapping = {
        'palm': 'switch_tab:palm',
        'fortune': 'switch_tab:fortune',
        'dream': 'switch_tab:companion',
        'companion': 'switch_tab:companion',
        'health': 'switch_tab:palm',
    }
    return mapping.get(intent)


def _detect_emotion(msg: str) -> str:
    """情绪检测（用于 TTS 音色选择）"""
    anger = sum(1 for w in ['气','怒','恨','烦','火','过分','不公平','针对'] if w in msg)
    sad = sum(1 for w in ['难过','哭','伤心','失落','委屈','累','疲惫','绝望','孤单','孤独'] if w in msg)
    fear = sum(1 for w in ['怕','害怕','担心','焦虑','紧张','慌','不安','恐惧'] if w in msg)
    joy = sum(1 for w in ['开心','高兴','哈哈','太好','棒','惊喜','快乐','幸福','感恩'] if w in msg)
    if joy > max(anger, sad, fear): return 'excited'
    if anger > max(sad, fear, joy): return 'anger'
    if sad > max(anger, fear, joy): return 'sadness'
    if fear > max(anger, sad, joy): return 'anxiety'
    return 'gentle'


def _generate_local_reply(intent, emotion, msg, params, user_name, history):
    """本地模板降级（LLM 不可用时）"""
    tones = {
        'excited': {'emotion': 'excited'},
        'sadness': {'emotion': 'sad'},
        'anger': {'emotion': 'gentle'},
        'anxiety': {'emotion': 'calm'},
        'gentle': {'emotion': 'gentle'},
    }
    tone = tones.get(emotion, tones['gentle'])

    replies = {
        'palm': f'好的{user_name}，让我看看你的掌纹~ 请切换到「掌纹」页面，手掌平放镜头前，五指自然张开。我帮你分析体质！',
        'fortune': f'{user_name}，帮你查运势~ 切换到「运势」页面，告诉我天气和计划，我帮你推演卦象。',
        'dream': f'梦是身体的密语。{user_name}，去「树洞」页面，详细说说这个梦，我帮你用中医五行解读。',
        'companion': f'{user_name}，我听到了。你的感受是真实的。愿意多说一点吗？我在这里认真听。',
        'greeting': f'{user_name}你好呀！我是灵枢，你的掌纹体质管家~ 想拍掌纹看体质、查运势、还是聊聊心事？',
        'thanks': f'不客气~ {user_name}，照顾好自己就是对我最好的感谢！',
        'goodbye': f'拜拜{user_name}~ 明天记得来找我看掌纹哦。做个好梦！',
        'health': f'{user_name}，最好的方式是拍张掌纹让我分析。切换到「掌纹」页面，我帮你看看五脏功能状态。',
        'chat': f'{user_name}，你可以跟我说：看掌纹、查运势、解梦、或者聊聊心事。我都会认真听的~',
    }

    return {
        'reply': replies.get(intent, replies['chat']),
        'emotion': tone['emotion'],
        'intent': intent,
    }


# ======================== 启动 ========================
if __name__ == '__main__':
    import threading

    print('=' * 55)
    print('  🧚 灵枢 LingShu — AI掌纹溯源 · 语音精灵版')
    print('  📱 HTTPS: https://localhost:8080 （手机/相机需此端口）')
    print('  📱 HTTP:  http://localhost:8081 （台账生成器用这个）')
    print('=' * 55)

    # HTTP 线程：给台账生成器等不需要摄像头的页面用，免证书烦恼
    def run_http():
        from flask import Flask as F2
        import sys as _s, os as _o
        _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
        http_app = F2(__name__, static_folder='static', static_url_path='')
        # 把所有路由从 app 复制到 http_app
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                http_app.add_url_rule(
                    rule.rule, rule.endpoint,
                    app.view_functions[rule.endpoint],
                    methods=rule.methods
                )
        http_app.run(host='0.0.0.0', port=8081, debug=False)

    threading.Thread(target=run_http, daemon=True).start()

    # HTTPS 主线程
    app.run(host='0.0.0.0', port=8080, debug=False, ssl_context=('ssl/cert.pem', 'ssl/key.pem'))
