# -*- coding: utf-8 -*-
"""
Простая обёртка над SQLite для хранения замьюченных пользователей.
Файл базы создаётся автоматически при первом запуске.
"""

import sqlite3
from contextlib import closing

from config import DB_PATH


def init_db() -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS muted_users (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                PRIMARY KEY (chat_id, user_id)
            )
            """
        )
        conn.commit()


def mute_user(chat_id: int, user_id: int) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO muted_users (chat_id, user_id) VALUES (?, ?)",
            (chat_id, user_id),
        )
        conn.commit()


def unmute_user(chat_id: int, user_id: int) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "DELETE FROM muted_users WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id),
        )
        conn.commit()


def is_muted(chat_id: int, user_id: int) -> bool:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.execute(
            "SELECT 1 FROM muted_users WHERE chat_id = ? AND user_id = ? LIMIT 1",
            (chat_id, user_id),
        )
        return cur.fetchone() is not None


def list_muted(chat_id: int) -> list:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.execute(
            "SELECT user_id FROM muted_users WHERE chat_id = ?", (chat_id,)
        )
        return [row[0] for row in cur.fetchall()]
