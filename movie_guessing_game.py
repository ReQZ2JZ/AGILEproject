import random
import logging
from aiogram import types, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# Список фильмов с эмодзи
movies_with_emojis = [
    {"title": "Король Лев", "emoji": "🦁👑🌅"},
    {"title": "Гарри Поттер", "emoji": "⚡🧙‍♂️🦉🏰"},
    {"title": "Человек-Паук", "emoji": "🕷️🕸️🦸‍♂️🌆"},
    {"title": "Люди в черном", "emoji": "🕶️👽🔫🚗🌌"},
    {"title": "Планета обезьян", "emoji": "🦍🌍⚔️🧬"},
    {"title": "Хитмэн", "emoji": "🧑‍🦲🔫🎯💼"},
    {"title": "Моана", "emoji": "🌊⛵🐷🐓💪🌺"},
    {"title": "Бременские музыканты", "emoji": "🎶🐴🐶🐱🦜"},
    {"title": "Бэтмен", "emoji": "🦇🌃🚨⚔️😈"},
    {"title": "Голодные игры", "emoji": "🏹🔥🏟️💪🕊️"},
    {"title": "Росомаха", "emoji": "🦁🔪🔪🔪💪🩺"},
    {"title": "Плохие парни", "emoji": "🚓🔫😎😎💥"},
    {"title": "Чаки", "emoji": "👶🔪😱👿"},
    {"title": "Мадагаскар", "emoji": "🦒🦁🦓🌴🚢"},
    {"title": "Шрек", "emoji": "🧟‍♂️👸🐴🏰💚"},
    {"title": "Вилли Вонка", "emoji": "🍫🎩🏭🍬✨"},
    {"title": "Элементарно", "emoji": "🔥💧🌬️🌍💞"},
    {"title": "Шерлок Холмс", "emoji": "🕵️‍♂️🔍🎻💡"},
    {"title": "Соник", "emoji": "🦔💨⚡🌍🏃"},
    {"title": "Как приручить дракона", "emoji": "🐉🧑🔥🛡️"}
]

# Список команд главного меню
MENU_COMMANDS = [
    "🎬 фильм дня",
    "📚 жанры",
    "💡 подсказки",
    "🎞 история запросов",
    "⭐ избранное",
    "📊 статистика",
    "🧠 ии-чат",
    "🎮 угадай фильм",
    "📋 смотреть позже",
    "🎨 тематические подборки",
    "🎭 режиссер/актер",
    "⚙️ настройки",
    "🔙 назад"
]

def get_random_movie():
    """Выбирает случайный фильм из списка."""
    return random.choice(movies_with_emojis)

def register_handlers_guess_movie(dp, user_states, user_history):
    """Регистрирует обработчики для игры 'Угадай фильм'."""
    # Словарь для хранения текущего фильма в игре
    game_state = {}

    @router.message(lambda message: message.text.lower() == "🎮 угадай фильм")
    async def start_guess_movie(message: types.Message):
        logging.info(f"Запуск игры 'Угадай фильм' для пользователя {message.from_user.id}")
        random_movie = get_random_movie()
        user_states[message.from_user.id] = "guess_movie"
        game_state[message.from_user.id] = random_movie
        await message.answer(
            f"🎲 Угадайте фильм по эмодзи: {random_movie['emoji']}\nНапишите ваш ответ:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_home")]
            ])
        )

    @router.message(lambda message: message.from_user.id in user_states and user_states[message.from_user.id] == "guess_movie")
    async def check_guess(message: types.Message):
        random_movie = game_state.get(message.from_user.id)
        if not random_movie:
            await message.answer("❗ Ошибка: начните игру заново, выбрав '🎮 Угадай фильм'.")
            return
        # Проверяем, является ли сообщение командой из меню
        if message.text.lower() in MENU_COMMANDS:
            # Очищаем состояние игры
            user_states.pop(message.from_user.id, None)
            game_state.pop(message.from_user.id, None)
            await message.answer("❌ Игра прервана. Выберите действие из меню:", reply_markup=main_kb)
            return
        # Сохраняем попытку угадывания
        if not isinstance(user_history.get(message.from_user.id), list):
            user_history[message.from_user.id] = []
        user_history[message.from_user.id].append(f"Попытка угадать: {message.text}")
        if message.text.lower() == random_movie['title'].lower():
            await message.answer(
                f"✅ Правильно! Это был фильм: {random_movie['title']}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_home")],
                    [InlineKeyboardButton(text="🎮 Играть дальше", callback_data="play_again")]
                ])
            )
            # Добавляем успешное угадывание
            user_history[message.from_user.id].append(f"Угадай фильм: {random_movie['title']}")
            user_states.pop(message.from_user.id, None)
            game_state.pop(message.from_user.id, None)
        else:
            await message.answer(
                "❌ Неправильно. Попробуйте еще раз или узнайте правильный ответ.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_home")],
                    [InlineKeyboardButton(text="ℹ️ Узнать правильный ответ", callback_data="show_answer")]
                ])
            )

    @router.callback_query(lambda c: c.data == "show_answer")
    async def show_answer(callback: types.CallbackQuery):
        random_movie = game_state.get(callback.from_user.id)
        if not random_movie:
            await callback.message.answer("❗ Сначала начните игру, выбрав '🎮 Угадай фильм'.")
            await callback.answer()
            return
        await callback.message.answer(
            f"ℹ️ Правильный ответ: {random_movie['title']}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_home")],
                [InlineKeyboardButton(text="🎮 Играть дальше", callback_data="play_again")]
            ])
        )
        # Добавляем фильм в историю
        if not isinstance(user_history.get(callback.from_user.id), list):
            user_history[callback.from_user.id] = []
        user_history[callback.from_user.id].append(f"Угадай фильм (показан ответ): {random_movie['title']}")
        user_states.pop(callback.from_user.id, None)
        game_state.pop(callback.from_user.id, None)
        await callback.answer()

    @router.callback_query(lambda c: c.data == "play_again")
    async def play_again(callback: types.CallbackQuery):
        random_movie = get_random_movie()
        user_states[callback.from_user.id] = "guess_movie"
        game_state[callback.from_user.id] = random_movie
        await callback.message.answer(
            f"🎲 Угадайте фильм по эмодзи: {random_movie['emoji']}\nНапишите ваш ответ:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_home")]
            ])
        )
        await callback.answer()

    @router.callback_query(lambda c: c.data == "go_home")
    async def go_home(callback: types.CallbackQuery):
        from main import main_kb
        # Очищаем состояние игры при возврате в главное меню
        user_states.pop(callback.from_user.id, None)
        game_state.pop(callback.from_user.id, None)
        await callback.message.answer("🏠 Главное меню:", reply_markup=main_kb)
        await callback.answer()

    logging.info("Регистрация роутера игры 'Угадай фильм'")
    dp.include_router(router)