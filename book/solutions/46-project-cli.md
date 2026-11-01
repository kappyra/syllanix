---
chapter: ch-46-project-cli
number: 46
exercise_count: 10
---

# Решения к главе 46

## 1. Добавление команды `undone` {#sol-ch46-01}

Изменения по слоям:

- **CLI**: добавить подкоманду `undone` с аргументом `id` и ветку обработки.
- **Сервис**: добавить метод `reopen(task_id)`, который снимает `done` и
  поднимает `KeyError`, если задачи нет.
- **Хранилище**: не меняется — структура данных та же.

```python exec
from dataclasses import dataclass

@dataclass
class Task:
    id: int
    title: str
    done: bool = False

class TaskService:
    def __init__(self, tasks):
        self._tasks = list(tasks)

    def reopen(self, task_id: int) -> Task:
        for task in self._tasks:
            if task.id == task_id:
                task.done = False
                return task
        raise KeyError(f"задача {task_id} не найдена")

service = TaskService([Task(1, "Купить хлеб", done=True), Task(2, "Глава", done=True)])
service.reopen(1)
print(service._tasks[0])
print(service._tasks[1])
```

```output
Task(id=1, title='Купить хлеб', done=False)
Task(id=2, title='Глава', done=True)
```

## 2. Приоритеты {#sol-ch46-02}

Обратная совместимость обеспечивается значением по умолчанию: при чтении
старой записи отсутствующее поле `priority` трактуется как `"normal"`.

```python
from dataclasses import dataclass

VALID = {"low", "normal", "high"}

@dataclass
class Task:
    id: int
    title: str
    done: bool = False
    priority: str = "normal"

def task_from_dict(data: dict) -> Task:
    priority = data.get("priority", "normal")
    if priority not in VALID:
        raise ValueError(f"неизвестный приоритет: {priority}")
    return Task(id=data["id"], title=data["title"], done=data.get("done", False),
                priority=priority)
```

Правило: новые поля добавляются только с безопасным значением по умолчанию;
удаление и переименование полей — ломающее изменение, требующее миграции.

## 3. Поиск {#sol-ch46-03}

Логика поиска — часть предметной области, поэтому живёт в сервисе. CLI только
передаёт подстроку и печатает результат.

```python exec
tasks = ["Купить хлеб", "Написать главу", "Позвонить в банк"]
query = "ХЛЕБ".lower()
found = [title for title in tasks if query in title.lower()]
print(found)
```

```output
['Купить хлеб']
```

## 4. Коды возврата {#sol-ch46-04}

| Команда | Ситуация | Сообщение | Код |
|---|---|---|---|
| `add` | пустое название | `ошибка: название задачи не может быть пустым` | 1 |
| `done` | задача не найдена | `ошибка: задача 99 не найдена` | 1 |
| любой | неизвестная команда | справка argparse | 2 |
| любой | `id` не число | `argument id: invalid int value` | 2 |
| `list` | успех | список задач | 0 |

`2` означает ошибку **вызова** (неверные аргументы), `1` — ошибку **правил**
(вызов корректен, но операция невозможна). Разделение позволяет вызывающему
скрипту понять, нужно ли исправлять команду или данные.

## 5. Атомарность {#sol-ch46-05}

(а) При прямой записи в `tasks.json` система может успеть усечь файл, но не
записать содержимое — останется пустой или частичный файл, и приложение
потеряет данные.

(б) При записи во временный файл с последующей заменой `os.replace` основной
файл в любой момент времени содержит либо старую, либо новую полную версию.
Гарантия: **читатель никогда не видит частично записанный файл**; при сбое
остаётся прежняя версия, а временный файл можно удалить.

Чтобы гарантия сохранялась и при обрыве питания, одного `os.replace`
недостаточно: данные временного файла могут ещё не дойти до диска. Нужны
`fsync` временного файла до замены и `fsync` каталога после неё — тогда новая
версия либо зафиксирована целиком, либо не зафиксирована вовсе. Без `fsync`
атомарность для параллельного читателя остаётся, а долговечность после сбоя
питания — нет.

## 6. Тесты на границы {#sol-ch46-06}

