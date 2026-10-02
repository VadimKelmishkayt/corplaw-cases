# Картотека корпоративных кейсов — Telegram Mini App

1379 разборов из канала [@corplawpro](https://t.me/corplawpro): фабула, вывод суда округа,
реквизиты акта и ссылка на исходный пост. Поиск понимает словоформы и целые фразы
(«директор продал участок дешевле рыночной цены»), есть фильтры по 208 темам.

```
index.html   мини-приложение (самодостаточная страница)
cases.json   данные, 1379 записей (1,6 МБ; ~320 КБ в gzip)
bot.py       бот: поиск текстом + inline-режим (нужен, только если хочется их)
```

Адрес мини-приложения: **https://vadimkelmishkayt.github.io/corplaw-cases/**

## 1. Выложить страницу на HTTPS

Мини-приложение — это обычная статика, серверной части у неё нет. Подойдёт любой
HTTPS-хостинг; самый короткий путь — GitHub Pages:

```bash
git init && git add . && git commit -m "mini app"
git branch -M main
git remote add origin git@github.com:<аккаунт>/corplaw-cases.git
git push -u origin main
```

В настройках репозитория: **Settings → Pages → Source: Deploy from a branch →
main / root**. Через минуту страница будет по адресу
`https://vadimkelmishkayt.github.io/corplaw-cases/`.

Важно: на бесплатном тарифе Pages работает только из публичного репозитория —
картотека станет общедоступной. Содержимое взято из открытого канала, но решение
за вами; если нужно закрыто — Cloudflare Pages, Vercel или свой сервер с
Basic-авторизацией.

## 2. Создать бота и привязать мини-приложение

В [@BotFather](https://t.me/BotFather):

1. `/newbot` → имя и username → сохраните токен.
2. `/mybots` → ваш бот → **Bot Settings → Menu Button → Edit menu button URL** →
   вставьте адрес из шага 1 → подпись кнопки, например «Картотека».

Этого достаточно: у бота появится кнопка меню, открывающая картотеку внутри
Telegram. Никакого сервера держать не нужно.

Дополнительно, если хотите открывать её из любого чата: `/setinline` →
подсказка «опишите ситуацию», и `/setinlinefeedback` → Enabled.

## 3. Бот с поиском текстом (необязательно)

```bash
pip install aiogram
export BOT_TOKEN=123456:AA...
export WEBAPP_URL=https://vadimkelmishkayt.github.io/corplaw-cases/
python bot.py
```

Тогда бот отвечает на сообщения вроде «участника не пускают на собрание» пятью
подходящими кейсами и работает в inline-режиме. Для этого нужен постоянно
запущенный процесс — VPS, Railway, Render или systemd-сервис; GitHub Actions для
long-polling не подходит.

## Как обновлять картотеку

Данные собираются из постов канала в `cases.jsonl` (одна запись на строку),
`python3 build.py` пересобирает из них `cases_min.json` и страницу-артефакт.
После пополнения достаточно скопировать `cases_min.json` в `cases.json`
и запушить — мини-приложение подхватит новые кейсы само.
