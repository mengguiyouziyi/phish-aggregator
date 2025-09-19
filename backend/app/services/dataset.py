from __future__ import annotations
from pathlib import Path
import csv
from typing import List, Tuple
from ..config import DATASETS_DIR

def load_sample() -> Tuple[list[str], list[int]]:
    path = DATASETS_DIR / "sample" / "urls_labeled.csv"
    if not path.exists():
        return [], []
    urls, labels = [], []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            urls.append(row["url"])
            labels.append(int(row["label"]))
    return urls, labels
