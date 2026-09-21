"""批改求值模块 (evaluator.py)

用于独立解析给定的题目文件与答案文件，计算并对比统计。

核心功能：
1. 分词解析 (Tokenizer)：正则提取带分数、纯分数、整数、运算符及括号。
2. 求值引擎 (Shunting-Yard 逆波兰算法)：双栈模型，中缀转后缀并执行精准无损分数计算。
3. 对错统计与输出 (grade_exercises)：逐行对比题目计算结果与答案，格式化写入 Grade.txt。
"""

import re
from fractions import Fraction
from typing import List, Tuple
from fraction_utils import parse_fraction

# 运算符优先级字典
PRECEDENCE = {
    "+": 1,
    "−": 1,
    "-": 1,  # 兼容 ASCII 减号
    "×": 2,
    "*": 2,  # 兼容 ASCII 乘号
    "÷": 2,
}

# 提取操作数（带分数、纯分数、整数）、运算符及括号的正规表达式
TOKEN_PATTERN = re.compile(r"\d+[’']\d+/\d+|\d+/\d+|\d+|[+−×÷()\-*]")


def tokenize(expr: str) -> List[str]:
    """对算式字符串进行分词处理。

    - 自动去除前导序号（如 '1. ', '1、', '(1) '）
    - 自动去除末尾的等号与空白（如 ' = '）
    - 规范化运算符（ASCII '-' 转 '−'，'*' 转 '×'）
    """
    s = expr.strip()
    # 去除题目可能携带的题号，例如 "1. ", "1、", "(1) "（必须有标点符号，防止误删第一个操作数）
    s = re.sub(r"^\(?\d+[\.、\)]\s*", "", s)
    # 去除末尾的等号及之后的内容
    s = re.sub(r"=\s*$", "", s).strip()

    raw_tokens = TOKEN_PATTERN.findall(s)
    tokens: List[str] = []
    for t in raw_tokens:
        if t == "-":
            tokens.append("−")
        elif t == "*":
            tokens.append("×")
        else:
            tokens.append(t)
    return tokens


def apply_operator(op: str, right: Fraction, left: Fraction) -> Fraction:
    """执行单个二元操作计算。"""
    if op == "+":
        return left + right
    elif op == "−":
        if left < right:
            raise ValueError(f"运算过程中产生负数: {left} − {right}")
        return left - right
    elif op == "×":
        return left * right
    elif op == "÷":
        if right == 0:
            raise ZeroDivisionError("运算过程中出现除以零错误")
        return left / right
    raise ValueError(f"未知操作符: {op}")


def evaluate_expression(expr: str) -> Fraction:
    """使用双栈调度场算法 (Shunting-Yard) 对算式字符串进行精准求值。

    Args:
        expr: 算式中缀表达式字符串

    Returns:
        最终求得的标准 Fraction 结果
    """
    tokens = tokenize(expr)
    if not tokens:
        raise ValueError(f"空算式或无法解析: {expr}")

    val_stack: List[Fraction] = []
    op_stack: List[str] = []

    for token in tokens:
        if token == "(":
            op_stack.append("(")
        elif token == ")":
            while op_stack and op_stack[-1] != "(":
                op = op_stack.pop()
                if len(val_stack) < 2:
                    raise ValueError(f"表达式语法错误: {expr}")
                r = val_stack.pop()
                l = val_stack.pop()
                val_stack.append(apply_operator(op, r, l))
            if not op_stack or op_stack[-1] != "(":
                raise ValueError(f"括号不匹配: {expr}")
            op_stack.pop()  # 弹出 '('
        elif token in PRECEDENCE:
            current_p = PRECEDENCE[token]
            while (
                op_stack
                and op_stack[-1] != "("
                and PRECEDENCE.get(op_stack[-1], 0) >= current_p
            ):
                op = op_stack.pop()
                if len(val_stack) < 2:
                    raise ValueError(f"表达式语法错误: {expr}")
                r = val_stack.pop()
                l = val_stack.pop()
                val_stack.append(apply_operator(op, r, l))
            op_stack.append(token)
        else:
            # 操作数：解析为 Fraction
            val_stack.append(parse_fraction(token))

    while op_stack:
        op = op_stack.pop()
        if op == "(":
            raise ValueError(f"括号不匹配: {expr}")
        if len(val_stack) < 2:
            raise ValueError(f"表达式语法错误: {expr}")
        r = val_stack.pop()
        l = val_stack.pop()
        val_stack.append(apply_operator(op, r, l))

    if len(val_stack) != 1:
        raise ValueError(f"表达式求值异常: {expr}")

    return val_stack[0]


def grade_exercises(
    exercise_path: str,
    answer_path: str,
    output_path: str = "Grade.txt",
) -> Tuple[List[int], List[int]]:
    """批改作业：对比题目文件与答案文件，输出统计至指定文件。

    格式要求：
    Correct: 5 (1, 3, 5, 7, 9)

    Wrong: 5 (2, 4, 6, 8, 10)

    Args:
        exercise_path: 题目文件路径
        answer_path: 答案文件路径
        output_path: 批改统计文件路径 (默认 Grade.txt)

    Returns:
        (correct_indices, wrong_indices) 题目序号列表元组（索引从 1 开始）
    """
    with open(exercise_path, "r", encoding="utf-8") as f:
        exercise_lines = [line.strip() for line in f if line.strip()]

    with open(answer_path, "r", encoding="utf-8") as f:
        answer_lines = [line.strip() for line in f if line.strip()]

    total_exercises = min(len(exercise_lines), len(answer_lines))
    correct_indices: List[int] = []
    wrong_indices: List[int] = []

    for idx in range(total_exercises):
        q_num = idx + 1
        raw_expr = exercise_lines[idx]
        raw_ans = answer_lines[idx]

        # 清除答案行可能携带的前导序号（如 "1. "）
        clean_ans = re.sub(r"^\(?\d+[\.、\)]\s*", "", raw_ans).strip()

        try:
            expected_val = evaluate_expression(raw_expr)
            given_val = parse_fraction(clean_ans)
            if expected_val == given_val:
                correct_indices.append(q_num)
            else:
                wrong_indices.append(q_num)
        except Exception:
            wrong_indices.append(q_num)

    # 格式化输出到 Grade.txt
    correct_list_str = ", ".join(map(str, correct_indices))
    wrong_list_str = ", ".join(map(str, wrong_indices))

    content = (
        f"Correct: {len(correct_indices)} ({correct_list_str})\n\n"
        f"Wrong: {len(wrong_indices)} ({wrong_list_str})\n"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return correct_indices, wrong_indices
