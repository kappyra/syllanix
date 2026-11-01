---
chapter: ch-53-refactoring
number: 53
exercise_count: 10
---

# Решения к главе 53

В каждом решении показаны два состояния — до и после, — и проверка того, что
поведение не изменилось. Именно эта проверка отличает рефакторинг от
переписывания.

## 1. Прогноз вывода {#sol-ch53-01}

```python exec
def total_for_user(items):
    result = 0
    for item in items:
        result += item["price"] * item["quantity"]
    if result > 1000:
        result = result * 0.9
    return result

def total_for_company(items):
    result = 0
    for item in items:
        result += item["price"] * item["quantity"]
    if result > 5000:
        result = result * 0.9
    return result

items = [{"price": 300, "quantity": 4}]
print(total_for_user(items))
print(total_for_company(items))
```

```output
1080.0
1200
```

Сумма без скидки равна `300 * 4 = 1200`. Для пользователя порог `1000`
превышен, поэтому результат умножается на `0.9` и становится `1080.0`. Для
компании порог `5000` не превышен, поэтому остаётся `1200`. После устранения
дублирования (упражнение 5) вывод обязан совпасть: смысл правил не менялся,
менялось только их расположение в коде.

## 2. Извлечение функции {#sol-ch53-02}

Расчёт и печать разделены: `calc_total` возвращает число, `report` печатает.
Проверим, что вывод прежний:

```python exec
def calc_total(items):
    result = 0
    for item in items:
        result += item["price"] * item["quantity"]
    if result > 1000:
        result = result * 0.9
    return result

def report(items):
    print("Итого:", round(calc_total(items), 2))

report([{"price": 300, "quantity": 4}])
report([{"price": 100, "quantity": 1}])
```

```output
Итого: 1080.0
Итого: 100
```

Теперь расчёт можно проверить отдельно, без перехвата вывода `print`. Это
первый шаг к тестам: функция, которая возвращает значение, тестируется
несложно, а функция, которая печатает, требует сравнения текста.

## 3. Магические числа {#sol-ch53-03}

```python exec
BULK_QUANTITY = 3
BULK_DISCOUNT = 0.9
VIP_DISCOUNT = 0.95

def price_of(item, is_vip):
    price = item["price"]
    if item["quantity"] > BULK_QUANTITY:
        price = price * BULK_DISCOUNT
    if is_vip:
        price = price * VIP_DISCOUNT
    return price

items = [{"price": 100, "quantity": 5}, {"price": 50, "quantity": 1}]
print(sum(price_of(item, False) * item["quantity"] for item in items))
print(sum(price_of(item, True) * item["quantity"] for item in items))
```

```output
500.0
475.0
```

Значения те же, что в примере главы. Разница в читаемости: теперь видно, что
`3` — это порог оптовой покупки, а `0.9` и `0.95` — скидки. Если правило
изменится, правка будет в одном месте, и её смысл понятен без догадок.

## 4. Флаговый аргумент {#sol-ch53-04}

```python exec
def send(text, *, urgent=False):
    if urgent:
        return "срочно: " + text
    return text

print(send("привет"))
print(send("пожар", urgent=True))
```

```output
привет
срочно: пожар
```

Результат прежний, но вызов стал читаемым: `send("пожар", urgent=True)` не
требует помнить порядок аргументов. Кроме того, у режима появилось значение по
умолчанию, поэтому обычный вызов стал короче. Флаг не исчез — он превратился в
именованный параметр, что для читателя одно и то же по смыслу, но гораздо
понятнее.

## 5. Устранение дублирования {#sol-ch53-05}

```python exec
def subtotal(items):
    return sum(item["price"] * item["quantity"] for item in items)

def total(items, *, discount_from):
    amount = subtotal(items)
    return amount * 0.9 if amount > discount_from else amount

items = [{"price": 300, "quantity": 4}]
print(total(items, discount_from=1000))
print(total(items, discount_from=5000))
```

```output
1080.0
1200
```

Обе прежние функции давали эти же значения. Общая часть — подсчёт суммы —
теперь существует в одном экземпляре, а различие (порог скидки) стало
параметром. Если правило скидки изменится, правка понадобится в одном месте, а
не в двух.

## 6. Замена условия полиморфизмом {#sol-ch53-06}

```python exec
class Transport:
    def speed(self):
        return 5

class Bike(Transport):
    def speed(self):
        return 15

class Car(Transport):
    def speed(self):
        return 60

for vehicle in (Bike(), Car(), Transport()):
    print(vehicle.speed())
```

```output
15
60
5
```

Результаты совпадают с прежней цепочкой `if`. Новый вид транспорта теперь
добавляется отдельным классом, а не новой ветвью в функции. Код, который
перебирает транспорт, не знает о видах: он вызывает `speed` у каждого объекта.
Это тот же полиморфизм, что разбирался в главе 27.

## 7. Пустой except {#sol-ch53-07}

Сначала покажем, как ошибка исчезает: функция возвращает `None`, и вызывающий
код не знает, что произошло.

```python exec
def parse_age(text):
    try:
        return int(text)
    except ValueError:
        pass

print(parse_age("42"))
print(parse_age("сорок два"))
```

```output
42
None
```

Исправление — не подавлять ошибку, а превратить её в понятное исключение с
сохранением причины:

```python exec
def parse_age(text):
    try:
        return int(text)
    except ValueError as error:
        raise ValueError(f"возраст должен быть числом: {text!r}") from error

print(parse_age("42"))
try:
    parse_age("сорок два")
except ValueError as error:
    print("отказ:", error)
```

