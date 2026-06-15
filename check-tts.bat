@echo off
title Edge-TTS Diagnostic
echo ========================================
echo   Edge-TTS Diagnostic
echo ========================================
echo.

echo [1] Check edge-tts installation...
python -c "import edge_tts; print('edge-tts version:', edge_tts.__version__)" 2>&1
if errorlevel 1 (
    echo [FAIL] edge-tts NOT installed!
    echo Run: pip install edge-tts
) else (
    echo [OK] edge-tts installed
)

echo.
echo [2] Test TTS generation (quick)...
python -c "
import asyncio, edge_tts, tempfile, os
async def test():
    try:
        communicate = edge_tts.Communicate('你好，我是灵枢，测试语音。', 'zh-CN-XiaoxiaoNeural')
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            path = f.name
        await communicate.save(path)
        size = os.path.getsize(path)
        os.unlink(path)
        print(f'[OK] TTS generated successfully ({size} bytes)')
    except Exception as e:
        print(f'[FAIL] {e}')
asyncio.run(test())
" 2>&1

echo.
echo [3] Check if server is running...
python -c "
import urllib.request
try:
    resp = urllib.request.urlopen('http://127.0.0.1:8080/api/constitution_types', timeout=3)
    print('[OK] Server is running on port 8080')
except:
    print('[WARN] Server not detected on port 8080')
    print('       Please start serve.bat first, then re-run this test')
" 2>&1

echo.
echo ========================================
echo   If [OK] for all three, TTS is ready.
echo   If any [FAIL], fix that item.
echo ========================================
pause
