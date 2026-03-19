"""
数据预处理工具模块
包含图像预处理、标注文件处理、数据清洗等功能
"""

import os
import cv2
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import yaml
import json
from PIL import Image, ExifTags
import shutil

class DataPreprocessor:
    """数据预处理器类"""
    
    def __init__(self, data_dir: str):
        """
        初始化数据预处理器
        
        Args:
            data_dir: 数据根目录
        """
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.annotations_dir = self.data_dir / "annotations"
        
        # 创建处理后的目录
        self.processed_dir.mkdir(exist_ok=True)
        (self.processed_dir / "images").mkdir(exist_ok=True)
        (self.processed_dir / "labels").mkdir(exist_ok=True)
    
    def check_image_quality(self, image_path: Path) -> Dict[str, any]:
        """
        检查图像质量
        
        Args:
            image_path: 图像路径
            
        Returns:
            质量检查结果字典
        """
        try:
            # 读取图像
            img = cv2.imread(str(image_path))
            if img is None:
                return {"valid": False, "reason": "无法读取图像"}
            
            height, width = img.shape[:2]
            
            # 检查图像尺寸
            if width < 100 or height < 100:
                return {"valid": False, "reason": "图像尺寸过小"}
            
            # 检查模糊度（使用拉普拉斯算子）
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            if laplacian_var < 50:  # 阈值可根据需要调整
                return {"valid": False, "reason": "图像模糊", "blur_score": laplacian_var}
            
            # 检查是否过曝或欠曝
            mean_brightness = np.mean(gray)
            if mean_brightness > 250 or mean_brightness < 10:
                return {"valid": False, "reason": "曝光异常", "brightness": mean_brightness}
            
            return {
                "valid": True,
                "resolution": (width, height),
                "blur_score": laplacian_var,
                "brightness": mean_brightness
            }
            
        except Exception as e:
            return {"valid": False, "reason": f"处理错误: {str(e)}"}
    
    def remove_duplicates(self, image_dir: Path, hash_threshold: float = 0.95) -> List[Path]:
        """
        移除重复或相似的图像
        
        Args:
            image_dir: 图像目录
            hash_threshold: 相似度阈值
            
        Returns:
            移除的文件列表
        """
        removed_files = []
        image_hashes = {}
        
        for img_path in image_dir.glob("*.{jpg,jpeg,png,JPG,JPEG,PNG}"):
            try:
                # 计算图像哈希
                img = Image.open(img_path)
                img_hash = self._calculate_image_hash(img)
                
                # 检查是否与已有图像相似
                is_duplicate = False
                for existing_hash, existing_path in image_hashes.items():
                    similarity = self._compare_hashes(img_hash, existing_hash)
                    if similarity > hash_threshold:
                        is_duplicate = True
                        print(f"发现重复图像: {img_path.name} 与 {existing_path.name} (相似度: {similarity:.2f})")
                        break
                
                if is_duplicate:
                    removed_files.append(img_path)
                    # 可选：移动到其他目录而不是删除
                    duplicate_dir = image_dir / "duplicates"
                    duplicate_dir.mkdir(exist_ok=True)
                    shutil.move(str(img_path), str(duplicate_dir / img_path.name))
                else:
                    image_hashes[img_hash] = img_path
                    
            except Exception as e:
                print(f"处理图像 {img_path} 时出错: {e}")
        
        print(f"共移除 {len(removed_files)} 个重复图像")
        return removed_files
    
    def _calculate_image_hash(self, img: Image.Image, hash_size: int = 8) -> np.ndarray:
        """计算图像哈希"""
        # 调整图像大小
        img = img.resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
        # 转换为灰度图
        img = img.convert("L")
        pixels = np.array(img)
        
        # 计算差异哈希
        diff = pixels[:, 1:] > pixels[:, :-1]
        return diff.flatten()
    
    def _compare_hashes(self, hash1: np.ndarray, hash2: np.ndarray) -> float:
        """比较两个哈希的相似度"""
        if len(hash1) != len(hash2):
            return 0.0
        
        # 计算汉明距离
        hamming_distance = np.sum(hash1 != hash2)
        # 转换为相似度
        similarity = 1 - (hamming_distance / len(hash1))
        return similarity
    
    def standardize_images(self, input_dir: Path, output_size: Tuple[int, int] = (640, 640), 
                          quality: int = 95) -> None:
        """
        标准化图像尺寸和质量
        
        Args:
            input_dir: 输入图像目录
            output_size: 输出图像尺寸
            quality: JPEG质量
        """
        output_dir = self.processed_dir / "images"
        
        for img_path in input_dir.glob("*.{jpg,jpeg,png,JPG,JPEG,PNG}"):
            try:
                # 读取图像
                img = cv2.imread(str(img_path))
                if img is None:
                    print(f"无法读取图像: {img_path}")
                    continue
                
                # 调整尺寸
                img_resized = cv2.resize(img, output_size, interpolation=cv2.INTER_LANCZOS4)
                
                # 保存标准化后的图像
                output_path = output_dir / f"{img_path.stem}.jpg"
                cv2.imwrite(str(output_path), img_resized, [cv2.IMWRITE_JPEG_QUALITY, quality])
                
                print(f"处理完成: {img_path.name} -> {output_path.name}")
                
            except Exception as e:
                print(f"处理图像 {img_path} 时出错: {e}")
    
    def convert_annotation_format(self, annotation_dir: Path, input_format: str = "xml", 
                                 output_format: str = "yolo") -> None:
        """
        转换标注文件格式
        
        Args:
            annotation_dir: 标注文件目录
            input_format: 输入格式 (xml, json, csv)
            output_format: 输出格式 (yolo)
        """
        output_dir = self.processed_dir / "labels"
        
        if input_format.lower() == "xml":
            self._convert_xml_to_yolo(annotation_dir, output_dir)
        elif input_format.lower() == "json":
            self._convert_json_to_yolo(annotation_dir, output_dir)
        elif input_format.lower() == "csv":
            self._convert_csv_to_yolo(annotation_dir, output_dir)
        else:
            raise ValueError(f"不支持的输入格式: {input_format}")
    
    def _convert_xml_to_yolo(self, xml_dir: Path, output_dir: Path) -> None:
        """将Pascal VOC XML格式转换为YOLO格式"""
        import xml.etree.ElementTree as ET
        
        for xml_path in xml_dir.glob("*.xml"):
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                
                # 获取图像尺寸
                size = root.find('size')
                width = int(size.find('width').text)
                height = int(size.find('height').text)
                
                # YOLO格式标注
                yolo_annotations = []
                
                for obj in root.findall('object'):
                    class_name = obj.find('name').text
                    bbox = obj.find('bndbox')
                    
                    xmin = int(bbox.find('xmin').text)
                    ymin = int(bbox.find('ymin').text)
                    xmax = int(bbox.find('xmax').text)
                    ymax = int(bbox.find('ymax').text)
                    
                    # 转换为YOLO格式 (中心点坐标 + 宽高，归一化)
                    x_center = (xmin + xmax) / 2 / width
                    y_center = (ymin + ymax) / 2 / height
                    box_width = (xmax - xmin) / width
                    box_height = (ymax - ymin) / height
                    
                    # 这里需要类别到ID的映射
                    class_id = self._get_class_id(class_name)
                    
                    yolo_annotations.append(f"{class_id} {x_center} {y_center} {box_width} {box_height}")
                
                # 保存YOLO格式标注文件
                output_path = output_dir / f"{xml_path.stem}.txt"
                with open(output_path, 'w') as f:
                    f.write('\n'.join(yolo_annotations))
                
                print(f"转换完成: {xml_path.name} -> {output_path.name}")
                
            except Exception as e:
                print(f"转换标注文件 {xml_path} 时出错: {e}")
    
    def _get_class_id(self, class_name: str) -> int:
        """获取类别ID映射"""
        # 异物检测类别定义
        class_mapping = {
            'kite': 0,          # 风筝
            'plastic_film': 1,  # 塑料薄膜
            'color_cloth': 2,   # 彩条布
            'balloon': 3,       # 气球
            'bird_nest': 4,     # 鸟巢
            'foreign_object': 5  # 其他异物
        }
        
        return class_mapping.get(class_name.lower(), 5)
    
    def create_data_yaml(self, class_names: List[str], train_path: str = "train", 
                        val_path: str = "val", test_path: str = "test") -> None:
        """
        创建YOLO数据配置文件
        
        Args:
            class_names: 类别名称列表
            train_path: 训练集路径
            val_path: 验证集路径
            test_path: 测试集路径
        """
        data_config = {
            'path': str(self.data_dir),
            'train': train_path,
            'val': val_path,
            'test': test_path,
            'nc': len(class_names),
            'names': class_names
        }
        
        yaml_path = self.data_dir / "data.yaml"
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data_config, f, allow_unicode=True, sort_keys=False)
        
        print(f"数据配置文件已创建: {yaml_path}")

