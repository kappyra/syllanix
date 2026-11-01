---
chapter: ch-22-higher-order
number: 22
exercise_count: 10
---

# Решения к главе 22

Ключ к главе — различать саму функцию и её вызов. Как только это различение
становится привычным, замыкания и декораторы перестают выглядеть магией.

## 1. Прогнозирование вывода {#sol-ch22-01}

Первая строка работает: `add_one(add_one(5))` равно `7`. Вторая падает,
потому что `add_one(5)` — уже число, а не функция.

```python exec
def apply_twice(func, value):
    return func(func(value))


def add_one(x):
    return x + 1


print(apply_twice(add_one, 5))
```

```output
7
```

```python exec expect-error
def apply_twice(func, value):
    return func(func(value))


def add_one(x):
    return x + 1


print(apply_twice(add_one(5), 5))
```

```output
TypeError: 'int' object is not callable
```

В функцию высшего порядка передаётся ссылка на функцию (`add_one`), а не
результат её вызова. Скобки означают «вычисли сейчас».

## 2. Функция в словаре {#sol-ch22-02}

```python exec
def greeting(name):
    return "привет, " + name


def farewell(name):
    return "до встречи, " + name


def question(name):
    return name + ", как дела?"


actions = {"приветствие": greeting, "прощание": farewell, "вопрос": question}
for name in ["приветствие", "танец"]:
    action = actions.get(name)
    if action is None:
        print("неизвестное действие:", name)
    else:
        print(action("Анна"))
```

```output
привет, Анна
неизвестное действие: танец
```

`actions.get(name)` возвращает функцию или `None`; проверка `is None` не даёт
вызвать отсутствующее действие. Это простейший диспетчер команд.

## 3. Функция высшего порядка {#sol-ch22-03}

```python exec
def combine(first, second, value):
    return second(first(value))


def double(x):
    return x * 2


def add_one(x):
    return x + 1


print(combine(double, add_one, 5))
print(combine(add_one, double, 5))
```

```output
11
12
```

Порядок применения важен: в первом случае сначала удвоение, потом прибавление
единицы; во втором — наоборот. `combine` не знает, что именно делают функции,
и потому подходит для любой пары.

## 4. Замыкание-умножитель {#sol-ch22-04}

```python exec
def make_adder(amount):
    def add(value):
        return value + amount

    return add


add_ten = make_adder(10)
add_hundred = make_adder(100)
print(add_ten(5), add_hundred(5))
```

```output
15 105
```

Каждый вызов `make_adder` создаёт своё замыкание со своим `amount`. Функции
независимы, потому что захватили разные переменные.

## 5. Счётчик с nonlocal {#sol-ch22-05}

```python exec
def make_counter():
    count = 0

    def step():
        nonlocal count
        count = count + 1
        return count

    return step


first = make_counter()
second = make_counter()
print(first(), first(), second(), first())
```

```output
1 2 1 3
```

Два счётчика независимы: у каждого своя `count`. Четвёртый вызов относится к
первому счётчику и продолжает его последовательность. Без `nonlocal` строка
`count = count + 1` создала бы локальную переменную и программа упала бы с
`UnboundLocalError`.

## 6. Декоратор-логгер {#sol-ch22-06}

```python exec
def log_call(func):
    def wrapper(value):
        print("вызов", func.__name__)
        return func(value)

    return wrapper


@log_call
def greet(name):
    return "привет, " + name


print(greet("Анна"))
```

```output
вызов greet
привет, Анна
```

`@log_call` означает `greet = log_call(greet)`. Перед исходным вызовом
обёртка печатает имя функции, затем возвращает результат.

## 7. wraps на практике {#sol-ch22-07}

```python exec
import functools


def log_plain(func):
    def wrapper(value):
        return func(value)

    return wrapper


def log_wrapped(func):
    @functools.wraps(func)
    def wrapper(value):
        return func(value)

    return wrapper


@log_plain
def greet_plain(name):
    """Возвращает приветствие."""
    return "привет, " + name


@log_wrapped
def greet_wrapped(name):
    """Возвращает приветствие."""
    return "привет, " + name


print(greet_plain.__name__, greet_plain.__doc__)
print(greet_wrapped.__name__, greet_wrapped.__doc__)
```

```output
wrapper None
greet_wrapped Возвращает приветствие.
```

Без `functools.wraps` метаданные обёртки подменяют исходные: имя `wrapper`,
документация `None`. `wraps` копирует `__name__`, `__doc__` и другие атрибуты,
поэтому инструменты отладки видят настоящую функцию.

## 8. Декоратор с параметром {#sol-ch22-08}

```python exec
def repeat(times):
    def decorator(func):
        def wrapper(value):
            result = None
            for _ in range(times):
                result = func(value)
            return result

        return wrapper

    return decorator


@repeat(3)
def shout(text):
    return text + "!"


print(shout("ура"))
```

```output
ура!
```

Здесь три уровня: `repeat(3)` возвращает `decorator`, `decorator` получает
функцию и возвращает `wrapper`. Синтаксис `@repeat(3)` означает
`shout = repeat(3)(shout)`.

## 9. Мини-проект: проверка аргументов {#sol-ch22-09}

```python exec
def require_positive(func):
    def wrapper(value):
        if value <= 0:
            return "ошибка: нужно положительное число"
        return func(value)

    return wrapper


@require_positive
def half(value):
    """Делит число пополам."""
    return value / 2


print(half(10))
print(half(-4))
```

```output
5.0
ошибка: нужно положительное число
```

Обёртка проверяет аргумент до вызова и не пропускает некорректное значение
внутрь. Такой приём называют защитной проверкой аргументов; в реальном коде
вместо строки с сообщением чаще поднимают исключение, но идея та же.

## 10. Замыкание или класс {#sol-ch22-10}

Замыкание:

```python exec
def make_counter():
    count = 0

    def step():
        nonlocal count
        count = count + 1
        return count

    return step


counter = make_counter()
print(counter(), counter())
```

```output
1 2
```

Словарь с состоянием:

```python exec
state = {"count": 0}


def bump():
    state["count"] = state["count"] + 1
    return state["count"]


print(bump(), bump())
```

```output
1 2
```

Для вызывающего кода оба варианта выглядят одинаково: есть функция без
аргументов, которая возвращает следующее число. Разница в том, где хранится
состояние: в замыкании оно спрятано в области видимости и недоступно снаружи,
а в словаре лежит рядом и его может изменить кто угодно. Замыкание удобнее,
когда состояние должно быть защищено и когда счётчиков нужно много: каждый
вызов фабрики даёт независимый счётчик. Словарь удобнее для отладки и для
состояния, которое нужно сохранять и читать в других местах программы.

## Ответы на вопросы для самопроверки

1. Функция — объект: её можно связать с именем, передать аргументом, вернуть
   из функции, положить в список или словарь.
2. `double` — ссылка на функцию, её можно передать и вызвать позже; `double(3)`
   — уже вычисленное значение.
3. Замыкание захватывает имена из объемлющей области; они сохраняются в
   специальной области замыкания и доступны после завершения внешней функции.
4. `nonlocal` разрешает присваивание имени из объемлющей области; без него
   создалась бы локальная переменная и возникла бы ошибка `UnboundLocalError`.
5. Декоратор принимает функцию и возвращает новую с добавленным поведением;
   `@announce` означает `func = announce(func)`.
6. Без `wraps` обёртка теряет имя и документацию исходной функции, что мешает
   отладке и инструментам; `wraps` копирует метаданные.
7. `partial` создаёт обёртку с заранее зафиксированными аргументами, не
   переписывая тело функции; вручную пришлось бы писать новую функцию.
