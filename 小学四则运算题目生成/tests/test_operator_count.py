"""运算符数量不变量与输出校验的回归测试。

背景：历史上 division 剪枝分支在交换左右子树时未同步交换各自的运算符预算
(left_ops/right_ops)，导致重新采样右子树时与已挪到左侧的子树重复计数，
偶发产生包含 4~5 个四则运算符的题目（例如
"3 ÷ (92 − 90’27/83) ÷ (12/13 + 92 − 18’13/17) = " 含 5 个运算符）。

本文件覆盖三层保护：
1. 表达式树结构不变量：generate_tree(num_ops).count_operators() == num_ops；
2. 文本级独立复核：validator.count_operators / validate_exercises；
3. 端到端：大批量生成后逐题统计运算符数量，并复核答案正确性与去重。

所有涉及随机的用例均显式设定随机种子，保证可复现。
"""

import random

import pytest

from exercises.evaluator import evaluate_expression
from exercises.fraction_utils import parse_fraction
from exercises.generator import generate_exercises, generate_tree
from exercises.validator import (
    count_operators,
    describe_violations,
    validate_exercises,
)

# 修复前会产出超过 3 个运算符题目的随机种子（generate_exercises(400, 100)）
REGRESSION_SEEDS = [0, 1, 18, 40, 52]

# 用户报告中实际出现的题目：2 个 ÷、2 个 −、1 个 +，共 5 个四则运算符
REPORTED_QUESTION = "3 ÷ (92 − 90’27/83) ÷ (12/13 + 92 − 18’13/17) = "


class TestCountOperatorsExcludesFractions:
    """文本级统计必须忽略分数中的 '/'。"""

    def test_reported_question_has_five_operators(self):
        assert count_operators(REPORTED_QUESTION) == 5

    def test_fraction_slash_is_not_an_operator(self):
        assert count_operators("1/6 + 1/8 = ") == 1
        assert count_operators("2’3/8 = ") == 0
        assert count_operators("2’3/8 − 1/4 = ") == 1
        assert count_operators("2’3/8 × 1/4 = ") == 1

    def test_operators_at_the_upper_bound(self):
        assert count_operators("1 + 2 + 3 + 4 = ") == 3
        assert count_operators("1 + 2 + 3 + 4 + 5 = ") == 4


class TestTreeOperatorInvariant:
    """generate_tree(num_ops) 返回的树，运算符节点数必须恰为 num_ops。"""

    def test_invariant_over_seeded_sweep(self):
        mismatches = []
        checked = 0
        for seed in range(60):
            random.seed(seed)
            for _ in range(200):
                num_ops = random.randint(1, 3)
                max_r = random.choice([2, 3, 10, 50, 100])
                tree = generate_tree(num_ops, max_r)
                if tree is None:
                    continue
                checked += 1
                actual = tree.count_operators()
                if actual != num_ops:
                    mismatches.append((seed, num_ops, actual, tree.to_infix()))
        assert checked > 5000, f"抽查样本过少：{checked}"
        assert not mismatches, f"运算符数量不变量被破坏（前 3 条）：{mismatches[:3]}"

    def test_infix_text_matches_tree_operator_count(self):
        """to_infix() 打印的文本与其表达式树的运算符数量必须一致。"""
        for seed in range(30):
            random.seed(seed)
            for _ in range(100):
                num_ops = random.randint(1, 3)
                tree = generate_tree(num_ops, 100)
                if tree is None:
                    continue
                assert count_operators(tree.to_infix()) == tree.count_operators()


class TestGenerationRespectsOperatorLimit:
    """端到端：批量生成结果中每道题的运算符个数均为 1~3。"""

    @pytest.mark.parametrize("seed", REGRESSION_SEEDS)
    def test_regression_seeds(self, seed):
        """这些种子在修复前会生成超过 3 个运算符的题目。"""
        random.seed(seed)
        exercises, answers = generate_exercises(400, 100)
        assert len(exercises) == len(answers) == 400
        for index, expression in enumerate(exercises, 1):
            n_ops = count_operators(expression)
            assert 1 <= n_ops <= 3, f"第 {index} 题运算符数量为 {n_ops}: {expression}"

    @pytest.mark.parametrize("seed", [7, 11, 23, 42])
    def test_multi_seed_large_batch(self, seed):
        """多轮中等规模生成，逐题校验运算符数量、答案正确性与文本唯一性。"""
        random.seed(seed)
        exercises, answers = generate_exercises(2000, 100)
        assert len(exercises) == len(answers) == 2000
        assert len(set(exercises)) == 2000, "题目文本存在重复"

        for index, (expression, answer) in enumerate(zip(exercises, answers), 1):
            n_ops = count_operators(expression)
            assert 1 <= n_ops <= 3, f"第 {index} 题运算符数量为 {n_ops}: {expression}"
            assert expression.endswith("= "), f"第 {index} 题格式错误: {expression!r}"
            expected = evaluate_expression(expression)
            assert expected == parse_fraction(answer), (
                f"第 {index} 题答案错误: {expression} / {answer}"
            )

    def test_full_scale_10000(self):
        """保持一万道题目的生成能力，且全部满足运算符数量约束。"""
        random.seed(20260922)
        exercises, answers = generate_exercises(10000, 100)
        assert len(exercises) == len(answers) == 10000
        assert all(1 <= count_operators(e) <= 3 for e in exercises)
        assert not validate_exercises(exercises, answers)


class TestValidatorIsAnIndependentGuard:
    """写出前的独立复核必须能发现问题并给出具体题号与原因。"""

    def test_accepts_valid_output(self):
        random.seed(3)
        exercises, answers = generate_exercises(200, 50)
        assert validate_exercises(exercises, answers) == []

    def test_detects_operator_overflow(self):
        exercises = ["1 + 2 = ", REPORTED_QUESTION, "1/2 + 1/3 = "]
        answers = ["3", "1", "5/6"]
        violations = validate_exercises(exercises, answers)
        assert len(violations) == 1
        violation = violations[0]
        assert violation.index == 2
        assert violation.expression == REPORTED_QUESTION
        assert "运算符数量为 5" in violation.reason

    def test_detects_missing_equals_sign(self):
        violations = validate_exercises(["1 + 2", "1/2 + 1/3 = "], ["3", "5/6"])
        assert [v.index for v in violations] == [1]
        assert "等号" in violations[0].reason

    def test_detects_length_mismatch(self):
        violations = validate_exercises(["1 + 2 = "], ["3", "4"])
        assert violations and "数量不一致" in violations[0].reason

    def test_describe_violations_reports_specific_question(self):
        violations = validate_exercises([REPORTED_QUESTION], ["1"])
        text = describe_violations(violations)
        assert "第 1 题" in text
        assert "运算符数量为 5" in text
        assert REPORTED_QUESTION in text
