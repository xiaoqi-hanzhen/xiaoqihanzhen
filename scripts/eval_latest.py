"""
自动查找最新的训练输出并运行评估
支持更好的路径检测和错误处理
"""
import argparse
import logging
from pathlib import Path
from datetime import datetime
from evaluation.evaluate_model import evaluate

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_latest_weights(runs_dir: str, weight_name: str = "best.pt") -> Path:
    """
    查找最新的模型权重文件

    Args:
        runs_dir: 训练输出目录
        weight_name: 权重文件名，默认为"best.pt"

    Returns:
        最新权重文件的路径

    Raises:
        FileNotFoundError: 未找到任何训练输出或权重文件
    """
    runs_path = Path(runs_dir)

    if not runs_path.exists():
        raise FileNotFoundError(f"训练输出目录不存在: {runs_path}")

    # 尝试多种可能的目录结构
    possible_patterns = [
        "*/*",  # training/runs/exp1/
        "*",    # training/runs/exp1 (如果runs本身就是实验目录)
        "*/train",  # training/runs/exp1/train
    ]

    all_runs = []
    for pattern in possible_patterns:
        runs = list(runs_path.glob(pattern))
        all_runs.extend([r for r in runs if r.is_dir()])

    if not all_runs:
        raise FileNotFoundError(f"在 {runs_path} 中未找到任何训练输出目录")

    # 按修改时间排序，获取最新的
    all_runs = sorted(all_runs, key=lambda p: p.stat().st_mtime, reverse=True)

    logger.info(f"找到 {len(all_runs)} 个训练输出目录")

    # 在最新的几个目录中查找权重文件
    for run_dir in all_runs[:5]:  # 检查最新的5个目录
        # 尝试多个可能的权重文件位置
        possible_weight_paths = [
            run_dir / "weights" / weight_name,
            run_dir / weight_name,
            run_dir / "best.pt",
            run_dir / "last.pt",
        ]

        for weight_path in possible_weight_paths:
            if weight_path.exists():
                logger.info(f"找到权重文件: {weight_path}")
                logger.info(f"  训练目录: {run_dir}")
                logger.info(f"  最后修改时间: {datetime.fromtimestamp(weight_path.stat().st_mtime)}")
                return weight_path

    raise FileNotFoundError(
        f"在最新的训练输出中未找到权重文件。\n"
        f"检查的目录: {', '.join(str(r) for r in all_runs[:5])}\n"
        f"查找的权重文件名: {weight_name}, best.pt, last.pt"
    )


def verify_data_yaml(data_path: str) -> Path:
    """
    验证数据配置文件是否存在

    Args:
        data_path: 数据配置文件路径

    Returns:
        验证后的Path对象

    Raises:
        FileNotFoundError: 配置文件不存在
    """
    data_file = Path(data_path)

    if not data_file.exists():
        # 尝试查找可能的data.yaml位置
        possible_locations = [
            Path("data/data.yaml"),
            Path("data/splits/data.yaml"),
            Path("data.yaml"),
        ]

        for loc in possible_locations:
            if loc.exists():
                logger.warning(f"指定的配置文件不存在，使用: {loc}")
                return loc

        raise FileNotFoundError(
            f"数据配置文件不存在: {data_path}\n"
            f"也未在以下位置找到:\n" +
            "\n".join(f"  - {loc}" for loc in possible_locations)
        )

    return data_file


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="自动评估最新训练的模型",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认参数
  python scripts/eval_latest.py

  # 指定训练输出目录和数据配置
  python scripts/eval_latest.py --runs-dir training/runs --data data/data.yaml

  # 评估last.pt而不是best.pt
  python scripts/eval_latest.py --weight-name last.pt

  # 使用不同的图像尺寸
  python scripts/eval_latest.py --imgsz 1280
        """
    )
    parser.add_argument(
        "--runs-dir",
        default="training/runs",
        help="训练输出目录 (默认: training/runs)"
    )
    parser.add_argument(
        "--data",
        default="data/data.yaml",
        help="数据配置文件路径 (默认: data/data.yaml)"
    )
    parser.add_argument(
        "--weight-name",
        default="best.pt",
        help="权重文件名 (默认: best.pt，可选: last.pt)"
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="评估时的图像尺寸 (默认: 640)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="评估时的批次大小 (默认: 16)"
    )
    parser.add_argument(
        "--conf-thres",
        type=float,
        default=0.001,
        help="置信度阈值 (默认: 0.001)"
    )
    parser.add_argument(
        "--iou-thres",
        type=float,
        default=0.6,
        help="IoU阈值用于NMS (默认: 0.6)"
    )
    args = parser.parse_args()

    try:
        logger.info("=" * 60)
        logger.info("开始自动评估最新模型")
        logger.info("=" * 60)

        # 1. 查找最新的权重文件
        logger.info(f"\n步骤 1/3: 在 {args.runs_dir} 中查找最新的权重文件...")
        weights_path = find_latest_weights(args.runs_dir, args.weight_name)

        # 2. 验证数据配置文件
        logger.info(f"\n步骤 2/3: 验证数据配置文件...")
        data_path = verify_data_yaml(args.data)
        logger.info(f"使用数据配置: {data_path}")

        # 3. 执行评估
        logger.info(f"\n步骤 3/3: 开始评估模型...")
        logger.info(f"  权重文件: {weights_path}")
        logger.info(f"  数据配置: {data_path}")
        logger.info(f"  图像尺寸: {args.imgsz}")
        logger.info(f"  批次大小: {args.batch_size}")
        logger.info(f"  置信度阈值: {args.conf_thres}")
        logger.info(f"  IoU阈值: {args.iou_thres}")
        logger.info("")

        evaluate(
            weights=str(weights_path),
            data=str(data_path),
            imgsz=args.imgsz,
            batch=args.batch_size,
            conf=args.conf_thres,
            iou=args.iou_thres
        )

        logger.info("\n" + "=" * 60)
        logger.info("✅ 评估完成！")
        logger.info("=" * 60)

    except FileNotFoundError as e:
        logger.error(f"\n❌ 错误: {e}")
        logger.error("\n请确保:")
        logger.error("  1. 已经完成至少一次训练")
        logger.error("  2. 训练输出目录正确")
        logger.error("  3. 数据配置文件存在")
        return 1

    except Exception as e:
        logger.error(f"\n❌ 评估过程中发生错误: {e}")
        logger.exception("详细错误信息:")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
