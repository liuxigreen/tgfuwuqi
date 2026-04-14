#!/usr/bin/env python3
"""
AgentHansa Context-Aware Red Envelope Solver
=============================================
Multi-strategy solver with pattern learning, difficulty assessment,
and adaptive solving. Remembers past puzzles to solve similar ones faster.
"""

import json
import re
import time
import hashlib
import operator
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, Callable

# ── Pattern Memory ──────────────────────────────────────────────────────────

MEMORY_PATH = Path(__file__).parent / "solver_memory.json"

OPERATORS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
    '%': operator.mod,
    '**': operator.pow,
    '>>': operator.rshift,
    '<<': operator.lshift,
    '&': operator.and_,
    '|': operator.or_,
    '^': operator.xor,
}

# Common puzzle patterns with solver functions
PATTERNS: Dict[str, Callable[[str], Optional[str]]] = {}

def register_pattern(name: str):
    """Decorator to register a solving pattern."""
    def decorator(fn):
        PATTERNS[name] = fn
        return fn
    return decorator


class SolverMemory:
    """Persistent memory for solved puzzles and patterns."""

    def __init__(self, path: Path = MEMORY_PATH):
        self.path = path
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text())
            except Exception:
                pass
        return {
            "solved": {},         # hash -> {question, answer, pattern, ts}
            "patterns": {},       # pattern_name -> {hits, misses, avg_time}
            "difficulty_log": [], # {hash, difficulty, time_spent, pattern}
            "stats": {
                "total_solved": 0,
                "total_failed": 0,
                "by_difficulty": {"trivial": 0, "easy": 0, "medium": 0, "hard": 0, "impossible": 0},
                "by_pattern": {}
            }
        }

    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False))

    def lookup(self, question: str) -> Optional[str]:
        """Look up a previously solved question."""
        h = hashlib.md5(question.strip().lower().encode()).hexdigest()
        entry = self.data["solved"].get(h)
        if entry:
            age_hours = (time.time() - entry["ts"]) / 3600
            if age_hours < 720:  # 30 days
                return entry["answer"]
        return None

    def remember(self, question: str, answer: str, pattern: str, difficulty: str):
        """Store a solved puzzle."""
        h = hashlib.md5(question.strip().lower().encode()).hexdigest()
        self.data["solved"][h] = {
            "question": question,
            "answer": answer,
            "pattern": pattern,
            "difficulty": difficulty,
            "ts": time.time()
        }
        self.data["stats"]["total_solved"] += 1
        self.data["stats"]["by_difficulty"][difficulty] = (
            self.data["stats"]["by_difficulty"].get(difficulty, 0) + 1
        )
        if pattern not in self.data["stats"]["by_pattern"]:
            self.data["stats"]["by_pattern"][pattern] = 0
        self.data["stats"]["by_pattern"][pattern] += 1
        self.save()

    def record_failure(self, question: str, difficulty: str):
        self.data["stats"]["total_failed"] += 1
        self.save()

    def get_pattern_success_rate(self, pattern: str) -> float:
        """Get success rate for a pattern."""
        hits = self.data["stats"]["by_pattern"].get(pattern, 0)
        total = self.data["stats"]["total_solved"] + self.data["stats"]["total_failed"]
        if total == 0:
            return 0.5
        return hits / total


# ── Difficulty Assessment ────────────────────────────────────────────────────

class DifficultyAssessor:
    """Assess puzzle difficulty before attempting to solve."""

    @staticmethod
    def assess(question: str, answer: str = None) -> str:
        """
        Returns: trivial | easy | medium | hard | impossible
        """
        q = question.strip()

        # If answer is already given
        if answer and answer.strip():
            return "trivial"

        length = len(q)

        # Pure math
        if re.match(r'^[\d\s\+\-\*\/\(\)\.]+$', q):
            ops = len(re.findall(r'[\+\-\*\/]', q))
            if ops <= 1:
                return "easy"
            if ops <= 3:
                return "medium"
            return "hard"

        # Word/emoji puzzles
        emojis = len(re.findall(r'[\U0001F300-\U0001FAFF]', q))
        if emojis > 3:
            return "hard"

        # Text-based riddles
        if '?' in q or any(w in q.lower() for w in ['what', 'how many', 'find', 'next', 'complete']):
            if length < 50:
                return "medium"
            return "hard"

        # Short codes
        if length < 20:
            return "easy"

        return "medium"


