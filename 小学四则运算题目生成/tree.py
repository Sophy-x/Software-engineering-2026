"""表达式二叉树模块 (tree.py)

构建表达式树 (Expression Tree)，实现：
- 严格最小括号化中缀表达式生成
- 交换律规范化哈希/元组签名生成（用于题目去重）
"""

from fractions import Fraction
from typing import Optional, Union
from fraction_utils import format_fraction

# 运算符优先级字典
OPERATOR_PRECEDENCE = {
    "+": 1,
    "−": 1,
    "×": 2,
    "÷": 2,
}


class TreeNode:
    """表达式语法树节点。

    叶子节点：
        op 为 None，value 为 Fraction 对象，left 和 right 为 None。
    操作符节点：
        op 为 '+', '−', '×', '÷' 之一，value 为子树计算出的 Fraction 对象，
        left 和 right 为 TreeNode 节点。
    """

    def __init__(
        self,
        op: Optional[str] = None,
        value: Optional[Fraction] = None,
        left: Optional["TreeNode"] = None,
        right: Optional["TreeNode"] = None,
    ):
        self.op = op
        self.value = value
        self.left = left
        self.right = right

    def is_leaf(self) -> bool:
        """是否为叶子节点。"""
        return self.op is None

    def to_infix(self, parent_op: Optional[str] = None, is_right: bool = False) -> str:
        """生成严格最小括号化的中缀表达式。

        规则：
        1. 叶子节点：直接调用 format_fraction(value)。
        2. 当前节点优先级 < 父节点优先级：必须加括号（如父是 ×，当前是 +）。
        3. 当前节点优先级 == 父节点优先级：
           - 处于右子树且父节点为非结合/左结合运算符（− 或 ÷）：必须加括号。
             例如：a - (b - c) 不能去掉括号，因为 a - b + c != a - (b - c)
                   a / (b / c) 不能去掉括号，因为 a / b * c != a / (b / c)
                   a - (b + c) 必须加括号：a - (b + c) != a - b + c
                   a / (b * c) 必须加括号：a / (b * c) != a / b * c
           - 处于左子树或运算符完全结合（+ 或 ×）：无需加括号。
        4. 当前节点优先级 > 父节点优先级：无需加括号。

        Returns:
            符合运算优先级、不含多余括号的中缀表达式字符串。
        """
        if self.is_leaf():
            return format_fraction(self.value)

        current_prec = OPERATOR_PRECEDENCE[self.op]

        # 递归构造左右子树字符串
        left_str = self.left.to_infix(parent_op=self.op, is_right=False)
        right_str = self.right.to_infix(parent_op=self.op, is_right=True)

        expr = f"{left_str} {self.op} {right_str}"

        need_parens = False
        if parent_op is not None:
            parent_prec = OPERATOR_PRECEDENCE[parent_op]
            if current_prec < parent_prec:
                need_parens = True
            elif current_prec == parent_prec:
                if is_right and parent_op in ("−", "÷"):
                    need_parens = True

        return f"({expr})" if need_parens else expr

    def canonical_repr(self) -> tuple:
        """生成符合交换律等价归一化的元组结构（用于判重）。

        若当前算符属于可交换操作符（'+' 或 '×'）：
        通过比较左右子树规范化元组的字典序（或递归比较），固定左小右大次序；
        若属于非交换算符（'−' 或 '÷'）：保持原始顺序；
        叶子节点返回元组 ('val', value.numerator, value.denominator)。
        """
        if self.is_leaf():
            return ("val", self.value.numerator, self.value.denominator)

        left_repr = self.left.canonical_repr()
        right_repr = self.right.canonical_repr()

        if self.op in ("+", "×"):
            # 可交换算符：将较小的子树元组放在左边
            if left_repr > right_repr:
                left_repr, right_repr = right_repr, left_repr

        return (self.op, left_repr, right_repr)

    def __str__(self) -> str:
        return self.to_infix()

    def __repr__(self) -> str:
        if self.is_leaf():
            return f"Leaf({format_fraction(self.value)})"
        return f"Node({self.op}, {repr(self.left)}, {repr(self.right)})"
