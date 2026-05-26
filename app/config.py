import os
import json
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "app" / "static" / "uploads"
CERT_DIR = BASE_DIR / "cert"
CONFIG_FILE = DATA_DIR / "config.json"

SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8

ADMIN_USERNAME = "admin"


def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_admin_password() -> str:
    cfg = load_config()
    return cfg.get("admin_password", "")


def init_admin_password() -> str:
    cfg = load_config()
    if "admin_password" not in cfg:
        password = secrets.token_urlsafe(12)
        cfg["admin_password"] = password
        save_config(cfg)
        return password
    return cfg["admin_password"]


def get_secret_key() -> str:
    cfg = load_config()
    if "secret_key" not in cfg:
        key = secrets.token_hex(32)
        cfg["secret_key"] = key
        save_config(cfg)
        return key
    return cfg["secret_key"]
