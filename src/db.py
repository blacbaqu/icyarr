# db.py
import sqlite3
from typing import List, Dict, Any

DB_PATH = "channel.db"


# ------------------------------------------------------------
# Get DB connection
# ------------------------------------------------------------
def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# ------------------------------------------------------------
# Initialize database + table
# ------------------------------------------------------------
def init_db():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            url TEXT PRIMARY KEY,
            name TEXT,
            group_title TEXT,
            tvg_id TEXT,
            tvg_name TEXT,
            icy_title TEXT,
            bitrate INTEGER
        )
    """)

    db.commit()


# ------------------------------------------------------------
# Load all channels from DB into Python list
# ------------------------------------------------------------
def load_channels() -> List[Dict[str, Any]]:
    db = get_db()
    cur = db.cursor()

    rows = cur.execute("SELECT * FROM channels").fetchall()
    channels = []

    for r in rows:
        channels.append({
            "url": r[0],
            "name": r[1],
            "group": r[2],
            "tvg_id": r[3],
            "tvg_name": r[4],
            "icy_title": r[5],
            "bitrate": r[6],
        })

    return channels


# ------------------------------------------------------------
# Save or update a channel
# ------------------------------------------------------------
def save_channel(ch: Dict[str, Any]):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO channels (url, name, group_title, tvg_id, tvg_name, icy_title, bitrate)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            name=excluded.name,
            group_title=excluded.group_title,
            tvg_id=excluded.tvg_id,
            tvg_name=excluded.tvg_name,
            icy_title=excluded.icy_title,
            bitrate=excluded.bitrate
    """, (
        ch.get("url"),
        ch.get("name"),
        ch.get("group"),
        ch.get("tvg_id"),
        ch.get("tvg_name"),
        ch.get("icy_title"),
        ch.get("bitrate"),
    ))

    db.commit()


# ------------------------------------------------------------
# Delete a channel
# ------------------------------------------------------------
def delete_channel(url: str):
    db = get_db()
    cur = db.cursor()

    cur.execute("DELETE FROM channels WHERE url = ?", (url,))
    db.commit()
