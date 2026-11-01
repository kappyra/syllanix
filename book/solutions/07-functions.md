---
chapter: ch-07-functions
number: 7
exercise_count: 10
---

# Решения к главе 7

Функции удобно проверять на нескольких наборах аргументов: один вызов мало что
доказывает. Сравните свои решения с приведёнными и обратите внимание на
формулировки, а не только на вывод.

## 1. Первая функция {#sol-ch07-01}

```python exec
def rectangle_area(width, height):
    return width * height

print(rectangle_area(3, 4))
```

```output
12
```

Определение создаёт функцию, вызов выполняет тело. Если убрать `return`,
функция вернёт `None`, и `print` выведет `None` вместо `12`.

## 2. Параметр или аргумент {#sol-ch07-02}

```python exec
def repeat(text, times):
    return text * times

print(repeat("да", 3))
```

```output
дадада
```

У функции два параметра — `text` и `times`; это имена в определении. В вызове
два аргумента — строка `"да"` и число `3`; это конкретные значения,
переданные на место параметров. Различие принципиально: параметры описывают
форму функции, аргументы — конкретный вызов. У одной функции может быть много
вызовов с разными аргументами, но набор параметров у неё один.

## 3. Печать или возврат {#sol-ch07-03}

```python exec
def show_area(width, height):
    print(width * height)

def get_area(width, height):
    return width * height

show_area(2, 5)
print(get_area(2, 5))
```

```output
10
10
```

Обе строки выглядят одинаково, но происходят разные вещи. `show_area` печатает
число и возвращает `None`; `get_area` возвращает число, а печатает его уже
`print` снаружи. Поэтому `show_area(2, 5) + 1` невозможно: к `None` нельзя
прибавить единицу.

```python exec expect-error
def show_area(width, height):
    print(width * height)

print(show_area(2, 5) + 1)
```

```output
TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'
```

```python exec
def get_area(width, height):
    return width * height

print(get_area(2, 5) + 1)
```

```output
11
```

## 4. Порядок аргументов {#sol-ch07-04}

```python exec
def power(base, exp):
    return base ** exp

print(power(2, 5))
print(power(5, 2))
print(power(exp=2, base=5))
```

```output
32
25
25
```

Позиционные аргументы заполняют параметры по порядку: `power(2, 5)` — это
`2 ** 5`, а `power(5, 2)` — `5 ** 2`. Именованные аргументы привязываются к
параметрам по имени, поэтому `power(exp=2, base=5)` совпадает с
`power(5, 2)`.

## 5. Аргумент по умолчанию {#sol-ch07-05}

```python exec
def ticket_price(age, base=600):
    if age < 18:
        return base // 2
    return base

print(ticket_price(12))
print(ticket_price(30))
```

```output
300
600
```

Для 12 лет сработала скидка: `600 // 2 = 300`. Для 30 лет вернулась базовая
цена. Второй аргумент не передавался, поэтому использовалось значение по
умолчанию.

## 6. Исправление ошибки вызова {#sol-ch07-06}

В вызове `power(2)` передан один аргумент, а параметров два, и у `exp` нет
значения по умолчанию. Отсюда `TypeError`.

```python exec expect-error
def power(base, exp):
    return base ** exp

print(power(2))
```

```output
TypeError: power() missing 1 required positional argument: 'exp'
```

Два исправления — позиционным и именованным аргументом:

```python exec
def power(base, exp):
    return base ** exp

print(power(2, 3))
print(power(base=2, exp=3))
```

```output
8
8
```

## 7. Локальная область {#sol-ch07-07}

```python exec
def compute():
    result = 42
    return result

print(compute())
```

```output
42
```

А вторая строка программы завершается ошибкой:

```python exec expect-error
def compute():
    result = 42
    return result

print(compute())
print(result)
```

```output
NameError: name 'result' is not defined
```

Имя `result` создано внутри функции, поэтому существует только во время её
вызова. Снаружи такого имени нет: функция вернула значение, но не создала
глобальную переменную.

## 8. docstring {#sol-ch07-08}

```python exec
def celsius_to_fahrenheit(celsius):
    """Перевести температуру из градусов Цельсия в градусы Фаренгейта."""
    return celsius * 9 / 5 + 32

print(celsius_to_fahrenheit(0))
print(celsius_to_fahrenheit(100))
print(celsius_to_fahrenheit.__doc__)
```

```output
32.0
212.0
Перевести температуру из градусов Цельсия в градусы Фаренгейта.
```

При `0` получается `32.0`, при `100` — `212.0`. Результат дробный, потому что
деление `/` всегда даёт `float`. Docstring доступен как атрибут `__doc__`
(обращение через точку подробно разбирается в главе 25) — именно его показывают
инструменты справки.

## 9. Функция из функции {#sol-ch07-09}

```python exec
def square(n):
    return n * n

def sum_of_squares(a, b):
    return square(a) + square(b)

print(sum_of_squares(3, 4))
```

```output
25
```

`sum_of_squares` не повторяет формулу квадрата, а вызывает `square`. Если
правило возведения в квадрат изменится, достаточно поправить одну функцию.

## 10. Мини-задача: чек {#sol-ch07-10}

```python exec
def order_total(price, count, discount=0):
    total = price * count
    return total - total * discount // 100

def format_receipt(price, count, discount=0):
    amount = order_total(price, count, discount)
    return f"Товаров: {count}, к оплате: {amount} рублей"

print(format_receipt(250, 3, 10))
```

```output
Товаров: 3, к оплате: 675 рублей
```

`format_receipt` отвечает за текст, `order_total` — за вычисление. Такое
разделение удобно: сумму можно использовать отдельно от сообщения, а формат
сообщения менять, не трогая арифметику. Обратите внимание, что значение
`discount` передаётся дальше как аргумент, а не читается из глобального имени.

## Ответы на вопросы для самопроверки

1. Параметр — имя в определении функции; аргумент — значение, переданное при
   вызове.
2. `def` только создаёт функцию и связывает её с именем; тело исполняется в
   момент вызова.
3. `return` передаёт значение вызывающему коду, `print` выводит текст в
   терминал и возвращает `None`. Без `return` функцию нельзя использовать в
   арифметике: её результат — `None`.
4. `None`.
5. Записью `параметр=значение`; это снимает зависимость от порядка и делает
   вызов понятнее.
6. Один раз, в момент определения функции, а не при каждом вызове.
7. Потому что у каждого вызова своя локальная область видимости, которая
   исчезает после завершения.
8. Потому что позиционный аргумент не может идти после именованного: непонятно,
   какому параметру отдать позицию.
9. Docstring — часть объекта функции, доступная программно (`__doc__`) и в
   справке; комментарий виден только в исходном тексте.
