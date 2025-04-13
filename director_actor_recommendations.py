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

class DirectorActorStates(StatesGroup):
    WaitingForName = State()

async def generate_director_actor_recommendations(name: str) -> str:
    prompt = (
        f"Ты — эксперт по фильмам. Пользователь указал имя: '{name}'. "
        "Определи, является ли это имя режиссером или актером, и составь список из 3-5 фильмов, "
        "где этот человек играл ключевую роль (как режиссер или актер). "
        "Для каждого фильма укажи: название, год выпуска, краткое описание (2-3 предложения), "
        "роль человека (режиссер или актер). Форматируй ответ так:\n\n"
        "**Название (Год)**\nОписание: ...\nРоль: ...\n\n"
        "Если имя неоднозначное, выбери наиболее вероятный вариант. "
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
            return f"😔 Не удалось найти фильмы для '{name}'. Проверьте правильность имени или попробуйте другое!"
        response = re.sub(r'^\d+\.\s*', '', response, flags=re.MULTILINE)
        return response
    except Exception as e:
        logging.error(f"Ошибка при генерации рекомендаций для '{name}': {e}")
        return f"😔 Произошла ошибка: {e}"

@router.message(F.text.lower() == "🎭 режиссер/актер")
async def director_actor_start(message: types.Message, state: FSMContext):
    logging.info(f"Пользователь {message.from_user.id} начал 'Режиссер/Актер'")
    await state.clear()
    await message.answer(
        "🎭 Введите имя режиссера или актера (например, 'Кристофер Нолан' или 'Леонардо ДиКаприо'):",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="🔙 Назад")]],
            resize_keyboard=True
        )
    )
    await state.set_state(DirectorActorStates.WaitingForName)

@router.message(DirectorActorStates.WaitingForName)
async def process_director_actor_name(message: types.Message, state: FSMContext, user_history: dict):
    logging.info(f"Пользователь {message.from_user.id} ввел имя: {message.text}")
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

    await message.answer(f"🔎 Ищу фильмы с '{message.text}'...")
    result = await generate_director_actor_recommendations(message.text)
    user_history.setdefault(message.from_user.id, []).append(f"Режиссер/Актер: {message.text}")
    await message.answer(result, reply_markup=reaction_kb)
    await state.clear()

def register_handlers_director_actor(dp):
    dp.include_router(router)