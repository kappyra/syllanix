---
chapter: ch-27-inheritance
number: 27
exercise_count: 10
---

# Решения к главе 27

Решения показывают, как общий интерфейс заменяет проверки типов, а композиция
оказывается надёжнее наследования там, где нет отношения «является».

## 1. Прогноз вывода {#sol-ch27-01}

```python exec
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return "..."

class Dog(Animal):
    def speak(self):
        return "гав"

print(Dog("Рекс").speak())
print(Animal("кто-то").speak())
print(Dog("Рекс").name)
```

```output
гав
...
Рекс
```

У `Dog` есть собственный `speak`, поэтому вызывается он. У `Animal` остаётся
реализация по умолчанию. Атрибут `name` создаётся в конструкторе базового
класса и наследуется: подкласс его не объявляет, но получает.

## 2. Базовый класс и два подкласса {#sol-ch27-02}

```python exec
class Vehicle:
    def __init__(self, name, speed):
        self.name = name
        self.speed = speed

    def describe(self):
        return f"{self.name}: {self.speed} км/ч"

class Car(Vehicle):
    pass

class Truck(Vehicle):
    def describe(self):
        return super().describe() + " (грузовик)"

print(Car("Седан", 180).describe())
print(Truck("Фура", 90).describe())
```

```output
Седан: 180 км/ч
Фура: 90 км/ч (грузовик)
```

`Car` ничего не меняет и получает описание целиком от `Vehicle`. `Truck`
переопределяет `describe`, но не копирует формат: он вызывает базовую версию
через `super()` и добавляет уточнение. Если формат когда-нибудь изменится,
правка понадобится только в базовом классе.

## 3. Исправление конструктора {#sol-ch27-03}

Подкласс создаёт `breed`, но не вызывает конструктор `Animal`, поэтому
атрибут `name` не появляется. Ошибка видна:

```python exec expect-error
class Animal:
    def __init__(self, name):
        self.name = name

class Dog(Animal):
    def __init__(self, name, breed):
        self.breed = breed

d = Dog("Рекс", "лабрадор")
print(d.name)
```

```output
AttributeError: 'Dog' object has no attribute 'name'
```

Исправление — вызвать базовый конструктор до собственных действий:

```python exec
class Animal:
    def __init__(self, name):
        self.name = name

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)
        self.breed = breed

d = Dog("Рекс", "лабрадор")
print(d.name, d.breed)
```

```output
Рекс лабрадор
```

## 4. Расширение через super() {#sol-ch27-04}

```python exec
class Logger:
    def log(self, message):
        return ["log: " + message]

class TimestampLogger(Logger):
    def log(self, message):
        records = super().log(message)
        records.append("готово")
        return records

print(TimestampLogger().log("старт"))
```

```output
['log: старт', 'готово']
```

Подкласс получил список от базового метода и дополнил его. Обратите
внимание: `super().log(message)` возвращает новый список, а `append`
изменяет уже его. Такой приём называется расширением поведения: базовый
метод остаётся единственным местом, где формируется формат записи.

## 5. Полиморфная функция {#sol-ch27-05}

```python exec
class Square:
    def __init__(self, side):
        self.side = side

    def area(self):
        return self.side ** 2

class Circle:
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return round(3.14159 * self.radius ** 2, 2)

def total(shapes):
    return round(sum(shape.area() for shape in shapes), 2)

print(total([Square(3), Circle(2)]))
```

```output
21.57
```

Функция `total` не содержит проверок типа: она вызывает `area` у каждого
объекта. Квадрат и круг не связаны наследованием, но следуют одному
интерфейсу. Округление применяется и внутри `Circle.area`, и в `total`,
поэтому сумма не накапливает ошибку представления.

## 6. isinstance против type {#sol-ch27-06}

```python exec
class Animal:
    pass

class Dog(Animal):
    pass

d = Dog()
print(isinstance(d, Dog), isinstance(d, Animal), type(d) is Dog, type(d) is Animal)
print(issubclass(Dog, Animal), issubclass(Animal, Dog))
```

```output
True True True False
True False
```

`isinstance` учитывает наследование и отвечает на вопрос «является ли объект
экземпляром этого класса или его подкласса». `type` возвращает ровно класс
объекта, поэтому `type(d) is Animal` ложно. `issubclass` задаёт тот же вопрос
про классы, а не про объекты: собака — подкласс животного, но не наоборот.

