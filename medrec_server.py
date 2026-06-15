# -*- coding: utf-8 -*-
"""
病历质控台账生成器 - 独立服务器（知识产权保护版）
特点：HTML 源码嵌入/无控制台/自动打开浏览器/生产级服务器
"""
import sys, os, io, json, re, time, zipfile, webbrowser, threading, shutil
import xml.etree.ElementTree as ET

# 给模块级代码用的 stderr 引用
_sys_mod = sys

# ======================== 路径自适应 ========================
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = sys._MEIPASS
    EXE_DIR = os.path.dirname(sys.executable)
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR = BUNDLE_DIR

CONFIG_PATH = os.path.join(BUNDLE_DIR, 'config.json')
EXE_CONFIG_PATH = os.path.join(EXE_DIR, 'config.json')
if os.path.exists(EXE_CONFIG_PATH):
    CONFIG_PATH = EXE_CONFIG_PATH

# 数据目录：始终用 EXE/脚本 同级的 data/，不再回退到 training-map
TRAINING_MAP_DIR = os.path.join(EXE_DIR, 'data')
MEDREC_BASE = os.path.join(TRAINING_MAP_DIR, '病历质控测试组')

# 如果 training-map 有数据但 data/ 还没有，自动复制一份
_TM_SRC = os.path.join(EXE_DIR, '..', 'training-map', '病历质控测试组')
if os.path.exists(_TM_SRC) and not os.path.exists(MEDREC_BASE):
    try:
        shutil.copytree(_TM_SRC, MEDREC_BASE)
        print(f'[INIT] 已从 training-map 复制数据到 {MEDREC_BASE}', file=_sys_mod.stderr, flush=True)
    except Exception as _e:
        print(f'[INIT] 复制失败: {_e}', file=_sys_mod.stderr, flush=True)
MEDREC_EXTRACTED = os.path.join(MEDREC_BASE, '_extracted')
MEDREC_ANALYSIS = os.path.join(MEDREC_BASE, '_analysis')

# ======================== 加载嵌入的 HTML ========================
HTML_CONTENT = ''
_html_path = os.path.join(BUNDLE_DIR, 'static', '病历质控台账生成器.html')
try:
    with open(_html_path, 'r', encoding='utf-8') as f:
        HTML_CONTENT = f.read()
except:
    HTML_CONTENT = '<h1>加载失败，请重新安装</h1>'

from flask import Flask, request, jsonify, Response
print(f'[LOAD] medrec_server.py loaded at {__file__}', file=_sys_mod.stderr, flush=True)
print(f'[LOAD] MEDREC_BASE = {MEDREC_BASE}', file=_sys_mod.stderr, flush=True)

app = Flask(__name__)

# ======================== 配置 ========================
def load_config():
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except: pass
    return {
        'llm': {'provider': 'deepseek', 'api_url': 'https://api.deepseek.com/v1/chat/completions',
                 'api_key': '', 'model': 'deepseek-chat', 'max_tokens': 600, 'temperature': 1.0},
        'agent_name': '灵枢'
    }

