#!/usr/bin/env python3
"""
Unified training script for YOLO26 CBAM experiments (E0 to E5).

Usage:
    python experiments/scripts/train.py --exp E0 --model-size x
    python experiments/scripts/train.py --exp E1 --epochs 100 --batch 8
    python experiments/scripts/train.py --exp E5 --pretrained yolo26x.pt
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Register CBAM module with Ultralytics
from experiments.modules.cbam import register_cbam  # noqa: E402

register_cbam()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("train_experiment")

EXPERIMENT_CONFIG_MAP = {
    "E0": "experiments/configs/e0_yolo26_baseline.yaml",
    "E1": "experiments/configs/e1_yolo26_cbam_backbone_1x.yaml",
    "E2": "experiments/configs/e2_yolo26_cbam_backbone_2x.yaml",
    "E3": "experiments/configs/e3_yolo26_cbam_backbone_3x.yaml",
    "E4": "experiments/configs/e4_yolo26_cbam_neck.yaml",
    "E5": "experiments/configs/e5_yolo26_cbam_combined.yaml",
}


def load_defaults() -> Dict[str, Any]:
    defaults_file = PROJECT_ROOT / "experiments" / "configs" / "train_defaults.yaml"
    if defaults_file.is_file():
        with open(defaults_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def resolve_dataset_yaml(configured_path: str | None, defaults: Dict[str, Any]) -> Path:
    candidates = []
    if configured_path:
        candidates.append(Path(configured_path))
        candidates.append(PROJECT_ROOT / configured_path)

    if "dataset_yaml" in defaults:
        candidates.append(PROJECT_ROOT / defaults["dataset_yaml"])
    if "fallback_dataset_yaml" in defaults:
        candidates.append(PROJECT_ROOT / defaults["fallback_dataset_yaml"])

    candidates.append(
        PROJECT_ROOT / "datasets" / "enemy-detection-1-fps-v1" / "data_yolo26_local.yaml"
    )
    candidates.append(
        PROJECT_ROOT / "datasets" / "enemy-detection-1-fps-v1" / "data.yaml"
    )

    for candidate in candidates:
        candidate_resolved = candidate.resolve()
        if candidate_resolved.is_file():
            return candidate_resolved

    # If dataset is missing, attempt auto-download via Roboflow if API key is present
    logger.warning("Dataset YAML not found in standard paths. Checking Roboflow download...")
    return attempt_roboflow_download(defaults)


def attempt_roboflow_download(defaults: Dict[str, Any]) -> Path:
    rf_cfg = defaults.get("roboflow", {})
    api_key = os.environ.get("ROBOFLOW_API_KEY")

    if not api_key:
        logger.error(
            "Dataset not found locally and ROBOFLOW_API_KEY environment variable is not set.\n"
            "Please provide a valid dataset or set ROBOFLOW_API_KEY to download."
        )
        raise FileNotFoundError("Dataset YAML not found. Set ROBOFLOW_API_KEY to auto-download.")

    try:
        from roboflow import Roboflow

        rf = Roboflow(api_key=api_key)
        workspace = rf_cfg.get("workspace", "aaaa-g4pgj")
        project_name = rf_cfg.get("project", "enemy-detection-1-fps")
        version = rf_cfg.get("version", 1)
        fmt = rf_cfg.get("format", "yolo26")

        project = rf.workspace(workspace).project(project_name)
        dataset = project.version(version).download(fmt)
        data_yaml = Path(dataset.location) / "data.yaml"
        if data_yaml.is_file():
            logger.info(f"Dataset successfully downloaded to: {data_yaml}")
            return data_yaml.resolve()
    except Exception as exc:
        logger.error(f"Failed to auto-download dataset: {exc}")
        raise


def train_experiment(
    exp_id: str,
    model_size: str = "x",
    epochs: int | None = None,
    batch: int | None = None,
    imgsz: int | None = None,
    device: str | int | None = None,
    data: str | None = None,
    pretrained: bool | str = True,
    resume: str | None = None,
    project: str | None = None,
    patience: int | None = None,
    workers: int | None = None,
) -> Any:
    """
    Run training for a specific experiment ID (E0 to E5).
    """
    from ultralytics import YOLO
    import torch

    defaults = load_defaults()

    if exp_id not in EXPERIMENT_CONFIG_MAP:
        raise ValueError(
            f"Invalid experiment ID '{exp_id}'. Must be one of: {list(EXPERIMENT_CONFIG_MAP.keys())}"
        )

    config_rel_path = EXPERIMENT_CONFIG_MAP[exp_id]
    config_file = (PROJECT_ROOT / config_rel_path).resolve()
    if not config_file.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    data_yaml = resolve_dataset_yaml(data, defaults)
    logger.info(f"Using dataset YAML: {data_yaml}")

    # Determine batch size
    batch_map = defaults.get("batch_sizes", {"n": -1, "s": 32, "m": 12, "l": 12, "x": 8})
    final_batch = batch if batch is not None else batch_map.get(model_size, 8)
    final_epochs = epochs if epochs is not None else defaults.get("epochs", 100)
    final_imgsz = imgsz if imgsz is not None else defaults.get("imgsz", 640)
    final_patience = patience if patience is not None else defaults.get("patience", 25)
    final_workers = workers if workers is not None else defaults.get("workers", 4)
    final_project = (
        Path(project).resolve()
        if project
        else (PROJECT_ROOT / defaults.get("project", "runs/experiments")).resolve()
    )

    if device is None:
        device = 0 if torch.cuda.is_available() else "cpu"

    exp_run_name = f"{exp_id}_yolo26{model_size}"

    logger.info("=" * 60)
    logger.info(f"STARTING EXPERIMENT: {exp_id} ({exp_run_name})")
    logger.info(f"Architecture config: {config_file.name}")
    logger.info(f"Model Scale: {model_size} | Epochs: {final_epochs} | Batch: {final_batch} | Imgsz: {final_imgsz}")
    logger.info(f"Device: {device} | Output dir: {final_project / exp_run_name}")
    logger.info("=" * 60)

    if resume:
        resume_pt = Path(resume).resolve()
        if not resume_pt.is_file():
            raise FileNotFoundError(f"Resume checkpoint not found: {resume_pt}")
        logger.info(f"Resuming training from checkpoint: {resume_pt}")
        model = YOLO(str(resume_pt))
        train_results = model.train(resume=True)
        return train_results

    # Build model from custom architecture YAML with specified scale
    # Ultralytics accepts model=config_file with scale=model_size
    model = YOLO(str(config_file))

    # Pretrained weights loading
    if pretrained:
        if isinstance(pretrained, str) and Path(pretrained).is_file():
            weights_name = str(Path(pretrained).resolve())
        else:
            weights_name = f"yolo26{model_size}.pt"

        try:
            logger.info(f"Loading pretrained weights for transfer learning: {weights_name}")
            model.load(weights_name)
        except Exception as exc:
            logger.warning(
                f"Could not load pretrained weights '{weights_name}' directly ({exc}). "
                "Training will proceed with available layer weights or from scratch."
            )

    train_args = {
        "data": str(data_yaml),
        "epochs": final_epochs,
        "imgsz": final_imgsz,
        "batch": final_batch,
        "device": device,
        "workers": final_workers,
        "patience": final_patience,
        "optimizer": defaults.get("optimizer", "auto"),
        "amp": defaults.get("amp", True),
        "cache": defaults.get("cache", False),
        "seed": defaults.get("seed", 42),
        "project": str(final_project),
        "name": exp_run_name,
        "plots": defaults.get("plots", True),
        "save": defaults.get("save", True),
        "save_period": defaults.get("save_period", 10),
        "verbose": defaults.get("verbose", True),
        "exist_ok": True,
    }

    train_results = model.train(**train_args)

    save_dir = Path(model.trainer.save_dir).resolve()
    logger.info("=" * 60)
    logger.info(f"EXPERIMENT {exp_id} COMPLETED SUCCESSFULLY!")
    logger.info(f"Run Directory: {save_dir}")
    logger.info(f"Best Checkpoint: {save_dir / 'weights' / 'best.pt'}")
    logger.info("=" * 60)

    return train_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train YOLO26 CBAM Experiment Matrix (E0 to E5)"
    )
    parser.add_argument(
        "--exp",
        type=str,
        required=True,
        choices=list(EXPERIMENT_CONFIG_MAP.keys()),
        help="Experiment ID to execute (E0, E1, E2, E3, E4, E5)",
    )
    parser.add_argument(
        "--model-size",
        type=str,
        default="x",
        choices=["n", "s", "m", "l", "x"],
        help="YOLO26 model scale variant (default: x)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Number of training epochs (default from train_defaults.yaml)",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=None,
        help="Training batch size (default from scale mapping)",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=None,
        help="Input image resolution (default: 640)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Device to run on (e.g., 0, 0,1, cpu)",
    )
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Path to dataset YAML file",
    )
    parser.add_argument(
        "--no-pretrained",
        action="store_true",
        help="Disable pretrained weight loading and train from scratch",
    )
    parser.add_argument(
        "--weights",
        type=str,
        default=None,
        help="Custom pretrained weights path (.pt)",
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Path to checkpoint (.pt) to resume training",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="Root directory for saving experiment runs",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    pretrained_arg = False if args.no_pretrained else (args.weights or True)
    train_experiment(
        exp_id=args.exp,
        model_size=args.model_size,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        data=args.data,
        pretrained=pretrained_arg,
        resume=args.resume,
        project=args.project,
    )


if __name__ == "__main__":
    main()
