import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from openai import OpenAI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp
from movie_guessing_game import register_handlers_guess_movie
from watch_later import router as watch_later_router
from thematic_collections import register_handlers_thematic
from director_actor_recommendations import register_handlers_director_actor
from company_recommendations import register_handlers_company
from movie_description import register_handlers_movie_description
from typing import Callable, Dict, Any, Awaitable

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токены и ключи API
BOT_TOKEN = "7847598451:AAH8B9-S2QPOznckDlKJZSoSpDs1SLphQ34"
OPENROUTER_API_KEY = "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"
TMDB_API_KEY = "941d2663b8c7da9e88d80d9ac8e48105"

# Инициализация клиента OpenRouter
client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# Глобальные словари для хранения данных
user_states = {}
user_ids = set()
user_language = {}
user_subscriptions = set()
user_history = {}
user_favorites = {}
user_reactions = {}

# Middleware для передачи user_history
class UserHistoryMiddleware(BaseMiddleware):
    def __init__(self, user_history: dict):
        self.user_history = user_history
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any]
    ) -> Any:
        logging.info(f"Middleware вызван для пользователя {event.from_user.id}")
        data['user_history'] = self.user_history
        return await handler(event, data)

# Состояния FSM
class UserStates(StatesGroup):
    AIChat = State()
    Tips = State()

# Клавиатуры
main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🎬 Фильм дня")],
    [KeyboardButton(text="📚 Жанры"), KeyboardButton(text="💡 Подсказки")],
    [KeyboardButton(text="🎞 История запросов"), KeyboardButton(text="⭐ Избранное")],
    [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="🧠 ИИ-чат")],
    [KeyboardButton(text="🎮 Угадай фильм"), KeyboardButton(text="📋 Смотреть позже")],
    [KeyboardButton(text="🎨 Тематические подборки"), KeyboardButton(text="🎭 Режиссер/Актер")],
    [KeyboardButton(text="👥 Рекомендации по компании"), KeyboardButton(text="🎥 Описание фильма одной фразой")],
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

# Функция для получения рекомендации от ИИ
async def get_movie_recommendation(query: str):
    prompt = f"Опиши фильм '{query}' одной фразой."
    try:
        logging.info(f"Отправка запроса к OpenRouter API: {query}")
        completion = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Ошибка при запросе к OpenRouter: {e}")
        return None

# Функция для получения фильма дня от TMDB
async def get_tmdb_trending_movie():
    url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={TMDB_API_KEY}&language=ru-RU"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logging.error(f"Ошибка TMDB API: Статус {response.status}, {await response.text()}")
                    return "😔 Не удалось получить фильм дня.", None
                data = await response.json()
                logging.info(f"Ответ TMDB: {data}")
                if data.get("results"):
                    movie = data["results"][0]
                    return (
                        f"🎬 {movie.get('title', 'Без названия')}\n\n{movie.get('overview', 'Описание отсутствует.')}",
                        movie.get('title', 'Без названия')
                    )
                logging.warning("TMDB API не вернул результатов")
                return "😔 Фильмы не найдены.", None
    except aiohttp.ClientError as e:
        logging.error(f"Ошибка сети в запросе TMDB: {e}")
        return "😔 Ошибка сети. Попробуйте позже.", None
    except ValueError as e:
        logging.error(f"Ошибка декодирования JSON в ответе TMDB: {e}")
        return "😔 Ошибка обработки ответа сервера.", None
    except Exception as e:
        logging.error(f"Неизвестная ошибка в get_tmdb_trending_movie: {e}")
        return "😔 Произошла неизвестная ошибка.", None

# Обработчик команды /start
@dp.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    user_ids.add(message.from_user.id)
    await message.answer("👋 Привет! Я ScreenFox. Выбери пункт из меню:", reply_markup=main_kb)

