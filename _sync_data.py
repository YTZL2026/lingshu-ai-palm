# -*- coding: utf-8 -*-
"""一次性同步脚本：从 training-map 复制三个区样本到 病历数据/"""
import os, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
TRAINING_MAP = os.path.join(BASE, '..', 'training-map', '病历质控测试组')
DATA_DIR = os.path.join(BASE, '病历数据')

# 三个区
WARDS = ['A组', 'C组', 'D组']

# --- XPS ---
xps_dst = os.path.join(DATA_DIR, 'XPS源文件')
os.makedirs(xps_dst, exist_ok=True)
for ward in WARDS:
    src_dir = os.path.join(TRAINING_MAP, ward)
    if os.path.exists(src_dir):
        for f in os.listdir(src_dir):
            if f.endswith('.xps'):
                src = os.path.join(src_dir, f)
                dst = os.path.join(xps_dst, f)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    print(f'XPS copied: {f}')

# --- TXT ---
txt_dst = os.path.join(DATA_DIR, '已提取文本')
os.makedirs(txt_dst, exist_ok=True)
extracted_src = os.path.join(TRAINING_MAP, '_extracted')
if os.path.exists(extracted_src):
    for f in os.listdir(extracted_src):
        if f.endswith('.txt'):
            src = os.path.join(extracted_src, f)
            dst = os.path.join(txt_dst, f)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
                print(f'TXT copied: {f}')

# --- JSON ---
json_dst = os.path.join(DATA_DIR, 'AI分析结果')
os.makedirs(json_dst, exist_ok=True)
analysis_src = os.path.join(TRAINING_MAP, '_analysis')
if os.path.exists(analysis_src):
    for f in os.listdir(analysis_src):
        if f.endswith('.json'):
            src = os.path.join(analysis_src, f)
            dst = os.path.join(json_dst, f)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
                print(f'JSON copied: {f}')

print('\nDone. Check 病历数据/ for all 9 files.')
