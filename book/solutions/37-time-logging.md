---
chapter: ch-37-time-logging
number: 37
exercise_count: 10
---

# Решения к главе 37

Примеры используют фиксированные моменты времени: так вывод одинаков при
любом запуске. В рабочем коде текущее время берут в одном месте программы и
передают дальше, а не вызывают `datetime.now` в каждом модуле.

## 1. Наивное и осведомлённое {#sol-ch37-01}

```python exec
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

naive = datetime(2026, 11, 1, 12, 0)
aware = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
print(naive.tzinfo)
print(aware.tzinfo)
print(aware.astimezone(ZoneInfo("Europe/Moscow")).isoformat())
```

```output
None
UTC
2026-11-01T15:00:00+03:00
```

Сравнение такого наивного и осведомлённого времени завершается ошибкой:

```python exec expect-error
from datetime import datetime, timezone

naive = datetime(2026, 11, 1, 12, 0)
aware = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
print(naive < aware)
```

```output
TypeError: can't compare offset-naive and offset-aware datetimes
```

Python не знает, в каком поясе задано наивное время, поэтому честно отказывается
сравнивать. Правильный ход — добавить пояс явно: `naive.replace(tzinfo=...)`
или прочитать значение как UTC, если такова договорённость в данных.

## 2. Перевод между поясами {#sol-ch37-02}

```python exec
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

instant = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
for zone in ("Europe/Moscow", "Asia/Tokyo", "America/New_York"):
    print(zone, instant.astimezone(ZoneInfo(zone)).isoformat())
print(instant.astimezone(ZoneInfo("Europe/Moscow")) == instant)
```

```output
Europe/Moscow 2026-11-01T15:00:00+03:00
Asia/Tokyo 2026-11-01T21:00:00+09:00
America/New_York 2026-11-01T07:00:00-05:00
True
```

Все три строки обозначают один момент, и сравнение с исходным подтверждает
это. Нью-Йорк в ноябре уже на зимнем времени (`-05:00`), поэтому разница с
UTC пять часов, а не четыре.

## 3. Интервалы {#sol-ch37-03}

```python exec
from datetime import datetime, timezone

start = datetime(2026, 3, 1, tzinfo=timezone.utc)
finish = datetime(2026, 11, 1, 12, 30, tzinfo=timezone.utc)
delta = finish - start
print(delta.days)
print(delta.seconds // 3600)
print((delta.seconds % 3600) // 60)
print(delta.total_seconds())
```

```output
245
12
30
21213000.0
```

`delta.days` и `delta.seconds` — разные части интервала: дни и остаток меньше
суток. Поэтому часы и минуты считают из `delta.seconds`, а не из общего числа
секунд. `total_seconds` даёт весь интервал одним числом — удобно для сравнений
и хранения.

## 4. Отметка времени {#sol-ch37-04}

```python exec
from datetime import datetime, timedelta, timezone

local = datetime(2026, 11, 1, 15, 0, tzinfo=timezone(timedelta(hours=3)))
stamp = local.timestamp()
print(int(stamp))
print(datetime.fromtimestamp(stamp, tz=timezone.utc).isoformat())
```

```output
1793534400
2026-11-01T12:00:00+00:00
```

Момент `15:00+03:00` — это `12:00 UTC`. Отметка времени от пояса не зависит:
она всегда считает секунды от эпохи. Обратное преобразование выполняют с
явным `tz=timezone.utc`, иначе интерпретатор подставит локальный пояс машины и
результат изменится.

## 5. Неоднозначный час {#sol-ch37-05}

При обратном переводе часов 25 октября 2026 года Берлин проходит через 02:30
дважды. Атрибут `fold` выбирает вхождение:

```python exec
from datetime import datetime
from zoneinfo import ZoneInfo

berlin = ZoneInfo("Europe/Berlin")
first = datetime(2026, 10, 25, 2, 30, tzinfo=berlin, fold=0)
second = datetime(2026, 10, 25, 2, 30, tzinfo=berlin, fold=1)
print(first.isoformat(), first.utcoffset())
print(second.isoformat(), second.utcoffset())
print(first.timestamp() - second.timestamp())
```

