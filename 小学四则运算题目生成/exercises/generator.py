"""表达式生成器模块 (generator.py)

负责四则运算表达式的生成、约束剪枝与高效去重。

1. 运算符数量：每道题目中出现的运算符个数不超过 3 个 (num_ops in [1, 3])。
2. 数值范围：基于参数 -r，数值及分母均处于 [0, r) 区间。
   - 自然数：在 [0, r) 内随机采样整数。
   - 纯真分数：分母 d in [2, r)，分子 n in [1, d)。
   - 带分数：整数部分 q in [1, r)，分母 d in [2, r)，真分数分子 r' in [1, d)。
3. 减法非负剪枝 (e1 >= e2)：
   - 若 left.val < right.val，直接交换左右子树，确保 left.val >= right.val，差值非负。
4. 除法真分数剪枝：
   - 根据 spec.md 要求，真分数包含带分数（如 1’1/2）。
   - 合规判定：除数 right.val != 0，被除数 left.val > 0，且结果分母 res.denominator > 1。
   - 优雅处理：
     a. 若计算结果为整数（如 4 ÷ 2 = 2，分母为 1）：
        若 right.val / left.val 为真分数（如 2 ÷ 4 = 1/2），优先交换左右子树指针。
     b. 若交换仍不满足（如 3 ÷ 3 = 1），则重新采样右子树（多次重试），避免直接跳过。
5. 题目去重：
   - 基于 canonical_repr 判重，消除有限次交换 + 和 × 导致的同构题目。
"""

import random
from fractions import Fraction
from typing import List, Optional, Set, Tuple
from .fraction_utils import format_fraction, is_true_fraction
from .tree import TreeNode

OPERATORS = ["+", "−", "×", "÷"]


