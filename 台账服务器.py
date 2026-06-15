# -*- coding: utf-8 -*-
"""
病历质控台账生成器 — 极简版
XPS 放入 病历数据/ → 刷新 → 提取 → 分析 → 导入台账 → 导出Excel
"""
import sys, os, io, json, re, time, zipfile, webbrowser, threading, shutil
import xml.etree.ElementTree as ET

# ===== 路径：EXE/脚本同级目录下的"病历数据"文件夹 =====
if getattr(sys, 'frozen', False):
    ROOT = os.path.dirname(sys.executable)
    BUNDLE = sys._MEIPASS
else:
    ROOT = os.path.dirname(os.path.abspath(__file__))
    BUNDLE = ROOT

DATA_DIR = os.path.join(ROOT, '病历数据')
XPS_DIR = os.path.join(DATA_DIR, 'XPS源文件')       # 放 .xps
TXT_DIR = os.path.join(DATA_DIR, '已提取文本')       # 提取后的 .txt
JSON_DIR = os.path.join(DATA_DIR, 'AI分析结果')      # 分析后的 .json
CONFIG = os.path.join(ROOT, 'config.json')

# 确保目录存在
for d in [XPS_DIR, TXT_DIR, JSON_DIR]:
    os.makedirs(d, exist_ok=True)

# ===== Flask =====
from flask import Flask, request, jsonify, Response
app = Flask(__name__)
@app.route("/api/ping", methods=["GET"])
def ping():
    return jsonify({"has_search": True})

# ===== HTML 路径 =====
_HTML_PATH = os.path.join(BUNDLE, 'static', '病历质控台账生成器.html')

# ===== 配置 =====
def load_config():
    try:
        if os.path.exists(CONFIG):
            with open(CONFIG, 'r', encoding='utf-8') as f:
                return json.load(f)
    except: pass
    return {
        'llm': {'api_url': 'https://api.deepseek.com/v1/chat/completions',
                'api_key': '', 'model': 'deepseek-chat', 'max_tokens': 600, 'temperature': 1.0}
    }

def call_llm(msgs, cfg=None):
    if cfg is None: cfg = load_config()['llm']
    if not cfg['api_key']: return None
    try:
        import urllib.request
        body = json.dumps({'model':cfg['model'],'messages':msgs,'max_tokens':cfg.get('max_tokens',600),
                           'temperature':cfg.get('temperature',0.8),'stream':False}).encode()
        req = urllib.request.Request(cfg['api_url'], body, {'Content-Type':'application/json',
                                     'Authorization':f'Bearer {cfg["api_key"]}'})
        r = urllib.request.urlopen(req, timeout=120)
        return json.loads(r.read())['choices'][0]['message']['content']
    except: return None

# ===== 提示词 =====
POLISH = "你是病历质控文字润色工具。把用户输入改写为一句专业客观的质控语言，直接输出，不加任何评论问候emoji。"

ANALYSIS = """你是辽宁中医嘉和医院病历质控专家。请对照以下六维标准，逐项检查这份病历，输出 JSON 格式结果。

## 六维标准（34项细则 + 5项一票否决）

一、核心时限：入院记录24h·首程8h·主治查房48h·主任查房72h·连续3天病程·康复评定72h·阶段小结30天
二、康复专项：标准化量表·中期评定4周·治疗记录单完整·三单一致
三、病程记录质量：首程要素完整·上级查房分析·病情变化记录·有创操作记录·患方签名·阶段小结非复制
四、文书完整性：一般项目无空项·三史无遗漏·体格检查完整·辅助检查有序·报告单签名·医师亲笔签名·首页完整·出院小结
五、知情同意：授权委托书·特殊检查同意书·康复风险告知书·各类告知书齐全·患方签名+日期
六、书写规范：无大段复制粘贴·双线划改·24h制·术语规范

一票否决：核心记录超时24h以上·康复初始评定完全缺失·知情同意书缺失/伪造·诊断与治疗严重不符·复制粘贴致重大错误

## 输出（只输出JSON）
{"patient_name":"","admit_no":"","ward":"A/C/D","attending_doctor":"","summary":"一句话","defects":[{"dimension":"一、核心时限","item":"入院记录24h内完成","description":"客观描述","responsible":"姓名或待确认"}],"veto_items":[],"pass":false}"""

# ===== 首页（每次实时读取，不缓存） =====
@app.route('/')
@app.route('/病历质控台账生成器.html')
def index():
    try:
        with open(_HTML_PATH, 'r', encoding='utf-8') as f:
            return Response(f.read(), mimetype='text/html; charset=utf-8')
    except:
        return Response('<h1>HTML 文件读取失败</h1>', mimetype='text/html; charset=utf-8')
