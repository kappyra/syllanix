---
chapter: ch-54-practice
number: 54
exercise_count: 10
---

# Решения к главе 54

Разбор идёт от идеи к коду: сначала коротко объясняется приём, затем полное
решение. Сравнивайте не только результат, но и то, как выбраны границы и
почему решение завершается.

## 1. Обобщённый FizzBuzz {#sol-ch54-01}

```python exec
def fizzbuzz_custom(limit: int, divisors: dict[int, str]) -> list[str]:
    result: list[str] = []
    for number in range(1, limit + 1):
        label = "".join(text for divisor, text in divisors.items() if number % divisor == 0)
        result.append(label or str(number))
    return result


print(fizzbuzz_custom(21, {3: "Fizz", 5: "Buzz", 7: "Boom"}))
```

```output
['1', '2', 'Fizz', '4', 'Buzz', 'Fizz', 'Boom', '8', 'Fizz', 'Buzz', '11', 'Fizz', '13', 'Boom', 'FizzBuzz', '16', '17', 'Fizz', '19', 'Buzz', 'FizzBoom']
```

Порядок ключей словаря определяет порядок меток: при `{3: "Fizz", 5: "Buzz"}`
число 15 даст `FizzBuzz`, а при обратном порядке — `BuzzFizz`. В Python 3.7+
порядок вставки сохраняется, поэтому результат предсказуем. Проверка «ни один
делитель не подошёл» сводится к пустой строке: `label or str(number)`.

## 2. Подсчёт ходов Ханойской башни {#sol-ch54-02}

```python exec
def hanoi_count(n: int) -> int:
    if n == 0:
        return 0
    return 2 * hanoi_count(n - 1) + 1


def hanoi_formula(n: int) -> int:
    return 2**n - 1


print([hanoi_count(n) for n in range(8)])
print(hanoi_formula(12))
print(all(hanoi_count(n) == hanoi_formula(n) for n in range(13)))
```

```output
[0, 1, 3, 7, 15, 31, 63, 127]
4095
True
```

Рекурсивная версия делает `2ⁿ − 1` вызовов-шагов, то есть работает за
экспоненциальное время `O(2ⁿ)` и хранит в стеке `O(n)` кадров. Формула
вычисляется за `O(1)`, но она не описывает сами ходы — только их число.
Проверка совпадения на диапазоне 0–12 подтверждает индуктивное рассуждение:
`T(n) = 2T(n−1) + 1`, `T(0) = 0`, значит `T(n) = 2ⁿ − 1`.

## 3. Палиндром без нормализации {#sol-ch54-03}

```python exec
def is_palindrome_lazy(text: str) -> bool:
    left, right = 0, len(text) - 1
    while left < right:
        while left < right and not text[left].isalpha():
            left += 1
        while left < right and not text[right].isalpha():
            right -= 1
        if text[left].lower() != text[right].lower():
            return False
        left += 1
        right -= 1
    return True


for sample in ["А роза упала на лапу Азора", "Я иду с мечем судия", "Привет"]:
    print(repr(sample), is_palindrome_lazy(sample))
```

```output
'А роза упала на лапу Азора' True
'Я иду с мечем судия' True
'Привет' False
```

Указатели пропускают всё, что не является буквой, поэтому копия строки не
создаётся: память `O(1)`, время `O(n)`. Внешний `while` завершается, когда
указатели встретились; если все пары совпали, строка — палиндром. Пустая
строка и строка из одного символа дают `True` без единой итерации: цикл
`while left < right` не выполняется.

## 4. Скобки нескольких видов {#sol-ch54-04}

```python exec
def bracket_error(text: str) -> int:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[tuple[str, int]] = []
    for index, char in enumerate(text):
        if char in "([{":
            stack.append((char, index))
        elif char in pairs:
            if not stack or stack[-1][0] != pairs[char]:
                return index
            stack.pop()
    return stack[0][1] if stack else -1


for sample in ["a(b[c]d)e", "a(b[c)d]e", "((()))"]:
    print(repr(sample), bracket_error(sample))
```

```output
'a(b[c]d)e' -1
'a(b[c)d]e' 5
'((()))' -1
```

