---
chapter: ch-55-tkinter
number: 55
exercise_count: 10
---

# Решения к главе 55

GUI-примеры приведены в блоках `python` и не исполняются автоматически: в
песочнице нет графической среды, окно открыть нельзя. Логика, которую можно
проверить без окна, вынесена в исполняемые блоки — именно так и стоит
организовывать настоящее приложение.

## 1. Минимальное окно {#sol-ch55-01}

```python
import tkinter as tk

root = tk.Tk()
root.title("Мой первый GUI")
root.geometry("400x300")

tk.Label(root, text="Привет").pack(expand=True)
tk.Button(root, text="Закрыть", command=root.destroy).pack(pady=10)

root.mainloop()
```

`Tk()` создаёт корневое окно, `title` и `geometry` задают заголовок и размер,
`pack` размещает метку и кнопку, `mainloop` запускает цикл событий. Кнопка
вызывает `root.destroy` и завершает программу.

Если убрать `mainloop()`, окно может появиться на мгновение и сразу исчезнуть:
программа завершится, не дождавшись ни одного события. Цикл событий — это то,
что удерживает приложение живым и вызывает обработчики. Без него нет ни
реакции на кнопки, ни гарантированной отрисовки.

## 2. Витрина виджетов {#sol-ch55-02}

```python
import tkinter as tk

root = tk.Tk()
root.title("Витрина")

status = tk.StringVar(value="—")
name = tk.StringVar()

tk.Label(root, text="Имя:").pack(anchor="w", padx=8, pady=4)
tk.Entry(root, textvariable=name).pack(fill="x", padx=8)
tk.Checkbutton(root, text="Запомнить").pack(anchor="w", padx=8, pady=4)


def greet() -> None:
    status.set(f"Привет, {name.get() or 'гость'}!")


tk.Button(root, text="Показать", command=greet).pack(pady=6)
tk.Label(root, textvariable=status).pack(pady=6)

root.mainloop()
```

Здесь понадобились: `StringVar` — чтобы не читать поле вручную и обновлять
метку автоматически; `fill="x"` — чтобы поле ввода растянулось по ширине;
`anchor="w"` — чтобы подпись прижималась влево; `padx`/`pady` — отступы.
Кнопка связана с функцией через `command`, а функция читает значение из
переменной и меняет вторую переменную, связанную с меткой результата.

## 3. Модель счётчика {#sol-ch55-03}

```python exec
class CounterModel:
    def __init__(self) -> None:
        self.value = 0

    def increment(self) -> int:
        self.value += 1
        return self.value

    def decrement(self) -> int:
        if self.value > 0:
            self.value -= 1
        return self.value

    def reset(self) -> int:
        self.value = 0
        return self.value


counter = CounterModel()
print(counter.increment(), counter.increment(), counter.decrement())
print(counter.reset(), counter.decrement())
```

```output
1 2 1
0 0
```

Класс не знает про Tkinter: его можно проверить в терминале, покрыть тестами и
переиспользовать в другом интерфейсе. Ограничение «не ниже нуля» живёт в
модели, а не в обработчике кнопки, поэтому его нельзя обойти через другой
способ ввода.

## 4. Форма на grid {#sol-ch55-04}

```python
import tkinter as tk

root = tk.Tk()
root.title("Форма")
root.columnconfigure(1, weight=1)

tk.Label(root, text="Имя:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
tk.Entry(root).grid(row=0, column=1, sticky="ew", padx=8, pady=6)

tk.Label(root, text="Email:").grid(row=1, column=0, sticky="w", padx=8, pady=6)
tk.Entry(root).grid(row=1, column=1, sticky="ew", padx=8, pady=6)

tk.Button(root, text="Отправить").grid(row=2, column=0, columnspan=2, pady=10)

root.mainloop()
```

`columnconfigure(1, weight=1)` отдаёт второму столбцу всё лишнее место, поэтому
поля ввода растягиваются при изменении ширины окна. `sticky="ew"` растягивает
виджет внутри ячейки по горизонтали, `sticky="w"` прижимает подпись влево.
`columnspan=2` объединяет две ячейки под кнопку. Если убрать `weight`, окно при
растяжении оставит форму компактной в левом верхнем углу — свободное место
никуда не распределится.

## 5. Обработчик и событие {#sol-ch55-05}

