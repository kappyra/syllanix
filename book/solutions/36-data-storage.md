---
chapter: ch-36-data-storage
number: 36
exercise_count: 10
---

# Решения к главе 36

Примеры работают с временной базой в песочнице: каталог исполнения одноразовый,
поэтому файл `app.db` не влияет на другие запуски. В реальном проекте путь к
базе задают явно и не хранят в каталоге с кодом.

## 1. Первая таблица {#sol-ch36-01}

```python exec
import sqlite3

connection = sqlite3.connect("books.db")
connection.execute(
    """
    CREATE TABLE books (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        year INTEGER NOT NULL
    )
    """
)
connection.executemany(
    "INSERT INTO books (title, author, year) VALUES (?, ?, ?)",
    [
        ("Чистый код", "Роберт Мартин", 2008),
        ("Fluent Python", "Лучано Рамальо", 2022),
    ],
)
rows = connection.execute(
    "SELECT id, title, year FROM books ORDER BY year"
).fetchall()
print(rows)
connection.close()
```

```output
[(1, 'Чистый код', 2008), (2, 'Fluent Python', 2022)]
```

`executemany` выполняет один и тот же запрос с разными наборами параметров: это
быстрее и безопаснее, чем собирать `INSERT` строками. `ORDER BY year` задаёт
порядок, не полагаясь на физическое расположение строк.

## 2. Выборка с условием {#sol-ch36-02}

```python exec
import sqlite3

connection = sqlite3.connect("books.db")
connection.execute(
    "CREATE TABLE books (id INTEGER PRIMARY KEY, title TEXT NOT NULL, year INTEGER NOT NULL)"
)
connection.executemany(
    "INSERT INTO books (title, year) VALUES (?, ?)",
    [("Книга A", 2019), ("Книга B", 2021), ("Книга C", 2024)],
)
rows = connection.execute(
    "SELECT title FROM books WHERE year > ? ORDER BY year", (2020,)
).fetchall()
print(rows)
connection.close()
```

```output
[('Книга B',), ('Книга C',)]
```

Год передаётся параметром, потому что это данные, а не часть структуры
запроса. f-строка сработала бы в этом примере, но при первом же значении из
пользовательского ввода появилась бы возможность инъекции. Привычка
параметризовать всё дешевле, чем вспоминать об этом в спешке.

## 3. Обновление и удаление {#sol-ch36-03}

```python exec
import sqlite3

connection = sqlite3.connect("app.db")
connection.execute(
    "CREATE TABLE books (id INTEGER PRIMARY KEY, title TEXT NOT NULL, year INTEGER NOT NULL)"
)
connection.executemany(
    "INSERT INTO books (title, year) VALUES (?, ?)",
    [("Книга A", 2019), ("Книга B", 2021)],
)
with connection:
    connection.execute("UPDATE books SET year = ? WHERE title = ?", (2020, "Книга A"))
    connection.execute("DELETE FROM books WHERE title = ?", ("Книга B",))
print(connection.execute("SELECT title, year FROM books").fetchall())
connection.close()
```

```output
[('Книга A', 2020)]
```

Оба изменения объединены в транзакцию: если второе не выполнится, первое тоже
откатится. Для пары «логически связанных» изменений это правильно; для
независимых операций транзакции можно разделить, чтобы не держать блокировку
дольше нужного.

## 4. Откат транзакции {#sol-ch36-04}

```python exec
import sqlite3

connection = sqlite3.connect(":memory:")
connection.execute("CREATE TABLE accounts (name TEXT, balance INTEGER)")
connection.executemany(
    "INSERT INTO accounts VALUES (?, ?)", [("Аня", 100), ("Борис", 50)]
)
connection.commit()

try:
    with connection:
        connection.execute("UPDATE accounts SET balance = balance - 40 WHERE name = 'Аня'")
        connection.execute("UPDATE accounts SET balance = balance + 40 WHERE name = 'Борис'")
        raise RuntimeError("сбой")
except RuntimeError:
    pass

print(connection.execute("SELECT name, balance FROM accounts ORDER BY name").fetchall())

with connection:
    connection.execute("UPDATE accounts SET balance = balance - 40 WHERE name = 'Аня'")
    connection.execute("UPDATE accounts SET balance = balance + 40 WHERE name = 'Борис'")

print(connection.execute("SELECT name, balance FROM accounts ORDER BY name").fetchall())
connection.close()
```

