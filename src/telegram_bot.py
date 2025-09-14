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
    waiting_for_price_from = State()
    waiting_for_price_to = State()


# --- Category IDs ---
REAL_ESTATE_BUY_HOUSE = 1602
REAL_ESTATE_BUY_APPARTMENT = 1758

# --- Currency options ---
CURRENCY_UAH = "UAH"
CURRENCY_USD = "USD"
CURRENCY_EUR = "EUR"

# --- Price options ---
PRICE_FROM_OPTIONS = [
    ("немає", ""),
    ("10 000", "10000"),
    ("20 000", "20000"),
    ("30 000", "30000"),
    ("50 000", "50000"),
    ("100 000", "100000"),
]

PRICE_TO_OPTIONS = [
    ("немає", ""),
    ("30 000", "30000"),
    ("50 000", "50000"),
    ("60 000", "60000"),
    ("70 000", "70000"),
    ("100 000", "100000"),
    ("1 000 000", "1000000"),
]


# --- Persistent menu ---
def get_persistent_menu() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text="/start")]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=False)


# --- Inline main menu ---
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

    # Show category buttons
    builder = InlineKeyboardBuilder()
    builder.button(text="Купити будинок", callback_data=f"category_detail:{REAL_ESTATE_BUY_HOUSE}:Купити будинок")
    builder.button(
        text="Купити квартиру", callback_data=f"category_detail:{REAL_ESTATE_BUY_APPARTMENT}:Купити квартиру"
    )
    builder.adjust(1)

    if isinstance(callback.message, types.Message):
        await callback.message.edit_text(
            "✅ Ви обрали категорію: Нерухомість\nОберіть тип нерухомості:",
            reply_markup=builder.as_markup(),
        )
    await state.set_state(SearchStates.waiting_for_category_detail)
    await callback.answer()


# --- Category detail handler ---
@dp.callback_query(F.data.startswith("category_detail:"))
async def category_detail_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.data is None:
        await callback.answer("⚠️ Не вдалося отримати дані callback.", show_alert=True)
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


# --- City input handler ---
@dp.message(SearchStates.waiting_for_city)
async def process_city_input(message: types.Message, state: FSMContext) -> None:
    if message.text is None:
        await message.answer("⚠️ Не вдалося отримати текст повідомлення.")
        return
    city_name = message.text.strip()
    if len(city_name) < 3:
        await message.answer("⚠️ Введіть щонайменше 3 літери для пошуку міста.")
        return

    # Send temporary "searching city" message
    searching_msg = await message.answer("⏳ Шукаю місто...")

    try:
        data = await get_city_info(city_name)
    except Exception as e:
        await searching_msg.edit_text(f"❌ Помилка при виклику API: {e}")
        return

    if not data.get("data"):
        await searching_msg.edit_text("❌ Місто не знайдено. Спробуйте ще раз.")
        return

    unique_cities = remove_duplicate_cities(data["data"])
    options = unique_cities[:5]

    builder = InlineKeyboardBuilder()
    for item in options:
        city = item["city"]
        region = item["region"]["name"]
        region_id = item["region"]["id"]
        builder.button(
            text=f"{city['name']} ({region})", callback_data=f"choose_city:{city['id']}:{city['name']}:{region_id}"
        )

    builder.adjust(1)
    await searching_msg.edit_text(
        "✅ Знайдено ось такі населені пункти. Оберіть ваш:", reply_markup=builder.as_markup()
    )
    await state.set_state(SearchStates.waiting_for_currency)
    await state.update_data(temp_msg_id=searching_msg.message_id)
    await state.update_data(temp_chat_id=searching_msg.chat.id)


