from aiogram import types, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from typing import Callable, Awaitable
import logging
from functools import partial

# Настройка логов, чтобы видеть, где что ломается
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Состояния для FSM
class MovieDescriptionState(StatesGroup):
    WaitingForMovie = State()

# Обработчик команды "Описание фильма одной фразой"
async def movie_description_handler(message: types.Message, state: FSMContext):
    logging.info(f"Юзер {message.from_user.id} хочет описание фильма")
    await state.set_state(MovieDescriptionState.WaitingForMovie)
    await message.answer("🎥 Назови фильм, и я зафигачу описание одной фразой:")

# Обработчик ввода названия фильма
async def handle_movie_description(message: types.Message, state: FSMContext, get_movie_recommendation: Callable[[str], Awaitable[str]]):
    movie_name = message.text.strip()  # Чистим пробелы, чтобы не тупило
    logging.info(f"Юзер {message.from_user.id} ввел фильм: {movie_name}")
    
    await message.answer("🔎 Ща поищу описание...")
    
    try:
        prompt = f"Опиши фильм '{movie_name}' одной фразой."
        logging.info(f"Запрос к get_movie_recommendation: {prompt}")
        

        description = await get_movie_recommendation(prompt)  # Раскомменти, когда будешь готов
        
        logging.info(f"Получил описание: {description}")
        
        if description:
            await message.answer(f"🎥 {movie_name}:\n{description}")
        else:
            logging.warning(f"Описание для '{movie_name}' пустое")
            await message.answer("😔 Не нашел описание, сорян, бро.")
    except Exception as e:
        logging.error(f"Косяк в handle_movie_description: {e}", exc_info=True)
        await message.answer("😔 Что-то пошло не так, попробуй еще разок.")
    finally:
        logging.info("Чистим состояние FSM")
        await state.clear()

# Регистрация обработчиков
def register_handlers_movie_description(dp: Dispatcher, get_movie_recommendation: Callable[[str], Awaitable[str]]):
    logging.info("Регистрируем обработчики для описания фильма")
    dp.message.register(movie_description_handler, F.text.lower() == "🎥 описание фильма одной фразой")
    dp.message.register(
        partial(handle_movie_description, get_movie_recommendation=get_movie_recommendation),
        MovieDescriptionState.WaitingForMovie
    )