import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from openai import OpenAI
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp

BOT_TOKEN = "7847598451:AAH8B9-S2QPOznckDlKJZSoSpDs1SLphQ34"
OPENROUTER_API_KEY = "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"
TMDB_API_KEY = "941d2663b8c7da9e88d80d9ac8e48105"

logging.basicConfig(level=logging.INFO)

client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

user_ids = set()
user_language = {}
user_subscriptions = set()
user_history = {}
user_favorites = {}
user_reactions = {}

main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🎬 Фильм дня")],
    [KeyboardButton(text="📚 Жанры"), KeyboardButton(text="💡 Подсказки")],
    [KeyboardButton(text="🎞 История запросов"), KeyboardButton(text="⭐ Избранное")],
    [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="🧠 ИИ-чат")],
    [KeyboardButton(text="⚙️ Настройки")]
], resize_keyboard=True)

back_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Назад")]], resize_keyboard=True)

genres_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎭 Драма", callback_data="genre_драма"),
     InlineKeyboardButton(text="😂 Комедия", callback_data="genre_комедия")],
    [InlineKeyboardButton(text="🎢 Триллер", callback_data="genre_триллер"),
     InlineKeyboardButton(text="💥 Боевик", callback_data="genre_боевик")],
    [InlineKeyboardButton(text="💘 Романтика", callback_data="genre_романтика"),
     InlineKeyboardButton(text="🎥 Аниме", callback_data="genre_аниме")],
    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_home")]
])

settings_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🌍 Язык: Русский (скоро)", callback_data="lang_ru")],
    [InlineKeyboardButton(text="🔔 Подписка на 'Фильм дня'", callback_data="subscribe")],
    [InlineKeyboardButton(text="🚫 Отписаться", callback_data="unsubscribe")],
    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_home")]
])

reaction_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👍", callback_data="like"),
     InlineKeyboardButton(text="👎", callback_data="dislike")],
    [InlineKeyboardButton(text="💾 В избранное", callback_data="add_favorite")]
])

async def get_movie_recommendation(query: str):
    prompt = f"Ты — эксперт по фильмам, сериалам и аниме. Пользователь пишет: '{query}'. Подбери актуальные тайтлы."
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

async def get_tmdb_trending_movie():
    url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={TMDB_API_KEY}&language=ru-RU"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            if data.get("results"):
                movie = data["results"][0]
                return f"🎬 {movie.get('title', 'Без названия')}\n\n{movie.get('overview', 'Описание отсутствует.')}", movie.get('title', 'Без названия')
            return "😔 Не удалось получить фильм дня.", None

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_ids.add(message.from_user.id)
    await message.answer("👋 Привет! Я ScreenFox. Напиши тему или выбери пункт меню:", reply_markup=main_kb)

@dp.message(F.text.lower() == "🎬 фильм дня")
async def movie_of_the_day(message: types.Message):
    await message.answer("🎬 Ищу фильм дня...")
    result, title = await get_tmdb_trending_movie()
    user_history.setdefault(message.from_user.id, []).append(title)
    await message.answer(result, reply_markup=reaction_kb)

@dp.message(F.text.lower() == "💡 подсказки")
async def tips_handler(message: types.Message):
    await message.answer("💡 Примеры запросов:\n- комедия 2020-х\n- боевик как Джон Уик\n- романтическое аниме", reply_markup=back_kb)

@dp.message(F.text.lower() == "📚 жанры")
async def genre_menu(message: types.Message):
    await message.answer("📚 Выбери жанр:", reply_markup=genres_kb)

@dp.callback_query(F.data.startswith("genre_"))
async def genre_callback(callback: types.CallbackQuery):
    genre = callback.data.replace("genre_", "")
    await callback.message.answer(f"🔍 Ищу фильмы в жанре {genre}...")
    result = await get_movie_recommendation(f"Фильмы в жанре {genre}")
    user_history.setdefault(callback.from_user.id, []).append(f"Жанр: {genre}")
    await callback.message.answer(result, reply_markup=reaction_kb)
    await callback.answer()

@dp.message(F.text.lower() == "⚙️ настройки")
async def settings_handler(message: types.Message):
    await message.answer("⚙️ Настройки:", reply_markup=settings_kb)

