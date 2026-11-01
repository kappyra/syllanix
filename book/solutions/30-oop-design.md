---
chapter: ch-30-oop-design
number: 30
exercise_count: 10
---

# Решения к главе 30

Решения показывают, как проектные решения выглядят в коде: разделение
обязанностей, передача зависимостей, композиция и собственные исключения.

## 1. Прогноз вывода {#sol-ch30-01}

```python exec
class Order:
    def __init__(self, title, rows):
        self.title = title
        self.rows = rows

    def total(self):
        return sum(row["amount"] for row in self.rows)

class OrderFormatter:
    def __init__(self, width=20):
        self.width = width

    def format(self, order):
        lines = [order.title]
        for row in order.rows:
            lines.append(f"{row['name']:<{self.width}} {row['amount']}")
        lines.append(f"{'Итого':<{self.width}} {order.total()}")
        return "\n".join(lines)

order = Order("Продажи", [{"name": "Книга", "amount": 500}, {"name": "Ручка", "amount": 50}])
print(OrderFormatter().format(order))
```

```output
Продажи
Книга                500
Ручка                50
Итого                550
```

`Order` хранит данные и умеет считать сумму, `OrderFormatter` отвечает за
вид. Форматер не меняет заказ и не знает, откуда взялись строки; заказ не
знает, как его напечатают. Ширина выравнивания — настройка форматера, а не
свойство данных.

## 2. Разделение обязанностей {#sol-ch30-02}

```python exec
class Report:
    def __init__(self, rows):
        self.rows = rows

    def total(self):
        return sum(row["amount"] for row in self.rows)

class ReportPrinter:
    def print_report(self, report):
        for row in report.rows:
            print(row["name"], row["amount"])
        print("Итого:", report.total())

report = Report([{"name": "Книга", "amount": 500}, {"name": "Ручка", "amount": 50}])
ReportPrinter().print_report(report)
```

```output
Книга 500
Ручка 50
Итого: 550
```

Вывод не изменился, но причин для изменения стало две вместо одной: данные
меняются отдельно от печати. Если понадобится другой формат (например, с
заголовком), правится только `ReportPrinter`. Если появится новое поле
строки, правится `Report`.

## 3. Связанность через зависимость {#sol-ch30-03}

```python exec
class MemoryConnection:
    def __init__(self):
        self.messages = []

    def send(self, text):
        self.messages.append(text)

class Mailer:
    def __init__(self, connection):
        self.connection = connection

    def send_welcome(self, name):
        self.connection.send("Добро пожаловать, " + name)
        return "отправлено"

connection = MemoryConnection()
mailer = Mailer(connection)
print(mailer.send_welcome("Аня"))
print(connection.messages)
```

```output
отправлено
['Добро пожаловать, Аня']
```

`Mailer` больше не создаёт соединение сам: он получает объект с методом
`send` и вызывает его. В тесте подставляется `MemoryConnection`, который
ничего не отправляет наружу. Связанность снизилась: класс зависит от
маленького контракта, а не от конкретной реализации сети.

## 4. Композиция вместо наследования {#sol-ch30-04}

```python exec
class FileWriter:
    def __init__(self):
        self.lines = []

    def write(self, text):
        self.lines.append(text)

class FileLogger:
    def __init__(self, writer):
        self.writer = writer

    def log(self, message):
        self.writer.write("log: " + message)
        return len(self.writer.lines)

writer = FileWriter()
logger = FileLogger(writer)
print(logger.log("старт"))
print(writer.lines)
```

```output
1
['log: старт']
```

`FileLogger` не является записывателем файла, он им пользуется. Если
понадобится писать в память, достаточно передать другой объект с методом
`write`. При наследовании логгер получил бы все остальные методы писателя,
включая те, что к журналу не относятся, и его интерфейс стал бы шире
необходимого.

## 5. Собственное исключение {#sol-ch30-05}

```python exec
class NegativeQuantity(ValueError):
    def __init__(self, quantity, message):
        super().__init__(message)
        self.quantity = quantity

def create_item(name, quantity):
    if quantity <= 0:
        raise NegativeQuantity(quantity, f"количество должно быть положительным: {name}")
    return {"name": name, "quantity": quantity}

print(create_item("Книга", 3))
try:
    create_item("Ручка", 0)
except NegativeQuantity as error:
    print("отказ:", error, "| quantity:", error.quantity)
```

```output
{'name': 'Книга', 'quantity': 3}
отказ: количество должно быть положительным: Ручка | quantity: 0
```

Исключение наследует `ValueError`, поэтому код, который уже ловил ошибки
значений, продолжает работать. Дополнительное поле `quantity` позволяет
обработать ошибку по данным, а не разбирать текст сообщения. Сообщение
собирается в момент ошибки, поэтому в нём есть имя товара.

## 6. API с настройками {#sol-ch30-06}

```python exec
def render_report(rows, *, title="Отчёт", width=20, with_total=True):
    if width < 5:
        raise ValueError("ширина должна быть не меньше 5")
    lines = [title]
    for row in rows:
        lines.append(f"{row['name']:<{width}} {row['amount']}")
    if with_total:
        lines.append(f"{'Итого':<{width}} {sum(row['amount'] for row in rows)}")
    return "\n".join(lines)

rows = [{"name": "Книга", "amount": 500}, {"name": "Ручка", "amount": 50}]
print(render_report(rows, title="Продажи", width=10))
print(render_report(rows, width=5, with_total=False))
```

```output
Продажи
Книга      500
Ручка      50
Итого      550
Отчёт
Книга 500
Ручка 50
```

