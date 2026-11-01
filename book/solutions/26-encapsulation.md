---
chapter: ch-26-encapsulation
number: 26
exercise_count: 10
---

# Решения к главе 26

Решения показывают, как соглашения и свойства превращают правила класса в
проверяемый код. Обращайте внимание не только на результат, но и на то, где
именно стоит проверка.

## 1. Прогноз вывода {#sol-ch26-01}

```python exec
class Cat:
    legs = 4

    def __init__(self, name):
        self.name = name

a = Cat("Мурка")
b = Cat("Барсик")
b.legs = 3
print(a.legs, b.legs, Cat.legs)
print(a.__dict__)
print(b.__dict__)
```

```output
4 3 4
{'name': 'Мурка'}
{'name': 'Барсик', 'legs': 3}
```

У `a` собственного `legs` нет, поэтому чтение поднялось к классу и вернуло 4.
Присваивание `b.legs = 3` создало атрибут у `b`, и теперь `b.legs` находит
его на первом шаге поиска. Класс при этом не изменился: `Cat.legs` по-прежнему
4. Словари экземпляров подтверждают: у `a` только имя, у `b` — имя и
переопределённое число ног.

## 2. Атрибут класса для константы {#sol-ch26-02}

```python exec
class Circle:
    PI = 3.14159

    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return self.PI * self.radius ** 2

a = Circle(1)
b = Circle(2)
print(a.area(), b.area())
print(Circle.PI == a.PI == b.PI)
```

```output
3.14159 12.56636
True
```

`PI` — неизменяемое значение, одинаковое для всех кругов, поэтому его место в
классе. Радиус у каждого свой, он создаётся в методе инициализации. Метод
`area` читает `self.PI`: поиск не находит атрибут в экземпляре и поднимается
к классу.

## 3. Исправление общей коллекции {#sol-ch26-03}

Список `grades` объявлен в теле класса, поэтому он один на всех студентов.
Метод `add_grade` изменяет именно его, а не список конкретного экземпляра.
Исправление — создавать список в методе инициализации:

```python exec
class Student:
    def __init__(self):
        self.grades = []

    def add_grade(self, grade):
        self.grades.append(grade)

a = Student()
b = Student()
a.add_grade(5)
print(a.grades)
print(b.grades)
```

```output
[5]
[]
```

Теперь у каждого студента собственный список. Правило: изменяемое значение —
только в экземпляре, в методе `__init__`.

## 4. Свойство только для чтения {#sol-ch26-04}

```python exec
class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    @property
    def area(self):
        return self.width * self.height

r = Rectangle(2, 3)
print(r.area)
```

```output
6
```

Площадь не хранится, а вычисляется при обращении, поэтому её нельзя
рассинхронизировать с размерами. Присваивание отклоняется, потому что сеттера
нет:

```python exec expect-error
class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    @property
    def area(self):
        return self.width * self.height

r = Rectangle(2, 3)
r.area = 10
```

```output
AttributeError: property 'area' of 'Rectangle' object has no setter
```

## 5. Сеттер с проверкой {#sol-ch26-05}

```python exec
class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        if value <= 0:
            raise ValueError("ширина должна быть положительной")
        self._width = value

r = Rectangle(2, 3)
r.width = 5
print(r.width)
try:
    r.width = 0
except ValueError as error:
    print("отказ:", error)
print(r.width)
try:
    Rectangle(-5, 2)
except ValueError as error:
    print("создание отклонено:", error)
```

```output
5
отказ: ширина должна быть положительной
5
создание отклонено: ширина должна быть положительной
```

Сеттер проверяет значение до записи, а `__init__` присваивает через него, поэтому
`Rectangle(-5, 2)` тоже отклоняется. После отказа от присваивания внутреннее
поле осталось прежним: 5. Обратите внимание на имя внутреннего атрибута `_width` — оно не
совпадает с именем свойства, иначе сеттер вызвал бы сам себя.

## 6. Искажение имён {#sol-ch26-06}

```python exec
class Wallet:
    def __init__(self):
        self.__balance = 0

    def add(self, amount):
        self.__balance += amount

    @property
    def balance(self):
        return self.__balance

w = Wallet()
w.add(50)
w.add(25)
print(w.balance)
print(w.__dict__)
```

```output
75
{'_Wallet__balance': 75}
```

В исходном коде атрибут называется `__balance`, но при разборе класса Python
переименовал его в `_Wallet__balance`. Внутри класса обращение по короткому
имени работает: интерпретатор подставляет префикс автоматически. Снаружи
видно итоговое имя, и подкласс с таким же `__balance` получит своё имя
`_Subclass__balance`, не перекрыв внутренний атрибут родителя.

