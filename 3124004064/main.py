# -*- coding: utf-8 -*-
"""
main.py - 命令行运行入口
用法: python main.py [原文文件绝对路径] [抄袭版文件绝对路径] [答案文件绝对路径]
"""
import os
import sys
from similarity import calculate_similarity

SUPPORTED_ENCODINGS = ("utf-8", "gbk", "gb18030", "utf-8-sig")


def read_file(file_path: str) -> str:
    """
    读取指定路径文本，具备多编码自适应降级尝试机制
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到指定文件: {file_path}")
    if not os.path.isfile(file_path):
        raise IsADirectoryError(f"目标路径是目录而非文件: {file_path}")

    for enc in SUPPORTED_ENCODINGS:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue

    raise ValueError(f"无法使用常见中文编码(UTF-8/GBK)解码文件: {file_path}")


def write_answer(ans_path: str, similarity: float) -> None:
    """
    将计算结果按规范输出至目标文件（保留两位小数）
    """
    parent_dir = os.path.dirname(os.path.abspath(ans_path))
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    formatted_ans = f"{similarity:.2f}"
    with open(ans_path, "w", encoding="utf-8") as f:
        f.write(formatted_ans)


def run_pipeline(orig_path: str, plagiarized_path: str, ans_path: str) -> float:
    """
    调度全流程并写入结果
    """
    orig_content = read_file(orig_path)
    plagiarized_content = read_file(plagiarized_path)
    similarity = calculate_similarity(orig_content, plagiarized_content)
    write_answer(ans_path, similarity)
    return similarity


def main():
    # 严格校验命令行参数数量
    if len(sys.argv) != 4:
        print("【参数错误】参数数量不符合规范！")
        print("标准格式: python main.py [原文绝对路径] [抄袭版绝对路径] [答案输出绝对路径]")
        sys.exit(1)

    orig_path = sys.argv[1]
    copy_path = sys.argv[2]
    ans_path = sys.argv[3]

    try:
        sim = run_pipeline(orig_path, copy_path, ans_path)
        print(f"查重已完成！重复率: {sim:.2f}，结果已保存至: {ans_path}")
    except FileNotFoundError as e:
        print(f"【文件不存在异常】: {e}", file=sys.stderr)
        sys.exit(2)
    except ValueError as e:
        print(f"【解码/内容异常】: {e}", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"【运行时未知错误】: {e}", file=sys.stderr)
        sys.exit(4)


if __name__ == "__main__":
    main()