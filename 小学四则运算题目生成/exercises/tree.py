"""表达式二叉树模块 (tree.py)

构建表达式二叉树 (Expression Tree)，实现：
1. 中缀表达式生成 (to_infix)：严格遵循运算优先级与结合律加括号，保证打印出的中缀表达式无歧义；
2. 同构去重签名 (canonical_repr)：基于可交换算符字典序排序的规范化表示（Canonical AST），实现 O(1) 题目去重。
"""

from fractions import Fraction
from typing import Optional
from .fraction_utils import format_fraction

# 运算符优先级字典
OPERATOR_PRECEDENCE = {
    "+": 1,
    "−": 1,
    "×": 2,
    "÷": 2,
}


class TreeNode:
    """二叉表达式树节点。

    属性：
    - op: 运算符 ('+', '−', '×', '÷')，叶子节点为 None
    - val: 节点（或以当前节点为根的子树）计算后的精准 Fraction 数值
    - left: 左子树 TreeNode
    - right: 右子树 TreeNode
    """

    def __init__(
        self,
        op: Optional[str] = None,
        val: Optional[Fraction] = None,
        left: Optional["TreeNode"] = None,
        right: Optional["TreeNode"] = None,
    ):
        self.op = op
        self.val = val
        self.left = left
        self.right = right

    @property
    def value(self) -> Optional[Fraction]:
        return self.val

    @value.setter
    def value(self, v: Optional[Fraction]):
        self.val = v

    def is_leaf(self) -> bool:
        """是否为叶子节点。"""
        return self.op is None

    def to_infix(self, parent_op: Optional[str] = None, is_right: bool = False) -> str:
        """递归生成中缀表达式字符串。

        加括号规则说明：
        1. 叶子节点：直接格式化为其数值字符串。
        2. 左子树加括号规则：
           - 当 left.op 的优先级严格低于当前节点优先级时加括号（如当前为 ×，左子为 +，得到 (a + b) × c）。
           - 若优先级相同，由于加减乘除皆为左结合，左子树不加括号（如 (a + b) + c 展现为 a + b + c）。
        3. 右子树加括号规则：
           - 当 right.op 的优先级严格低于当前节点优先级时，必须加括号（如 a × (b + c)）。
           - 当 right.op 的优先级等于当前节点优先级时：
             因四则运算在数学文本中严格默认左结合律，若右子树同级运算不加括号，
             例如 3 + (2 + 1) 若不加括号打印为 3 + 2 + 1，按左结合将被解释为 (3 + 2) + 1，
             从而改变了树原本的结构与意图。因此当右子树优先级 <= 当前节点时，
             右子树均必须加上括号以明确运算顺序（例如 3 + (2 + 1)、a − (b − c)、a ÷ (b ÷ c) 等）。
        4. 格式要求：运算符两端均保留单个空格分隔符。
        """
        if self.is_leaf():
            return format_fraction(self.val)

        current_prec = OPERATOR_PRECEDENCE[self.op]

        # 递归构造左右子树字符串
        left_str = self.left.to_infix(parent_op=self.op, is_right=False)
        right_str = self.right.to_infix(parent_op=self.op, is_right=True)

        expr = f"{left_str} {self.op} {right_str}"

        # 判断当前节点是否需要被外层父节点加括号包裹
        need_parens = False
        if parent_op is not None:
            parent_prec = OPERATOR_PRECEDENCE[parent_op]
            if is_right:
                # 右子树：优先级小于或等于父节点，均需加括号保证左结合语义不被破坏
                if current_prec <= parent_prec:
                    need_parens = True
            else:
                # 左子树：只有当优先级严格小于父节点时才需加括号
                if current_prec < parent_prec:
                    need_parens = True

        return f"({expr})" if need_parens else expr

    def canonical_repr(self) -> str:
        """生成基于可交换算符排序的规范化字符串（Canonical AST）。

        算法规则：
        1. 若为叶子节点：返回其最简分数的规范化字符串 f"{val.numerator}/{val.denominator}"。
        2. 若为不可交换操作符 ('−', '÷')：
           递归保持原顺序：f"({left.canonical_repr()}{op}{right.canonical_repr()})"
        3. 若为可交换操作符 ('+', '×')：
           分别获取左右子树的标准化字符串 S_left 和 S_right，
           强制按字典序较小者排在左侧，较大者排在右侧：
           f"({min(S_left, S_right)}{op}{max(S_left, S_right)})"

        示例验证：
        - 1 + 2 + 3 (即 ((1+2)+3)) 与 3 + (2 + 1)：
          规范化后均为 "(((1/1+2/1))+3/1)"，判定为重复。
        - 1 + 2 + 3 与 3 + 2 + 1 (即 ((3+2)+1))：
          规范化后分别为 "(((1/1+2/1))+3/1)" 与 "(((2/1+3/1))+1/1)"，判定为不重复。
        """
        if self.is_leaf():
            return f"{self.val.numerator}/{self.val.denominator}"

        left_repr = self.left.canonical_repr()
        right_repr = self.right.canonical_repr()

        if self.op in ("+", "×"):
            s1 = min(left_repr, right_repr)
            s2 = max(left_repr, right_repr)
            return f"({s1}{self.op}{s2})"
        else:
            return f"({left_repr}{self.op}{right_repr})"

    def __str__(self) -> str:
        return self.to_infix()

    def __repr__(self) -> str:
        if self.is_leaf():
            return f"Leaf({format_fraction(self.val)})"
        return f"Node({self.op}, {repr(self.left)}, {repr(self.right)})"