# ── Solving Strategies ──────────────────────────────────────────────────────

@register_pattern("direct_answer")
def solve_direct(question: str, answer: str = None) -> Optional[str]:
    """Answer is already provided."""
    if answer and answer.strip():
        return answer.strip()
    return None


@register_pattern("arithmetic")
def solve_arithmetic(question: str, **_) -> Optional[str]:
    """Extract and evaluate arithmetic expressions."""
    q = question.replace('×', '*').replace('÷', '/').replace('^', '**')

    # Try direct eval of math expression
    expr_match = re.search(r'([\d\s\+\-\*\/\(\)\.\%]+)', q)
    if expr_match:
        expr = expr_match.group(1).strip()
        if any(op in expr for op in ['+', '-', '*', '/']):
            try:
                result = eval(expr)
                if isinstance(result, float) and result == int(result):
                    return str(int(result))
                return str(round(result, 4))
            except Exception:
                pass

    # "X + Y = ?" pattern
    eq_match = re.search(r'(\d+)\s*([\+\-\*\/])\s*(\d+)\s*=?\s*\?', q)
    if eq_match:
        a, op, b = int(eq_match.group(1)), eq_match.group(2), int(eq_match.group(3))
        result = OPERATORS[op](a, b)
        return str(int(result)) if isinstance(result, float) and result == int(result) else str(result)

    # "If X = Y, what is Z?" pattern
    assign = re.findall(r'(\w)\s*=\s*(\d+)', q)
    if assign:
        vars_dict = {k: int(v) for k, v in assign}
        expr_part = re.search(r'(?:what is|find|calculate)\s+(.+?)(?:\?|$)', q, re.I)
        if expr_part:
            expr_str = expr_part.group(1)
            for var, val in vars_dict.items():
                expr_str = expr_str.replace(var, str(val))
            try:
                result = eval(expr_str.replace('^', '**'))
                return str(int(result)) if isinstance(result, float) and result == int(result) else str(result)
            except Exception:
                pass

    return None


@register_pattern("sequence")
def solve_sequence(question: str, **_) -> Optional[str]:
    """Find the next number in a sequence."""
    numbers = re.findall(r'-?\d+', question)
    if len(numbers) < 3:
        return None

    nums = [int(n) for n in numbers]

    # Check if last number is "?" context — use all but maybe last is the sequence
    if 'next' in question.lower() or 'find' in question.lower() or '?' in question:
        seq = nums
    else:
        seq = nums

    if len(seq) < 3:
        return None

    # Arithmetic progression
    diffs = [seq[i+1] - seq[i] for i in range(len(seq)-1)]
    if len(set(diffs)) == 1:
        return str(seq[-1] + diffs[0])

    # Geometric progression
    if all(seq[i] != 0 for i in range(len(seq)-1)):
        ratios = [seq[i+1] / seq[i] for i in range(len(seq)-1)]
        if all(abs(r - ratios[0]) < 0.001 for r in ratios):
            result = seq[-1] * ratios[0]
            return str(int(result)) if result == int(result) else str(round(result, 2))

    # Second-order differences
    if len(diffs) >= 3:
        diffs2 = [diffs[i+1] - diffs[i] for i in range(len(diffs)-1)]
        if len(set(diffs2)) == 1:
            next_diff = diffs[-1] + diffs2[0]
            return str(seq[-1] + next_diff)

    # Fibonacci-like
    if len(seq) >= 3:
        is_fib = all(seq[i] == seq[i-1] + seq[i-2] for i in range(2, min(5, len(seq))))
        if is_fib:
            return str(seq[-1] + seq[-2])

    return None


