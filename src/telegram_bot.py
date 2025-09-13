import asyncio
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from db import add_telegram_user
from olx_api import get_city_info
from utils import remove_duplicate_cities

# --- Load environment variables from .env file ---
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

if not API_TOKEN:
    raise ValueError("No API token provided. Please set the API_TOKEN environment variable.")


# --- Initialize bot and dispatcher ---
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


# --- States for FSM ---
class SearchStates(StatesGroup):
    waiting_for_city = State()


# --- Persistent bottom menu (ReplyKeyboard) ---
def get_persistent_menu() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text="/start")]]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


# --- Inline main menu (for categories) ---
def get_main_menu() -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton(text="🏠 Нерухомість", callback_data="category_real_estate")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# --- /start command handler ---
@dp.message(Command("start"))
async def start_handler(message: types.Message) -> None:
    if message.from_user is None:
        await message.answer("Помилка: не вдалося отримати дані користувача.")
        return

    user = message.from_user
    text = (
        f"Привіт, <b>{user.first_name}</b>!\n\n"
        f"Твій ID: <code>{user.id}</code>\n"
        f"Username: @{user.username if user.username else '—'}\n\n"
        "Оберіть категорію для пошуку:"
    )
    add_telegram_user(telegram_id=user.id, telegram_username=user.username or "")
    await message.answer(text, reply_markup=get_main_menu())

    # Send reply keyboard (always visible)
    await message.answer("Меню доступне завжди 👇", reply_markup=get_persistent_menu())


# --- Callback handler for menu selection ---
@dp.callback_query(F.data == "category_real_estate")
async def category_real_estate_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not isinstance(callback.message, types.Message):
        await callback.answer("Помилка: повідомлення недоступне.", show_alert=True)
        return

    await callback.message.edit_text(
        "✅ Ви обрали категорію: <b>Нерухомість</b>\n\nВведіть назву міста:",
        reply_markup=None,
    )
    await state.set_state(SearchStates.waiting_for_city)
    await callback.answer()


# --- Handler for city input ---
@dp.message(SearchStates.waiting_for_city)
async def process_city_input(message: types.Message, state: FSMContext) -> None:
    if message.text is None:
        await message.answer("⚠️ Не вдалося отримати текст повідомлення.")
        return
    city_name = message.text.strip()

    if len(city_name) < 3:
        await message.answer("⚠️ Введіть щонайменше 3 літери для пошуку міста.")
        return

    await message.answer("⏳ Шукаю місто...")
    try:
        data = await get_city_info(city_name)
    except Exception as e:
        await message.answer(f"❌ Помилка при виклику API: {e}")
        return

    if not data.get("data"):
        await message.answer("❌ Місто не знайдено. Спробуйте ще раз.")
        return

    city_data = data["data"]
    # remove duplicates:
    unique_cities = remove_duplicate_cities(city_data)

    # Take first 5 options HARD CODED
    options = unique_cities[:5]

    builder = InlineKeyboardBuilder()
    for item in options:
        city = item["city"]
        region = item["region"]["name"]
        region_id = item["region"]["id"]
        button_text = f"{city['name']} ({region}, {region_id})"
        callback_data = f"choose_city:{city['id']}:{city['name']}:{region_id}"
        builder.button(text=button_text, callback_data=callback_data)

    builder.adjust(1)  # 1 button per row

    await message.answer(
        "✅ Знайдено ось такі населені пункти. Оберіть ваш:",
        reply_markup=builder.as_markup(),
    )

    await state.clear()

    # Show found cities
    cities = [f"🏙 {item['city']['name']} (ID: {item['city']['id']})" for item in unique_cities]
    await message.answer("Знайдені міста:\n" + "\n".join(cities))

    await state.clear()  # Clear state for next steps


@dp.callback_query(F.data.startswith("choose_city:"))
async def choose_city_handler(callback: types.CallbackQuery) -> None:
    if callback.data is None:
        await callback.answer("⚠️ Не вдалося отримати дані callback.", show_alert=True)
        return
    parts = callback.data.split(":")
    city_id = parts[1]
    city_name = parts[2]
    region_id = parts[3]

    if callback.message and isinstance(callback.message, types.Message):
        await callback.message.edit_text(
            f"🏙 Ви обрали місто: <b>{city_name}</b> (ID: {city_id}), (REGION ID: {region_id})"
        )
    await callback.answer()


# --- Main entrypoint ---
async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
