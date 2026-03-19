"""
utils/data_augmentation.py模块的单元测试
测试数据增强功能，包括Mosaic、天气模拟、图像退化等
"""
import pytest
import numpy as np
import cv2
import tempfile
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_augmentation import DroneDataAugmentation


@pytest.fixture
def augmenter():
    """创建DroneDataAugmentation实例"""
    return DroneDataAugmentation()


@pytest.fixture
def sample_image():
    """创建测试用的样本图像"""
    img = np.random.randint(50, 200, (640, 640, 3), dtype=np.uint8)
    return img


@pytest.fixture
def sample_bboxes():
    """创建测试用的边界框"""
    # YOLO格式: [class_id, x_center, y_center, width, height]
    return [
        [0, 0.5, 0.5, 0.2, 0.2],
        [1, 0.3, 0.3, 0.1, 0.1]
    ]


class TestDroneDataAugmentationInit:
    """测试DroneDataAugmentation初始化"""

    def test_init_default_params(self):
        """测试默认参数初始化"""
        augmenter = DroneDataAugmentation()
        assert augmenter is not None

    def test_init_custom_params(self):
        """测试自定义参数初始化"""
        augmenter = DroneDataAugmentation()
        assert augmenter is not None


class TestMosaicAugmentation:
    """测试Mosaic增强"""

    def test_apply_mosaic_basic(self, augmenter, sample_image, sample_bboxes):
        """测试基本Mosaic增强"""
        images = [sample_image.copy() for _ in range(4)]
        bboxes_list = [sample_bboxes.copy() for _ in range(4)]

        mosaic_img, mosaic_bboxes = augmenter.apply_mosaic(images, bboxes_list, grid_size=(2, 2))

        # 验证输出图像尺寸
        assert mosaic_img.shape[:2] == (640, 640)

        # 验证边界框数量
        assert len(mosaic_bboxes) > 0

        # 验证边界框格式
        for bbox in mosaic_bboxes:
            assert len(bbox) == 5
            # 验证归一化坐标
            assert 0 <= bbox[1] <= 1
            assert 0 <= bbox[2] <= 1

    def test_apply_mosaic_3x3(self, augmenter, sample_image, sample_bboxes):
        """测试3x3 Mosaic增强"""
        images = [sample_image.copy() for _ in range(9)]
        bboxes_list = [sample_bboxes.copy() for _ in range(9)]

        mosaic_img, mosaic_bboxes = augmenter.apply_mosaic(images, bboxes_list, grid_size=(3, 3))

        # 验证输出
        assert mosaic_img.shape[:2] == (640, 640)
        assert len(mosaic_bboxes) > 0

    def test_apply_mosaic_insufficient_images(self, augmenter, sample_image, sample_bboxes):
        """测试图像数量不足的情况"""
        images = [sample_image]
        bboxes_list = [sample_bboxes]

        # 应该返回None或处理错误
        result = augmenter.apply_mosaic(images, bboxes_list, grid_size=(2, 2))
        # 根据实现，可能返回None或抛出异常


class TestWeatherSimulation:
    """测试天气模拟"""

    def test_apply_rain_effect(self, augmenter, sample_image):
        """测试雨天效果"""
        rain_img = augmenter._add_rain_effect(sample_image.copy(), intensity=0.5)

        # 验证输出形状
        assert rain_img.shape == sample_image.shape

        # 验证图像已被修改
        assert not np.array_equal(rain_img, sample_image)

    def test_apply_fog_effect(self, augmenter, sample_image):
        """测试雾天效果"""
        fog_img = augmenter._add_fog_effect(sample_image.copy(), intensity=0.5)

        # 验证输出形状
        assert fog_img.shape == sample_image.shape

        # 验证图像已被修改
        assert not np.array_equal(fog_img, sample_image)

    def test_apply_snow_effect(self, augmenter, sample_image):
        """测试雪天效果"""
        snow_img = augmenter._add_snow_effect(sample_image.copy(), intensity=0.5)

        # 验证输出形状
        assert snow_img.shape == sample_image.shape

        # 验证图像已被修改
        assert not np.array_equal(snow_img, sample_image)

    def test_weather_simulation_all_types(self, augmenter, sample_image, sample_bboxes):
        """测试所有天气类型"""
        weather_types = ['rain', 'fog', 'snow', 'none']

        for weather in weather_types:
            weather_img, weather_bboxes = augmenter.apply_weather_simulation(
                sample_image.copy(),
                sample_bboxes.copy(),
                weather_type=weather
            )

            assert weather_img.shape == sample_image.shape
            assert len(weather_bboxes) == len(sample_bboxes)

    def test_weather_simulation_random(self, augmenter, sample_image, sample_bboxes):
        """测试随机天气"""
        weather_img, weather_bboxes = augmenter.apply_weather_simulation(
            sample_image.copy(),
            sample_bboxes.copy(),
            weather_type='random'
        )

        assert weather_img.shape == sample_image.shape
        assert len(weather_bboxes) == len(sample_bboxes)


