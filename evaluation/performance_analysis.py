"""
对评估结果进行统计（PR 曲线、尺寸分布）。
"""
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np


def plot_pr(curves_path: str, save_path: str):
    data = json.loads(Path(curves_path).read_text())
    precision = np.array(data["precision"])
    recall = np.array(data["recall"])
    plt.figure()
    plt.plot(recall, precision)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.grid(True)
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=200)
    plt.close()

