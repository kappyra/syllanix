---
chapter: ch-29-dataclasses-protocols
number: 29
exercise_count: 10
---

# Решения к главе 29

Решения показывают, что дают инструменты стандартной библиотеки и в каких
случаях ручной код всё ещё уместен.

## 1. Прогноз вывода {#sol-ch29-01}

```python exec
from dataclasses import dataclass

@dataclass
class Book:
    title: str
    year: int

b = Book("Питон", 2026)
print(b)
print(b == Book("Питон", 2026))
print(b.title, b.year)
```

```output
Book(title='Питон', year=2026)
True
Питон 2026
```

Декоратор породил `__init__`, `__repr__` и `__eq__`. Конструктор принимает
поля в порядке объявления, представление печатает имена и значения,
сравнение идёт по значениям полей. Аннотации `str` и `int` здесь нужны как
объявление полей; проверку типов они не выполняют.

## 2. Dataclass для товара {#sol-ch29-02}

```python exec
from dataclasses import dataclass

@dataclass
class Product:
    title: str
    price: float
    count: int

    def total(self):
        return round(self.price * self.count, 2)

a = Product("Книга", 500.0, 2)
b = Product("Ручка", 50.0, 10)
print(a)
print(b)
print(a == Product("Книга", 500.0, 2))
print(a.total(), b.total())
```

```output
Product(title='Книга', price=500.0, count=2)
Product(title='Ручка', price=50.0, count=10)
True
1000.0 500.0
```

Собственный метод `total` добавлен рядом со сгенерированными: dataclass не
запрещает объявлять свои методы. Округление до двух знаков защищает от
накопления ошибки представления при умножении цен с дробной частью.

## 3. Список в заказе {#sol-ch29-03}

```python exec
from dataclasses import dataclass, field

@dataclass
class Order:
    title: str
    items: list = field(default_factory=list)

first = Order("Первый")
second = Order("Второй")
first.items.append("книга")
print(first)
print(second)
print(first.items is second.items)
```

```output
Order(title='Первый', items=['книга'])
Order(title='Второй', items=[])
False
```

`default_factory=list` означает «вызови `list()` для каждого нового
экземпляра». Без фабрики список в объявлении поля был бы общим, а Python
прямо запрещает такое объявление с `ValueError`. Ссылки на списки разные,
поэтому заказы независимы.

## 4. Неизменяемая точка {#sol-ch29-04}

```python exec
from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: int
    y: int

p = Point(1, 2)
print(p)
print(hash(p) == hash(Point(1, 2)))
print(len({p, Point(1, 2)}))
```

```output
Point(x=1, y=2)
True
1
```

`frozen=True` запрещает присваивание атрибутов, поэтому объект безопасно
хешировать: его хеш не изменится. Две равные точки дают одинаковый хеш, и
множество оставляет одну. Проверим запрет на изменение:

```python exec expect-error
from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: int

p = Point(1)
p.x = 5
```

```output
dataclasses.FrozenInstanceError: cannot assign to field 'x'
```

Исключение `FrozenInstanceError` — подкласс `AttributeError`, поэтому
перехватывать его можно как ошибку атрибута.

## 5. namedtuple для координат {#sol-ch29-05}

```python exec
from collections import namedtuple

Point = namedtuple("Point", "x y")
p = Point(3, 4)
print(p)
print(p.x + p.y)
print(p._asdict())
```

```output
Point(x=3, y=4)
7
{'x': 3, 'y': 4}
```

Кода заметно меньше: одна строка вместо декоратора и класса. Но `namedtuple`
не даёт добавить свои методы и проверки в объявлении — для этого пришлось бы
наследоваться от созданного типа. Если нужны валидация или поведение,
dataclass удобнее; если нужна компактная запись, совместимая с кортежем,
выигрывает `namedtuple`.

## 6. Абстрактная фигура {#sol-ch29-06}

```python exec
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        ...

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return round(3.14159 * self.radius ** 2, 2)

print(Circle(2).area())
```

```output
12.57
```

`Circle` реализует `area`, поэтому создаётся нормально. Создать сам `Shape`
нельзя:

```python exec expect-error
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        ...

print(Shape())
```

```output
TypeError: Can't instantiate abstract class Shape without an implementation for abstract method 'area'
```

Проверка происходит в момент создания экземпляра: абстрактный класс не
обещает поведения, поэтому объект без реализации считался бы неполным.

## 7. Протокол без наследования {#sol-ch29-07}

