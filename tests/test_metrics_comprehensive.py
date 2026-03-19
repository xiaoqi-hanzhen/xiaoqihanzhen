"""
utils/metrics.py模块的全面单元测试
测试精确率、召回率、IoU、mAP等指标计算函数
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.metrics import (
    f1_score,
    calculate_precision,
    calculate_recall,
    calculate_iou,
    xywh_to_xyxy,
    xyxy_to_xywh,
    calculate_ap,
    calculate_map,
    calculate_confusion_matrix,
    non_max_suppression
)


class TestBasicMetrics:
    """基本指标计算测试"""

    def test_f1_score_basic(self):
        """测试F1分数计算"""
        assert f1_score(1.0, 1.0) == 1.0
        assert f1_score(0.5, 0.5) == 0.5
        assert f1_score(0.0, 0.0) == 0.0

    def test_f1_score_edge_cases(self):
        """测试F1分数边界情况"""
        # 精确率为0
        assert f1_score(0.0, 1.0) == 0.0
        # 召回率为0
        assert f1_score(1.0, 0.0) == 0.0
        # 精确率和召回率不同
        result = f1_score(0.8, 0.6)
        assert abs(result - 0.6857) < 0.001

    def test_calculate_precision(self):
        """测试精确率计算"""
        assert calculate_precision(80, 20) == 0.8
        assert calculate_precision(100, 0) == 1.0
        assert calculate_precision(0, 100) == 0.0
        assert calculate_precision(0, 0) == 0.0

    def test_calculate_recall(self):
        """测试召回率计算"""
        assert calculate_recall(80, 20) == 0.8
        assert calculate_recall(100, 0) == 1.0
        assert calculate_recall(0, 100) == 0.0
        assert calculate_recall(0, 0) == 0.0


class TestIoU:
    """IoU计算测试"""

    def test_iou_perfect_overlap(self):
        """测试完全重叠的边界框"""
        box1 = [0, 0, 10, 10]
        box2 = [0, 0, 10, 10]
        iou = calculate_iou(box1, box2, format='xyxy')
        assert abs(iou - 1.0) < 1e-6

    def test_iou_no_overlap(self):
        """测试无重叠的边界框"""
        box1 = [0, 0, 10, 10]
        box2 = [20, 20, 30, 30]
        iou = calculate_iou(box1, box2, format='xyxy')
        assert abs(iou - 0.0) < 1e-6

    def test_iou_partial_overlap(self):
        """测试部分重叠的边界框"""
        box1 = [0, 0, 10, 10]
        box2 = [5, 5, 15, 15]
        # 交集面积: 5*5 = 25
        # 并集面积: 100 + 100 - 25 = 175
        # IoU = 25/175 = 0.142857
        iou = calculate_iou(box1, box2, format='xyxy')
        assert abs(iou - 0.142857) < 0.001

    def test_iou_xywh_format(self):
        """测试xywh格式的IoU计算"""
        # xywh格式: [x_center, y_center, width, height]
        box1 = [5, 5, 10, 10]  # 对应xyxy: [0, 0, 10, 10]
        box2 = [5, 5, 10, 10]
        iou = calculate_iou(box1, box2, format='xywh')
        assert abs(iou - 1.0) < 1e-6

    def test_iou_one_inside_another(self):
        """测试一个框完全包含另一个框"""
        box1 = [0, 0, 20, 20]
        box2 = [5, 5, 15, 15]
        # 交集: 10*10 = 100
        # 并集: 400 + 100 - 100 = 400
        # IoU = 100/400 = 0.25
        iou = calculate_iou(box1, box2, format='xyxy')
        assert abs(iou - 0.25) < 1e-6


class TestBoxConversion:
    """边界框格式转换测试"""

    def test_xywh_to_xyxy(self):
        """测试xywh到xyxy转换"""
        box_xywh = [10, 10, 20, 20]
        box_xyxy = xywh_to_xyxy(box_xywh)
        assert box_xyxy == [0, 0, 20, 20]

    def test_xyxy_to_xywh(self):
        """测试xyxy到xywh转换"""
        box_xyxy = [0, 0, 20, 20]
        box_xywh = xyxy_to_xywh(box_xyxy)
        assert box_xywh == [10, 10, 20, 20]

    def test_conversion_round_trip(self):
        """测试往返转换"""
        original = [100, 100, 50, 50]
        converted = xywh_to_xyxy(original)
        back = xyxy_to_xywh(converted)
        assert all(abs(a - b) < 1e-6 for a, b in zip(original, back))


class TestAP:
    """平均精度计算测试"""

    def test_ap_perfect_predictions(self):
        """测试完美预测的AP"""
        precisions = [1.0, 1.0, 1.0, 1.0, 1.0]
        recalls = [0.2, 0.4, 0.6, 0.8, 1.0]
        ap = calculate_ap(precisions, recalls, method='11point')
        assert abs(ap - 1.0) < 1e-6

    def test_ap_empty_input(self):
        """测试空输入"""
        assert calculate_ap([], [], method='11point') == 0.0

    def test_ap_11point_method(self):
        """测试11点插值法"""
        precisions = [1.0, 0.9, 0.8, 0.7, 0.6]
        recalls = [0.1, 0.3, 0.5, 0.7, 0.9]
        ap = calculate_ap(precisions, recalls, method='11point')
        assert 0.0 <= ap <= 1.0

    def test_ap_interp_method(self):
        """测试全插值法（COCO风格）"""
        precisions = [1.0, 0.9, 0.8, 0.7, 0.6]
        recalls = [0.1, 0.3, 0.5, 0.7, 0.9]
        ap = calculate_ap(precisions, recalls, method='interp')
        assert 0.0 <= ap <= 1.0

    def test_ap_invalid_method(self):
        """测试无效的方法参数"""
        precisions = [1.0, 0.9]
        recalls = [0.5, 0.8]
        with pytest.raises(ValueError):
            calculate_ap(precisions, recalls, method='invalid')


class TestMAP:
    """mAP计算测试"""

    def test_map_single_class(self):
        """测试单类别mAP"""
        aps = {'kite': 0.85}
        map_value = calculate_map(aps)
        assert abs(map_value - 0.85) < 1e-6

    def test_map_multiple_classes(self):
        """测试多类别mAP"""
        aps = {
            'kite': 0.85,
            'plastic_film': 0.90,
            'color_cloth': 0.80,
            'balloon': 0.75,
            'bird_nest': 0.88,
            'foreign_object': 0.82
        }
        map_value = calculate_map(aps)
        expected = sum(aps.values()) / len(aps)
        assert abs(map_value - expected) < 1e-6

    def test_map_empty_dict(self):
        """测试空字典"""
        assert calculate_map({}) == 0.0


class TestConfusionMatrix:
    """混淆矩阵测试"""

    def test_confusion_matrix_basic(self):
        """测试基本混淆矩阵"""
        predictions = [0, 1, 2, 0, 1, 2]
        ground_truths = [0, 1, 2, 0, 1, 2]
        num_classes = 3

        cm = calculate_confusion_matrix(predictions, ground_truths, num_classes)

        # 完美预测，应该是对角矩阵
        expected = np.array([
            [2, 0, 0],
            [0, 2, 0],
            [0, 0, 2]
        ])
        assert np.array_equal(cm, expected)

    def test_confusion_matrix_with_errors(self):
        """测试有错误的混淆矩阵"""
        predictions = [0, 1, 2, 1, 0, 2]
        ground_truths = [0, 1, 1, 2, 2, 2]
        num_classes = 3

        cm = calculate_confusion_matrix(predictions, ground_truths, num_classes)

        # 检查矩阵形状
        assert cm.shape == (num_classes, num_classes)

        # 检查总数
        assert cm.sum() == len(predictions)

    def test_confusion_matrix_boundary_check(self):
        """测试边界检查"""
        predictions = [0, 1, 5, -1]  # 包含超出范围的值
        ground_truths = [0, 1, 2, 2]
        num_classes = 3

        cm = calculate_confusion_matrix(predictions, ground_truths, num_classes)

        # 超出范围的值应该被忽略
        assert cm.sum() == 2  # 只有前两个有效


class TestNMS:
    """非极大值抑制测试"""

    def test_nms_no_overlap(self):
        """测试无重叠情况"""
        boxes = np.array([
            [0, 0, 10, 10],
            [20, 20, 30, 30],
            [40, 40, 50, 50]
        ])
        scores = np.array([0.9, 0.8, 0.7])

        keep = non_max_suppression(boxes, scores, iou_threshold=0.5)

        # 无重叠，全部保留
        assert len(keep) == 3

    def test_nms_complete_overlap(self):
        """测试完全重叠情况"""
        boxes = np.array([
            [0, 0, 10, 10],
            [0, 0, 10, 10],
            [0, 0, 10, 10]
        ])
        scores = np.array([0.9, 0.8, 0.7])

        keep = non_max_suppression(boxes, scores, iou_threshold=0.5)

        # 完全重叠，只保留分数最高的
        assert len(keep) == 1
        assert keep[0] == 0  # 应该保留第一个（分数最高）

    def test_nms_partial_overlap(self):
        """测试部分重叠情况"""
        boxes = np.array([
            [0, 0, 10, 10],
            [5, 5, 15, 15],
            [20, 20, 30, 30]
        ])
        scores = np.array([0.9, 0.8, 0.7])

        keep = non_max_suppression(boxes, scores, iou_threshold=0.2)

        # 前两个框重叠，第三个框独立
        # 应该保留第一个和第三个
        assert len(keep) == 2
        assert 0 in keep
        assert 2 in keep

    def test_nms_empty_input(self):
        """测试空输入"""
        boxes = np.array([])
        scores = np.array([])

        keep = non_max_suppression(boxes, scores, iou_threshold=0.5)

        assert len(keep) == 0

    def test_nms_single_box(self):
        """测试单个框"""
        boxes = np.array([[0, 0, 10, 10]])
        scores = np.array([0.9])

        keep = non_max_suppression(boxes, scores, iou_threshold=0.5)

        assert len(keep) == 1
        assert keep[0] == 0


class TestIntegration:
    """集成测试"""

    def test_detection_evaluation_workflow(self):
        """测试完整的检测评估工作流"""
        # 模拟检测结果
        tp = 85
        fp = 15
        fn = 20

        # 计算指标
        precision = calculate_precision(tp, fp)
        recall = calculate_recall(tp, fn)
        f1 = f1_score(precision, recall)

        # 验证指标范围
        assert 0.0 <= precision <= 1.0
        assert 0.0 <= recall <= 1.0
        assert 0.0 <= f1 <= 1.0

        # 验证关系
        assert f1 <= min(precision, recall)

    def test_multiclass_evaluation(self):
        """测试多类别评估"""
        # 6个类别的AP
        aps = {
            'kite': 0.85,
            'plastic_film': 0.90,
            'color_cloth': 0.80,
            'balloon': 0.75,
            'bird_nest': 0.88,
            'foreign_object': 0.82
        }

        # 计算mAP
        map_value = calculate_map(aps)

        # mAP应该在最小和最大AP之间
        assert min(aps.values()) <= map_value <= max(aps.values())

        # 验证计算正确性
        expected = sum(aps.values()) / len(aps)
        assert abs(map_value - expected) < 1e-6


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
