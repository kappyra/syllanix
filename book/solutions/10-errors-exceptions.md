---
chapter: ch-10-errors-exceptions
number: 10
exercise_count: 10
---

# Решения к главе 10

Сначала попробуйте ответить сами: обработку ошибок понимают не по тексту, а
по поведению кода в неудачном сценарии. Затем сверьтесь с разбором.

## 1. Порядок вывода {#sol-ch10-01}

```python exec
def check(value):
    try:
        print("try:", 10 / value)
    except ZeroDivisionError:
        print("except: деление на ноль")
    finally:
        print("finally: конец")

check(2)
check(0)
```

```output
try: 5.0
finally: конец
except: деление на ноль
finally: конец
```

В первом вызове деление прошло успешно, поэтому исполнилось тело try, а
затем finally. Во втором вызове исключение прервало try, управление ушло в
ветвь except, и после неё всё равно исполнилась finally. Значит, порядок
при успехе: try → finally; при ошибке: try (до сбоя) → except → finally.

## 2. Исправление падения {#sol-ch10-02}

```python exec
def to_number(text):
    try:
        return int(text) * 2
    except ValueError:
        return None

print(to_number("21"))
print(to_number("двадцать один"))
```

```output
42
None
```

Перехватываем `ValueError`: именно этот тип поднимает `int`, когда строка не
является записью числа. Ловить `Exception` не нужно: `TypeError` при
передаче, скажем, `None` — это дефект вызывающего кода, и его лучше не
скрывать.

## 3. Значение по умолчанию {#sol-ch10-03}

```python exec
def safe_int(text, default):
    try:
        return int(text)
    except ValueError:
        return default

print(safe_int("15", 0))
print(safe_int("1 5", -1))
print(safe_int("", None))
```

```output
15
-1
None
```

Пробел внутри строки `"1 5"` не делает её числом: `int` не игнорирует
внутренние пробелы, поэтому разбор завершается `ValueError`, и функция
возвращает переданное значение по умолчанию.

## 4. Недостижимая ветвь {#sol-ch10-04}

`ValueError` — подкласс `Exception`, поэтому первая ветвь перехватывает его
раньше, чем управление дойдёт до второй. Вторая ветвь становится мёртвым
кодом. Исправление — поставить конкретный тип выше общего:

```python exec
def parse(text):
    try:
        return int(text)
    except ValueError:
        return 0
    except TypeError:
        return None

print(parse("42"))
print(parse("сорок два"))
print(parse(None))
```

```output
42
0
None
```

Теперь обе ветви достижимы: `ValueError` отвечает за нечисловой текст,
`TypeError` — за неподходящий тип аргумента.

## 5. Собственное исключение {#sol-ch10-05}

```python exec
def check_score(score):
    if not isinstance(score, int) or isinstance(score, bool):
        raise TypeError(f"балл должен быть целым, получено {type(score).__name__}")
    if not 0 <= score <= 100:
        raise ValueError(f"балл вне диапазона 0..100: {score}")
    return score

print(check_score(87))
try:
    check_score("87")
except TypeError as error:
    print("TypeError:", error)
try:
    check_score(120)
except ValueError as error:
    print("ValueError:", error)
```

```output
87
TypeError: балл должен быть целым, получено str
ValueError: балл вне диапазона 0..100: 120
```

Проверка `isinstance(score, bool)` нужна потому, что `bool` — подкласс
`int`: без неё `True` прошёл бы как балл 1. Разделение типов исключений
даёт вызывающему коду возможность реагировать по-разному: неверный тип —
дефект вызова, неверное значение — проблема данных.

## 6. Сохранение причины {#sol-ch10-06}

```python exec
def parse_minutes(text):
    try:
        return int(text)
    except ValueError as error:
        raise ValueError("продолжительность должна быть целым числом минут") from error

print(parse_minutes("90"))
try:
    parse_minutes("полтора часа")
except ValueError as error:
    print("сообщение:", error)
    print("причина:", repr(error.__cause__))
```

```output
90
сообщение: продолжительность должна быть целым числом минут
причина: ValueError("invalid literal for int() with base 10: 'полтора часа'")
```

Конструкция `from error` записывает исходное исключение в атрибут
`__cause__`. Читатель отчёта увидит оба сообщения: понятное объяснение
верхнего уровня и техническую причину под ним.

## 7. Что вернёт функция {#sol-ch10-07}

