# -*- coding: utf-8 -*-
"""
Точка входа. Запуск: python bot.py
Требует .env с BOT_TOKEN (см. .env.example).
"""

import logging

from telegram import Update
from telegram.ext import Application, MessageHandler, filters

import database as db
from config import BOT_TOKEN
from handlers import dispatch

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("dotbot")


def main() -> None:
    db.init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    # Обычные сообщения (личка/группы) + сообщения из Telegram Business
    app.add_handler(
        MessageHandler(
            filters.UpdateType.MESSAGES | filters.UpdateType.BUSINESS_MESSAGES,
            dispatch,
        )
    )

    log.info("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