```output
[('Аня', 100), ('Борис', 50)]
[('Аня', 60), ('Борис', 90)]
```

Первый блок откатился: исключение внутри `with` отменило обе операции. Второй
зафиксировался: балансы изменились согласованно. Сумма по счетам сохраняется в
обоих случаях — это признак корректной транзакции.

## 5. Анализ инъекции {#sol-ch36-05}

```python exec
import sqlite3

connection = sqlite3.connect(":memory:")
connection.execute("CREATE TABLE users (name TEXT)")
connection.executemany("INSERT INTO users VALUES (?)", [("Аня",), ("Борис",)])

name = "' OR '1'='1"
unsafe = f"SELECT * FROM users WHERE name = '{name}'"
print(connection.execute(unsafe).fetchall())
print(connection.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchall())
connection.close()
```

```output
[('Аня',), ('Борис',)]
[]
```

В небезопасном варианте ввод закрыл кавычку и добавил условие `OR '1'='1`,
которое истинно для каждой строки. Безопасный вариант передаёт строку целиком
как значение: база ищет пользователя с таким именем и не находит. Опасность
зависит от контекста: в `SELECT` это утечка данных, в `DELETE` или `UPDATE` —
изменение чужих записей. Поэтому параметризация нужна везде, а не только в
«важных» запросах.

## 6. Агрегаты {#sol-ch36-06}

```python exec
import sqlite3

connection = sqlite3.connect(":memory:")
connection.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, amount INTEGER)")
connection.executemany(
    "INSERT INTO orders (amount) VALUES (?)", [(100,), (250,), (50,)]
)
row = connection.execute(
    "SELECT COUNT(*), SUM(amount), AVG(amount) FROM orders"
).fetchone()
print(row)

connection.execute("DELETE FROM orders")
empty = connection.execute(
    "SELECT COUNT(*), SUM(amount), AVG(amount) FROM orders"
).fetchone()
print(empty)
connection.close()
```

```output
(3, 400, 133.33333333333334)
(0, None, None)
```

`COUNT(*)` на пустой таблице возвращает `0`, а `SUM` и `AVG` — `NULL`
(`None` в Python): складывать нечего. Код должен обрабатывать `None` явно,
иначе арифметика с результатом упадёт с `TypeError`. Деньги в реальной базе
хранят целыми копейками: среднее `133.33` рубля в вещественном типе копится с
погрешностью.

## 7. Связь двух таблиц {#sol-ch36-07}

```python exec
import sqlite3

connection = sqlite3.connect(":memory:")
connection.execute("PRAGMA foreign_keys = ON")
connection.execute("CREATE TABLE authors (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
connection.execute(
    """
    CREATE TABLE books (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        author_id INTEGER NOT NULL REFERENCES authors(id)
    )
    """
)
connection.execute("INSERT INTO authors (name) VALUES (?)", ("Аня",))
connection.execute("INSERT INTO authors (name) VALUES (?)", ("Борис",))
connection.executemany(
    "INSERT INTO books (title, author_id) VALUES (?, ?)",
    [("Книга A", 1), ("Книга B", 2)],
)
rows = connection.execute(
    """
    SELECT books.title, authors.name
    FROM books
    JOIN authors ON authors.id = books.author_id
    ORDER BY books.title
    """
).fetchall()
print(rows)
connection.close()
```

```output
[('Книга A', 'Аня'), ('Книга B', 'Борис')]
```

Внешний ключ `author_id REFERENCES authors(id)` связывает строку книги с
автором. `JOIN` соединяет таблицы по условию и возвращает обогащённый
результат. SQLite по умолчанию не проверяет внешние ключи; `PRAGMA
foreign_keys = ON` включает проверку — её стоит включать в начале соединения.

## 8. JSON в базе {#sol-ch36-08}

```python exec
import json
import sqlite3

connection = sqlite3.connect(":memory:")
connection.execute("CREATE TABLE settings (user TEXT PRIMARY KEY, data TEXT NOT NULL)")
settings = {"theme": "dark", "language": "ru", "notifications": ["email", "sms"]}
connection.execute(
    "INSERT INTO settings (user, data) VALUES (?, ?)",
    ("anya", json.dumps(settings, ensure_ascii=False)),
)
raw = connection.execute(
    "SELECT data FROM settings WHERE user = ?", ("anya",)
).fetchone()[0]
print(json.loads(raw))
connection.close()
```

