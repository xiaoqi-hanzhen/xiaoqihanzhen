"""
基础指标计算封装。
"""
def f1_score(precision: float, recall: float):
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)
