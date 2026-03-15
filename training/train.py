"""
YOLO训练脚本
专门优化用于无人机航拍异物检测
"""

import os
import torch
import yaml
import argparse
from pathlib import Path
from ultralytics import YOLO
import wandb
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YOLOTrainer:
    """YOLO训练器类"""
    
    def __init__(self, config_path: str, data_path: str):
        """
        初始化训练器
        
        Args:
            config_path: 配置文件路径
            data_path: 数据配置文件路径
        """
        self.config_path = Path(config_path)
        self.data_path = Path(data_path)
        
        # 加载配置
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 设置设备
        self.device = self._setup_device()
        
        # 创建输出目录
        self.output_dir = Path(f"runs/train/{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化WandB（可选）
        self._init_wandb()
    
    def _setup_device(self) -> str:
        """设置训练设备"""
        if torch.cuda.is_available():
            device = "cuda:0"
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            logger.info(f"使用GPU: {gpu_name} ({gpu_memory:.1f}GB)")
            
            # RTX 3070 Ti特殊优化
            if "3070" in gpu_name or gpu_memory <= 8:
                logger.info("检测到RTX 3070 Ti，应用显存优化设置")
                torch.cuda.empty_cache()
                
                # 设置显存增长（避免一次性分配）
                if hasattr(torch.cuda, 'memory_allocated'):
                    torch.cuda.empty_cache()
            
            return device
        else:
            logger.warning("未检测到GPU，将使用CPU训练（速度较慢）")
            return "cpu"
    
    def _init_wandb(self):
        """初始化WandB日志记录"""
        try:
            wandb.init(
                project="yolo-drone-foreign-object-detection",
                name=f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                config=self.config
            )
            logger.info("WandB日志记录已启动")
        except Exception as e:
            logger.warning(f"WandB初始化失败: {e}")
    
    def setup_model(self, model_size: str = "s"):
        """
        设置YOLO模型
        
        Args:
            model_size: 模型大小 (n, s, m, l, x)
        """
        model_name = f"yolov8{model_size}.pt"
        logger.info(f"加载预训练模型: {model_name}")
        
        try:
            self.model = YOLO(model_name)
            
            # 更新模型配置
            self.model.overrides.update({
                'data': str(self.data_path),
                'epochs': self.config['train']['epochs'],
                'batch': self.config['train']['batch'],
                'imgsz': self.config['model']['imgsz'],
                'device': self.device,
                'workers': self.config['train']['workers'],
                'cache': self.config['train']['cache'],
                'amp': self.config['performance']['amp'],
                'exist_ok': False,
                'project': str(self.output_dir.parent),
                'name': self.output_dir.name
            })
            
            logger.info("模型配置完成")
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def train(self, resume: bool = False):
        """
        开始训练
        
        Args:
            resume: 是否从上次检查点继续训练
        """
        logger.info("开始训练...")
        
        try:
            # 训练参数
            train_args = {
                'data': str(self.data_path),
                'epochs': self.config['train']['epochs'],
                'batch': self.config['train']['batch'],
                'imgsz': self.config['model']['imgsz'],
                'device': self.device,
                'workers': self.config['train']['workers'],
                'cache': self.config['train']['cache'],
                'amp': self.config['performance']['amp'],
                'resume': resume,
                'exist_ok': False,
                'project': str(self.output_dir.parent),
                'name': self.output_dir.name
            }
            
            # 小目标检测优化
            if self.config.get('small_object', {}):
                small_obj_config = self.config['small_object']
                train_args.update({
                    'multi_scale': small_obj_config.get('multi_scale', True),
                    'anchor_t': small_obj_config.get('anchor_t', 4.0),
                    'label_smoothing': small_obj_config.get('label_smoothing', 0.1)
                })
            
            # 开始训练
            results = self.model.train(**train_args)
            
            logger.info("训练完成！")
            
            # 保存训练结果
            self._save_training_results(results)
            
            return results
            
        except Exception as e:
            logger.error(f"训练失败: {e}")
            raise
    
    def _save_training_results(self, results):
        """保存训练结果"""
        results_file = self.output_dir / "training_results.yaml"
        
        # 提取关键指标
        training_info = {
            'best fitness': float(results.fitness) if hasattr(results, 'fitness') else 0.0,
            'best epoch': int(results.epoch) if hasattr(results, 'epoch') else 0,
            'mAP@0.5': float(results.results_dict.get('metrics/mAP_0.5', 0)) if hasattr(results, 'results_dict') else 0.0,
            'mAP@0.5:0.95': float(results.results_dict.get('metrics/mAP_0.5:0.95', 0)) if hasattr(results, 'results_dict') else 0.0,
            'precision': float(results.results_dict.get('metrics/precision', 0)) if hasattr(results, 'results_dict') else 0.0,
            'recall': float(results.results_dict.get('metrics/recall', 0)) if hasattr(results, 'results_dict') else 0.0
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            yaml.dump(training_info, f, allow_unicode=True)
        
        logger.info(f"训练结果已保存: {results_file}")
    
    def validate(self):
        """验证模型"""
        logger.info("开始模型验证...")
        
        try:
            # 在验证集上评估
            metrics = self.model.val()
            
            logger.info("验证完成！")
            logger.info(f"mAP@0.5: {metrics.box.map50:.4f}")
            logger.info(f"mAP@0.5:0.95: {metrics.box.map:.4f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"验证失败: {e}")
            raise
    
    def export_model(self, format: str = "onnx"):
        """
        导出模型
        
        Args:
            format: 导出格式 (onnx, torchscript, openvino, engine, coreml, saved_model, pb, tflite, edgetpu, tfjs)
        """
        logger.info(f"导出模型为 {format} 格式...")
        
        try:
            # 导出模型
            exported_model = self.model.export(format=format)
            
            logger.info(f"模型导出完成: {exported_model}")
            return exported_model
            
        except Exception as e:
            logger.error(f"模型导出失败: {e}")
            raise

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="YOLO无人机异物检测训练脚本")
    parser.add_argument("--config", type=str, default="models/configs/yolov8_drone_config.yaml",
                       help="配置文件路径")
    parser.add_argument("--data", type=str, default="data/data.yaml",
                       help="数据配置文件路径")
    parser.add_argument("--model-size", type=str, default="s",
                       choices=["n", "s", "m", "l", "x"], help="模型大小")
    parser.add_argument("--resume", action="store_true",
                       help="从上次检查点继续训练")
    parser.add_argument("--validate", action="store_true",
                       help="只进行验证")
    parser.add_argument("--export", type=str, default=None,
                       choices=["onnx", "torchscript", "openvino", "engine", "coreml",
                               "saved_model", "pb", "tflite", "edgetpu", "tfjs"],
                       help="导出模型格式")
    
    args = parser.parse_args()
    
    # 创建训练器
    trainer = YOLOTrainer(args.config, args.data)
    
    if args.validate:
        # 只进行验证
        trainer.setup_model(args.model_size)
        trainer.validate()
    elif args.export:
        # 导出模型
        trainer.setup_model(args.model_size)
        trainer.export_model(args.export)
    else:
        # 训练模型
        trainer.setup_model(args.model_size)
        trainer.train(resume=args.resume)
        
        # 训练完成后验证
        trainer.validate()

if __name__ == "__main__":
    main()