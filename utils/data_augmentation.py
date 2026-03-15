"""
数据增强模块
专门针对无人机航拍小目标检测的数据增强策略
"""

import cv2
import numpy as np
import random
from PIL import Image, ImageEnhance, ImageFilter
import albumentations as A
from albumentations.pytorch import ToTensorV2
from typing import List, Tuple, Optional, Union
import os
from pathlib import Path

class DroneDataAugmentation:
    """无人机数据增强器"""
    
    def __init__(self, target_size: Tuple[int, int] = (640, 640)):
        """
        初始化数据增强器
        
        Args:
            target_size: 目标图像尺寸
        """
        self.target_size = target_size
        
        # 基础增强
        self.base_transform = A.Compose([
            A.Resize(target_size[0], target_size[1]),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.3),
            A.RandomRotate90(p=0.5),
        ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))
        
        # 天气条件增强（模拟不同天气）
        self.weather_transform = A.Compose([
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
            A.RandomGamma(gamma_limit=(80, 120), p=0.3),
            A.CLAHE(clip_limit=2.0, tile_grid_size=(8, 8), p=0.3),
            A.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1, p=0.4),
        ])
        
        # 退化仿真（模拟图像质量下降）
        self.degradation_transform = A.Compose([
            A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
            A.ImageCompression(quality_lower=70, quality_upper=100, p=0.3),
            A.Blur(blur_limit=3, p=0.2),
            A.Downscale(scale_min=0.8, scale_max=0.99, p=0.2),
        ])
        
        # 小目标专用增强
        self.small_object_transform = A.Compose([
            A.RandomSizedBBoxSafeCrop(height=target_size[0], width=target_size[1], 
                                    erosion_rate=0.2, p=0.4),
            A.Affine(scale=(0.8, 1.2), translate_percent=0.1, rotate=10, p=0.5),
        ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))
    
    def apply_mosaic(self, images: List[np.ndarray], bboxes: List[List], 
                     class_labels: List[List], mosaic_size: int = 2) -> Tuple[np.ndarray, List, List]:
        """
        应用Mosaic增强
        
        Args:
            images: 图像列表
            bboxes: 边界框列表
            class_labels: 类别标签列表
            mosaic_size: Mosaic尺寸（2x2或3x3）
            
        Returns:
            增强后的图像、边界框、类别标签
        """
        if len(images) < mosaic_size * mosaic_size:
            raise ValueError(f"需要至少 {mosaic_size * mosaic_size} 张图像进行Mosaic增强")
        
        # 随机选择图像
        selected_indices = random.sample(range(len(images)), mosaic_size * mosaic_size)
        
        # 创建Mosaic图像
        target_height, target_width = self.target_size
        mosaic_img = np.zeros((target_height * mosaic_size, target_width * mosaic_size, 3), dtype=np.uint8)
        
        all_bboxes = []
        all_labels = []
        
        for i, idx in enumerate(selected_indices):
            img = images[idx].copy()
            img_bboxes = bboxes[idx].copy()
            img_labels = class_labels[idx].copy()
            
            # 计算在Mosaic中的位置
            row = i // mosaic_size
            col = i % mosaic_size
            
            # 调整图像大小
            img_resized = cv2.resize(img, (target_width, target_height))
            
            # 放置到Mosaic中
            y1, y2 = row * target_height, (row + 1) * target_height
            x1, x2 = col * target_width, (col + 1) * target_width
            mosaic_img[y1:y2, x1:x2] = img_resized
            
            # 调整边界框坐标
            for bbox, label in zip(img_bboxes, img_labels):
                x_center, y_center, width, height = bbox
                
                # 转换到Mosaic坐标系
                new_x_center = (x_center * target_width + col * target_width) / (target_width * mosaic_size)
                new_y_center = (y_center * target_height + row * target_height) / (target_height * mosaic_size)
                new_width = width / mosaic_size
                new_height = height / mosaic_size
                
                all_bboxes.append([new_x_center, new_y_center, new_width, new_height])
                all_labels.append(label)
        
        # 调整最终尺寸
        mosaic_img = cv2.resize(mosaic_img, self.target_size)
        
        # 调整边界框尺寸
        final_bboxes = []
        for bbox in all_bboxes:
            x_center, y_center, width, height = bbox
            final_bboxes.append([
                x_center,
                y_center,
                width * mosaic_size,
                height * mosaic_size
            ])
        
        return mosaic_img, final_bboxes, all_labels
    
    def apply_random_crop_with_bboxes(self, image: np.ndarray, bboxes: List[List], 
                                    class_labels: List, crop_size: Tuple[int, int] = None) -> Tuple[np.ndarray, List, List]:
        """
        应用随机裁剪，确保保留小目标
        
        Args:
            image: 输入图像
            bboxes: 边界框
            class_labels: 类别标签
            crop_size: 裁剪尺寸
            
        Returns:
            裁剪后的图像、边界框、类别标签
        """
        if crop_size is None:
            crop_size = (int(self.target_size[0] * 0.8), int(self.target_size[1] * 0.8))
        
        height, width = image.shape[:2]
        
        if len(bboxes) == 0:
            # 随机裁剪
            x = random.randint(0, width - crop_size[0])
            y = random.randint(0, height - crop_size[1])
        else:
            # 基于目标位置进行裁剪，确保包含目标
            bbox = random.choice(bboxes)
            x_center, y_center, box_width, box_height = bbox
            
            # 转换为像素坐标
            x_center_px = int(x_center * width)
            y_center_px = int(y_center * height)
            
            # 随机偏移，但确保目标在裁剪区域内
            max_offset_x = min(x_center_px, crop_size[0] // 2)
            max_offset_y = min(y_center_px, crop_size[1] // 2)
            
            offset_x = random.randint(-max_offset_x, max_offset_x)
            offset_y = random.randint(-max_offset_y, max_offset_y)
            
            x = max(0, min(x_center_px - crop_size[0] // 2 + offset_x, width - crop_size[0]))
            y = max(0, min(y_center_px - crop_size[1] // 2 + offset_y, height - crop_size[1]))
        
        # 执行裁剪
        cropped_img = image[y:y+crop_size[1], x:x+crop_size[0]]
        
        # 调整边界框坐标
        new_bboxes = []
        new_labels = []
        
        for bbox, label in zip(bboxes, class_labels):
            x_center, y_center, box_width, box_height = bbox
            
            # 转换到裁剪坐标系
            x_center_px = x_center * width - x
            y_center_px = y_center * height - y
            
            # 检查目标是否在裁剪区域内
            if (0 <= x_center_px <= crop_size[0] and 
                0 <= y_center_px <= crop_size[1]):
                
                # 归一化坐标
                new_x_center = x_center_px / crop_size[0]
                new_y_center = y_center_px / crop_size[1]
                new_width = box_width * width / crop_size[0]
                new_height = box_height * height / crop_size[1]
                
                new_bboxes.append([new_x_center, new_y_center, new_width, new_height])
                new_labels.append(label)
        
        # 调整尺寸到目标大小
        cropped_img = cv2.resize(cropped_img, self.target_size)
        
        return cropped_img, new_bboxes, new_labels
    
    def apply_weather_simulation(self, image: np.ndarray, weather_type: str = None) -> np.ndarray:
        """
        应用天气条件仿真
        
        Args:
            image: 输入图像
            weather_type: 天气类型 (rain, fog, snow, none)
            
        Returns:
            仿真后的图像
        """
        if weather_type is None:
            weather_type = random.choice(['rain', 'fog', 'snow', 'none'])
        
        result_img = image.copy()
        
        if weather_type == 'rain':
            # 雨效果
            result_img = self._add_rain_effect(result_img)
        elif weather_type == 'fog':
            # 雾效果
            result_img = self._add_fog_effect(result_img)
        elif weather_type == 'snow':
            # 雪效果
            result_img = self._add_snow_effect(result_img)
        
        return result_img
    
    def _add_rain_effect(self, image: np.ndarray) -> np.ndarray:
        """添加雨效果"""
        result = image.copy()
        height, width = result.shape[:2]
        
        # 创建雨滴
        num_drops = int(width * height * 0.001)  # 雨滴密度
        
        for _ in range(num_drops):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            length = random.randint(5, 15)
            thickness = random.randint(1, 2)
            
            # 雨滴方向（斜向下）
            end_x = x + random.randint(-2, 2)
            end_y = y + length
            
            if end_y < height:
                cv2.line(result, (x, y), (end_x, end_y), (200, 200, 255), thickness)
        
        # 添加模糊效果
        result = cv2.GaussianBlur(result, (3, 3), 0)
        
        return result
    
    def _add_fog_effect(self, image: np.ndarray) -> np.ndarray:
        """添加雾效果"""
        result = image.copy()
        
        # 创建雾层
        fog_layer = np.ones_like(result) * 220
        
        # 随机透明度
        alpha = random.uniform(0.3, 0.7)
        
        # 混合图像
        result = cv2.addWeighted(result, 1 - alpha, fog_layer, alpha, 0)
        
        return result
    
    def _add_snow_effect(self, image: np.ndarray) -> np.ndarray:
        """添加雪效果"""
        result = image.copy()
        height, width = result.shape[:2]
        
        # 创建雪花
        num_flakes = int(width * height * 0.0005)  # 雪花密度
        
        for _ in range(num_flakes):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            radius = random.randint(1, 3)
            
            cv2.circle(result, (x, y), radius, (255, 255, 255), -1)
        
        return result
    
    def apply_degradation(self, image: np.ndarray, degradation_level: str = None) -> np.ndarray:
        """
        应用图像退化仿真
        
        Args:
            image: 输入图像
            degradation_level: 退化级别 (light, moderate, severe)
            
        Returns:
            退化后的图像
        """
        if degradation_level is None:
            degradation_level = random.choice(['light', 'moderate', 'severe'])
        
        result = image.copy()
        
        if degradation_level == 'light':
            # 轻度退化
            if random.random() < 0.5:
                result = cv2.GaussianBlur(result, (3, 3), 0)
            if random.random() < 0.3:
                noise = np.random.normal(0, 10, result.shape).astype(np.uint8)
                result = cv2.add(result, noise)
        
        elif degradation_level == 'moderate':
            # 中度退化
            result = cv2.GaussianBlur(result, (5, 5), 0)
            noise = np.random.normal(0, 20, result.shape).astype(np.uint8)
            result = cv2.add(result, noise)
            
            # 降低对比度
            result = cv2.convertScaleAbs(result, alpha=0.8, beta=10)
        
        elif degradation_level == 'severe':
            # 重度退化
            result = cv2.GaussianBlur(result, (7, 7), 0)
            noise = np.random.normal(0, 30, result.shape).astype(np.uint8)
            result = cv2.add(result, noise)
            
            # 显著降低对比度和亮度
            result = cv2.convertScaleAbs(result, alpha=0.6, beta=20)
        
        return result
    
    def augment_single_image(self, image: np.ndarray, bboxes: List[List] = None, 
                           class_labels: List = None, apply_mosaic: bool = False) -> Tuple[np.ndarray, List, List]:
        """
        对单张图像应用增强
        
        Args:
            image: 输入图像
            bboxes: 边界框
            class_labels: 类别标签
            apply_mosaic: 是否应用Mosaic增强
            
        Returns:
            增强后的图像、边界框、类别标签
        """
        if bboxes is None:
            bboxes = []
        if class_labels is None:
            class_labels = []
        
        augmented_img = image.copy()
        augmented_bboxes = bboxes.copy()
        augmented_labels = class_labels.copy()
        
        # 随机选择增强策略
        augmentation_types = ['base', 'weather', 'degradation', 'small_object', 'crop']
        selected_types = random.sample(augmentation_types, k=random.randint(1, 3))
        
        for aug_type in selected_types:
            try:
                if aug_type == 'base' and len(augmented_bboxes) > 0:
                    # 基础增强
                    transformed = self.base_transform(
                        image=augmented_img,
                        bboxes=augmented_bboxes,
                        class_labels=augmented_labels
                    )
                    augmented_img = transformed['image']
                    augmented_bboxes = transformed['bboxes']
                    augmented_labels = transformed['class_labels']
                
                elif aug_type == 'weather':
                    # 天气增强
                    augmented_img = self.apply_weather_simulation(augmented_img)
                
                elif aug_type == 'degradation':
                    # 退化增强
                    augmented_img = self.apply_degradation(augmented_img)
                
                elif aug_type == 'small_object' and len(augmented_bboxes) > 0:
                    # 小目标增强
                    transformed = self.small_object_transform(
                        image=augmented_img,
                        bboxes=augmented_bboxes,
                        class_labels=augmented_labels
                    )
                    augmented_img = transformed['image']
                    augmented_bboxes = transformed['bboxes']
                    augmented_labels = transformed['class_labels']
                
                elif aug_type == 'crop' and len(augmented_bboxes) > 0:
                    # 随机裁剪
                    augmented_img, augmented_bboxes, augmented_labels = \
                        self.apply_random_crop_with_bboxes(augmented_img, augmented_bboxes, augmented_labels)
                
            except Exception as e:
                print(f"应用增强 {aug_type} 时出错: {e}")
                continue
        
        return augmented_img, augmented_bboxes, augmented_labels
    
    def create_augmented_dataset(self, images: List[np.ndarray], bboxes: List[List], 
                               class_labels: List[List], output_dir: str, 
                               augmentation_factor: int = 3) -> None:
        """
        创建增强后的数据集
        
        Args:
            images: 原始图像列表
            bboxes: 边界框列表
            class_labels: 类别标签列表
            output_dir: 输出目录
            augmentation_factor: 每个图像的增强倍数
        """
        output_path = Path(output_dir)
        images_dir = output_path / "images"
        labels_dir = output_path / "labels"
        
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)
        
        for i, (image, bboxes_list, labels_list) in enumerate(zip(images, bboxes, class_labels)):
            # 保存原始图像
            original_img_path = images_dir / f"image_{i:06d}_original.jpg"
            cv2.imwrite(str(original_img_img_path), image)
            
            # 保存原始标注
            original_label_path = labels_dir / f"image_{i:06d}_original.txt"
            with open(original_label_path, 'w') as f:
                for bbox, label in zip(bboxes_list, labels_list):
                    f.write(f"{label} {bbox[0]} {bbox[1]} {bbox[2]} {bbox[3]}\n")
            
            # 应用增强
            for j in range(augmentation_factor):
                try:
                    aug_img, aug_bboxes, aug_labels = self.augment_single_image(
                        image, bboxes_list, labels_list
                    )
                    
                    # 保存增强后的图像
                    aug_img_path = images_dir / f"image_{i:06d}_aug_{j}.jpg"
                    cv2.imwrite(str(aug_img_path), aug_img)
                    
                    # 保存增强后的标注
                    aug_label_path = labels_dir / f"image_{i:06d}_aug_{j}.txt"
                    with open(aug_label_path, 'w') as f:
                        for bbox, label in zip(aug_bboxes, aug_labels):
                            f.write(f"{label} {bbox[0]} {bbox[1]} {bbox[2]} {bbox[3]}\n")
                    
                except Exception as e:
                    print(f"增强图像 {i} 的第 {j} 次增强时出错: {e}")
                    continue
            
            if (i + 1) % 100 == 0:
                print(f"已处理 {i + 1}/{len(images)} 张图像")
        
        print(f"增强数据集创建完成！共生成 {len(images) * (augmentation_factor + 1)} 个样本")

def main():
    """主函数：数据增强示例"""
    # 初始化增强器
    augmenter = DroneDataAugmentation(target_size=(640, 640))
    
    # 示例：加载一些图像进行增强
    # 这里只是示例代码，实际使用时需要加载真实数据
    print("数据增强器初始化完成！")
    print("支持的增强类型:")
    print("- 基础增强: 翻转、旋转、缩放")
    print("- 天气仿真: 雨、雾、雪效果")
    print("- 退化仿真: 模糊、噪声、压缩")
    print("- 小目标增强: 专门优化小目标检测")
    print("- Mosaic增强: 多图像组合")
    print("- 智能裁剪: 保留目标的随机裁剪")

if __name__ == "__main__":
    main()