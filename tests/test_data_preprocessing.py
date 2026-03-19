"""
utils/data_preprocessing.py模块的全面单元测试
测试图像质量检查、去重、标准化、标注转换等功能
"""
import pytest
import numpy as np
import cv2
import tempfile
import shutil
import sys
from pathlib import Path
from PIL import Image

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_preprocessing import DataPreprocessor


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # 清理
    shutil.rmtree(temp_dir)


@pytest.fixture
def preprocessor(temp_data_dir):
    """创建DataPreprocessor实例"""
    return DataPreprocessor(str(temp_data_dir))


@pytest.fixture
def sample_image():
    """创建测试用的样本图像"""
    img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    return img


class TestDataPreprocessorInit:
    """测试DataPreprocessor初始化"""

    def test_init_creates_directories(self, temp_data_dir):
        """测试初始化时创建必要的目录"""
        preprocessor = DataPreprocessor(str(temp_data_dir))

        assert preprocessor.processed_dir.exists()
        assert (preprocessor.processed_dir / "images").exists()
        assert (preprocessor.processed_dir / "labels").exists()

    def test_init_with_existing_directories(self, temp_data_dir):
        """测试已存在目录时的初始化"""
        # 预先创建目录
        processed_dir = temp_data_dir / "processed"
        processed_dir.mkdir(parents=True)

        preprocessor = DataPreprocessor(str(temp_data_dir))

        # 不应该报错，目录应该存在
        assert preprocessor.processed_dir.exists()


class TestImageQualityCheck:
    """测试图像质量检查功能"""

    def test_check_valid_image(self, preprocessor, temp_data_dir, sample_image):
        """测试有效图像的质量检查"""
        # 创建并保存有效图像
        img_path = temp_data_dir / "test_image.jpg"
        cv2.imwrite(str(img_path), sample_image)

        result = preprocessor.check_image_quality(img_path)

        assert result["valid"] is True
        assert "resolution" in result
        assert "blur_score" in result
        assert "brightness" in result

    def test_check_small_image(self, preprocessor, temp_data_dir):
        """测试尺寸过小的图像"""
        # 创建小尺寸图像
        small_img = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        img_path = temp_data_dir / "small_image.jpg"
        cv2.imwrite(str(img_path), small_img)

        result = preprocessor.check_image_quality(img_path)

        assert result["valid"] is False
        assert "尺寸过小" in result["reason"]

    def test_check_blurry_image(self, preprocessor, temp_data_dir):
        """测试模糊图像检测"""
        # 创建模糊图像（低方差）
        blurry_img = np.ones((480, 640, 3), dtype=np.uint8) * 128
        img_path = temp_data_dir / "blurry_image.jpg"
        cv2.imwrite(str(img_path), blurry_img)

        result = preprocessor.check_image_quality(img_path)

        assert result["valid"] is False
        assert "模糊" in result["reason"]

    def test_check_overexposed_image(self, preprocessor, temp_data_dir):
        """测试过曝图像检测"""
        # 创建过曝图像
        overexposed_img = np.ones((480, 640, 3), dtype=np.uint8) * 255
        img_path = temp_data_dir / "overexposed_image.jpg"
        cv2.imwrite(str(img_path), overexposed_img)

        result = preprocessor.check_image_quality(img_path)

        assert result["valid"] is False
        assert "曝光异常" in result["reason"]

    def test_check_underexposed_image(self, preprocessor, temp_data_dir):
        """测试欠曝图像检测"""
        # 创建欠曝图像
        underexposed_img = np.ones((480, 640, 3), dtype=np.uint8) * 5
        img_path = temp_data_dir / "underexposed_image.jpg"
        cv2.imwrite(str(img_path), underexposed_img)

        result = preprocessor.check_image_quality(img_path)

        assert result["valid"] is False
        assert "曝光异常" in result["reason"]

    def test_check_nonexistent_image(self, preprocessor, temp_data_dir):
        """测试不存在的图像文件"""
        img_path = temp_data_dir / "nonexistent.jpg"

        result = preprocessor.check_image_quality(img_path)

        assert result["valid"] is False
        assert "无法读取" in result["reason"]


