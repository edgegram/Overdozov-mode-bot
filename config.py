# -*- coding: utf-8 -*-
"""Загрузка настроек из .env"""

import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_PATH = os.getenv("DB_PATH", "bot.db")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", ".")

if not BOT_TOKEN:
    raise SystemExit(
        "BOT_TOKEN не задан. Скопируй .env.example в .env и впиши токен от @BotFather."
    )