# ===== 配置管理 =====
@app.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    if request.method == 'GET':
        cfg = load_config()
        llm = cfg.get('llm', {})
        return jsonify({
            'api_url': llm.get('api_url', ''),
            'model': llm.get('model', ''),
            'api_key': llm.get('api_key', '')[:8] + '***' if llm.get('api_key') else '',
        })
    # POST: 保存配置
    try:
        cfg = load_config()
        if 'api_key' in request.form and request.form['api_key']:
            cfg['llm']['api_key'] = request.form['api_key']
        if 'model' in request.form:
            cfg['llm']['model'] = request.form['model']
        if 'api_url' in request.form:
            cfg['llm']['api_url'] = request.form['api_url']
        with open(CONFIG, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== 润色 =====
@app.route('/api/polish', methods=['POST'])
def polish():
    t = request.form.get('text','').strip()[:500]
    if not t: return jsonify({'error':'empty'}), 400
    r = call_llm([{'role':'system','content':POLISH},{'role':'user','content':t}],
                 {**load_config()['llm'], 'max_tokens':200, 'temperature':0.3})
    return jsonify({'polished':r.strip()}) if r else (jsonify({'error':'failed'}), 500)

# ===== 全局搜索引擎 =====
def _find_project_root(start_dir):
    """向上查找 CC Switch 项目根目录（以 serve.bat 或 index.html 为标记）
    确保无论 EXE 放在哪里都能定位到项目根，全局搜索不漏文件。"""
    d = os.path.abspath(start_dir)
    for _ in range(5):  # 最多向上5层
        if os.path.exists(os.path.join(d, 'serve.bat')) or \
           os.path.exists(os.path.join(d, 'index.html')):
            return d
        parent = os.path.dirname(d)
        if parent == d:  # 到达文件系统根
            break
        d = parent
    return start_dir  # 兜底：找不到标记就用启动目录

SEARCH_ROOT = _find_project_root(ROOT)

@app.route('/api/search')
def global_search():
    """全局搜索：扫描整个 CC Switch 目录树，找到所有病历相关文件"""
    try:
        result = {'xps': [], 'txt': [], 'json': [], 'search_root': SEARCH_ROOT}
        for dirpath, dirnames, filenames in os.walk(SEARCH_ROOT):
            # 跳过系统目录
            dirnames[:] = [d for d in dirnames if d not in ['__pycache__','.git','node_modules','build','.claude']]
            depth = dirpath.replace(SEARCH_ROOT, '').count(os.sep)
            if depth > 6:  # 限制深度
                dirnames[:] = []
            for f in filenames:
                fp = os.path.join(dirpath, f)
                rel = os.path.relpath(fp, SEARCH_ROOT)
                try:
                    st = os.stat(fp)
                    size_kb = st.st_size // 1024
                except:
                    continue
                if f.lower().endswith('.xps') and not f.startswith('~'):
                    result['xps'].append({'name': f, 'path': rel, 'dir': dirpath, 'size_kb': size_kb})
                elif f.endswith('.txt') and ('_extracted' in dirpath or '已提取' in dirpath):
                    result['txt'].append({'name': f, 'path': rel, 'dir': dirpath, 'size_kb': size_kb})
                elif f.endswith('.json') and ('_analysis' in dirpath or 'AI分析' in dirpath or 'analysis' in f.lower()):
                    # 读取摘要
                    try:
                        with open(fp, 'r', encoding='utf-8') as jf:
                            d = json.load(jf)
                        result['json'].append({
                            'name': f, 'path': rel, 'dir': dirpath,
                            'patient_name': d.get('patient_name','?'),
                            'ward': d.get('ward','?'),
                            'attending_doctor': d.get('attending_doctor','?'),
                            'defects_count': len(d.get('defects',[])),
                            'veto_count': len(d.get('veto_items',[])),
                            'pass': d.get('pass', False),
                            'summary': d.get('summary','')[:80]
                        })
                    except:
                        result['json'].append({'name': f, 'path': rel, 'dir': dirpath, 'patient_name':'?'})
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'xps':[], 'txt':[], 'json':[]})

# ===== 通过路径读取或处理文件 =====
@app.route('/api/file-action', methods=['POST'])
def file_action():
    """通用文件操作：extract(提取XPS) / analyze(分析txt) / read(读取内容)"""
    action = request.form.get('action','')
    fpath = request.form.get('path','')
    if not fpath or '..' in fpath: return jsonify({'error':'bad path'}), 400
    if not os.path.isabs(fpath):
        fpath = os.path.join(SEARCH_ROOT, fpath)
    if not os.path.exists(fpath): return jsonify({'error':f'not found: {fpath}'}), 404

    if action == 'extract':
        return _do_extract(fpath)
    elif action == 'analyze':
        return _do_analyze(fpath)
    elif action == 'read':
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                return jsonify({'content': f.read()[:500], 'path': fpath})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error':'unknown action'}), 400

