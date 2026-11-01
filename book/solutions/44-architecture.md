---
chapter: ch-44-architecture
number: 44
exercise_count: 10
---

# Решения к главе 44

Решения отделены от условий. В задачах об архитектуре главное — объяснить
решение, а не только получить работающий код: почти любую структуру можно
сделать по-разному, и выбор нужно защитить.

## 1. Слои и импорты {#sol-ch44-01}

Текущие зависимости выглядят так:

```text
app.py      → handlers.py
storage.py  → handlers.py
domain.py   → sqlite3
handlers.py → (импортов инфраструктуры нет)
```

Нарушений два. Первое: `domain.py` импортирует `sqlite3`, то есть правила
предметной области зависят от конкретной базы. Второе: `storage.py`
импортирует `handlers.py` — инфраструктура зависит от представления, хотя
должна зависеть только от домена. Кроме того, расчёт скидки живёт в
`handlers.py`, то есть бизнес-логика оказалась в слое представления.

Исправление: расчёт скидки переносится в `domain.py` без импортов
инфраструктуры; `storage.py` реализует интерфейс, объявленный в домене или
приложении, и зависит только от него; `handlers.py` вызывает приложение, а не
содержит правила; `app.py` собирает объекты вместе. Направление зависимостей
становится однонаправленным: представление → приложение → домен, а
инфраструктура подключается к домену через интерфейс.

## 2. Единственная ответственность {#sol-ch44-02}

```python exec
class Invoice:
    def __init__(self, items):
        self.items = items
    def total(self):
        return sum(price * quantity for price, quantity in self.items)

class InvoiceFormatter:
    def format(self, invoice):
        return f"позиций: {len(invoice.items)}, итог: {invoice.total()}"

class InvoiceNotifier:
    def __init__(self):
        self.sent = []
    def send(self, address, text):
        self.sent.append((address, text))
        return True

invoice = Invoice([(100, 2), (50, 3)])
formatter = InvoiceFormatter()
notifier = InvoiceNotifier()
text = formatter.format(invoice)
print(text)
print("отправлено:", notifier.send("client@example.com", text))
```

```output
позиций: 2, итог: 350
отправлено: True
```

Три причины изменения и три владельца требований: правила расчёта меняет
бухгалтерия, формат письма — поддержка клиентов, способ доставки — команда
инфраструктуры. Пока всё в одном классе, любое требование заставляет менять
его целиком и проверять остальные функции заново. После разделения каждая
часть меняется независимо.

## 3. Открытость для расширения {#sol-ch44-03}

```python exec
class CountryRate:
    def __init__(self, base, per_kg):
        self.base = base
        self.per_kg = per_kg
    def cost(self, weight):
        return self.base + weight * self.per_kg

class ShippingCost:
    def __init__(self, rates):
        self.rates = rates
    def cost(self, country, weight):
        rate = self.rates.get(country)
        if rate is None:
            raise ValueError(f"нет тарифа для страны {country!r}")
        return rate.cost(weight)

rates = {
    "RU": CountryRate(300, 50),
    "KZ": CountryRate(500, 70),
}
shipping = ShippingCost(rates)
print(shipping.cost("RU", 2))
print(shipping.cost("KZ", 2))
try:
    shipping.cost("US", 2)
except ValueError as error:
    print("ValueError:", error)
```

```output
400
640
ValueError: нет тарифа для страны 'US'
```

Для изменения закрыт сам расчёт: `ShippingCost.cost` не знает, сколько стран
существует и какие у них формулы. Для расширения открыт словарь тарифов:
новая страна добавляется записью, а если формула отличается — новым классом с
методом `cost`. Цепочка `if country == ...` исчезла, и вместе с ней исчезла
необходимость править функцию при каждом новом тарифе.

## 4. Нарушение подстановки {#sol-ch44-04}

`ReadOnlyList`, наследующий `list`, ломает любую функцию, которая ожидает
изменяемый список и вызывает `append`. Клиент получает `ValueError` там, где
по контракту `list` ошибки быть не может, значит подстановка неверна.
Исправление — не наследовать изменяемость, а зависеть от возможности чтения.

```python exec
from typing import Protocol

class Readable(Protocol):
    def all(self):
        ...

class MutableList:
    def __init__(self, items):
        self._items = list(items)
    def all(self):
        return list(self._items)
    def add(self, item):
        self._items.append(item)

class ReadOnlyView:
    def __init__(self, items):
        self._items = list(items)
    def all(self):
        return list(self._items)

def total_items(collection):
    return len(collection.all())

print(total_items(MutableList([1, 2, 3])))
print(total_items(ReadOnlyView([1, 2, 3])))
```

