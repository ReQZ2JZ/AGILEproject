import random
import logging
from aiogram import types, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

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

# Определяем состояние для игры
class GameStates(StatesGroup):
    GuessMovie = State()

def get_random_movie():
    return random.choice(movies_with_emojis)

def register_handlers_guess_movie(dp, user_history, main_kb):
    @router.message(lambda message: message.text.lower() == "🎮 угадай фильм")
    async def start_guess_movie(message: types.Message, state: FSMContext):
        logging.info(f"Запуск игры 'Угадай фильм' для пользователя {message.from_user.id}")
        random_movie = get_random_movie()
        # Сохраняем данные игры в состоянии FSM
        await state.set_state(GameStates.GuessMovie)
        await state.update_data(movie=random_movie, attempts=0)
        await message.answer(
            f"🎲 Угадайте фильм по эмодзи: {random_movie['emoji']}\nНапишите ваш ответ:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_home")]
            ])
        )

    @router.message(GameStates.GuessMovie)
    async def check_guess(message: types.Message, state: FSMContext):
        # Получаем данные игры из состояния
        game_data = await state.get_data()
        if not game_data:
            await message.answer("❗ Ошибка: начните игру заново, выбрав '🎮 Угадай фильм'.")
            await state.clear()
            return

        random_movie = game_data["movie"]
        if message.text.lower() == random_movie['title'].lower():
            await message.answer(
                f"✅ Правильно! Это был фильм: {random_movie['title']}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_home")],
                    [InlineKeyboardButton(text="🎮 Играть дальше", callback_data="play_again")]
                ])
            )
            # Сбрасываем состояние
            await state.clear()
        else:
            attempts = game_data["attempts"] + 1
            await state.update_data(attempts=attempts)
            await message.answer(
                "❌ Неправильно. Попробуйте еще раз.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_home")],
                    [InlineKeyboardButton(text="ℹ️ Узнать правильный ответ", callback_data="show_answer")]
                ])
            )

    @router.callback_query(lambda c: c.data == "show_answer")
    async def show_answer(callback: types.CallbackQuery, state: FSMContext):
        game_data = await state.get_data()
        if not game_data:
            await callback.message.answer("❗ Сначала начните игру, выбрав '🎮 Угадай фильм'.")
            await callback.answer()
            return
        random_movie = game_data["movie"]
        await callback.message.answer(
            f"ℹ️ Правильный ответ: {random_movie['title']}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_home")],
                [InlineKeyboardButton(text="🎮 Играть дальше", callback_data="play_again")]
            ])
        )
        # Сбрасываем состояние
        await state.clear()
        await callback.answer()

    @router.callback_query(lambda c: c.data == "play_again")
    async def play_again(callback: types.CallbackQuery, state: FSMContext):
        random_movie = get_random_movie()
        await state.set_state(GameStates.GuessMovie)
        await state.update_data(movie=random_movie, attempts=0)
        await callback.message.answer(
            f"🎲 Угадайте фильм по эмодзи: {random_movie['emoji']}\nНапишите ваш ответ:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_home")]
            ])
        )
        await callback.answer()

    @router.callback_query(lambda c: c.data == "go_home")
    async def go_home(callback: types.CallbackQuery, state: FSMContext):
        # Сбрасываем состояние игры
        await state.clear()
        # Удаляем старую клавиатуру и возвращаем главное меню
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("🏠 Игра завершена. Вы вернулись в главное меню.", reply_markup=main_kb)
        await callback.answer()

    dp.include_router(router)