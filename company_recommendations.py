from aiogram import types, Dispatcher, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from typing import Dict
import logging

# Клавиатура для выбора компании
company_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👫 С друзьями", callback_data="company_friends")],
    [InlineKeyboardButton(text="❤️ С парой", callback_data="company_couple")],
    [InlineKeyboardButton(text="👨‍👩‍👧‍👦 С семьей", callback_data="company_family")],
    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_home")]
])

# Обработчик "Рекомендации по компании"
async def company_recommendations_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("👥 С кем вы собираетесь смотреть фильм?", reply_markup=company_kb)

# Callback-обработчик для выбора компании
async def company_callback(callback: types.CallbackQuery, user_history: Dict[int, list], get_movie_recommendation):
    company = callback.data.replace("company_", "")
    if company == "friends":
        query = "Фильмы для просмотра с друзьями: комедии, экшены, приключения."
    elif company == "couple":
        query = "Фильмы для просмотра с парой: романтика, драмы, мелодрамы."
    elif company == "family":
        query = "Фильмы для просмотра с семьей: семейные фильмы, мультфильмы, приключения."
    else:
        query = "Фильмы для любой компании."
    
    await callback.message.answer(f"🔍 Ищу фильмы для компании: {query}")
    try:
        result = await get_movie_recommendation(query)
        if not isinstance(user_history.get(callback.from_user.id), list):
            user_history[callback.from_user.id] = []
        user_history[callback.from_user.id].append(f"Компания: {company}")
        await callback.message.answer(result)
    except Exception as e:
        logging.error(f"Ошибка в обработчике company_callback: {e}")
        await callback.message.answer("😔 Произошла ошибка при обработке запроса.")
    finally:
        await callback.answer()  # Завершение callback

# Регистрация обработчиков
def register_handlers_company(dp: Dispatcher, user_history: Dict[int, list], get_movie_recommendation):
    dp.message.register(company_recommendations_handler, F.text.lower() == "👥 рекомендации по компании")
    dp.callback_query.register(
        lambda callback: company_callback(callback, user_history, get_movie_recommendation),
        F.data.startswith("company_")
    )