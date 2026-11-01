---
chapter: ch-31-typing
number: 31
exercise_count: 10
---

# Решения к главе 31

Решения показывают не только результат, но и рассуждение: что обещает
аннотация, где проходит граница статической проверки и что происходит при
запуске. Сначала попробуйте сами, затем сравните.

## 1. Аннотации простой функции {#sol-ch31-01}

```python exec
def mean(a: float, b: float) -> float:
    return (a + b) / 2


print(mean(3, 4))
print(mean.__annotations__)
```

```output
3.5
{'a': <class 'float'>, 'b': <class 'float'>, 'return': <class 'float'>}
```

В словаре `__annotations__` лежат объекты типов: `float` для параметров и для
результата. Аннотация `-> float` описывает ожидание, но не мешает вернуть
другое значение — за это отвечает уже mypy.

## 2. Прогнозирование вывода {#sol-ch31-02}

Первая строка выводит `дада`. Вторая строка завершается ошибкой: строку
нельзя умножить на строку.

```python exec
def repeat(text: str, times: int) -> str:
    return text * times


print(repeat("да", 2))
```

```output
дада
```

```python exec expect-error
def repeat(text: str, times: int) -> str:
    return text * times


print(repeat("да", "2"))
```

```output
TypeError: can't multiply sequence by non-int of type 'str'
```

mypy поймал бы это до запуска: `Argument 2 to "repeat" has incompatible type
"str"; expected "int"  [arg-type]`. Обратите внимание: аннотации при запуске
не сверяются, поэтому ошибка возникла только на конкретном вызове.

## 3. Исправление Optional {#sol-ch31-03}

```python exec
config = {"level": "warning"}
level: str | None = config.get("level")
print(level.upper() if level is not None else "INFO")

empty: dict[str, str] = {}
missing: str | None = empty.get("level")
print(missing.upper() if missing is not None else "INFO")
```

```output
WARNING
INFO
```

`dict.get` возвращает `str | None`, поэтому после проверки `is not None`
анализатор сужает тип до `str` и разрешает вызвать `.upper()`. Без проверки
второй вызов упал бы с `AttributeError: 'NoneType' object has no attribute
'upper'`.

## 4. Объединение типов {#sol-ch31-04}

```python exec
def describe(value: int | str | None) -> str:
    if value is None:
        return "пусто"
    if isinstance(value, str):
        return f"строка: {value}"
    return f"число: {value}"


print(describe(None))
print(describe("кот"))
print(describe(42))
```

```output
пусто
строка: кот
число: 42
```

Порядок проверок важен: `None` проверяется первым, потому что `isinstance`
для него дал бы `False` в обеих ветках. После двух проверок остаётся только
`int`, поэтому в последней строке не нужен дополнительный `isinstance`.

## 5. Обобщённый минимум {#sol-ch31-05}

```python exec
from typing import TypeVar

T = TypeVar("T")


def smallest(items: list[T]) -> T:
    ordered = sorted(items)
    return ordered[0]


print(smallest([3, 1, 2]))
print(smallest(["манго", "авокадо", "банан"]))
```

```output
1
авокадо
```

`TypeVar` связывает тип элемента списка с типом результата: для `list[int]`
результат `int`, для `list[str]` — `str`. Сортировка копии не меняет исходный
список; это важно, потому что мутация аргумента — неожиданный побочный эффект
для функции с таким названием.

## 6. mypy по описанию {#sol-ch31-06}

В исходном коде три ошибки:

1. `total(["10", "20"])` — аргумент `list[str]` вместо `list[float]`
   (`arg-type`).
2. `label("три")` — аргумент `str` вместо `int` (`arg-type`).
3. `return count` в `label` — возвращается `int`, а обещан `str`
   (`return-value`).

Исправленный вариант:

```python exec
def total(prices: list[float]) -> float:
    return sum(prices)


def label(count: int) -> str:
    return f"количество: {count}"


print(total([10.0, 20.0]))
print(label(3))
```

```output
30.0
количество: 3
```

Заметьте: внутри тела типы уже выведены, а аннотации на границах `total` и
`label` фиксируют контракт, который проверяет mypy; дублировать типы в каждой
строке тела не нужно — читателю важнее сигнатура.

## 7. Сужение типа {#sol-ch31-07}

```python exec
def length(value: list[int] | str | None) -> int:
    if value is None:
        return 0
    return len(value)


print(length(None))
print(length("кот"))
print(length([1, 2, 3]))
```

```output
0
3
3
```

Ранний возврат убирает `None` из типа, после чего `len` применима и к строке,
и к списку: обе ветки объединения поддерживают длину. Анализатор видит это без
дополнительных проверок.

