import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
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

# Клавиатура
main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🎬 Фильм дня"), KeyboardButton(text="⚙️ Настройки")]
], resize_keyboard=True)

# Функция получения рекомендаций от OpenRouter (GPT)
async def get_movie_recommendation(query: str):
    prompt = f"""
    Ты — эксперт по фильмам, сериалам и аниме. Пользователь пишет: '{query}'.
    Подбери актуальный фильм,сериал или аниме по запросу пользователя и интересные тайтла с краткими описаниями. Формат:
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
        "👋 Привет! Я ScreenFox — подбираю фильмы, сериалы и аниме. Просто напиши тему или жанр.\n\n"
        "Например:\n- триллер с неожиданной концовкой\n- романтическое аниме\n- сериал как Во все тяжкие",
        reply_markup=main_kb
    )

# Обработка команды /movie или кнопки "Фильм дня"
@dp.message(F.text.lower() == "🎬 фильм дня")
@dp.message(Command("movie"))
async def movie_of_the_day(message: types.Message):
    await message.answer("🎬 Выбираю фильм дня...")
    result = await get_tmdb_trending_movie()
    await message.answer(f"🍿 Фильм дня:\n\n{result}")

# Обработка кнопки "Настройки"
@dp.message(F.text.lower() == "⚙️ настройки")
async def settings_handler(message: types.Message):
    await message.answer("⚙️ Здесь вы можете настроить язык (в будущем) и подписку на \"Фильм дня\". Пока доступна только локализация на русский язык. Напишите 'отписаться', чтобы не получать фильм дня.")

# Ответ на обычный текст — через ИИ
@dp.message(F.text)
async def query_handler(message: types.Message):
    user_ids.add(message.from_user.id)
    await message.answer("🔎 Ищу подборку...")
    result = await get_movie_recommendation(message.text)
    await message.answer(f"📽 Рекомендации:\n\n{result}")

# Плановая рассылка "Фильма дня" через TMDB
async def send_daily_recommendation():
    if user_ids:
        text = await get_tmdb_trending_movie()
        for uid in user_ids:
            try:
                await bot.send_message(uid, f"🌅 Доброе утро! Вот фильм дня от ScreenFox:\n\n{text}")
            except Exception as e:
                logging.warning(f"Не удалось отправить сообщение {uid}: {e}")

# Запуск
async def main():
    scheduler.add_job(send_daily_recommendation, trigger='cron', hour=9, minute=0)  # каждый день в 9:00
    scheduler.start()
    print("✅ ScreenFox запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
