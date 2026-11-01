---
chapter: ch-19-files-formats
number: 19
exercise_count: 10
---

# Решения к главе 19

Все примеры работают во временном каталоге: их можно запускать многократно,
и они не зависят от того, что уже лежит на диске.

## 1. Прогнозирование вывода {#sol-ch19-01}

```python exec
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "note.txt"
    path.write_text("один\nдва\n", encoding="utf-8")
    with open(path, "w", encoding="utf-8") as file:
        file.write("три\n")
    print(path.read_text(encoding="utf-8"))
```

```output
три
```

Режим `"w"` не дописывает, а открывает файл на запись с усечением: прежнее
содержимое уничтожается в момент открытия, ещё до первой записи. Поэтому
строки `один` и `два` исчезли.

## 2. Путь из частей {#sol-ch19-02}

```python exec
from pathlib import Path

p = Path("отчёты") / "2026" / "январь.csv"
print(p.name)
print(p.stem)
print(p.suffix)
print(p.parent.as_posix())
```

```output
январь.csv
январь
.csv
отчёты/2026
```

Оператор `/` соединяет части пути, а не выполняет деление. Атрибуты `name`,
`stem`, `suffix` и `parent` разбирают готовый путь на части.

## 3. Чтение построчно {#sol-ch19-03}

```python exec
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "lines.txt"
    path.write_text("альфа\nбета\nгамма\n", encoding="utf-8")
    with open(path, encoding="utf-8") as file:
        for number, line in enumerate(file, start=1):
            print(number, line.rstrip())
```

```output
1 альфа
2 бета
3 гамма
```

`enumerate(file, start=1)` нумерует строки. `rstrip()` убирает символ перевода
строки справа; `strip()` тоже подошёл бы, но удалил бы и значимые пробелы в
начале строки.

## 4. Дописать, не стирая {#sol-ch19-04}

```python exec
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "notes.txt"
    path.write_text("первая\n", encoding="utf-8")
    with open(path, "a", encoding="utf-8") as file:
        file.write("вторая\n")
    print(path.read_text(encoding="utf-8"))
```

```output
первая
вторая
```

Режим `"w"` очистил бы файл в момент открытия, поэтому для дописывания нужен
`"a"`. Если файла нет, режим `"a"` создаст его.

## 5. Защита от перезаписи {#sol-ch19-05}

```python exec
import tempfile
from pathlib import Path


def create_report(path):
    try:
        with open(path, "x", encoding="utf-8") as file:
            file.write("отчёт\n")
        return "создан"
    except FileExistsError:
        return "файл уже существует"


with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "report.txt"
    print(create_report(path))
    print(create_report(path))
    print(path.read_text(encoding="utf-8"))
```

```output
создан
файл уже существует
отчёт
```

Режим `"x"` проверяет существование и создание одной атомарной операцией:
между проверкой и созданием нет промежутка, в который могла бы вклиниться
другая программа. Поэтому он надёжнее, чем `if path.exists()` плюс `open(..., "w")`.

## 6. Кодировки {#sol-ch19-06}

```python exec
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "legacy.txt"
    path.write_bytes("привет".encode("cp1251"))
    try:
        print(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        print(type(exc).__name__)
    print(path.read_text(encoding="cp1251"))
```

```output
UnicodeDecodeError
привет
```

Текст был записан в `cp1251`, а прочитан как UTF-8: байты не складываются в
допустимую последовательность символов, поэтому возникает
`UnicodeDecodeError`. Чтение с той же кодировкой, в которой писали, даёт
исходную строку. Вывод: кодировка — часть формата файла, её нужно знать и
указывать явно.

## 7. CSV в словари {#sol-ch19-07}

```python exec
import csv
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "fruit.csv"
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["товар", "цена"])
        writer.writerow(["яблоко", 90])
        writer.writerow(["банан", 120])
    total = 0
    with open(path, encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            price = int(row["цена"])
            total = total + price
            print(row["товар"], price)
    print("итого:", total)
```

```output
яблоко 90
банан 120
итого: 210
```