# --- City selection handler ---
@dp.callback_query(F.data.startswith("choose_city:"))
async def choose_city_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.data is None:
        await callback.answer("⚠️ Не вдалося отримати дані callback.", show_alert=True)
        return
    parts = callback.data.split(":")
    city_id = parts[1]
    city_name = parts[2]
    region_id = parts[3]

    # Save city to state
    await state.update_data(city_id=city_id, city_name=city_name, region_id=region_id)

    # Retrieve temporary message
    data = await state.get_data()
    msg_id = data.get("temp_msg_id")
    chat_id = data.get("temp_chat_id")

    # Show currency selection
    builder = InlineKeyboardBuilder()
    builder.button(text="USD - Долар США", callback_data=f"currency:{CURRENCY_USD}")
    builder.button(text="UAH - Гривня", callback_data=f"currency:{CURRENCY_UAH}")
    builder.button(text="EUR - Євро", callback_data=f"currency:{CURRENCY_EUR}")
    builder.adjust(1)

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg_id,
        text=f"✨ Обрані параметри пошуку:\n\n🏙 Місто: <b>{city_name}</b>\n\nТепер оберіть валюту:",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(SearchStates.waiting_for_currency)
    await callback.answer()


# --- Currency handler ---
@dp.callback_query(F.data.startswith("currency:"))
async def currency_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.data is None:
        await callback.answer("⚠️ Не вдалося отримати дані callback.", show_alert=True)
        return
    currency = callback.data.split(":", 1)[1]
    await state.update_data(currency=currency)

    # Retrieve temporary message
    data = await state.get_data()
    msg_id = data.get("temp_msg_id")
    chat_id = data.get("temp_chat_id")

    # Show "price from" selection
    builder = InlineKeyboardBuilder()
    for label, value in PRICE_FROM_OPTIONS:
        builder.button(text=label, callback_data=f"price_from:{value}")
    builder.adjust(2)

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg_id,
        text=f"✨ Обрані параметри пошуку:\n\n💵 Валюта: {currency}\n\nОберіть <b>Ціну від</b>:",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(SearchStates.waiting_for_price_from)
    await callback.answer()


# --- Price from handler ---
@dp.callback_query(F.data.startswith("price_from:"))
async def price_from_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.data is None:
        await callback.answer("⚠️ Не вдалося отримати дані callback.", show_alert=True)
        return
    price_from = callback.data.split(":", 1)[1]
    await state.update_data(price_from=price_from)

    # Retrieve temporary message
    data = await state.get_data()
    msg_id = data.get("temp_msg_id")
    chat_id = data.get("temp_chat_id")

    # Show "price to" selection
    builder = InlineKeyboardBuilder()
    for label, value in PRICE_TO_OPTIONS:
        builder.button(text=label, callback_data=f"price_to:{value}")
    builder.adjust(2)
    price_from = price_from if price_from else "немає"
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg_id,
        text=f"✨ Обрані параметри пошуку:\n\n📈 Ціна від: {price_from}\n\nОберіть <b>Ціну до</b>:",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(SearchStates.waiting_for_price_to)
    await callback.answer()


# --- Price to handler ---
@dp.callback_query(F.data.startswith("price_to:"))
async def price_to_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.data is None:
        await callback.answer("⚠️ Не вдалося отримати дані callback.", show_alert=True)
        return
    price_to = callback.data.split(":", 1)[1]
    await state.update_data(price_to=price_to)

    # Retrieve all data
    data = await state.get_data()
    city_id = data.get("city_id")
    city_name_raw = data.get("city_name")
    city_name: str = city_name_raw if isinstance(city_name_raw, str) and city_name_raw is not None else ""
    region_id = data.get("region_id")
    category_id = data.get("category_id")
    category_name = data.get("category_name")
    currency = data.get("currency")
    price_from = data.get("price_from")
    price_to_val = data.get("price_to")
    price_to_str: str = price_to_val if isinstance(price_to_val, str) and price_to_val is not None else ""
    msg_id = data.get("temp_msg_id")
    chat_id = data.get("temp_chat_id")

    # Show final selected parameters
    text = (
        f"✨ Обрані параметри пошуку:\n\n"
        f"🏙 Місто: <b>{city_name}</b> (ID: {city_id}, REG ID: {region_id})\n"
        f"📌 Категорія: {category_name} (ID: {category_id})\n"
        f"💵 Валюта: {currency}\n"
        f"📈 Ціна від: {price_from if price_from else 'немає'}\n"
        f"📉 Ціна до: {price_to_str if price_to_str else 'немає'}"
    )

    await bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text)
    await state.clear()
    await callback.answer()


# --- Entrypoint ---
async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
