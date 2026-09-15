# -*- coding: utf-8 -*-
"""
similarity.py - 论文查重核心算法模块
包含文本预处理、中文分词、词频向量提取及余弦相似度计算
"""
import math
import re
from collections import Counter
from typing import List, Tuple
import jieba


class TextPreprocessor:
    """文本清洗与预处理类"""

    @staticmethod
    def clean_text(text: str) -> str:
        """
        去除标点符号、特殊空白字符，仅保留中文、英文字母及数字
        """
        if not text:
            return ""
        # 匹配中文字符、英文字母、数字
        pattern = re.compile(r"[\u4e00-\u9fa5a-zA-Z0-9]+")
        matched = pattern.findall(text)
        return "".join(matched)


class TextTokenizer:
    """分词处理类，封装 Jieba 分词器"""

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        对已清洗的文本进行中文精确分词
        """
        if not text:
            return []
        # 使用 jieba.lcut 进行精确切分
        return jieba.lcut(text)


class SimilarityCalculator:
    """相似度计算核心类"""

    @staticmethod
    def compute_cosine_similarity(words1: List[str], words2: List[str]) -> float:
        """
        基于词频向量计算两个词序列的余弦相似度
        :param words1: 原文词列表
        :param words2: 抄袭版词列表
        :return: 相似度浮点数（范围 0.0 ~ 1.0）
        """
        if not words1 and not words2:
            return 1.0  # 两篇均为空文本，视为完全一致
        if not words1 or not words2:
            return 0.0  # 其中一篇为空，相似度为 0

        counter1 = Counter(words1)
        counter2 = Counter(words2)

        # 仅遍历词汇交集，大幅优化稀疏向量点积计算速度 (O(min(|V1|, |V2|)))
        intersection = set(counter1.keys()) & set(counter2.keys())
        dot_product = sum(counter1[token] * counter2[token] for token in intersection)

        # 分别计算两个向量的模长 (Norm)
        norm1 = math.sqrt(sum(count**2 for count in counter1.values()))
        norm2 = math.sqrt(sum(count**2 for count in counter2.values()))

        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        # 浮点精度截断，限制在 [0.0, 1.0] 范围内
        return max(0.0, min(1.0, similarity))


def calculate_similarity(raw_text1: str, raw_text2: str) -> float:
    """
    顶层接口：串联清洗、分词、计算相似度全流程
    """
    # 快速短路：若文本字面完全相同，直接返回 1.0
    if raw_text1 == raw_text2:
        return 1.0

    clean_text1 = TextPreprocessor.clean_text(raw_text1)
    clean_text2 = TextPreprocessor.clean_text(raw_text2)

    # 清洗后若文本相同（例如仅标点不同且字完全一致）
    if clean_text1 == clean_text2:
        return 1.0 if clean_text1 else 0.0

    tokens1 = TextTokenizer.tokenize(clean_text1)
    tokens2 = TextTokenizer.tokenize(clean_text2)

    return SimilarityCalculator.compute_cosine_similarity(tokens1, tokens2)