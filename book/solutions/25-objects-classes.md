---
chapter: ch-25-objects-classes
number: 25
exercise_count: 10
---

# Решения к главе 25

Решения показывают не только работающий код, но и то, как класс меняет
структуру программы: где теперь живёт состояние и кто отвечает за его
изменение.

## 1. Прогноз вывода {#sol-ch25-01}

```python exec
class Box:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

b = Box(2, 5)
print(b.area())
b.width = 10
print(b.area())
print(type(b).__name__)
```

```output
10
50
Box
```

Первый вызов `area` умножает 2 на 5. Затем атрибут `width` заменяется на 10,
и второй вызов умножает уже 10 на 5 — метод каждый раз читает текущее
состояние экземпляра, поэтому результат меняется. `type(b).__name__`
возвращает имя класса как строку.

## 2. Класс Rectangle {#sol-ch25-02}

```python exec
class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

    def perimeter(self):
        return 2 * (self.width + self.height)

r = Rectangle(3, 4)
print(r.area())
print(r.perimeter())
```

```output
12
14
```

Оба метода читают одни и те же атрибуты и не меняют состояние. Периметр
считается как удвоенная сумма сторон, поэтому `2 * (3 + 4) = 14`.

## 3. Исправление ошибки {#sol-ch25-03}

В исходном классе у метода нет параметра `self`, поэтому при вызове
`g.greet()` первый аргумент — сам экземпляр — попал в параметр `name`:

```python exec expect-error
class Greeter:
    def greet(name):
        return "Привет, " + name

g = Greeter()
print(g.greet())
```

```output
TypeError: can only concatenate str (not "Greeter") to str
```

Сообщение выглядит странно только на первый взгляд: в `name` оказался
экземпляр `Greeter`, а сложить строку с объектом нельзя. Исправление —
объявить `self` и хранить имя в атрибуте:

```python exec
class Greeter:
    def greet(self):
        return "Привет, " + self.name

g = Greeter()
g.name = "Аня"
print(g.greet())
print(Greeter.greet(g))
```

```output
Привет, Аня
Привет, Аня
```

Вторая строка показывает явный вызов через класс: то же самое, что делает
`g.greet()`, только экземпляр передан руками.

## 4. Счётчик с командами {#sol-ch25-04}

```python exec
class Counter:
    def __init__(self):
        self.count = 0

    def click(self):
        self.count += 1
        return self.count

    def reset(self):
        self.count = 0

    def value(self):
        return self.count

c = Counter()
print(c.click(), c.click())
c.reset()
print(c.click())
print(c.value())
```

```output
1 2
1
1
```

Два щелчка дают 1 и 2, сброс обнуляет счётчик, следующий щелчок снова даёт 1.
Имя метода `value` и имя атрибута `count` не совпадают намеренно: если бы
атрибут назывался `value`, он перекрыл бы метод, и вызов `c.value()` падал бы
с `TypeError: 'int' object is not callable`. Внутри одного экземпляра
атрибут и метод делят одно пространство имён, поэтому имена обязаны
различаться.

## 5. Анализ ссылок {#sol-ch25-05}

```python exec
class Counter:
    def __init__(self):
        self.count = 0

    def click(self):
        self.count += 1
        return self.count

a = Counter()
b = a
a.click()
print(a.count, b.count, a is b)

c = Counter()
c.click()
print(a.count, c.count, a is c)
```

```output
1 1 True
1 1 False
```

В первом случае `b = a` связывает второе имя с тем же объектом: изменение
видно через оба имени, а `is` даёт `True`. Второй вызов `Counter()` создаёт
новый экземпляр с собственным атрибутом, поэтому изменение `a` на нём не
отражается, и `is` даёт `False`.

## 6. Класс Temperature {#sol-ch25-06}

```python exec
class Temperature:
    def __init__(self, celsius):
        self.celsius = celsius

    def to_fahrenheit(self):
        return self.celsius * 9 / 5 + 32

    def is_freezing(self):
        return self.celsius <= 0

for value in (0, 100, -10):
    t = Temperature(value)
    print(t.celsius, t.to_fahrenheit(), t.is_freezing())
```

```output
0 32.0 True
100 212.0 False
-10 14.0 True
```

Формула перевода: `C * 9 / 5 + 32`. Результат всегда `float`, потому что в
выражении есть деление. `is_freezing` возвращает логическое значение: ноль
считается точкой замерзания, поэтому условие `<= 0`. Методы только читают
`celsius`, состояние объекта после них не меняется.

