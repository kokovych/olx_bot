# OLX BOT

Start telegram olx bot
Setup your filters
Get all advertisement, get all new advertisement with this filter



1. Install poetry
```
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies and virtualenv creation
```
poetry install
```

3. Activation:
```
poetry env list           # get env NAME
poetry env activate <env NAME>
```

Or with pugin

```
poetry self add poetry-plugin-shell
poetry shell
```


### DATABASE

#### Initial steps for postgres
Open psql in terminal:
```bash
psql postgres
```
Create new database:
```sql
CREATE DATABASE YOUR_DB_NAME_HERE;
```
Create new DB user with password:
```sql
CREATE USER YOUR_USER_HERE WITH PASSWORD 'YOUR_PASSWORD_HERE';
```
Grant all previlegies:
```sql
GRANT ALL PRIVILEGES ON DATABASE YOUR_DB_NAME_HERE TO YOUR_USER_HERE;
```

#### Migration
New DB Migration (Alembic + SQLModel)
1. Install Alembic (if not already):
```sh
poetry add --dev alembic
```

2. Initialize Alembic:
```sh
alembic init alembic
```

3. Set your Postgres connection string in 
alembic.ini:
```sh
sqlalchemy.url = postgresql://user:password@localhost:5432/olx_bot_db
```

4. In `env.py`, import your models and set metadata:
```py
from src.db import SQLModel
target_metadata = SQLModel.metadata
```

5. Create migration:
```sh
alembic revision --autogenerate -m "Your message"
```

6. Apply migration:
```sh
alembic upgrade head
```