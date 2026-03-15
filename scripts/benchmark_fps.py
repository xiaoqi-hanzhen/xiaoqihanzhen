"""
简单的推理 FPS 基准测试脚本。
使用指定权重在一批图片上测时间，计算平均 FPS。
"""
import argparse
import time
from pathlib import Path
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="Benchmark inference FPS")
    parser.add_argument("--weights", required=True)
    parser.add_argument("--source", default="data/splits/test")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--warmup", type=int, default=2, help="warmup iterations to skip timing")
    args = parser.parse_args()

    model = YOLO(args.weights)
    # warmup
    model.predict(source=args.source, imgsz=args.imgsz, conf=args.conf, verbose=False)

    start = time.time()
    results = model.predict(source=args.source, imgsz=args.imgsz, conf=args.conf, verbose=False)
    elapsed = time.time() - start
    n = len(results)
    fps = n / elapsed if elapsed > 0 else 0
    print(f"Inferred {n} images in {elapsed:.2f}s, FPS={fps:.2f} (imgsz={args.imgsz}, conf={args.conf})")


if __name__ == "__main__":
    main()
