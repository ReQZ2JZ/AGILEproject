from aiogram import types, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from typing import Callable, Awaitable
import logging

# Состояние FSM для описания фильма
class MovieDescriptionState(StatesGroup):
    WaitingForMovie = State()

# Обработчик кнопки "Описание фильма одной фразой"
async def movie_description_handler(message: types.Message, state: FSMContext):
    await state.set_state(MovieDescriptionState.WaitingForMovie)
    await message.answer("🎥 Введите название фильма, и я опишу его одной фразой:")

# Обработчик ввода названия фильма
async def handle_movie_description(message: types.Message, state: FSMContext, get_movie_recommendation: Callable[[str], Awaitable[str]]):
    movie_name = message.text
    await message.answer("🔎 Ищу описание фильма...")
    try:
        # Генерация описания фильма
        prompt = f"Опиши фильм '{movie_name}' одной фразой."
        description = await get_movie_recommendation(prompt)
        if description:
            await message.answer(f"🎥 {movie_name}:\n{description}")
        else:
            await message.answer("😔 Не удалось найти описание для этого фильма.")
    except Exception as e:
        logging.error(f"Ошибка в handle_movie_description: {e}")
        await message.answer("😔 Произошла ошибка при получении описания фильма.")
    finally:
        await state.clear()

# Регистрация обработчиков
def register_handlers_movie_description(dp: Dispatcher, get_movie_recommendation: Callable[[str], Awaitable[str]]):
    dp.message.register(movie_description_handler, F.text.lower() == "🎥 описание фильма одной фразой")
    dp.message.register(
        lambda message, state: handle_movie_description(message, state, get_movie_recommendation),
        MovieDescriptionState.WaitingForMovie
    )