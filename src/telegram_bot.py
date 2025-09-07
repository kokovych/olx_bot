import asyncio
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

if not API_TOKEN:
    raise ValueError("No API token provided. Please set the API_TOKEN environment variable.")

# Initialize bot and dispatcher
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


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
    await message.answer(text, reply_markup=get_main_menu())

    # Send reply keyboard (always visible)
    await message.answer("Меню доступне завжди 👇", reply_markup=get_persistent_menu())


# --- Callback handler for menu selection ---
@dp.callback_query(F.data == "category_real_estate")
async def category_real_estate_handler(callback: types.CallbackQuery) -> None:
    if callback.message is None or not isinstance(callback.message, types.Message):
        await callback.answer("Помилка: повідомлення недоступне.", show_alert=True)
        return

    await callback.message.edit_text(
        "✅ Ви обрали категорію: <b>Нерухомість</b>\n\n" "Тут можемо продовжувати діалог...",
        reply_markup=None,
    )
    await callback.answer()  # closes the loading animation on the button


# --- Main entrypoint ---
async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
