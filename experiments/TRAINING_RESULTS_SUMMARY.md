# Comprehensive Experimental Matrix Training & Evaluation Report

**Project:** UAV Enemy Detection (YOLO26 + CBAM Architectural Suite)  
**Total Runs Executed:** 30 Runs (5 Model Scales $\times$ 6 Architectural Experiments E0–E5)  
**Hardware Used:** NVIDIA GeForce RTX 5070 (12 GB VRAM) | PyTorch 2.14.0+cu132  
**Dataset:** `enemy-detection-1-fps` (Classes: `ally`, `enemy`)  

---

## 1. Executive Summary & Key Highlights

1. **Overall Best Architecture & Scale:**
   - **`E0_yolo26n` (Baseline Nano)** achieved the highest overall validation metric across the entire suite with **mAP@50 = 0.9183** and **mAP@50:95 = 0.4669**, closely followed by **`E4_yolo26n` (Neck CBAM)** at **mAP@50 = 0.9077**.
2. **Attention Impact across Scales:**
   - **Small & Medium (`m`, `l`):** Adding single-stage CBAM attention in the deepest backbone layer (**E1: 1× Backbone CBAM at $P_5$**) outperformed baseline models:
     - YOLO26m: mAP@50 increased from **0.8011 (E0)** $\rightarrow$ **0.8214 (E1)** (+2.03% gain).
     - YOLO26l: mAP@50 increased from **0.8125 (E0)** $\rightarrow$ **0.8224 (E1)** (+0.99% gain).
   - **Heavy Attention Saturation:** Applying attention at all stages simultaneously (**E2, E3, E5**) introduced architectural overhead and slightly degraded performance compared to focused single-point attention (**E1** or **E4**).
3. **Winning Large-Capacity Configuration (E6 Test Split Benchmark):**
   - In the high-capacity bracket (`yolo26x`), **E1** was crowned the winning model.
   - Evaluated on unseen **Test split**:
     - **Test mAP@50:** **82.66%** (`enemy`: **86.81%**, `ally`: **78.51%**)
     - **Test Precision:** **74.32%**
     - **Test Recall:** **76.54%**
     - **Inference Speed:** **10.15 ms / frame (~98.5 FPS)** on RTX 5070.

---

## 2. Cross-Architecture Matrix Comparison (Pivot Table)

### Metric: Validation mAP@50 ($B$)
| Experiment | CBAM Topology | Nano (`n`) | Small (`s`) | Medium (`m`) | Large (`l`) | X-Large (`x`) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **E0** | Baseline (No Attention) | **0.9183** | **0.8044** | 0.8011 | 0.8125 | 0.7922 |
| **E1** | 1× Backbone ($P_5$) | 0.8939 | 0.7929 | **0.8214** | **0.8224** | **0.7929** |
| **E2** | 2× Backbone ($P_4, P_5$) | 0.8740 | 0.7844 | 0.7890 | 0.7720 | 0.7654 |
| **E3** | 3× Backbone ($P_3, P_4, P_5$) | 0.8567 | 0.8034 | 0.7982 | 0.7908 | 0.7870 |
| **E4** | 3× Neck Outputs ($P_3, P_4, P_5$) | 0.9077 | 0.7994 | 0.7790 | 0.7888 | 0.7825 |
| **E5** | Combined Backbone + Neck | 0.8702 | 0.7909 | 0.7797 | 0.7827 | 0.7648 |

### Metric: Validation mAP@50-95 ($B$)
| Experiment | CBAM Topology | Nano (`n`) | Small (`s`) | Medium (`m`) | Large (`l`) | X-Large (`x`) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **E0** | Baseline (No Attention) | **0.4669** | **0.3730** | 0.3811 | 0.3830 | 0.3673 |
| **E1** | 1× Backbone ($P_5$) | 0.4302 | 0.3570 | **0.3961** | **0.3886** | **0.3790** |
| **E2** | 2× Backbone ($P_4, P_5$) | 0.4273 | 0.3529 | 0.3734 | 0.3669 | 0.3572 |
| **E3** | 3× Backbone ($P_3, P_4, P_5$) | 0.4095 | 0.3604 | 0.3814 | 0.3749 | 0.3755 |
| **E4** | 3× Neck Outputs ($P_3, P_4, P_5$) | 0.4491 | 0.3728 | 0.3741 | 0.3745 | 0.3771 |
| **E5** | Combined Backbone + Neck | 0.4190 | 0.3658 | 0.3606 | 0.3633 | 0.3514 |

---

## 3. Complete 30-Model Performance Breakdown

