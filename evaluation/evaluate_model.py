"""
统一评估入口：加载权重，对 test 集计算指标并生成可视化。
"""
import argparse
from pathlib import Path
from ultralytics import YOLO


def evaluate(weights: str, data_yaml: str, imgsz: int = 640, save_dir: str = "evaluation/outputs"):
    model = YOLO(weights)
    metrics = model.val(data=data_yaml, imgsz=imgsz, split="test", project=save_dir, name="latest_eval", save_json=True, save_hybrid=True)
    print(f"mAP50: {metrics.box.map50:.4f}, mAP50-95: {metrics.box.map:.4f}")
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Evaluate trained YOLO model")
    parser.add_argument("--weights", required=True, help="path to model weights")
    parser.add_argument("--data", default="data/data.yaml")
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()
    evaluate(args.weights, args.data, args.imgsz)


if __name__ == "__main__":
    main()