def call_llm(messages, config=None):
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
        import urllib.request, urllib.error
        body = json.dumps({'model': model, 'messages': messages,
                           'max_tokens': max_tokens, 'temperature': temperature,
                           'stream': False}).encode('utf-8')
        req = urllib.request.Request(api_url, data=body, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Authorization', f'Bearer {api_key}')
        resp = urllib.request.urlopen(req, timeout=90)
        result = json.loads(resp.read().decode('utf-8'))
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
    except: pass
    return None

# ======================== 提示词 ========================
POLISH_PROMPT = "你是病历质控文字润色工具。把用户输入改写为一句专业客观的质控语言，直接输出，不加任何评论问候emoji。保持原意的紧迫感，不过度委婉。"

ANALYSIS_PROMPT = """你是辽宁中医嘉和医院病历质控专家。请对照以下六维标准，逐项检查这份病历，输出 JSON 格式结果。

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
    {"dimension": "一、核心时限", "item": "入院记录24h内完成并签名", "description": "客观描述发现的问题", "responsible": "如有署名则填，否则填待确认"}
  ],
  "veto_items": [],
  "pass": true
}

只输出 JSON，不要任何解释。如果某项合格（未发现问题），不要列入 defects 数组。只列确实有问题的项。描述要专业客观，用"需关注""建议完善"等措辞。"""

# ======================== 路由：首页（嵌入HTML，不暴露静态文件） ========================
@app.route('/')
def index():
    return Response(HTML_CONTENT, mimetype='text/html; charset=utf-8')

@app.route('/病历质控台账生成器.html')
def ledger_page():
    return Response(HTML_CONTENT, mimetype='text/html; charset=utf-8')

# ======================== API: 文字润色 ========================
@app.route('/api/polish', methods=['POST'])
def polish_text():
    try:
        text = request.form.get('text', '')
        if not text.strip():
            return jsonify({'error': 'empty'}), 400
        cfg = load_config().get('llm', {})
        if not cfg.get('api_key'):
            return jsonify({'error': 'LLM not configured'}), 503
        result = call_llm([
            {'role': 'system', 'content': POLISH_PROMPT},
            {'role': 'user', 'content': text.strip()[:500]}
        ], {**cfg, 'max_tokens': 200, 'temperature': 0.3})
        if result:
            return jsonify({'polished': result.strip()})
        return jsonify({'error': 'LLM failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ======================== API: 分析列表 ========================
@app.route('/api/analysis-list', methods=['GET'])
def list_analyses():
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
                    'filename': f, 'patient_name': data.get('patient_name', '?'),
                    'ward': data.get('ward', '?'), 'attending_doctor': data.get('attending_doctor', '?'),
                    'defects_count': len(data.get('defects', [])),
                    'veto_count': len(data.get('veto_items', [])),
                    'pass': data.get('pass', False),
                })
            except:
                results.append({'filename': f, 'patient_name': '?', 'ward': '?', 'defects_count': 0, 'veto_count': 0, 'pass': False, 'attending_doctor': '?'})
        return jsonify({'analyses': results, 'total': len(results)})
    except Exception as e:
        return jsonify({'error': str(e), 'analyses': [], 'total': 0})

# ======================== API: 获取单个分析 ========================
@app.route('/api/analysis', methods=['GET'])
def get_analysis():
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

# ======================== API: 待分析文本列表 ========================
@app.route('/api/extracted-list', methods=['GET'])
def list_extracted():
    try:
        os.makedirs(MEDREC_EXTRACTED, exist_ok=True)
        files = sorted([f for f in os.listdir(MEDREC_EXTRACTED) if f.endswith('.txt')])
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

# ======================== API: 运行 AI 分析 ========================
@app.route('/api/run-analysis', methods=['POST'])
def run_analysis():
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
        {'role': 'system', 'content': ANALYSIS_PROMPT},
        {'role': 'user', 'content': f'请分析以下病历：\n\n{truncated}'}
    ], {**cfg, 'max_tokens': 1500, 'temperature': 0.1})

    if not result:
        return jsonify({'error': 'LLM call failed'}), 500

    json_match = re.search(r'\{[\s\S]*\}', result)
    if not json_match:
        return jsonify({'error': 'Failed to parse AI response', 'raw': result[:500]}), 500
    try:
        analysis = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        return jsonify({'error': f'JSON parse error: {e}', 'raw': result[:500]}), 500

    os.makedirs(MEDREC_ANALYSIS, exist_ok=True)
    json_name = fname.replace('.txt', '_analysis.json')
    json_path = os.path.join(MEDREC_ANALYSIS, json_name)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)

    return jsonify(analysis)

