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