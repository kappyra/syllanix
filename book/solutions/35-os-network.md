---
chapter: ch-35-os-network
number: 35
exercise_count: 10
---

# Решения к главе 35

Сетевые и процессные вызовы в примерах заменены подготовленными данными или
функциями-заглушками: книга исполняется в песочнице без сети. Показанные
приёмы — таймауты, проверка кодов, разбор URL — применимы к настоящему коду
без изменений.

## 1. Разбор URL {#sol-ch35-01}

```python exec
from urllib.parse import parse_qs, urlparse

url = "https://shop.example.com/catalog/items?category=books&page=3"
parsed = urlparse(url)
print(parsed.scheme)
print(parsed.netloc)
print(parsed.path)
print(parse_qs(parsed.query))
```

```output
https
shop.example.com
/catalog/items
{'category': ['books'], 'page': ['3']}
```

`parse_qs` возвращает словарь списков: параметр может повторяться, например
`?tag=python&tag=book`. Поэтому значение — всегда список, даже если оно одно.

## 2. Сборка параметров {#sol-ch35-02}

```python exec
from urllib.parse import urlencode

params = {"q": "язык python", "limit": 10}
query = urlencode(params)
print(query)
print(query.count("%20") == 0)
```

```output
q=%D1%8F%D0%B7%D1%8B%D0%BA+python&limit=10
True
```

`urlencode` кодирует кириллицу и заменяет пробел на `+` — это допустимая
форма кодирования в строке запроса. Ручная склейка строк потеряла бы пробел и
сломала бы URL: браузер или сервер прочитали бы адрес иначе.

## 3. Пути через os.path {#sol-ch35-03}

```python exec
import os

path = "backups/2026/october.tar.gz"
directory = os.path.dirname(path)
name = os.path.basename(path)
stem, extension = os.path.splitext(name)
rebuilt = os.path.join(directory, name)
print(directory)
print(name)
print((stem, extension))
print(rebuilt)
```

```output
backups/2026
october.tar.gz
('october.tar', '.gz')
backups/2026/october.tar.gz
```

`splitext` отделяет только последнее расширение: для `october.tar.gz` это
`.gz`, а `october.tar` остаётся основой. Если нужны все части архива,
разбирайте имя вручную или используйте `Path.suffixes`.

## 4. Настройки из окружения {#sol-ch35-04}

```python exec
def load_settings(env: dict[str, str]) -> dict[str, object]:
    return {
        "debug": env.get("DEBUG", "0") == "1",
        "port": int(env.get("PORT", "8000")),
        "database_url": env.get("DATABASE_URL", "sqlite:///local.db"),
    }


print(load_settings({}))
print(load_settings({"DEBUG": "1", "PORT": "5432"}))
```

```output
{'debug': False, 'port': 8000, 'database_url': 'sqlite:///local.db'}
{'debug': True, 'port': 5432, 'database_url': 'sqlite:///local.db'}
```

Функция принимает окружение словарём, поэтому её легко проверить без
изменения реальных переменных процесса. В рабочем коде на её месте будет
`os.environ`, а тест подставит свой словарь. Такой приём называется
внедрением зависимости: функция не создаёт зависимость сама, а получает её
снаружи.

## 5. Команда процесса {#sol-ch35-05}

```python
import subprocess


def git_status() -> tuple[int, str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    return result.returncode, result.stdout
```

Аргументы передаются списком, а не одной строкой: программа получает ровно
два аргумента, `status` и `--short`, и ничего лишнего. Если бы путь к файлу
содержал пробел или точку с запятой, он остался бы частью аргумента, а не
командой оболочки. `timeout=10` гарантирует, что зависший `git` не заблокирует
программу навсегда. `check=False` означает, что ненулевой код возврата — не
исключение, а данные: вызывающий код сам решает, как реагировать. В песочнице
этот пример не запускается, потому что запуск процессов запрещён.

## 6. Коды состояния {#sol-ch35-06}

```python exec
def classify(status: int) -> str:
    if not 100 <= status <= 599:
        raise ValueError(f"некорректный код: {status}")
    if 200 <= status < 300:
        return "успех"
    if 300 <= status < 400:
        return "перенаправление"
    if 400 <= status < 500:
        return "ошибка клиента"
    return "ошибка сервера"


for code in (200, 301, 404, 503):
    print(code, classify(code))
```

```output
200 успех
301 перенаправление
404 ошибка клиента
503 ошибка сервера
```

Проверка диапазона 100–599 отсекает бессмысленные значения вроде `42` или
`700`: такой код не может прийти по HTTP. Явная ошибка лучше, чем тихое
отнесение неизвестного кода к «ошибке сервера».

## 7. Клиент API {#sol-ch35-07}

```python exec
import json


def parse_items(payload: str) -> list[dict[str, object]]:
    data = json.loads(payload)
    if not isinstance(data, list):
        raise ValueError("ожидался JSON-массив")
    items: list[dict[str, object]] = []
    for entry in data:
        try:
            items.append(
                {
                    "id": entry["id"],
                    "name": entry["name"],
                    "price": entry["price"],
                }
            )
        except (KeyError, TypeError) as exc:
            raise ValueError(f"в товаре нет обязательного поля: {exc}") from exc
    return items


raw = '[{"id": 1, "name": "чай", "price": 199}, {"id": 2, "name": "кофе", "price": 349}]'
print(parse_items(raw))
```

```output
[{'id': 1, 'name': 'чай', 'price': 199}, {'id': 2, 'name': 'кофе', 'price': 349}]
```

