---
chapter: ch-43-metaprogramming
number: 43
exercise_count: 10
---

# Решения к главе 43

Решения отделены от условий. В этой главе важно не только получить рабочий
код, но и объяснить, почему выбранный механизм уместен. Запускайте примеры:
все выводы детерминированы.

## 1. Порядок поиска {#sol-ch43-01}

`property` — data-дескриптор: у него есть `__set__`, поэтому при чтении он
стоит в порядке поиска раньше словаря экземпляра. Значение из `__dict__`
игнорируется, `instance.price` вернёт то, что вычисляет `property`, то есть
`100`.

Если заменить `property` на объект только с `__get__` (non-data дескриптор),
порядок изменится: словарь экземпляра проверяется раньше non-data дескриптора,
и атрибут вернёт `999`. Показать это можно так:

```python exec
class DataDescriptor:
    def __get__(self, instance, owner=None):
        return "из дескриптора"
    def __set__(self, instance, value):
        pass

class NonDataDescriptor:
    def __get__(self, instance, owner=None):
        return "из дескриптора"

class WithData:
    field = DataDescriptor()

class WithNonData:
    field = NonDataDescriptor()

with_data = WithData()
with_data.__dict__["field"] = "из словаря"
with_nondata = WithNonData()
with_nondata.__dict__["field"] = "из словаря"
print("data:", with_data.field)
print("non-data:", with_nondata.field)
```

```output
data: из дескриптора
non-data: из словаря
```

Различие практическое: если нужен полный контроль над атрибутом, дескриптор
делают data-дескриптором, добавляя `__set__` (и, при необходимости,
`__delete__`).

## 2. Проверяющий дескриптор {#sol-ch43-02}

```python exec
class Bounded:
    def __init__(self, minimum, maximum):
        self.minimum = minimum
        self.maximum = maximum

    def __set_name__(self, owner, name):
        self.name = f"_{name}"

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return getattr(instance, self.name)

    def __set__(self, instance, value):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError("ожидается число")
        if not self.minimum <= value <= self.maximum:
            raise ValueError(f"значение вне диапазона {self.minimum}..{self.maximum}")
        setattr(instance, self.name, value)

class Sensor:
    temperature = Bounded(-50, 150)

sensor = Sensor()
sensor.temperature = 21
print("температура:", sensor.temperature)
try:
    sensor.temperature = 200
except ValueError as error:
    print("ValueError:", error)
```

```output
температура: 21
ValueError: значение вне диапазона -50..150
```

`__set_name__` избавляет от ручной передачи имени: дескриптор сам узнаёт, что
он объявлен как `temperature`, и хранит значение в `_temperature`. Проверка
типа отделена от проверки диапазона: `True` не должно считаться числом 1,
поэтому `bool` исключён явно.

## 3. `__set_name__` {#sol-ch43-03}

```python exec
class Field:
    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = "_" + name
    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return getattr(instance, self.private_name)
    def __set__(self, instance, value):
        setattr(instance, self.private_name, value)

class Point:
    x = Field()
    y = Field()
    def __init__(self, x, y):
        self.x = x
        self.y = y

point = Point(1, 2)
print("имена:", Point.x.public_name, Point.y.public_name)
print("хранение:", sorted(point.__dict__))
print("чтение:", point.x, point.y)
```

```output
имена: x y
хранение: ['_x', '_y']
чтение: 1 2
```

`__set_name__` вызывается автоматически при создании класса, сразу после
создания его пространства имён. Именно поэтому дескриптор знает своё имя без
дополнительных аргументов. Если назначить дескриптор атрибутом после создания
класса (`Point.z = Field()`), `__set_name__` не вызовется: он выполняется
только на этапе создания класса. Такой атрибут работать не будет, пока имя не
задано вручную.

## 4. `__getattr__` или `__getattribute__` {#sol-ch43-04}

Нужен `__getattr__`: он вызывается только тогда, когда обычный поиск не нашёл
атрибут. Это ровно случай «значение по умолчанию для отсутствующего ключа».
`__getattribute__` перехватывает все обращения, включая доступ к служебным
полям, и требует очень аккуратной реализации, иначе объект ломается.

```python exec
class Defaults:
    def __init__(self, values):
        self.values = values
    def __getattr__(self, name):
        if name in {"values"}:
            raise AttributeError(name)
        return self.values.get(name, 0)

settings = Defaults({"timeout": 30})
print("есть ключ:", settings.timeout)
print("нет ключа:", settings.retries)
print("обычное поле работает:", settings.values == {"timeout": 30})
```

