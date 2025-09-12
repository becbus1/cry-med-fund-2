from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from .config import Config

def _make_engine():
    url = Config.DATABASE_URL
    if url:
        return create_engine(url, pool_pre_ping=True, future=True)
    # SQLite fallback (for local dev)
    return create_engine("sqlite+pysqlite:///./paper.db", future=True)

ENGINE = _make_engine()
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False, future=True)

def init_db():
    with ENGINE.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER,
                px REAL,
                qty REAL
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER,
                side TEXT,
                px REAL,
                qty REAL,
                status TEXT
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                ts INTEGER,
                px REAL,
                qty REAL
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pnl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER,
                realized REAL,
                unrealized REAL
            );
        """))