| Run Directory | Exp | Scale | Epochs Trained | Best Epoch | Precision | Recall | mAP@50 | mAP@50:95 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `E0_yolo26n` | E0 | n | 100 | 80 | **0.8806** | **0.8700** | **0.9183** | **0.4669** |
| `E4_yolo26n` | E4 | n | 100 | 86 | **0.8667** | **0.8601** | **0.9077** | **0.4491** |
| `E1_yolo26n` | E1 | n | 100 | 97 | 0.8310 | 0.8518 | **0.8939** | 0.4302 |
| `E2_yolo26n` | E2 | n | 100 | 93 | 0.8471 | 0.8043 | 0.8740 | 0.4273 |
| `E5_yolo26n` | E5 | n | 100 | 83 | 0.8085 | 0.8305 | 0.8702 | 0.4190 |
| `E3_yolo26n` | E3 | n | 100 | 97 | 0.8266 | 0.7887 | 0.8567 | 0.4095 |
| `E1_yolo26l` | E1 | l | 100 | 90 | 0.7880 | 0.7526 | 0.8224 | 0.3886 |
| `E1_yolo26m` | E1 | m | 100 | 100 | 0.7940 | 0.7578 | 0.8214 | 0.3961 |
| `E0_yolo26l` | E0 | l | 100 | 88 | 0.7638 | 0.7471 | 0.8125 | 0.3830 |
| `E0_yolo26s` | E0 | s | 100 | 95 | 0.7594 | 0.7497 | 0.8044 | 0.3730 |
| `E3_yolo26s` | E3 | s | 100 | 85 | 0.7877 | 0.7431 | 0.8034 | 0.3604 |
| `E0_yolo26m` | E0 | m | 100 | 98 | 0.7798 | 0.7151 | 0.8011 | 0.3811 |
| `E4_yolo26s` | E4 | s | 100 | 91 | 0.7547 | 0.7517 | 0.7994 | 0.3728 |
| `E3_yolo26m` | E3 | m | 100 | 100 | 0.7753 | 0.7054 | 0.7982 | 0.3814 |
| `E1_yolo26s` | E1 | s | 100 | 97 | 0.7648 | 0.7364 | 0.7929 | 0.3570 |
| `E1_yolo26x` | E1 | x | 100 | 95 | 0.7449 | 0.7230 | 0.7929 | 0.3790 |
| `E0_yolo26x` | E0 | x | 100 | 97 | 0.7581 | 0.7336 | 0.7922 | 0.3673 |
| `E5_yolo26s` | E5 | s | 100 | 85 | 0.7564 | 0.7133 | 0.7909 | 0.3658 |
| `E3_yolo26l` | E3 | l | 100 | 100 | 0.7500 | 0.7291 | 0.7908 | 0.3749 |
| `E2_yolo26m` | E2 | m | 100 | 85 | 0.7449 | 0.7457 | 0.7890 | 0.3734 |
| `E4_yolo26l` | E4 | l | 100 | 85 | 0.7799 | 0.7149 | 0.7888 | 0.3745 |
| `E3_yolo26x` | E3 | x | 100 | 95 | 0.7323 | 0.7357 | 0.7870 | 0.3755 |
| `E2_yolo26s` | E2 | s | 100 | 99 | 0.7294 | 0.7414 | 0.7844 | 0.3529 |
| `E5_yolo26l` | E5 | l | 100 | 98 | 0.7290 | 0.7061 | 0.7827 | 0.3633 |
| `E4_yolo26x` | E4 | x | 100 | 93 | 0.7668 | 0.7069 | 0.7825 | 0.3771 |
| `E5_yolo26m` | E5 | m | 100 | 85 | 0.7228 | 0.7270 | 0.7797 | 0.3606 |
| `E4_yolo26m` | E4 | m | 100 | 86 | 0.7422 | 0.7319 | 0.7790 | 0.3741 |
| `E2_yolo26l` | E2 | l | 100 | 86 | 0.7364 | 0.7131 | 0.7720 | 0.3669 |
| `E2_yolo26x` | E2 | x | 100 | 98 | 0.7446 | 0.6875 | 0.7654 | 0.3572 |
| `E5_yolo26x` | E5 | x | 100 | 90 | 0.7267 | 0.7086 | 0.7648 | 0.3514 |

---

## 4. E6 Final Model Evaluation on Unseen Test Set

- **Target Checkpoint:** `runs/experiments/E1_yolo26x/weights/best.pt`
- **Benchmark Latency:** **10.15 ms/frame** (**98.5 FPS**)

### Test Set Metrics Summary
| Target Class | Instances | Precision | Recall | mAP@50 | mAP@50-95 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **All Classes** | 610 | **0.7432** | **0.7654** | **0.8266** | **0.3963** |
| `ally` | 340 | 0.7333 | 0.7176 | 0.7851 | 0.3875 |
| `enemy` | 270 | **0.7530** | **0.8131** | **0.8681** | **0.4052** |

> **Key Observation:** The detector displays significantly higher accuracy and recall on the primary target class (`enemy` @ **86.8% mAP@50** and **81.3% Recall**) compared to the friendly class (`ally`).

---

## 5. Artifacts and Output Files

All raw logs, confusion matrices, PR curves, and weights are preserved in:
- Comparison plots: `runs/experiments/E6_final_analysis/matrix_comparison_metrics.png`
- E6 Test Benchmark curves: `runs/experiments/E6_final_analysis/best_E1_test_evaluation/`
- Full CSV Comparison: `runs/experiments/E6_final_analysis/experiment_matrix_comparison.csv`
- Model Checkpoints: `runs/experiments/<EXP_ID>_<MODEL_SIZE>/weights/best.pt`