```python exec
from typing import Protocol

class HasArea(Protocol):
    def area(self) -> float:
        ...

class Square:
    def __init__(self, side):
        self.side = side

    def area(self) -> float:
        return float(self.side ** 2)

class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self) -> float:
        return float(self.width * self.height)

def total(shapes):
    return sum(shape.area() for shape in shapes)

print(total([Square(2), Rectangle(3, 4)]))
```

```output
16.0
```

Ни `Square`, ни `Rectangle` не наследуют `HasArea`, но оба ему соответствуют
по набору методов. Функция `total` работает с любым объектом, у которого
есть `area`. Протокол здесь — документация требования, а не базовый класс:
он не добавляет методов и не создаёт иерархию.

## 8. runtime_checkable {#sol-ch29-08}

```python exec
from typing import Protocol, runtime_checkable

@runtime_checkable
class HasArea(Protocol):
    def area(self) -> float:
        ...

class Square:
    def area(self) -> float:
        return 1.0

print(isinstance(Square(), HasArea))
print(isinstance("текст", HasArea))
```

```output
True
False
```

`isinstance` с протоколом проверяет только наличие атрибута с нужным именем
и его вызываемость. Сигнатура, типы аргументов и смысл метода не
проверяются: класс с методом `area`, принимающим три аргумента, тоже пройдёт
проверку. Поэтому `runtime_checkable` — грубая проверка на границе, а
полноценный контроль набора методов выполняют статические анализаторы.

## 9. Анализ: dataclass или обычный класс {#sol-ch29-09}

Настройки приложения — значение, которое не должно меняться после запуска:
подходит `@dataclass(frozen=True)`. Счёт в банке — объект с инвариантом и
операциями: обычный класс со свойствами. Точка на карте — неизменяемое
значение с равенством и хешем: `frozen` dataclass.

```python exec
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    host: str = "localhost"
    port: int = 8000

settings = Settings(port=9000)
print(settings)

class Account:
    def __init__(self, balance=0):
        if balance < 0:
            raise ValueError("баланс не может быть отрицательным")
        self._balance = balance

    @property
    def balance(self):
        return self._balance

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("сумма должна быть положительной")
        self._balance += amount
        return self._balance

acc = Account(100)
print(acc.deposit(50), acc.balance)
```

```output
Settings(host='localhost', port=9000)
150 150
```

Настройкам не нужно поведение — только поля и неизменяемость. Счёту нужны
проверки и операции, поэтому dataclass не подходит: инвариант «баланс не
отрицателен» пришлось бы защищать свойствами вручную, а изменяемость
исключает хеширование.

## 10. Мини-проект: каталог книг {#sol-ch29-10}

```python exec
from dataclasses import dataclass

@dataclass
class Book:
    title: str
    author: str
    year: int

class Catalog:
    def __init__(self):
        self.books = []

    def add(self, book):
        self.books.append(book)

    def by_author(self, name):
        return [book.title for book in self.books if book.author == name]

catalog = Catalog()
catalog.add(Book("Мастер и Маргарита", "Булгаков", 1967))
catalog.add(Book("Пикник на обочине", "Стругацкие", 1972))
catalog.add(Book("Белая гвардия", "Булгаков", 1925))
print(catalog.by_author("Булгаков"))
print(len(catalog.books))
```

```output
['Мастер и Маргарита', 'Белая гвардия']
3
```

Словарь тоже справился бы, но с ним пришлось бы помнить имена ключей и
писать доступ через скобки. Dataclass задаёт поля один раз, проверяет их
наличие при создании и даёт читаемое представление в отладочном выводе.
Каталог остаётся обычным классом: у него есть состояние (`books`) и
поведение (добавление, фильтрация), а инвариантов, требующих свойств, пока
нет.

## Ответы на вопросы для самопроверки

1. `@dataclass` порождает `__init__`, `__repr__` и `__eq__`; при
   `frozen=True` добавляется `__hash__`, при `order=True` — методы сравнения.
2. Общее изменяемое значение связало бы все экземпляры. Взамен предлагается
   `default_factory` — функция, создающая новое значение для каждого объекта.
3. `frozen=True` запрещает присваивание полей; неизменяемый объект можно
   хешировать, потому что его хеш не меняется.
4. `namedtuple` — компактная неизменяемая запись, совместимая с кортежем;
   dataclass — полноценный класс с методами и настройками.
5. Интерфейс — набор операций для внешнего кода; явное описание делает
   требование видимым и позволяет проверить соответствие.
6. Протокол описывает набор методов без наследования; абстрактный базовый
   класс требует наследования и может содержать общий код.
