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

# --- Load environment variables ---
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


# --- FSM States ---
class SearchStates(StatesGroup):
    waiting_for_category_detail = State()
    waiting_for_city = State()
    waiting_for_currency = State()


# --- Category IDs ---
REAL_ESTATE_BUY_HOUSE = 1602
REAL_ESTATE_BUY_APPARTMENT = 1758

# Currency:
CURRENCY_UAH = "UAH"
CURRENCY_USD = "USD"
CURRENCY_EUR = "EUR"


# --- Persistent menu (bottom keyboard) ---
def get_persistent_menu() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text="/start")]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=False)


# --- Inline main menu (categories) ---
def get_main_menu() -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton(text="🏠 Нерухомість", callback_data="category_real_estate")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# --- /start handler ---
@dp.message(Command("start"))
async def start_handler(message: types.Message) -> None:
    user = message.from_user
    if not user:
        await message.answer("Помилка: не вдалося отримати дані користувача.")
        return

    # Save user in DB
    add_telegram_user(telegram_id=user.id, telegram_username=user.username or "")

    text = (
        f"Привіт, <b>{user.first_name}</b>!\n\n"
        f"Твій ID: <code>{user.id}</code>\n"
        f"Username: @{user.username if user.username else '—'}\n\n"
        "Оберіть категорію для пошуку:"
    )
    await message.answer(text, reply_markup=get_main_menu())
    await message.answer("Меню доступне завжди 👇", reply_markup=get_persistent_menu())


# --- Real estate category handler ---
@dp.callback_query(F.data == "category_real_estate")
async def category_real_estate_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    if not callback.message:
        await callback.answer("Помилка: повідомлення недоступне.", show_alert=True)
        return

    # Show "Buy house / Buy apartment" buttons
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Купити будинок",
        callback_data=f"category_detail:{REAL_ESTATE_BUY_HOUSE}:Купити будинок",
    )
    builder.button(
        text="Купити квартиру",
        callback_data=f"category_detail:{REAL_ESTATE_BUY_APPARTMENT}:Купити квартиру",
    )
    builder.adjust(1)

    if isinstance(callback.message, types.Message):
        await callback.message.edit_text(
            "✅ Ви обрали категорію: Нерухомість\nОберіть тип нерухомості:",
            reply_markup=builder.as_markup(),
        )
    await state.set_state(SearchStates.waiting_for_category_detail)
    await callback.answer()


# --- Handler for real estate detail selection ---
@dp.callback_query(F.data.startswith("category_detail:"))
async def category_detail_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    if not callback.data or not callback.message:
        await callback.answer("Помилка")
        return

    parts = callback.data.split(":")
    category_id = int(parts[1])
    category_name = parts[2]

    # Save category to state
    await state.update_data(category_id=category_id, category_name=category_name)

    if isinstance(callback.message, types.Message):
        await callback.message.edit_text(f"✅ Ви обрали: {category_name}\n\nВведіть назву міста:")
    await state.set_state(SearchStates.waiting_for_city)
    await callback.answer()


# --- Handler for city input ---
@dp.message(SearchStates.waiting_for_city)
async def process_city_input(message: types.Message, state: FSMContext) -> None:
    if not message.text:
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

    unique_cities = remove_duplicate_cities(data["data"])
    options = unique_cities[:5]

    builder = InlineKeyboardBuilder()
    for item in options:
        city = item["city"]
        region = item["region"]["name"]
        region_id = item["region"]["id"]
        callback_data = f"choose_city:{city['id']}:{city['name']}:{region_id}"
        builder.button(text=f"{city['name']} ({region})", callback_data=callback_data)

    builder.adjust(1)
    await message.answer(
        "✅ Знайдено ось такі населені пункти. Оберіть ваш:",
        reply_markup=builder.as_markup(),
    )


# --- Handler for city selection ---
@dp.callback_query(F.data.startswith("choose_city:"))
async def choose_city_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    if not callback.data or not callback.message:
        await callback.answer("Помилка")
        return

    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("Невірні дані", show_alert=True)
        return

    city_id = parts[1]
    city_name = parts[2]
    region_id = parts[3]

    # Save to state
    await state.update_data(city_id=city_id, city_name=city_name, region_id=region_id)

    # Show currency menu
    builder = InlineKeyboardBuilder()
    builder.button(text="USD - Долар США", callback_data=f"currency:{CURRENCY_USD}")
    builder.button(text="UAH - Гривня", callback_data=f"currency:{CURRENCY_UAH}")
    builder.button(text="EUR - Євро", callback_data=f"currency:{CURRENCY_EUR}")
    builder.adjust(1)

    if isinstance(callback.message, types.Message):
        await callback.message.edit_text(
            f"🏙 Ви обрали місто: <b>{city_name}</b>\n\nТепер оберіть валюту:",
            reply_markup=builder.as_markup(),
        )
    await state.set_state(SearchStates.waiting_for_currency)
    await callback.answer()


# --- Currency handler ---
@dp.callback_query(F.data.startswith("currency:"))
async def currency_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    if not callback.data or not callback.message:
        await callback.answer("Помилка")
        return

    currency = callback.data.split(":", 1)[1]
    await state.update_data(currency=currency)

    # Get all data from state
    data = await state.get_data()
    city_id = data.get("city_id")
    city_name = data.get("city_name")
    region_id = data.get("region_id")
    category_id = data.get("category_id")
    category_name = data.get("category_name")

    text = f"🏙 Місто: <b>{city_name}</b> (ID: {city_id}, REG ID: {region_id})\n"
    if category_id and category_name:
        text += f"📌 Категорія: {category_name} (ID: {category_id})\n"
    text += f"💵 Валюта: {currency}"

    if isinstance(callback.message, types.Message):
        await callback.message.edit_text(text)

    await callback.answer()
    await state.clear()


# --- Entrypoint ---
async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