## 7. Анализ: свойство вместо атрибута {#sol-ch26-07}

Свойство и обычный атрибут читаются и записываются одинаково, поэтому замена
не требует менять вызовы:

```python exec
class TemperatureV1:
    def __init__(self, celsius):
        self.celsius = celsius

class TemperatureV2:
    def __init__(self, celsius):
        self._celsius = celsius

    @property
    def celsius(self):
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError("ниже абсолютного нуля")
        self._celsius = value

def show(t):
    print(t.celsius)

show(TemperatureV1(20))
show(TemperatureV2(20))
t = TemperatureV2(20)
t.celsius = 30
print(t.celsius)
```

```output
20
20
30
```

Функция `show` не знает, с какой версией работает: в обоих случаях она
обращается к `t.celsius` без скобок. Разница только в том, что вторая версия
проверяет значение. Это и есть причина, по которой в Python не спешат
объявлять свойства заранее: переход от атрибута к свойству безопасен.

## 8. Счётчик созданных объектов {#sol-ch26-08}

```python exec
class Counter:
    total = 0

    def __init__(self):
        type(self).total += 1

a = Counter()
b = Counter()
c = Counter()
print(Counter.total)
print(a.total)

class Node:
    total = 0

    def __init__(self):
        self.total += 1

Node()
Node()
print(Node.total)
print(Node().total)
```

```output
3
3
0
1
```

`type(self).total += 1` явно берёт атрибут у класса и увеличивает его, поэтому
счётчик общий. Запись `self.total += 1` читает классовое значение 0,
прибавляет 1 и создаёт атрибут экземпляра; классовое значение остаётся нулём.
Чтение `Node().total` в последней строке создаёт ещё один экземпляр, у
которого уже есть собственный `total` со значением 1.

## 9. Исправление рекурсии {#sol-ch26-09}

Свойство `celsius` читает `self.celsius`, то есть снова обращается к самому
себе; сеттер делает то же с присваиванием. Хранить значение нужно в
отдельном внутреннем атрибуте:

```python exec
class Temperature:
    def __init__(self, celsius):
        self.celsius = celsius

    @property
    def celsius(self):
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError("ниже абсолютного нуля")
        self._celsius = value

t = Temperature(-10)
print(t.celsius)
t.celsius = 0
print(t.celsius)
```

```output
-10
0
```

Правило: геттер читает `self._x`, сеттер пишет `self._x`, а имя свойства —
`x`. Любое обращение к `self.x` внутри свойства снова запускает свойство.

## 10. Мини-проект: товар со скидкой {#sol-ch26-10}

```python exec
class Product:
    def __init__(self, title, price):
        self.title = title
        self.price = price

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        if value < 0:
            raise ValueError("цена не может быть отрицательной")
        self._price = value

    @property
    def price_with_discount(self):
        return round(self._price * 0.9, 2)

p = Product("Книга", 1000)
print(p.price)
print(p.price_with_discount)
p.price = 500
print(p.price, p.price_with_discount)
try:
    p.price = -1
except ValueError as error:
    print("отказ:", error)
try:
    Product("Книга", -100)
except ValueError as error:
    print("создание отклонено:", error)
```

```output
1000
900.0
500 450.0
отказ: цена не может быть отрицательной
создание отклонено: цена не может быть отрицательной
```

Цена хранится в `_price`, доступна через свойство с проверкой, а скидка
вычисляется при каждом обращении. После изменения цены скидочная цена
пересчиталась сама: её никто не забыл обновить, потому что она не хранится.
Попытка записать отрицательное значение отклонена, и прежняя цена осталась.

## Ответы на вопросы для самопроверки

1. Атрибут экземпляра хранится в экземпляре, атрибут класса — в классе и
   виден всем. Поиск идёт от экземпляра к классу, затем к базовым классам.
2. Список изменяем, и атрибут класса у всех экземпляров один: изменения видны
   всем. Число неизменяемо, поэтому общий атрибут безопасен.
3. Инкапсуляция в Python — соглашение: внутренние части помечают
   подчёркиванием, а правила проверяют в методах и свойствах.
4. Искажение имён защищает от случайного перекрытия внутреннего атрибута в
   подклассе. От прямого чтения и записи оно не защищает.
5. Сеттер вызывается при обычном присваивании, поэтому проверка работает для
   любого кода, который пишет в свойство. Отдельный метод можно забыть
   вызвать.
6. Свойство без сеттера не поддерживает запись, и Python сообщает об этом
   явно, вместо того чтобы молча проигнорировать присваивание.
