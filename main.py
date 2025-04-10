import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from openai import OpenAI
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp

# Вставьте свои ключи здесь напрямую
BOT_TOKEN = "7847598451:AAH8B9-S2QPOznckDlKJZSoSpDs1SLphQ34"
OPENROUTER_API_KEY = "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"
TMDB_API_KEY = "941d2663b8c7da9e88d80d9ac8e48105"

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация клиента OpenRouter
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Инициализация Telegram-бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# Простая база пользователей и их языков
user_ids = set()
user_language = {}

# Клавиатура главного меню
main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🎬 Фильм дня")],
    [KeyboardButton(text="📚 Жанры"), KeyboardButton(text="💡 Подсказки")],
    [KeyboardButton(text="⚙️ Настройки")]
], resize_keyboard=True)

# Inline-кнопки для жанров
genres_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎭 Драма", callback_data="genre_драма"),
     InlineKeyboardButton(text="😂 Комедия", callback_data="genre_комедия")],
    [InlineKeyboardButton(text="🎢 Триллер", callback_data="genre_триллер"),
     InlineKeyboardButton(text="💥 Боевик", callback_data="genre_боевик")],
    [InlineKeyboardButton(text="💘 Романтика", callback_data="genre_романтика"),
     InlineKeyboardButton(text="🎥 Аниме", callback_data="genre_аниме")]
])

# Функция получения рекомендаций от OpenRouter (GPT)
async def get_movie_recommendation(query: str):
    prompt = f"""
    Ты — эксперт по фильмам, сериалам и аниме. Пользователь пишет: '{query}'.
    Подбери актуальный фильм, сериал или аниме по запросу пользователя и интересные тайтлы с краткими описаниями. Формат:
    1. НАЗВАНИЕ (год) - Краткое описание.
    """
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return f"😔 Произошла ошибка: {e}"

# Получение фильма дня с TMDB
async def get_tmdb_trending_movie():
    url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={TMDB_API_KEY}&language=ru-RU"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            if data.get("results"):
                movie = data["results"][0]
                title = movie.get("title", "Без названия")
                overview = movie.get("overview", "Описание отсутствует.")
                return f"🎬 {title}\n\n{overview}"
            return "😔 Не удалось получить фильм дня."

# Команда /start
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_ids.add(message.from_user.id)
    user_language[message.from_user.id] = "ru"
    await message.answer(
        "👋 Привет! Я ScreenFox — подбираю фильмы, сериалы и аниме. Просто напиши тему или жанр или выбери из меню:",
        reply_markup=main_kb
    )

# Фильм дня
@dp.message(F.text.lower() == "🎬 фильм дня")
async def movie_of_the_day(message: types.Message):
    await message.answer("🎬 Выбираю фильм дня...")
    result = await get_tmdb_trending_movie()
    await message.answer(f"🍿 Фильм дня:\n\n{result}")

# Подсказки
@dp.message(F.text.lower() == "💡 подсказки")
async def tips_handler(message: types.Message):
    await message.answer("💡 Примеры запросов:\n- триллер с неожиданной концовкой\n- комедия 2020-х годов\n- сериал как Во все тяжкие\n- романтическое аниме")

# Жанры
@dp.message(F.text.lower() == "📚 жанры")
async def genre_menu(message: types.Message):
    await message.answer("📚 Выбери жанр, и я подберу что-то интересное:", reply_markup=genres_kb)

# Inline callback по жанрам
@dp.callback_query()
async def genre_callback(callback: types.CallbackQuery):
    genre = callback.data.replace("genre_", "")
    await callback.message.answer(f"🔍 Ищу что-то в жанре: {genre}...")
    result = await get_movie_recommendation(f"Фильмы в жанре {genre}")
    await callback.message.answer(result)
    await callback.answer()

# Настройки
@dp.message(F.text.lower() == "⚙️ настройки")
async def settings_handler(message: types.Message):
    await message.answer("⚙️ Настройки будут доступны позже. Сейчас доступна только локализация на русский язык. Чтобы отключить \"Фильм дня\" — напиши 'отписаться'.")

# Обычный текст
@dp.message(F.text)
async def query_handler(message: types.Message):
    user_ids.add(message.from_user.id)
    await message.answer("🔎 Ищу подборку...")
    result = await get_movie_recommendation(message.text)
    await message.answer(f"📽 Рекомендации:\n\n{result}")

# Рассылка фильма дня
async def send_daily_recommendation():
    if user_ids:
        text = await get_tmdb_trending_movie()
        for uid in user_ids:
            try:
                await bot.send_message(uid,f"🌅 Доброе утро! Вот фильм дня от ScreenFox:\n\n{text}")
            except Exception as e:
                logging.warning(f"Не удалось отправить сообщение {uid}: {e}")

# Запуск
async def main():
    scheduler.add_job(send_daily_recommendation, trigger='cron', hour=9, minute=0)
    scheduler.start()
    print("✅ ScreenFox запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
