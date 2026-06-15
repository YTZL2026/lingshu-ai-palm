"""Edge-TTS 诊断脚本 — 双击运行或 python check_tts.py"""
import sys, os

print("=" * 50)
print("  Edge-TTS Diagnostic")
print("=" * 50)

# 1. 检查 edge-tts 是否安装
print("\n[1] Checking edge-tts installation...")
try:
    import edge_tts
    ver = getattr(edge_tts, '__version__', 'unknown')
    print(f"    [OK] edge-tts installed (version: {ver})")
except ImportError:
    print("    [FAIL] edge-tts NOT installed!")
    print("    Run: pip install edge-tts")
    print("\nPress Enter to exit...")
    input()
    sys.exit(1)

# 2. 测试 TTS 生成
print("\n[2] Testing TTS generation...")
try:
    import asyncio, tempfile

    async def test():
        text = "你好，我是灵枢，语音测试成功。"
        communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            path = f.name
        await communicate.save(path)
        size = os.path.getsize(path)
        os.unlink(path)
        print(f"    [OK] Generated {size} bytes — voice sounds natural!")
        return True

    ok = asyncio.run(test())
    if not ok:
        print("    [FAIL] Unknown error")
except Exception as e:
    print(f"    [FAIL] {e}")

# 3. 检查服务是否运行
print("\n[3] Checking if server is running...")
try:
    import urllib.request
    resp = urllib.request.urlopen("http://127.0.0.1:8080/api/constitution_types", timeout=3)
    print("    [OK] Server running on http://127.0.0.1:8080")
except:
    print("    [WARN] Server not running!")
    print("    Start serve.bat first, then re-run this test.")

print("\n" + "=" * 50)
print("  Done. If all [OK], TTS is ready.")
print("=" * 50)
print("\nPress Enter to exit...")
input()
