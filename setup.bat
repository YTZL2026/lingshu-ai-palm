@echo off
chcp 65001 >nul
echo ============================================
echo   灵枢 LingShu — 一键部署脚本
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

:: Create venv
if not exist "venv\" (
    echo [1/3] 创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
) else (
    echo [1/3] 虚拟环境已存在，跳过
)

:: Activate and install
echo [2/3] 安装依赖...
call venv\Scripts\activate.bat
pip install --upgrade pip -q
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo [警告] 清华镜像失败，尝试官方源...
    pip install -r requirements.txt
)

:: Install edge-tts separately
pip install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple 2>nul
if %errorlevel% neq 0 (
    pip install edge-tts
)

echo.
echo [3/3] 依赖安装完成
echo.

:: Generate SSL cert
echo 正在生成 SSL 证书...
python -c "from cryptography import x509; from cryptography.x509.oid import NameOID; from cryptography.hazmat.primitives import hashes; from cryptography.hazmat.primitives.asymmetric import rsa; from cryptography.hazmat.backends import default_backend; from cryptography.hazmat.primitives import serialization; import datetime, ipaddress, socket, os; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); ip=s.getsockname()[0]; s.close(); key=rsa.generate_private_key(65537,2048,default_backend()); subj=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'localhost')]); cert=x509.CertificateBuilder().subject_name(subj).issuer_name(subj).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(datetime.datetime.now(datetime.UTC)).not_valid_after(datetime.datetime.now(datetime.UTC)+datetime.timedelta(days=365)).add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost'),x509.IPAddress(ipaddress.IPv4Address('127.0.0.1')),x509.IPAddress(ipaddress.IPv4Address(ip))]),critical=False).sign(key,hashes.SHA256(),default_backend()); os.makedirs('ssl',exist_ok=True); open('ssl/key.pem','wb').write(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())); open('ssl/cert.pem','wb').write(cert.public_bytes(serialization.Encoding.PEM)); print(f'SSL证书已生成  当前IP: {ip}')" 2>nul
if %errorlevel% neq 0 (
    echo [警告] SSL 证书自动生成失败，请手动运行生成脚本
)

echo.
echo ============================================
echo   部署完成！
echo.
echo   下一步：
echo   1. 编辑 config.json 填入 DeepSeek API Key
echo   2. 运行 python main.py 启动服务
echo   3. 手机浏览器打开 https://你的IP:8080
echo ============================================
echo.
echo   详细说明见「项目迁移说明.md」
echo.
pause