## 8. Проверка на границе {#sol-ch31-08}

```python exec
def parse_age(raw: object) -> int:
    if isinstance(raw, bool):
        raise TypeError("возраст не может быть логическим значением")
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        try:
            return int(raw)
        except ValueError as exc:
            raise TypeError("возраст должен быть числом") from exc
    raise TypeError(f"неподдерживаемый тип: {type(raw).__name__}")


print(parse_age(30))
print(parse_age("41"))
```

```output
30
41
```

```python exec expect-error
def parse_age(raw: object) -> int:
    if isinstance(raw, bool):
        raise TypeError("возраст не может быть логическим значением")
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        try:
            return int(raw)
        except ValueError as exc:
            raise TypeError("возраст должен быть числом") from exc
    raise TypeError(f"неподдерживаемый тип: {type(raw).__name__}")


print(parse_age(3.5))
```

```output
TypeError: неподдерживаемый тип: float
```

Проверка `bool` стоит первой: в Python `bool` — подкласс `int`, поэтому без
неё `True` прошёл бы как возраст `1`. Аннотация `object` честно говорит, что
на границе тип неизвестен, а проверки сужают его постепенно.

## 9. Аннотации и реальность {#sol-ch31-09}

Код не падает: f-строка `f"#{value}"` принимает объект любого типа,
преобразует его в текст и печатает `#десять`. Аннотация `value: int` остаётся
обещанием, а не ограничением: интерпретатор не сверяет аргументы с
аннотациями при вызове и проверку не выполняет. mypy, разбирая код без
запуска, видит, что в `tag` передаётся `str`, и сообщает `Argument 1 to "tag"
has incompatible type "str"; expected "int"  [arg-type]`. Опасность именно в
том, что программа «работает»: результат выглядит правдоподобно, и нарушение
контракта обнаружится позже, когда значение начнут использовать как число.
Разница принципиальна: анализатор находит несоответствие типов до исполнения,
а интерпретатор молчит, пока конкретные данные случайно не приведут к сбою.
Именно поэтому статическую проверку запускают в CI, а не полагаются на «код
же работает у меня».

## 10. Мини-проект: контракт функции {#sol-ch31-10}

Контракт: `price` — неотрицательная цена; `percent` — скидка от 0 до 100
включительно; `minimum` — минимальная итоговая цена, задаётся только по имени
(параметр после `*`). При отрицательной цене или проценте вне диапазона
поднимается `ValueError`: это ошибка вызывающего кода, а не сбой программы.
Если скидка больше 100 %, процент отклоняется; результат никогда не ниже
`minimum`, поэтому итог не бывает отрицательным.

```python exec
def apply_discount(price: float, percent: float, *, minimum: float = 0.0) -> float:
    if price < 0:
        raise ValueError("цена не может быть отрицательной")
    if not 0 <= percent <= 100:
        raise ValueError("процент должен быть в диапазоне 0..100")
    return max(price * (1 - percent / 100), minimum)


print(apply_discount(1000.0, 10))
print(apply_discount(100.0, 90, minimum=25.0))
```

```output
900.0
25.0
```

```python exec expect-error
def apply_discount(price: float, percent: float, *, minimum: float = 0.0) -> float:
    if price < 0:
        raise ValueError("цена не может быть отрицательной")
    if not 0 <= percent <= 100:
        raise ValueError("процент должен быть в диапазоне 0..100")
    return max(price * (1 - percent / 100), minimum)


print(apply_discount(-10.0, 5))
```

```output
ValueError: цена не может быть отрицательной
```

## Ответы на вопросы для самопроверки

1. Аннотация — синтаксическая запись типа рядом с именем; аннотация типа —
   указание ожидаемого типа для статических анализаторов. Первое существует
   как объект в `__annotations__`, второе проверяется инструментом.
2. mypy читает код, выводит типы и сверяет их с обещаниями, не исполняя
   программу. Значения, данные извне и ветки исполнения он не проверяет,
   поэтому тесты остаются нужны.
3. `str | None` включает `None`, поэтому перед строковой операцией нужно
   исключить `None`; у `str` такой возможности нет.
4. `TypeVar` сохраняет связь между типами входа и выхода: `list[object] ->
   object` теряет информацию о том, что вернулось ровно то же, что лежало
   внутри.
5. Строки появляются при отложенных аннотациях и явных строковых аннотациях;
   `get_type_hints` разрешает их в объекты типов.
6. «Не проверяется» означает, что механизма проверки нет; «невозможна» было
   бы слишком сильным утверждением — проверку можно сделать вручную через
   `isinstance`.
7. Такой программист думает, что `Optional` делает аргумент необязательным,
   и забывает либо значение по умолчанию, либо обработку `None`.
