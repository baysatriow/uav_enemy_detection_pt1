#!/usr/bin/env python3
"""
Evaluate and Benchmark All 30 Trained Models on the Test Split.

Iterates over all runs (E0 to E5 across n, s, m, l, x), performs inference on the test split,
benchmarks latency, and outputs a complete markdown summary.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import torch
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.modules.cbam import register_cbam
from experiments.scripts.evaluate import evaluate_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("evaluate_all_test")

EXPERIMENT_DESCRIPTIONS = {
    "E0": "Baseline (Standard YOLO26)",
    "E1": "1x Backbone CBAM (P5)",
    "E2": "2x Backbone CBAM (P4 + P5)",
    "E3": "3x Backbone CBAM (P3 + P4 + P5)",
    "E4": "Neck CBAM (3x Neck branches)",
    "E5": "Combined Attention (Backbone + Neck)",
}


def benchmark_latency(model: Any, imgsz: int = 640, device: str = "cuda", iterations: int = 50) -> Dict[str, float]:
    """Measure inference latency and FPS."""
    try:
        dummy = torch.randn(1, 3, imgsz, imgsz)
        if device != "cpu" and torch.cuda.is_available():
            dummy = dummy.cuda()
            # Warmup
            for _ in range(10):
                _ = model.predict(dummy, verbose=False)
            torch.cuda.synchronize()

            start = time.time()
            for _ in range(iterations):
                _ = model.predict(dummy, verbose=False)
            torch.cuda.synchronize()
            elapsed = time.time() - start
        else:
            dummy = dummy.cpu()
            for _ in range(5):
                _ = model.predict(dummy, verbose=False)
            start = time.time()
            for _ in range(iterations):
                _ = model.predict(dummy, verbose=False)
            elapsed = time.time() - start

        latency_ms = (elapsed / iterations) * 1000.0
        fps = 1000.0 / latency_ms if latency_ms > 0 else 0.0
        return {"latency_ms": round(latency_ms, 2), "fps": round(fps, 1)}
    except Exception as exc:
        logger.warning(f"Could not complete latency benchmark: {exc}")
        return {"latency_ms": 0.0, "fps": 0.0}


def run_all_test_evaluations(
    project_dir: Path | str = "runs/experiments",
    data_yaml: Path | str | None = None,
    imgsz: int = 640,
    device: str | int | None = None,
) -> None:
    register_cbam()
    project = (PROJECT_ROOT / project_dir).resolve() if not Path(project_dir).is_absolute() else Path(project_dir)
    
    if data_yaml is None:
        candidates = [
            PROJECT_ROOT / "enemy-detection-1-fps-1" / "data.yaml",
            PROJECT_ROOT / "datasets" / "enemy-detection-1-fps-v1" / "data_yolo26_local.yaml",
            PROJECT_ROOT / "datasets" / "enemy-detection-1-fps-v1" / "data.yaml",
        ]
        for c in candidates:
            if c.is_file():
                data_yaml = c
                break

    if not data_yaml or not Path(data_yaml).is_file():
        raise FileNotFoundError(f"data.yaml not found. Checked: {candidates}")

    data_yaml = Path(data_yaml).resolve()
    logger.info(f"Using dataset YAML: {data_yaml}")

    eval_out_dir = project / "all_test_evaluations"
    eval_out_dir.mkdir(parents=True, exist_ok=True)

    # Collect runs
    run_dirs = sorted([d for d in project.iterdir() if d.is_dir() and not d.name.startswith("E6_") and not d.name.startswith("all_test")])

    logger.info(f"Found {len(run_dirs)} experiment directories to evaluate.")

    results_list: List[Dict[str, Any]] = []

    for idx, r_dir in enumerate(run_dirs, 1):
        best_pt = r_dir / "weights" / "best.pt"
        if not best_pt.is_file():
            logger.warning(f"Skipping {r_dir.name}: best.pt not found.")
            continue

        parts = r_dir.name.split("_")
        exp_id = parts[0]
        model_name = parts[1] if len(parts) > 1 else ""
        scale = model_name.replace("yolo26", "") if "yolo26" in model_name else model_name

        logger.info(f"\n[{idx}/{len(run_dirs)}] Evaluating on Test Set: {r_dir.name} ({exp_id} scale={scale})...")

        save_sub = eval_out_dir / r_dir.name
        try:
            eval_res = evaluate_model(
                weights_path=best_pt,
                data_yaml=data_yaml,
                split="test",
                device=device,
                imgsz=imgsz,
                save_dir=save_sub,
            )

            # Benchmark latency
            loaded_model = YOLO(str(best_pt))
            bench = benchmark_latency(loaded_model, imgsz=imgsz, device=str(device) if device else "cuda", iterations=30)

            overall = eval_res.get("overall", {})
            per_class = {c["class_name"]: c for c in eval_res.get("per_class", [])}
            ally = per_class.get("ally", {})
            enemy = per_class.get("enemy", {})

            row = {
                "Run": r_dir.name,
                "Exp": exp_id,
                "Scale": scale,
                "Architecture": EXPERIMENT_DESCRIPTIONS.get(exp_id, ""),
                "test_p": round(overall.get("precision", 0.0), 4),
                "test_r": round(overall.get("recall", 0.0), 4),
                "test_map50": round(overall.get("map50", 0.0), 4),
                "test_map50_95": round(overall.get("map50_95", 0.0), 4),
                "ally_map50": round(ally.get("map50", 0.0), 4),
                "enemy_map50": round(enemy.get("map50", 0.0), 4),
                "latency_ms": bench.get("latency_ms", 0.0),
                "fps": bench.get("fps", 0.0),
            }
            results_list.append(row)
        except Exception as exc:
            logger.error(f"Failed to evaluate {r_dir.name}: {exc}", exc_info=True)

    df = pd.DataFrame(results_list)
    csv_file = eval_out_dir / "all_30_models_test_results.csv"
    df.to_csv(csv_file, index=False)
    logger.info(f"Test results CSV saved to: {csv_file}")

    # Generate Markdown Summary Report
    generate_markdown_report(df, eval_out_dir / "ALL_30_MODELS_TEST_EVALUATION.md")


def generate_markdown_report(df: pd.DataFrame, output_path: Path) -> None:
    top10 = df.sort_values("test_map50", ascending=False).head(10)
    pivot_map50 = df.pivot(index="Exp", columns="Scale", values="test_map50")[["n", "s", "m", "l", "x"]]
    pivot_map95 = df.pivot(index="Exp", columns="Scale", values="test_map50_95")[["n", "s", "m", "l", "x"]]
    pivot_enemy = df.pivot(index="Exp", columns="Scale", values="enemy_map50")[["n", "s", "m", "l", "x"]]

    md = []
    md.append("# Full Test Set Evaluation & Benchmark Report (All 30 Models)")
    md.append("")
    md.append("This report presents the objective evaluation metrics of **all 30 YOLO26 + CBAM models** evaluated exclusively on the **unseen Test Split** (`test/`, 134 images, 610 instances).")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 1. Top 10 Models Ranked by Test mAP@50")
    md.append("")
    md.append(top10[["Run", "Exp", "Scale", "test_p", "test_r", "test_map50", "test_map50_95", "enemy_map50", "fps"]].to_markdown(index=False))
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 2. Test mAP@50 Matrix (Architecture x Scale)")
    md.append("")
    md.append(pivot_map50.to_markdown())
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 3. Test mAP@50:95 Matrix (Architecture x Scale)")
    md.append("")
    md.append(pivot_map95.to_markdown())
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 4. Primary Target Class (`enemy`) Test mAP@50")
    md.append("")
    md.append(pivot_enemy.to_markdown())
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 5. Complete 30-Model Performance Table on Test Split")
    md.append("")
    md.append(df.sort_values("test_map50", ascending=False).to_markdown(index=False))
    md.append("")

    output_path.write_text("\n".join(md), encoding="utf-8")
    logger.info(f"Markdown report saved to: {output_path}")

    # Also copy to experiments root for immediate accessibility
    root_md = PROJECT_ROOT / "experiments" / "ALL_30_MODELS_TEST_EVALUATION.md"
    root_md.write_text("\n".join(md), encoding="utf-8")
    logger.info(f"Markdown report synced to: {root_md}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate all 30 models on test split")
    parser.add_argument("--project", default="runs/experiments", help="Project runs directory")
    parser.add_argument("--data", default=None, help="Dataset data.yaml path")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default=None)
    args = parser.parse_args()

    run_all_test_evaluations(
        project_dir=args.project,
        data_yaml=args.data,
        imgsz=args.imgsz,
        device=args.device,
    )