## 7. Валидация в инициализации {#sol-ch25-07}

```python exec
class Rectangle:
    def __init__(self, width, height):
        if width <= 0 or height <= 0:
            raise ValueError("стороны должны быть положительными")
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

print(Rectangle(3, 4).area())
try:
    Rectangle(0, 5)
except ValueError as error:
    print("отказ:", error)
```

```output
12
отказ: стороны должны быть положительными
```

Проверка стоит до присваивания атрибутов: если данные некорректны,
исключение поднимается раньше, чем появится «полуготовый» объект. Это важное
правило — объект либо создан правильным, либо не создан вовсе.

## 8. Стек {#sol-ch25-08}

```python exec
class Stack:
    def __init__(self):
        self.items = []

    def push(self, value):
        self.items.append(value)

    def pop(self):
        return self.items.pop()

    def size(self):
        return len(self.items)

s = Stack()
s.push("a")
s.push("b")
print(s.pop())
print(s.size())
```

```output
b
1
```

Список создаётся в `__init__`, поэтому у каждого стека он свой. `push`
добавляет в конец, `pop` снимает с конца — получается порядок «последним
пришёл, первым вышел». Попытка снять значение из пустого стека передаёт
работу методу списка:

```python exec expect-error
class Stack:
    def __init__(self):
        self.items = []

    def pop(self):
        return self.items.pop()

s = Stack()
print(s.pop())
```

```output
IndexError: pop from empty list
```

## 9. Мини-проект: библиотека {#sol-ch25-09}

```python exec
class Book:
    def __init__(self, title, author, year):
        self.title = title
        self.author = author
        self.year = year

class Library:
    def __init__(self):
        self.books = []

    def add(self, book):
        self.books.append(book)

    def titles(self):
        return [book.title for book in self.books]

lib = Library()
lib.add(Book("Мастер и Маргарита", "Булгаков", 1967))
lib.add(Book("Пикник на обочине", "Стругацкие", 1972))
print(lib.titles())
```

```output
['Мастер и Маргарита', 'Пикник на обочине']
```

Список книг создаётся в `__init__` экземпляра `Library`. Если бы он был
атрибутом класса, все библиотеки делили бы один список: добавление книги в
одну было бы видно в другой. Правило простое: изменяемое состояние создаётся
для каждого экземпляра отдельно, в его методе инициализации.

## 10. Словарь или класс {#sol-ch25-10}

```python exec
book_dict = {"title": "Мастер и Маргарита", "author": "Булгаков", "year": 1967}

class Book:
    def __init__(self, title, author, year):
        self.title = title
        self.author = author
        self.year = year

    def describe(self):
        return f"{self.title} ({self.author}, {self.year})"

book = Book("Мастер и Маргарита", "Булгаков", 1967)
print(book_dict["title"])
book_dict["tittle"] = "опечатка"
print(len(book_dict))
print(book.describe())
```

```output
Мастер и Маргарита
4
Мастер и Маргарита (Булгаков, 1967)
```

Словарь молча принял ключ с опечаткой, и теперь в нём четыре записи вместо
трёх; обнаружится это только при чтении, когда нужного ключа не окажется на
месте. Класс защищает иначе: набор атрибутов задан методом инициализации, а
поведение собрано в методах. За опечатку в имени атрибута тоже не наказывают,
но её видно сразу — нужное значение не появится. Класс выигрывает там, где у
сущности есть обязательные поля и поведение; словарь остаётся удобным для
одноразовых структур и передачи параметров.

## Ответы на вопросы для самопроверки

1. Класс — описание типа, экземпляр — значение этого типа. `type(p)` даёт
   класс экземпляра, `type(Point)` даёт `type`: сам класс — тоже объект.
2. Python подставляет экземпляр первым аргументом автоматически; поэтому
   `p.method()` равносильно `Point.method(p)`.
3. Без `self` первый аргумент вызова попадёт в первый параметр метода, и
   логика сломается. Без присваивания атрибута в `__init__` чтение атрибута
   даст `AttributeError`.
4. Конструктор — вызов класса, создающий объект; `__init__` заполняет уже
   созданный экземпляр и обязан вернуть `None`.
5. Присваивание связывает имя с тем же объектом. Независимый экземпляр
   создаётся новым вызовом класса.
6. Класс держит данные и операции вместе, задаёт обязательные поля в одном
   месте и не требует помнить договорённость о ключах.
