import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from openai import OpenAI
import logging

# Вставьте свои ключи здесь напрямую
BOT_TOKEN = "7847598451:AAH8B9-S2QPOznckDlKJZSoSpDs1SLphQ34"
OPENROUTER_API_KEY = "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"

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

# Функция получения рекомендаций
async def get_movie_recommendation(query: str):
    prompt = f"""
    Ты — эксперт по фильмам, сериалам и аниме. Пользователь пишет: '{query}'.
    Подбери 3 актуальных и интересных тайтла с краткими описаниями. Формат:

    1. Название — описание.
    2. Название — описание.
    3. Название — описание.
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

# Обработка команды /start
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "👋 Привет! Я ScreenFox — подбираю фильмы, сериалы и аниме. Просто напиши тему или жанр.\n\n"
        "Например:\n- триллер с неожиданной концовкой\n- романтическое аниме\n- сериал как Во все тяжкие"
    )

# Обработка команды /movie
@dp.message(Command("movie"))
async def movie_of_the_day(message: types.Message):
    await message.answer("🎬 Выбираю фильм дня...")
    result = await get_movie_recommendation("фильм дня")
    await message.answer(f"🍿 Фильм дня:\n\n{result}")

# Ответ на обычный текст
@dp.message(F.text)
async def query_handler(message: types.Message):
    await message.answer("🔎 Ищу подборку...")
    result = await get_movie_recommendation(message.text)
    await message.answer(f"📽 Рекомендации:\n\n{result}")

# Запуск бота
async def main():
    print("✅ ScreenFox запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())