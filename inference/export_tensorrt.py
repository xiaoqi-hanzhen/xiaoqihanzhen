import argparse
from ultralytics import YOLO


def export(weights: str, half: bool = True, device: int = 0):
    model = YOLO(weights)
    model.export(format="engine", device=device, half=half, simplify=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export YOLO weights to TensorRT engine")
    parser.add_argument("--weights", required=True)
    parser.add_argument("--fp32", action="store_true", help="use FP32 instead of FP16")
    parser.add_argument("--device", type=int, default=0)
    args = parser.parse_args()
    export(args.weights, half=not args.fp32, device=args.device)
