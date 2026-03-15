"""
将 VOC/COCO 标注转为 YOLO txt，并校验类别表。
"""
import argparse
from pathlib import Path
import json
import xml.etree.ElementTree as ET


def convert_voc(voc_dir: Path, out_dir: Path, class_names):
    out_dir.mkdir(parents=True, exist_ok=True)
    for xml_file in voc_dir.glob("*.xml"):
        tree = ET.parse(xml_file)
        root = tree.getroot()
        size = root.find("size")
        w = float(size.find("width").text)
        h = float(size.find("height").text)
        lines = []
        for obj in root.findall("object"):
            cls = obj.find("name").text
            if cls not in class_names:
                raise ValueError(f"Unknown class {cls} in {xml_file}")
            cls_id = class_names.index(cls)
            bnd = obj.find("bndbox")
            x1, y1 = float(bnd.find("xmin").text), float(bnd.find("ymin").text)
            x2, y2 = float(bnd.find("xmax").text), float(bnd.find("ymax").text)
            xc = (x1 + x2) / (2 * w)
            yc = (y1 + y2) / (2 * h)
            bw = (x2 - x1) / w
            bh = (y2 - y1) / h
            lines.append(f"{cls_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")
        (out_dir / (xml_file.stem + ".txt")).write_text("\n".join(lines), encoding="utf-8")


def convert_coco(coco_json: Path, out_dir: Path, image_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(coco_json.read_text(encoding="utf-8"))
    id_to_filename = {img["id"]: img["file_name"] for img in data["images"]}
    cat_map = {c["id"]: c["name"] for c in data["categories"]}
    grouped = {}
    for ann in data["annotations"]:
        grouped.setdefault(ann["image_id"], []).append(ann)
    for img_id, anns in grouped.items():
        filename = id_to_filename[img_id]
        w = next(img["width"] for img in data["images"] if img["id"] == img_id)
        h = next(img["height"] for img in data["images"] if img["id"] == img_id)
        lines = []
        for ann in anns:
            cls = cat_map[ann["category_id"]]
            cls_id = list(cat_map.values()).index(cls)
            x, y, bw, bh = ann["bbox"]
            xc = (x + bw / 2) / w
            yc = (y + bh / 2) / h
            lines.append(f"{cls_id} {xc:.6f} {yc:.6f} {bw / w:.6f} {bh / h:.6f}")
        (out_dir / f"{Path(filename).stem}.txt").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--voc-dir", type=Path, help="VOC xml directory")
    parser.add_argument("--coco-json", type=Path, help="COCO json path")
    parser.add_argument("--image-dir", type=Path, help="COCO image dir")
    parser.add_argument("--out", type=Path, default=Path("data/annotations"))
    parser.add_argument("--classes", nargs="+", default=["kite", "plastic_film", "color_cloth", "balloon", "bird_nest", "foreign_object"])
    args = parser.parse_args()

    if args.voc_dir:
        convert_voc(args.voc_dir, args.out, args.classes)
    if args.coco_json and args.image_dir:
        convert_coco(args.coco_json, args.out, args.image_dir)


if __name__ == "__main__":
    main()