```output
2026-10-25T02:30:00+02:00 2:00:00
2026-10-25T02:30:00+01:00 1:00:00
-3600.0
```

`fold=0` — первое, ещё летнее вхождение, `fold=1` — второе, уже зимнее. Без
`fold` интерпретатор берёт `0`, поэтому второй момент выглядит как первый:
одинаковые цифры скрывают разницу в час.

Теперь весенний переход:

```python exec
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

instant = datetime(2026, 3, 29, 1, 30, tzinfo=timezone.utc)
print(instant.astimezone(ZoneInfo("Europe/Berlin")).isoformat())
print(instant.astimezone(ZoneInfo("Europe/Moscow")).isoformat())
```

```output
2026-03-29T03:30:00+02:00
2026-03-29T04:30:00+03:00
```

В ночь на 29 марта 2026 года Европа переходит на летнее время: в 01:00 UTC
часы переводятся с 02:00 на 03:00, поэтому `01:30 UTC` соответствует
`03:30` по Берлину со смещением `+02:00`. Москва не переходит на летнее
время, её смещение постоянно `+03:00`, поэтому там `04:30`. Это и есть
разница между «правилом пояса» и «числом смещения»: одно и то же смещение
`+03:00` у Москвы круглый год, а у Берлина меняется.

## 6. Настройка логирования {#sol-ch37-06}

```python exec
import logging
from io import StringIO

console_stream = StringIO()
file_stream = StringIO()

console = logging.StreamHandler(console_stream)
console.setLevel(logging.WARNING)
console.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))

file_handler = logging.StreamHandler(file_stream)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))

logger = logging.getLogger("task")
logger.handlers.clear()
logger.propagate = False
logger.setLevel(logging.DEBUG)
logger.addHandler(console)
logger.addHandler(file_handler)

logger.info("шаг выполнен")
logger.warning("медленный ответ")
logger.debug("подробность")

print("консоль:")
print(console_stream.getvalue(), end="")
print("файл:")
print(file_stream.getvalue(), end="")
```

```output
консоль:
WARNING:медленный ответ
файл:
INFO:шаг выполнен
WARNING:медленный ответ
```

`DEBUG` не попал никуда: уровень регистратора `DEBUG`, но обработчики
фильтруют записи каждый по своему порогу. Консоль пропускает только
`WARNING` и выше, файл — `INFO` и выше. В реальном коде вместо `StringIO`
будет файл или стандартный поток, но принцип тот же.

## 7. Разбор журнала {#sol-ch37-07}

```python exec
from collections import Counter

lines = ["INFO:start", "ERROR:fail", "INFO:step", "WARNING:slow", "ERROR:fail"]
records = []
for line in lines:
    level, message = line.split(":", 1)
    records.append({"level": level, "message": message})
print(records)
print(Counter(record["level"] for record in records))
```

```output
[{'level': 'INFO', 'message': 'start'}, {'level': 'ERROR', 'message': 'fail'}, {'level': 'INFO', 'message': 'step'}, {'level': 'WARNING', 'message': 'slow'}, {'level': 'ERROR', 'message': 'fail'}]
Counter({'INFO': 2, 'ERROR': 2, 'WARNING': 1})
```

`split(":", 1)` делит строку только по первому двоеточию, поэтому текст
сообщения может содержать свои двоеточия. `Counter` по полю `level` сразу
даёт сводку — типичная задача при разборе журналов.

## 8. Структурированная запись {#sol-ch37-08}

```python exec
import json
import logging
from io import StringIO

stream = StringIO()
handler = logging.StreamHandler(stream)
logger = logging.getLogger("requests")
logger.handlers.clear()
logger.propagate = False
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def log_request(request_id: str, path: str, status: int, duration_ms: int) -> None:
    record = {
        "event": "request_finished",
        "request_id": request_id,
        "path": path,
        "status": status,
        "duration_ms": duration_ms,
    }
    logger.info(json.dumps(record, ensure_ascii=False, sort_keys=True))


log_request("req-1", "/notes", 200, 42)
raw = stream.getvalue().strip()
print(raw)
parsed = json.loads(raw)
print(parsed["status"], parsed["duration_ms"])
```