def clean_and_split(input_dir: str, processed_dir: str, splits_dir: str,
                    train_ratio: float = 0.8, val_ratio: float = 0.1) -> None:
    """
    一键数据清洗和划分函数

    该函数执行完整的数据准备流程：
    1. 检查和过滤低质量图像
    2. 移除重复图像
    3. 标准化图像尺寸
    4. 将数据集划分为训练集、验证集和测试集
    5. 生成YOLO数据配置文件

    Args:
        input_dir: 输入数据目录（包含原始图像和标注）
        processed_dir: 处理后的数据目录
        splits_dir: 数据集划分输出目录
        train_ratio: 训练集比例 (默认: 0.8)
        val_ratio: 验证集比例 (默认: 0.1)
    """
    import random
    from typing import List

    input_path = Path(input_dir)
    processed_path = Path(processed_dir)
    splits_path = Path(splits_dir)

    # 创建必要的目录
    processed_path.mkdir(parents=True, exist_ok=True)
    splits_path.mkdir(parents=True, exist_ok=True)

    # 创建训练/验证/测试集目录
    for split in ['train', 'val', 'test']:
        (splits_path / split / 'images').mkdir(parents=True, exist_ok=True)
        (splits_path / split / 'labels').mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("开始数据清洗和划分流程...")
    print("=" * 60)

    # 初始化预处理器
    data_dir = input_path.parent if input_path.name == "annotations" else input_path.parent.parent
    preprocessor = DataPreprocessor(str(data_dir))

    # 确定原始图像目录
    raw_images_dir = data_dir / "raw"
    if not raw_images_dir.exists():
        print(f"警告: {raw_images_dir} 不存在，使用输入目录作为源")
        raw_images_dir = input_path

    # 1. 检查图像质量
    print("\n步骤 1/6: 检查图像质量...")
    valid_images = []
    invalid_images = []

    image_patterns = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]
    for pattern in image_patterns:
        for img_path in raw_images_dir.glob(pattern):
            quality_check = preprocessor.check_image_quality(img_path)
            if quality_check["valid"]:
                valid_images.append(img_path)
            else:
                invalid_images.append((img_path, quality_check.get("reason", "未知原因")))
                print(f"  ⚠️  跳过低质量图像: {img_path.name} - {quality_check.get('reason', '未知')}")

    print(f"  ✓ 有效图像: {len(valid_images)}, 无效图像: {len(invalid_images)}")

    if len(valid_images) == 0:
        print("\n错误: 没有找到有效的图像文件！")
        return

    # 2. 移除重复图像
    print("\n步骤 2/6: 检测并移除重复图像...")
    # 创建临时目录用于去重处理
    temp_dir = processed_path / "temp_dedup"
    temp_dir.mkdir(exist_ok=True)

    # 复制有效图像到临时目录
    for img_path in valid_images:
        shutil.copy2(str(img_path), str(temp_dir / img_path.name))

    removed_files = preprocessor.remove_duplicates(temp_dir, hash_threshold=0.95)

    # 获取去重后的图像列表
    unique_images = []
    for pattern in image_patterns:
        unique_images.extend(list(temp_dir.glob(pattern)))

    print(f"  ✓ 去重完成，保留 {len(unique_images)} 张唯一图像")

    # 3. 标准化图像尺寸
    print("\n步骤 3/6: 标准化图像尺寸和质量...")
    standardized_dir = processed_path / "standardized"
    standardized_dir.mkdir(exist_ok=True)

    standardized_images = []
    for img_path in unique_images:
        try:
            img = cv2.imread(str(img_path))
            if img is None:
                continue

            # 调整尺寸为640x640
            img_resized = cv2.resize(img, (640, 640), interpolation=cv2.INTER_LANCZOS4)

            # 保存标准化后的图像
            output_path = standardized_dir / f"{img_path.stem}.jpg"
            cv2.imwrite(str(output_path), img_resized, [cv2.IMWRITE_JPEG_QUALITY, 95])
            standardized_images.append(output_path)

        except Exception as e:
            print(f"  ⚠️  处理图像 {img_path.name} 时出错: {e}")

    print(f"  ✓ 标准化完成，共处理 {len(standardized_images)} 张图像")

    # 4. 处理标注文件
    print("\n步骤 4/6: 转换标注格式...")
    annotations_dir = input_path if input_path.name == "annotations" else input_path / "annotations"
    labels_dir = processed_path / "labels"
    labels_dir.mkdir(exist_ok=True)

    if annotations_dir.exists():
        # 支持XML和TXT格式
        xml_files = list(annotations_dir.glob("*.xml"))
        txt_files = list(annotations_dir.glob("*.txt"))

        if xml_files:
            print(f"  发现 {len(xml_files)} 个XML标注文件，开始转换...")
            preprocessor._convert_xml_to_yolo(annotations_dir, labels_dir)

        if txt_files:
            print(f"  发现 {len(txt_files)} 个TXT标注文件，直接复制...")
            for txt_file in txt_files:
                shutil.copy2(str(txt_file), str(labels_dir / txt_file.name))
    else:
        print(f"  ⚠️  警告: 未找到标注目录 {annotations_dir}")

    # 统计有效的图像-标注对
    valid_pairs = []
    for img_path in standardized_images:
        label_path = labels_dir / f"{img_path.stem}.txt"
        if label_path.exists():
            valid_pairs.append((img_path, label_path))
        else:
            print(f"  ⚠️  图像 {img_path.name} 缺少对应的标注文件")

    print(f"  ✓ 找到 {len(valid_pairs)} 对有效的图像-标注对")

    if len(valid_pairs) == 0:
        print("\n错误: 没有找到有效的图像-标注对！")
        return

    # 5. 划分数据集
    print(f"\n步骤 5/6: 划分数据集 (train: {train_ratio}, val: {val_ratio}, test: {1-train_ratio-val_ratio})...")

    # 随机打乱数据
    random.seed(42)
    random.shuffle(valid_pairs)

    # 计算划分点
    total = len(valid_pairs)
    train_count = int(total * train_ratio)
    val_count = int(total * val_ratio)

    train_pairs = valid_pairs[:train_count]
    val_pairs = valid_pairs[train_count:train_count + val_count]
    test_pairs = valid_pairs[train_count + val_count:]

    print(f"  训练集: {len(train_pairs)} 对")
    print(f"  验证集: {len(val_pairs)} 对")
    print(f"  测试集: {len(test_pairs)} 对")

    # 复制文件到对应的划分目录
    def copy_pairs(pairs: List[Tuple[Path, Path]], split: str):
        for img_path, label_path in pairs:
            # 复制图像
            dst_img = splits_path / split / 'images' / img_path.name
            shutil.copy2(str(img_path), str(dst_img))
            # 复制标注
            dst_label = splits_path / split / 'labels' / label_path.name
            shutil.copy2(str(label_path), str(dst_label))

    print("  正在复制文件...")
    copy_pairs(train_pairs, 'train')
    copy_pairs(val_pairs, 'val')
    copy_pairs(test_pairs, 'test')

    print("  ✓ 数据集划分完成")

    # 6. 创建数据配置文件
    print("\n步骤 6/6: 生成YOLO数据配置文件...")

    class_names = ['kite', 'plastic_film', 'color_cloth', 'balloon', 'bird_nest', 'foreign_object']

    data_config = {
        'path': str(splits_path.absolute()),
        'train': 'train/images',
        'val': 'val/images',
        'test': 'test/images',
        'nc': len(class_names),
        'names': class_names
    }

    yaml_path = splits_path / "data.yaml"
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data_config, f, allow_unicode=True, sort_keys=False)

    print(f"  ✓ 数据配置文件已创建: {yaml_path}")

    # 清理临时目录
    print("\n清理临时文件...")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    print("\n" + "=" * 60)
    print("✅ 数据清洗和划分流程完成！")
    print("=" * 60)
    print(f"\n数据集位置: {splits_path}")
    print(f"配置文件: {yaml_path}")
    print(f"\n现在可以使用以下命令开始训练:")
    print(f"  python scripts/train_yolov8.py --data {yaml_path}")
    print("=" * 60)