Первая ошибка — либо закрывающая скобка, не совпавшая с вершиной стека, либо
лишняя закрывающая при пустом стеке; в обоих случаях возвращается её индекс.
Если строка закончилась, а стек не пуст, ошибка — первая незакрытая
открывающая, поэтому возвращается индекс `stack[0]`. Возврат `-1` означает
корректную последовательность.

## 5. Оптимальная стратегия угадывания {#sol-ch54-05}

```python exec
def best_guess(secret: int, low: int = 1, high: int = 100) -> int:
    attempts = 0
    while low <= high:
        attempts += 1
        middle = (low + high) // 2
        if middle == secret:
            return attempts
        if middle < secret:
            low = middle + 1
        else:
            high = middle - 1
    raise ValueError("секрет вне диапазона")


print([(secret, best_guess(secret)) for secret in (1, 50, 100)])
```

```output
[(1, 6), (50, 1), (100, 7)]
```

Каждая догадка делит оставшийся диапазон примерно пополам, поэтому число
попыток не превышает `⌈log₂(100)⌉ = 7`. Для секрета 1 требуется 6 попыток:
после 50, 25, 12, 6, 3 и 1 диапазон заканчивается. Если секрет вне диапазона,
цикл завершится без ответа, и функция честно поднимет `ValueError` вместо
бесконечного поиска.

## 6. Самая длинная цепочка Коллатца {#sol-ch54-06}

```python exec
def collatz_steps(start: int) -> int:
    if start < 1:
        raise ValueError("нужно положительное целое")
    number = start
    steps = 0
    while number != 1:
        number = number // 2 if number % 2 == 0 else 3 * number + 1
        steps += 1
    return steps


best = max(range(1, 1001), key=lambda value: (collatz_steps(value), -value))
print(best)
print(collatz_steps(best))
```

```output
871
178
```

Ключ сортировки `(шаги, −число)` выбирает максимум шагов, а при равенстве —
меньшее число: `−value` больше для меньшего `value`, поэтому `max` берёт его.
Цепочки пересчитываются заново для каждого числа, то есть время растёт как
сумма длин цепочек. Для 1000 чисел это приемлемо; для миллионов понадобился бы
кэш уже вычисленных значений (мемоизация) — но это отдельная оптимизация,
и начинать с неё не стоит.

## 7. Расшифровка Цезаря перебором {#sol-ch54-07}

```python exec
def caesar(text: str, shift: int) -> str:
    result: list[str] = []
    for char in text:
        if "a" <= char <= "z":
            result.append(chr((ord(char) - ord("a") + shift) % 26 + ord("a")))
        elif "A" <= char <= "Z":
            result.append(chr((ord(char) - ord("A") + shift) % 26 + ord("A")))
        else:
            result.append(char)
    return "".join(result)


cipher = "Clguba 3.14 — это здорово!"
for shift in range(26):
    candidate = caesar(cipher, -shift)
    if "Python" in candidate:
        print(shift, candidate)
```

```output
13 Python 3.14 — это здорово!
```

Перебор всех 26 ключей — это константное число вариантов, поэтому полный
перебор здесь не «медленный»: сложность `O(26 · n)` равна `O(n)`. Такой подход
называют атакой полным перебором ключей; для шифра Цезаря он работает, потому
что пространство ключей крошечное. Для современного шифрования это невозможно
из-за огромного пространства ключей — именно поэтому длина ключа важна.

## 8. Частоты с игнорированием слов {#sol-ch54-08}

```python exec
import re


def words(text: str) -> list[str]:
    return re.findall(r"[а-яёa-z]+", text.lower())


def top_words(
    text: str,
    limit: int = 3,
    stopwords: frozenset[str] = frozenset(),
) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for word in words(text):
        if word in stopwords:
            continue
        counts[word] = counts.get(word, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]


print(top_words("кот и пёс и кот", stopwords=frozenset({"и"})))
print(top_words("кот и пёс и кот"))
```

```output
[('кот', 2), ('пёс', 1)]
[('и', 2), ('кот', 2), ('пёс', 1)]
```

Стоп-слова фильтруются до подсчёта: так частоты остальных слов не искажаются.
Параметр по умолчанию — `frozenset()`, неизменяемое пустое множество: его можно
безопасно использовать как значение по умолчанию (изменяемый аргумент по
умолчанию — классическая ловушка). При равных частотах порядок алфавитный:
`и` идёт раньше `к` и `п`.

## 9. Поиск ошибки в игре {#sol-ch54-09}

