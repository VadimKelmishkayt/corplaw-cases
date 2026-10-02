"""
Телеграм-бот «Картотека корпоративных кейсов».

Что умеет:
  • /start — кнопка, открывающая мини-приложение;
  • обычное сообщение — ищет по картотеке и присылает 5 лучших кейсов ссылками;
  • inline-режим (@ваш_бот запрос в любом чате) — выдаёт кейсы прямо в переписку.

Запуск:
    pip install aiogram
    export BOT_TOKEN=...        # токен от @BotFather
    export WEBAPP_URL=https://<ваш-аккаунт>.github.io/<репозиторий>/
    python bot.py

Боту для мини-приложения сервер не обязателен: кнопку меню можно задать прямо
в @BotFather (Bot Settings → Menu Button → ссылка на WEBAPP_URL). Этот скрипт
нужен, только если хочется ещё и поиск текстом и inline-режим.
"""
import asyncio
import html
import json
import os
import re
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, InlineQuery,
    InlineQueryResultArticle, InputTextMessageContent, Message, WebAppInfo,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBAPP_URL = os.environ.get("WEBAPP_URL", "")
CHANNEL = "corplawpro"
DATA = json.loads((Path(__file__).parent / "cases.json").read_text("utf-8"))

WORD_RE = re.compile(r"[^0-9a-zа-я/\-]+")
ENDINGS = re.compile(
    r"(ами|ями|ость|ение|ений|ого|ему|ыми|ими|ах|ях|ов|ев|ем|ом|ой|ей|ую|юю|ые|ие|ый|ий|ая|яя|ла|ли|ло|ть|ся|а|я|у|ю|е|и|ы|о|ь)$"
)


def norm(s: str) -> str:
    return WORD_RE.sub(" ", (s or "").lower().replace("ё", "е")).strip()


def stem(w: str) -> str:
    return ENDINGS.sub("", w) if len(w) > 5 else w


for rec in DATA:
    blob = norm(" ".join([
        rec["title"], rec["gist"], " ".join(rec.get("keywords", [])),
        " ".join(rec.get("tags", [])), rec.get("court", ""),
        rec.get("case_no", ""), rec.get("act_date", ""),
    ]))
    rec["_k"] = blob
    rec["_s"] = " ".join(stem(w) for w in blob.split())
    rec["_t"] = norm(rec["title"])


def search(query: str, limit: int = 5) -> list[dict]:
    """Та же логика, что в мини-приложении: ранжирование по покрытию слов запроса."""
    terms = [w for w in norm(query).split() if len(w) > 2]
    if not terms:
        return sorted(DATA, key=lambda r: -r["post"])[:limit]
    need = len(terms) if len(terms) <= 2 else max(2, (len(terms) + 1) // 2)
    scored = []
    for rec in DATA:
        hit = points = 0
        for t in terms:
            st = stem(t)
            if t in rec["_k"]:
                v = 3
            elif len(st) > 2 and st in rec["_s"]:
                v = 2
            else:
                continue
            hit += 1
            points += v + (2 if t in rec["_t"] else 0)
        if hit >= need:
            scored.append((hit * 10 + points, rec["post"], rec))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    return [rec for _, _, rec in scored[:limit]]


def requisites(rec: dict) -> str:
    bits = [rec.get("court", ""), rec.get("case_no", "")]
    if rec.get("act_date"):
        bits.insert(1, ".".join(reversed(rec["act_date"].split("-"))))
    return " · ".join(b for b in bits if b)


def card(rec: dict) -> str:
    head = f'<a href="https://t.me/{CHANNEL}/{rec["post"]}"><b>{html.escape(rec["title"])}</b></a>'
    meta = requisites(rec)
    return f"{head}\n<i>{html.escape(meta)}</i>\n{html.escape(rec['gist'])}" if meta else f"{head}\n{html.escape(rec['gist'])}"


dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message) -> None:
    kb = None
    if WEBAPP_URL:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔎 Открыть картотеку", web_app=WebAppInfo(url=WEBAPP_URL))
        ]])
    await message.answer(
        f"<b>Картотека корпоративных кейсов</b>\n"
        f"{len(DATA)} разборов из канала @{CHANNEL} — с реквизитами актов и выводами судов округов.\n\n"
        "Опишите ситуацию своими словами прямо здесь — пришлю подходящие кейсы. "
        "Или откройте картотеку кнопкой ниже: там поиск и фильтры по темам.",
        reply_markup=kb, disable_web_page_preview=True,
    )


@dp.message(F.text & ~F.text.startswith("/"))
async def by_text(message: Message) -> None:
    hits = search(message.text, limit=5)
    if not hits:
        await message.answer("Ничего не нашлось. Попробуйте короче — «убытки директор», «выход из ООО» — или номер дела.")
        return
    body = "\n\n".join(card(r) for r in hits)
    await message.answer(f"Нашёл {len(hits)}:\n\n{body}", disable_web_page_preview=True)


@dp.inline_query()
async def inline(query: InlineQuery) -> None:
    results = [
        InlineQueryResultArticle(
            id=str(rec["post"]),
            title=rec["title"][:120],
            description=(requisites(rec) + " — " if requisites(rec) else "") + rec["gist"][:160],
            url=f"https://t.me/{CHANNEL}/{rec['post']}",
            input_message_content=InputTextMessageContent(
                message_text=card(rec), parse_mode="HTML", disable_web_page_preview=True
            ),
        )
        for rec in search(query.query, limit=20)
    ]
    await query.answer(results, cache_time=300, is_personal=False)


async def main() -> None:
    bot = Bot(BOT_TOKEN, parse_mode="HTML")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
