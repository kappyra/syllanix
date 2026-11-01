---
chapter: ch-39-asyncio
number: 39
exercise_count: 10
---

# Решения к главе 39

Решения отделены от условий, чтобы вы сначала попробовали сами. Запускайте
код и сверяйте порядок вывода: в асинхронных примерах именно порядок строк
показывает, поняли вы модель задач или нет.

## 1. Порядок строк {#sol-ch39-01}

```python exec
import asyncio

async def one():
    print("один")
    await asyncio.sleep(0)
    print("один после паузы")

async def two():
    print("два")

async def main():
    await asyncio.gather(one(), two())

asyncio.run(main())
```

```output
один
два
один после паузы
```

`gather` превращает обе корутины в задачи и запускает их по очереди. Задача
`one` печатает «один» и уступает на `sleep(0)`. Задача `two` печатает «два» и
завершается. После этого `one` возобновляется и печатает вторую строку.
Никакой случайности здесь нет: порядок задан очередью готовых задач.

## 2. Последовательное и конкурентное ожидание {#sol-ch39-02}

```python exec
import asyncio

async def step(name):
    print(f"{name}: начало")
    await asyncio.sleep(0)
    print(f"{name}: конец")

async def sequential():
    for name in ("A", "B", "C"):
        await step(name)

async def concurrent():
    await asyncio.gather(*(step(name) for name in ("A", "B", "C")))

async def main():
    print("последовательно")
    await sequential()
    print("конкурентно")
    await concurrent()

asyncio.run(main())
```

```output
последовательно
A: начало
A: конец
B: начало
B: конец
C: начало
C: конец
конкурентно
A: начало
B: начало
C: начало
A: конец
B: конец
C: конец
```

В последовательной версии каждой корутине дают завершиться полностью, прежде
чем начать следующую. В конкурентной все три доходят до точки ожидания, и
только потом выполняется продолжение. Для настоящего ввода-вывода это значит,
что общее время равно не сумме времён, а максимуму.

## 3. Исправление ошибки {#sol-ch39-03}

Корутина создаётся вызовом `report()`, но никто её не ожидает. Python не
поднимает исключение, потому что создание корутины — обычная операция: тело
не исполняется, а объект-корутина просто уничтожается сборщиком мусора
(обычно с предупреждением в stderr). Исправление — `await report()`:

```python exec
import asyncio

async def report():
    print("отчёт готов")

async def main():
    await report()

asyncio.run(main())
```

```output
отчёт готов
```

Если корутину нужно запустить как отдельную задачу, её создают через
`asyncio.create_task` и обязательно дожидаются результата.

## 4. Блокирующий вызов {#sol-ch39-04}

Пока корутина выполняет `time.sleep(1)`, она владеет потоком и цикл событий
не может запустить другие задачи: все ожидающие задачи стоят всю секунду.
Причина в том, что `time.sleep` занимает поток, а не приостанавливает задачу —
у планировщика нет точки, в которой можно переключиться.

Для ожидания нужно асинхронное ожидание, для вычислений — вынос в поток:

```python exec
import asyncio

async def wait_async():
    await asyncio.sleep(0)
    print("ожидание асинхронное")

def blocking_sum(limit):
    return sum(range(limit))

async def main():
    await wait_async()
    total = await asyncio.to_thread(blocking_sum, 100_000)
    print("сумма посчитана:", total > 0)

asyncio.run(main())
```

```output
ожидание асинхронное
сумма посчитана: True
```

`asyncio.sleep` уступает управление циклу, а `asyncio.to_thread` отправляет
синхронную функцию в рабочий поток, оставляя цикл свободным. Для долгих
вычислений, которые упираются в процессор, выгоднее процессы: GIL не даёт
потокам считать одновременно.

## 5. Отмена задачи {#sol-ch39-05}

```python exec
import asyncio

async def counter():
    total = 0
    try:
        while True:
            await asyncio.sleep(0)
            total += 1
            print("итерация", total)
    finally:
        print("итог:", total)

async def main():
    task = asyncio.create_task(counter())
    for _ in range(3):
        await asyncio.sleep(0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("отмена обработана")

asyncio.run(main())
```

```output
итерация 1
итерация 2
итог: 2
отмена обработана
```

Три `sleep(0)` дают задачи дойти до второй итерации. `cancel()` лишь
запрашивает отмену: `CancelledError` возникает в ближайшей точке `await`,
поэтому `finally` успевает напечатать итог. Пробрасывать исключение дальше
обязательно — иначе отмена будет проглочена.

## 6. Таймаут {#sol-ch39-06}

```python exec
import asyncio

async def slow():
    await asyncio.sleep(10)
    return "готово"

async def quick():
    await asyncio.sleep(0)
    return "быстро"

async def run_with_limit(coro, seconds):
    try:
        async with asyncio.timeout(seconds):
            return await coro
    except TimeoutError:
        return "таймаут"

async def main():
    print(await run_with_limit(quick(), 1))
    print(await run_with_limit(slow(), 0.01))

asyncio.run(main())
```

```output
быстро
таймаут
```

`asyncio.timeout` — асинхронный контекстный менеджер. Когда срок истекает, он
отменяет текущую задачу, и внутри блока поднимается `TimeoutError`. Мы ловим
его и возвращаем строку вместо исключения. Обратите внимание: сама `slow()`
не «останавливается по часам» — её отменяют, а она должна корректно
отреагировать на `CancelledError`.

## 7. Асинхронный контекстный менеджер {#sol-ch39-07}

