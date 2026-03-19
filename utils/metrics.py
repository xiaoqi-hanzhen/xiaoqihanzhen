"""
目标检测评估指标计算模块
包含精确率、召回率、IoU、mAP等常用指标的计算函数
"""
import numpy as np
from typing import List, Tuple, Dict, Optional


def f1_score(precision: float, recall: float) -> float:
    """
    计算F1分数

    Args:
        precision: 精确率
        recall: 召回率

    Returns:
        F1分数
    """
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def calculate_precision(tp: int, fp: int) -> float:
    """
    计算精确率 (Precision)

    精确率 = TP / (TP + FP)
    衡量预测为正例的样本中真正例的比例

    Args:
        tp: 真正例数量 (True Positives)
        fp: 假正例数量 (False Positives)

    Returns:
        精确率，范围[0, 1]
    """
    if tp + fp == 0:
        return 0.0
    return tp / (tp + fp)


def calculate_recall(tp: int, fn: int) -> float:
    """
    计算召回率 (Recall / Sensitivity)

    召回率 = TP / (TP + FN)
    衡量所有正例中被正确预测的比例

    Args:
        tp: 真正例数量 (True Positives)
        fn: 假负例数量 (False Negatives)

    Returns:
        召回率，范围[0, 1]
    """
    if tp + fn == 0:
        return 0.0
    return tp / (tp + fn)


def calculate_iou(box1: List[float], box2: List[float], format: str = 'xyxy') -> float:
    """
    计算两个边界框的IoU (Intersection over Union)

    Args:
        box1: 第一个边界框 [x1, y1, x2, y2] 或 [x_center, y_center, width, height]
        box2: 第二个边界框 [x1, y1, x2, y2] 或 [x_center, y_center, width, height]
        format: 边界框格式，'xyxy' 或 'xywh'

    Returns:
        IoU值，范围[0, 1]
    """
    # 转换为xyxy格式
    if format == 'xywh':
        box1 = xywh_to_xyxy(box1)
        box2 = xywh_to_xyxy(box2)

    # 计算交集区域的坐标
    x1_inter = max(box1[0], box2[0])
    y1_inter = max(box1[1], box2[1])
    x2_inter = min(box1[2], box2[2])
    y2_inter = min(box1[3], box2[3])

    # 计算交集面积
    if x2_inter < x1_inter or y2_inter < y1_inter:
        intersection = 0.0
    else:
        intersection = (x2_inter - x1_inter) * (y2_inter - y1_inter)

    # 计算各自的面积
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])

    # 计算并集面积
    union = area1 + area2 - intersection

    # 计算IoU
    if union == 0:
        return 0.0

    return intersection / union


def xywh_to_xyxy(box: List[float]) -> List[float]:
    """
    将边界框从xywh格式转换为xyxy格式

    Args:
        box: [x_center, y_center, width, height]

    Returns:
        [x1, y1, x2, y2]
    """
    x_center, y_center, width, height = box
    x1 = x_center - width / 2
    y1 = y_center - height / 2
    x2 = x_center + width / 2
    y2 = y_center + height / 2
    return [x1, y1, x2, y2]


def xyxy_to_xywh(box: List[float]) -> List[float]:
    """
    将边界框从xyxy格式转换为xywh格式

    Args:
        box: [x1, y1, x2, y2]

    Returns:
        [x_center, y_center, width, height]
    """
    x1, y1, x2, y2 = box
    x_center = (x1 + x2) / 2
    y_center = (y1 + y2) / 2
    width = x2 - x1
    height = y2 - y1
    return [x_center, y_center, width, height]


def calculate_ap(precisions: List[float], recalls: List[float], method: str = '11point') -> float:
    """
    计算平均精度 (Average Precision, AP)

    Args:
        precisions: 精确率列表
        recalls: 召回率列表
        method: 计算方法，'11point'(11点插值) 或 'interp'(全插值)

    Returns:
        AP值，范围[0, 1]
    """
    if len(precisions) == 0 or len(recalls) == 0:
        return 0.0

    # 确保按召回率排序
    sorted_indices = np.argsort(recalls)
    recalls = np.array(recalls)[sorted_indices]
    precisions = np.array(precisions)[sorted_indices]

    if method == '11point':
        # 11点插值法
        ap = 0.0
        for t in np.linspace(0, 1, 11):
            if np.sum(recalls >= t) == 0:
                p = 0
            else:
                p = np.max(precisions[recalls >= t])
            ap += p / 11
        return ap

    elif method == 'interp':
        # 全插值法（COCO风格）
        # 添加哨兵值
        recalls = np.concatenate(([0.0], recalls, [1.0]))
        precisions = np.concatenate(([0.0], precisions, [0.0]))

        # 确保精确率单调递减
        for i in range(len(precisions) - 2, -1, -1):
            precisions[i] = max(precisions[i], precisions[i + 1])

        # 计算面积
        indices = np.where(recalls[1:] != recalls[:-1])[0] + 1
        ap = np.sum((recalls[indices] - recalls[indices - 1]) * precisions[indices])

        return ap

    else:
        raise ValueError(f"不支持的方法: {method}，请使用 '11point' 或 'interp'")


def calculate_map(aps: Dict[str, float]) -> float:
    """
    计算平均精度均值 (mean Average Precision, mAP)

    Args:
        aps: 字典，键为类别名称，值为对应的AP

    Returns:
        mAP值，范围[0, 1]
    """
    if len(aps) == 0:
        return 0.0

    return sum(aps.values()) / len(aps)


def calculate_confusion_matrix(predictions: List[int], ground_truths: List[int],
                               num_classes: int) -> np.ndarray:
    """
    计算混淆矩阵

    Args:
        predictions: 预测类别列表
        ground_truths: 真实类别列表
        num_classes: 类别总数

    Returns:
        混淆矩阵，形状为 (num_classes, num_classes)
        行表示真实类别，列表示预测类别
    """
    confusion = np.zeros((num_classes, num_classes), dtype=np.int32)

    for pred, gt in zip(predictions, ground_truths):
        if 0 <= gt < num_classes and 0 <= pred < num_classes:
            confusion[gt, pred] += 1

    return confusion


def non_max_suppression(boxes: np.ndarray, scores: np.ndarray,
                        iou_threshold: float = 0.5) -> List[int]:
    """
    非极大值抑制 (Non-Maximum Suppression, NMS)

    Args:
        boxes: 边界框数组，形状为 (N, 4)，格式为 [x1, y1, x2, y2]
        scores: 置信度分数数组，形状为 (N,)
        iou_threshold: IoU阈值，用于判断是否抑制

    Returns:
        保留的边界框索引列表
    """
    if len(boxes) == 0:
        return []

    # 按置信度降序排列
    order = scores.argsort()[::-1]
    keep = []

    while len(order) > 0:
        # 保留当前最高分数的框
        i = order[0]
        keep.append(i)

        if len(order) == 1:
            break

        # 计算当前框与其他框的IoU
        ious = np.array([calculate_iou(boxes[i].tolist(), boxes[j].tolist(), format='xyxy')
                        for j in order[1:]])

        # 保留IoU小于阈值的框
        indices = np.where(ious <= iou_threshold)[0]
        order = order[indices + 1]

    return keep
