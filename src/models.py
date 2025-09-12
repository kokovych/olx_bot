from sqlmodel import Field, SQLModel


class TelegramUser(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    telegram_id: int
    telegram_username: str
