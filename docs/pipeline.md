# 数据到部署流水线

1. 数据收集与清洗  
   - 放入 `data/raw/`，用去重/模糊检测脚本清洗，结果登记到 `data/data_manifest.csv`。
2. 标注  
   - 用 LabelImg/AnyLabeling，类别表：kite, plastic_film, color_cloth, balloon, bird_nest, foreign_object。  
   - 运行 `annotation/convert_formats.py` 转为 YOLO TXT，输出至 `data/annotations/`。
3. 预处理与划分  
   - `python utils/data_preprocessing.py --input data/annotations --output data/processed`  
   - 划分 8:1:1 到 `data/splits/{train,val,test}`。
4. 增强  
   - `python utils/data_augmentation.py --input data/splits/train --output data/augmented`  
   - 关注小目标：Mosaic、随机裁剪、颜色/天气扰动。
5. 训练  
   - 配置 `models/configs/yolov8_drone_config.yaml`；运行 `python training/train.py --config ... --data data/data.yaml`。  
   - 输出至 `training/runs/<date_experiment>/`。
6. 评估  
   - `python training/validate.py --config ... --data data/data.yaml`  
   - `python evaluation/evaluate_model.py --weights <best.pt> --data data/data.yaml` → `evaluation/outputs/`。
7. 导出与部署  
   - ONNX: `python inference/export_onnx.py --weights <best.pt>`  
   - TensorRT: `python inference/export_tensorrt.py --weights <best.pt>`.
8. 批量推理  
   - `python inference/batch_inference.py --weights <best.engine/pt> --source <dir>`。

硬件提示：3070 Ti 8GB 建议 `batch<=8`、`imgsz=640`、`cache=False`、`workers<=4`；32GB 内存可开 `cache=ram`。