```python
import tkinter as tk

root = tk.Tk()
status = tk.StringVar(value="готово")


def on_button() -> None:
    status.set("нажата кнопка")


def on_enter(event: tk.Event) -> None:
    status.set(f"нажат Enter в {event.widget.__class__.__name__}")


tk.Label(root, textvariable=status).pack(padx=10, pady=10)
tk.Button(root, text="Кнопка", command=on_button).pack(pady=4)
root.bind("<Return>", on_enter)

root.mainloop()
```

`command` связывает действие с конкретным виджетом и вызывает функцию без
аргументов: это удобно для кнопок. `bind` подписывает окно (или виджет) на
событие и передаёт объект `event`, в котором есть `widget`, `keysym`, `char`,
`x`, `y`. `command` проще для «нажали кнопку», `bind` нужен для клавиатуры,
мыши и событий, у которых важны детали.

## 6. Валидация ввода {#sol-ch55-06}

```python exec
def parse_percent(text: str) -> float:
    cleaned = text.strip().replace(",", ".")
    if not cleaned:
        raise ValueError("введите процент")
    try:
        value = float(cleaned)
    except ValueError as exc:
        raise ValueError(f"не число: {text!r}") from exc
    if not 0 <= value <= 100:
        raise ValueError("процент должен быть от 0 до 100")
    return value


for raw in ["42", "0", "100", " 12,5 ", "140", "abc"]:
    try:
        print(repr(raw), "→", parse_percent(raw))
    except ValueError as error:
        print(repr(raw), "→ ошибка:", error)
```

```output
'42' → 42.0
'0' → 0.0
'100' → 100.0
' 12,5 ' → 12.5
'140' → ошибка: процент должен быть от 0 до 100
'abc' → ошибка: не число: 'abc'
```

Функция чистая: она не зависит от окна и проверяется в терминале. Обработчик
кнопки просто вызывает её в `try`/`except` и показывает сообщение об ошибке в
метке. Запятая как десятичный разделитель поддерживается заменой на точку —
частая просьба пользователей русскоязычных интерфейсов.

## 7. Модель списка задач {#sol-ch55-07}

```python exec
class TaskList:
    def __init__(self) -> None:
        self._tasks: list[dict[str, object]] = []

    def add(self, title: str) -> int:
        if not title.strip():
            raise ValueError("пустой заголовок")
        self._tasks.append({"title": title.strip(), "done": False})
        return len(self._tasks) - 1

    def toggle(self, index: int) -> bool:
        if not 0 <= index < len(self._tasks):
            raise IndexError("нет такой задачи")
        task = self._tasks[index]
        task["done"] = not task["done"]
        return bool(task["done"])

    def remove(self, index: int) -> str:
        if not 0 <= index < len(self._tasks):
            raise IndexError("нет такой задачи")
        return str(self._tasks.pop(index)["title"])

    def visible(self) -> list[str]:
        return [("✓ " if task["done"] else "· ") + str(task["title"]) for task in self._tasks]


tasks = TaskList()
first = tasks.add("купить хлеб")
second = tasks.add("позвонить")
tasks.add("прочитать главу")
print(tasks.toggle(first))
print(tasks.visible())
print(tasks.remove(second))
print(tasks.visible())
```

```output
True
['✓ купить хлеб', '· позвонить', '· прочитать главу']
позвонить
['✓ купить хлеб', '· прочитать главу']
```

Модель возвращает индексы и строки, а не виджеты: интерфейс сам решит, как
показать состояние. Проверки индекса и пустого заголовка живут здесь, поэтому
одинаково работают для кнопки, горячей клавиши и любого будущего способа
ввода.

## 8. Не блокировать цикл {#sol-ch55-08}

Если обработчик вызывает `time.sleep(3)`, цикл событий занят три секунды:
окно не перерисовывается, не отвечает на нажатия и может помечаться системой
как «не отвечает». Пользователь видит зависшее приложение, хотя программа
всего лишь ждёт.

Правильный вариант — не блокировать, а запланировать действие:

```python
import tkinter as tk

root = tk.Tk()
status = tk.StringVar(value="готово")


def finish() -> None:
    status.set("готово")


def on_click() -> None:
    status.set("подождите…")
    root.after(3000, finish)


tk.Label(root, textvariable=status).pack(padx=10, pady=10)
tk.Button(root, text="Запустить", command=on_click).pack()
root.mainloop()
```

