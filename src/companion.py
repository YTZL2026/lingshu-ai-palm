# -*- coding: utf-8 -*-
"""
AI掌纹溯源 — 情绪伴侣引擎
PUA·职场冷暴力·学习压力·生活受挫等场景的情绪排解

理论框架：
  积极心理学（Positive Psychology, Seligman）
  认知行为疗法（CBT）基础原则
  共情倾听技术（Carl Rogers 人本主义）
  中国传统智慧中的情绪调节（《黄帝内经》情志理论）

参考：
  [E1] Martin Seligman. "Flourish". 2011.
  [E2] Carl Rogers. "On Becoming a Person". 1961.
  [E3] 《黄帝内经·素问·举痛论》 — "怒则气上，喜则气缓，悲则气消，恐则气下"
  [E4] 彭凯平.《活出心花怒放的人生》. 中信出版社, 2020.
"""

from typing import Tuple
import random

COMPANION_SCENARIOS = {
    'pua': {
        'name': 'PUA/情感操控',
        'icon': '💔',
        'desc': '被贬低、被控制、自我怀疑...你不是一个人',
        'intro': '我听到了你的声音。PUA的核心是让对方怀疑自己的感受——而你的感受是真实的、有效的。我们先做一次深呼吸：吸气4秒，屏住2秒，呼气6秒。\n\n好的。现在我们一起看看：',
        'steps': [
            '🔍 识别操控信号：对方是否反复贬低你？是否让你觉得自己"不够好"？是否隔离你的社交圈？',
            '💪 重建自我价值：你的价值不依赖于任何人的评价。列出你独立于这段关系之外的三个优点。',
            '🚧 设立边界："我有权保护自己的情感空间"——这句话你可以对自己说，也可以对对方说。',
            '📞 支持网络：你现在最信任的一个人是谁？如果可以，今天就和ta聊聊。',
        ],
        'affirmation': '你没有做错什么。被操控不是你的弱点，是操控者的手段。你值得被尊重、被珍视。今天你能意识到这一点，已经是巨大的勇气。',
    },
    'workplace': {
        'name': '职场冷暴力',
        'icon': '🏢',
        'desc': '被孤立、被打压、付出不被看见...',
        'intro': '职场冷暴力是一种隐形伤害——它不像语言暴力那样明显，却同样伤人。被忽视、被排挤、付出不被认可——这些感受都是真实的。\n\n先允许自己感到不舒服，这不代表你不够专业。然后我们一步步来：',
        'steps': [
            '📋 客观记录：把让你不舒服的具体事件写下来（时间、地点、谁做了什么），区分事实和感受。',
            '🎯 明确诉求：你希望在什么方面被公平对待？把它具体化，而不是笼统的"被尊重"。',
            '🗣️ 策略沟通：选择一个合适的时机，用"I feel"句式表达："当XX发生时，我感到XX，我希望XX。"',
            '🌱 自我成长：这段经历让你更清楚什么是不健康的工作环境。长期来看，这也是职业判断力的提升。',
        ],
        'affirmation': '你的专业价值不由任何一个同事或上司来定义。冷暴力往往反映了施与者自身的问题，而非你的不足。你值得在一个尊重你的环境中工作。',
    },
    'study': {
        'name': '学习压力',
        'icon': '📚',
        'desc': '考试焦虑、学习倦怠、自我怀疑...',
        'intro': '学习的压力往往来自"我必须完美"的信念——但其实，学习本身就是不断试错的过程。《黄帝内经》说"怒则气上，恐则气下"，过度的恐惧和焦虑会抑制思维的活跃。\n\n先放下手中的书，我们一起调整状态：',
        'steps': [
            '🧘 身体扫描：闭上眼睛，注意力从头顶慢慢移到脚尖，感受每一处肌肉的紧张和放松。',
            '📊 合理归因：这次没考好，具体是哪个知识点没掌握？把"我很差"换成"这个知识点我还需要加强"。',
            '⏰ 番茄工作法：25分钟专注 + 5分钟休息。不是学得越久越好，而是学得越专注越好。',
            '🏆 小成就记录：今天你完成了什么？哪怕只是背了5个单词，也值得被记录下来。',
        ],
        'affirmation': '学习是一辈子的事，不是一场考试的事。你已经比昨天的自己进步了，这才是最重要的。休息也是学习的一部分——你不是在偷懒，你是在给大脑充电。',
    },
    'life': {
        'name': '生活受挫',
        'icon': '🌈',
        'desc': '失恋、失业、迷茫、觉得人生没有方向...',
        'intro': '人生如四季，有春华秋实，也有寒冬凛冽。《黄帝内经》说"悲则气消"——悲伤会消耗我们的能量，这是正常的生理反应。你不是"不够坚强"，你只是正在经历一个自然的情绪过程。\n\n先接纳现在的自己：',
        'steps': [
            '🕯️ 接纳当下：允许自己难过。不需要假装坚强，不需要马上"振作起来"。此刻的感受是真实的，而真实的感受终会过去。',
            '🔭 拉长视角：回想五年前让你痛苦的事，今天看来是什么感觉？五年后再看今天的事，你可能会感谢这段经历。',
            '🌱 微小的掌控感：今天只做一件小事——整理桌面、洗个热水澡、走10分钟路。从一件小事开始恢复"我能掌控生活"的感觉。',
            '💌 给未来的自己写信：写一封信给三个月后的自己，告诉他/她你现在的心情，以及你希望三个月后的自己过什么样的生活。',
        ],
        'affirmation': '人生没有白走的路，每一步都算数。此刻的低谷是你人生的深度——它让你未来的快乐更值得珍惜。黑暗中你仍然在成长，只是暂时看不到光。但光，一定会来。',
    },
    'general': {
        'name': '情绪舒缓',
        'icon': '🌿',
        'desc': '说不清原因，就是不舒服、烦躁、低落...',
        'intro': '有时候我们不需要一个具体的理由来觉得不开心。情绪就像天气，有晴有阴，都是自然的。\n\n我们先不急着"解决问题"，先跟自己的情绪待一会儿：',
        'steps': [
            '🌬️ 4-7-8呼吸法：吸气4秒→屏息7秒→缓慢呼气8秒。重复3次。感受气息进入和离开身体。',
            '📝 情绪命名：你现在感受到的情绪叫什么名字？焦虑？烦躁？空虚？给它一个名字，它就不再是无形的怪兽。',
            '🎨 自由书写：拿一张纸，不加思考地写5分钟。不管写什么，不用管字迹好不好看。',
            '🚶 接地练习：说出你看到的5样东西、听到的4种声音、感受到的3种触感、闻到的2种气味、尝到的1种味道。',
        ],
        'affirmation': '你不需要时刻都"好"。情绪来了，它也会走。你比你的情绪更大——你是天空，情绪只是飘过的云。照顾好今天的自己，就是对未来最好的投资。',
    },
}

