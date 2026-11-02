---
chapter: ch-47-project-api
number: 47
exercise_count: 10
---

# Решения к главе 47

## 1. Контракт API {#sol-ch47-01}

| Метод | Путь | Успех | Ошибки |
|---|---|---|---|
| `GET` | `/notes` | `200` + массив | `500` |
| `POST` | `/notes` | `201` + объект | `400`, `500` |
| `GET` | `/notes/{id}` | `200` + объект | `404`, `500` |
| `PATCH` | `/notes/{id}` | `200` + объект | `400`, `404` |
| `DELETE` | `/notes/{id}` | `204` | `404` |

Формат ошибки: `{"error": "..."}`.

`/notes/3` лучше `/notes?id=3`, потому что `id` — часть адреса ресурса, а не
параметр фильтрации. Адрес ресурса стабилен, его можно кэшировать, на него
можно ссылаться; параметры запроса естественно использовать для фильтрации,
сортировки и пагинации списка.

## 2. Валидация {#sol-ch47-02}

```python exec
class ValidationError(Exception):
    pass

VALID_PRIORITIES = {"low", "normal", "high"}

def parse_priority(data: dict) -> str:
    priority = data.get("priority", "normal")
    if priority not in VALID_PRIORITIES:
        raise ValidationError(
            "поле priority должно быть одним из: low, normal, high"
        )
    return priority

for payload in ({"title": "x"}, {"title": "x", "priority": "high"},
                {"title": "x", "priority": "urgent"}):
    try:
        print(payload, "->", parse_priority(payload))
    except ValidationError as exc:
        print(payload, "-> 400:", exc)
```

```output
{'title': 'x'} -> normal
{'title': 'x', 'priority': 'high'} -> high
{'title': 'x', 'priority': 'urgent'} -> 400: поле priority должно быть одним из: low, normal, high
```

Значение по умолчанию — `normal`: оно сохраняет обратную совместимость со
старыми клиентами, которые ещё не присылают поле. При неверном значении —
`400` (ошибка клиента), а не `500`.

## 3. Коды состояния {#sol-ch47-03}

(а) `201 Created`; (б) `404 Not Found`; (в) `400 Bad Request`;
(г) `503 Service Unavailable` (или `500`, если сбой не связан с доступностью
зависимости); (д) `204 No Content`.

Коды `4xx` означают, что клиент может исправить запрос и повторить; `5xx` —
что проблема на стороне сервера и клиент бессилен. Мониторинг обычно считает
долю `5xx`: именно она сигнализирует о деградации сервиса.

## 4. SQL-инъекция {#sol-ch47-04}

Конкатенация вставляет пользовательский текст прямо в SQL и открывает
возможность SQL-инъекции. В этом примере драйвер `sqlite3.execute()` отклонит
попытку выполнить несколько операторов за один вызов; это **не делает**
конкатенацию SQL безопасной. Другие запросы и драйверы могут вести себя иначе.

```python exec
import sqlite3
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp_dir:
    conn = sqlite3.connect(Path(tmp_dir) / "db.sqlite")
    conn.execute("CREATE TABLE tasks (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
    conn.execute("INSERT INTO tasks (title) VALUES (?)", ("легитимная",))
    malicious = "'; DROP TABLE tasks; --"
    try:
        conn.execute("SELECT * FROM tasks WHERE title = '" + malicious + "'")
    except sqlite3.ProgrammingError:
        print("драйвер отказался выполнять несколько операторов")
    rows = conn.execute("SELECT title FROM tasks WHERE title = ?", (malicious,)).fetchall()
    print("параметризация: найдено строк:", len(rows))
    remaining = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    print("строк в таблице после попытки:", remaining)
    conn.close()
```

```output
драйвер отказался выполнять несколько операторов
параметризация: найдено строк: 0
строк в таблице после попытки: 1
```

Драйвер `sqlite3` отказался выполнять несколько операторов в одном вызове —
это защита «в глубину», на которую нельзя рассчитывать как на основную. Другие
СУБД и конфигурации таких ограничений не имеют, поэтому конкатенация остаётся
уязвимой. Параметризация передаёт значение отдельно от текста запроса, и оно
никогда не интерпретируется как SQL-код. Это единственный правильный способ
подстановки данных.

## 5. Транзакции {#sol-ch47-05}

Без транзакции первая запись останется в базе, а вторая — нет: получится
задача без записи в истории, то есть противоречивое состояние. Решение —
обернуть обе операции в транзакцию: либо применяются обе, либо ни одной.

