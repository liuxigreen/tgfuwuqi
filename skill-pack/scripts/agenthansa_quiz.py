#!/usr/bin/env python3
import re

UNITS = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
    'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
    'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
    'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
    'eighteen': 18, 'nineteen': 19,
}

TENS = {
    'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
    'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90,
}

SCALE = {
    'hundred': 100,
    'thousand': 1000,
}

NUMBER_WORDS = set(UNITS) | set(TENS) | set(SCALE) | {'and'}


def _words_to_number(tokens):
    current = 0
    total = 0
    seen = False
    for token in tokens:
        if token == 'and':
            continue
        if token in UNITS:
            current += UNITS[token]
            seen = True
        elif token in TENS:
            current += TENS[token]
            seen = True
        elif token == 'hundred':
            current = max(1, current) * 100
            seen = True
        elif token == 'thousand':
            total += max(1, current) * 1000
            current = 0
            seen = True
        else:
            return None
    if not seen:
        return None
    return total + current


def normalize_question(question: str) -> str:
    text = (question or '').lower().replace('-', ' ')
    tokens = re.findall(r'\d+|[a-z]+|[^\w\s]', text)
    out = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in NUMBER_WORDS:
            j = i
            chunk = []
            while j < len(tokens) and tokens[j] in NUMBER_WORDS:
                chunk.append(tokens[j])
                j += 1
            value = _words_to_number(chunk)
            if value is not None:
                out.append(str(value))
                i = j
                continue
        out.append(tok)
        i += 1

    text = ' '.join(out)
    text = re.sub(r'\s+([?.!,;:])', r'\1', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _format_number(value):
    if isinstance(value, float) and abs(value - round(value)) < 1e-9:
        value = int(round(value))
    return str(value)


def _divide(a, b):
    if b == 0:
        return None
    val = a / b
    if abs(val - round(val)) < 1e-9:
        return int(round(val))
    return val


def _asks_total(q: str) -> bool:
    total_triggers = [
        ' in total', 'total?', ' total ', ' altogether',
        ' combined', ' together', 'all together', 'how many total',
    ]
    return any(token in q for token in total_triggers)


def solve_question_local(question: str):
    q = normalize_question(question)
    if not q:
        return None

    nums = [int(x) for x in re.findall(r'-?\d+', q)]

    if len(nums) >= 2:
        remainder_ctx = any(token in q for token in ['left over', 'leftover', 'remainder'])
        grouped_ctx = any(token in q for token in ['groups of', 'split into', 'divided into', 'divide into'])
        if remainder_ctx or ('remain' in q and grouped_ctx):
            divisor = nums[1]
            if divisor != 0:
                return str(nums[0] % divisor)

    m = re.search(r'\bsubtract\s+(-?\d+)\s+from\s+(-?\d+)\b', q)
    if m:
        return str(int(m.group(2)) - int(m.group(1)))

    m = re.search(r'\badd\s+(-?\d+)\s+to\s+(-?\d+)\b', q)
    if m:
        return str(int(m.group(1)) + int(m.group(2)))

    if 'sum of' in q and len(nums) >= 2:
        return str(nums[0] + nums[1])

    if 'product of' in q and len(nums) >= 2:
        return str(nums[0] * nums[1])

    if len(nums) >= 2 and _asks_total(q) and any(token in q for token in [
        ' each ', 'each has', 'each have', 'each carry',
        'each carries', 'each get', 'each gets', 'per ',
    ]):
        return str(nums[0] * nums[1])

    if any(token in q for token in ['split evenly among', 'each gets', 'each get', 'per ']) and len(nums) >= 2:
        val = _divide(nums[0], nums[1])
        if val is not None:
            return _format_number(val)

    if 'more than' in q and len(nums) >= 2:
        return str(nums[0] + nums[1])

    if nums and re.search(r'\b(double|doubles|doubled|twice)\b', q):
        return str(nums[0] * 2)

    if nums and re.search(r'\b(triple|triples|tripled|thrice)\b', q):
        return str(nums[0] * 3)

    if nums and re.search(r'\b(quadruple|quadruples|quadrupled)\b', q):
        return str(nums[0] * 4)

    m = re.search(r'\b(-?\d+)\s+(?:\w+\s+){0,4}?(fewer|less)\b.*?\bthan\s+(-?\d+)\b', q)
    if m:
        return str(int(m.group(3)) - int(m.group(1)))

    if len(nums) >= 2 and (
        'fewer than' in q or ' less than ' in q
        or re.search(r'\b\d+\s+fewer\b', q)
        or re.search(r'\b\d+\s+less\b', q)
    ):
        return str(nums[0] - nums[1])

    expr = re.sub(r'[^0-9+\-*/(). ]', '', q)
    if expr and any(ch.isdigit() for ch in expr) and any(op in expr for op in '+-*/'):
        try:
            if re.fullmatch(r'[0-9+\-*/(). ]+', expr):
                val = eval(expr, {'__builtins__': {}}, {})
                if isinstance(val, (int, float)):
                    return _format_number(val)
        except Exception:
            pass

    if not nums:
        return None

    total = nums[0]
    idx = 1
    tokens = re.findall(
        r'\b(gain|gains|find|finds|collect|collects|add|adds|plus|'
        r'lose|loses|give|gives|minus|less|subtract|spent|spends|'
        r'times|multiply|multiplied|divide|divided)\b|(?<![a-z])x(?![a-z])|\*',
        q
    )
    for token in tokens:
        if token == 'more' and 'more than' in q:
            continue
        if token in {'less'} and 'less than' in q:
            continue
        if idx >= len(nums):
            break
        n = nums[idx]
        idx += 1
        if token in {'gain', 'gains', 'find', 'finds', 'collect', 'collects', 'add', 'adds', 'plus'}:
            total += n
        elif token in {'lose', 'loses', 'give', 'gives', 'minus', 'less', 'subtract', 'spent', 'spends'}:
            total -= n
        elif token in {'times', 'multiply', 'multiplied', 'x', '*'}:
            total *= n
        elif token in {'divide', 'divided'}:
            val = _divide(total, n)
            if val is not None:
                total = val

    if 'half' in q:
        if any(token in q for token in [
            'gives away half', 'give away half', 'shares half',
            'share half', 'loses half', 'lose half', 'keeps half', 'keep half',
        ]):
            val = _divide(total, 2)
            if val is not None:
                total = val
        elif 'half of' in q:
            val = _divide(total, 2)
            if val is not None:
                total = val

    return _format_number(total)