class TestHashFunctions:
    """测试图像哈希和比较功能"""

    def test_calculate_hash_consistency(self, preprocessor):
        """测试哈希计算的一致性"""
        img1 = Image.new('RGB', (100, 100), color='red')
        img2 = Image.new('RGB', (100, 100), color='red')

        hash1 = preprocessor._calculate_image_hash(img1)
        hash2 = preprocessor._calculate_image_hash(img2)

        # 相同图像应该产生相同哈希
        assert np.array_equal(hash1, hash2)

    def test_calculate_hash_different_images(self, preprocessor):
        """测试不同图像的哈希"""
        img1 = Image.new('RGB', (100, 100), color='red')
        img2 = Image.new('RGB', (100, 100), color='blue')

        hash1 = preprocessor._calculate_image_hash(img1)
        hash2 = preprocessor._calculate_image_hash(img2)

        # 不同图像应该产生不同哈希
        assert not np.array_equal(hash1, hash2)

    def test_compare_hashes_identical(self, preprocessor):
        """测试完全相同哈希的比较"""
        img = Image.new('RGB', (100, 100), color='red')
        hash1 = preprocessor._calculate_image_hash(img)
        hash2 = preprocessor._calculate_image_hash(img)

        similarity = preprocessor._compare_hashes(hash1, hash2)

        assert abs(similarity - 1.0) < 1e-6

    def test_compare_hashes_different(self, preprocessor):
        """测试不同哈希的比较"""
        img1 = Image.new('RGB', (100, 100), color='red')
        img2 = Image.new('RGB', (100, 100), color='blue')

        hash1 = preprocessor._calculate_image_hash(img1)
        hash2 = preprocessor._calculate_image_hash(img2)

        similarity = preprocessor._compare_hashes(hash1, hash2)

        assert 0.0 <= similarity < 1.0

    def test_compare_hashes_different_length(self, preprocessor):
        """测试不同长度哈希的比较"""
        hash1 = np.array([True, False, True])
        hash2 = np.array([True, False])

        similarity = preprocessor._compare_hashes(hash1, hash2)

        assert similarity == 0.0


class TestRemoveDuplicates:
    """测试图像去重功能"""

    def test_remove_duplicates_no_duplicates(self, preprocessor, temp_data_dir):
        """测试无重复图像的情况"""
        # 创建不同的图像
        for i in range(3):
            img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            img_path = temp_data_dir / f"image_{i}.jpg"
            cv2.imwrite(str(img_path), img)

        removed = preprocessor.remove_duplicates(temp_data_dir, hash_threshold=0.95)

        assert len(removed) == 0

    def test_remove_duplicates_with_duplicates(self, preprocessor, temp_data_dir):
        """测试有重复图像的情况"""
        # 创建相同的图像
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        for i in range(3):
            img_path = temp_data_dir / f"image_{i}.jpg"
            cv2.imwrite(str(img_path), img)

        removed = preprocessor.remove_duplicates(temp_data_dir, hash_threshold=0.95)

        # 应该移除2个重复图像
        assert len(removed) == 2


class TestStandardizeImages:
    """测试图像标准化功能"""

    def test_standardize_images_resize(self, preprocessor, temp_data_dir, sample_image):
        """测试图像尺寸标准化"""
        # 创建不同尺寸的图像
        img_path = temp_data_dir / "test_image.jpg"
        cv2.imwrite(str(img_path), sample_image)

        preprocessor.standardize_images(temp_data_dir, output_size=(640, 640))

        # 检查输出图像
        output_dir = preprocessor.processed_dir / "images"
        output_images = list(output_dir.glob("*.jpg"))

        assert len(output_images) == 1

        # 验证尺寸
        result_img = cv2.imread(str(output_images[0]))
        assert result_img.shape[:2] == (640, 640)

    def test_standardize_images_quality(self, preprocessor, temp_data_dir, sample_image):
        """测试图像质量设置"""
        img_path = temp_data_dir / "test_image.jpg"
        cv2.imwrite(str(img_path), sample_image)

        preprocessor.standardize_images(temp_data_dir, output_size=(640, 640), quality=90)

        # 验证输出文件存在
        output_dir = preprocessor.processed_dir / "images"
        output_images = list(output_dir.glob("*.jpg"))

        assert len(output_images) == 1