```output
есть ключ: 30
нет ключа: 0
обычное поле работает: True
```

Строка `if name in {"values"}` защищает от рекурсии: если `__getattr__`
обратится к `self.values`, а его ещё нет, произойдёт бесконечный вызов.
Проверка на служебные имена — минимальная страховка.

## 5. Опечатка в динамическом атрибуте {#sol-ch43-05}

`__getattr__`, возвращающий `None` для любого имени, маскирует ошибки. Пример
первый: `config.timout` вместо `config.timeout` молча даёт `None`, и
программа продолжает работу с неверным значением. Пример второй: `hasattr`
возвращает `True` для любого имени, поэтому проверки вида «есть ли у объекта
такой метод» перестают что-либо значить, а библиотеки, которые полагаются на
`AttributeError`, ведут себя неправильно.

```python exec
class LooseConfig:
    def __init__(self):
        self.debug = True
    def __getattr__(self, name):
        return None

config = LooseConfig()
print("обычное поле:", config.debug)
print("опечатка:", config.timout)
print("hasattr для опечатки:", hasattr(config, "timout"))
```

```output
обычное поле: True
опечатка: None
hasattr для опечатки: True
```

Исправление — поднимать `AttributeError` для всего, что не задано явно:

```python exec
class StrictConfig:
    def __init__(self, values):
        self.debug = bool(values.get("debug", False))
        self.values = values
    def __getattr__(self, name):
        if name in {"values", "debug"}:
            raise AttributeError(name)
        try:
            return self.values[name]
        except KeyError:
            raise AttributeError(f"нет настройки {name!r}") from None

config = StrictConfig({"timeout": 30})
print("debug:", config.debug)
print("timeout:", config.timeout)
try:
    config.timout
except AttributeError as error:
    print("AttributeError:", error)
```

```output
debug: False
timeout: 30
AttributeError: нет настройки 'timout'
```

`raise ... from None` убирает из трассировки лишнюю цепочку: причина ошибки
понятна и без внутреннего `KeyError`.

## 6. Реестр подклассов {#sol-ch43-06}

```python exec
class BaseA:
    registry = {}
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseA.registry[cls.__name__] = cls

class Alpha(BaseA): pass
class Beta(BaseA): pass

class MetaB(type):
    registry = {}
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if name != "PluginB":
            MetaB.registry[name] = cls
        return cls

class PluginB(metaclass=MetaB): pass
class Gamma(PluginB): pass

print("через __init_subclass__:", sorted(BaseA.registry))
print("через метакласс:", sorted(MetaB.registry))
```

```output
через __init_subclass__: ['Alpha', 'Beta']
через метакласс: ['Gamma']
```

`__init_subclass__` короче и понятнее: это обычный метод базового класса,
который вызывается при создании подкласса. Метакласс даёт больше: он видит
создание самого базового класса, может менять его пространство имён до
создания и управлять всеми классами с этим метаклассом, включая базовый.
Метакласс нужен, когда поведение должно применяться к классу и его потомкам
независимо от их кода, — например, в ORM, где метакласс собирает описание
таблицы из объявленных полей.

## 7. Декоратор класса {#sol-ch43-07}

Наивный декоратор, который просто присваивает `__slots__`, не работает:
`__slots__` учитывается только при создании класса. Чтобы получить эффект,
класс нужно создать заново.

```python exec
def with_slots(*fields):
    def decorate(cls):
        namespace = {name: value for name, value in vars(cls).items()
                     if name not in {"__dict__", "__weakref__"}}
        namespace["__slots__"] = fields
        return type(cls)(cls.__name__, cls.__bases__, namespace)
    return decorate

@with_slots("x", "y")
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

point = Point(1, 2)
print("x, y:", point.x, point.y)
try:
    point.z = 3
except AttributeError:
    print("лишний атрибут отклонён:", True)
```

```output
x, y: 1 2
лишний атрибут отклонён: True
```

Декоратор собирает пространство имён существующего класса, убирает служебные
записи `__dict__` и `__weakref__`, добавляет `__slots__` и создаёт класс
заново через `type`. Это показывает, почему `__slots__` нельзя «включить»
после создания класса: он должен присутствовать в момент, когда класс
собирается.

