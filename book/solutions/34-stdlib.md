---
chapter: ch-34-stdlib
number: 34
exercise_count: 10
---

# Решения к главе 34

Решения построены вокруг выбора инструмента: почему здесь `Counter`, а не
словарь, почему `deque`, а не список. Сравнивайте не только результат, но и
цену альтернатив.

## 1. Частотный анализ {#sol-ch34-01}

```python exec
from collections import Counter

text = "один два один три два один"
counts = Counter(text.split())
print(counts)
print(counts.most_common(1))
```

```output
Counter({'один': 3, 'два': 2, 'три': 1})
[('один', 3)]
```

`Counter` сам считает вхождения и хранит их в порядке первого появления.
`most_common(1)` возвращает список из одной пары — это удобно, если нужен
именно формат «список самых частых», а не отдельное значение.

## 2. История действий {#sol-ch34-02}

```python exec
from collections import deque

history: deque[str] = deque(maxlen=3)
for command in ["open", "save", "copy", "paste", "undo"]:
    history.append(command)
print(history)
```

```output
deque(['copy', 'paste', 'undo'], maxlen=3)
```

`maxlen=3` автоматически выбрасывает самый старый элемент при добавлении
четвёртого. Список пришлось бы обрезать вручную (`history = history[-3:]`), и
это создавало бы новый список на каждом шаге. `deque` делает ограничение
частью структуры данных, а не обязанностью вызывающего кода.

## 3. Группировка по ключу {#sol-ch34-03}

```python exec
from itertools import groupby

items = [
    ("фрукты", "яблоко"),
    ("овощи", "морковь"),
    ("фрукты", "груша"),
    ("овощи", "свёкла"),
]
ordered = sorted(items, key=lambda pair: pair[0])
for category, group in groupby(ordered, key=lambda pair: pair[0]):
    print(category, [name for _category, name in group])
```

```output
овощи ['морковь', 'свёкла']
фрукты ['яблоко', 'груша']
```

Перед `groupby` данные обязательно сортируют по тому же ключу: функция
группирует только соседние элементы. Без сортировки «фрукты» и «овощи»
чередовались бы, и получилось бы четыре группы вместо двух.

## 4. Пагинация итератора {#sol-ch34-04}

```python exec
from itertools import islice

numbers = range(21)
page_size = 3
page = 2  # вторая страница при нумерации с единицы

start = (page - 1) * page_size
finish = start + page_size
print(list(islice(numbers, start, finish)))
```

```output
[3, 4, 5]
```

`islice` берёт срез итератора, не материализуя его. Для `range` разница
невелика, но для файла или генератора срез списка потребовал бы прочитать всё
в память. Обратите внимание: `range` можно передавать в `islice` повторно,
а одноразовый итератор после первого прохода уже не восстановится.

## 5. Частичное применение {#sol-ch34-05}

```python exec
from functools import partial


def format_price(amount: int, currency: str) -> str:
    return f"{amount:,} {currency}".replace(",", " ")


rubles = partial(format_price, currency="₽")
dollars = partial(format_price, currency="$")
print(rubles(1250))
print(dollars(99))
```

```output
1 250 ₽
99 $
```

`partial` фиксирует именованный аргумент и оставляет свободным первый. Это
читается лучше, чем `lambda amount: format_price(amount, "₽")`, и не создаёт
новую функцию при каждом вызове. Ограничение: `partial` не подменяет имя
функции в traceback так, как это сделал бы `wraps`.

## 6. Пути и расширения {#sol-ch34-06}

```python exec
from pathlib import Path

path = Path("reports") / "2026" / "october.csv"
print(path.stem)
print(path.parent)
print(path.with_suffix(".json"))
```

```output
october
reports/2026
reports/2026/october.json
```

`stem` отбрасывает последнее расширение, `parent` возвращает каталог как
объект `Path`, а `with_suffix` заменяет расширение. Все три операции
кроссплатформенны: разделитель подставляется правильный для системы.

## 7. Статусы заказа {#sol-ch34-07}