```output
{'theme': 'dark', 'language': 'ru', 'notifications': ['email', 'sms']}
```

JSON-столбец уместен для необязательных, редко запрашиваемых настроек: схема
не разрастается, формат гибкий. Но искать по такому столбцу неудобно: SQL не
умеет индексировать вложенные ключи без специальных расширений. Если поле
участвует в фильтрах и отчётах, ему место в отдельном столбце.

## 9. Жизненный цикл соединения {#sol-ch36-09}

`with sqlite3.connect(...)` вызывает у соединения `__enter__` и `__exit__`,
которые управляют транзакцией: фиксируют её при успехе и откатывают при
исключении. Метод `close` при этом не вызывается — соединение остаётся
открытым, и файл базы может удерживаться процессом. Для детерминированного
закрытия используют `contextlib.closing`.

```python exec
from contextlib import closing
import pathlib
import sqlite3

path = pathlib.Path("app.db")
with closing(sqlite3.connect(path)) as connection:
    with connection:
        connection.execute("CREATE TABLE IF NOT EXISTS t (x INTEGER)")
        connection.execute("INSERT INTO t VALUES (?)", (1,))

with closing(sqlite3.connect(path)) as connection:
    print(connection.execute("SELECT COUNT(*) FROM t").fetchone()[0])
print("файл можно открыть повторно")
```

```output
1
файл можно открыть повторно
```

Повторное открытие после закрытия — практическая проверка: если соединение не
закрыто, на некоторых системах файл остаётся заблокированным. В больших
приложениях соединениями управляет пул, но правило «освобождай ресурс явно»
остаётся тем же.

## 10. Мини-проект: хранилище заметок {#sol-ch36-10}

```python exec
import sqlite3


def open_db(path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    connection.commit()
    return connection


def add(connection: sqlite3.Connection, title: str) -> int:
    if not title.strip():
        raise ValueError("заголовок не может быть пустым")
    with connection:
        cursor = connection.execute(
            "INSERT INTO notes (title) VALUES (?)", (title.strip(),)
        )
    return int(cursor.lastrowid)


def list_notes(connection: sqlite3.Connection) -> list[dict[str, object]]:
    rows = connection.execute("SELECT id, title, done FROM notes ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def mark_done(connection: sqlite3.Connection, note_id: int) -> bool:
    with connection:
        cursor = connection.execute(
            "UPDATE notes SET done = 1 WHERE id = ?", (note_id,)
        )
    return cursor.rowcount > 0


connection = open_db("notes.db")
first = add(connection, "купить хлеб")
second = add(connection, "позвонить")
print(mark_done(connection, first))
print(mark_done(connection, 999))
print(list_notes(connection))
connection.close()
```

```output
True
False
[{'id': 1, 'title': 'купить хлеб', 'done': 1}, {'id': 2, 'title': 'позвонить', 'done': 0}]
```

`row_factory = sqlite3.Row` позволяет обращаться к столбцам по имени и
превращать строку в словарь. `cursor.rowcount` показывает, сколько строк
изменилось: по нему видно, существовала ли заметка. Проверка пустого
заголовка стоит до запроса, чтобы не писать бессмыслицу в базу. Все изменения
идут через транзакции, а соединение закрывается в конце явно.

## Ответы на вопросы для самопроверки

1. Таблица — набор строк с фиксированными столбцами; строка описывает один
   объект, столбец — одно свойство всех объектов.
2. `PRIMARY KEY` однозначно идентифицирует строку, `NOT NULL` не даёт
   записать отсутствующее значение; это ограничения целостности.
3. Параметры передаются отдельно от текста, поэтому база не интерпретирует их
   как SQL; f-строка делает ввод частью запроса.
4. Транзакция применяет группу изменений целиком или не применяет вовсе, что и
   означает атомарность.
5. `with sqlite3.connect(...)` управляет транзакцией, а `closing(...)`
   гарантирует закрытие соединения.
6. JSON — вложенные структуры, CSV — плоские таблицы, база — запросы,
   обновления и связи.
7. ORM избавляет от ручного SQL в типовых операциях, но скрывает запросы;
   SQL нужен для сложных выборок и понимания того, что ORM делает.
