import argparse
from pathlib import Path
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="Batch inference on a folder")
    parser.add_argument("--weights", required=True)
    parser.add_argument("--source", default="data/splits/test")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.25)
    args = parser.parse_args()

    model = YOLO(args.weights)
    outputs = model.predict(source=args.source, imgsz=args.imgsz, conf=args.conf, save=True, save_txt=True, project="inference/runs", name="batch")
    print(f"Processed {len(outputs)} images. Results in inference/runs/batch/")


if __name__ == "__main__":
    main()