## 7. Порядок разрешения методов {#sol-ch27-07}

```python exec
class A:
    def who(self):
        return "A"

class B(A):
    def who(self):
        return "B + " + super().who()

class C(A):
    def who(self):
        return "C + " + super().who()

class D(B, C):
    pass

print(D().who())
print([cls.__name__ for cls in D.__mro__])
```

```output
B + C + A
['D', 'B', 'C', 'A', 'object']
```

Порядок поиска: `D`, `B`, `C`, `A`, `object`. У `D` своего метода нет,
поэтому работает `B.who`. Его `super()` идёт дальше по цепочке и попадает в
`C`, а не в `A`. Затем `C.who` вызывает `super().who()`, и теперь очередь
`A`. Результат складывается из трёх частей. Это прямое следствие того, что
`super()` означает «следующий в порядке разрешения методов», а не «прямой
родитель».

## 8. Композиция {#sol-ch27-08}

```python exec
class Logger:
    def __init__(self):
        self.lines = []

    def write(self, message):
        self.lines.append(message)

class Report:
    def __init__(self, title, logger):
        self.title = title
        self.logger = logger

    def build(self):
        self.logger.write("отчёт: " + self.title)
        return {"title": self.title, "lines": list(self.logger.lines)}

logger = Logger()
print(Report("Продажи", logger).build())
print(isinstance(Report("x", logger), Logger))
```

```output
{'title': 'Продажи', 'lines': ['отчёт: Продажи']}
False
```

`Report` содержит логгер и вызывает его метод — это композиция. Отчёт не
является логгером, поэтому `isinstance` даёт `False`, и это правильно.
Логгер можно заменить другой реализацией с тем же методом `write`, не меняя
класс отчёта.

## 9. Стек без наследования {#sol-ch27-09}

```python exec
class Stack:
    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        return self._items.pop()

    def size(self):
        return len(self._items)

s = Stack()
s.push("a")
s.push("b")
print(s.pop(), s.size())
print(hasattr(s, "append"))
```

```output
b 1
False
```

Внутренний список `_items` не входит в интерфейс: у класса нет метода
`append`, поэтому случайно обойти правило «только в конец» нельзя. Сознательно
это возможно через `s._items.append(...)`, но такое обращение — явное нарушение
соглашения об имени. Если бы `Stack` наследовал `list`, методы `append`,
`insert` и `extend` были бы частью публичного интерфейса и позволяли нарушить
порядок без всяких соглашений.

## 10. Мини-проект: расчёт зарплат {#sol-ch27-10}

```python exec
class Employee:
    def __init__(self, name, base):
        self.name = name
        self.base = base

    def salary(self):
        return self.base

class Manager(Employee):
    def __init__(self, name, base, bonus):
        super().__init__(name, base)
        self.bonus = bonus

    def salary(self):
        return self.base + self.bonus

class Intern(Employee):
    def salary(self):
        return round(self.base * 0.5)

staff = [Employee("Аня", 100), Manager("Боря", 100, 50), Intern("Вера", 100)]
for person in staff:
    print(person.name, person.salary())
print(round(sum(person.salary() for person in staff), 2))
```

```output
Аня 100
Боря 150
Вера 50
300
```

Функция подсчёта обращается к `person.salary()` и не проверяет тип: любой
сотрудник умеет сообщить свою зарплату. Новый вид сотрудника подключается
без правки цикла и суммы. `Manager` дополняет базовый конструктор премией,
а `Intern` переопределяет расчёт целиком — оба варианта используют один
интерфейс.

## Ответы на вопросы для самопроверки

1. Наследование описывает отношение «является» (собака является животным),
   композиция — «содержит» (автомобиль содержит двигатель).
2. `super()` даёт доступ к следующему классу в порядке разрешения методов.
   При множественном наследовании следующий класс не обязан быть прямым
   родителем.
3. Метод с `NotImplementedError` объявляет обязательный интерфейс и
   напоминает, что подкласс должен реализовать поведение.
4. `isinstance` учитывает наследование, `type(d) is X` — нет: он сравнивает
   ровно класс объекта.
5. Цепочку `isinstance` нужно править при каждом новом классе, а общий
   интерфейс подключает новые классы без изменений.
6. Наследник `list` получает все методы родителя, включая те, что позволяют
   нарушить правила стека; композиция показывает только нужные операции.