Настройки доступны только по имени, поэтому вызов читается как набор
уточнений: `title=...`, `width=...`. Проверка ширины стоит в начале функции:
ошибка обнаруживается до формирования строк, и сообщение объясняет, что
не так. Второй вызов показывает, что значения по умолчанию позволяют
короткую запись, а `with_total=False` отключает итог.

## 7. Анализ связности {#sol-ch30-07}

Четыре обязанности — четыре класса: `Loader` читает данные, `Validator`
проверяет и преобразует, `Sorter` упорядочивает, `Storage` сохраняет. У
каждого одна причина для изменения: формат файла, правила проверки,
порядок сортировки, место хранения.

```python exec
class Loader:
    def load(self):
        return ["3", "1", "2"]

class Validator:
    def check(self, rows):
        for row in rows:
            if not row.isdigit():
                raise ValueError("ожидалось число")
        return [int(row) for row in rows]

class Sorter:
    def sort(self, values):
        return sorted(values)

class Storage:
    def __init__(self):
        self.saved = []

    def save(self, values):
        self.saved = list(values)

values = Validator().check(Loader().load())
ordered = Sorter().sort(values)
storage = Storage()
storage.save(ordered)
print(storage.saved)
```

```output
[1, 2, 3]
```

Если бы всё это жило в одном классе, изменение формата файла затрагивало бы
класс, в котором также проверка, сортировка и сохранение. Ошибка в одной
части требовала бы прогонять сценарии остальных. Разделение даёт
возможность проверить каждую часть отдельно и заменить её, не трогая
остальные.

## 8. Исключение с данными {#sol-ch30-08}

```python exec
class InsufficientFunds(ValueError):
    def __init__(self, balance, amount):
        super().__init__(f"нужно {amount}, доступно {balance}")
        self.balance = balance
        self.amount = amount

class Account:
    def __init__(self, balance=0):
        self._balance = balance

    def withdraw(self, amount):
        if amount > self._balance:
            raise InsufficientFunds(self._balance, amount)
        self._balance -= amount
        return self._balance

acc = Account(100)
print(acc.withdraw(30))
try:
    acc.withdraw(500)
except InsufficientFunds as error:
    print("отказ:", error, "| баланс:", error.balance)
```

```output
70
отказ: нужно 500, доступно 70 | баланс: 70
```

Исключение несёт и текст, и данные: вызывающий код может показать
пользователю сообщение или построить свой текст из полей. Важно, что
исключение поднимает метод, который владеет инвариантом: проверка не
размазана по вызывающему коду.

## 9. Мини-проект: сервис заказов {#sol-ch30-09}

```python exec
from dataclasses import dataclass

@dataclass
class Order:
    order_id: int
    amount: int

class InMemoryOrders:
    def __init__(self):
        self.items = []

    def save(self, order):
        self.items.append(order)
        return order.order_id

class OrderService:
    def __init__(self, storage):
        self.storage = storage

    def place(self, order):
        if order.amount <= 0:
            raise ValueError("сумма заказа должна быть положительной")
        return self.storage.save(order)

storage = InMemoryOrders()
service = OrderService(storage)
print(service.place(Order(1, 500)))
try:
    service.place(Order(2, 0))
except ValueError as error:
    print("отказ:", error)
print(len(storage.items))
```

```output
1
отказ: сумма заказа должна быть положительной
1
```

Сервис проверяет правило и передаёт сохранение хранилищу. Хранилище не
знает правил, а сервис не знает, как хранятся заказы. После отказа в
хранилище по-прежнему один заказ: исключение поднято до сохранения, и
частичного результата не осталось. Это важное свойство дизайна: проверка
стоит до побочного эффекта.

## 10. Рефакторинг большого класса {#sol-ch30-10}

```python exec
class Catalog:
    def __init__(self):
        self.items = []

    def add(self, name, price, quantity):
        self.items.append({"name": name, "price": price, "quantity": quantity})

class Cart:
    def __init__(self, items, discount=0):
        self.items = items
        self.discount = discount

    def total(self):
        amount = sum(item["price"] * item["quantity"] for item in self.items)
        return round(amount * (1 - self.discount), 2)

class ReceiptPrinter:
    def print_receipt(self, cart):
        for item in cart.items:
            print(item["name"], item["price"] * item["quantity"])
        print("Итого:", cart.total())

catalog = Catalog()
catalog.add("Книга", 500, 2)
catalog.add("Ручка", 50, 1)
cart = Cart(catalog.items, discount=0.1)
ReceiptPrinter().print_receipt(cart)
```

```output
Книга 1000
Ручка 50
Итого: 945.0
```

Каталог отвечает за состав товаров, корзина — за расчёт с учётом скидки,
принтер — за вид чека. Скидку можно изменить, не трогая печать; формат чека
можно заменить, не трогая расчёт. Обратите внимание на округление в
`total`: деньги считают с фиксированной точностью, и это решение принадлежит
корзине, а не принтеру.

## Ответы на вопросы для самопроверки

1. Связность — мера сосредоточенности класса на одной ответственности.
   Низкая связность видна, когда методы работают с разными наборами данных
   и класс меняется по разным причинам.
2. Связанность — мера зависимости классов друг от друга. Зависимость,
   созданная внутри, привязывает класс к конкретному окружению и мешает
   тестам.
3. Композиция точнее, когда отношение «является» неверно: `Notifier`
   содержит канал, а не является им; `FileLogger` содержит писатель.
4. Наследование от стандартного исключения сохраняет совместимость: старый
   код, который ловил базовое исключение, продолжает работать.
5. Параметры только для именованных аргументов делают вызов читаемым и
   позволяют добавлять новые настройки, не меняя порядок аргументов.
6. `None` не отличает «пустой результат» от «ошибка». Исключение сообщает
   факт, причину и данные, с которыми произошла ошибка.
