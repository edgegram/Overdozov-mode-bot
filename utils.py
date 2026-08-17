# -*- coding: utf-8 -*-
"""Вспомогательные функции: анимация текста и приблизительная дата регистрации по ID."""

from datetime import date, timedelta

# Telegram Bot API НЕ отдаёт точную дату создания аккаунта.
# Это грубая интерполяция по известным контрольным точкам ID -> примерная дата
# (собрана по открытым данным сторонних сервисов оценки возраста аккаунта).
# Точность не гарантируется, особенно для очень старых/новых ID.
ID_DATE_TABLE = [
    (100_000_000, date(2013, 8, 1)),
    (200_000_000, date(2014, 8, 1)),
    (300_000_000, date(2016, 3, 1)),
    (400_000_000, date(2017, 3, 1)),
    (500_000_000, date(2017, 11, 1)),
    (600_000_000, date(2018, 6, 1)),
    (700_000_000, date(2018, 11, 1)),
    (800_000_000, date(2019, 4, 1)),
    (900_000_000, date(2019, 8, 1)),
    (1_000_000_000, date(2019, 12, 1)),
    (1_200_000_000, date(2020, 7, 1)),
    (1_400_000_000, date(2021, 2, 1)),
    (1_600_000_000, date(2021, 8, 1)),
    (1_800_000_000, date(2022, 1, 1)),
    (2_000_000_000, date(2022, 6, 1)),
    (5_000_000_000, date(2023, 8, 1)),
    (6_500_000_000, date(2024, 6, 1)),
    (7_500_000_000, date(2025, 6, 1)),
]


def estimate_creation_date(user_id: int) -> str:
    """Возвращает приблизительную дату регистрации в формате ММ.ГГГГ."""
    if user_id <= ID_DATE_TABLE[0][0]:
        return f"раньше {ID_DATE_TABLE[0][1].strftime('%m.%Y')} (примерно)"

    for (id1, d1), (id2, d2) in zip(ID_DATE_TABLE, ID_DATE_TABLE[1:]):
        if id1 <= user_id <= id2:
            ratio = (user_id - id1) / (id2 - id1)
            days = (d2 - d1).days
            approx = d1 + timedelta(days=days * ratio)
            return f"~{approx.strftime('%m.%Y')} (примерно)"

    last_id, last_date = ID_DATE_TABLE[-1]
    return f"позже {last_date.strftime('%m.%Y')} (примерно, вне таблицы)"


def build_animation_frames(text: str, max_steps: int = 40) -> list:
    """Разбивает текст на кадры для плавного 'проявления' по буквам."""
    step = max(1, len(text) // max_steps)
    frames = [text[: i + step] for i in range(0, len(text), step)]
    if frames and frames[-1] != text:
        frames.append(text)
    return frames or [text]
