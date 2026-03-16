
### use pydantic_settings and load all .env variables on startup

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ...

settings = Settings()
```

### avoid ned db connection on every endpoint

```python
async def get_db():
    async with async_session() as session:
        yield session
```


я створив папку database в які потрібно розмістити логіку взаємодії з базами
там має бути визначенно створення сесії з postgres та redis
також там має бути визначенно створення пулу з postgres та redis


Налаштування налаштувань (Settings):

Створи файл app/core/config.py.

Використовуй pydantic-settings (клас Settings(BaseSettings)), щоб зібрати всі змінні середовища (Postgres URL, Redis URL, JWT секрети тощо) в один об'єкт.

Заміни всі виклики os.getenv по всьому проекту на використання об'єкта settings.

Організація папки database:

Створи app/database/session.py для PostgreSQL. Налаштуй там async_engine (з пулом з'єднань) та async_sessionmaker. Реалізуй асинхронну функцію-залежність get_db.

Створи app/database/redis.py для Redis. Налаштуй створення пулу з'єднань через redis.asyncio. Реалізуй функцію або залежність для отримання клієнта Redis.

Lifespan:

Налаштуй ініціалізацію та закриття пулів (Postgres та Redis) у lifespan в main.py, використовуючи створену логіку з папки database.



2. Порядок залежностей (Performance)
Зараз service ініціалізується до того, як перевіряється current_user.

Python
service: BookService = Depends(get_book_service),
current_user: User = Depends(get_current_user),
Якщо токен невалідний, FastAPI спочатку створить підключення до БД для сервісу, а потім викине 401. Краще поставити current_user першим у списку аргументів.

# ---------------------------------
Необхідно додати ендпоінти для генерації access token, та захистити ендпоінти для books з використанням Token-based authentication. Обов'язково використати refresh token flow!

Потрібно реалізувати rate limiter.
Для авторизованих юзерів обмежимо до 10 запитів за хвилину.
Для анонімних юзерів до 2.

допрацювати оновлення токенів refresh tokens

https://docs.secureauth.com/iam/refresh-token-flow

видалити rate_limiter з проєкту, та написати його наново, як middleware\декоратор

мені не подобається що якщо юзер не зареганий то він отримає unauthenticated, а не rate limit exceeded

# ---------------------------------
