---
chapter: ch-28-dunder
number: 28
exercise_count: 10
---

# Решения к главе 28

Решения показывают, как один-два специальных метода меняют поведение класса
во всех встроенных операциях. Проверяйте не только вывод, но и то, какой
метод его создал.

## 1. Прогноз вывода {#sol-ch28-01}

```python exec
class Tag:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Tag({self.name!r})"

print(Tag("python"))
print(repr(Tag("python")))
print([Tag("a"), Tag("b")])
```

```output
Tag('python')
Tag('python')
[Tag('a'), Tag('b')]
```

`__str__` не объявлен, поэтому `print` использует `__repr__`. Внутри списка
тоже вызывается `__repr__` для каждого элемента. Выражение `{self.name!r}`
подставляет строку в кавычках — так представление становится однозначным:
видно, что `name` — строка, а не имя переменной.

## 2. Представление для денег {#sol-ch28-02}

```python exec
class Money:
    def __init__(self, amount, currency="руб."):
        self.amount = amount
        self.currency = currency

    def __repr__(self):
        return f"Money({self.amount}, {self.currency!r})"

    def __str__(self):
        return f"{self.amount} {self.currency}"

print(repr(Money(100)))
print(Money(100))
print([Money(100, "USD")])
```

```output
Money(100, 'руб.')
100 руб.
[Money(100, 'USD')]
```

`repr` печатает код, которым можно создать такой же объект, — с кавычками
вокруг валюты и запятой между аргументами. `print` использует `__str__` и
показывает сумму так, как её увидит пользователь. Список снова идёт через
`__repr__`, поэтому в нём видны технические подробности.

## 3. Равенство точек {#sol-ch28-03}

```python exec
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return (self.x, self.y) == (other.x, other.y)

print(Point(1, 2) == Point(1, 2))
print(Point(1, 2) == Point(3, 4))
print(Point(1, 2) == "точка")
```

```output
True
False
False
```

Сравниваются значения полей, а не ссылки. Для строки возвращается
`NotImplemented`: Python пробует сравнение с другой стороны, не находит
подходящего метода и возвращает `False`. Исключения не возникает, потому что
`NotImplemented` — это не ошибка, а сигнал «попробуй иначе».

## 4. Согласование равенства и хеша {#sol-ch28-04}

```python exec
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return isinstance(other, Point) and (self.x, self.y) == (other.x, other.y)

    def __hash__(self):
        return hash((self.x, self.y))

p1 = Point(1, 2)
p2 = Point(1, 2)
print(p1 == p2)
print(hash(p1) == hash(p2))
print(len({p1, p2}))
```

```output
True
True
1
```

Хеш вычисляется из той же пары полей, что и равенство, поэтому контракт
соблюдён: равные объекты дают равные хеши. Множество из двух равных точек
содержит один элемент. Без `__hash__` тот же класс стал бы нехешируемым:

```python exec expect-error
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)

p = Point(1, 2)
print(hash(p))
```

```output
TypeError: unhashable type: 'Point'
```

## 5. Сортировка версий {#sol-ch28-05}

```python exec
class Version:
    def __init__(self, major, minor):
        self.major = major
        self.minor = minor

    def __repr__(self):
        return f"{self.major}.{self.minor}"

    def __lt__(self, other):
        return (self.major, self.minor) < (other.major, other.minor)

versions = [Version(1, 10), Version(1, 2), Version(2, 0)]
print(sorted(versions))
```

```output
[1.2, 1.10, 2.0]
```

Сравнение идёт по паре чисел, а не по тексту. Строковое сравнение поставило
бы `1.10` раньше `1.2`, потому что символ `1` меньше символа `2`. Кортеж
сравнивается по первому элементу, затем по второму, поэтому `1.2` меньше
`1.10`: два меньше десяти. Если в проекте несколько компонент версии, tuple
из них — самый простой и предсказуемый ключ.

## 6. Длина и истинность {#sol-ch28-06}

```python exec
class Queue:
    def __init__(self, items=()):
        self.items = list(items)

    def __len__(self):
        return len(self.items)

q = Queue(["a", "b"])
print(len(q))
print(bool(q))
print(bool(Queue()))
```

```output
2
True
False
```

