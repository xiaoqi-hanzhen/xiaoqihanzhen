"""
可视化工具：绘制样本、预测框、增强结果。
"""
import cv2
from pathlib import Path
import random


def draw_boxes(image_path: str, boxes, class_names, save_path: str = None, color=None, thickness: int = 2):
    img = cv2.imread(image_path)
    for cls_id, xyxy in boxes:
        c = color or (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        x1, y1, x2, y2 = map(int, xyxy)
        cv2.rectangle(img, (x1, y1), (x2, y2), c, thickness)
        cv2.putText(img, class_names[cls_id], (x1, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 1)
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(save_path, img)
    return img
