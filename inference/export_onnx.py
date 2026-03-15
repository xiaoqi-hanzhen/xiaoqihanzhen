import argparse
from ultralytics import YOLO


def export(weights: str, opset: int = 12, dynamic: bool = False):
    model = YOLO(weights)
    model.export(format="onnx", opset=opset, dynamic=dynamic)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export YOLO weights to ONNX")
    parser.add_argument("--weights", required=True)
    parser.add_argument("--opset", type=int, default=12)
    parser.add_argument("--dynamic", action="store_true")
    args = parser.parse_args()
    export(args.weights, args.opset, args.dynamic)