# Обработчик "Фильм дня"
@dp.message(F.text.lower() == "🎬 фильм дня")
async def movie_of_the_day(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🎬 Ищу фильм дня...")
    result, title = await get_tmdb_trending_movie()
    if title:
        if not isinstance(user_history.get(message.from_user.id), list):
            user_history[message.from_user.id] = []
        user_history[message.from_user.id].append(title)
    await message.answer(result, reply_markup=reaction_kb)

# Обработчик "Подсказки"
@dp.message(F.text.lower() == "💡 подсказки")
async def tips_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("💡 Примеры запросов:\n- комедия 2020-х\n- боевик как Джон Уик\n- романтическое аниме", reply_markup=back_kb)
    await state.set_state(UserStates.Tips)

@dp.message(UserStates.Tips)
async def handle_tips(message: types.Message, state: FSMContext):
    await message.answer("🔎 Ищу рекомендации...")
    result = await get_movie_recommendation(message.text)
    if not isinstance(user_history.get(message.from_user.id), list):
        user_history[message.from_user.id] = []
    user_history[message.from_user.id].append(f"Подсказка: {message.text}")
    await message.answer(result)
    await state.clear()

# Обработчик "Жанры"
@dp.message(F.text.lower() == "📚 жанры")
async def genre_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("📚 Выбери жанр:", reply_markup=genres_kb)

@dp.callback_query(F.data.startswith("genre_"))
async def genre_callback(callback: types.CallbackQuery):
    genre = callback.data.replace("genre_", "")
    await callback.message.answer(f"🔍 Ищу фильмы в жанре {genre}...")
    result = await get_movie_recommendation(f"Фильмы в жанре {genre}")
    if not isinstance(user_history.get(callback.from_user.id), list):
        user_history[callback.from_user.id] = []
    user_history[callback.from_user.id].append(f"Жанр: {genre}")
    await callback.message.answer(result, reply_markup=reaction_kb)
    await callback.answer()

# Обработчик "Настройки"
@dp.message(F.text.lower() == "⚙️ настройки")
async def settings_handler(message: types.Message, state: FSMContext):
    await state.clear()
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

# Обработчик "Назад"
@dp.message(F.text.lower() == "🔙 назад")
async def back_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Главное меню:", reply_markup=main_kb)

# Обработчик "История запросов"
@dp.message(F.text.lower() == "🎞 история запросов")
async def history_handler(message: types.Message, state: FSMContext):
    await state.clear()
    history = user_history.get(message.from_user.id, [])
    if not isinstance(history, list):
        history = []
        user_history[message.from_user.id] = history
    filtered_history = [str(item) for item in history if item is not None]
    text = "\n".join(filtered_history) if filtered_history else "История пуста."
    await message.answer(f"📜 История запросов:\n{text}")

# Обработчик "Избранное"
@dp.message(F.text.lower() == "⭐ избранное")
async def favorites_handler(message: types.Message, state: FSMContext):
    await state.clear()
    favorites = user_favorites.get(message.from_user.id, [])
    text = "\n".join(favorites) if favorites else "⭐ Ваш список избранного пуст."
    await message.answer(text)

# Обработчик "Статистика"
@dp.message(F.text.lower() == "📊 статистика")
async def stats_handler(message: types.Message, state: FSMContext):
    await state.clear()
    reactions = user_reactions.get(message.from_user.id, {"like": 0, "dislike": 0})
    favs = len(user_favorites.get(message.from_user.id, []))
    await message.answer(f"📊 Ваша статистика:\n👍 Лайков: {reactions['like']}\n👎 Дизлайков: {reactions['dislike']}\n⭐ Избранное: {favs}")

# Обработчик "ИИ-чат"
@dp.message(F.text.lower() == "🧠 ии-чат")
async def ai_chat_prompt(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🧠 Введите ваш вопрос к ИИ-эксперту по фильмам:")
    await state.set_state(UserStates.AIChat)

@dp.message(UserStates.AIChat)
async def handle_ai_chat(message: types.Message, state: FSMContext):
    await message.answer("🔎 Ищу ответ от ИИ...")
    result = await get_movie_recommendation(message.text)
    if not isinstance(user_history.get(message.from_user.id), list):
        user_history[message.from_user.id] = []
    user_history[message.from_user.id].append(f"ИИ-чат: {message.text}")
    await message.answer(result)
    await state.clear()

# Обработчики реакций
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

# Функция для отправки ежедневных рекомендаций
async def send_daily_recommendation():
    if user_subscriptions:
        text, title = await get_tmdb_trending_movie()
        for uid in user_subscriptions:
            try:
                if title:
                    if not isinstance(user_history.get(uid), list):
                        user_history[uid] = []
                    user_history[uid].append(title)
                await bot.send_message(uid, f"🌅 Доброе утро! 🎬 Фильм дня от ScreenFox:\n\n{text}", reply_markup=reaction_kb)
            except Exception as e:
                logging.warning(f"Не удалось отправить сообщение пользователю {uid}: {e}")

# Главная функция
async def main():
    dp.message.middleware(UserHistoryMiddleware(user_history))
    dp.include_router(watch_later_router)
    register_handlers_guess_movie(dp, user_states, user_history)
    register_handlers_thematic(dp)
    register_handlers_director_actor(dp)
    register_handlers_company(dp, user_history, get_movie_recommendation)
    register_handlers_movie_description(dp, get_movie_recommendation)  # Регистрация обработчиков описания фильма
    scheduler.add_job(send_daily_recommendation, trigger='cron', hour=9, minute=0)
    scheduler.start()
    logging.info("✅ ScreenFox запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())