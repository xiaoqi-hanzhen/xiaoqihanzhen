"""
查找最新的训练输出并运行评估。
"""
import argparse
from pathlib import Path
from evaluation.evaluate_model import evaluate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-dir", default="training/runs")
    parser.add_argument("--data", default="data/data.yaml")
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()

    runs = sorted(Path(args.runs_dir).glob("*/*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not runs:
        raise SystemExit("No runs found.")
    latest = runs[0]
    weights = latest / "weights" / "best.pt"
    if not weights.exists():
        raise SystemExit(f"No weights found at {weights}")
    evaluate(str(weights), args.data, args.imgsz)


if __name__ == "__main__":
    main()