def _do_extract(fp):
    fname = os.path.basename(fp)
    try:
        txt = []
        with zipfile.ZipFile(fp) as z:
            for pg in sorted([n for n in z.namelist() if n.endswith('.fpage')]):
                root = ET.fromstring(z.read(pg).decode('utf-8'))
                gs = [g.get('UnicodeString','') for g in root.findall('.//{http://schemas.microsoft.com/xps/2005/06}Glyphs') if g.get('UnicodeString','').strip()]
                if gs: txt.append('\n'.join(gs))
        full = '\n--- PAGE ---\n'.join(txt)
        if not full.strip(): return jsonify({'error':'empty'}), 500
        tname = fname.replace('.xps','.txt')
        with open(os.path.join(TXT_DIR, tname), 'w', encoding='utf-8') as f:
            f.write(full)
        return jsonify({'success':True, 'file':fname, 'chars':len(full), 'output':tname})
    except Exception as e:
        return jsonify({'error':str(e)}), 500

def _do_analyze(fp):
    fname = os.path.basename(fp)
    try:
        with open(fp, 'r', encoding='utf-8') as f:
            text = f.read()[:8000]
    except: return jsonify({'error':'read failed'}), 500
    cfg = load_config()['llm']
    if not cfg['api_key']: return jsonify({'error':'no API key'}), 503
    r = call_llm([{'role':'system','content':ANALYSIS},{'role':'user','content':f'请分析：\n\n{text}'}],
                 {**cfg, 'max_tokens':1500, 'temperature':0.1})
    if not r: return jsonify({'error':'LLM failed'}), 500
    m = re.search(r'\{[\s\S]*\}', r)
    if not m: return jsonify({'error':'bad response','raw':r[:300]}), 500
    try: a = json.loads(m.group())
    except: return jsonify({'error':'JSON parse','raw':r[:300]}), 500
    jname = fname.replace('.txt','_analysis.json')
    with open(os.path.join(JSON_DIR, jname), 'w', encoding='utf-8') as f:
        json.dump(a, f, ensure_ascii=False, indent=2)
    return jsonify(a)

# ===== 提取单份XPS（旧接口保留） =====
@app.route('/api/extract-xps', methods=['POST'])
def extract_xps():
    fname = request.form.get('file','')
    if not fname or '..' in fname: return jsonify({'error':'bad file'}), 400
    fp = os.path.join(XPS_DIR, fname)
    if not os.path.exists(fp): return jsonify({'error':'not found'}), 404
    try:
        txt = []
        with zipfile.ZipFile(fp) as z:
            for pg in sorted([n for n in z.namelist() if n.endswith('.fpage')]):
                root = ET.fromstring(z.read(pg).decode('utf-8'))
                gs = [g.get('UnicodeString','') for g in root.findall('.//{http://schemas.microsoft.com/xps/2005/06}Glyphs') if g.get('UnicodeString','').strip()]
                if gs:
                    txt.append('\n'.join(gs))
        full = '\n--- PAGE ---\n'.join(txt)
        if not full.strip(): return jsonify({'error':'empty'}), 500
        tname = fname.replace('.xps','.txt')
        with open(os.path.join(TXT_DIR, tname), 'w', encoding='utf-8') as f:
            f.write(full)
        return jsonify({'file':fname, 'chars':len(full), 'output':tname, 'success':True})
    except Exception as e:
        return jsonify({'error':str(e)}), 500

# ===== 提取全部 =====
@app.route('/api/extract-all', methods=['POST'])
def extract_all():
    done = set()
    for f in os.listdir(TXT_DIR):
        if f.endswith('.txt'): done.add(f.replace('.txt','.xps'))
    pending = [f for f in os.listdir(XPS_DIR) if f.lower().endswith('.xps') and f not in done]
    results = []
    for fname in pending:
        try:
            fp = os.path.join(XPS_DIR, fname)
            txt = []
            with zipfile.ZipFile(fp) as z:
                for pg in sorted([n for n in z.namelist() if n.endswith('.fpage')]):
                    root = ET.fromstring(z.read(pg).decode('utf-8'))
                    gs = [g.get('UnicodeString','') for g in root.findall('.//{http://schemas.microsoft.com/xps/2005/06}Glyphs') if g.get('UnicodeString','').strip()]
                    if gs: txt.append('\n'.join(gs))
            full = '\n--- PAGE ---\n'.join(txt)
            if not full.strip(): continue
            tname = fname.replace('.xps','.txt')
            with open(os.path.join(TXT_DIR, tname), 'w', encoding='utf-8') as f:
                f.write(full)
            results.append({'file':fname, 'chars':len(full), 'success':True})
        except Exception as e:
            results.append({'file':fname, 'error':str(e)})
    return jsonify({'results':results, 'total':len(results), 'success':sum(1 for r in results if r.get('success'))})

