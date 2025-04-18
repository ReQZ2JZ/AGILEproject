from aiogram import Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from openai import OpenAI
import logging
import re

router = Router()
OPENROUTER_API_KEY = "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"
client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")

reaction_kb = types.InlineKeyboardMarkup(inline_keyboard=[
    [types.InlineKeyboardButton(text="👍", callback_data="like"),
     types.InlineKeyboardButton(text="👎", callback_data="dislike")],
    [types.InlineKeyboardButton(text="💾 В избранное", callback_data="add_favorite")]
])

class ThematicStates(StatesGroup):
    WaitingForQuery = State()

async def generate_thematic_collection(query: str) -> str:
    prompt = (
        f"Ты — эксперт по фильмам. Пользователь просит тематическую подборку: '{query}'. "
        "Составь список из 3-5 фильмов, соответствующих запросу. "
        "Для каждого фильма укажи: название, год выпуска, краткое описание (2-3 предложения), "
        "почему он подходит под запрос. Форматируй ответ так:\n\n"
        "**Название (Год)**\nОписание: ...\nПодходит, потому что: ...\n\n"
        "Не используй нумерацию, только указанный формат."
    )
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        response = completion.choices[0].message.content.strip()
        if not response or "не найдено" in response.lower():
            return "😔 Не удалось найти подходящие фильмы. Попробуйте другой запрос!"
        response = re.sub(r'^\d+\.\s*', '', response, flags=re.MULTILINE)
        return response
    except Exception as e:
        logging.error(f"Ошибка при генерации подборки: {e}")
        return f"😔 Произошла ошибка: {e}"

@router.message(F.text.lower() == "🎨 тематические подборки")
async def thematic_collections_start(message: types.Message, state: FSMContext):
    logging.info(f"Пользователь {message.from_user.id} начал 'Тематические подборки'")
    await state.clear()
    await message.answer(
        "🎨 Введите запрос для тематической подборки (например, 'фильмы с неожиданным финалом' или 'атмосферные триллеры'):",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="🔙 Назад")]],
            resize_keyboard=True
        )
    )
    await state.set_state(ThematicStates.WaitingForQuery)

@router.message(ThematicStates.WaitingForQuery)
async def process_thematic_query(message: types.Message, state: FSMContext, user_history: dict):
    logging.info(f"Пользователь {message.from_user.id} ввел запрос: {message.text}")
    if message.text.lower() == "🔙 назад":
        await message.answer("🏠 Главное меню:", reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="🎬 Фильм дня")],
                [types.KeyboardButton(text="📚 Жанры"), types.KeyboardButton(text="💡 Подсказки")],
                [types.KeyboardButton(text="🎞 История запросов"), types.KeyboardButton(text="⭐ Избранное")],
                [types.KeyboardButton(text="📊 Статистика"), types.KeyboardButton(text="🧠 ИИ-чат")],
                [types.KeyboardButton(text="🎮 Угадай фильм"), types.KeyboardButton(text="📋 Смотреть позже")],
                [types.KeyboardButton(text="🎨 Тематические подборки"), types.KeyboardButton(text="🎭 Режиссер/Актер")],
                [types.KeyboardButton(text="⚙️ Настройки")]
            ],
            resize_keyboard=True
        ))
        await state.clear()
        return

    await message.answer("🔎 Формирую подборку...")
    result = await generate_thematic_collection(message.text)
    user_history.setdefault(message.from_user.id, []).append(f"Тематическая подборка: {message.text}")
    await message.answer(result, reply_markup=reaction_kb)
    await state.clear()

def register_handlers_thematic(dp):
    dp.include_router(router)