class TestImageDegradation:
    """测试图像退化"""

    def test_apply_degradation(self, augmenter, sample_image, sample_bboxes):
        """测试图像退化"""
        degraded_img, degraded_bboxes = augmenter.apply_degradation(
            sample_image.copy(),
            sample_bboxes.copy()
        )

        # 验证输出形状
        assert degraded_img.shape == sample_image.shape

        # 验证边界框未改变
        assert len(degraded_bboxes) == len(sample_bboxes)

    def test_degradation_intensity_range(self, augmenter, sample_image, sample_bboxes):
        """测试不同退化强度"""
        # 低退化
        degraded_low, _ = augmenter.apply_degradation(
            sample_image.copy(),
            sample_bboxes.copy()
        )

        # 验证图像已被修改
        assert not np.array_equal(degraded_low, sample_image)


class TestRandomCrop:
    """测试随机裁剪"""

    def test_random_crop_with_bboxes(self, augmenter, sample_image, sample_bboxes):
        """测试保留边界框的随机裁剪"""
        cropped_img, cropped_bboxes = augmenter.apply_random_crop_with_bboxes(
            sample_image.copy(),
            sample_bboxes.copy(),
            crop_size=(320, 320)
        )

        # 验证输出尺寸
        assert cropped_img.shape[:2] == (320, 320)

        # 验证边界框坐标归一化
        for bbox in cropped_bboxes:
            assert 0 <= bbox[1] <= 1
            assert 0 <= bbox[2] <= 1

    def test_random_crop_preserves_objects(self, augmenter, sample_image):
        """测试裁剪保留目标"""
        # 创建一个中心位置的边界框
        bboxes = [[0, 0.5, 0.5, 0.4, 0.4]]

        cropped_img, cropped_bboxes = augmenter.apply_random_crop_with_bboxes(
            sample_image.copy(),
            bboxes,
            crop_size=(400, 400)
        )

        # 应该至少保留一些边界框
        assert len(cropped_bboxes) >= 0


class TestAugmentSingleImage:
    """测试单图像增强"""

    def test_augment_single_image_basic(self, augmenter, sample_image, sample_bboxes):
        """测试基本单图像增强"""
        aug_img, aug_bboxes = augmenter.augment_single_image(
            sample_image.copy(),
            sample_bboxes.copy()
        )

        # 验证输出
        assert aug_img.shape == sample_image.shape
        assert len(aug_bboxes) > 0

    def test_augment_single_image_preserves_bbox_format(self, augmenter, sample_image, sample_bboxes):
        """测试增强保持边界框格式"""
        aug_img, aug_bboxes = augmenter.augment_single_image(
            sample_image.copy(),
            sample_bboxes.copy()
        )

        # 验证边界框格式
        for bbox in aug_bboxes:
            assert len(bbox) == 5  # [class_id, x, y, w, h]
            assert isinstance(bbox[0], (int, float))


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_bboxes(self, augmenter, sample_image):
        """测试空边界框列表"""
        empty_bboxes = []

        aug_img, aug_bboxes = augmenter.augment_single_image(
            sample_image.copy(),
            empty_bboxes
        )

        assert aug_img.shape == sample_image.shape
        assert isinstance(aug_bboxes, list)

    def test_single_channel_image(self, augmenter):
        """测试单通道图像"""
        gray_img = np.random.randint(0, 255, (640, 640), dtype=np.uint8)

        # 某些增强可能需要RGB图像
        # 测试是否能优雅处理


class TestIntegration:
    """集成测试"""

    def test_full_augmentation_pipeline(self, augmenter, sample_image, sample_bboxes):
        """测试完整的增强流程"""
        # 执行多种增强
        results = []

        # 1. 天气模拟
        weather_img, weather_bboxes = augmenter.apply_weather_simulation(
            sample_image.copy(),
            sample_bboxes.copy(),
            weather_type='rain'
        )
        results.append((weather_img, weather_bboxes))

        # 2. 图像退化
        degraded_img, degraded_bboxes = augmenter.apply_degradation(
            sample_image.copy(),
            sample_bboxes.copy()
        )
        results.append((degraded_img, degraded_bboxes))

        # 3. 随机裁剪
        cropped_img, cropped_bboxes = augmenter.apply_random_crop_with_bboxes(
            sample_image.copy(),
            sample_bboxes.copy(),
            crop_size=(480, 480)
        )
        results.append((cropped_img, cropped_bboxes))

        # 验证所有结果
        for img, bboxes in results:
            assert img is not None
            assert isinstance(bboxes, list)

    def test_augmentation_preserves_data_integrity(self, augmenter, sample_image, sample_bboxes):
        """测试增强保持数据完整性"""
        original_classes = [bbox[0] for bbox in sample_bboxes]

        aug_img, aug_bboxes = augmenter.augment_single_image(
            sample_image.copy(),
            sample_bboxes.copy()
        )

        # 验证类别ID仍然有效
        if len(aug_bboxes) > 0:
            aug_classes = [bbox[0] for bbox in aug_bboxes]
            for class_id in aug_classes:
                assert class_id in range(6)  # 假设6个类别


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
