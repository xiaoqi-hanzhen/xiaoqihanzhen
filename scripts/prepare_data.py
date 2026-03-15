"""
一键数据清洗 + 划分入口。
"""
import argparse
from pathlib import Path
from utils import data_preprocessing


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/annotations")
    parser.add_argument("--output", default="data/processed")
    parser.add_argument("--splits", default="data/splits")
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    args = parser.parse_args()

    data_preprocessing.clean_and_split(
        input_dir=args.input,
        processed_dir=args.output,
        splits_dir=args.splits,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
    )


if __name__ == "__main__":
    main()