`DictReader` берёт заголовок из первой строки и делает ключи словаря. Значения
остаются строками, поэтому `int(row["цена"])` обязателен: без него выражение
`total + row["цена"]` упадёт с `TypeError: unsupported operand type(s) for +:
'int' and 'str'` — `total` число, а значение из CSV строка.

## 8. JSON-настройки {#sol-ch19-08}

```python exec
import json
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "settings.json"
    settings = {"тема": "тёмная", "язык": "ru", "размер": 14}
    with open(path, "w", encoding="utf-8") as file:
        json.dump(settings, file, ensure_ascii=False, indent=2)
    print(path.read_text(encoding="utf-8"))
    with open(path, encoding="utf-8") as file:
        loaded = json.load(file)
    print(loaded["размер"], type(loaded["размер"]).__name__)
```

```output
{
  "тема": "тёмная",
  "язык": "ru",
  "размер": 14
}
14 int
```

`ensure_ascii=False` сохраняет кириллицу в читаемом виде, `indent=2` добавляет
отступы. При чтении JSON-число возвращается как `int`, поэтому тип сохраняется.

## 9. Мини-проект: журнал оценок {#sol-ch19-09}

```python exec
import json
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "grades.json"
    grades = {}
    if path.exists():
        with open(path, encoding="utf-8") as file:
            grades = json.load(file)
    grades["Анна"] = [4, 5, 5]
    grades["Борис"] = [3, 4]
    with open(path, "w", encoding="utf-8") as file:
        json.dump(grades, file, ensure_ascii=False, indent=2)
    with open(path, encoding="utf-8") as file:
        loaded = json.load(file)
    for name in loaded:
        marks = loaded[name]
        print(name, round(sum(marks) / len(marks), 1))
```

```output
Анна 4.7
Борис 3.5
```

Программа устроена по образцу «прочитать — изменить — записать». Проверка
`path.exists()` нужна для первого запуска: файла ещё нет, и читать нечего.
Обратите внимание: `round` даёт одно значение после запятой, как и требовалось.

## 10. Формат под задачу {#sol-ch19-10}

- продажи по дням для табличного редактора — CSV: плоская таблица;
- конфигурация с вложенными разделами — JSON: нужна вложенность;
- список контактов «имя, телефон, город» — CSV: ровные строки одинаковых
  столбцов;
- заказ с позициями и адресом — JSON: структура с вложенным списком.

Пример заказа в JSON:

```python exec
import json

order = {
    "номер": 42,
    "позиции": [{"товар": "яблоко", "количество": 2}],
    "адрес": "Казань",
}
text = json.dumps(order, ensure_ascii=False, indent=2)
print(text)
print(json.loads(text)["позиции"][0]["товар"])
```

```output
{
  "номер": 42,
  "позиции": [
    {
      "товар": "яблоко",
      "количество": 2
    }
  ],
  "адрес": "Казань"
}
яблоко
```

CSV здесь потребовал бы либо нескольких файлов, либо повторения номера
заказа в каждой строке, либо отдельного формата для вложенности. JSON хранит
структуру как есть.

## Ответы на вопросы для самопроверки

1. Файл хранится вне памяти процесса и переживает его завершение; внешний
   ресурс нужно открыть, закрыть и можно потерять доступ.
2. `pathlib` избавляет от ручной склейки разделителей, даёт разбор пути на
   части, чтение, запись и обход каталогов.
3. `"w"` очищает файл и создаёт его, `"a"` дописывает в конец, `"x"`
   создаёт только новый файл и падает, если файл уже есть.
4. `with` гарантирует освобождение ресурса при любом выходе из блока;
   контекстный менеджер — объект с протоколом `__enter__`/`__exit__`.
5. По умолчанию кодировка берётся из локали; явное указание делает поведение
   одинаковым на разных машинах.
6. CSV хранит текст; числа не являются частью формата, поэтому при чтении
   всё возвращается строками.
7. Объект — `dict`, массив — `list` (кортеж тоже записывается как массив),
   `null` — `None`.
8. `TypeError` возникает при попытке сериализовать неподдерживаемый объект,
   `JSONDecodeError` — когда текст не является корректным JSON.
