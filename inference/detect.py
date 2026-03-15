import argparse
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="Single-image/dir detection")
    parser.add_argument("--weights", required=True)
    parser.add_argument("--source", default="data/splits/test")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.25)
    args = parser.parse_args()

    model = YOLO(args.weights)
    model.predict(source=args.source, imgsz=args.imgsz, conf=args.conf, save=True, project="inference/runs", name="detect")


if __name__ == "__main__":
    main()
