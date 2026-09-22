"""主程序入口模块 (main.py)

提供命令行接口 (CLI)，支持两种工作模式：
1. 题目生成模式: python main.py -r <数值范围> [-n <题目数量>]
   - -r 为必须指定的参数
   - -n 为可选参数，默认生成 10 道题目
   - 生成题目文件 Exercises.txt 与答案文件 Answers.txt
2. 批改验证模式: python main.py -e <题目文件> -a <答案文件>
   - 评测给定题目与答案，结果写入 Grade.txt
"""

import argparse
import sys
from typing import List
from exercises.generator import generate_exercises
from exercises.evaluator import grade_exercises
from exercises.validator import validate_exercises, describe_violations


def save_lines(file_path: str, lines: List[str]) -> None:
    """将文本行写入指定文件，自动添加序号编号并采用 UTF-8 编码。"""
    with open(file_path, "w", encoding="utf-8") as f:
        for idx, line in enumerate(lines, 1):
            f.write(f"{idx}. {line}\n")


def run_generate_mode(n: int, r: int) -> None:
    """运行题目生成模式。"""
    if n <= 0:
        print("错误: 生成题目数量 -n 必须大于 0", file=sys.stderr)
        sys.exit(1)
    if r <= 0:
        print("错误: 数值范围上限 -r 必须为大于 0 的自然数", file=sys.stderr)
        sys.exit(1)

    print(f"正在生成 {n} 道四则运算题目 (数值范围: [0, {r}))...")
    try:
        exercises, answers = generate_exercises(n, r)

        # 写出前的独立复核：逐题按文本统计四则运算符个数（分数中的 '/' 不计入），
        # 一旦发现不合格题目立即报告具体题号与原因，并终止写入，绝不静默落盘。
        violations = validate_exercises(exercises, answers)
        if violations:
            print("生成结果校验未通过，已中止写入文件：", file=sys.stderr)
            print(describe_violations(violations), file=sys.stderr)
            sys.exit(1)

        save_lines("Exercises.txt", exercises)
        save_lines("Answers.txt", answers)
        print("生成完毕！")
        print(f"  - 题目文件已生成: Exercises.txt ({n} 题)")
        print(f"  - 答案文件已生成: Answers.txt ({n} 题)")
    except Exception as e:
        print(f"生成失败: {e}", file=sys.stderr)
        sys.exit(1)


def run_grade_mode(exercise_path: str, answer_path: str) -> None:
    """运行答案批改模式。"""
    print(f"正在批改作业: 题目={exercise_path}, 答案={answer_path}...")
    try:
        correct_ids, wrong_ids = grade_exercises(exercise_path, answer_path, "Grade.txt")
        print("批改完成！统计结果已输出至 Grade.txt")
        print(f"  - 正确: {len(correct_ids)} 题")
        print(f"  - 错误: {len(wrong_ids)} 题")
    except Exception as e:
        print(f"批改失败: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="小学四则运算题目自动生成与评测系统",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("-n", type=int, default=None, help="生成题目的数量（可选，默认为 10）")
    parser.add_argument("-r", type=int, default=None, help="题目中数值与分母的上限范围 [0, r)（生成模式必填）")
    parser.add_argument("-e", type=str, default=None, help="待评测的题目文件路径 (例如: Exercises.txt)")
    parser.add_argument("-a", type=str, default=None, help="待评测的答案文件路径 (例如: Answers.txt)")

    args = parser.parse_args()

    has_gen = args.r is not None or args.n is not None
    has_grade = args.e is not None or args.a is not None

    # 1. 互斥检查
    if has_gen and has_grade:
        print("错误: 题目生成模式 (-r, -n) 与批改模式 (-e, -a) 互斥，不能同时使用！\n", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # 2. 批改模式
    if has_grade:
        if args.e is None or args.a is None:
            print("错误: 作业批改模式必须同时指定 -e 和 -a 参数", file=sys.stderr)
            parser.print_help()
            sys.exit(1)
        run_grade_mode(args.e, args.a)
        return

    # 3. 生成模式
    if args.r is not None:
        n = args.n if args.n is not None else 10
        run_generate_mode(n, args.r)
        return

    # 4. 未指定 -r 或任何有效模式时，报错并打印帮助信息
    print("错误: 必须使用 -r 参数指定数值范围以生成题目，或使用 -e/-a 进行批改！\n", file=sys.stderr)
    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
