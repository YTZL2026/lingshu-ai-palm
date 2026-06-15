# -*- coding: utf-8 -*-
"""
病历质控台账生成器 - 一键打包脚本
运行: python build_exe.py
"""
import os, sys, shutil, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(BASE, 'dist')
BUILD = os.path.join(BASE, 'build')
TRAINING_MAP = os.path.join(BASE, '..', 'training-map', '病历质控测试组')
LOGO_PNG = os.path.join(BASE, '..', 'palm-ai', '掌纹溯源ico.png')
ICO_PATH = os.path.join(BASE, 'app_icon.ico')

def run(cmd, desc=''):
    print(f'  {desc}...')
    result = subprocess.run(cmd, shell=True, cwd=BASE,
                           capture_output=True, text=True)
    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip()
        if err:
            print(f'  Error: {err[-300:]}')
        return False
    return True

def main():
    print('=' * 55)
    print('  MedRec Ledger - EXE Builder')
    print('=' * 55)

    # Step 1: Check env
    print('\n[1/6] Checking Python...')
    try:
        v = subprocess.check_output([sys.executable, '--version'], text=True)
        print(f'  OK: Python {v.strip()}')
    except:
        print('  ERROR: Python not found')
        return

    # Step 2: Convert logo PNG to ICO
    print('\n[2/6] Converting logo to .ico...')
    if os.path.exists(LOGO_PNG):
        try:
            from PIL import Image
            img = Image.open(LOGO_PNG)
            sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
            img.save(ICO_PATH, format='ICO', sizes=sizes)
            print(f'  OK: {ICO_PATH} ({img.size[0]}x{img.size[1]})')
        except ImportError:
            print('  Installing Pillow...')
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'Pillow', '--quiet'])
            try:
                from PIL import Image
                img = Image.open(LOGO_PNG)
                sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
                img.save(ICO_PATH, format='ICO', sizes=sizes)
                print(f'  OK: {ICO_PATH}')
            except Exception as e:
                print(f'  WARNING: convert failed ({e}), building without icon')
        except Exception as e:
            print(f'  WARNING: convert failed ({e}), building without icon')
    else:
        print(f'  WARNING: logo not found at {LOGO_PNG}')

    # Step 3: Install deps
    print('\n[3/6] Installing PyInstaller + Flask + waitress...')
    if not run(f'"{sys.executable}" -m pip install pyinstaller flask waitress --quiet', 'pip install'):
        print('  WARNING: install may have failed, continuing...')

    # Step 4: Clean
    print('\n[4/6] Cleaning old build...')
    for d in [DIST, BUILD]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)
    print('  OK')

    # Step 5: Build EXE
    icon_arg = f'--icon="{ICO_PATH}"' if os.path.exists(ICO_PATH) else ''
    print('\n[5/6] Building EXE (1-2 min)...')
    cmd = (
        f'"{sys.executable}" -m PyInstaller '
        f'--onefile --noconsole --name="MedRecLedger" '
        f'{icon_arg} '
        f'--add-data "static{os.pathsep}static" '
        f'--add-data "config.json{os.pathsep}." '
        f'--hidden-import=flask '
        f'--hidden-import=waitress '
        f'--hidden-import=webbrowser '
        f'--collect-all=flask '
        f'台账服务器.py'
    )
    print(f'  Command: {" ".join(cmd.split()[4:8])}...')
    if not run(cmd, 'PyInstaller'):
        print('\n  ERROR: Build failed')
        return

    # Step 6: Copy data
    print('\n[6/6] Copying data files...')
    data_dir = os.path.join(DIST, '病历数据')
    for sub in ['XPS源文件', '已提取文本', 'AI分析结果']:
        os.makedirs(os.path.join(data_dir, sub), exist_ok=True)

    # 从 training-map 复制已有数据
    if os.path.exists(TRAINING_MAP):
        tm_data = os.path.join(TRAINING_MAP)
        # XPS from ward dirs
        for ward in ['A组', 'C组', 'D组']:
            src = os.path.join(tm_data, ward)
            dst = os.path.join(data_dir, 'XPS源文件')
            if os.path.exists(src):
                for f in os.listdir(src):
                    if f.endswith('.xps'):
                        shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
        # TXT
        src = os.path.join(tm_data, '_extracted')
        dst = os.path.join(data_dir, '已提取文本')
        if os.path.exists(src):
            for f in os.listdir(src):
                if f.endswith('.txt'):
                    shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
        # JSON
        src = os.path.join(tm_data, '_analysis')
        dst = os.path.join(data_dir, 'AI分析结果')
        if os.path.exists(src):
            for f in os.listdir(src):
                if f.endswith('.json'):
                    shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
        print(f'  OK: Copied from training-map')
    else:
        print(f'  WARNING: training-map not found, data dir empty')

    # Copy config
    config_src = os.path.join(BASE, 'config.json')
    if os.path.exists(config_src):
        shutil.copy2(config_src, os.path.join(DIST, 'config.json'))

    # Rename
    exe_src = os.path.join(DIST, 'MedRecLedger.exe')
    exe_dst = os.path.join(DIST, '病历质控台账生成器.exe')
    if os.path.exists(exe_src):
        if os.path.exists(exe_dst):
            os.remove(exe_dst)
        os.rename(exe_src, exe_dst)

    print('\n' + '=' * 55)
    print('  BUILD SUCCESS!')
    print(f'  Output: {exe_dst}')
    print()
    print('  To use:')
    print('  1. Open dist folder')
    print('  2. Double-click EXE')
    print('  3. Browser: http://localhost:8081')
    print('  4. Enter DeepSeek API Key in toolbar')
    print('=' * 55)

if __name__ == '__main__':
    main()
    input('\nPress Enter to exit...')