```python exec
import sqlite3
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp_dir:
    conn = sqlite3.connect(Path(tmp_dir) / "db.sqlite")
    conn.execute("CREATE TABLE tasks (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
    conn.execute("CREATE TABLE history (id INTEGER PRIMARY KEY, event TEXT NOT NULL)")
    try:
        with conn:
            cursor = conn.execute("INSERT INTO tasks (title) VALUES (?)", ("задача",))
            # имитируем сбой второй операции
            raise RuntimeError("сбой после первой записи")
    except RuntimeError as exc:
        print("сбой:", exc)
    print("задач в базе:", conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0])
    conn.close()
```

```output
сбой: сбой после первой записи
задач в базе: 0
```

Внутри `with conn:` при исключении выполняется откат, поэтому частичных
изменений не остаётся.

## 6. Тесты ошибок {#sol-ch47-06}

```python
import os

os.environ["TASKS_DB"] = ":memory:"

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


@pytest.mark.parametrize("payload", [{"title": ""}, {"title": "   "}, {}])
def test_invalid_title(payload):
    assert client.post("/tasks", json=payload).status_code == 422


def test_too_long_title():
    assert client.post("/tasks", json={"title": "я" * 201}).status_code == 422


def test_unknown_id():
    assert client.get("/tasks/999999").status_code == 404


def test_broken_json():
    response = client.post("/tasks", content=b"{oops",
                           headers={"Content-Type": "application/json"})
    assert response.status_code == 422
```

Фреймворк возвращает `422 Unprocessable Entity` для семантически неверного
тела; `400` обычно оставляют для ошибок формата. Главное — код должен быть
согласован по всему API. Тесты важны не только для успешных сценариев: именно
проверки ошибок фиксируют контракт, на который рассчитывают клиенты. Если
завтра обработчик начнёт возвращать `500` вместо `404`, тест поймает это до
выпуска. Обратите внимание на параметризацию: один тест покрывает три варианта
неверного `title`, и при добавлении нового варианта достаточно дописать строку
в список, а не копировать тест.

## 7. Ограничение размера {#sol-ch47-07}

Проверять `Content-Length` до чтения тела и отклонять запрос с кодом
`413 Payload Too Large`:

```python
MAX_BODY = 64 * 1024

length = int(self.headers.get("Content-Length", "0"))
if length > MAX_BODY:
    self._send_json(413, {"error": "тело запроса слишком велико"})
    return
```

Лимит защищает память и время обработки. Дополнительно полезно ограничивать
длину отдельных полей (как `title` в 200 символов).

## 8. Ошибки без утечек {#sol-ch47-08}

В лог записывается полная информация: тип исключения, трассировка, идентификатор
запроса, параметры (без секретов). Клиенту возвращается нейтральное сообщение и
код `500`:

```python
try:
    task = repository.get(task_id)
except DatabaseError:
    logger.exception("ошибка базы при получении задачи %s", task_id)
    raise HTTPException(status_code=500, detail="внутренняя ошибка сервера")
```

Возвращать текст исключения нельзя: он раскрывает структуру таблиц, пути
файлов и версии библиотек, что помогает атакующему. Кроме того, текст
исключения может содержать пользовательские данные.

## 9. Пагинация {#sol-ch47-09}

```python
DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def list_tasks(limit: int = DEFAULT_LIMIT, offset: int = 0) -> list[dict]:
    if limit < 1 or limit > MAX_LIMIT:
        raise ValueError(f"limit должен быть от 1 до {MAX_LIMIT}")
    if offset < 0:
        raise ValueError("offset не может быть отрицательным")
    rows = conn.execute(
        "SELECT id, title, done FROM tasks ORDER BY id LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    return [dict(row) for row in rows]
```

Значения по умолчанию `20` и `0` разумны: клиент получает страницу без
параметров. Максимум `100` обязателен — иначе `limit=1000000` превращается в
отказ в обслуживании. Ответ полезно дополнять общим количеством записей.

## 10. Мини-релиз API {#sol-ch47-10}

1. Все тесты и проверки зелёные локально и в CI.
2. Миграции базы данных готовы и проверены на копии данных.
3. Конфигурация (адрес, порт, лимиты, секреты) вынесена в окружение.
4. Метрики и оповещения настроены до выпуска, а не после аварии.
5. План отката: артефакт предыдущей версии доступен, миграции совместимы.
6. Обновлён журнал изменений, версия зафиксирована в `pyproject.toml`.
7. Выпуск поэтапный (например, канареечный): доля трафика растёт по мере
   подтверждения стабильности.

До публикации должно быть зелёным: тесты, линтер, проверка типов, сборка
артефакта и успешный прогон миграций на копии.
