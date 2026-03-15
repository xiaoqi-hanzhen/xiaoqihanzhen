# Baseline 实验记录模板

- 日期/实验名：
- 模型：YOLOv8n/s  | imgsz=640 | batch=8 | epochs=300
- 数据版本：raw v__ / split seed __
- 训练命令：
  ```
  python scripts/train_yolov8.py --config models/configs/yolov8_drone_config.yaml --data data/data.yaml --model-size n
  ```
- 指标（val/test）：
  - Precision:
  - Recall:
  - mAP50:
  - mAP50-95:
  - FPS (640):
  - Params / FLOPs:
- 观察：
  - 小目标漏检：
  - 复杂背景误检：
- 后续改进想法：