```python exec
from enum import Enum


class Status(Enum):
    NEW = "new"
    PAID = "paid"
    SHIPPED = "shipped"
    DONE = "done"


def parse_status(value: str) -> Status:
    return Status(value)


print(parse_status("paid"))
print(parse_status("done").value)
```

```output
Status.PAID
done
```

```python exec expect-error
from enum import Enum


class Status(Enum):
    NEW = "new"
    PAID = "paid"
    SHIPPED = "shipped"
    DONE = "done"


print(Status("unknown"))
```

```output
ValueError: 'unknown' is not a valid Status
```

Конструктор перечисления сам проверяет значение и поднимает `ValueError` с
понятным сообщением. Это готовая валидация на границе: не нужно писать цепочку
`if value == "new": ... elif ...`.

## 8. Контекстный менеджер {#sol-ch34-08}

```python exec
from contextlib import contextmanager


@contextmanager
def capture(log: list[str]):
    log.append("вход")
    try:
        yield log
    finally:
        log.append("выход")


events: list[str] = []
with capture(events):
    events.append("работа")

failed: list[str] = []
try:
    with capture(failed):
        raise RuntimeError("сбой внутри блока")
except RuntimeError:
    pass

print(events)
print(failed)
```

```output
['вход', 'работа', 'выход']
['вход', 'выход']
```

`finally` гарантирует запись «выход» в обоих случаях. Без него исключение
внутри блока оставило бы ресурс в незакрытом состоянии — классическая утечка,
которую контекстный менеджер предотвращает по построению.

## 9. Прогнозирование вывода {#sol-ch34-09}

```python exec
from collections import deque

items = deque([1, 2, 3], maxlen=3)
items.append(4)
items.append(5)
print(items)
```

```output
deque([3, 4, 5], maxlen=3)
```

При добавлении четвёртого элемента выбрасывается `1`, при добавлении
пятого — `2`. В очереди остаются три последних значения. Если бы `maxlen` не
было, `deque` хранил бы все пять.

## 10. Мини-проект: анализ журнала {#sol-ch34-10}

```python exec
from collections import Counter
from enum import Enum


class Level(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


lines = ["INFO старт", "ERROR сбой", "INFO шаг", "ERROR сбой"]
levels: Counter[Level] = Counter()
messages: Counter[str] = Counter()
for line in lines:
    raw_level, message = line.split(" ", 1)
    levels[Level(raw_level)] += 1
    messages[message] += 1

report = {
    "levels": {level.value: count for level, count in levels.items()},
    "top_message": messages.most_common(1)[0][0],
    "top_message_count": messages.most_common(1)[0][1],
}
print(report)
```

```output
{'levels': {'INFO': 2, 'ERROR': 2}, 'top_message': 'сбой', 'top_message_count': 2}
```

`Counter` работает и с членами перечисления: они хешируемы и сравниваются по
идентичности. `Level(raw_level)` заодно проверяет, что уровень известен;
неизвестное значение подняло бы `ValueError`. Отчёт собирается в один словарь —
удобный формат для вывода или сохранения в JSON.

## Ответы на вопросы для самопроверки

1. `Counter` — словарь с методами подсчёта: отсутствующий ключ даёт `0`,
   есть `most_common` и арифметика счётчиков. Он удобнее, когда задача —
   частоты, а не произвольные значения.
2. `deque` добавляет и извлекает с обоих концов за постоянное время, а список
   при удалении из начала сдвигает все элементы.
3. `groupby` группирует соседние элементы, поэтому одинаковые ключи должны
   идти подряд — для этого данные сортируют.
4. Ленивость означает вычисление по требованию: элементы создаются, когда их
   запрашивает потребитель. Это экономит память на больших и бесконечных
   потоках.
5. `partial` фиксирует аргументы явно и переиспользуется; `lambda` тоже
   подходит, но для повторяющейся конфигурации `partial` читается лучше.
6. `Enum` ограничивает набор допустимых значений, проверяет их при создании и
   исключает опечатки, которые проходят со строками.
7. `finally` гарантирует выполнение кода очистки при любом выходе из блока,
   включая исключение.