```output
3
3
```

Функция `total_items` требует только чтения, поэтому обе реализации
подходят. Клиенту, которому нужно изменение, передают `MutableList`, и
вопрос «а можно ли сюда писать» решается на уровне типа, а не исключением во
время выполнения.

## 5. Разделение интерфейсов {#sol-ch44-05}

```python exec
from typing import Protocol

class Reader(Protocol):
    def read(self, name):
        ...

class Writer(Protocol):
    def write(self, name, data):
        ...

class FileStorage:
    def __init__(self):
        self.data = {}
    def read(self, name):
        return self.data[name]
    def write(self, name, data):
        self.data[name] = data

def export(storage, name):
    return storage.read(name).upper()

storage = FileStorage()
storage.write("report", "итог: 900")
print(export(storage, "report"))
```

```output
ИТОГ: 900
```

`export` зависит только от `Reader`: клиенту, который читает, не нужны
`write`, `delete` и `list`. Если разделить интерфейс на части, каждую
реализацию можно проверить отдельно, а заглушка для теста чтения содержит
один метод вместо четырёх. Большой протокол удобен автору библиотеки и
неудобен клиенту — принцип требует думать о клиенте.

## 6. Инверсия зависимостей {#sol-ch44-06}

Сервис, создающий `SmtpClient` внутри конструктора, невозможно проверить без
сети и невозможно переключить на другой канал. Зависимость нужно передавать
снаружи.

```python exec
class FakeNotifier:
    def __init__(self):
        self.sent = []
    def send(self, address, text):
        self.sent.append((address, text))

class EmailNotifier:
    def send(self, address, text):
        return f"письмо на {address}: {text}"

class NotificationService:
    def __init__(self, notifier):
        self.notifier = notifier
    def welcome(self, address):
        self.notifier.send(address, "добро пожаловать")
        return True

fake = FakeNotifier()
service = NotificationService(fake)
print("результат:", service.welcome("anna@example.com"))
print("вызовы:", fake.sent)
print("настоящий клиент:", EmailNotifier().send("anna@example.com", "привет"))
```

```output
результат: True
вызовы: [('anna@example.com', 'добро пожаловать')]
настоящий клиент: письмо на anna@example.com: привет
```

`NotificationService` зависит от абстракции «кто-то умеет отправлять
сообщение», а не от SMTP. В тесте подставляется заглушка, в работе — реальный
клиент. Обратите внимание: интерфейс объявлять не обязательно, достаточно
того, что обе реализации имеют метод `send` с одинаковым смыслом; но для
явности контракта протокол полезен.

## 7. Внедрение зависимостей {#sol-ch44-07}

```python exec
class FixedRates:
    def __init__(self, rates):
        self.rates = rates
    def rate(self, currency):
        return self.rates[currency]

class LoggingRates:
    def __init__(self, rates):
        self.rates = rates
        self.calls = []
    def rate(self, currency):
        self.calls.append(currency)
        return self.rates[currency]

class PriceService:
    def __init__(self, rates):
        self.rates = rates
    def convert(self, amount, currency):
        return amount * self.rates.rate(currency) // 100

print("фиксированные:", PriceService(FixedRates({"USD": 9000})).convert(10000, "USD"))
logging_rates = LoggingRates({"USD": 9000})
print("с журналом:", PriceService(logging_rates).convert(10000, "USD"))
print("обращения:", logging_rates.calls)
```

```output
фиксированные: 900000
с журналом: 900000
обращения: ['USD']
```

Расчёт одинаков, различается только источник курса. Заглушка с журналом
показывает, какие валюты запрашивались, — это удобно для тестов и отладки.
Внедрение через конструктор делает зависимость обязательной: сервис нельзя
случайно создать без источника курсов.

## 8. Адаптер {#sol-ch44-08}

```python exec
class ThirdPartyClient:
    def fetch(self, city):
        return {"temp": 21, "code": city}

class WeatherAdapter:
    def __init__(self, client):
        self.client = client
    def get_forecast(self, city_code):
        raw = self.client.fetch(city_code)
        return {"temperature_c": raw["temp"], "city_code": raw["code"]}

adapter = WeatherAdapter(ThirdPartyClient())
forecast = adapter.get_forecast("MSK")
print("температура:", forecast["temperature_c"])
print("код города:", forecast["city_code"])
```

