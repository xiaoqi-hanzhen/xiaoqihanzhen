"""
简单的网格/随机搜索入口，用于批量尝试 batch / lr / img_size 等。
"""
import itertools
import random
from pathlib import Path
import yaml
from ultralytics import YOLO


def grid_search(config_path: str, data_path: str, search_space: dict, max_trials: int = None):
    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    keys = list(search_space.keys())
    values = list(search_space.values())
    combos = list(itertools.product(*values))
    if max_trials:
        random.shuffle(combos)
        combos = combos[:max_trials]

    results = []
    for combo in combos:
        params = dict(zip(keys, combo))
        run_name = "_".join(f"{k}{v}" for k, v in params.items())
        model = YOLO(f"yolov8{cfg['model'].get('size', 's')}.pt")
        overrides = {
            "data": str(data_path),
            "epochs": cfg["train"]["epochs"],
            "imgsz": cfg["model"]["imgsz"],
            "batch": params.get("batch", cfg["train"]["batch"]),
            "lr0": params.get("lr0", cfg["train"].get("lr0", 0.01)),
            "device": 0,
            "workers": cfg["train"]["workers"],
            "cache": cfg["train"]["cache"],
            "project": "training/runs",
            "name": f"tune_{run_name}",
        }
        metrics = model.train(**overrides)
        results.append((params, float(metrics.fitness) if hasattr(metrics, "fitness") else None))
    return results


if __name__ == "__main__":
    space = {
        "batch": [4, 8, 12],
        "lr0": [0.01, 0.005],
    }
    grid_search("models/configs/yolov8_drone_config.yaml", "data/data.yaml", space, max_trials=4)
