# YOLO 无人机异物检测

面向风筝、塑料薄膜、彩条布、气球、鸟巢等异物的航拍检测项目。基于 YOLOv8，可在 RTX 3070 Ti 8GB 的笔记本上训练与推理。

## 环境
```bash
# Conda
conda env create -f environment/environment.yml
conda activate yolo-drone
# 或 pip
pip install -r environment/requirements.txt
```
验证 GPU 与 CUDA：
```bash
python environment/setup_cuda.py
```

## 数据放置
- 原始图像：`data/raw/`
- 标注：`data/annotations/`
- 预处理输出：`data/processed/`
- 增强输出：`data/augmented/`
- 划分：`data/splits/{train,val,test}/`
- 在 `data/data_manifest.csv` 中记录 `image_path,label,source,split,is_clean`.

## 快速训练
```bash
python scripts/prepare_data.py      # 清洗+划分，可选
python scripts/train_yolov8.py      # 读取 models/configs/yolov8_drone_config.yaml
```
训练产物保存在 `training/runs/<date_experiment>/`。评估报告输出到 `evaluation/outputs/`。

## 目录速览
见 `project_structure.md`；流程细节见 `docs/pipeline.md`。