## 8. Метод как дескриптор {#sol-ch43-08}

```python exec
class Greeter:
    def hello(self):
        return "привет"

greeter = Greeter()
print("атрибут класса:", type(Greeter.hello).__name__)
print("атрибут экземпляра:", type(greeter.hello).__name__)
print("вызов:", greeter.hello())
```

```output
атрибут класса: function
атрибут экземпляра: method
вызов: привет
```

Функция — non-data дескриптор: у неё есть `__get__`. При обращении через
класс `__get__` получает `instance=None` и возвращает саму функцию. При
обращении через экземпляр `__get__` получает этот экземпляр и возвращает
связанный метод — объект, который при вызове подставляет экземпляр первым
аргументом. Именно поэтому `self` не передаётся вручную.

## 9. Кэширующий дескриптор {#sol-ch43-09}

```python exec
class Lazy:
    def __init__(self, function):
        self.function = function

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        value = self.function(instance)
        instance.__dict__[self.name] = value
        return value

class Report:
    def __init__(self, rows):
        self.rows = rows

    @Lazy
    def total(self):
        print("вычисляем итог")
        return sum(self.rows)

report = Report([1, 2, 3])
print("первое чтение:", report.total)
print("второе чтение:", report.total)
print("в словаре:", report.__dict__["total"])
```

```output
вычисляем итог
первое чтение: 6
второе чтение: 6
в словаре: 6
```

Дескриптор non-data: после первого вычисления значение попадает в словарь
экземпляра, и при следующем чтении поиск находит его раньше дескриптора.
Если добавить `__set__`, дескриптор станет data-дескриптором и будет
перехватывать чтение всегда, а значение из словаря окажется недоступным:
кэш перестанет работать, и вычисление повторится.

## 10. Мини-задача: поля с валидацией {#sol-ch43-10}

```python exec
class Validated:
    def __init__(self, checker):
        self.checker = checker

    def __set_name__(self, owner, name):
        self.name = f"_{name}"
        self.public_name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return getattr(instance, self.name)

    def __set__(self, instance, value):
        try:
            self.checker(value)
        except ValueError as error:
            raise ValueError(f"{self.public_name}: {error}") from None
        setattr(instance, self.name, value)

def non_empty(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("ожидается непустая строка")

def valid_age(value):
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 130:
        raise ValueError("ожидается целое от 0 до 130")

class User:
    name = Validated(non_empty)
    age = Validated(valid_age)
    def __init__(self, name, age):
        self.name = name
        self.age = age

user = User("анна", 30)
print("пользователь:", user.name, user.age)
try:
    user.age = 200
except ValueError as error:
    print("ValueError:", error)
try:
    user.name = "  "
except ValueError as error:
    print("ValueError:", error)
```

```output
пользователь: анна 30
ValueError: age: ожидается целое от 0 до 130
ValueError: name: ожидается непустая строка
```

Дескриптор принимает функцию-проверку и не знает, что именно она проверяет:
это делает его универсальным. Имя поля добавляется в сообщение через
`__set_name__`, поэтому ошибка сразу указывает, что исправлять. Проверка
`bool` отдельно нужна потому, что `True` в Python — подкласс `int` и без
явного исключения прошёл бы проверку возраста.

## Ответы на вопросы для самопроверки

1. Сначала данные-дескрипторы в типе, затем словарь экземпляра, затем
   остальные атрибуты типа, затем `__getattr__`.
2. Data-дескриптор имеет `__set__` или `__delete__` и стоит раньше словаря
   экземпляра; non-data — только `__get__` и уступает словарю.
3. `__set_name__` сообщает дескриптору имя, под которым он объявлен в классе,
   чтобы тот мог хранить данные под производным именем.
4. `property` — data-дескриптор, поэтому при чтении он проверяется раньше
   словаря экземпляра.
5. `__getattr__` вызывается только при неудачном поиске; `__getattribute__` —
   при любом обращении. Безопаснее `__getattr__`.
6. Метакласс — класс, экземплярами которого являются классы. У обычного класса
   метакласс `type`, поэтому `type(Order)` возвращает `type`.
7. `__init_subclass__` проще, не создаёт конфликтов метаклассов и решает
   большинство задач регистрации и настройки подклассов.
8. Метапрограммирование скрывает поведение за кодом, который не виден при
   чтении класса. Компенсация — говорящие имена, документация, тесты и выбор
   самого простого механизма.
