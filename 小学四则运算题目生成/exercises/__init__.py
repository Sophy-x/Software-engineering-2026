"""小学四则运算题目自动生成与评测核心包 (exercises)。

提供核心模块与函数：
- 分数处理工具 (fraction_utils): format_fraction, parse_fraction, is_true_fraction
- 表达式语法树 (tree): TreeNode, OPERATOR_PRECEDENCE
- 题目生成器 (generator): generate_exercises, generate_tree, random_leaf
- 评测与批改 (evaluator): evaluate_expression, grade_exercises, tokenize
- 输出校验 (validator): count_operators, validate_exercises, describe_violations
"""

from .fraction_utils import (
    format_fraction,
    parse_fraction,
    is_true_fraction,
    fraction_to_str,
    str_to_fraction,
)
from .tree import (
    TreeNode,
    OPERATOR_PRECEDENCE,
)
from .generator import (
    generate_exercises,
    generate_tree,
    random_leaf,
)
from .evaluator import (
    tokenize,
    evaluate_expression,
    grade_exercises,
)
from .validator import (
    count_operators,
    validate_exercises,
    describe_violations,
)

__all__ = [
    "format_fraction",
    "parse_fraction",
    "is_true_fraction",
    "fraction_to_str",
    "str_to_fraction",
    "TreeNode",
    "OPERATOR_PRECEDENCE",
    "generate_exercises",
    "generate_tree",
    "random_leaf",
    "tokenize",
    "evaluate_expression",
    "grade_exercises",
    "count_operators",
    "validate_exercises",
    "describe_violations",
]