```output
42
отказ: возраст должен быть числом: 'сорок два'
```

Теперь вызывающий код видит и факт ошибки, и понятное сообщение. Конструкция
`from error` сохраняет исходное исключение как причину, поэтому при отладке
виден весь путь ошибки.

## 8. Тест-характеристика {#sol-ch53-08}

```python exec
def legacy_items(text):
    return text.split(",")

def characterize():
    cases = {"a, b": ["a", " b"], "a,,b": ["a", "", "b"], "": [""]}
    for text, expected in cases.items():
        assert legacy_items(text) == expected, text
    print("характеристика зафиксирована:", len(cases), "случая")

characterize()

def parse_items(text):
    if not text:
        return [""]
    return text.split(",")

for text in ("a, b", "a,,b", ""):
    print(repr(parse_items(text)))
```

```output
характеристика зафиксирована: 3 случая
['a', ' b']
['a', '', 'b']
['']
```

Тест зафиксировал странности поведения: пробел не удаляется, пустой элемент
сохраняется, пустая строка даёт список с одним пустым элементом. Без него
рефакторинг был бы опасен: любая «чистка» могла изменить результат для
реальных данных. После фиксации переписанная версия проверяется на тех же
свойствах, и поведение остаётся прежним.

## 9. Разбор инцидента {#sol-ch53-09}

Причина видна сразу, если её воспроизвести:

```python exec
class Cart:
    def __init__(self, items=[]):
        self.items = items

a = Cart()
b = Cart()
a.items.append("книга")
print(b.items)
```

```output
['книга']
```

Список по умолчанию создаётся один раз при определении функции, поэтому обе
корзины используют его. Цепочка «почему»: почему у второй корзины появился
товар? Потому что список общий. Почему он общий? Потому что значение по
умолчанию одно на всех. Почему так написали? Потому что хотели сделать список
необязательным. Почему это не заметили? Потому что тест создавал один объект.
Почему тест создавал один? Потому что проверяли один сценарий.

Две меры: в коде — не использовать изменяемое значение по умолчанию; в
тестах — проверять независимость двух экземпляров.

```python exec
class Cart:
    def __init__(self, items=None):
        self.items = [] if items is None else list(items)

def test_carts_are_independent():
    first = Cart()
    second = Cart()
    first.items.append("книга")
    assert second.items == []
    print("тест пройден: корзины независимы")

test_carts_are_independent()
print(Cart().items)
```

```output
тест пройден: корзины независимы
[]
```

## 10. Мини-проект: рефакторинг отчёта {#sol-ch53-10}

До рефакторинга функция собирала всё сразу:

```python exec
def report(items):
    lines = ["Чек"]
    result = 0
    for item in items:
        line = item["name"] + " " + str(item["price"] * item["quantity"])
        lines.append(line)
        result += item["price"] * item["quantity"]
    if result > 1000:
        result = result * 0.9
    lines.append("Итого: " + str(round(result, 2)))
    return lines

items = [{"name": "Книга", "price": 500, "quantity": 2}, {"name": "Ручка", "price": 50, "quantity": 1}]
for line in report(items):
    print(line)
print("строк в отчёте:", len(report([{"name": "Книга", "price": 500, "quantity": 2}])))
```

```output
Чек
Книга 1000
Ручка 50
Итого: 945.0
строк в отчёте: 3
```

После разделения на три функции — строка позиции, итог, сборка отчёта:

```python exec
def line_for(item):
    return item["name"] + " " + str(item["price"] * item["quantity"])

def total(items):
    result = sum(item["price"] * item["quantity"] for item in items)
    return result * 0.9 if result > 1000 else result

def report(items):
    lines = ["Чек"]
    lines.extend(line_for(item) for item in items)
    lines.append("Итого: " + str(round(total(items), 2)))
    return lines

items = [{"name": "Книга", "price": 500, "quantity": 2}, {"name": "Ручка", "price": 50, "quantity": 1}]
for line in report(items):
    print(line)
print("строк в отчёте:", len(report([{"name": "Книга", "price": 500, "quantity": 2}])))
```

```output
Чек
Книга 1000
Ручка 50
Итого: 945.0
строк в отчёте: 3
```

Вывод совпал полностью: и содержимое чека, и число строк. Длина `report`
сократилась с десяти строк до пяти, а расчёт и форматирование стали
отдельными функциями. Стоимость будущих правок уменьшилась: изменить формат
строки теперь можно в `line_for`, не трогая правило скидки; изменить правило —
в `total`, не трогая вывод.

## Ответы на вопросы для самопроверки

1. Запах кода — признак возможной проблемы, а не доказанный дефект. Устранять
   его стоит там, где он реально мешает изменениям.
2. «Поведение не изменилось» означает те же значения, ошибки и формат. Это
   проверяют тестами, написанными до рефакторинга.
3. Малый шаг легко проверить и откатить; большой шаг содержит несколько
   причин изменения сразу, и при сбое непонятно, какая из них виновата.
4. Технический долг повышает стоимость изменений: каждое новое изменение
   требует больше чтения, проверок и обходов хрупких мест.
5. Тесты-характеристики описывают текущее поведение, включая странности, и
   дают возможность менять структуру, не теряя совместимость.
6. Поиск виноватого заставляет людей скрывать проблемы, а системные причины
   остаются; без виноватых находятся именно те меры, которые предотвращают
   повторение.
