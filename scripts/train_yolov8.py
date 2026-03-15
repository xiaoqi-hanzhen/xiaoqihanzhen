"""
轻量训练入口，便于命令行调用。
"""
import argparse
from training.train import YOLOTrainer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="models/configs/yolov8_drone_config.yaml")
    parser.add_argument("--data", default="data/data.yaml")
    parser.add_argument("--model-size", default="s", choices=["n", "s", "m", "l", "x"])
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    trainer = YOLOTrainer(args.config, args.data)
    trainer.setup_model(args.model_size)
    trainer.train(resume=args.resume)
    trainer.validate()


if __name__ == "__main__":
    main()
