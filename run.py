#!/usr/bin/env python3
"""
問卷填答與即時統計分析平台 — 一鍵啟動腳本

使用方式：
  Mac/Linux:  sudo python run.py
  Windows:    以系統管理員身份執行 -> python run.py

Port 443 需要管理者/root 權限。
若不想用 sudo，可改為其他 port，例如：python run.py --port 8501
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).parent
CERT_DIR = BASE_DIR / "cert"
DATA_DIR = BASE_DIR / "data"
REQ_FILE = BASE_DIR / "requirements.txt"


def print_banner():
    print("\n" + "="*55)
    print("  問卷填答與即時統計分析平台")
    print("  Survey Analysis Platform")
    print("="*55)


def check_python():
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 8):
        print(f"[錯誤] 需要 Python 3.8 以上，目前版本：{major}.{minor}")
        sys.exit(1)
    print(f"[OK] Python {major}.{minor}")


def install_requirements():
    print("\n[1/4] 安裝套件依賴...")
    if not REQ_FILE.exists():
        print("  找不到 requirements.txt，跳過")
        return
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(REQ_FILE), "-q"],
            stdout=subprocess.DEVNULL,
        )
        print("  [OK] 套件安裝完成")
    except subprocess.CalledProcessError as e:
        print(f"  [警告] 安裝部分套件失敗：{e}")
        print("  請手動執行：pip install -r requirements.txt")


def generate_ssl_cert():
    print("\n[2/4] 檢查 SSL 憑證...")
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    cert_file = CERT_DIR / "cert.pem"
    key_file = CERT_DIR / "key.pem"

    if cert_file.exists() and key_file.exists():
        print("  [OK] 已有 SSL 憑證")
        return

    print("  生成自簽 SSL 憑證...")
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from datetime import datetime, timedelta
        import ipaddress

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "TW"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Survey Platform"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=3650))
            .add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                ]),
                critical=False,
            )
            .sign(key, hashes.SHA256())
        )

        with open(key_file, "wb") as f:
            f.write(key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            ))
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        print("  [OK] SSL 憑證生成完成（有效期 10 年）")
    except ImportError:
        print("  [警告] cryptography 套件未安裝，嘗試用 openssl 指令...")
        try:
            subprocess.check_call([
                "openssl", "req", "-x509", "-newkey", "rsa:2048",
                "-keyout", str(key_file), "-out", str(cert_file),
                "-days", "3650", "-nodes",
                "-subj", "/CN=localhost",
            ], stderr=subprocess.DEVNULL)
            print("  [OK] SSL 憑證生成完成")
        except Exception:
            print("  [錯誤] 無法生成 SSL 憑證，請手動安裝 cryptography 套件")
            sys.exit(1)


def init_database_and_config():
    print("\n[3/4] 初始化資料庫與設定...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(BASE_DIR))
    from app.config import init_admin_password, get_secret_key, ADMIN_USERNAME

    password = init_admin_password()
    _ = get_secret_key()

    # 確保資料庫表格存在（避免 DB 空白導致功能異常）
    from app.database import init_db
    init_db()

    print(f"  [OK] 資料庫就緒")
    print(f"\n  ┌─────────────────────────────────┐")
    print(f"  │  管理者帳號：{ADMIN_USERNAME:<20} │")
    print(f"  │  管理者密碼：{password:<20} │")
    print(f"  └─────────────────────────────────┘")
    print(f"  (密碼儲存於 data/config.json，可自行修改)")
    return password


def check_port_permission(port: int):
    if port < 1024:
        if sys.platform != "win32" and os.geteuid() != 0:
            print(f"\n[警告] Port {port} 需要 root 權限！")
            print("  請使用：sudo python run.py")
            print(f"  或使用高 port：python run.py --port 8501")
            if input("  繼續嘗試啟動？(y/N): ").strip().lower() != "y":
                sys.exit(0)


def get_public_ip():
    import urllib.request
    for url in [
        "http://api.ipify.org",
        "http://ifconfig.me/ip",
        "http://ipecho.net/plain",
    ]:
        try:
            return urllib.request.urlopen(url, timeout=4).read().decode().strip()
        except Exception:
            continue
    return None


def get_local_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def start_server(port: int, host: str):
    print(f"\n[4/4] 啟動伺服器...")
    local_ip = get_local_ip()
    public_ip = get_public_ip()

    print(f"\n  ╔══════════════════════════════════════════════╗")
    print(f"  ║  平台已啟動！（HTTP 模式）                     ║")
    print(f"  ║  本機：  http://localhost:{port}                    ║")
    print(f"  ║  區網：  http://{local_ip}:{port}             ║")
    if public_ip:
        print(f"  ║  外網：  http://{public_ip}:{port}            ║")
    print(f"  ║  按 Ctrl+C 停止服務                           ║")
    print(f"  ╚══════════════════════════════════════════════╝\n")

    try:
        import uvicorn
        uvicorn.run("app.main:app", host=host, port=port, reload=False, log_level="info")
    except ImportError:
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "app.main:app",
             "--host", host, "--port", str(port)],
            cwd=str(BASE_DIR)
        )


def main():
    parser = argparse.ArgumentParser(description="問卷分析平台啟動器")
    parser.add_argument("--port", type=int, default=8501, help="監聽 port（預設 8501）")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="監聽 host（預設 0.0.0.0）")
    parser.add_argument("--skip-install", action="store_true", help="跳過套件安裝")
    args = parser.parse_args()

    print_banner()
    check_python()
    if not args.skip_install:
        install_requirements()
    init_database_and_config()
    start_server(args.port, args.host)


if __name__ == "__main__":
    main()