```output
температура: 21
код города: MSK
```

Адаптер переводит одно представление в другое и изолирует остальную
программу от формата чужого клиента. Если библиотека обновится и переименует
поля, изменится только адаптер; вызывающий код продолжит работать. В тестах
адаптер позволяет подставить клиент с заранее заданным ответом без сети.

## 9. Репозиторий {#sol-ch44-09}

```python exec
import sqlite3

class InMemoryNoteRepository:
    def __init__(self):
        self.items = []
    def add(self, text):
        self.items.append(text)
        return len(self.items)
    def all(self):
        return list(self.items)

class SqliteNoteRepository:
    def __init__(self, connection):
        self.connection = connection
        self.connection.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, text TEXT)")
    def add(self, text):
        cursor = self.connection.execute("INSERT INTO notes (text) VALUES (?)", (text,))
        return cursor.lastrowid
    def all(self):
        rows = self.connection.execute("SELECT text FROM notes ORDER BY id")
        return [row[0] for row in rows]

def render(repository):
    return " | ".join(repository.all())

memory = InMemoryNoteRepository()
memory.add("первая")
memory.add("вторая")
print("в памяти:", render(memory))

connection = sqlite3.connect(":memory:")
sqlite_repo = SqliteNoteRepository(connection)
sqlite_repo.add("первая")
sqlite_repo.add("вторая")
print("в базе:", render(sqlite_repo))
```

```output
в памяти: первая | вторая
в базе: первая | вторая
```

Функция `render` не знает, откуда берутся заметки. Возможности репозитория
заканчиваются там, где начинаются запросы, специфичные для базы: сложная
фильтрация, соединения, полнотекстовый поиск. Если добавить их в интерфейс,
он начнёт повторять SQL и превратится в протекающую абстракцию. Разумная
граница — операции, которые нужны домену: получить, сохранить, найти по
простому признаку. Сложные запросы лучше выносить в отдельные
специализированные методы с понятными именами.

## 10. Мини-задача: оформление заказа {#sol-ch44-10}

```python exec
from typing import Protocol

class OrderRepository(Protocol):
    def save(self, order_id: str, total: int) -> None: ...
    def get(self, order_id: str) -> int | None: ...

class InMemoryOrders:
    def __init__(self):
        self._data = {}
    def save(self, order_id, total):
        self._data[order_id] = total
    def get(self, order_id):
        return self._data.get(order_id)

def order_total(amount, percent):
    return amount - amount * percent // 100

class OrderService:
    def __init__(self, repository):
        self.repository = repository
    def place(self, order_id, amount, percent):
        total = order_total(amount, percent)
        self.repository.save(order_id, total)
        return total

def format_order(order_id, total):
    return f"заказ {order_id}: {total} ₽"

repository = InMemoryOrders()
service = OrderService(repository)
total = service.place("A-1", 1000, 10)
print(format_order("A-1", total))
print("в хранилище:", repository.get("A-1"))
```

```output
заказ A-1: 900 ₽
в хранилище: 900
```

Три слоя разделены по ответственности. Домен — функция `order_total`: она
считает правило и ничего не знает о хранении. Приложение — `OrderService`: оно
проводит сценарий и работает с хранилищем через протокол. Представление —
`format_order`: превращает результат в строку. Тест подставляет
`InMemoryOrders` и проверяет итог без базы. Если завтра появится SQLite,
изменится только реализация репозитория, а домен и представление останутся
прежними.

## Ответы на вопросы для самопроверки

1. Направление зависимостей: хорошая архитектура делает изменение дешёвым
   благодаря односторонним зависимостям и границам, а не названиям каталогов.
2. Связность — про единство задачи внутри части; связанность — про
   зависимости между частями. Хорошая архитектура повышает первую и понижает
   вторую.
3. Домен должен проверяться без базы и сети; импорт деталей делает его
   зависимым от инфраструктуры и усложняет тесты.
4. У класса одна причина для изменения — одна группа требований, которая
   может заставить его меняться.
5. Подстановочность требует, чтобы клиент не замечал замены: важны обещания
   поведения, а не факт наследования.
6. Инверсия зависимостей — принцип о направлении зависимостей к абстракциям;
   внедрение зависимостей — приём передачи готовых объектов снаружи.
7. Адаптер оправдан при несовпадении интерфейсов, особенно для чужого кода;
   без такого несовпадения это лишний слой.
8. Репозиторий протекает, когда его интерфейс повторяет возможности базы;
   лечится специализированными методами и честным признанием границ.
