"""主程序入口模块 (main.py)

提供命令行接口 (CLI)，支持两种工作模式：
1. 题目生成模式: python main.py -n <数量> -r <范围>
2. 批改验证模式: python main.py -e <题目文件> -a <答案文件>
"""

import argparse
import sys
from typing import List
from generator import generate_exercises


def save_lines(file_path: str, lines: List[str]) -> None:
    """将文本行写入指定文件，自动添加序号编号并采用 UTF-8 编码。"""
    with open(file_path, "w", encoding="utf-8") as f:
        for idx, line in enumerate(lines, 1):
            f.write(f"{idx}. {line}\n")


def run_generate_mode(n: int, r: int) -> None:
    """运行题目生成模式，生成题目与答案并写入 Exercises.txt 和 Answers.txt。"""
    if n <= 0:
        print("错误: 生成题目数量 -n 必须大于 0", file=sys.stderr)
        sys.exit(1)
    if r <= 0:
        print("错误: 操作数范围约束 -r 必须大于 0", file=sys.stderr)
        sys.exit(1)

    print(f"正在生成 {n} 道四则运算题目 (操作数范围: {r})...")
    try:
        exercises, answers = generate_exercises(n, r)
        save_lines("Exercises.txt", exercises)
        save_lines("Answers.txt", answers)
        print("题目生成完成！")
        print("- 题目文件: Exercises.txt")
        print("- 答案文件: Answers.txt")
    except Exception as e:
        print(f"生成失败: {e}", file=sys.stderr)
        sys.exit(1)


def run_grade_mode(exercise_path: str, answer_path: str) -> None:
    """运行作业批改模式，比对学生答案并输出统计至 Grade.txt。"""
    try:
        from evaluator import grade_exercises
    except ImportError:
        print("错误: 找不到 evaluator.py 模块，无法执行批改功能。", file=sys.stderr)
        sys.exit(1)

    try:
        grade_exercises(exercise_path, answer_path, "Grade.txt")
        print("批改完成！统计结果已输出至 Grade.txt")
    except Exception as e:
        print(f"批改失败: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="小学四则运算题目自动生成与批改系统",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("-n", type=int, help="生成题目的数量 (例如: -n 10000)")
    parser.add_argument("-r", type=int, help="题目中数值的取值范围/上限 (例如: -r 10)")
    parser.add_argument("-e", type=str, help="待评测的题目文件路径 (例如: -e <exercisefile>.txt)")
    parser.add_argument("-a", type=str, help="学生或待比对的答案文件路径 (例如: -a <answerfile>.txt)")

    args = parser.parse_args()

    # 模式判定
    has_gen = args.n is not None or args.r is not None
    has_eval = args.e is not None or args.a is not None

    if has_gen and has_eval:
        print("错误: 不能同时指定生成参数 (-n, -r) 和评测参数 (-e, -a)", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    if has_gen:
        if args.n is None or args.r is None:
            print("错误: 题目生成模式必须同时指定 -n 和 -r 参数", file=sys.stderr)
            parser.print_help()
            sys.exit(1)
        run_generate_mode(args.n, args.r)
    elif has_eval:
        if args.e is None or args.a is None:
            print("错误: 作业批改模式必须同时指定 -e 和 -a 参数", file=sys.stderr)
            parser.print_help()
            sys.exit(1)
        run_grade_mode(args.e, args.a)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