@register_pattern("word_puzzle")
def solve_word_puzzle(question: str, **_) -> Optional[str]:
    """Solve word-based puzzles."""
    q = question.lower()

    # "How many X in Y?"
    count_match = re.search(r'how many (\w)\w*\s+(?:in|does)\s+[\"']?(\w+)[\"']?', q)
    if count_match:
        letter = count_match.group(1)
        word = count_match.group(2)
        return str(word.count(letter))

    # Count specific characters
    count_match2 = re.search(r'count (?:the )?(?:letter|character)s?\s+[\"']?(\w)[\"']?\s+in\s+[\"']?(\w+)[\"']?', q)
    if count_match2:
        return str(count_match2.group(2).count(count_match2.group(1)))

    # "What comes next? A, B, C, ?"
    alpha = re.findall(r'([A-Za-z])', question)
    if len(alpha) >= 3:
        ords = [ord(c.upper()) for c in alpha]
        diffs = [ords[i+1] - ords[i] for i in range(len(ords)-1)]
        if len(set(diffs)) == 1:
            next_char = chr(ords[-1] + diffs[0])
            return next_char

    return None


@register_pattern("emoji_puzzle")
def solve_emoji(question: str, **_) -> Optional[str]:
    """Emoji-based math puzzles (e.g., 🍎 + 🍎 = 10, 🍎 + 🍌 = 7)."""
    import re

    # Find emoji equations
    equations = re.findall(r'([^\=\s]+?)\s*=\s*(\d+)', question)
    if not equations:
        return None

    # Map emojis to values
    emoji_values = {}
    for lhs, rhs in equations:
        rhs_val = int(rhs)
        emojis_in_lhs = re.findall(r'[\U0001F300-\U0001FAFF\U00002600-\U000027BF]', lhs)
        unique = list(set(emojis_in_lhs))

        if len(unique) == 1 and emojis_in_lhs.count(unique[0]) > 0:
            count = emojis_in_lhs.count(unique[0])
            emoji_values[unique[0]] = rhs_val / count

    # Solve for final expression (usually last line with ?)
    question_lines = question.replace('?', ' ?').split('\n')
    for line in question_lines:
        if '?' in line:
            expr = line.strip().rstrip('?').strip()
            emojis_in_expr = re.findall(r'[\U0001F300-\U0001FAFF\U00002600-\U000027BF]', expr)
            ops = re.findall(r'[\+\-\*\/]', expr)

            if all(e in emoji_values for e in emojis_in_expr):
                values = [emoji_values[e] for e in emojis_in_expr]
                result = values[0]
                for i, op in enumerate(ops):
                    if i + 1 < len(values):
                        result = OPERATORS[op](result, values[i + 1])
                return str(int(result)) if result == int(result) else str(round(result, 2))

    return None


@register_pattern("logic")
def solve_logic(question: str, **_) -> Optional[str]:
    """Simple logic puzzles."""
    q = question.lower()

    # "X is greater/less than Y" comparisons
    greater = re.findall(r'(\w+)\s+(?:is|>)\s+(?:greater|bigger|larger|more|>)\s+than\s+(\w+)', q)
    less = re.findall(r'(\w+)\s+(?:is|<)\s+(?:less|smaller|fewer|<)\s+than\s+(\w+)', q)

    # "Arrange in order"
    if 'order' in q or 'arrange' in q or 'sort' in q:
        numbers = re.findall(r'\d+', q)
        if numbers:
            ascending = 'asc' in q or 'smallest' in q or 'smallest to' in q
            if 'desc' in q or 'largest' in q or 'largest to' in q:
                ascending = False
            sorted_nums = sorted([int(n) for n in numbers], reverse=not ascending)
            return ','.join(str(n) for n in sorted_nums)

    return None


@register_pattern("pattern_recognition")
def solve_pattern(question: str, **_) -> Optional[str]:
    """Detect patterns in number grids or tables."""
    lines = question.strip().split('\n')
    grid = []
    for line in lines:
        nums = re.findall(r'-?\d+', line)
        if len(nums) >= 2:
            grid.append([int(n) for n in nums])

    if len(grid) < 2:
        return None

    # Check if each row follows same operation
    # e.g., row: [a, b, a+b]
    if all(len(row) == 3 for row in grid):
        # Try a op b = c
        for op_sym, op_fn in OPERATORS.items():
            if op_sym in ('>>', '<<', '&', '|', '^', '%', '**'):
                continue
            valid = True
            for row in grid:
                try:
                    if abs(op_fn(row[0], row[1]) - row[2]) > 0.01:
                        valid = False
                        break
                except Exception:
                    valid = False
                    break
            if valid:
                # Apply to last row if it has a missing value (represented by 0 or ?)
                return None  # Grid is complete, no solving needed

    # Row sum pattern
    if all(len(row) >= 2 for row in grid):
        row_sums = [sum(row) for row in grid]
        if len(set(row_sums)) == 1:
            # All rows sum to same value
            pass

    return None


# ── Solver Engine ────────────────────────────────────────────────────────────

class SmartSolver:
    """
    Multi-strategy context-aware solver.

    Order of operations:
    1. Check memory for exact match
    2. Assess difficulty
    3. Try patterns in order of success rate
    4. Remember solution for future
    """

    def __init__(self, memory: SolverMemory = None):
        self.memory = memory or SolverMemory()
        self.strategies = list(PATTERNS.items())

    def _sorted_strategies(self) -> list:
        """Sort strategies by historical success rate (best first)."""
        return sorted(
            self.strategies,
            key=lambda x: self.memory.get_pattern_success_rate(x[0]),
            reverse=True
        )

    def solve(self, question: str, answer: str = None, context: dict = None) -> dict:
        """
        Main solving entry point.

        Returns:
            {
                "success": bool,
                "answer": str or None,
                "method": str,       # pattern name used
                "difficulty": str,
                "from_memory": bool,
                "time_ms": float
            }
        """
        start = time.time()

        # 1. Check if answer is already given
        if answer and answer.strip():
            result = {
                "success": True,
                "answer": answer.strip(),
                "method": "direct_answer",
                "difficulty": "trivial",
                "from_memory": False,
                "time_ms": (time.time() - start) * 1000
            }
            self.memory.remember(question, answer.strip(), "direct_answer", "trivial")
            return result

        # 2. Check memory
        cached = self.memory.lookup(question)
        if cached:
            return {
                "success": True,
                "answer": cached,
                "method": "memory",
                "difficulty": "trivial",
                "from_memory": True,
                "time_ms": (time.time() - start) * 1000
            }

        # 3. Assess difficulty
        difficulty = DifficultyAssessor.assess(question, answer)

        # 4. Try strategies in order of success rate
        for name, strategy_fn in self._sorted_strategies():
            if name == "direct_answer":
                continue
            try:
                result = strategy_fn(question, answer=answer)
                if result is not None:
                    elapsed = (time.time() - start) * 1000
                    self.memory.remember(question, result, name, difficulty)
                    return {
                        "success": True,
                        "answer": result,
                        "method": name,
                        "difficulty": difficulty,
                        "from_memory": False,
                        "time_ms": elapsed
                    }
            except Exception as e:
                continue

        # 5. All strategies failed
        self.memory.record_failure(question, difficulty)
        return {
            "success": False,
            "answer": None,
            "method": "none",
            "difficulty": difficulty,
            "from_memory": False,
            "time_ms": (time.time() - start) * 1000
        }

    def stats(self) -> dict:
        """Return solver statistics."""
        return self.memory.data["stats"]


# ── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    """Test the solver with sample puzzles."""
    solver = SmartSolver()

    test_puzzles = [
        ("What is 15 + 27?", None),
        ("Find the next number: 2, 4, 8, 16, ?", None),
        ("🍎 + 🍎 = 10\n🍎 + 🍌 = 7\n🍌 + 🍌 = ?", None),
        ("How many R's in strawberry?", None),
        ("3 * 7 + 2 = ?", None),
        ("1, 1, 2, 3, 5, 8, ?", None),
    ]

    for question, answer in test_puzzles:
        result = solver.solve(question, answer)
        status = "✅" if result["success"] else "❌"
        print(f"{status} Q: {question}")
        print(f"   A: {result['answer']} [{result['method']}, {result['difficulty']}, {result['time_ms']:.1f}ms]")
        print()

    print("📊 Stats:", json.dumps(solver.stats(), indent=2))


if __name__ == "__main__":
    main()