Вызов вернёт `"из finally"`: инструкция `return` в finally выполняется
после return из try и перекрывает его. Исходное значение теряется молча,
поэтому такой приём считается дефектом. Правильно — не возвращать
значения из finally:

```python exec
def mystery():
    try:
        return "из try"
    finally:
        print("finally выполнилась")

print(mystery())
```

```output
finally выполнилась
из try
```

Теперь finally только сообщает о себе, а возвращаемое значение приходит из
try: функция возвращает `"из try"`.

## 8. Иерархия на практике {#sol-ch10-08}

```python exec
def classify(value):
    try:
        print(100 / value)
    except ArithmeticError:
        print("арифметическая проблема")

classify(0)
classify(4)
try:
    classify("ноль")
except TypeError as error:
    print("TypeError:", error)
```

```output
арифметическая проблема
25.0
TypeError: unsupported operand type(s) for /: 'int' and 'str'
```

`ZeroDivisionError` — потомок `ArithmeticError`, поэтому первый вызов попал
в ветвь. Второй вызов прошёл успешно. Третий поднял `TypeError`, который не
является арифметическим исключением: ветвь его не ловит, и программа
падает, если не перехватить снаружи. Это и есть точная обработка: ловится
ровно то, что ожидалось.

## 9. Утверждение или проверка {#sol-ch10-09}

`balance >= 0` — внутренний инвариант: отрицательный баланс означает
дефект в логике самого кода, поэтому проверку можно оставить утверждением.
`amount > 0` — пользовательское значение, его нужно проверять явно.

```python exec
def withdraw(balance, amount):
    assert balance >= 0, "баланс не может быть отрицательным"
    if amount <= 0:
        raise ValueError(f"сумма снятия должна быть положительной, получено {amount}")
    return balance - amount

print(withdraw(100, 30))
try:
    withdraw(100, -10)
except ValueError as error:
    print("ValueError:", error)
```

```output
70
ValueError: сумма снятия должна быть положительной, получено -10
```

При запуске с `-O` строка `assert` исчезает, и `withdraw(-5, 1)` вернёт `-6`
вместо того, чтобы остановиться. Для внутреннего инварианта это осознанный
риск: проверка предназначена для отладки, а не для защиты от внешних данных.

Правило простое: assert защищает инварианты кода, `raise` сообщает о
неверных данных извне.

## 10. Мини-задача: безопасная операция {#sol-ch10-10}

```python exec
def safe_operation(a, op, b):
    if op not in ("+", "-", "*", "/"):
        raise ValueError(f"неизвестная операция: {op!r}")
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    try:
        return a / b
    except ZeroDivisionError:
        return "деление на ноль"

print(safe_operation(7, "+", 5))
print(safe_operation(7, "-", 5))
print(safe_operation(7, "*", 5))
print(safe_operation(7, "/", 5))
print(safe_operation(7, "/", 0))
try:
    safe_operation(7, "%", 5)
except ValueError as error:
    print("ValueError:", error)
```

```output
12
2
35
1.4
деление на ноль
ValueError: неизвестная операция: '%'
```

Функция разделяет два вида проблем. Неизвестная операция — ошибка
вызывающего кода, её нельзя молча игнорировать, поэтому поднимается
`ValueError`. Деление на ноль — ожидаемая ситуация для калькулятора, её
функция обрабатывает сама и возвращает понятную строку. Обратите внимание
на порядок проверок: тип операции проверяется до вычислений, иначе
неизвестный оператор привёл бы к другой ошибке.

## Ответы на вопросы для самопроверки

1. Синтаксическая ошибка возникает при разборе до запуска и не даёт
   программе стартовать; исключение возникает во время исполнения, после
   того как часть программы уже выполнилась.
2. Тип исключения — часть контракта языка, он стабилен между версиями;
   текст сообщения меняется и зависит от данных.
3. Интерпретатор идёт по ветвям сверху вниз и выбирает первую, чей тип
   совпадает с типом исключения или является его базовым классом.
4. При успешном исполнении except не выполняется, а освобождать ресурсы
   нужно всегда; кроме того, finally срабатывает и при `return`.
5. `from error` сохраняет исходное исключение в `__cause__`, поэтому
   причина не теряется; без `from` связь может остаться только в
   `__context__` или исчезнуть из объяснения.
6. Утверждения удаляются при запуске с `-O`, поэтому проверка ввода может
   не выполниться и программа примет неверные данные.
7. Когда вызывающий код знает, что делать с проблемой; функция должна
   сообщить о сбое, а не решать за всех, как его скрыть.