```python
import pytest

from tasks.model import validate_title


@pytest.mark.parametrize("title", ["", "   ", "\n\t"])
def test_empty_titles_rejected(title):
    with pytest.raises(ValueError):
        validate_title(title)


def test_exactly_200_allowed():
    assert len(validate_title("я" * 200)) == 200


def test_201_rejected():
    with pytest.raises(ValueError):
        validate_title("я" * 201)


def test_title_is_trimmed():
    assert validate_title("  задача  ") == "задача"
```

Параметризация через `pytest.mark.parametrize` важна не для краткости: она
показывает, что все варианты проверяются одинаково и ни один не забыт при
добавлении нового случая. Отдельный тест на ровно 200 символов фиксирует
границу «включительно», а тест на 201 — что ограничение действительно
действует. Дополнительные границы: строка из эмодзи (длина считается в
символах Unicode, а не в байтах), строки с `\n` и табуляцией внутри, пустая
строка как аргумент командной строки, максимально длинное название при
экспорте в файл.

## 7. Некорректный JSON {#sol-ch46-07}

Правильное поведение — не падать со стектрейсом и не затирать файл: сообщить
понятную ошибку и код возврата `1`. Данные при этом не перезаписываются.

```python exec
import json

def load_tasks(raw: str) -> list:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"файл задач повреждён: строка {exc.lineno}") from exc
    if not isinstance(data, list):
        raise ValueError("ожидался список задач")
    return data

for raw in ['[{"id": 1}]', '{"id": 1}', 'не json']:
    try:
        print("ok:", load_tasks(raw))
    except ValueError as exc:
        print("ошибка:", exc)
```

```output
ok: [{'id': 1}]
ошибка: ожидался список задач
ошибка: файл задач повреждён: строка 1
```

## 8. Порядок вывода {#sol-ch46-08}

Сортировка — вопрос представления, а не правил хранения, поэтому её место в CLI
(или в отдельной функции форматирования). Сервис должен возвращать задачи в
предсказуемом, но нейтральном порядке.

```python exec
from dataclasses import dataclass

@dataclass
class Task:
    id: int
    title: str
    done: bool

tasks = [Task(3, "третья", True), Task(1, "первая", False), Task(2, "вторая", True)]
ordered = sorted(tasks, key=lambda task: (task.done, task.id))
for task in ordered:
    print(task.id, task.title, "выполнена" if task.done else "не выполнена")
```

```output
1 первая не выполнена
2 вторая выполнена
3 третья выполнена
```

Ключ `(task.done, task.id)` использует `False < True`: сначала невыполненные,
затем выполненные, внутри — по идентификатору.

## 9. Флаг `--json` {#sol-ch46-09}

Машиночитаемый вывод не нужно парсить регулярными выражениями: он стабилен,
корректно экранирует спецсимволы и содержит все поля, включая те, что не
попали в человекочитаемую строку. Человекочитаемый формат при этом можно
менять свободно (добавлять цвета, менять порядок колонок), не ломая интеграции
и скрипты, которые вызывают приложение. Практическое правило: если вывод
предназначен для программы, он должен быть данными, а не текстом для глаз.

```python
import json
from dataclasses import asdict

def render(tasks, as_json: bool) -> str:
    if as_json:
        return json.dumps([asdict(task) for task in tasks], ensure_ascii=False)
    return "\n".join(f"[{'x' if t.done else ' '}] {t.id}. {t.title}" for t in tasks)
```

## 10. Мини-релиз {#sol-ch46-10}

1. Убедиться, что все изменения в `main`, CI зелёный.
2. Обновить версию в `pyproject.toml`: `1.0.0` → `1.1.0`.
3. Добавить запись в `CHANGELOG.md` (разделы «Добавлено», «Исправлено»).
4. Прогнать тесты и проверку типов локально.
5. Создать тег `v1.1.0` и запушить его.
6. Опубликовать артефакт (пакет или сборку) из тега.
7. Создать релиз с описанием изменений.

До публикации зелёными должны быть: тесты, линтер, проверка типов, сборка
пакета. Если хотя бы одно — красное, релиз не выпускается.
