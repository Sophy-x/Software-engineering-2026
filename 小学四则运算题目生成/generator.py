"""表达式生成器模块 (generator.py)

负责四则运算表达式的生成、约束剪枝与高效去重。
包含：
- 操作数随机生成（自然数、真分数、带分数）
- 表达式二叉树递归构建与即时剪枝
- 题目生成管理（基于规范化哈希去重、动态重试）
"""

import random
from fractions import Fraction
from typing import List, Optional, Set, Tuple
from fraction_utils import format_fraction
from tree import TreeNode

OPERATORS = ["+", "−", "×", "÷"]


def random_fraction(max_r: int) -> Fraction:
    """按规范随机生成数值范围在 [0, max_r) 内的操作数。

    生成类型：
    - 自然数：在 [0, max_r) 随机选取整数。
    - 真分数（纯真分数）：分子 a 随机在 [1, b-1]，分母 b 在 [2, max_r-1]（要求 max_r > 2）。
    - 带分数：整数部分 q 在 [1, max_r-1]，分子 a 在 [1, b-1]，分母 b 在 [2, max_r-1]（若 max_r > 2）。
    """
    if max_r <= 1:
        return Fraction(0, 1)

    types = ["natural"]
    if max_r > 2:
        types.extend(["proper", "mixed"])

    choice = random.choice(types)

    if choice == "natural":
        val = random.randint(0, max_r - 1)
        return Fraction(val, 1)
    elif choice == "proper":
        # 纯真分数：分母在 [2, max_r - 1]，分子在 [1, denominator - 1]
        b = random.randint(2, max_r - 1)
        a = random.randint(1, b - 1)
        return Fraction(a, b)
    else:
        # 带分数：整数部分在 [1, max_r - 1]
        q = random.randint(1, max_r - 1)
        b = random.randint(2, max_r - 1)
        a = random.randint(1, b - 1)
        return Fraction(q * b + a, b)


def evaluate_op(op: str, left_val: Fraction, right_val: Fraction) -> Optional[Fraction]:
    """计算单个二元操作，并进行业务约束剪枝。

    剪枝规则：
    1. 减法约束：差不能为负数 (left_val >= right_val)。
    2. 除法约束：除数不能为 0 (right_val != 0)。
    3. 除法结果约束：除法结果必须是真分数（分母严格大于 1，即不为整数）。

    Returns:
        若计算合法则返回结果 Fraction，否则返回 None。
    """
    if op == "+":
        return left_val + right_val
    elif op == "−":
        if left_val < right_val:
            return None
        return left_val - right_val
    elif op == "×":
        return left_val * right_val
    elif op == "÷":
        if right_val == 0:
            return None
        res = left_val / right_val
        # 需求规定：除法运算结果必须为真分数（分子小于分母，且不能是整数）
        if res.denominator == 1 or res.numerator >= res.denominator:
            return None
        return res
    return None


def generate_tree(num_ops: int, max_r: int, max_attempts: int = 50) -> Optional[TreeNode]:
    """递归生成具有 num_ops 个运算符的表达式树，并进行即时合法性检验。

    Args:
        num_ops: 运算符个数 (1 <= num_ops <= 3)
        max_r: 操作数范围约束
        max_attempts: 当前子树尝试最大次数

    Returns:
        合法的 TreeNode 对象，若无法生成则返回 None。
    """
    if num_ops == 0:
        val = random_fraction(max_r)
        return TreeNode(op=None, value=val)

    for _ in range(max_attempts):
        op = random.choice(OPERATORS)
        # 将操作符随机分配给左子树和右子树
        left_ops = random.randint(0, num_ops - 1)
        right_ops = num_ops - 1 - left_ops

        left_node = generate_tree(left_ops, max_r, max_attempts=20)
        if left_node is None:
            continue

        right_node = generate_tree(right_ops, max_r, max_attempts=20)
        if right_node is None:
            continue

        val = evaluate_op(op, left_node.value, right_node.value)
        if val is None:
            # 针对减法 left < right 的情况，若可能可尝试交换两子树（仅限减法结果反转）
            if op == "−" and right_node.value >= left_node.value:
                # 交换左右节点尝试满足非负
                swapped_val = evaluate_op("−", right_node.value, left_node.value)
                if swapped_val is not None:
                    return TreeNode(op="−", value=swapped_val, left=right_node, right=left_node)
            continue

        return TreeNode(op=op, value=val, left=left_node, right=right_node)

    return None


def generate_exercises(n: int, max_r: int, max_retries: int = 1000) -> Tuple[List[str], List[str]]:
    """批量生成不重复的小学四则运算题目及对应答案。

    - 算符数量：题目中的运算符个数在 1 到 3 之间随机。
    - 判重机制：使用 tree.canonical_repr() 维护全局已生成题目集合，完全过滤交换律等价题目。
    - 防死锁机制：连续达到最大重试次数 (max_retries) 无法生成新题时，抛出异常或提前终止并警告。

    Args:
        n: 题目数量
        max_r: 操作数上限数值 (> 0)
        max_retries: 连续失败重试阈值

    Returns:
        (exercises, answers) 字符串列表元组
    """
    exercises: List[str] = []
    answers: List[str] = []
    seen_canonical: Set[tuple] = set()

    consecutive_failures = 0

    while len(exercises) < n:
        num_ops = random.randint(1, 3)
        tree = generate_tree(num_ops, max_r)

        if tree is None:
            consecutive_failures += 1
            if consecutive_failures >= max_retries:
                raise RuntimeError(
                    f"在给定的参数 (r={max_r}) 空间下，无法生成更多不重复的合法题目。"
                    f"已生成 {len(exercises)} / {n} 道题。"
                )
            continue

        c_repr = tree.canonical_repr()
        if c_repr in seen_canonical:
            consecutive_failures += 1
            if consecutive_failures >= max_retries:
                raise RuntimeError(
                    f"题目空间已耗尽（连续 {max_retries} 次生成重复题目）。"
                    f"已生成 {len(exercises)} / {n} 道题。"
                )
            continue

        # 成功生成新题
        consecutive_failures = 0
        seen_canonical.add(c_repr)

        expr_str = f"{tree.to_infix()} ="
        ans_str = format_fraction(tree.value)

        exercises.append(expr_str)
        answers.append(ans_str)

    return exercises, answers