class TestGetClassId:
    """测试类别ID映射"""

    def test_get_class_id_valid_classes(self, preprocessor):
        """测试有效类别的ID映射"""
        assert preprocessor._get_class_id('kite') == 0
        assert preprocessor._get_class_id('plastic_film') == 1
        assert preprocessor._get_class_id('color_cloth') == 2
        assert preprocessor._get_class_id('balloon') == 3
        assert preprocessor._get_class_id('bird_nest') == 4
        assert preprocessor._get_class_id('foreign_object') == 5

    def test_get_class_id_case_insensitive(self, preprocessor):
        """测试大小写不敏感"""
        assert preprocessor._get_class_id('KITE') == 0
        assert preprocessor._get_class_id('Kite') == 0
        assert preprocessor._get_class_id('kItE') == 0

    def test_get_class_id_unknown_class(self, preprocessor):
        """测试未知类别"""
        # 未知类别应该映射到foreign_object (5)
        assert preprocessor._get_class_id('unknown_class') == 5


class TestCreateDataYaml:
    """测试数据配置文件创建"""

    def test_create_data_yaml(self, preprocessor, temp_data_dir):
        """测试YAML配置文件创建"""
        class_names = ['kite', 'plastic_film', 'color_cloth',
                      'balloon', 'bird_nest', 'foreign_object']

        preprocessor.create_data_yaml(
            class_names,
            train_path='train/images',
            val_path='val/images',
            test_path='test/images'
        )

        yaml_path = temp_data_dir / "data.yaml"
        assert yaml_path.exists()

        # 读取并验证内容
        import yaml
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        assert config['nc'] == 6
        assert config['names'] == class_names
        assert 'train' in config
        assert 'val' in config
        assert 'test' in config


class TestXMLToYoloConversion:
    """测试XML到YOLO格式转换"""

    def test_convert_xml_to_yolo(self, preprocessor, temp_data_dir):
        """测试XML标注转换"""
        # 创建示例XML文件
        xml_content = """<?xml version="1.0"?>
<annotation>
    <size>
        <width>640</width>
        <height>480</height>
    </size>
    <object>
        <name>kite</name>
        <bndbox>
            <xmin>100</xmin>
            <ymin>100</ymin>
            <xmax>200</xmax>
            <ymax>200</ymax>
        </bndbox>
    </object>
</annotation>
"""
        xml_dir = temp_data_dir / "annotations"
        xml_dir.mkdir(exist_ok=True)
        xml_path = xml_dir / "test.xml"

        with open(xml_path, 'w') as f:
            f.write(xml_content)

        output_dir = temp_data_dir / "labels"
        output_dir.mkdir(exist_ok=True)

        preprocessor._convert_xml_to_yolo(xml_dir, output_dir)

        # 验证输出
        txt_path = output_dir / "test.txt"
        assert txt_path.exists()

        with open(txt_path, 'r') as f:
            content = f.read().strip()

        # 验证YOLO格式 (class_id x_center y_center width height)
        parts = content.split()
        assert len(parts) == 5
        assert parts[0] == '0'  # kite的class_id

        # 验证坐标归一化
        x_center, y_center, width, height = map(float, parts[1:])
        assert 0 <= x_center <= 1
        assert 0 <= y_center <= 1
        assert 0 <= width <= 1
        assert 0 <= height <= 1


class TestIntegration:
    """集成测试"""

    def test_full_preprocessing_workflow(self, temp_data_dir):
        """测试完整的预处理流程"""
        # 创建测试数据结构
        raw_dir = temp_data_dir / "raw"
        raw_dir.mkdir(exist_ok=True)

        # 创建测试图像
        for i in range(3):
            img = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
            img_path = raw_dir / f"image_{i}.jpg"
            cv2.imwrite(str(img_path), img)

        # 初始化预处理器
        preprocessor = DataPreprocessor(str(temp_data_dir))

        # 执行质量检查
        valid_count = 0
        for img_path in raw_dir.glob("*.jpg"):
            result = preprocessor.check_image_quality(img_path)
            if result["valid"]:
                valid_count += 1

        assert valid_count > 0

        # 执行标准化
        preprocessor.standardize_images(raw_dir, output_size=(640, 640))

        # 验证输出
        output_dir = preprocessor.processed_dir / "images"
        output_images = list(output_dir.glob("*.jpg"))
        assert len(output_images) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
