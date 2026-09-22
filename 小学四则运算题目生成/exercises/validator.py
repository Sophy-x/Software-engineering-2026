"""输出校验模块 (validator.py)

对"即将写入 Exercises.txt 的最终题目文本"做独立复核，不依赖表达式树与生成器
的任何内部结构，仅按字符串做统计，用于防止不合格题目被静默写入文件。

核心约定 (spec.md 第 5 条)：每道题目中出现的四则运算符个数不超过 3 个。
注意：真分数与带分数中的 '/' 属于操作数的一部分，不是四则运算符，不计入数量。
例如 "3 ÷ (92 − 90’27/83) ÷ (12/13 + 92 − 18’13/17) = " 含 5 个四则运算符
(2 个 ÷、2 个 −、1 个 +)，而其中的 '/' 全部忽略。
"""

import re
from typing import List, NamedTuple, Optional, Sequence

# 操作数：带分数 (q’a/b 或 q'a/b)、纯真分数 (a/b)、自然数 (a)
OPERAND_PATTERN = re.compile(r"\d+[’']\d+/\d+|\d+/\d+|\d+")

# 四则运算符：仅这 4 个符号计入数量；'/' 不在其中
OPERATOR_PATTERN = re.compile(r"[+−×÷]")

MAX_OPERATORS = 3
MIN_OPERATORS = 1


class Violation(NamedTuple):
    """一条不合格题目的描述。"""

    index: int  # 题目序号（从 1 开始）
    expression: str  # 题目原文
    reason: str  # 不合格原因


def count_operators(expr: str) -> int:
    """统计算式中四则运算符的个数，分数中的 '/' 不计入。

    实现方式：先剔除全部操作数（自然数、真分数、带分数），
    再在剩余文本中匹配 '+' '−' '×' '÷'，因此与表达式树无关，属于独立复核。
    """
    residue = OPERAND_PATTERN.sub(" ", expr)
    return len(OPERATOR_PATTERN.findall(residue))


def validate_exercises(
    exercises: Sequence[str],
    answers: Optional[Sequence[str]] = None,
    max_ops: int = MAX_OPERATORS,
    min_ops: int = MIN_OPERATORS,
) -> List[Violation]:
    """校验待写出的题目（及可选答案）列表，返回全部不合格项。

    检查内容：
    1. 题目与答案数量一致（传入 answers 时）；
    2. 题目以 '=' 结尾（spec.md 第 2 条：四则运算题目形如 e = ）；
    3. 题目中四则运算符个数在 [min_ops, max_ops] 区间内，分数中的 '/' 不计入。

    Args:
        exercises: 题目字符串列表（含末尾 '='）
        answers: 答案字符串列表，可选；传入时校验数量一致
        max_ops: 允许的最大运算符个数，默认 3
        min_ops: 允许的最小运算符个数，默认 1

    Returns:
        不合格项列表；为空表示全部通过。
    """
    violations: List[Violation] = []

    if answers is not None and len(answers) != len(exercises):
        violations.append(
            Violation(
                0,
                "",
                f"题目与答案数量不一致：题目 {len(exercises)} 条，答案 {len(answers)} 条",
            )
        )

    for index, expression in enumerate(exercises, 1):
        text = expression.strip()
        if not text.endswith("="):
            violations.append(Violation(index, expression, "题目缺少末尾的等号 '='"))
            continue

        n_ops = count_operators(text)
        if not (min_ops <= n_ops <= max_ops):
            violations.append(
                Violation(
                    index,
                    expression,
                    f"运算符数量为 {n_ops}，超出允许范围 {min_ops}~{max_ops}",
                )
            )

    return violations


def describe_violations(violations: Sequence[Violation], limit: int = 20) -> str:
    """将不合格项格式化为便于阅读的多行文本（最多列出 limit 条）。"""
    lines = [f"共发现 {len(violations)} 道不合格题目："]
    for violation in violations[:limit]:
        if violation.index > 0:
            lines.append(
                f"  - 第 {violation.index} 题（{violation.reason}）：{violation.expression}"
            )
        else:
            lines.append(f"  - {violation.reason}")
    if len(violations) > limit:
        lines.append(f"  ... 其余 {len(violations) - limit} 道省略")
    return "\n".join(lines)
