from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import DATA_DIR

DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DATA_DIR}/survey.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _migrate_db()


def _migrate_db():
    """在每次啟動時自動偵測並補全缺少的欄位，確保存量資料庫相容新版 schema。"""
    import sqlite3
    from app.config import DATA_DIR
    db_path = DATA_DIR / "survey.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(datasets)")
    columns = [row[1] for row in cursor.fetchall()]
    if "form_id" not in columns:
        cursor.execute("ALTER TABLE datasets ADD COLUMN form_id TEXT")
        conn.commit()
    conn.close()