# ===== 已提取文本列表 =====
@app.route('/api/extracted-list')
def extracted_list():
    txts = sorted([f for f in os.listdir(TXT_DIR) if f.endswith('.txt')])
    analyzed = set()
    for f in os.listdir(JSON_DIR):
        if f.endswith('.json'): analyzed.add(f.replace('_analysis.json','.txt').replace('.json','.txt'))
    return jsonify({
        'files': [{'name':f, 'analyzed':f in analyzed} for f in txts],
        'total': len(txts)
    })

# ===== AI分析 =====
@app.route('/api/run-analysis', methods=['POST'])
def run_analysis():
    fname = request.form.get('file','')
    if not fname or '..' in fname: return jsonify({'error':'bad file'}), 400
    fp = os.path.join(TXT_DIR, fname)
    if not os.path.exists(fp): return jsonify({'error':'not found'}), 404
    with open(fp, encoding='utf-8') as f:
        text = f.read()[:8000]
    cfg = load_config()['llm']
    if not cfg['api_key']: return jsonify({'error':'no API key'}), 503
    r = call_llm([{'role':'system','content':ANALYSIS},{'role':'user','content':f'请分析：\n\n{text}'}],
                 {**cfg, 'max_tokens':1500, 'temperature':0.1})
    if not r: return jsonify({'error':'LLM failed'}), 500
    m = re.search(r'\{[\s\S]*\}', r)
    if not m: return jsonify({'error':'bad response','raw':r[:300]}), 500
    try:
        a = json.loads(m.group())
    except:
        return jsonify({'error':'JSON parse failed','raw':r[:300]}), 500
    jname = fname.replace('.txt','_analysis.json')
    with open(os.path.join(JSON_DIR, jname), 'w', encoding='utf-8') as f:
        json.dump(a, f, ensure_ascii=False, indent=2)
    return jsonify(a)

# ===== 通过路径读取完整 JSON（用于导入） =====
@app.route('/api/read-json')
def read_json():
    fpath = request.args.get('path','')
    if not fpath or '..' in fpath: return jsonify({'error':'bad'}), 400
    if not os.path.isabs(fpath):
        fpath = os.path.join(SEARCH_ROOT, fpath)
    if not os.path.exists(fpath): return jsonify({'error':'not found'}), 404
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({'error':str(e)}), 500

# ===== 分析结果列表 =====
@app.route('/api/analysis-list')
def analysis_list():
    jsons = sorted([f for f in os.listdir(JSON_DIR) if f.endswith('.json')])
    results = []
    for f in jsons:
        try:
            with open(os.path.join(JSON_DIR, f), encoding='utf-8') as fp:
                d = json.load(fp)
            results.append({'filename':f, 'patient_name':d.get('patient_name','?'),
                           'ward':d.get('ward','?'), 'attending_doctor':d.get('attending_doctor','?'),
                           'defects_count':len(d.get('defects',[])), 'veto_count':len(d.get('veto_items',[])),
                           'pass':d.get('pass',False)})
        except: pass
    return jsonify({'analyses':results, 'total':len(results)})

# ===== 获取单个分析 =====
@app.route('/api/analysis')
def get_analysis():
    fn = request.args.get('file','')
    if not fn or '..' in fn: return jsonify({'error':'bad'}), 400
    fp = os.path.join(JSON_DIR, fn)
    if not os.path.exists(fp): return jsonify({'error':'not found'}), 404
    with open(fp, encoding='utf-8') as f:
        return jsonify(json.load(f))

# ===== 启动 =====
def _open_browser():
    time.sleep(1)
    webbrowser.open('http://localhost:8081')

if __name__ == '__main__':
    print('*'*55)
    print(' 辽宁中医嘉和医院 · 病历质控台账生成器')
    print(f' 数据目录: {DATA_DIR}')
    print(f' XPS源文件: {XPS_DIR}')
    print('*'*55)

    # 打印全部注册路由，启动时核对/api/ping是否存在
    print("===台账服务已注册路由列表===")
    for route in app.url_map.iter_rules():
        print(route)

    # 浏览器打开线程
    threading.Thread(target=_open_browser, daemon=True).start()
    try:
        from waitress import serve
        import logging
        logging.getLogger('waitress').setLevel(logging.WARNING)
        # waitress监听本地8081
        serve(app, host='127.0.0.1', port=8081, _quiet=True)
    except:
        # Flask兜底：关闭热重载，单进程运行，杜绝404
        app.run(host='127.0.0.1', port=8081, debug=False, use_reloader=False)
