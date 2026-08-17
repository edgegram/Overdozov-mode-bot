# -*- coding: utf-8 -*-
"""
Обработчики команд.

Бот понимает команды через точку (.help, .anim и т.д.) в обычных чатах
и в чатах, подключённых через Telegram Business (Premium-функция,
Настройки Telegram -> Telegram для бизнеса -> Чат-боты).

Для business-чатов python-telegram-bot (начиная с версии 21.4) сам
подставляет business_connection_id в reply_text / edit_text / delete,
поэтому весь код команд написан один раз и работает в обоих случаях.
"""

import asyncio
import logging

from telegram import Message, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden, RetryAfter
from telegram.ext import ContextTypes

import database as db
from config import COMMAND_PREFIX
from utils import build_animation_frames, estimate_creation_date

log = logging.getLogger("dotbot.handlers")

HELP_TEXT = (
    "<b>Доступные команды:</b>\n\n"
    "<code>.anim [текст]</code> — плавная анимация появления текста\n"
    "<code>.help</code> — список команд\n"
    "<code>.info</code> — инфо о собеседнике (ID, примерная дата регистрации; "
    "ответом на сообщение — покажет того, кому ответили)\n"
    "<code>.mute</code> — замьютить пользователя (ответом на его сообщение, только в группах, только админам)\n"
    "<code>.unmute</code> — снять мут (ответом на его сообщение)\n\n"
    "<i>Дальше будут обновления!</i>"
)


def get_message(update: Update) -> Message | None:
    """Возвращает сообщение независимо от того, обычное оно или business."""
    return update.effective_message


async def is_admin(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


# ---------- КОМАНДЫ ----------

async def cmd_help(message: Message, context: ContextTypes.DEFAULT_TYPE):
    await message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def cmd_anim(message: Message, context: ContextTypes.DEFAULT_TYPE, arg: str):
    text = arg.strip()
    if not text:
        await message.reply_text(f"Напиши текст: {COMMAND_PREFIX}anim твой текст")
        return

    text = text[:300]  # ограничение, чтобы не словить flood-лимит Telegram
    sent = await message.reply_text("…")
    frames = build_animation_frames(text)

    try:
        for frame in frames:
            try:
                await sent.edit_text(frame)
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after)
                await sent.edit_text(frame)
            except BadRequest as e:
                if "not modified" not in str(e).lower():
                    raise
            await asyncio.sleep(0.25)
    except Exception:
        log.exception("Ошибка анимации")
        await sent.edit_text(text)


async def cmd_info(message: Message, context: ContextTypes.DEFAULT_TYPE):
    reply = message.reply_to_message
    user = reply.from_user if reply else message.from_user

    lines = [
        "<b>Информация о пользователе</b>",
        f"🆔 ID: <code>{user.id}</code>",
        f"👤 Имя: {user.full_name}",
    ]
    if user.username:
        lines.append(f"🔗 Username: @{user.username}")
    lines.append(f"📅 Дата регистрации: {estimate_creation_date(user.id)}")
    lines.append(
        "⚠️ Telegram не отдаёт точную дату регистрации через Bot API — "
        "это приблизительная оценка по номеру ID."
    )
    await message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def cmd_mute(message: Message, context: ContextTypes.DEFAULT_TYPE):
    chat = message.chat
    if chat.type not in ("group", "supergroup"):
        await message.reply_text("Команда работает только в группах.")
        return
    if not await is_admin(context, chat.id, message.from_user.id):
        await message.reply_text("Только администраторы могут использовать эту команду.")
        return
    if not message.reply_to_message:
        await message.reply_text(
            f"Ответь командой {COMMAND_PREFIX}mute на сообщение пользователя, которого нужно замьютить."
        )
        return

    target = message.reply_to_message.from_user
    db.mute_user(chat.id, target.id)
    await message.reply_text(f"🔇 {target.full_name} замьючен. Его новые сообщения будут удаляться.")


async def cmd_unmute(message: Message, context: ContextTypes.DEFAULT_TYPE):
    chat = message.chat
    if chat.type not in ("group", "supergroup"):
        await message.reply_text("Команда работает только в группах.")
        return
    if not await is_admin(context, chat.id, message.from_user.id):
        await message.reply_text("Только администраторы могут использовать эту команду.")
        return
    if not message.reply_to_message:
        await message.reply_text(
            f"Ответь командой {COMMAND_PREFIX}unmute на сообщение пользователя, которого нужно размьютить."
        )
        return

    target = message.reply_to_message.from_user
    db.unmute_user(chat.id, target.id)
    await message.reply_text(f"🔊 {target.full_name} размьючен.")


# ---------- ГЛАВНЫЙ ДИСПЕТЧЕР ----------

COMMANDS = {
    "help": cmd_help,
    "info": cmd_info,
}
COMMANDS_WITH_ARG = {"anim": cmd_anim}
COMMANDS_NO_MESSAGE_ARG = {"mute": cmd_mute, "unmute": cmd_unmute}


async def dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = get_message(update)
    if not message or not message.text or not message.from_user:
        return

    chat_id = message.chat_id
    user_id = message.from_user.id

    # 1. Если пользователь в муте — удаляем сообщение и выходим
    if db.is_muted(chat_id, user_id):
        try:
            await message.delete()
        except (Forbidden, BadRequest):
            log.warning("Нет прав удалить сообщение в чате %s", chat_id)
        return

    # 2. Обработка команд
    text = message.text.strip()
    if not text.startswith(COMMAND_PREFIX):
        return

    parts = text[len(COMMAND_PREFIX):].split(maxsplit=1)
    if not parts:
        return
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd in COMMANDS:
        await COMMANDS[cmd](message, context)
    elif cmd in COMMANDS_WITH_ARG:
        await COMMANDS_WITH_ARG[cmd](message, context, arg)
    elif cmd in COMMANDS_NO_MESSAGE_ARG:
        await COMMANDS_NO_MESSAGE_ARG[cmd](message, context)
    # неизвестные команды молча игнорируем
