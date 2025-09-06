import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

if not API_TOKEN:
    raise ValueError("No API token provided. Please set the API_TOKEN environment variable.")


bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# Обробник команди /start
@dp.message(Command("start"))
async def start_handler(message: types.Message) -> None:
    await message.answer("Hello! I am bot aiogram 3 🚀")


# Ехо для всіх повідомлень
@dp.message()
async def echo_handler(message: types.Message) -> None:
    await message.answer(f"You have just written: {message.text}")


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
