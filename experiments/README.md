# YOLO26 + CBAM Experimental Matrix Suite (E0 – E6)

This directory contains the complete implementation of the experimental matrix evaluating the impact of **Convolutional Block Attention Module (CBAM)** at different topological locations within the **YOLO26** architecture for UAV enemy detection.

---

## 1. Experimental Matrix

| ID | Architecture | CBAM Integration | Attention Scale / Location | Purpose |
|:---|:---|:---|:---|:---|
| **E0** | YOLO26 | None | None | **Baseline**: Standard YOLO26 model. |
| **E1** | YOLO26 | 1× Backbone | Deepest stage ($P_5$) | **Single attention**: Evaluate minimal attention at the highest semantic level. |
| **E2** | YOLO26 | 2× Backbone | Multi-scale stages ($P_4, P_5$) | **Multiple attention**: Evaluate attention on medium and large object features. |
| **E3** | YOLO26 | 3× Backbone | Full hierarchy ($P_3, P_4, P_5$) | **Attention depth**: Evaluate attention across all multi-scale backbone stages. |
| **E4** | YOLO26 | Neck | 3× Neck output branches ($P_3, P_4, P_5$) | **Location comparison**: Directly compare Neck attention vs. Backbone attention. |
| **E5** | YOLO26 | Backbone + Neck | Backbone ($P_3, P_4, P_5$) + Neck ($P_3, P_4, P_5$) | **Combined attention**: Evaluate end-to-end multi-scale attention synergy. |
| **E6** | Best Model | — | Determined by best validation metric from E0–E5 | **Final model analysis**: Full test split evaluation, PR curves, confusion matrices, latency benchmark, and error analysis. |

---

## 2. Directory Structure

```
experiments/
├── README.md                           # Documentation & execution guide
├── modules/
│   ├── __init__.py
│   └── cbam.py                         # PyTorch CBAM module & dynamic Ultralytics hook
├── configs/
│   ├── e0_yolo26_baseline.yaml         # E0: Baseline YOLO26
│   ├── e1_yolo26_cbam_backbone_1x.yaml # E1: 1× Backbone CBAM (P5)
│   ├── e2_yolo26_cbam_backbone_2x.yaml # E2: 2× Backbone CBAM (P4, P5)
│   ├── e3_yolo26_cbam_backbone_3x.yaml # E3: 3× Backbone CBAM (P3, P4, P5)
│   ├── e4_yolo26_cbam_neck.yaml        # E4: Neck CBAM (3x Neck branches)
│   ├── e5_yolo26_cbam_combined.yaml    # E5: Combined Backbone + Neck CBAM
│   └── train_defaults.yaml             # Shared hyperparameters & training settings
├── scripts/
│   ├── train.py                        # Unified training CLI for any experiment
│   ├── evaluate.py                     # Checkpoint evaluation script (Val / Test)
│   ├── run_matrix.py                   # Automated sequential matrix runner (E0 -> E5)
│   └── analyze_e6.py                   # E6: Comparison table, ranking & test benchmark
└── notebooks/
    ├── YOLO26_CBAM_Experiments.ipynb   # Colab/remote GPU training & comparison notebook
    └── E6_Best_Model_Evaluation.ipynb  # Dedicated deep-dive evaluation notebook
```

---

## 3. CBAM Implementation & Zero-Modification Hook

The CBAM module (`experiments/modules/cbam.py`) is implemented with:
1. **Channel Attention Module (CAM)**:
   $$M_c(F) = \sigma(\text{MLP}(\text{AvgPool}(F)) + \text{MLP}(\text{MaxPool}(F)))$$
2. **Spatial Attention Module (SAM)**:
   $$M_s(F') = \sigma(f^{7\times 7}([\text{AvgPool}(F'); \text{MaxPool}(F')]))$$

### Dynamic Ultralytics Registration
No files in the installed `ultralytics` package need to be manually edited. Calling:
```python
from experiments.modules.cbam import register_cbam
register_cbam()
```
automatically registers `CBAM` into Ultralytics' module registry and enables automatic channel resolution during YAML parsing across all model scales (`n`, `s`, `m`, `l`, `x`).

---

## 4. How to Run

### Option A: Run via Interactive Jupyter Notebook (Google Colab / Kaggle / Cloud GPU)
Open [`experiments/notebooks/YOLO26_CBAM_Experiments.ipynb`](file:///home/zerxx/Documents/Code/Enemy%20Detection/uav_enemy_detection_pt1/experiments/notebooks/YOLO26_CBAM_Experiments.ipynb):
- Automatically downloads dataset from Roboflow if missing.
- Contains individual cells to train each experiment **E0** to **E5**.
- Automatically runs **E6** comparative analysis and test benchmarking.

### Option B: Run Individual Experiments via CLI
Train any experiment by specifying `--exp`:
```bash
# Train E0 (Baseline)
python experiments/scripts/train.py --exp E0 --model-size x

# Train E1 (1x Backbone CBAM)
python experiments/scripts/train.py --exp E1 --model-size x

# Train E3 (3x Backbone CBAM) with custom batch and epochs
python experiments/scripts/train.py --exp E3 --model-size x --batch 8 --epochs 100

# Train E5 (Combined Backbone + Neck)
python experiments/scripts/train.py --exp E5 --model-size x
```

### Option C: Run Full Experimental Matrix Sequentially
To train all experiments from E0 to E5 automatically in sequence:
```bash
python experiments/scripts/run_matrix.py --model-size x
```

### Option D: Run E6 Final Analysis & Benchmark
After running experiments, run E6 to rank models and generate comparison artifacts:
```bash
python experiments/scripts/analyze_e6.py --metric val_map50 --split test
```
This generates:
- `runs/experiments/E6_final_analysis/experiment_matrix_comparison.csv`
- `runs/experiments/E6_final_analysis/experiment_matrix_comparison.md`
- `runs/experiments/E6_final_analysis/matrix_comparison_metrics.png`
- Detailed test metrics, confusion matrix heatmaps, and latency benchmark for the winning model.
