"""
独立验证入口，读取同一 config/data 配置，便于与 train 解耦。
"""
import argparse
from pathlib import Path
from ultralytics import YOLO
import yaml


def run_validation(config_path: str, data_path: str, model_size: str = "s"):
    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    model_name = f"yolov8{model_size}.pt"
    model = YOLO(model_name)

    overrides = {
        "data": str(data_path),
        "imgsz": cfg["model"]["imgsz"],
        "batch": cfg["train"]["batch"],
        "device": 0,
        "workers": cfg["train"]["workers"],
        "cache": cfg["train"]["cache"],
        "amp": cfg["performance"]["amp"],
    }

    metrics = model.val(**overrides)
    print(f"mAP50: {metrics.box.map50:.4f}, mAP50-95: {metrics.box.map:.4f}")
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Validate YOLO model")
    parser.add_argument("--config", default="models/configs/yolov8_drone_config.yaml")
    parser.add_argument("--data", default="data/data.yaml")
    parser.add_argument("--model-size", default="s", choices=["n", "s", "m", "l", "x"])
    args = parser.parse_args()

    run_validation(args.config, args.data, args.model_size)


if __name__ == "__main__":
    main()
