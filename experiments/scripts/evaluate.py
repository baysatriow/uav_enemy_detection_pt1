#!/usr/bin/env python3
"""
Evaluation script for YOLO26 CBAM models.

Usage:
    python experiments/scripts/evaluate.py --weights runs/experiments/E1_yolo26x/weights/best.pt --split test
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.modules.cbam import register_cbam  # noqa: E402

register_cbam()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("evaluate_experiment")


def evaluate_model(
    weights_path: str | Path,
    data_yaml: str | Path | None = None,
    split: str = "test",
    device: str | int | None = None,
    imgsz: int = 640,
    save_dir: str | Path | None = None,
) -> Dict[str, Any]:
    from ultralytics import YOLO
    import torch

    weights = Path(weights_path).resolve()
    if not weights.is_file():
        raise FileNotFoundError(f"Weights file not found: {weights}")

    # Determine data.yaml
    if data_yaml is None:
        defaults_file = PROJECT_ROOT / "experiments" / "configs" / "train_defaults.yaml"
        if defaults_file.is_file():
            with open(defaults_file, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                local_data = PROJECT_ROOT / cfg.get("dataset_yaml", "")
                if local_data.is_file():
                    data_yaml = local_data
                else:
                    data_yaml = PROJECT_ROOT / cfg.get("fallback_dataset_yaml", "")

        if not data_yaml or not Path(data_yaml).is_file():
            candidates = [
                PROJECT_ROOT / "enemy-detection-1-fps-1" / "data.yaml",
                PROJECT_ROOT / "datasets" / "enemy-detection-1-fps-v1" / "data_yolo26_local.yaml",
                PROJECT_ROOT / "datasets" / "enemy-detection-1-fps-v1" / "data.yaml",
            ]
            for cand in candidates:
                if cand.is_file():
                    data_yaml = cand
                    break

    data_yaml = Path(data_yaml).resolve()
    if not data_yaml.is_file():
        raise FileNotFoundError(f"Dataset YAML file not found: {data_yaml}")

    if device is None:
        device = 0 if torch.cuda.is_available() else "cpu"

    if save_dir is None:
        save_dir = weights.parent.parent / "evaluations" / split
    save_dir = Path(save_dir).resolve()
    save_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info(f"EVALUATING MODEL: {weights.name}")
    logger.info(f"Split: {split} | Device: {device} | Imgsz: {imgsz}")
    logger.info(f"Data config: {data_yaml}")
    logger.info(f"Output directory: {save_dir}")
    logger.info("=" * 60)

    model = YOLO(str(weights))
    val_results = model.val(
        data=str(data_yaml),
        split=split,
        device=device,
        imgsz=imgsz,
        plots=True,
        project=str(save_dir.parent),
        name=save_dir.name,
        exist_ok=True,
    )

    # Read class names
    with open(data_yaml, "r", encoding="utf-8") as f:
        data_meta = yaml.safe_load(f) or {}
    class_names = data_meta.get("names", ["ally", "enemy"])
    if isinstance(class_names, dict):
        class_names = [class_names[k] for k in sorted(class_names.keys())]

    # Overall metrics
    overall_metrics = {
        "precision": float(val_results.box.mp),
        "recall": float(val_results.box.mr),
        "map50": float(val_results.box.map50),
        "map50_95": float(val_results.box.map),
    }

    # Per-class metrics
    per_class = []
    ap_indices = [int(i) for i in getattr(val_results.box, "ap_class_index", [])]
    for idx_pos, class_id in enumerate(ap_indices):
        p, r, ap50, ap = val_results.box.class_result(idx_pos)
        name = class_names[class_id] if class_id < len(class_names) else f"Class_{class_id}"
        per_class.append(
            {
                "class_id": class_id,
                "class_name": name,
                "precision": float(p),
                "recall": float(r),
                "map50": float(ap50),
                "map50_95": float(ap),
            }
        )

    results_summary = {
        "weights": str(weights),
        "split": split,
        "overall": overall_metrics,
        "per_class": per_class,
    }

    # Save metrics JSON
    metrics_json_path = save_dir / "evaluation_metrics.json"
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)

    # Print summary table
    df_overall = pd.DataFrame([overall_metrics], index=["Overall"])
    print("\n--- Overall Metrics ---")
    print(df_overall.round(4).to_string())

    if per_class:
        df_classes = pd.DataFrame(per_class)
        print("\n--- Per-Class Metrics ---")
        print(df_classes.round(4).to_string(index=False))

    # Confusion matrix heatmap generation
    confusion = getattr(val_results, "confusion_matrix", None)
    if confusion is not None and getattr(confusion, "matrix", None) is not None:
        save_confusion_matrix_heatmaps(confusion.matrix, class_names, save_dir)

    logger.info(f"Evaluation complete. Metrics saved to: {metrics_json_path}")
    return results_summary


def save_confusion_matrix_heatmaps(
    raw_matrix: np.ndarray, class_names: list[str], output_dir: Path
) -> None:
    matrix = np.asarray(raw_matrix, dtype=float)
    labels = list(class_names) + ["Background"]
    if matrix.shape[0] != len(labels):
        labels = [f"Class_{i}" for i in range(matrix.shape[0] - 1)] + ["Background"]

    actual_totals = matrix.sum(axis=0, keepdims=True)
    norm_matrix = np.divide(
        matrix,
        actual_totals,
        out=np.zeros_like(matrix, dtype=float),
        where=actual_totals != 0,
    )

    for mat, title, fname, fmt in (
        (matrix, "Confusion Matrix (Counts)", "confusion_matrix_counts.png", "{:.0f}"),
        (norm_matrix, "Confusion Matrix (Normalized)", "confusion_matrix_normalized.png", "{:.2f}"),
    ):
        fig, ax = plt.subplots(figsize=(7, 6))
        im = ax.imshow(mat, cmap="Blues", interpolation="nearest")
        ax.set_title(title, fontsize=12, pad=10)
        ax.set_xlabel("Ground Truth Label", fontsize=10)
        ax.set_ylabel("Predicted Label", fontsize=10)
        ax.set_xticks(range(len(labels)), labels, rotation=30, ha="right")
        ax.set_yticks(range(len(labels)), labels)

        midpoint = float(np.nanmax(mat)) / 2 if mat.size and np.nanmax(mat) > 0 else 0
        for r in range(mat.shape[0]):
            for c in range(mat.shape[1]):
                val = mat[r, c]
                color = "white" if val > midpoint else "black"
                ax.text(c, r, fmt.format(val), ha="center", va="center", color=color, fontsize=9)

        fig.colorbar(im, ax=ax)
        fig.tight_layout()
        fig.savefig(output_dir / fname, dpi=160, bbox_inches="tight")
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Evaluate YOLO26 CBAM Checkpoint")
    parser.add_argument("--weights", type=str, required=True, help="Path to best.pt checkpoint")
    parser.add_argument("--data", type=str, default=None, help="Path to dataset data.yaml")
    parser.add_argument("--split", type=str, default="test", choices=["val", "test", "train"])
    parser.add_argument("--device", type=str, default=None, help="Device (0, cpu)")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--save-dir", type=str, default=None, help="Evaluation output directory")
    args = parser.parse_args()

    evaluate_model(
        weights_path=args.weights,
        data_yaml=args.data,
        split=args.split,
        device=args.device,
        imgsz=args.imgsz,
        save_dir=args.save_dir,
    )


if __name__ == "__main__":
    main()
