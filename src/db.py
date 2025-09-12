import logging
import os

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine, select

from models import TelegramUser

# logging configuration:
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_USER_PASSWORD = os.getenv("DB_USER_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

if not DB_USER or not DB_USER_PASSWORD or not DB_NAME:
    raise ValueError(
        "Database configuration is incomplete. Please set DB_USER, DB_USER_PASSWORD, and DB_NAME environment variables."
    )

# Postgres connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_USER_PASSWORD}@localhost:5432/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


# insert data into TelegramUser table:
def add_telegram_user(telegram_id: int, telegram_username: str) -> TelegramUser:
    """
    Add a new Telegram user to the database if they do not already exist.
    """

    with Session(engine) as session:
        statement = select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
        results = session.exec(statement)
        user = results.first()
        if user:
            logging.info(f"User with telegram_id {telegram_id} already exists.")
            return user

        new_user = TelegramUser(telegram_id=telegram_id, telegram_username=telegram_username)
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        logging.info(f"Added new user with telegram_id {telegram_id}.")
        return new_user
