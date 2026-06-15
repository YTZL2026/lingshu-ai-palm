# -*- coding: utf-8 -*-
"""Download MediaPipe HandLandmarker model file"""
import os, urllib.request, sys

MODEL_DIR = os.path.join(os.path.expanduser('~'), '.mediapipe_models')
MODEL_PATH = os.path.join(MODEL_DIR, 'hand_landmarker.task')

if os.path.exists(MODEL_PATH):
    print(f'✅ Model already exists: {MODEL_PATH}')
    print(f'   Size: {os.path.getsize(MODEL_PATH)/1024/1024:.1f} MB')
    sys.exit(0)

os.makedirs(MODEL_DIR, exist_ok=True)

# Try Google storage first, then fallback to alternative
URLS = [
    'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task',
    'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.18/wasm/hand_landmarker.task',
]

for i, url in enumerate(URLS):
    print(f'[{i+1}/{len(URLS)}] Downloading from: {url}')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        with open(MODEL_PATH, 'wb') as f:
            f.write(data)
        print(f'✅ Downloaded! Size: {len(data)/1024/1024:.1f} MB')
        print(f'   Saved to: {MODEL_PATH}')
        sys.exit(0)
    except Exception as e:
        print(f'   Failed: {e}')

print('\n❌ All URLs failed. Manually download from:')
print('   https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task')
print(f'   Save to: {MODEL_PATH}')