@dp.callback_query(F.data == "subscribe")
async def subscribe_callback(callback: types.CallbackQuery):
    user_subscriptions.add(callback.from_user.id)
    await callback.message.answer("✅ Вы подписаны на ежедневные рекомендации!")
    await callback.answer()

@dp.callback_query(F.data == "unsubscribe")
async def unsubscribe_callback(callback: types.CallbackQuery):
    user_subscriptions.discard(callback.from_user.id)
    await callback.message.answer("🚫 Вы отписались от 'Фильма дня'.")
    await callback.answer()

@dp.callback_query(F.data == "go_home")
async def go_home_callback(callback: types.CallbackQuery):
    await callback.message.answer("🏠 Главное меню:", reply_markup=main_kb)
    await callback.answer()

@dp.message(F.text.lower() == "🔙 назад")
async def back_handler(message: types.Message):
    await message.answer("🏠 Главное меню:", reply_markup=main_kb)

@dp.message(F.text.lower() == "🎞 история запросов")
async def history_handler(message: types.Message):
    history = user_history.get(message.from_user.id, [])
    text = "\n".join(history[-10:]) if history else "История пуста."
    await message.answer(f"📜 История запросов:\n{text}")

@dp.message(F.text.lower() == "⭐ избранное")
async def favorites_handler(message: types.Message):
    favorites = user_favorites.get(message.from_user.id, [])
    text = "\n".join(favorites) if favorites else "⭐ Ваш список избранного пуст."
    await message.answer(text)

@dp.message(F.text.lower() == "📊 статистика")
async def stats_handler(message: types.Message):
    reactions = user_reactions.get(message.from_user.id, {"like": 0, "dislike": 0})
    favs = len(user_favorites.get(message.from_user.id, []))
    await message.answer(f"📊 Ваша статистика:\n👍 Лайков: {reactions['like']}\n👎 Дизлайков: {reactions['dislike']}\n⭐ Избранное: {favs}")

@dp.message(F.text.lower() == "🧠 ии-чат")
async def ai_chat_prompt(message: types.Message):
    await message.answer("🧠 Введите ваш вопрос к ИИ-эксперту по фильмам:")

@dp.callback_query(F.data == "like")
async def like_handler(callback: types.CallbackQuery):
    user_reactions.setdefault(callback.from_user.id, {"like": 0, "dislike": 0})["like"] += 1
    await callback.answer("👍 Спасибо за лайк!")

@dp.callback_query(F.data == "dislike")
async def dislike_handler(callback: types.CallbackQuery):
    user_reactions.setdefault(callback.from_user.id, {"like": 0, "dislike": 0})["dislike"] += 1
    await callback.answer("👎 Спасибо за отзыв!")

@dp.callback_query(F.data == "add_favorite")
async def favorite_handler(callback: types.CallbackQuery):
    message_text = callback.message.text.split('\n')[0].replace("🎬 ", "").strip()
    user_favorites.setdefault(callback.from_user.id, []).append(message_text)
    await callback.answer("💾 Добавлено в избранное!")

@dp.message(F.text)
async def query_handler(message: types.Message):
    user_ids.add(message.from_user.id)
    user_history.setdefault(message.from_user.id, []).append(message.text)
    await message.answer("🔎 Ищу подборку...")
    result = await get_movie_recommendation(message.text)
    await message.answer(f"📽 Рекомендации:\n\n{result}", reply_markup=reaction_kb)

async def send_daily_recommendation():
    if user_subscriptions:
        text, title = await get_tmdb_trending_movie()
        for uid in user_subscriptions:
            try:
                user_history.setdefault(uid, []).append(title)
                await bot.send_message(uid, f"🌅 Доброе утро! 🎬 Фильм дня от ScreenFox:\n\n{text}", reply_markup=reaction_kb)
            except Exception as e:
                logging.warning(f"Не удалось отправить сообщение {uid}: {e}")

async def main():
    scheduler.add_job(send_daily_recommendation, trigger='cron', hour=9, minute=0)
    scheduler.start()
    print("✅ ScreenFox запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