```python exec expect-error
import json


def parse_items(payload: str) -> list[dict[str, object]]:
    data = json.loads(payload)
    if not isinstance(data, list):
        raise ValueError("ожидался JSON-массив")
    items: list[dict[str, object]] = []
    for entry in data:
        try:
            items.append(
                {"id": entry["id"], "name": entry["name"], "price": entry["price"]}
            )
        except (KeyError, TypeError) as exc:
            raise ValueError(f"в товаре нет обязательного поля: {exc}") from exc
    return items


print(parse_items('[{"id": 1, "name": "чай"}]'))
```

```output
ValueError: в товаре нет обязательного поля: 'price'
```

Цепочка исключений (`raise ... from exc`) сохраняет исходную причину: в
traceback видно и `KeyError: 'price'`, и понятное сообщение о недостающем
поле. Это лучше, чем голый `KeyError`, который ничего не говорит о контракте
API.

## 8. Безопасность команды {#sol-ch35-08}

Конструкция `subprocess.run(f"ls {user_input}", shell=True)` передаёт строку
оболочке, а оболочка понимает служебные символы. Если пользователь введёт
`; cat /etc/passwd`, выполнится не только `ls`, но и чтение файла; ввод
`&& rm -rf ~` удалит домашний каталог. Это инъекция команд: данные
пользователя становятся частью программы, которую исполняет система.

Безопасный вариант — без оболочки и со списком аргументов:

```python
import subprocess
import sys


def list_directory(path: str) -> str:
    result = subprocess.run(
        [sys.executable, "-c", "import os,sys; print(os.listdir(sys.argv[1]))", path],
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )
    return result.stdout
```

Здесь значение `path` — отдельный аргумент, а не фрагмент командной строки.
Даже если оно содержит `;` или `&&`, оболочка не участвует и ничего лишнего не
выполнит. Если оболочка действительно нужна, данные экранируют через
`shlex.quote`, но лучший вариант — обойтись без неё.

## 9. Ошибка сети {#sol-ch35-09}

```python exec
from urllib.error import HTTPError, URLError


def safe_get(url: str, opener) -> str:
    try:
        with opener(url, timeout=5) as response:
            return response.read().decode("utf-8")
    except HTTPError as exc:
        return f"HTTP {exc.code}"
    except (URLError, TimeoutError, OSError):
        return "недоступно"


def broken(url: str, timeout: int):
    raise URLError("нет сети")


print(safe_get("https://api.example.com/v1/items", broken))
```

```output
недоступно
```

Параметр `opener` — точка подмены транспорта: в рабочем коде сюда передают
`urlopen`, в тесте — заглушку, поэтому проверка не ходит в сеть. `HTTPError` —
подкласс `URLError`, поэтому его перехватывают первым: иначе код ошибки
потерялся бы и всё превратилось в «недоступно». Перехватывать
`Exception` целиком нельзя: так скрываются ошибки программирования
(`AttributeError`, `TypeError`) и программа продолжает работать в неверном
состоянии. Таймаут указывается в вызове, а не надеждой на удачу.

## 10. Мини-проект: описание клиента {#sol-ch35-10}

Клиент хранит базовый адрес, транспорт и таймаут. Транспорт — функция,
принимающая путь и возвращающая тело ответа; в production это HTTP-клиент, в
тестах — заглушка. Такое разделение позволяет проверить разбор ответов без
сети.

```python exec
import json
from urllib.parse import urljoin


class NoteClient:
    def __init__(self, base_url: str, transport) -> None:
        self.base_url = base_url
        self._transport = transport

    def _request(self, path: str) -> dict[str, object]:
        raw = self._transport(urljoin(self.base_url, path))
        return json.loads(raw)

    def list_notes(self) -> list[dict[str, object]]:
        data = self._request("notes")
        return list(data["items"])

    def get_note(self, note_id: int) -> dict[str, object]:
        return self._request(f"notes/{note_id}")


def fake_transport(url: str) -> str:
    if url.endswith("notes"):
        return '{"items": [{"id": 1, "title": "первая"}]}'
    return '{"id": 2, "title": "вторая"}'


client = NoteClient("https://api.example.com/v1/", fake_transport)
print(client.list_notes())
print(client.get_note(2))
```

```output
[{'id': 1, 'title': 'первая'}]
{'id': 2, 'title': 'вторая'}
```

Контракт клиента: 404 превращается в отдельное исключение «заметка не
найдена», 401 — в «нет доступа», 5xx — в «сервис недоступен». Метод
`create_note` отправляет `POST` с телом и не повторяется автоматически, чтобы
не создать дубликат. Таймаут задаётся в конструкторе и применяется к каждому
запросу. Возвращаемые данные — обычные словари и списки, а не сырой JSON:
вызывающий код не должен знать, как устроен формат ответа.

## Ответы на вопросы для самопроверки

1. `os.path` работает со строками и не создаёт объектов, `pathlib` даёт
   объекты `Path` с методами. В новом коде удобнее `pathlib`, а `os.path`
   встречается в старом коде и сторонних библиотеках.
2. Переменные окружения отделяют конфигурацию от кода: один артефакт
   запускается в разных средах, а секреты не попадают в репозиторий.
3. Без таймаута внешний процесс или сетевой запрос может ждать бесконечно и
   заблокировать программу.
4. `shell=True` передаёт строку оболочке, и данные пользователя могут стать
   командой. Безопасно передавать аргументы списком без оболочки.
5. 2xx — успех; 4xx — ошибка клиента, запрос нужно исправить; 5xx — ошибка
   сервера, возможен повтор позже.
6. Клиент API собирает адреса, заголовки, таймауты и обработку ошибок в одном
   месте, поэтому логика не дублируется и её проще менять.
7. Между проверкой существования и открытием файл может исчезнуть или
   измениться; надёжнее открывать и обрабатывать исключение.
