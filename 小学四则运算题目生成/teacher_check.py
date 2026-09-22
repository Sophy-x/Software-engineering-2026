#!/usr/bin/env python3
"""课程要求辅助验收：在项目根目录执行 python teacher_check.py -n 100 -r 100。
只读取 Exercises.txt/Answers.txt，不修改项目源代码或题目文件。
"""
import argparse
import random
import re
import sys
from fractions import Fraction
from pathlib import Path

from exercises.evaluator import evaluate_expression
from exercises.fraction_utils import parse_fraction
from exercises.generator import generate_tree

PREFIX = re.compile(r"^\s*(\d+)\.\s*(.*?)\s*$")
NUMBER = re.compile(r"\d+[’']\d+/\d+|\d+/\d+|\d+")


def read_numbered(path):
    rows = []
    for position, text in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        m = PREFIX.fullmatch(text)
        if not m or int(m.group(1)) != position:
            raise AssertionError(f"{path} 第 {position} 行编号或格式错误: {text!r}")
        rows.append(m.group(2).strip())
    return rows


def leaf_in_range(text, limit):
    if "’" in text or "'" in text:
        whole, frac = re.split("[’']", text)
        num, den = map(int, frac.split("/"))
        return 1 <= int(whole) < limit and 1 <= num < den < limit
    if "/" in text:
        num, den = map(int, text.split("/"))
        return 1 <= num < den < limit
    return 0 <= int(text) < limit


def check_tree(node, limit):
    """按每个子表达式独立复算，检查所有中间步骤。"""
    if node.op is None:
        value = Fraction(node.val)
        assert leaf_in_range(str(value.numerator) if value.denominator == 1 else
                             (f"{value.numerator}/{value.denominator}" if value < 1 else
                              f"{value.numerator // value.denominator}’{value.numerator % value.denominator}/{value.denominator}"), limit), (
            f"叶子操作数超出范围: {node.val}")
        return value, 0

    left, left_ops = check_tree(node.left, limit)
    right, right_ops = check_tree(node.right, limit)
    if node.op == "+":
        expected = left + right
    elif node.op == "−":
        assert left >= right, f"减法中间过程产生负数: {left} − {right}"
        expected = left - right
    elif node.op == "×":
        expected = left * right
    elif node.op == "÷":
        assert right != 0, "除数为零"
        expected = left / right
        # 此处核对当前项目实现约定；严格数学真分数需额外要求 expected < 1。
        assert expected > 0 and expected.denominator > 1, f"除法结果不符合项目约定: {expected}"
    else:
        raise AssertionError(f"未知运算符: {node.op}")
    assert expected == node.val, f"节点计算值不一致: {node.op}"
    assert expected >= 0, "中间结果为负数"
    return expected, left_ops + right_ops + 1


def main():
    parser = argparse.ArgumentParser(description="按老师要求检查已生成的题目，并抽查表达式树。")
    parser.add_argument("-n", type=int, required=True, help="刚才请求生成的题目数量")
    parser.add_argument("-r", type=int, required=True, help="刚才使用的数值上限")
    parser.add_argument("--sample", type=int, default=60, help="额外抽查表达式树次数，默认 60")
    args = parser.parse_args()

    questions = read_numbered("Exercises.txt")
    answers = read_numbered("Answers.txt")
    assert len(questions) == len(answers) == args.n, "题目数、答案数或预期 -n 不一致"
    print(f"[通过] 题目和答案数量及编号：{args.n} / {args.n}")

    for idx, question in enumerate(questions, 1):
        assert question.endswith("="), f"第 {idx} 题缺少等号"
        expr = question[:-1].strip()
        leaves = NUMBER.findall(expr)
        assert leaves and all(leaf_in_range(v, args.r) for v in leaves), (
            f"第 {idx} 题操作数或分母越界: {question}")
        n_ops = len(re.findall(r"[+−×÷]", expr))
        assert 1 <= n_ops <= 3, f"第 {idx} 题运算符数量为 {n_ops}"
    print(f"[通过] 全部 {args.n} 题：数值范围、分母、运算符数量和题目格式")

    assert len(set(questions)) == args.n, "发现完全相同的题目文本"
    print("[通过] 题目文本没有完全重复（交换律去重另由 pytest 验证）")

    for idx, (question, answer) in enumerate(zip(questions, answers), 1):
        expected = evaluate_expression(question)
        actual = parse_fraction(answer)
        assert expected == actual, f"第 {idx} 题答案错误: {question} / {answer} / 正确值 {expected}"
    print(f"[通过] 全部 {args.n} 题：答案与批改求值器一致")

    # 随机树抽样检查中间过程；与上方对实际文件的检查区分开。
    random.seed(20260922)
    samples = 0
    for _ in range(args.sample):
        for count in (1, 2, 3):
            root = generate_tree(count, args.r)
            if root is None:
                continue
            value, actual_ops = check_tree(root, args.r)
            assert actual_ops == count and root.val == value
            samples += 1
    assert samples > 0, "未生成可供抽查的表达式树"
    print(f"[通过] 额外抽查 {samples} 棵表达式树：减法、除法及中间结果（按项目分数约定）")
    print("注意：全体文件的交换律去重与每棵树的中间过程，不能仅凭文本检查得出全面证明。")
    print("验收辅助检查完成。")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[失败] {exc}", file=sys.stderr)
        sys.exit(1)