# 快速情绪舒缓音乐推荐（中国传统音乐 + 自然白噪音）
MUSIC_RECOMMENDATIONS = [
    {'name':'古琴·流水','desc':'清越悠远，如临溪畔','url':''},
    {'name':'琵琶·春江花月夜','desc':'婉转恬静，心随月明','url':''},
    {'name':'古筝·高山流水','desc':'知音相伴，山水之间','url':''},
    {'name':'雨声白噪音','desc':'淅沥雨声，宁静致远','url':''},
    {'name':'森林鸟鸣','desc':'鸟语林间，生机盎然','url':''},
    {'name':'海浪轻拍','desc':'潮起潮落，烦恼随之而去','url':''},
]


def get_companion_response(scenario: str, user_message: str = '') -> dict:
    """获取情绪伴侣回应（场景模式）"""
    scene = COMPANION_SCENARIOS.get(scenario, COMPANION_SCENARIOS['general'])
    return {
        'scenario_name': scene['name'], 'icon': scene['icon'], 'desc': scene['desc'],
        'intro': scene['intro'], 'steps': scene['steps'], 'affirmation': scene['affirmation'],
    }


# 自由对话关键词→场景匹配
COMPANION_KEYWORDS = {
    'pua': ['pua','操控','控制','贬低','打压','不值得','配不上','煤气灯','自恋','情感虐待','分手'],
    'workplace': ['职场','同事','领导','老板','排挤','孤立','冷暴力','穿小鞋','降薪','裁员','加班'],
    'study': ['考试','学习','成绩','挂科','考研','高考','复习','论文','毕业','厌学','做题'],
    'life': ['失恋','分手','失业','迷茫','没方向','无聊','孤独','空虚','失败','失去','痛苦'],
}

