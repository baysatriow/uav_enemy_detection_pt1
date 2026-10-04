#!/usr/bin/env python3
"""
Experiment E6: Final Model Analysis & Comparative Benchmark.

Scans experiment runs E0 to E5, ranks models, identifies the best configuration,
and performs comprehensive test-split analysis (metrics, PR curves, confusion matrices,
speed benchmark, and sample visual detections).

Usage:
    python experiments/scripts/analyze_e6.py --metric map50
    python experiments/scripts/analyze_e6.py --project runs/experiments --split test
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.modules.cbam import register_cbam  # noqa: E402
from experiments.scripts.evaluate import evaluate_model  # noqa: E402

register_cbam()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("analyze_e6")

EXPERIMENT_DESCRIPTIONS = {
    "E0": "Baseline (Standard YOLO26)",
    "E1": "1x Backbone CBAM (P5)",
    "E2": "2x Backbone CBAM (P4 + P5)",
    "E3": "3x Backbone CBAM (P3 + P4 + P5)",
    "E4": "Neck CBAM (3x Neck branches)",
    "E5": "Combined Attention (Backbone + Neck)",
}


def find_experiment_runs(project_dir: Path) -> Dict[str, Path]:
    runs = {}
    if not project_dir.is_dir():
        return runs

    for sub in sorted(project_dir.iterdir()):
        if not sub.is_dir():
            continue
        # Match run prefix (e.g. E0_yolo26x or E0)
        prefix = sub.name.split("_")[0]
        if prefix in EXPERIMENT_DESCRIPTIONS:
            results_csv = sub / "results.csv"
            best_weights = sub / "weights" / "best.pt"
            if results_csv.is_file() and best_weights.is_file():
                runs[prefix] = sub
    return runs


def parse_run_results(run_dir: Path) -> Dict[str, Any]:
    csv_file = run_dir / "results.csv"
    df = pd.read_csv(csv_file)
    df.columns = [col.strip() for col in df.columns]

    # Ultralytics column names in results.csv
    map50_col = "metrics/mAP50(B)"
    map_col = "metrics/mAP50-95(B)"
    p_col = "metrics/precision(B)"
    r_col = "metrics/recall(B)"

    # Fallbacks if column names differ
    for col in df.columns:
        if "mAP50(B)" in col and map50_col not in df.columns:
            map50_col = col
        elif "mAP50-95(B)" in col and map_col not in df.columns:
            map_col = col
        elif "precision(B)" in col and p_col not in df.columns:
            p_col = col
        elif "recall(B)" in col and r_col not in df.columns:
            r_col = col

    best_idx = df[map50_col].idxmax() if map50_col in df.columns else -1
    row = df.iloc[best_idx] if best_idx >= 0 else df.iloc[-1]

    return {
        "epochs_trained": len(df),
        "best_epoch": int(row.get("epoch", len(df))),
        "val_precision": float(row.get(p_col, np.nan)),
        "val_recall": float(row.get(r_col, np.nan)),
        "val_map50": float(row.get(map50_col, np.nan)),
        "val_map50_95": float(row.get(map_col, np.nan)),
        "weights_path": run_dir / "weights" / "best.pt",
    }


def benchmark_latency(model: Any, imgsz: int = 640, device: str = "cuda", iterations: int = 100) -> Dict[str, float]:
    import torch

    dummy_input = torch.zeros((1, 3, imgsz, imgsz), device=device)
    # Warmup
    for _ in range(15):
        _ = model(dummy_input, verbose=False)

    if device.startswith("cuda"):
        torch.cuda.synchronize()

    start_time = time.time()
    for _ in range(iterations):
        _ = model(dummy_input, verbose=False)
        if device.startswith("cuda"):
            torch.cuda.synchronize()
    total_time = time.time() - start_time

    avg_latency_ms = (total_time / iterations) * 1000
    fps = 1000 / avg_latency_ms if avg_latency_ms > 0 else 0
    return {"latency_ms": round(avg_latency_ms, 2), "fps": round(fps, 1)}


def generate_comparison_plots(df: pd.DataFrame, output_dir: Path) -> None:
    metrics = ["val_map50", "val_map50_95", "val_precision", "val_recall"]
    metric_labels = ["mAP@0.5", "mAP@0.5:0.95", "Precision", "Recall"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for ax, met, lbl in zip(axes, metrics, metric_labels):
        if met not in df.columns:
            continue
        bars = ax.bar(df["Experiment"], df[met], color="#3973ac", edgecolor="black", alpha=0.85)
        # Highlight best bar in green
        best_val = df[met].max()
        for bar in bars:
            if bar.get_height() == best_val:
                bar.set_color("#2ca02c")
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.005,
                f"{bar.get_height():.3f}",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )
        ax.set_title(f"Comparison: {lbl}", fontsize=12, fontweight="bold")
        ax.set_ylim(0, max(1.0, (best_val + 0.1) if not np.isnan(best_val) else 1.0))
        ax.set_ylabel(lbl)
        ax.grid(axis="y", linestyle="--", alpha=0.4)

    fig.tight_layout()
    plot_file = output_dir / "matrix_comparison_metrics.png"
    fig.savefig(plot_file, dpi=160, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Comparison plot saved: {plot_file}")


def run_e6_analysis(
    project_dir: str | Path | None = None,
    primary_metric: str = "val_map50",
    split: str = "test",
    device: str | int | None = None,
    imgsz: int = 640,
) -> None:
    from ultralytics import YOLO
    import torch

    defaults_file = PROJECT_ROOT / "experiments" / "configs" / "train_defaults.yaml"
    with open(defaults_file, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    project = (
        Path(project_dir).resolve()
        if project_dir
        else (PROJECT_ROOT / cfg.get("project", "runs/experiments")).resolve()
    )

    if device is None:
        device = 0 if torch.cuda.is_available() else "cpu"

    e6_dir = project / "E6_final_analysis"
    e6_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 70)
    logger.info("EXPERIMENT E6: FINAL MODEL ANALYSIS & BENCHMARK")
    logger.info(f"Scanning project directory: {project}")
    logger.info("=" * 70)

    runs = find_experiment_runs(project)
    if not runs:
        logger.error(f"No completed experiment runs found in {project}.")
        logger.error("Please run experiments E0 through E5 first using train.py or run_matrix.py.")
        return

    logger.info(f"Found completed experiments: {list(runs.keys())}")
    rows = []
    for exp_id, r_dir in runs.items():
        data = parse_run_results(r_dir)
        data["Experiment"] = exp_id
        data["Configuration"] = EXPERIMENT_DESCRIPTIONS.get(exp_id, "")
        rows.append(data)

    df_comp = pd.DataFrame(rows).sort_values(primary_metric, ascending=False).reset_index(drop=True)

    # Save summary tables
    csv_out = e6_dir / "experiment_matrix_comparison.csv"
    md_out = e6_dir / "experiment_matrix_comparison.md"
    df_comp.to_csv(csv_out, index=False)

    md_content = "# Experimental Matrix Performance Comparison (E0 - E5)\n\n"
    md_content += df_comp[[
        "Experiment", "Configuration", "epochs_trained",
        "val_precision", "val_recall", "val_map50", "val_map50_95"
    ]].to_markdown(index=False)
    md_out.write_text(md_content, encoding="utf-8")

    print("\n" + "=" * 70)
    print("COMPARATIVE MATRIX SUMMARY:")
    print(df_comp[["Experiment", "Configuration", "val_precision", "val_recall", "val_map50", "val_map50_95"]].round(4).to_string(index=False))
    print("=" * 70)

    # Generate metric bar charts
    generate_comparison_plots(df_comp, e6_dir)

    # Select best model
    best_row = df_comp.iloc[0]
    best_exp_id = best_row["Experiment"]
    best_weights = Path(best_row["weights_path"]).resolve()
    logger.info(f"\nWINNING CONFIGURATION: {best_exp_id} ({best_row['Configuration']})")
    logger.info(f"Best Validation Metric ({primary_metric}): {best_row[primary_metric]:.4f}")
    logger.info(f"Evaluating {best_exp_id} best weights on {split} set...")

    # Run full test set evaluation on best model
    eval_results = evaluate_model(
        weights_path=best_weights,
        split=split,
        device=device,
        imgsz=imgsz,
        save_dir=e6_dir / f"best_{best_exp_id}_{split}_evaluation",
    )

    # Latency / FPS Benchmark
    logger.info("\nRunning inference latency benchmark on best model...")
    model = YOLO(str(best_weights))
    target_dev = f"cuda:{device}" if isinstance(device, int) or (isinstance(device, str) and device.isdigit()) else "cpu"
    bench_results = benchmark_latency(model, imgsz=imgsz, device=target_dev)

    logger.info(f"Benchmark Latency: {bench_results['latency_ms']} ms/frame ({bench_results['fps']} FPS)")

    e6_summary = {
        "best_experiment_id": best_exp_id,
        "best_configuration": best_row["Configuration"],
        "selection_metric": primary_metric,
        "validation_metric_score": float(best_row[primary_metric]),
        "test_evaluation": eval_results["overall"],
        "speed_benchmark": bench_results,
    }

    with open(e6_dir / "e6_final_report.json", "w", encoding="utf-8") as f:
        json.dump(e6_summary, f, indent=2)

    logger.info("\n" + "=" * 70)
    logger.info("E6 FINAL ANALYSIS COMPLETE!")
    logger.info(f"Results and visual plots saved to: {e6_dir}")
    logger.info("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Run E6 Final Model Analysis")
    parser.add_argument("--project", type=str, default=None, help="Path to runs/experiments directory")
    parser.add_argument("--metric", type=str, default="val_map50", choices=["val_map50", "val_map50_95"])
    parser.add_argument("--split", type=str, default="test", choices=["test", "val"])
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()

    run_e6_analysis(
        project_dir=args.project,
        primary_metric=args.metric,
        split=args.split,
        device=args.device,
        imgsz=args.imgsz,
    )


if __name__ == "__main__":
    main()