`len` вызывает `__len__` напрямую. Проверка истинности тоже обращается к
`__len__`: пустая очередь даёт ноль, а ноль — ложь. Отдельный `__bool__` не
нужен, если достаточно длины. Значение по умолчанию `items=()` выбрано
кортежем, а не списком, чтобы не повторять ловушку с изменяемым аргументом:
список создаётся внутри функции заново.

## 7. Сложение векторов {#sol-ch28-07}

```python exec
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Vector({self.x}, {self.y})"

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

a = Vector(1, 2)
b = Vector(3, 4)
print(a + b)
print(a, b)
```

```output
Vector(4, 6)
Vector(1, 2) Vector(3, 4)
```

`__add__` вернул новый объект, а исходные остались прежними. Это важное
свойство: оператор не должен незаметно изменять операнды. Если бы внутри
`__add__` стояло `self.x += other.x`, сложение двух векторов меняло бы первый,
и повторный вызов дал бы другой результат.

## 8. Вызываемый фильтр {#sol-ch28-08}

```python exec
class StartsWith:
    def __init__(self, prefix):
        self.prefix = prefix

    def __call__(self, text):
        return text.startswith(self.prefix)

words = ["python", "pytest", "java", "php"]
selected = [word for word in words if StartsWith("py")(word)]
print(selected)
```

```output
['python', 'pytest']
```

Объект с `__call__` можно передавать туда, где ожидается функция: в `filter`,
в ключ сортировки, в обработчик. При этом он хранит настройку — префикс — в
атрибуте, а не в замыкании. Включение вызывает объект сразу после создания;
для повторного использования префикс стоит сохранить в переменной.

## 9. Исправление нехешируемого класса {#sol-ch28-09}

Python запрещает хешировать объект, у которого объявлено равенство по
значению, но не объявлен хеш. Исправление — добавить `__hash__`,
согласованный с `__eq__`:

```python exec
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self):
        return hash((self.x, self.y))

print(len({Point(1, 2), Point(1, 2), Point(3, 4)}))
```

```output
2
```

Из трёх точек две равны, поэтому в множестве осталось две. Хеш считается из
тех же полей, что и равенство: если бы он зависел только от `x`, точки
`(1, 2)` и `(1, 3)` могли бы попасть в один элемент, не будучи равными.

## 10. Мини-проект: карточка товара {#sol-ch28-10}

```python exec
class Product:
    def __init__(self, title, price):
        self.title = title
        self.price = price

    def __repr__(self):
        return f"Product({self.title!r}, {self.price})"

    def __eq__(self, other):
        return isinstance(other, Product) and self.title == other.title

    def __hash__(self):
        return hash(self.title)

products = {Product("Книга", 500), Product("Книга", 700), Product("Ручка", 50)}
print(len(products))
by_title = {Product("Книга", 500): "в наличии"}
print(by_title[Product("Книга", 900)])
print(sorted([Product("Ручка", 50), Product("Книга", 500)], key=lambda p: p.price))
```

```output
2
в наличии
[Product('Ручка', 50), Product('Книга', 500)]
```

Множество объединило две книги с одинаковым названием, потому что равенство и
хеш зависят только от названия. Поиск в словаре по книге с другой ценой
сработал: ключ сравнивается по названию. Для сортировки специальные методы не
понадобились: `sorted` с `key` сравнивает уже числа, а не объекты. Если бы
`key` не указали, понадобился бы `__lt__`.

## Ответы на вопросы для самопроверки

1. `__repr__` должен позволять восстановить объект и однозначно называть
   значения; `__str__` предназначен для человека и может быть красивым.
2. `NotImplemented` — сигнал «я не умею сравнивать с этим типом»; Python
   попробует отражённый метод другой стороны. `False` сразу закрыл бы
   возможность сравнения.
3. Равенство по значению и стандартный хеш по адресу несовместимы: равные
   объекты давали бы разные хеши. Python запрещает такую комбинацию.
4. Если объекты равны, их хеши обязаны быть равны.
5. Хеш вычисляется при вставке. После изменения полей объект ищется по
   старому хешу и не находится.
6. `sorted` сравнивает элементы только через `<`. Оператор `>` работает через
   отражённое сравнение (`a > b` вызывает `b.__lt__(a)`), поэтому он тоже
   доступен. А `<=` и `>=` по умолчанию не выводятся: для них нужны
   собственные методы, иначе они поднимут `TypeError`.