def random_leaf(max_r: int) -> Fraction:
    """按规范随机生成数值范围在 [0, max_r) 内的叶子操作数。

    - 当 max_r <= 1 时：只能生成自然数 0。
    - 当 max_r == 2 时：生成自然数 0 或 1（因为分母要求 d >= 2 且 d < max_r，此时无合法分数分母）。
    - 当 max_r > 2 时：以均等概率随机选取自然数、纯真分数、带分数。
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
        # 纯真分数：分母 d in [2, max_r - 1]，分子 n in [1, d - 1]
        d = random.randint(2, max_r - 1)
        n = random.randint(1, d - 1)
        return Fraction(n, d)
    else:
        # 带分数：整数部分 q in [1, max_r - 1]，分母 d in [2, max_r - 1]，分子 r in [1, d - 1]
        q = random.randint(1, max_r - 1)
        d = random.randint(2, max_r - 1)
        r_prime = random.randint(1, d - 1)
        return Fraction(q * d + r_prime, d)


def evaluate_binary(op: str, left_val: Fraction, right_val: Fraction) -> Optional[Fraction]:
    """计算单个二元操作，若不符合四则运算业务约束则返回 None。"""
    if op == "+":
        return left_val + right_val
    elif op == "−":
        if left_val < right_val:
            return None
        return left_val - right_val
    elif op == "×":
        return left_val * right_val
    elif op == "÷":
        if right_val == 0 or left_val <= 0:
            return None
        res = left_val / right_val
        # 结果必须为真分数（包含纯真分数和带分数，即化简后分母 > 1）
        if not is_true_fraction(res):
            return None
        return res
    return None


def generate_tree(num_ops: int, max_r: int, max_attempts: int = 50) -> Optional[TreeNode]:
    """递归构建包含 num_ops 个运算符的表达式二叉树，并执行即时合规剪枝与子树调整。

    Args:
        num_ops: 当前子树中的运算符总个数 (0 <= num_ops <= 3)
        max_r: 数值上限
        max_attempts: 尝试生成当前子树的最大次数

    Returns:
        合规的 TreeNode，若尝试耗尽仍无法构建则返回 None。
    """
    if num_ops == 0:
        val = random_leaf(max_r)
        return TreeNode(op=None, val=val)

    for _ in range(max_attempts):
        op = random.choice(OPERATORS)
        # 将剩余的操作符 (num_ops - 1) 分配给左右子树
        left_ops = random.randint(0, num_ops - 1)
        right_ops = num_ops - 1 - left_ops

        left_node = generate_tree(left_ops, max_r, max_attempts=20)
        if left_node is None:
            continue

        right_node = generate_tree(right_ops, max_r, max_attempts=20)
        if right_node is None:
            continue

        # 1. 针对减法 e1 − e2：若 e1 < e2，直接在二叉树上交换左右指针，保证 e1 >= e2 非负
        if op == "−":
            if left_node.val < right_node.val:
                left_node, right_node = right_node, left_node
            diff = left_node.val - right_node.val
            return TreeNode(op="−", val=diff, left=left_node, right=right_node)

        # 2. 针对除法 e1 ÷ e2：必须确保除法结果为真分数（或者是带分数，即 res > 0 且分母 > 1）
        elif op == "÷":
            # 被除数必须 > 0 才能商为正真分数
            if left_node.val <= 0:
                # 若右子树值 > 0，尝试交换
                if right_node.val > 0:
                    left_node, right_node = right_node, left_node
                else:
                    continue

            # 检查当前除法是否直接满足真分数
            if right_node.val != 0:
                res = left_node.val / right_node.val
                if is_true_fraction(res):
                    return TreeNode(op="÷", val=res, left=left_node, right=right_node)

                # 若商不是真分数（如 4 ÷ 2 = 2 为整数）：
                # 处理 A：尝试交换左右操作数。若 right / left 为真分数（例如 2 ÷ 4 = 1/2），直接交换
                swapped_res = right_node.val / left_node.val
                if is_true_fraction(swapped_res):
                    return TreeNode(op="÷", val=swapped_res, left=right_node, right=left_node)

            # 处理 B：交换仍不满足时（如 3 ÷ 3 = 1），针对右子树重新采样多次
            found_valid_right = False
            for _ in range(15):
                new_right = generate_tree(right_ops, max_r, max_attempts=5)
                if new_right is not None and new_right.val != 0:
                    candidate_res = left_node.val / new_right.val
                    if is_true_fraction(candidate_res):
                        right_node = new_right
                        found_valid_right = True
                        break
                    # 也检查反向是否构成真分数，如构成，直接返回
                    swapped_cand = new_right.val / left_node.val
                    if is_true_fraction(swapped_cand):
                        return TreeNode(op="÷", val=swapped_cand, left=new_right, right=left_node)

            if found_valid_right:
                val = left_node.val / right_node.val
                return TreeNode(op="÷", val=val, left=left_node, right=right_node)

            # 若多次尝试后仍无法构造合法除法，放弃本轮 op 采样
            continue

        # 3. 针对加法 '+' 和乘法 '×'：由于操作数均为非负数，直接计算即可
        elif op == "+":
            val = left_node.val + right_node.val
            return TreeNode(op="+", val=val, left=left_node, right=right_node)
        elif op == "×":
            val = left_node.val * right_node.val
            return TreeNode(op="×", val=val, left=left_node, right=right_node)

    return None


def generate_exercises(n: int, max_r: int, max_retries: int = 2000) -> Tuple[List[str], List[str]]:
    """批量生成指定数量不重复的小学四则运算题目和对应标准答案。

    - 算符数量：题目中的运算符个数在 1 到 3 之间随机选取。
    - 查重机制：采用 Canonical AST 规范化字符串存入 set 进行全局碰撞检测。
    - 防死循环机制：连续达到 max_retries 次无法产出新题目时主动抛出异常提示并退出。

    Args:
        n: 目标生成题目数量
        max_r: 操作数及分母取值上限
        max_retries: 连续失败重试阈值

    Returns:
        (exercises, answers) 字符串列表元组
    """
    exercises: List[str] = []
    answers: List[str] = []
    seen_canonical: Set[str] = set()

    consecutive_failures = 0

    while len(exercises) < n:
        num_ops = random.randint(1, 3)
        tree = generate_tree(num_ops, max_r)

        if tree is None:
            consecutive_failures += 1
            if consecutive_failures >= max_retries:
                raise RuntimeError(
                    f"参数 (r={max_r}) 下的合法题目解空间已耗尽或难以生成。"
                    f"已成功生成 {len(exercises)} / {n} 道题。"
                )
            continue

        c_repr = tree.canonical_repr()
        if c_repr in seen_canonical:
            consecutive_failures += 1
            if consecutive_failures >= max_retries:
                raise RuntimeError(
                    f"题目查重空间耗尽（连续 {max_retries} 次生成重复题目）。"
                    f"已成功生成 {len(exercises)} / {n} 道题。"
                )
            continue

        # 成功生成新题
        consecutive_failures = 0
        seen_canonical.add(c_repr)

        expr_str = f"{tree.to_infix()} = "
        ans_str = format_fraction(tree.val)

        exercises.append(expr_str)
        answers.append(ans_str)

    return exercises, answers