`root.after(3000, finish)` вернёт управление циклу немедленно, а через три
секунды вызовет `finish` в главном потоке. Для настоящих длительных операций
(сеть, файлы) используют поток, который складывает результат в
`queue.Queue`, а интерфейс периодически проверяет очередь через `after` и
обновляет виджеты только в главном потоке.

## 9. Конвертер температуры {#sol-ch55-09}

```python exec
def celsius_to_fahrenheit(celsius: float) -> float:
    return celsius * 9 / 5 + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    return (fahrenheit - 32) * 5 / 9


print(celsius_to_fahrenheit(0))
print(celsius_to_fahrenheit(100))
print(fahrenheit_to_celsius(-40))
print(round(fahrenheit_to_celsius(212)))
```

```output
32.0
212.0
-40.0
100
```

Точка −40 удобна тем, что в ней шкалы совпадают: `celsius_to_fahrenheit(-40)`
и `fahrenheit_to_celsius(-40)` дают −40. Подключение к окну повторяет
конвертер расстояний: `StringVar` для ввода и результата, `Radiobutton` для
выбора направления, `command` кнопки вызывает функцию, а `try`/`except`
показывает ошибку в метке. Все вычисления остаются в чистых функциях.

## 10. Мини-проект: приложение «Заметки» {#sol-ch55-10}

Модель:

```python exec
class NoteBook:
    def __init__(self) -> None:
        self._notes: list[str] = []

    def add(self, text: str) -> int:
        if not text.strip():
            raise ValueError("пустая заметка")
        self._notes.append(text.strip())
        return len(self._notes) - 1

    def remove(self, index: int) -> str:
        if not 0 <= index < len(self._notes):
            raise IndexError("нет такой заметки")
        return self._notes.pop(index)

    def items(self) -> list[str]:
        return list(self._notes)


book = NoteBook()
book.add("купить хлеб")
book.add("позвонить")
print(book.items())
print(book.remove(0))
print(book.items())
```

```output
['купить хлеб', 'позвонить']
купить хлеб
['позвонить']
```

Интерфейс:

```python
import tkinter as tk

root = tk.Tk()
root.title("Заметки")

entry = tk.Entry(root)
entry.pack(fill="x", padx=8, pady=6)

listbox = tk.Listbox(root)
listbox.pack(fill="both", expand=True, padx=8)


def refresh() -> None:
    listbox.delete(0, "end")
    for note in book.items():
        listbox.insert("end", note)


def add_note() -> None:
    try:
        book.add(entry.get())
    except ValueError:
        return
    entry.delete(0, "end")
    refresh()


def remove_note() -> None:
    selection = listbox.curselection()
    if not selection:
        return
    book.remove(selection[0])
    refresh()


tk.Button(root, text="Добавить", command=add_note).pack(pady=4)
tk.Button(root, text="Удалить выбранную", command=remove_note).pack(pady=4)

book = NoteBook()
refresh()
root.mainloop()
```

Модель `NoteBook` проверяется без окна: добавление, удаление и список заметок
не зависят от Tkinter. Интерфейс получает выбранный индекс через
`curselection`, обновляет `Listbox` функцией `refresh` и не хранит состояние
сам. Если завтра понадобится сохранять заметки в файл, изменится только
модель — обработчики и виджеты останутся прежними.

## Ответы на вопросы для самопроверки

1. GUI рассчитан на интерактивную работу человека, консоль — на автоматизацию
   и скрипты; выбор зависит от того, кто и как часто будет пользоваться.
2. `mainloop` запускает цикл событий: ждёт события, вызывает обработчики и
   перерисовывает окно. Без него программа завершается сразу.
3. `pack` укладывает виджеты по стороне, `grid` — в строки и столбцы, `place`
   — по координатам. `grid` точнее описывает структуру и лучше переживает
   изменение размера.
4. `command` вызывает функцию без аргументов и привязан к действию виджета;
   `bind` подписывает на событие и передаёт объект `event` с деталями.
5. Цикл событий однопоточный: пока обработчик не вернул управление, окно не
   перерисовывается и не реагирует. Помогают `after`, потоки и очередь.
6. Разделение позволяет тестировать правила без окна и менять интерфейс, не
   переписывая логику.
7. Tkinter не потокобезопасен; из фонового потока нельзя менять виджеты.
   Используют очередь: поток кладёт данные, главный поток забирает их в
   `after` и обновляет интерфейс.
