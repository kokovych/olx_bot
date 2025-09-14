import enum

from sqlmodel import Column, Enum, Field, SQLModel


class TelegramUser(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    telegram_id: int
    telegram_username: str


class CurrencyEnum(str, enum.Enum):
    USD = "USD"
    UAH = "UAH"
    EUR = "EUR"


class SearchFilter(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    filter_name: str
    category_id: int
    city_id: int
    region_id: int
    currency: CurrencyEnum = Field(sa_column=Column(Enum(CurrencyEnum)), default=CurrencyEnum.USD)
    price_from: int | None = Field(default=None)
    price_to: int | None = Field(default=None)


class UserSearchFilters(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int
    search_filter_id: int
