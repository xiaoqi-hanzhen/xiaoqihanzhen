# YOLO 无人机异物检测

> 基于 YOLOv8 的无人机航拍异物检测系统，面向风筝、塑料薄膜、彩条布、气球、鸟巢等 6 类目标，针对 RTX 3070 Ti 8GB 显存优化，支持小目标检测、天气增强、多格式模型导出。

---

## 目录

- [环境安装](#环境安装)
- [快速开始](#快速开始)
- [项目结构与文件说明](#项目结构与文件说明)
  - [annotation/ — 标注格式转换](#annotation--标注格式转换)
  - [data/ — 数据目录](#data--数据目录)
  - [docs/ — 文档](#docs--文档)
  - [environment/ — 环境配置](#environment--环境配置)
  - [evaluation/ — 模型评估](#evaluation--模型评估)
  - [inference/ — 推理与导出](#inference--推理与导出)
  - [models/ — 模型配置](#models--模型配置)
  - [scripts/ — 便捷脚本](#scripts--便捷脚本)
  - [tests/ — 单元测试](#tests--单元测试)
  - [training/ — 训练核心](#training--训练核心)
  - [utils/ — 工具库](#utils--工具库)
- [完整工作流](#完整工作流)

---

## 环境安装

```bash
# 方式一：Conda（推荐）
conda env create -f environment/environment.yml
conda activate yolo-drone

# 方式二：pip
pip install -r environment/requirements.txt
```

验证 GPU 与 CUDA 是否就绪：

```bash
python environment/setup_cuda.py
```

---

## 快速开始

```bash
# 1. 数据清洗与划分
python scripts/prepare_data.py

# 2. 启动训练
python scripts/train_yolov8.py

# 3. 评估最新训练结果
python scripts/eval_latest.py

# 4. 单张图片检测
python inference/detect.py --source path/to/image.jpg --weights training/runs/best.pt
```

---

## 项目结构与文件说明

```
yolo-drone-foreign-object-detection/
├── annotation/          # 标注格式转换工具
├── data/                # 数据集目录
├── docs/                # 项目文档
├── environment/         # 环境配置与检查
├── evaluation/          # 模型评估与分析
├── inference/           # 推理脚本与模型导出
├── models/              # 模型配置文件
├── scripts/             # 便捷启动脚本
├── tests/               # 单元测试
├── training/            # 训练核心模块
└── utils/               # 通用工具库
```

---

### annotation/ — 标注格式转换

| 文件 | 说明 |
|------|------|
| `convert_formats.py` | 将 **VOC XML** 和 **COCO JSON** 标注格式批量转换为 YOLOv8 所需的 **YOLO TXT** 格式。支持命令行调用，内置类别合法性验证，是将各标注工具（LabelImg / AnyLabeling）输出对接训练流程的关键桥梁。主要函数：`convert_voc()`、`convert_coco()`。 |
| `anylabeling_config/` | AnyLabeling 标注工具的配置目录，存放自定义标签和快捷键配置。 |
| `labelimg_config/labelimg_config.ini` | LabelImg 标注工具的 INI 配置文件，记录默认标签列表、保存路径等偏好设置。 |

---

### data/ — 数据目录

该目录约定了整个数据流水线的分层存储结构，各子目录有明确分工：

| 路径 | 说明 |
|------|------|
| `data/raw/` | **原始图像**，从无人机、公开数据集或爬取获得，保持原样不做任何修改。 |
| `data/annotations/` | **原始标注文件**，支持 VOC XML、COCO JSON、YOLO TXT 等多种格式混放。 |
| `data/processed/` | **预处理后的图像**，经过质量检查、尺寸标准化、去重后的清洁数据。 |
| `data/augmented/` | **增强后的图像**，由 `utils/data_augmentation.py` 生成，包含天气模拟、Mosaic 等增强样本。 |
| `data/splits/` | **划分后的数据集**，含 `train/`、`val/`、`test/` 三个子目录，各含图像和 YOLO 格式标注。 |
| `data/data_manifest.csv` | **数据清单总表**，记录每张图片的路径、类别、来源、所属划分（train/val/test）和清洁状态（`is_clean`），便于追溯和管理。 |

---

### docs/ — 文档

| 文件 | 说明 |
|------|------|
| `pipeline.md` | **完整工作流文档**，按八个步骤详细描述从数据采集、标注、预处理、增强、训练、评估到模型导出部署的全流程，附硬件配置建议（RTX 3070 Ti 显存优化参数）和各步骤关键命令。 |
| `changelog.md` | **项目变更日志**，记录各版本的功能新增、重构、修复内容，方便团队协作时追溯历史改动。 |
| `experiment_template.md` | **实验记录模板**，提供标准化的实验复现格式，包含模型配置参数表、评估指标清单、实验观察和改进思路，供每次训练实验填写归档。 |

---

### environment/ — 环境配置

| 文件 | 说明 |
|------|------|
| `environment.yml` | **Conda 环境配置文件**，定义 Python 3.8 环境及全部依赖（PyTorch、Ultralytics YOLOv8、OpenCV 等）的版本约束，执行 `conda env create -f environment.yml` 一键创建可复现环境。 |
| `requirements.txt` | **pip 依赖清单**，列举所有 Python 包及最低版本要求，适用于不使用 Conda 的场景，执行 `pip install -r requirements.txt` 安装。 |
| `setup_cuda.py` | **CUDA 环境检查脚本**，自动检测 GPU 型号、CUDA 版本、可用显存，并针对 RTX 3070 Ti 等不同硬件给出最优 batch size、混合精度、Workers 数量等配置建议。 |

---

### evaluation/ — 模型评估

| 文件 | 说明 |
|------|------|
| `evaluate_model.py` | **评估主入口**，加载训练好的权重（`.pt` 文件）对测试集进行全面评估，计算 mAP@0.5、mAP@0.5:0.95、Precision、Recall 等核心指标，并将结果保存为 JSON 文件至 `outputs/` 目录。主要函数：`evaluate()`、`main()`。 |
| `confusion_matrix.py` | **混淆矩阵生成器**，基于验证集的预测结果构建并绘制各类别的混淆矩阵热力图，调用 Ultralytics 内置可视化接口，输出图片保存至 `outputs/`。主要函数：`build_confusion_matrix()`。 |
| `performance_analysis.py` | **深度性能分析**，读取评估结果，绘制精确率-召回率（PR）曲线、目标尺寸分布图等统计可视化图表，辅助分析模型在不同目标尺寸和类别上的表现短板。主要函数：`plot_pr()`。 |
| `outputs/` | 评估结果输出目录，存放 JSON 指标文件和各类可视化图表。 |

---

### inference/ — 推理与导出

| 文件 | 说明 |
|------|------|
| `detect.py` | **单图 / 目录检测脚本**，对单张图片或整个文件夹执行目标检测推理，在图像上绘制边界框和类别标签并保存结果。支持设置置信度阈值和 IoU 阈值。主要函数：`main()`。 |
| `batch_inference.py` | **批量推理脚本**，专为大规模数据集推理设计，批量处理文件夹中的多张图片，支持自定义输入分辨率、置信度阈值，并同时保存可视化图像和检测结果文本文件。主要函数：`main()`。 |
| `export_onnx.py` | **ONNX 格式导出**，将训练好的 YOLOv8 `.pt` 权重转换为 ONNX 格式，支持动态输入尺寸和自定义 opset 版本，用于跨平台推理部署（如 ONNX Runtime、OpenVINO）。主要函数：`export()`。 |
| `export_tensorrt.py` | **TensorRT 引擎导出**，将 YOLOv8 权重转换为 TensorRT `.engine` 格式，支持 FP32 / FP16 精度选择，充分利用 NVIDIA GPU 加速实现生产级高性能推理。主要函数：`export()`。 |
| `deployment/` | 部署相关的辅助配置和脚本目录（如 Docker、服务化接口等）。 |

---

### models/ — 模型配置

| 文件 | 说明 |
|------|------|
| `configs/yolov8_drone_config.yaml` | **YOLOv8 训练参数中心**，项目最核心的配置文件，包含以下配置章节：**模型**（YOLOv8s、640 输入分辨率、6 个目标类别）；**训练超参数**（300 轮、batch=8、初始学习率 0.01）；**小目标优化**（多尺度训练、anchor_t=4.0、标签平滑 0.1）；**性能优化**（AMP 混合精度训练、图像权重采样）；**数据路径**（指向 `data/splits/`）；**硬件配置**（针对 RTX 3070 Ti 8GB 显存的参数设定）。 |
| `custom_models/` | 自定义模型结构目录，可存放修改后的 YAML 网络结构文件（如增加 P2 检测头的小目标优化版本）。 |
| `weights/` | 预训练权重存放目录，如官方 `yolov8s.pt`，`.gitignore` 已排除此目录防止大文件入库。 |

---

### scripts/ — 便捷脚本

| 文件 | 说明 |
|------|------|
| `prepare_data.py` | **一键数据准备脚本**，依次调用 `utils/data_preprocessing.py` 完成图像质量检查 → 去重 → 尺寸标准化 → 标注格式转换 → 训练/验证/测试集划分，并生成 YOLO 所需的 `data.yaml` 配置文件。主要函数：`main()`。 |
| `train_yolov8.py` | **轻量训练入口脚本**，通过命令行参数指定模型规格（n/s/m/l/x）和数据路径，快速调用 `training/train.py` 启动训练，适合快速迭代实验。主要函数：`main()`。 |
| `eval_latest.py` | **自动评估最新模型脚本**，自动扫描 `training/runs/` 找到最新训练输出目录，加载其中的 `best.pt` 权重，自动调用评估流程，省去手动指定路径的操作。主要函数：`main()`。 |
| `benchmark_fps.py` | **推理 FPS 基准测试脚本**，在测试集上执行多次推理并精确计时，统计平均帧率（FPS）、延迟（ms/frame）等吞吐量指标，用于评估模型在目标硬件上的实时性能。主要函数：`main()`。 |

---

### tests/ — 单元测试

| 文件 | 说明 |
|------|------|
| `test_imports.py` | **模块导入测试**，验证 `utils/` 和 `training/` 等核心模块的所有依赖插件均已正确安装，能够被 Python 正常导入，防止环境配置问题导致隐性运行时错误。测试函数：`test_import_utils_modules()`。 |
| `test_metrics.py` | **指标计算单元测试**，验证 `utils/metrics.py` 中 F1 分数等评估指标函数的计算结果是否符合预期，确保指标实现的正确性。测试函数：`test_f1_score_basic()`。 |

运行测试：

```bash
pytest tests/
```

---

### training/ — 训练核心

| 文件 | 说明 |
|------|------|
| `train.py` | **完整训练框架**，项目最核心的训练模块。`YOLOTrainer` 类封装了完整的生产级训练工作流：**设备自动配置**（GPU/CPU 自动切换）、**WandB 实验日志**（训练曲线实时上传）、**RTX 3070 Ti 显存优化**（AMP 混合精度 + gradient checkpointing）、**小目标检测增强**（调用 `utils/data_augmentation.py`）、**训练后自动导出**（ONNX/TensorRT）。主要方法：`_setup_device()`、`_init_wandb()`、`setup_model()`、`train()`、`validate()`、`export_model()`。 |
| `validate.py` | **独立验证脚本**，从配置文件读取数据路径和模型参数，对指定权重文件执行模型验证，输出 mAP、Precision、Recall 等详细指标，可在训练外独立调用用于中间检查点评估。主要函数：`run_validation()`、`main()`。 |
| `hyperparameter_tuning.py` | **超参数调优脚本**，实现**网格搜索**和**随机搜索**两种策略，对 batch size、学习率、权重衰减等超参数组合批量实验，记录各组合的评估指标用于选取最优超参数。主要函数：`grid_search()`。 |
| `runs/` | 训练输出目录，每次训练自动创建以日期命名的子目录，存放权重文件（`best.pt`、`last.pt`）、训练曲线图表、混淆矩阵等产物。`.gitignore` 已排除此目录。 |

---

### utils/ — 工具库

| 文件 | 说明 |
|------|------|
| `data_augmentation.py` | **高级数据增强模块**，针对无人机航拍小目标检测场景专门设计。`DroneDataAugmentation` 类实现：**Mosaic 增强**（`apply_mosaic()`，将 4 张图拼接提升小目标密度）；**天气模拟**（`apply_weather_simulation()`，支持雨/雾/雪三种天气效果，提升恶劣环境鲁棒性）；**图像退化模拟**（`apply_degradation()`，模拟低质量航拍）；**智能随机裁剪**（`apply_random_crop_with_bboxes()`，裁剪时保证目标框完整性）；支持批量数据集增强（`create_augmented_dataset()`）。 |
| `data_preprocessing.py` | **数据预处理工具集**，`DataPreprocessor` 类提供完整的数据清洗流水线：**图像质量检查**（`check_image_quality()`，剔除模糊、过曝、欠曝图像）；**重复图像检测**（`remove_duplicates()`，基于感知哈希去除近似重复图像）；**图像标准化**（`standardize_images()`，统一分辨率和色彩空间）；**标注格式转换**（`convert_annotation_format()`，支持 VOC XML / COCO JSON / CSV → YOLO）；**YAML 配置生成**（`create_data_yaml()`，自动生成 YOLOv8 训练所需的 `data.yaml`）。 |
| `metrics.py` | **评估指标计算库**，提供模型性能评估所需的基础指标函数。`f1_score()` 函数基于真正例（TP）、假正例（FP）、假负例（FN）计算 F1 分数，供评估模块和测试模块调用。 |
| `visualization.py` | **可视化工具函数**，`draw_boxes()` 函数在图像上绘制检测边界框，支持自定义颜色、线宽和类别标签显示，用于检测结果可视化和数据增强效果展示。 |

---

## 完整工作流

```
数据采集 (data/raw/)
    ↓
标注 (LabelImg / AnyLabeling → annotation/convert_formats.py)
    ↓
数据清洗与划分 (scripts/prepare_data.py → utils/data_preprocessing.py)
    ↓
数据增强 (utils/data_augmentation.py → data/augmented/)
    ↓
模型训练 (scripts/train_yolov8.py → training/train.py)
    ↓
模型评估 (scripts/eval_latest.py → evaluation/evaluate_model.py)
    ↓
性能分析 (evaluation/confusion_matrix.py + evaluation/performance_analysis.py)
    ↓
模型导出 (inference/export_onnx.py / inference/export_tensorrt.py)
    ↓
部署推理 (inference/detect.py / inference/batch_inference.py)
```

详细流程参见 [docs/pipeline.md](docs/pipeline.md)。

---

## 检测类别

| ID | 类别名称 |
|----|---------|
| 0 | 风筝 |
| 1 | 塑料薄膜 |
| 2 | 彩条布 |
| 3 | 气球 |
| 4 | 鸟巢 |
| 5 | 其他异物 |

---

## 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| GPU | NVIDIA GTX 1060 6GB | RTX 3070 Ti 8GB （已优化） |
| 内存 | 16 GB | 32 GB |
| 存储 | 50 GB SSD | 200 GB SSD |
| CUDA | 11.8 | 12.x |