# ======================== API: XPS 文件列表 ========================
@app.route('/api/xps-list', methods=['GET'])
def list_xps_files():
    import sys as _sys
    print(f'[DEBUG] xps-list called, scan_path={MEDREC_BASE}', file=_sys.stderr, flush=True)
    try:
        wards = {}
        # 确保基础目录存在
        os.makedirs(MEDREC_BASE, exist_ok=True)
        for ward in ['A组', 'C组', 'D组']:
            os.makedirs(os.path.join(MEDREC_BASE, ward), exist_ok=True)
        # 1. 扫描病区子目录 (A组/C组/D组)
        for ward in ['A组', 'C组', 'D组']:
            ward_dir = os.path.join(MEDREC_BASE, ward)
            if not os.path.exists(ward_dir):
                continue
            xps_files = sorted([f for f in os.listdir(ward_dir) if f.endswith('.xps')])
            extracted_set = set()
            if os.path.exists(MEDREC_EXTRACTED):
                for f in os.listdir(MEDREC_EXTRACTED):
                    if f.endswith('.txt') and f.startswith(ward + '_'):
                        extracted_set.add(f[len(ward)+1:].replace('.txt', '.xps'))
            wards[ward] = []
            for xf in xps_files:
                wards[ward].append({'name': xf, 'extracted': xf in extracted_set, 'path': f'{ward}/{xf}'})

        # 2. 扫描根目录下的 .xps（直接放在 data/病历质控测试组/ 下）
        if os.path.exists(MEDREC_BASE):
            root_files = sorted([f for f in os.listdir(MEDREC_BASE) if f.endswith('.xps')])
            # 排除子目录中已有的（按文件名去重）
            known_names = set()
            for ward_files in wards.values():
                for wf in ward_files:
                    known_names.add(os.path.basename(wf['name']))
            root_new = [f for f in root_files if f not in known_names]
            if root_new:
                extracted_set = set()
                if os.path.exists(MEDREC_EXTRACTED):
                    for f in os.listdir(MEDREC_EXTRACTED):
                        if f.endswith('.txt'):
                            extracted_set.add(f.replace('.txt', '.xps'))
                wards['根目录（未分类）'] = []
                for xf in root_new:
                    wards['根目录（未分类）'].append({
                        'name': xf, 'extracted': xf in extracted_set, 'path': xf
                    })

        total = sum(len(v) for v in wards.values())
        extracted_total = sum(1 for v in wards.values() for f in v if f['extracted'])
        return jsonify({
            'wards': wards, 'total': total, 'extracted_total': extracted_total,
            'scan_path': MEDREC_BASE
        })
    except Exception as e:
        return jsonify({
            'error': str(e), 'wards': {}, 'total': 0,
            'scan_path': MEDREC_BASE
        })

# ======================== API: 提取 XPS ========================
@app.route('/api/extract-xps', methods=['POST'])
def extract_xps():
    files_str = request.form.get('files', '')
    if not files_str:
        return jsonify({'error': 'no files specified'}), 400
    file_list = [f.strip() for f in files_str.split(',') if f.strip()]
    results = []
    for rel_path in file_list:
        if '..' in rel_path:
            results.append({'file': rel_path, 'error': 'invalid path'})
            continue
        fpath = os.path.join(MEDREC_BASE, rel_path)
        if not os.path.exists(fpath):
            results.append({'file': rel_path, 'error': 'not found'})
            continue
        fname = os.path.basename(rel_path)
        parts = rel_path.replace('\\', '/').split('/')
        ward = parts[0] if len(parts) > 1 and parts[0] in ['A组','C组','D组'] else '未分类'
        patient_name = fname.split('（')[0] if '（' in fname else fname.replace('.xps', '')
        output_prefix = f'{ward}_' if ward != '未分类' else ''
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
            txt_path = os.path.join(MEDREC_EXTRACTED, f'{output_prefix}{txt_name}')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            results.append({'file': rel_path, 'patient_name': patient_name, 'ward': ward,
                            'chars': len(full_text), 'output': f'{output_prefix}{txt_name}', 'success': True})
        except Exception as e:
            results.append({'file': rel_path, 'error': str(e)})
    return jsonify({'results': results, 'total': len(results),
                    'success_count': sum(1 for r in results if r.get('success'))})

