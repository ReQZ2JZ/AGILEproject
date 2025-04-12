from aiogram import types, Router
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

router = Router()

watch_later_list = {}

class WatchLaterStates(StatesGroup):
    AddingMovie = State()
    DeletingMovie = State()

watch_later_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="➕ Добавить фильм"), KeyboardButton(text="📋 Показать список"), KeyboardButton(text="🗑 Удалить фильм")],
    [KeyboardButton(text="🏠 Главное меню")]
], resize_keyboard=True)

@router.message(lambda message: message.text.lower() == "📋 смотреть позже")
async def show_watch_later_list(message: types.Message):
    user_id = message.from_user.id
    movies = watch_later_list.get(user_id, [])

    if not movies:
        await message.answer("📜 Ваш список 'Посмотреть позже' пуст.", reply_markup=watch_later_kb)
    else:
        movies_text = "\n".join([f"• {movie}" for movie in movies])
        await message.answer(f"📜 Ваш список 'Посмотреть позже':\n{movies_text}", reply_markup=watch_later_kb)

@router.message(lambda message: message.text.lower() == "➕ добавить фильм")
async def add_to_watch_later_prompt(message: types.Message, state: FSMContext):
    await message.answer("Введите название фильма, который вы хотите добавить в список 'Посмотреть позже':")
    await state.set_state(WatchLaterStates.AddingMovie)

@router.message(WatchLaterStates.AddingMovie)
async def save_movie_to_watch_later(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    movie_title = message.text.strip()

    if user_id not in watch_later_list:
        watch_later_list[user_id] = []

    watch_later_list[user_id].append(movie_title)
    await message.answer(f"🎥 Фильм '{movie_title}' добавлен в список 'Посмотреть позже'!", reply_markup=watch_later_kb)
    await state.clear()

@router.message(lambda message: message.text.lower() == "📋 показать список")
async def show_watch_later_list_again(message: types.Message):
    user_id = message.from_user.id
    movies = watch_later_list.get(user_id, [])

    if not movies:
        await message.answer("📜 Ваш список 'Посмотреть позже' пуст.", reply_markup=watch_later_kb)
    else:
        movies_text = "\n".join([f"• {movie}" for movie in movies])
        await message.answer(f"📜 Ваш список 'Посмотреть позже':\n{movies_text}", reply_markup=watch_later_kb)

@router.message(lambda message: message.text.lower() == "🗑 удалить фильм")
async def delete_from_watch_later_prompt(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    movies = watch_later_list.get(user_id, [])

    if not movies:
        await message.answer("📜 Ваш список 'Посмотреть позже' пуст. Нечего удалять.", reply_markup=watch_later_kb)
    else:
        movies_text = "\n".join([f"{i + 1}. {movie}" for i, movie in enumerate(movies)])
        await message.answer(f"🗑 Ваш список фильмов:\n{movies_text}\n\nВведите номер фильма, который хотите удалить:")
        await state.set_state(WatchLaterStates.DeletingMovie)

@router.message(WatchLaterStates.DeletingMovie)
async def confirm_delete_movie(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    movies = watch_later_list.get(user_id, [])

    try:
        index = int(message.text.strip()) - 1
        if 0 <= index < len(movies):
            removed_movie = movies.pop(index)
            await message.answer(f"✅ Фильм '{removed_movie}' удален из списка 'Посмотреть позже'.", reply_markup=watch_later_kb)
        else:
            await message.answer("❌ Неверный номер. Попробуйте снова.", reply_markup=watch_later_kb)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный номер.", reply_markup=watch_later_kb)

    await state.clear()

@router.message(lambda message: message.text.lower() == "🏠 главное меню")
async def go_to_main_menu(message: types.Message):
    from main import main_kb
    await message.answer("🏠 Вы вернулись в главное меню:", reply_markup=main_kb)