# thematic_collections.py

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery  # Добавлен CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from openai import OpenAI
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Конфигурация OpenAI
OPENROUTER_API_KEY = "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"
client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")

# Создаем роутер
router = Router()

# Хранилище истории запросов (если не передается из основного кода)
user_history = {}

# Состояния FSM
class CollectionStates(StatesGroup):
    WaitingForQuery = State()

# Клавиатуры
back_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Назад")]], resize_keyboard=True)

reaction_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👍", callback_data="like"),
     InlineKeyboardButton(text="👎", callback_data="dislike")],
    [InlineKeyboardButton(text="💾 В избранное", callback_data="add_favorite")]
])

async def generate_thematic_collection(query: str) -> str:
    """
    Генерирует тематическую подборку фильмов на основе пользовательского запроса.
    """
    prompt = (
        f"Ты — эксперт по фильмам. Пользователь просит тематическую подборку: '{query}'. "
        f"Составь список из 3-5 фильмов, соответствующих запросу. Для каждого фильма укажи: "
        f"название, год выпуска, краткое описание (1-2 предложения). "
        f"Форматируй ответ в виде нумерованного списка."
    )
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Ошибка при генерации подборки: {e}")
        return "😔 Не удалось создать подборку. Попробуйте позже."

@router.message(F.text.lower() == "📽 тематические подборки")
async def thematic_collection_start(message: Message, state: FSMContext):
    """
    Запускает процесс создания тематической подборки.
    """
    await message.answer(
        "📽 Введите запрос для тематической подборки (например, 'фильмы с неожиданным финалом' или 'атмосферные триллеры'):",
        reply_markup=back_kb
    )
    await state.set_state(CollectionStates.WaitingForQuery)

@router.message(CollectionStates.WaitingForQuery)
async def process_collection_query(message: Message, state: FSMContext):
    """
    Обрабатывает пользовательский запрос для генерации подборки.
    """
    query = message.text.strip()
    if not query:
        await message.answer("😕 Запрос не может быть пустым. Попробуйте еще раз:")
        return

    await message.answer("🔎 Формирую подборку...")
    result = await generate_thematic_collection(query)

    # Сохраняем запрос в историю
    user_history.setdefault(message.from_user.id, []).append(f"Тематическая подборка: {query}")

    await message.answer(result, reply_markup=reaction_kb)
    await state.clear()

@router.message(F.text.lower() == "🔙 назад")
async def back_handler(message: Message, state: FSMContext):
    """
    Возвращает пользователя в главное меню (нужен основной код для полной работы).
    """
    await message.answer("🏠 Возвращаюсь в главное меню...", reply_markup=None)
    await state.clear()

@router.callback_query(F.data == "like")
async def like_handler(callback: CallbackQuery):
    """
    Обрабатывает лайк для подборки.
    """
    await callback.answer("👍 Спасибо за лайк!")

@router.callback_query(F.data == "dislike")
async def dislike_handler(callback: CallbackQuery):
    """
    Обрабатывает дизлайк для подборки.
    """
    await callback.answer("👎 Спасибо за отзыв!")

@router.callback_query(F.data == "add_favorite")
async def favorite_handler(callback: CallbackQuery):
    """
    Добавляет подборку в избранное (нужен основной код для хранения).
    """
    await callback.answer("💾 Добавлено в избранное!")