# ======================== API: 一键提取全部 XPS ========================
@app.route('/api/extract-all', methods=['POST'])
def extract_all_xps():
    try:
        all_pending = []
        # 扫描病区子目录
        for ward in ['A组', 'C组', 'D组']:
            ward_dir = os.path.join(MEDREC_BASE, ward)
            if not os.path.exists(ward_dir):
                continue
            xps_files = [f for f in os.listdir(ward_dir) if f.endswith('.xps')]
            extracted_set = set()
            if os.path.exists(MEDREC_EXTRACTED):
                for f in os.listdir(MEDREC_EXTRACTED):
                    if f.endswith('.txt') and f.startswith(ward + '_'):
                        extracted_set.add(f[len(ward)+1:].replace('.txt', '.xps'))
            for f in xps_files:
                if f not in extracted_set:
                    all_pending.append(f'{ward}/{f}')
        # 扫描根目录
        if os.path.exists(MEDREC_BASE):
            root_files = [f for f in os.listdir(MEDREC_BASE) if f.endswith('.xps') and os.path.isfile(os.path.join(MEDREC_BASE, f))]
            extracted_set = set()
            if os.path.exists(MEDREC_EXTRACTED):
                for f in os.listdir(MEDREC_EXTRACTED):
                    if f.endswith('.txt'):
                        extracted_set.add(f.replace('.txt', '.xps'))
            for f in root_files:
                if f not in extracted_set:
                    all_pending.append(f)
        if not all_pending:
            return jsonify({'results': [], 'total': 0, 'success_count': 0, 'message': '所有 XPS 已提取完毕'})

        results = []
        for rel_path in all_pending:
            fpath = os.path.join(MEDREC_BASE, rel_path)
            fname = os.path.basename(rel_path)
            parts = rel_path.replace('\\', '/').split('/')
            ward = parts[0] if len(parts) > 1 and parts[0] in ['A组','C组','D组'] else '未分类'
            output_prefix = f'{ward}_' if ward != '未分类' else ''
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
                txt_path = os.path.join(MEDREC_EXTRACTED, f'{output_prefix}{txt_name}')
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(full_text)
                results.append({'file': rel_path, 'patient_name': patient_name, 'ward': ward,
                                'chars': len(full_text), 'output': f'{output_prefix}{txt_name}', 'success': True})
            except Exception as e:
                results.append({'file': rel_path, 'error': str(e)})
        return jsonify({'results': results, 'total': len(results),
                        'success_count': sum(1 for r in results if r.get('success'))})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ======================== 启动 ========================
def start_browser():
    """延迟打开浏览器"""
    time.sleep(1.5)
    webbrowser.open('http://localhost:8081')

if __name__ == '__main__':
    # 确保必要目录存在
    os.makedirs(MEDREC_EXTRACTED, exist_ok=True)
    os.makedirs(MEDREC_ANALYSIS, exist_ok=True)
    for ward in ['A组', 'C组', 'D组']:
        os.makedirs(os.path.join(MEDREC_BASE, ward), exist_ok=True)

    print('=' * 55)
    print('  辽宁中医嘉和医院 · 病历质控台账生成器 v2.0')
    print('  http://localhost:8081')
    print('  浏览器将自动打开，请勿关闭本窗口')
    print('=' * 55)

    # 自动打开浏览器
    threading.Thread(target=start_browser, daemon=True).start()

    # 尝试使用 waitress（生产级），失败则降级到 Flask dev server
    try:
        from waitress import serve
        import logging
        logging.getLogger('waitress').setLevel(logging.WARNING)
        serve(app, host='0.0.0.0', port=8081, _quiet=True)
    except ImportError:
        app.run(host='0.0.0.0', port=8081, debug=False)
