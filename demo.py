#!/usr/bin/env python3
"""
快速演示脚本 - 展示项目核心功能
无需真实数据，使用模拟数据演示各模块功能
"""
import sys
import numpy as np
import cv2
from pathlib import Path
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.metrics import (
    calculate_precision, calculate_recall, f1_score,
    calculate_iou, calculate_ap, calculate_map
)
from utils.visualization import draw_boxes
from utils.data_preprocessing import DataPreprocessor
from utils.data_augmentation import DroneDataAugmentation


def print_header(text):
    """打印格式化的标题"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def demo_metrics():
    """演示评估指标计算"""
    print_header("1. 评估指标计算演示")

    # 模拟检测结果
    tp, fp, fn = 85, 15, 20

    precision = calculate_precision(tp, fp)
    recall = calculate_recall(tp, fn)
    f1 = f1_score(precision, recall)

    print(f"\n检测统计:")
    print(f"  真正例 (TP): {tp}")
    print(f"  假正例 (FP): {fp}")
    print(f"  假负例 (FN): {fn}")
    print(f"\n评估指标:")
    print(f"  精确率 (Precision): {precision:.4f}")
    print(f"  召回率 (Recall):    {recall:.4f}")
    print(f"  F1分数:            {f1:.4f}")

    # IoU计算
    print(f"\n边界框IoU计算:")
    box1 = [100, 100, 200, 200]  # [x1, y1, x2, y2]
    box2 = [150, 150, 250, 250]
    iou = calculate_iou(box1, box2, format='xyxy')
    print(f"  框1: {box1}")
    print(f"  框2: {box2}")
    print(f"  IoU: {iou:.4f}")

    # mAP计算
    print(f"\nmAP计算:")
    aps = {
        'kite': 0.85,
        'plastic_film': 0.90,
        'color_cloth': 0.80,
        'balloon': 0.75,
        'bird_nest': 0.88,
        'foreign_object': 0.82
    }
    map_value = calculate_map(aps)

    print(f"  各类别AP:")
    for class_name, ap in aps.items():
        print(f"    {class_name:15s}: {ap:.4f}")
    print(f"  mAP@0.5: {map_value:.4f}")


def demo_iou_calculation():
    """演示IoU计算的各种情况"""
    print_header("2. IoU计算演示")

    test_cases = [
        {
            'name': '完全重叠',
            'box1': [0, 0, 100, 100],
            'box2': [0, 0, 100, 100],
        },
        {
            'name': '部分重叠',
            'box1': [0, 0, 100, 100],
            'box2': [50, 50, 150, 150],
        },
        {
            'name': '无重叠',
            'box1': [0, 0, 100, 100],
            'box2': [200, 200, 300, 300],
        },
        {
            'name': '包含关系',
            'box1': [0, 0, 200, 200],
            'box2': [50, 50, 150, 150],
        },
    ]

    for case in test_cases:
        iou = calculate_iou(case['box1'], case['box2'], format='xyxy')
        print(f"\n{case['name']}:")
        print(f"  框1: {case['box1']}")
        print(f"  框2: {case['box2']}")
        print(f"  IoU: {iou:.4f}")


def demo_data_augmentation():
    """演示数据增强功能"""
    print_header("3. 数据增强演示")

    # 创建示例图像
    print("\n创建示例图像和标注...")
    img = np.random.randint(50, 200, (640, 640, 3), dtype=np.uint8)
    bboxes = [
        [0, 0.3, 0.3, 0.2, 0.2],  # [class_id, x_center, y_center, width, height]
        [1, 0.7, 0.7, 0.15, 0.15],
    ]

    augmenter = DroneDataAugmentation()

    # 1. 天气模拟
    print("\n应用天气模拟增强...")
    weather_types = ['rain', 'fog', 'snow']
    for weather in weather_types:
        weather_img, weather_bboxes = augmenter.apply_weather_simulation(
            img.copy(), bboxes.copy(), weather_type=weather
        )
        print(f"  ✓ {weather}天气效果已应用 (保留 {len(weather_bboxes)} 个边界框)")

    # 2. 图像退化
    print("\n应用图像退化模拟...")
    degraded_img, degraded_bboxes = augmenter.apply_degradation(img.copy(), bboxes.copy())
    print(f"  ✓ 图像退化已应用 (保留 {len(degraded_bboxes)} 个边界框)")

    # 3. 随机裁剪
    print("\n应用智能随机裁剪...")
    cropped_img, cropped_bboxes = augmenter.apply_random_crop_with_bboxes(
        img.copy(), bboxes.copy(), crop_size=(480, 480)
    )
    print(f"  ✓ 随机裁剪完成 (裁剪尺寸: {cropped_img.shape[:2]}, 保留 {len(cropped_bboxes)} 个边界框)")


def demo_data_preprocessing():
    """演示数据预处理功能"""
    print_header("4. 数据预处理演示")

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    try:
        print(f"\n使用临时目录: {temp_dir}")

        # 创建测试图像
        print("\n创建测试图像...")
        raw_dir = Path(temp_dir) / "raw"
        raw_dir.mkdir(parents=True)

        # 创建不同质量的图像
        test_images = [
            ("good_image.jpg", np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)),
            ("good_image2.jpg", np.random.randint(40, 180, (480, 640, 3), dtype=np.uint8)),
        ]

        for name, img in test_images:
            cv2.imwrite(str(raw_dir / name), img)
        print(f"  ✓ 创建了 {len(test_images)} 张测试图像")

        # 初始化预处理器
        preprocessor = DataPreprocessor(temp_dir)

        # 图像质量检查
        print("\n执行图像质量检查...")
        valid_count = 0
        for img_path in raw_dir.glob("*.jpg"):
            result = preprocessor.check_image_quality(img_path)
            if result["valid"]:
                valid_count += 1
                print(f"  ✓ {img_path.name}: 有效 (模糊度: {result['blur_score']:.2f}, "
                      f"亮度: {result['brightness']:.2f})")
            else:
                print(f"  ✗ {img_path.name}: 无效 - {result['reason']}")

        print(f"\n质量检查完成: {valid_count}/{len(test_images)} 张图像通过")

        # 图像标准化
        print("\n执行图像标准化...")
        preprocessor.standardize_images(raw_dir, output_size=(640, 640), quality=95)

        output_dir = preprocessor.processed_dir / "images"
        output_count = len(list(output_dir.glob("*.jpg")))
        print(f"  ✓ 标准化完成，输出 {output_count} 张图像到 {output_dir}")

        # 创建数据配置
        print("\n创建YAML数据配置...")
        class_names = ['kite', 'plastic_film', 'color_cloth', 'balloon', 'bird_nest', 'foreign_object']
        preprocessor.create_data_yaml(class_names)
        print(f"  ✓ 配置文件已创建: {Path(temp_dir) / 'data.yaml'}")

    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)
        print(f"\n临时目录已清理")


def demo_class_mapping():
    """演示类别映射"""
    print_header("5. 类别映射演示")

    class_names = ['kite', 'plastic_film', 'color_cloth', 'balloon', 'bird_nest', 'foreign_object']
    class_names_cn = ['风筝', '塑料薄膜', '彩条布', '气球', '鸟巢', '其他异物']

    print("\n检测类别映射:")
    print(f"{'ID':<5} {'英文名称':<20} {'中文名称':<10}")
    print("-" * 40)
    for i, (en, cn) in enumerate(zip(class_names, class_names_cn)):
        print(f"{i:<5} {en:<20} {cn:<10}")


def demo_visualization():
    """演示可视化功能"""
    print_header("6. 可视化演示")

    # 创建示例图像
    img = np.ones((640, 640, 3), dtype=np.uint8) * 255

    # 模拟检测框 [x1, y1, x2, y2]
    boxes = [
        [100, 100, 250, 250],
        [400, 400, 550, 550],
    ]
    classes = [0, 1]  # kite, plastic_film
    scores = [0.95, 0.87]

    print("\n绘制检测框...")
    print(f"  检测到 {len(boxes)} 个目标")
    for i, (box, cls, score) in enumerate(zip(boxes, classes, scores)):
        print(f"    目标 {i+1}: 类别={cls}, 置信度={score:.2f}, 位置={box}")

    # 绘制边界框
    class_names = ['kite', 'plastic_film']
    result_img = draw_boxes(img, boxes, classes, scores, class_names)

    print(f"  ✓ 边界框已绘制到图像上")


def demo_statistics():
    """演示统计信息"""
    print_header("7. 数据集统计演示")

    # 模拟数据集统计
    stats = {
        '总图像数': 1000,
        '训练集': 800,
        '验证集': 100,
        '测试集': 100,
        '平均每张图像的目标数': 2.3,
        '最小目标尺寸': '10x10 像素',
        '最大目标尺寸': '300x300 像素',
    }

    class_distribution = {
        'kite': 250,
        'plastic_film': 300,
        'color_cloth': 200,
        'balloon': 150,
        'bird_nest': 180,
        'foreign_object': 220,
    }

    print("\n数据集概览:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n类别分布:")
    total_objects = sum(class_distribution.values())
    for class_name, count in class_distribution.items():
        percentage = count / total_objects * 100
        print(f"  {class_name:15s}: {count:4d} ({percentage:5.2f}%)")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print(" " * 15 + "无人机异物检测系统 - 功能演示")
    print("=" * 70)
    print("\n本演示脚本展示项目的核心功能，无需真实数据即可运行。")
    print("演示内容包括：评估指标、数据增强、数据预处理、可视化等。")

    try:
        # 运行各个演示模块
        demo_metrics()
        demo_iou_calculation()
        demo_data_augmentation()
        demo_data_preprocessing()
        demo_class_mapping()
        demo_visualization()
        demo_statistics()

        # 总结
        print("\n" + "=" * 70)
        print("  演示完成！")
        print("=" * 70)
        print("\n所有核心功能已成功演示。")
        print("\n下一步:")
        print("  1. 准备真实的无人机图像数据")
        print("  2. 运行 python scripts/prepare_data.py 准备数据集")
        print("  3. 运行 python scripts/train_yolov8.py 开始训练")
        print("  4. 运行 python scripts/eval_latest.py 评估模型")
        print("  5. 运行 python inference/detect.py 进行目标检测")
        print("\n详细文档请参考 README.md 和 docs/pipeline.md")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