def main():
    """主函数：数据预处理流程示例"""
    # 设置数据目录
    data_dir = "data"

    # 初始化预处理器
    preprocessor = DataPreprocessor(data_dir)

    print("开始数据预处理...")

    # 1. 检查图像质量
    print("\n1. 检查图像质量...")
    raw_images_dir = preprocessor.raw_dir
    for img_path in raw_images_dir.glob("*.{jpg,jpeg,png,JPG,JPEG,PNG}"):
        quality_check = preprocessor.check_image_quality(img_path)
        if not quality_check["valid"]:
            print(f"⚠️  图像质量问题: {img_path.name} - {quality_check['reason']}")

    # 2. 移除重复图像
    print("\n2. 移除重复图像...")
    removed_files = preprocessor.remove_duplicates(raw_images_dir)

    # 3. 标准化图像
    print("\n3. 标准化图像尺寸...")
    preprocessor.standardize_images(raw_images_dir, output_size=(640, 640))

    # 4. 转换标注格式
    print("\n4. 转换标注格式...")
    annotations_dir = preprocessor.annotations_dir
    preprocessor.convert_annotation_format(annotations_dir, input_format="xml", output_format="yolo")

    # 5. 创建数据配置文件
    print("\n5. 创建数据配置文件...")
    class_names = ['kite', 'plastic_film', 'color_cloth', 'balloon', 'bird_nest', 'foreign_object']
    preprocessor.create_data_yaml(class_names)

    print("\n✅ 数据预处理完成！")

if __name__ == "__main__":
    main()