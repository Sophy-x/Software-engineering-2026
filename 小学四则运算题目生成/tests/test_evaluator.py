"""测试评测批改模块。"""

import os
import tempfile
from fractions import Fraction
import pytest
from exercises.evaluator import tokenize, evaluate_expression, grade_exercises


def test_tokenize():
    tokens = tokenize("1 + 2 = ")
    assert tokens == ["1", "+", "2"]

    tokens_with_index = tokenize("1. 3’1/2 × (2 + 1/4) = ")
    assert tokens_with_index == ["3’1/2", "×", "(", "2", "+", "1/4", ")"]


def test_evaluate_expression():
    assert evaluate_expression("1 + 2") == Fraction(3)
    assert evaluate_expression("1 + 2 = ") == Fraction(3)
    assert evaluate_expression("1. 1 + 2 = ") == Fraction(3)
    assert evaluate_expression("3 + (2 + 1) = ") == Fraction(6)
    assert evaluate_expression("(1 + 2) × 3 = ") == Fraction(9)
    assert evaluate_expression("1 + 2 × 3 = ") == Fraction(7)
    assert evaluate_expression("1’1/2 + 3/4 = ") == Fraction(9, 4)
    assert evaluate_expression("1’1/2 ÷ 3/4 = ") == Fraction(2)
    assert evaluate_expression("1’1/2 − 3/4 = ") == Fraction(3, 4)


def test_grade_exercises():
    with tempfile.TemporaryDirectory() as tmpdir:
        ex_path = os.path.join(tmpdir, "Exercises.txt")
        ans_path = os.path.join(tmpdir, "Answers.txt")
        grade_path = os.path.join(tmpdir, "Grade.txt")

        with open(ex_path, "w", encoding="utf-8") as f:
            f.write("1. 1 + 2 = \n")
            f.write("2. 5 − 3 = \n")
            f.write("3. 2 × 4 = \n")

        with open(ans_path, "w", encoding="utf-8") as f:
            f.write("1. 3\n")
            f.write("2. 999\n")  # 故意写错
            f.write("3. 8\n")

        correct, wrong = grade_exercises(ex_path, ans_path, grade_path)
        assert correct == [1, 3]
        assert wrong == [2]

        with open(grade_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Correct: 2 (1, 3)" in content
        assert "Wrong: 1 (2)" in content
