"""测试题目生成器与表达式树模块。"""

from fractions import Fraction
import pytest
from exercises.fraction_utils import format_fraction, parse_fraction, is_true_fraction
from exercises.tree import TreeNode
from exercises.generator import generate_exercises, random_leaf


def test_fraction_formatting():
    assert format_fraction(Fraction(0, 1)) == "0"
    assert format_fraction(Fraction(4, 1)) == "4"
    assert format_fraction(Fraction(1, 3)) == "1/3"
    assert format_fraction(Fraction(3, 2)) == "1’1/2"
    assert format_fraction(Fraction(19, 8)) == "2’3/8"


def test_fraction_parsing():
    assert parse_fraction("0") == Fraction(0, 1)
    assert parse_fraction("4") == Fraction(4, 1)
    assert parse_fraction("1/3") == Fraction(1, 3)
    assert parse_fraction("1’1/2") == Fraction(3, 2)
    assert parse_fraction("1'1/2") == Fraction(3, 2)
    assert parse_fraction("2’3/8") == Fraction(19, 8)
    assert parse_fraction("2'3/8") == Fraction(19, 8)


def test_is_true_fraction():
    assert is_true_fraction(Fraction(1, 2)) is True
    assert is_true_fraction(Fraction(3, 2)) is True
    assert is_true_fraction(Fraction(19, 8)) is True
    assert is_true_fraction(Fraction(0, 1)) is False
    assert is_true_fraction(Fraction(1, 1)) is False
    assert is_true_fraction(Fraction(6, 2)) is False


def test_tree_infix_parentheses():
    n1 = TreeNode(val=Fraction(1))
    n2 = TreeNode(val=Fraction(2))
    n3 = TreeNode(val=Fraction(3))

    # 1 + 2 + 3 -> ((1+2)+3)
    p1 = TreeNode(op="+", val=Fraction(3), left=n1, right=n2)
    p2 = TreeNode(op="+", val=Fraction(6), left=p1, right=n3)
    assert p2.to_infix() == "1 + 2 + 3"

    # 3 + (2 + 1)
    p3 = TreeNode(op="+", val=Fraction(3), left=n2, right=n1)
    p4 = TreeNode(op="+", val=Fraction(6), left=n3, right=p3)
    assert p4.to_infix() == "3 + (2 + 1)"

    # (1 + 2) * 3
    mul1 = TreeNode(op="×", val=Fraction(9), left=p1, right=n3)
    assert mul1.to_infix() == "(1 + 2) × 3"

    # 1 + 2 * 3
    mul2 = TreeNode(op="×", val=Fraction(6), left=n2, right=n3)
    add1 = TreeNode(op="+", val=Fraction(7), left=n1, right=mul2)
    assert add1.to_infix() == "1 + 2 × 3"


def test_canonical_deduplication():
    n1 = TreeNode(val=Fraction(1))
    n2 = TreeNode(val=Fraction(2))
    n3 = TreeNode(val=Fraction(3))

    p1 = TreeNode(op="+", val=Fraction(3), left=n1, right=n2)
    p2 = TreeNode(op="+", val=Fraction(6), left=p1, right=n3)

    p3 = TreeNode(op="+", val=Fraction(3), left=n2, right=n1)
    p4 = TreeNode(op="+", val=Fraction(6), left=n3, right=p3)

    p5 = TreeNode(op="+", val=Fraction(5), left=n3, right=n2)
    p6 = TreeNode(op="+", val=Fraction(6), left=p5, right=n1)

    assert p2.canonical_repr() == p4.canonical_repr()
    assert p2.canonical_repr() != p6.canonical_repr()


def test_generate_exercises():
    exercises, answers = generate_exercises(20, 10)
    assert len(exercises) == 20
    assert len(answers) == 20
    for ex in exercises:
        assert ex.endswith("= ")
