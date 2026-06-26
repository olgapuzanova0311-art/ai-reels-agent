# 🤖 AI Reels Agent — БЕСПЛАТНАЯ версия

Парсит YouTube Shorts про ИИ, транскрибирует и присылает адаптированный сценарий в Telegram.
**Стоимость: $0/мес**

---

## Что использует и почему бесплатно

| Компонент | Сервис | Почему бесплатно |
|-----------|--------|-----------------|
| Парсинг | yt-dlp | Open source, без API |
| Транскрипция | faster-whisper (tiny) | Локально на CPU |
| Адаптация | Groq API (llama-3.3-70b) | 14 400 запросов/день бесплатно |
| Отправка | Telegram Bot API | Бесплатно |
| Хостинг | Railway | 500 часов/мес бесплатно |

---

## Установка за 15 минут

### Шаг 1 — Telegram бот

1. Открой Telegram, найди @BotFather
2. Напиши `/newbot`, дай имя, получи токен вида `1234567890:ABCdef...`
3. Найди @userinfobot, напиши ему — получишь свой `id` (числo)

### Шаг 2 — Groq API (бесплатно)

1. Зайди на **console.groq.com**
2. Зарегистрируйся (можно через Google)
3. API Keys → Create API Key
4. Скопируй ключ вида `gsk_...`

### Шаг 3 — Railway

1. Зайди на **railway.app** → Sign Up (через GitHub)
2. New Project → Deploy from GitHub repo
3. Залей этот код в свой GitHub репозиторий
4. Подключи репозиторий в Railway

### Шаг 4 — Переменные окружения в Railway

В Railway → твой проект → Variables, добавь:

```
TELEGRAM_BOT_TOKEN = 1234567890:ABCdef...
TELEGRAM_CHAT_ID   = 123456789
GROQ_API_KEY       = gsk_...
```

Опционально (есть дефолты):
```
MIN_VIEWS           = 10000
MAX_AGE_HOURS       = 24
VIDEOS_PER_RUN      = 30
PARSE_INTERVAL_HOURS = 6
SEARCH_KEYWORDS     = нейросети,ChatGPT,ИИ,AI,midjourney,llm,claude ai
```

### Шаг 5 — Deploy

Railway сам задеплоит. Через 2-3 минуты придёт первое сообщение в Telegram.

---

## Что приходит в Telegram

**Сообщение 1 — карточка:**
```
▶️ YouTube Shorts | 45 231 просмотров
👤 TechChannel
🔗 https://youtube.com/shorts/...

🎯 Как написать ТЗ за 5 минут с ChatGPT

⚡️ ХУК: Ты тратишь 2 часа на ТЗ. Я — 5 минут

Оценка: 🔥🔥🔥 8/10
```

**Сообщение 2 — готовый сценарий** под твой голос

**Сообщение 3 — оригинальная транскрипция** для сравнения

После каждой сессии — краткая сводка.

---

## Ограничения бесплатной версии

- Только YouTube Shorts (TikTok/Instagram — только платно)
- ~30 роликов за запуск (Railway RAM лимит)
- Whisper `tiny` — иногда ошибается на сложных акцентах
- Groq лимит: 14 400 запросов/день (хватит с запасом)

---

## Структура

```
ai-reels-agent-free/
├── main.py          # Планировщик
├── agent.py         # Оркестратор
├── core/
│   ├── youtube_parser.py  # Парсинг YouTube
│   ├── transcriber.py     # Whisper транскрипция
│   └── adapter.py         # Groq адаптация
├── bot/
│   └── sender.py    # Telegram
├── Dockerfile
└── railway.toml
```