```python exec
import asyncio

class Counter:
    def __init__(self, name):
        self.name = name
        self.calls = 0
    async def __aenter__(self):
        print(f"{self.name}: начало")
        return self
    async def __aexit__(self, exc_type, exc, tb):
        self.calls += 1
        print(f"{self.name}: конец, вызовов {self.calls}")
        return False

async def main():
    async with Counter("блок") as counter:
        print(f"внутри {counter.name}")
    try:
        async with Counter("ошибка"):
            raise ValueError("что-то пошло не так")
    except ValueError as error:
        print("поймали:", error)

asyncio.run(main())
```

```output
блок: начало
внутри блок
блок: конец, вызовов 1
ошибка: начало
ошибка: конец, вызовов 1
поймали: что-то пошло не так
```

`__aexit__` получил сведения об исключении и вернул `False` — значит,
исключение не подавлено. Второй блок подтверждает, что выход выполняется при
любом исходе, как и у обычного `with`.

## 8. Задача как объект {#sol-ch39-08}

```python exec
import asyncio

async def work():
    await asyncio.sleep(0)
    return 42

async def main():
    task = asyncio.create_task(work())
    print("сразу после создания:", task.done(), task.cancelled())
    result = await task
    print("результат:", result)
    print("после ожидания:", task.done(), task.cancelled())

asyncio.run(main())
```

```output
сразу после создания: False False
результат: 42
после ожидания: True False
```

`done()` показывает, завершилась ли задача (успешно, ошибкой или отменой);
`cancelled()` — была ли она именно отменена. Пока задача в работе, оба
значения `False`. После `await` задача завершена успешно, поэтому `done()`
равен `True`, а `cancelled()` по-прежнему `False`.

## 9. Модель выполнения {#sol-ch39-09}

Сообщение второй задачи появится только после того, как первая закончит
вычисления: внутри цикла нет ни одного `await`, а значит, нет точки, где
планировщик мог бы переключиться. Пока задача владеет потоком, остальные
ждут.

```python exec
import asyncio

def heavy_sum():
    return sum(range(1_000_000))

async def first():
    print("первая: начало")
    total = heavy_sum()
    print("первая: конец")

async def second():
    print("вторая: сообщение")

async def main():
    one = asyncio.create_task(first())
    two = asyncio.create_task(second())
    await one
    await two

asyncio.run(main())
```

```output
первая: начало
первая: конец
вторая: сообщение
```

Чтобы сообщение появилось раньше, тяжёлую работу выносят в поток:

```python exec
import asyncio

def heavy_sum():
    return sum(range(1_000_000))

async def first():
    print("первая: начало")
    await asyncio.to_thread(heavy_sum)
    print("первая: конец")

async def second():
    print("вторая: сообщение")

async def main():
    one = asyncio.create_task(first())
    two = asyncio.create_task(second())
    await one
    await two

asyncio.run(main())
```

```output
первая: начало
вторая: сообщение
первая: конец
```

Второй вариант не ускоряет сумму, но освобождает цикл событий: пока поток
считает, другие задачи успевают выполняться.

## 10. Мини-задача: конкурентная загрузка {#sol-ch39-10}

```python exec
import asyncio

async def load_one(name, value):
    await asyncio.sleep(0)
    if value < 0:
        raise ValueError(f"{name}: отрицательное значение")
    return f"{name}: {value}"

async def load_all(sources):
    tasks = [asyncio.create_task(load_one(name, value)) for name, value in sources]
    results = []
    for task in tasks:
        try:
            results.append(await task)
        except ValueError as error:
            results.append(f"ошибка: {error}")
    return results

async def main():
    data = [("a", 1), ("b", -2), ("c", 3)]
    for line in await load_all(data):
        print(line)

asyncio.run(main())
```

```output
a: 1
ошибка: b: отрицательное значение
c: 3
```

Задачи создаются все сразу, поэтому «загрузка» идёт конкурентно. Ошибка одной
задачи не отменяет остальные: каждую задачу ожидают отдельно, а исключение
превращают в элемент результата. Если нужно, чтобы ошибка завершала всю
группу, используют `TaskGroup` — тогда остальные задачи будут отменены, а
исключения придут как `ExceptionGroup`.

## Ответы на вопросы для самопроверки

1. Задача — единица работы внутри одного потока, которую планирует цикл
   событий; поток — единица планирования операционной системы. Общее у них
   то, что оба позволяют нескольким работам продвигаться конкурентно.
2. Асинхронность переключается только в точках `await` и не даёт двум
   задачам выполняться одновременно, поэтому вычисления на одном ядре
   выполняются так же долго.
3. Корутина создаётся вызовом, но тело начинает исполняться при `await`
   (или при запуске через `asyncio.run`/`create_task`).
4. `sleep(0)` — точка приостановки, которая сразу возвращает управление
   планировщику; она нужна, чтобы дать другим задачам шанс выполниться.
5. Два последовательных `await` выполняют работы одну за другой; `gather`
   запускает их одновременно как задачи и ждёт все.
6. `time.sleep` занимает поток, и цикл событий не может запустить другие
   задачи: он не получает управления.
7. Отмена будет проглочена: задача продолжит работу, хотя её просили
   остановить, а вызывающий код решит, что задача завершилась.
8. `TaskGroup` связан с блоком `async with`: выйти из блока можно только
   после завершения всех задач, а исключения собираются в `ExceptionGroup`,
   который нельзя потерять незамеченным.
