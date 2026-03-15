"""
基于验证输出的 labels/preds 生成混淆矩阵。
"""
from ultralytics.utils.plotting import plot_confusion_matrix
import numpy as np


def build_confusion_matrix(matrix: np.ndarray, class_names, save_path: str):
    plot_confusion_matrix(matrix, names=class_names, save_dir=save_path)