# 多轮对话级的共情回应模板
EMPATHY_RESPONSES = {
    'greeting': [
        '我在这里，你想说什么都可以。不用组织语言，想到什么就说什么。',
        '谢谢你愿意跟我分享。我在听。',
        '深呼吸一下，慢慢说。这里没有评判，只有倾听。',
    ],
    'acknowledge': [
        '我听到了。这种感受是真实的，也是重要的。',
        '嗯，这确实不容易。你愿意多说一点吗？',
        '谢谢你告诉我这些。能说出来，本身就很有勇气。',
    ],
    'explore': [
        '这种感觉是从什么时候开始的？',
        '当这件事发生的时候，你身体有什么感觉吗？比如胸口紧、肩膀硬？',
        '如果用一个词来形容现在的感受，会是什么？',
    ],
    'support': [
        '你不是一个人在经历这些。很多人都有类似的感受，只是很少有人愿意说出来。',
        '你的感受是正常的。面对这样的处境，任何人都会觉得不容易。',
        '我听到的是一个在努力应对困难的人。你比自己意识到的更坚强。',
    ],
    'action': [
        '今天可以做一件小事来照顾自己——喝一杯热水、走五分钟路、或者只是深呼吸三次。你选哪一个？',
        '不需要马上解决所有问题。今天只关注一件事就好，你想先关注哪件？',
        '给自己五分钟，什么都不做，就坐着呼吸。这不是逃避，这是给自己充电。',
    ],
    'close': [
        '今天的对话就到这里。记住：你的感受被听到了，你是重要的。需要的时候，我随时在这里。',
        '谢谢你跟我聊这些。照顾好今天的自己——你已经做得够多了。',
    ],
}


def _extract_topic(msg: str) -> str:
    """从消息中提取具体话题（用于在回应中复述，表示理解）"""
    # 移除常见语气词
    for filler in ['就是','感觉','觉得','好像','可能','吧','啊','呀','呢','了','的','很','有点','特别','非常']:
        msg = msg.replace(filler, ' ')
    # 取关键词片段
    words = [w for w in msg.split() if len(w) >= 2]
    if len(words) >= 3:
        return ' '.join(words[:6])  # 前6个有效词
    return msg[:40]


def _detect_emotion(msg: str) -> str:
    """检测情绪基调"""
    anger = sum(1 for w in ['气','怒','恨','烦','火','操','妈的','过分','凭什么','不公平','针对'] if w in msg)
    sad = sum(1 for w in ['难过','哭','伤心','失落','委屈','累','疲惫','绝望','抑郁','孤单','孤独'] if w in msg)
    fear = sum(1 for w in ['怕','害怕','担心','焦虑','紧张','慌','不安','恐惧','压力'] if w in msg)
    confused = sum(1 for w in ['迷茫','不知道','怎么办','困惑','纠结','犹豫','矛盾'] if w in msg)

    if anger > sad and anger > fear: return 'anger'
    if sad > anger and sad > fear: return 'sadness'
    if fear > sad and fear > anger: return 'anxiety'
    if confused > 0: return 'confused'
    return 'general'


