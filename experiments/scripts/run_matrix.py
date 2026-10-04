#!/usr/bin/env python3
"""
Sequential runner for YOLO26 CBAM experimental matrix (E0 to E5).

Usage:
    python experiments/scripts/run_matrix.py --model-size x
    python experiments/scripts/run_matrix.py --experiments E0 E1 E2 --epochs 50
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.scripts.train import train_experiment  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("run_matrix")

DEFAULT_MATRIX = ["E0", "E1", "E2", "E3", "E4", "E5"]


def run_matrix(
    experiments: list[str],
    model_size: str = "x",
    epochs: int | None = None,
    batch: int | None = None,
    imgsz: int | None = None,
    device: str | int | None = None,
    data: str | None = None,
    pretrained: bool = True,
    project: str | None = None,
    continue_on_error: bool = True,
) -> None:
    logger.info("=" * 70)
    logger.info("STARTING EXPERIMENTAL MATRIX SUITE")
    logger.info(f"Target Experiments: {experiments}")
    logger.info(f"Model Scale: {model_size}")
    logger.info("=" * 70)

    summary = []
    start_all = time.time()

    for idx, exp_id in enumerate(experiments, 1):
        logger.info(f"\n[{idx}/{len(experiments)}] Launching {exp_id}...")
        exp_start = time.time()
        status = "SUCCESS"
        error_msg = ""
        try:
            train_experiment(
                exp_id=exp_id,
                model_size=model_size,
                epochs=epochs,
                batch=batch,
                imgsz=imgsz,
                device=device,
                data=data,
                pretrained=pretrained,
                project=project,
            )
        except Exception as exc:
            status = "FAILED"
            error_msg = str(exc)
            logger.error(f"Experiment {exp_id} encountered an error: {exc}", exc_info=True)
            if not continue_on_error:
                logger.error("Aborting subsequent experiments due to failure.")
                break

        elapsed = time.time() - exp_start
        summary.append({
            "Experiment": exp_id,
            "Status": status,
            "Time (min)": round(elapsed / 60, 2),
            "Notes": error_msg or "Completed successfully",
        })

    total_elapsed = time.time() - start_all
    logger.info("\n" + "=" * 70)
    logger.info("EXPERIMENTAL MATRIX SUITE EXECUTION FINISHED")
    logger.info(f"Total Time: {round(total_elapsed / 3600, 2)} hours ({round(total_elapsed / 60, 2)} minutes)")
    logger.info("=" * 70)

    import pandas as pd

    df = pd.DataFrame(summary)
    print("\nExecution Summary:")
    print(df.to_string(index=False))


def main():
    parser = argparse.ArgumentParser(description="Run full YOLO26 CBAM experimental matrix")
    parser.add_argument(
        "--experiments",
        nargs="+",
        default=DEFAULT_MATRIX,
        help="List of experiment IDs to run (default: E0 E1 E2 E3 E4 E5)",
    )
    parser.add_argument("--model-size", type=str, default="x", choices=["n", "s", "m", "l", "x"])
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch", type=int, default=None)
    parser.add_argument("--imgsz", type=int, default=None)
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--data", type=str, default=None)
    parser.add_argument("--no-pretrained", action="store_true")
    parser.add_argument("--project", type=str, default=None)
    parser.add_argument("--stop-on-error", action="store_true")

    args = parser.parse_args()
    run_matrix(
        experiments=args.experiments,
        model_size=args.model_size,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        data=args.data,
        pretrained=not args.no_pretrained,
        project=args.project,
        continue_on_error=not args.stop_on_error,
    )


if __name__ == "__main__":
    main()