```output
{"duration_ms": 42, "event": "request_finished", "path": "/notes", "request_id": "req-1", "status": 200}
200 42
```

Запись содержит поля, по которым можно фильтровать: `status` для поиска
ошибок, `duration_ms` для анализа медленных запросов, `request_id` для связи
с другими логами. Строка остаётся валидным JSON, поэтому её можно читать и
человеком, и программой.

## 9. Секреты в логах {#sol-ch37-09}

Логировать полный словарь заголовков опасно: `Authorization`, `Cookie`,
`Set-Cookie` содержат учётные данные, а тело запроса может включать пароль
или номер карты. Журналы копируются в системы поиска, хранятся месяцами и
доступны широкому кругу людей — утечка через лог ничем не лучше утечки через
ответ API.

```python exec
SENSITIVE = {"authorization", "cookie", "set-cookie", "password", "token"}


def mask_headers(headers: dict[str, str]) -> dict[str, str]:
    masked: dict[str, str] = {}
    for name, value in headers.items():
        if name.lower() in SENSITIVE:
            masked[name] = "***"
        else:
            masked[name] = value
    return masked


headers = {"Accept": "application/json", "Authorization": "Bearer secret-token"}
print(mask_headers(headers))
```

```output
{'Accept': 'application/json', 'Authorization': '***'}
```

Маскирование делают до записи, а не после: если секрет попал в строку лога,
он уже в файле. Список чувствительных полей стоит держать в одном месте и
дополнять по мере появления новых интеграций.

## 10. Мини-проект: журнал запросов {#sol-ch37-10}

```python exec
import json
from datetime import datetime, timezone

events = [
    {"timestamp": datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc), "event": "request_finished", "path": "/notes", "status": 200},
    {"timestamp": datetime(2026, 11, 1, 12, 0, 5, tzinfo=timezone.utc), "event": "request_finished", "path": "/notes/1", "status": 404},
]


def render(events: list[dict[str, object]]) -> list[str]:
    lines: list[str] = []
    for event in events:
        payload = dict(event)
        payload["timestamp"] = event["timestamp"].isoformat()
        lines.append(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return lines


lines = render(events)
for line in lines:
    print(line)

parsed = [json.loads(line) for line in lines]
print(len(parsed), parsed[1]["status"])
```

```output
{"event": "request_finished", "path": "/notes", "status": 200, "timestamp": "2026-11-01T12:00:00+00:00"}
{"event": "request_finished", "path": "/notes/1", "status": 404, "timestamp": "2026-11-01T12:00:05+00:00"}
2 404
```

Время сериализуется в ISO 8601 с явным смещением UTC — такой журнал можно
сортировать как строки и загружать в системы поиска. Обратный разбор
подтверждает, что каждая строка — самостоятельный JSON. В рабочем коде
`render` пишет в обработчик журнала, а не в `print`, но формат остаётся тем
же.

## Ответы на вопросы для самопроверки

1. Наивное время не знает пояса, осведомлённое хранит смещение и правило
   пояса; сравнивать и переводить можно только осведомлённое.
2. UTC не зависит от региона и перехода на летнее время, поэтому моменты
   остаются однозначными; локальное время показывают на границе.
3. Смещение — конкретное число часов в конкретный момент; пояс — правило,
   по которому это число вычисляется, включая переходы.
4. ISO 8601 — однозначная текстовая запись даты и времени; её понимают
   разные системы, и она сортируется.
5. Регистратор принимает записи, обработчик выбирает приёмник, форматтер
   задаёт вид строки.
6. Структурированное логирование превращает журнал в данные с полями, по
   которым можно фильтровать, считать и строить оповещения.
7. Нельзя писать пароли, токены, номера карт и персональные данные: журналы
   копируются, индексируются и хранятся дольше, чем кажется.
