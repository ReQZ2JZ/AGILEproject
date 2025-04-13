from aiogram import types, Dispatcher, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from typing import Dict
import logging
from functools import partial

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    logging.info(f"Пользователь {message.from_user.id} запросил рекомендации по компании")
    await message.answer("👥 С кем вы собираетесь смотреть фильм?", reply_markup=company_kb)

# Callback-обработчик для выбора компании
async def company_callback(callback: types.CallbackQuery, user_history: Dict[int, list], get_movie_recommendation):
    logging.info(f"Получен callback от {callback.from_user.id}: {callback.data}")
    
    company = callback.data.replace("company_", "")
    logging.info(f"Выбрана компания: {company}")
    
    # Формируем запрос
    if company == "friends":
        query = "Фильмы для просмотра с друзьями: комедии, экшены, приключения."
    elif company == "couple":
        query = "Фильмы для просмотра с парой: романтика, драмы, мелодрамы."
    elif company == "family":
        query = "Фильмы для просмотра с семьей: семейные фильмы, мультфильмы, приключения."
    else:
        logging.warning(f"Неизвестная компания: {company}")
        await callback.message.answer("⚠️ Неизвестная компания, возвращайтесь в меню.")
        await callback.answer()
        return
    
    # Отправляем сообщение о начале поиска
    await callback.message.answer(f"🔍 Ищу фильмы для компании: {query}")
    logging.info(f"Отправлено сообщение с запросом: {query}")
    
    try:
        # Временная заглушка для теста
        logging.info("Попытка вызвать get_movie_recommendation")
        result = await get_movie_recommendation(query)
        
        logging.info(f"Получен результат: {result}")
        
        # Обновление истории пользователя
        if not isinstance(user_history.get(callback.from_user.id), list):
            user_history[callback.from_user.id] = []
        user_history[callback.from_user.id].append(f"Компания: {company}")
        logging.info(f"История пользователя {callback.from_user.id} обновлена: {user_history[callback.from_user.id]}")
        
        await callback.message.answer(result)
    except Exception as e:
        logging.error(f"Ошибка в company_callback: {e}", exc_info=True)
        await callback.message.answer("😔 Произошла ошибка при получении рекомендаций. Попробуйте позже.")
    finally:
        logging.info("Завершение callback")
        await callback.answer()

# Регистрация обработчиков
def register_handlers_company(dp: Dispatcher, user_history: Dict[int, list], get_movie_recommendation):
    logging.info("Регистрация обработчиков для рекомендаций по компании")
    dp.message.register(company_recommendations_handler, F.text.lower() == "👥 рекомендации по компании")
    # Используем partial для передачи дополнительных аргументов
    dp.callback_query.register(
        partial(company_callback, user_history=user_history, get_movie_recommendation=get_movie_recommendation),
        F.data.startswith("company_")
    )