Ошибка в том, что счётчик увеличивается только в ветке неверной догадки:

```python
if guess < secret:
    attempts += 1
elif guess > secret:
    attempts += 1
else:
    return "победа", attempts
```

При победе с первой попытки возвращается `0`, а не `1`. Счётчик должен
увеличиваться до ветвления — тогда он отражает число сделанных попыток
независимо от исхода.

```python exec
def play(secret: int, guesses: list[int], max_attempts: int = 5) -> tuple[str, int]:
    attempts = 0
    for guess in guesses:
        attempts += 1
        if attempts > max_attempts:
            return "поражение", max_attempts
        if guess == secret:
            return "победа", attempts
    return "не завершено", attempts


assert play(7, [7]) == ("победа", 1)
assert play(7, [1, 9, 7]) == ("победа", 3)
print(play(7, [7]))
print(play(7, [1, 9, 7]))
print("тесты прошли")
```

```output
('победа', 1)
('победа', 3)
тесты прошли
```

Тесты проверяют оба края: победу сразу и победу после двух неверных догадок.
Граница `attempts > max_attempts` срабатывает до проверки догадки, поэтому
шестая попытка не учитывается как победная и игра завершается поражением.

## 10. Мини-проект: игра «камень — ножницы — бумага» {#sol-ch54-10}

```python exec
RULES = {("камень", "ножницы"), ("ножницы", "бумага"), ("бумага", "камень")}


def play_rounds(moves: list[tuple[str, str]]) -> tuple[str, int, int]:
    score = [0, 0]
    for number, (first, second) in enumerate(moves, start=1):
        if (first, second) in RULES:
            score[0] += 1
            state = "победа игрока 1"
        elif (second, first) in RULES:
            score[1] += 1
            state = "победа игрока 2"
        else:
            state = "ничья"
        print(f"раунд {number}: {first} против {second} — {state}")
    if score[0] > score[1]:
        final = "победа игрока 1"
    elif score[1] > score[0]:
        final = "победа игрока 2"
    else:
        final = "ничья"
    return final, score[0], score[1]


moves = [
    ("камень", "ножницы"),
    ("бумага", "камень"),
    ("ножницы", "ножницы"),
    ("бумага", "ножницы"),
    ("камень", "бумага"),
]
print(play_rounds(moves))
```

```output
раунд 1: камень против ножницы — победа игрока 1
раунд 2: бумага против камень — победа игрока 1
раунд 3: ножницы против ножницы — ничья
раунд 4: бумага против ножницы — победа игрока 2
раунд 5: камень против бумага — победа игрока 2
('ничья', 2, 2)
```

Правила заданы множеством выигрышных пар: проверяется пара и её обратный
порядок, поэтому одна таблица покрывает оба направления. Состояние раунда
(`победа игрока 1`, `победа игрока 2`, `ничья`) и итоговое состояние
вычисляются из счёта, а не хранятся отдельно — это уменьшает число мест, где
можно ошибиться. Такую игру легко тестировать: ходы передаются списком, вывод
детерминирован, а результат не зависит от ввода с клавиатуры.

## Ответы на вопросы для самопроверки

1. Декомпозиция позволяет проверять части отдельно и заменять их, не
   переписывая всё решение; маленькую функцию проще понять и протестировать.
2. В FizzBuzz порядок определяет, какая ветка сработает первой: проверка
   «делится и на 3, и на 5» должна стоять раньше общих. Для скобок порядок
   задаёт правило стека: закрывающая должна совпасть с последней открытой.
3. Каждый ход `n` дисков требует двух перемещений `n−1` дисков и одного хода,
   откуда `T(n) = 2T(n−1) + 1` и `T(n) = 2ⁿ − 1`.
4. Конечный автомат — набор состояний и правил перехода; в игре это состояния
   ожидания, «мало», «много», победы и поражения, счётчик попыток и условия
   переходов.
5. Без явных выходов цикл может зависнуть при неверном вводе или исчерпании
   данных; перечисление выходов делает завершение гарантированным.
6. «Работает на тестах» означает проверку на конечном наборе значений;
   «доказано» — утверждение обо всех случаях, которого для Collatz нет.
7. Без фиксированного порядка при равных частотах результат зависел бы от
   порядка вставки и тесты стали бы нестабильными.