# 针对性回应模板（不再random，而是根据情绪和话题匹配）
def _build_contextual_reply(msg: str, topic: str, emotion: str, scene_id: str, history_len: int) -> Tuple[str, str]:
    """根据实际情况构建上下文相关回应"""

    scene = COMPANION_SCENARIOS.get(scene_id, COMPANION_SCENARIOS['general'])
    topic_echo = f'我听到你说"{topic}"——'

    # 根据情绪选择开场
    emotion_openers = {
        'anger': f'{topic_echo}这件事让你很生气，这种愤怒是正常的。被不公正对待的时候，任何人都会愤怒。\n\n愤怒说明你在乎——在乎公平、在乎尊严、在乎自己的边界。这些都是在乎自己的表现。',
        'sadness': f'{topic_echo}听起来你现在心里很重。难过不是软弱，难过是因为你在乎的东西受到了伤害。\n\n允许自己难过。不需要马上"好起来"。悲伤是心灵在消化痛苦，给它一点时间。',
        'anxiety': f'{topic_echo}这种焦虑的感觉我理解——心里像是绷着一根弦。焦虑其实是你的大脑在试图保护你，只是它有时候保护得太用力了。\n\n我们先做一件事：深呼吸三次，把注意力放在呼吸上。你刚才说的这件事，我们一起慢慢看。',
        'confused': f'{topic_echo}当事情不太清晰的时候，感到迷茫是很自然的。迷茫不是没有方向，而是你正在寻找方向——这本身就是前进。\n\n有时候我们不需要马上有答案。先接纳"我现在还不确定"这件事本身。',
        'general': random.choice([
            f'{topic_echo}嗯，我听到了。',
            f'{topic_echo}继续说，我在。',
            f'{topic_echo}明白了——你接着说。',
            f'嗯，你继续说。',
            f'我听着呢。',
        ]),
    }
    reply = emotion_openers.get(emotion, emotion_openers['general'])

    # 根据场景加入具体引导
    if scene_id == 'pua':
        reply += '\n\n在一段关系中感到被贬低或控制，这不是你的问题。健康的关系应该让你感到安全、被尊重、可以做自己。你现在的感受是你内心的保护机制在提醒你：有什么东西不对。相信这个信号。'
    elif scene_id == 'workplace':
        reply += '\n\n职场中的不公正对待确实让人疲惫。记住：你的专业能力不取决于任何一个领导或同事的评价。给自己一些空间，区分"工作上的反馈"和"对人的不尊重"——前者可以改进，后者你有权拒绝。'
    elif scene_id == 'study':
        reply += '\n\n学习的压力往往来自"我必须完美"——但成长本身就是不断试错。今天做不到不代表永远做不到。把目标从"必须考好"换成"今天比昨天多掌握一个知识点"——小步前进也是前进。'
    elif scene_id == 'life':
        reply += '\n\n人生有起有落，就像四季更替。此刻的低谷不是终点——它只是你人生长路上的一个转弯。很多后来让你成长最多的经历，在当时看来都是最难熬的。给自己一点时间。'

    # 多轮对话调整
    if history_len >= 3:
        reply += f'\n\n聊了这么多，我想说：你愿意面对这些情绪，本身就很了不起。今天可以为自己做一件小事吗？哪怕只是好好喝一杯水、走五分钟路、或者听一首喜欢的歌。照顾自己，从现在开始。'

    # 肯定语
    affirmations_map = {
        'anger': '你的愤怒是正当的。它保护着你的底线。',
        'sadness': '会流泪说明你心里还有柔软的地方——那是最珍贵的地方。',
        'anxiety': '焦虑是你在乎的证明。你已经足够好了。',
        'confused': '迷茫是成长的开始。不急着有答案，答案会来找你。',
        'general': '你的感受是重要的。你值得被温柔对待。',
    }
    affirmation = affirmations_map.get(emotion, affirmations_map['general'])

    return reply, affirmation


def chat_companion(user_message: str, history: list = None) -> dict:
    """
    自由对话情绪伴侣 V2 — 理解上下文，针对性回应

    流程：提取话题→检测情绪→匹配场景→构建上下文回应
    不再使用random.choice()随机模板
    """
    if not user_message or not user_message.strip():
        return {
            'reply': '我在这里，你想说什么都可以。不用组织语言，想到什么就说什么。我会认真听。',
            'scenario': 'general', 'icon': '🌿', 'affirmation': '', 'suggest_followup': True,
        }

    msg = user_message.strip()

    # 1. 提取具体话题
    topic = _extract_topic(msg)

    # 2. 检测情绪
    emotion = _detect_emotion(msg)

    # 3. 匹配场景
    matched_scene = 'general'
    max_matches = 0
    for scene_id, keywords in COMPANION_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in msg)
        if matches > max_matches:
            max_matches = matches
            matched_scene = scene_id

    scene = COMPANION_SCENARIOS.get(matched_scene, COMPANION_SCENARIOS['general'])
    hist_len = len(history) if history else 0

    # 4. 构建上下文相关回应
    reply, affirmation = _build_contextual_reply(msg, topic, emotion, matched_scene, hist_len)

    return {
        'reply': reply,
        'scenario': matched_scene,
        'icon': scene['icon'],
        'affirmation': affirmation,
        'suggest_followup': len(msg) < 30,
    }
