import random
from aiogram import types, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

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

def get_random_movie():
    return random.choice(movies_with_emojis)

def register_handlers_guess_movie(dp, user_states, user_history):
    @router.message(lambda message: message.text.lower() == "🎮 угадай фильм")
    async def start_guess_movie(message: types.Message):
        random_movie = get_random_movie()
        user_states[message.from_user.id] = "guess_movie" 
        user_history[message.from_user.id] = random_movie  
        await message.answer(
            f"🎲 Угадайте фильм по эмодзи: {random_movie['emoji']}\nНапишите ваш ответ:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_home")]
            ])
        )

    @router.message(lambda message: message.from_user.id in user_history)
    async def check_guess(message: types.Message):
        random_movie = user_history.get(message.from_user.id)
        if message.text.lower() == random_movie['title'].lower():
            await message.answer(
                f"✅ Правильно! Это был фильм: {random_movie['title']}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_home")],
                    [InlineKeyboardButton(text="🎮 Играть дальше", callback_data="play_again")]
                ])
            )
            user_states.pop(message.from_user.id, None) 
            user_history.pop(message.from_user.id, None)
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
        random_movie = user_history.get(callback.from_user.id)
        if not random_movie:
            await callback.message.answer("❗ Сначала начните игру, выбрав '🎮 Угадай фильм'.")
            return

        await callback.message.answer(
            f"ℹ️ Правильный ответ: {random_movie['title']}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_home")],
                [InlineKeyboardButton(text="🎮 Играть дальше", callback_data="play_again")]
            ])
        )
        user_states.pop(callback.from_user.id, None) 
        user_history.pop(callback.from_user.id, None) 
        await callback.answer()

    @router.callback_query(lambda c: c.data == "play_again")
    async def play_again(callback: types.CallbackQuery):
        random_movie = get_random_movie()
        user_states[callback.from_user.id] = "guess_movie"
        user_history[callback.from_user.id] = random_movie 
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
        await callback.message.answer("🏠 Главное меню:", reply_markup=main_kb)
        await callback.answer()

    dp.include_router(router)