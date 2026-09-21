"""分数工具模块 (fraction_utils.py)

负责处理自然数、真分数和带分数的精准数值计算与文本双向转换。
"""

from fractions import Fraction
import re


def format_fraction(f: Fraction) -> str:
    """格式化输出分数。

    - 若分母为 1：输出自然数格式 str(f.numerator)（如 '0'、'3'）。
    - 若分子小于分母：输出纯真分数格式 f"{f.numerator}/{f.denominator}"（如 '3/5'）。
    - 若分子大于分母：输出带分数格式 f"{q}’{r}/{f.denominator}"，
      其中 q = numerator // denominator 为整数部分，
      r = numerator % denominator 为真分数分子，
      连接符采用需求指定的 Unicode 右单引号 ’ (\\u2019)（如 '2’3/8'）。

    Args:
        f: Fraction 有理数对象

    Returns:
        格式化后的字符串
    """
    if f.denominator == 1:
        return str(f.numerator)

    is_negative = f < 0
    num = abs(f.numerator)
    den = f.denominator

    q = num // den
    r = num % den
    sign = "-" if is_negative else ""

    if q == 0:
        return f"{sign}{r}/{den}"
    if r == 0:
        return f"{sign}{q}"
    return f"{sign}{q}’{r}/{den}"


def parse_fraction(s: str) -> Fraction:
    """文本解析与容错。

    - 单引号兼容：同时兼容中文右单引号 ’ (\\u2019) 与英文 ASCII 单引号 ' (\\u0027)，解析前统一规范化。
    - 带分数解析：拆解整数部分 q 与分数部分 a/b，转换为标准分数 (q * b + a) / b。
    - 纯真分数解析：匹配到 '/' 时按纯分数转换为 a / b。
    - 自然数解析：纯数字文本直接转换为 s / 1。

    Args:
        s: 待解析的字符串文本

    Returns:
        解析出的标准 Fraction 对象

    Raises:
        ValueError: 文本格式不合法
        ZeroDivisionError: 分母为 0
    """
    s = s.strip()
    if not s:
        raise ValueError("输入字符串不能为空")

    # 规范化单引号：将中文右单引号 ’ (\u2019) 统一替换为标准单引号 '
    normalized = s.replace("\u2019", "'")

    is_negative = False
    if normalized.startswith("-"):
        is_negative = True
        normalized = normalized[1:].strip()

    # 1. 匹配带分数：形如 q'a/b
    if "'" in normalized:
        parts = normalized.split("'", 1)
        int_part = parts[0].strip()
        frac_part = parts[1].strip()
        if not int_part.isdigit() or "/" not in frac_part:
            raise ValueError(f"带分数格式错误: {s}")
        a_str, b_str = frac_part.split("/", 1)
        a_str, b_str = a_str.strip(), b_str.strip()
        if not a_str.isdigit() or not b_str.isdigit():
            raise ValueError(f"带分数格式错误: {s}")
        q = int(int_part)
        a = int(a_str)
        b = int(b_str)
        if b == 0:
            raise ZeroDivisionError("分母不能为 0")
        result = Fraction(q * b + a, b)
        return -result if is_negative else result

    # 2. 匹配纯真/假分数：形如 a/b
    if "/" in normalized:
        parts = normalized.split("/", 1)
        a_str, b_str = parts[0].strip(), parts[1].strip()
        if not a_str.isdigit() or not b_str.isdigit():
            raise ValueError(f"分数格式错误: {s}")
        a = int(a_str)
        b = int(b_str)
        if b == 0:
            raise ZeroDivisionError("分母不能为 0")
        result = Fraction(a, b)
        return -result if is_negative else result

    # 3. 匹配自然数/整数：纯数字
    if normalized.isdigit():
        val = int(normalized)
        result = Fraction(val, 1)
        return -result if is_negative else result

    raise ValueError(f"无法解析的分数格式: {s}")


def is_true_fraction(f: Fraction) -> bool:
    """判断是否为需求文档定义的“真分数”。

    真分数定义为：化简后分母严格大于 1 的正有理数 (denominator >= 2 且数值 > 0)。
    - 纯真分数（如 1/2, 3/5）判定为 True。
    - 带分数（如 1’1/2 = 3/2, 2’3/8 = 19/8）判定为 True。
    - 自然数/整数（分母为 1，如 0, 1, 2）判定为 False。
    - 负数或 0 判定为 False。
    """
    return f > 0 and f.denominator > 1


# 兼容性别名
fraction_to_str = format_fraction
str_to_fraction = parse_fraction
