# -*- coding: utf-8 -*-
"""
test_main.py - 全覆盖单元测试模块
覆盖普通场景、边界场景、编码异常场景、目录创建及 CLI 命令行入口测试
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import main, read_file, run_pipeline, write_answer
from similarity import (
    SimilarityCalculator,
    TextPreprocessor,
    TextTokenizer,
    calculate_similarity,
)


class TestPaperCheck(unittest.TestCase):
    """查重系统全方位单元测试集"""

    # ---------------- 1. 基础逻辑与文本特征测试 ----------------
    def test_01_identical_text(self):
        """测试 1: 原文与抄袭版完全一致"""
        text = "今天是星期天，天气晴，今天晚上我要去看电影。"
        self.assertAlmostEqual(calculate_similarity(text, text), 1.0, places=2)

    def test_02_completely_different(self):
        """测试 2: 文本完全无关"""
        t1 = "今天是星期天，天气晴朗，适合户外徒步。"
        t2 = "量子力学与微积分在半导体材料物理中的最新应用。"
        self.assertAlmostEqual(calculate_similarity(t1, t2), 0.0, places=2)

    def test_03_partial_modification(self):
        """测试 3: 样例增删改文本"""
        t1 = "今天是星期天，天气晴，今天晚上我要去看电影。"
        t2 = "今天是周天，天气晴朗，我晚上要去看电影。"
        sim = calculate_similarity(t1, t2)
        self.assertTrue(0.5 < sim < 1.0)

    def test_04_pure_punctuation(self):
        """测试 4: 仅包含空白与标点符号的清洗"""
        cleaned = TextPreprocessor.clean_text(" ，。！？……【】 、\n\t  ")
        self.assertEqual(cleaned, "")

    def test_05_empty_text_cases(self):
        """测试 5: 空白文本及纯标点比对，打通 similarity.py 边缘分支"""
        # 一侧为空
        self.assertEqual(calculate_similarity("正常句子", ""), 0.0)
        self.assertEqual(calculate_similarity("", "正常句子"), 0.0)
        # 两侧皆为空
        self.assertEqual(calculate_similarity("", ""), 1.0)
        # 两侧清洗后皆变为空字符串（纯标点）
        self.assertEqual(calculate_similarity("，，，", "！！！"), 0.0)
        # 计算模块直接传入空列表
        self.assertEqual(
            SimilarityCalculator.compute_cosine_similarity([], []), 1.0
        )
        self.assertEqual(
            SimilarityCalculator.compute_cosine_similarity(["词"], []), 0.0
        )

    def test_06_special_alphanumeric(self):
        """测试 6: 英文、数字及特殊符号（阈值兼容）"""
        t1 = "Python 3.10 发布于 2021 年，支持模式匹配特性。"
        t2 = "Python 3.10 发布，增加了模式匹配新语法特性。"
        sim = calculate_similarity(t1, t2)
        self.assertTrue(0.3 < sim <= 1.0)

    def test_07_tokenizer_basic(self):
        """测试 7: 分词器基本切分"""
        tokens = TextTokenizer.tokenize("软件工程课程设计")
        self.assertIn("软件工程", tokens)
        self.assertEqual(TextTokenizer.tokenize(""), [])

    # ---------------- 2. I/O 与异常探测测试 ----------------
    def test_08_write_answer_format_and_mkdir(self):
        """测试 8: 测试格式化两位小数，并测试父级目录不存在时自动创建目录(main.py line 38)"""
        temp_dir = tempfile.mkdtemp()
        nested_ans_path = os.path.join(
            temp_dir, "nested_folder", "output", "ans.txt"
        )
        try:
            write_answer(nested_ans_path, 0.8)
            with open(nested_ans_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            self.assertEqual(content, "0.80")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_09_file_not_found_exception(self):
        """测试 9: 文件不存在异常"""
        with self.assertRaises(FileNotFoundError):
            read_file("tests/definitely_not_exist_file.txt")

    def test_10_directory_path_exception(self):
        """测试 10: 传入文件夹路径作为文件打开"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with self.assertRaises(IsADirectoryError):
            read_file(current_dir)

    def test_11_undecodable_binary_file(self):
        """测试 11: 传入不可解码二进制文件，触发 main.py 第 26-29 行异常分支"""
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            # 写入非法字节序列
            f.write(b"\x81\x00\xff\xfe\xaa\xbb\xcc\xdd")
            bin_path = f.name
        try:
            with self.assertRaises(ValueError):
                read_file(bin_path)
        finally:
            if os.path.exists(bin_path):
                os.remove(bin_path)

    def test_12_pipeline_integration(self):
        """测试 12: 管道集成测试"""
        with tempfile.NamedTemporaryFile(
            "w", delete=False, encoding="utf-8"
        ) as f1, tempfile.NamedTemporaryFile(
            "w", delete=False, encoding="utf-8"
        ) as f2, tempfile.NamedTemporaryFile(
            "w", delete=False, encoding="utf-8"
        ) as f_ans:
            f1.write("广东工业大学计算机学院。")
            f2.write("广东工业大学计算机学院软件工程。")
            p1, p2, pa = f1.name, f2.name, f_ans.name

        try:
            sim = run_pipeline(p1, p2, pa)
            self.assertTrue(0.0 <= sim <= 1.0)
        finally:
            for p in (p1, p2, pa):
                if os.path.exists(p):
                    os.remove(p)

    # ---------------- 3. CLI 命令行入口测试（拉满 main.py 行 58-78） ----------------
    def test_13_cli_argument_count_error(self):
        """测试 13: 命令行参数少于 3 个，应退出并返回状态码 1"""
        old_argv = sys.argv
        try:
            sys.argv = ["main.py", "arg1"]
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 1)
        finally:
            sys.argv = old_argv

    def test_14_cli_success(self):
        """测试 14: 模拟完整的命令行执行成功流程"""
        with tempfile.NamedTemporaryFile(
            "w", delete=False, encoding="utf-8"
        ) as f1, tempfile.NamedTemporaryFile(
            "w", delete=False, encoding="utf-8"
        ) as f2, tempfile.NamedTemporaryFile(
            "w", delete=False, encoding="utf-8"
        ) as f_ans:
            f1.write("今天天气很好。")
            f2.write("今天天气确实很好。")
            p1, p2, pa = f1.name, f2.name, f_ans.name

        old_argv = sys.argv
        try:
            sys.argv = ["main.py", p1, p2, pa]
            main()
            with open(pa, "r", encoding="utf-8") as f:
                self.assertTrue(len(f.read().strip()) > 0)
        finally:
            sys.argv = old_argv
            for p in (p1, p2, pa):
                if os.path.exists(p):
                    os.remove(p)

    def test_15_cli_file_not_found(self):
        """测试 15: 模拟命令行传入不存在的文件，退出码应为 2"""
        old_argv = sys.argv
        try:
            sys.argv = [
                "main.py",
                "not_exist_file1.txt",
                "not_exist_file2.txt",
                "ans.txt",
            ]
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 2)
        finally:
            sys.argv = old_argv

    def test_16_cli_value_error(self):
        """测试 16: 模拟命令行传入损坏的二进制文件，退出码应为 3"""
        with tempfile.NamedTemporaryFile("wb", delete=False) as f_bin:
            f_bin.write(b"\x81\x00\xff\xfe\xaa\xbb")
            bin_path = f_bin.name

        with tempfile.NamedTemporaryFile(
            "w", delete=False, encoding="utf-8"
        ) as f_ok:
            f_ok.write("正常内容")
            ok_path = f_ok.name

        old_argv = sys.argv
        try:
            sys.argv = ["main.py", bin_path, ok_path, "ans.txt"]
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 3)
        finally:
            sys.argv = old_argv
            for p in (bin_path, ok_path):
                if os.path.exists(p):
                    os.remove(p)


if __name__ == "__main__":
    unittest.main()