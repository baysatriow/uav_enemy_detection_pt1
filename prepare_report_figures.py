import os
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

# Output directory for figures
FIG_DIR = os.path.join(os.path.dirname(__file__), "reports", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# Set style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.edgecolor'] = '#CBD5E0'
plt.rcParams['axes.linewidth'] = 1.0

# Color palette matching report theme
NAVY = "#1A365D"
SLATE = "#2B6CB0"
AMBER = "#D69E2E"
GREEN = "#2E8540"
RED = "#C53030"
LIGHT_BG = "#F7FAFC"
DARK_GRAY = "#2D3748"

# Load 30 model results
CSV_PATH = os.path.join(os.path.dirname(__file__), "runs", "experiments", "all_test_evaluations", "all_30_models_test_results.csv")
df = pd.read_csv(CSV_PATH)

# ==============================================================================
# 1. HEATMAP: Test mAP@50 (Architecture x Scale)
# ==============================================================================
def generate_heatmap():
    print("Generating Figure 1: Test mAP@50 Heatmap...")
    piv = df.pivot(index='Exp', columns='Scale', values='test_map50')
    piv = piv.reindex(index=['E0', 'E1', 'E2', 'E3', 'E4', 'E5'], columns=['n', 's', 'm', 'l', 'x'])
    
    fig, ax = plt.subplots(figsize=(8, 5.2), dpi=300)
    
    # Custom colormap
    cmap = sns.light_palette(SLATE, as_cmap=True)
    
    sns.heatmap(piv, annot=True, fmt=".4f", cmap=cmap, cbar_kws={'label': 'Test mAP@50'},
                linewidths=1.2, linecolor='white', annot_kws={'size': 11, 'weight': 'bold', 'color': DARK_GRAY},
                ax=ax)
    
    ax.set_title("Matriks Performa Test mAP@50: Topologi CBAM vs Skala YOLO26", 
                 fontsize=13, weight='bold', color=NAVY, pad=14)
    ax.set_xlabel("Skala Kapasitas Model (Scale)", fontsize=11, weight='bold', color=DARK_GRAY, labelpad=8)
    ax.set_ylabel("Topologi Arsitektur (Exp)", fontsize=11, weight='bold', color=DARK_GRAY, labelpad=8)
    
    # Scale labels with full names
    ax.set_xticklabels(['Nano (n)', 'Small (s)', 'Medium (m)', 'Large (l)', 'X-Large (x)'], 
                       fontsize=10, weight='semibold')
    ax.set_yticklabels(['E0 (Baseline)', 'E1 (1x Backbone P5)', 'E2 (2x Backbone P4-P5)', 
                        'E3 (3x Backbone P3-P5)', 'E4 (3x Neck)', 'E5 (Backbone+Neck)'], 
                       fontsize=9.5, rotation=0)
    
    # Highlight highest in each column with a marker or text
    max_cells = piv.idxmax()
    col_coords = {'n': 0.5, 's': 1.5, 'm': 2.5, 'l': 3.5, 'x': 4.5}
    row_coords = {'E0': 0.5, 'E1': 1.5, 'E2': 2.5, 'E3': 3.5, 'E4': 4.5, 'E5': 5.5}
    for col, best_exp in max_cells.items():
        x = col_coords[col]
        y = row_coords[best_exp]
        rect = plt.Rectangle((x-0.48, y-0.48), 0.96, 0.96, fill=False, edgecolor=AMBER, lw=3.0)
        ax.add_patch(rect)
        ax.text(x, y - 0.28, "★ BEST", ha='center', va='center', fontsize=8, color=AMBER, weight='black')
        
    plt.tight_layout()
    out_path = os.path.join(FIG_DIR, "fig1_test_map50_heatmap.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved {out_path}")

# ==============================================================================
# 2. PARETO SPEED VS ACCURACY (FPS vs Test mAP@50)
# ==============================================================================
def generate_pareto_chart():
    print("Generating Figure 2: Speed vs Accuracy Pareto Frontier...")
    fig, ax = plt.subplots(figsize=(9, 5.8), dpi=300)
    
    scale_colors = {
        'n': '#2B6CB0',  # Slate Blue
        's': '#38A169',  # Green
        'm': '#DD6B20',  # Warm Orange
        'l': '#805AD5',  # Purple
        'x': '#E53E3E'   # Crimson
    }
    
    scale_names = {
        'n': 'Nano (n)', 's': 'Small (s)', 'm': 'Medium (m)', 'l': 'Large (l)', 'x': 'X-Large (x)'
    }
    
    exp_markers = {
        'E0': 'o', 'E1': 's', 'E2': '^', 'E3': 'D', 'E4': 'v', 'E5': 'X'
    }
    
    for scale, grp in df.groupby('Scale'):
        ax.scatter(grp['fps'], grp['test_map50'] * 100, 
                   color=scale_colors[scale], label=scale_names[scale], 
                   s=100, alpha=0.85, edgecolors='black', linewidth=0.8, zorder=4)
        
    # Annotate key Pareto optimal and top models
    key_models = [
        ('E0_yolo26n', (15, -5), '#1A365D', True),
        ('E1_yolo26n', (-75, 10), '#1A365D', False),
        ('E4_yolo26n', (-75, -15), '#1A365D', False),
        ('E0_yolo26l', (-80, 8), '#805AD5', True),
        ('E1_yolo26x', (15, 8), '#C53030', True),
        ('E1_yolo26m', (15, -12), '#DD6B20', False),
        ('E3_yolo26s', (-75, 10), '#38A169', False),
        ('E5_yolo26n', (12, -10), '#1A365D', False),
    ]
    
    for run_name, offset, text_color, is_pareto in key_models:
        row = df[df['Run'] == run_name].iloc[0]
        fps_val = row['fps']
        map_val = row['test_map50'] * 100
        
        prefix = "★ " if is_pareto else ""
        ax.annotate(f"{prefix}{run_name}\n({fps_val:.1f} FPS, {map_val:.1f}%)",
                    (fps_val, map_val),
                    xytext=offset, textcoords='offset points',
                    fontsize=8.5, weight='bold', color=text_color,
                    bbox=dict(boxstyle='round,pad=0.25', facecolor='#FFFFFF', edgecolor='#CBD5E0', alpha=0.9),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.15', color=text_color, lw=1.2),
                    zorder=6)
        
    # Ideal region highlight
    ax.axvspan(75, 100, ymin=0.6, ymax=1.0, color='#EBF8FF', alpha=0.5, zorder=1)
    ax.text(88, 93.5, "Zona Optimal Lapangan UAV\n(High Accuracy & Real-time FPS)", 
            ha='center', va='center', fontsize=9, color=SLATE, weight='bold', style='italic',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFFFFF', edgecolor=SLATE, alpha=0.85))

    ax.set_title("Analisis Trade-Off: Kecepatan Inferensi (FPS) vs Test mAP@50 (%)", 
                 fontsize=13, weight='bold', color=NAVY, pad=14)
    ax.set_xlabel("Kecepatan Inferensi Frame Per Second (FPS) [Batch Size = 1 pada RTX 5070]", 
                 fontsize=10.5, weight='bold', color=DARK_GRAY, labelpad=8)
    ax.set_ylabel("Test mAP@50 (%) pada 134 Citra Unseen", 
                 fontsize=10.5, weight='bold', color=DARK_GRAY, labelpad=8)
    
    ax.set_ylim(73, 96)
    ax.set_xlim(63, 98)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(title="Skala Model", title_fontsize='9.5', fontsize='8.5', loc='lower right', framealpha=0.95)
    
    plt.tight_layout()
    out_path = os.path.join(FIG_DIR, "fig2_fps_vs_map50_pareto.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved {out_path}")

# ==============================================================================
# 3. CLASS COMPARISON: Enemy vs Ally mAP@50
# ==============================================================================
def generate_enemy_vs_ally_chart():
    print("Generating Figure 3: Enemy vs Ally mAP@50 Comparison...")
    # Select top models and comparisons
    selected_runs = [
        'E0_yolo26n', 'E1_yolo26n', 'E4_yolo26n', 'E2_yolo26n', 
        'E3_yolo26s', 'E0_yolo26l', 'E1_yolo26m', 'E1_yolo26x', 
        'E0_yolo26x', 'E5_yolo26x'
    ]
    sub_df = df[df['Run'].isin(selected_runs)].copy()
    # Sort by enemy_map50 descending
    sub_df = sub_df.sort_values(by='enemy_map50', ascending=True)
    
    fig, ax = plt.subplots(figsize=(9, 6.2), dpi=300)
    y_pos = np.arange(len(sub_df))
    height = 0.38
    
    rects1 = ax.barh(y_pos + height/2, sub_df['enemy_map50'] * 100, height, 
                     label='Target Musuh (Enemy mAP@50)', color=NAVY, edgecolor='black', linewidth=0.6)
    rects2 = ax.barh(y_pos - height/2, sub_df['ally_map50'] * 100, height, 
                     label='Bukan Musuh (Ally mAP@50)', color=AMBER, edgecolor='black', linewidth=0.6)
    
    ax.set_yticks(y_pos)
    labels = []
    for run in sub_df['Run']:
        if run == 'E0_yolo26n':
            labels.append(f"{run} (#1 Overall)")
        elif run == 'E1_yolo26x':
            labels.append(f"{run} (#1 Large CBAM)")
        elif run == 'E0_yolo26x':
            labels.append(f"{run} (Baseline Large)")
        else:
            labels.append(run)
    ax.set_yticklabels(labels, fontsize=9.5, weight='semibold')
    
    ax.set_xlabel("Akurasi mAP@50 (%) pada Test Split", fontsize=10.5, weight='bold', color=DARK_GRAY, labelpad=8)
    ax.set_title("Komparasi Akurasi Deteksi Kelas Spesifik: Target Musuh (Enemy) vs Sekutu (Ally)", 
                 fontsize=12.5, weight='bold', color=NAVY, pad=14)
    
    # Add values on bars
    for rect in rects1:
        w = rect.get_width()
        ax.text(w + 0.5, rect.get_y() + rect.get_height()/2, f"{w:.1f}%", 
                va='center', ha='left', fontsize=8.5, weight='bold', color=NAVY)
    for rect in rects2:
        w = rect.get_width()
        ax.text(w + 0.5, rect.get_y() + rect.get_height()/2, f"{w:.1f}%", 
                va='center', ha='left', fontsize=8.5, weight='semibold', color="#975A16")
        
    # Highlight the E1_yolo26x vs E0_yolo26x delta
    ax.annotate("Delta CBAM: +6.92% Enemy mAP\n(79.89% -> 86.81%)",
                xy=(86.81, 6 + height/2), xytext=(65, 4.5),
                fontsize=9, weight='bold', color=RED,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF5F5', edgecolor=RED, lw=1.2),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=-0.2', color=RED, lw=1.5))

    ax.set_xlim(60, 102)
    ax.grid(True, linestyle='--', alpha=0.5, axis='x')
    ax.legend(loc='lower right', fontsize=9.5, framealpha=0.95)
    
    plt.tight_layout()
    out_path = os.path.join(FIG_DIR, "fig3_enemy_vs_ally_map50.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved {out_path}")

# ==============================================================================
# 4. TREND ACROSS SCALES: Topologies vs Capacity Scaling
# ==============================================================================
def generate_scale_trend_chart():
    print("Generating Figure 4: Topology Performance Across Scales...")
    fig, ax = plt.subplots(figsize=(8.5, 5.2), dpi=300)
    
    scales = ['n', 's', 'm', 'l', 'x']
    scale_labels = ['Nano (n)', 'Small (s)', 'Medium (m)', 'Large (l)', 'X-Large (x)']
    
    exp_styles = {
        'E0': ('E0 Baseline', '#4A5568', 'o', '-', 2.0),
        'E1': ('E1 (1x Backbone P5)', '#2B6CB0', 's', '-', 2.8),
        'E2': ('E2 (2x Backbone P4-P5)', '#319795', '^', '--', 1.8),
        'E3': ('E3 (3x Backbone P3-P5)', '#D69E2E', 'D', '--', 1.8),
        'E4': ('E4 (3x Neck Branches)', '#805AD5', 'v', '-.', 1.8),
        'E5': ('E5 (Full Comb. 6x CBAM)', '#E53E3E', 'X', ':', 2.2),
    }
    
    for exp, (label, color, marker, ls, lw) in exp_styles.items():
        sub = df[df['Exp'] == exp].set_index('Scale').reindex(scales)
        y_vals = sub['test_map50'] * 100
        ax.plot(range(len(scales)), y_vals, label=label, color=color, 
                marker=marker, linestyle=ls, linewidth=lw, markersize=7)
        
    ax.set_xticks(range(len(scales)))
    ax.set_xticklabels(scale_labels, fontsize=10, weight='semibold')
    ax.set_ylabel("Test mAP@50 (%)", fontsize=10.5, weight='bold', color=DARK_GRAY, labelpad=8)
    ax.set_xlabel("Skala Kapasitas Model YOLO26", fontsize=10.5, weight='bold', color=DARK_GRAY, labelpad=8)
    ax.set_title("Tren Performa Berdasarkan Kapasitas Parameter Model (Nano -> X-Large)", 
                 fontsize=12.5, weight='bold', color=NAVY, pad=14)
    
    ax.axhline(90, color='#38A169', linestyle='--', alpha=0.6, lw=1)
    ax.text(3.7, 90.5, "Ambang Sangat Tinggi (≥ 90%)", color='#276749', fontsize=8.5, weight='bold')

    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='lower left', fontsize=9, framealpha=0.95, ncol=2)
    ax.set_ylim(73, 95)
    
    plt.tight_layout()
    out_path = os.path.join(FIG_DIR, "fig4_cbam_topology_impact.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved {out_path}")

# ==============================================================================
# 5. CBAM ARCHITECTURE SCHEMATIC
# ==============================================================================
def generate_cbam_architecture_diagram():
    print("Generating Figure 5: CBAM Architecture Schematic...")
    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=300)
    ax.axis('off')
    
    # Title
    ax.text(0.5, 0.94, "Mekanisme Aliran Fitur Modular: Convolutional Block Attention Module (CBAM)", 
            ha='center', va='center', fontsize=12, weight='bold', color=NAVY)
    
    # Sub-boxes
    # 1. Input Features
    box_inp = dict(boxstyle='square,pad=0.6', facecolor='#EDF2F7', edgecolor=DARK_GRAY, lw=1.5)
    ax.text(0.08, 0.5, "Input Peta Fitur\nF ∈ ℝ^(C×H×W)", ha='center', va='center', fontsize=9.5, weight='bold', bbox=box_inp)
    
    # Arrow 1
    ax.annotate("", xy=(0.20, 0.5), xytext=(0.14, 0.5), arrowprops=dict(arrowstyle="->", lw=2, color=NAVY))
    
    # 2. Channel Attention Module (CAM)
    box_cam = dict(boxstyle='round,pad=0.8', facecolor='#EBF8FF', edgecolor=SLATE, lw=2)
    cam_text = (
        "Channel Attention Module (CAM)\n"
        "• AvgPool(F) & MaxPool(F) paralel\n"
        "• Shared MLP (Reduksi r=16)\n"
        "• Aktivasi Sigmoid: Mc(F)\n"
        "Fitur Modulasi Kanal: F' = Mc(F) ⊗ F"
    )
    ax.text(0.35, 0.5, cam_text, ha='center', va='center', fontsize=9, bbox=box_cam, color=NAVY)
    
    # Arrow 2
    ax.annotate("", xy=(0.53, 0.5), xytext=(0.48, 0.5), arrowprops=dict(arrowstyle="->", lw=2, color=NAVY))
    
    # 3. Spatial Attention Module (SAM)
    box_sam = dict(boxstyle='round,pad=0.8', facecolor='#FEFCBF', edgecolor=AMBER, lw=2)
    sam_text = (
        "Spatial Attention Module (SAM)\n"
        "• AvgPool(F') & MaxPool(F') kanal\n"
        "• Konvolusi 7×7 Filter\n"
        "• Aktivasi Sigmoid: Ms(F')\n"
        "Fitur Modulasi Spasial: F'' = Ms(F') ⊗ F'"
    )
    ax.text(0.68, 0.5, sam_text, ha='center', va='center', fontsize=9, bbox=box_sam, color="#744210")
    
    # Arrow 3
    ax.annotate("", xy=(0.86, 0.5), xytext=(0.81, 0.5), arrowprops=dict(arrowstyle="->", lw=2, color=NAVY))
    
    # 4. Refined Output
    box_out = dict(boxstyle='square,pad=0.6', facecolor='#C6F6D5', edgecolor=GREEN, lw=1.5)
    ax.text(0.92, 0.5, "Peta Fitur Final\nF'' (Refined)", ha='center', va='center', fontsize=9.5, weight='bold', bbox=box_out, color="#22543D")

    # Bottom notes
    ax.text(0.5, 0.1, "Catatan: CBAM mengekstrak 'fitur apa' (kanal) lalu 'di mana letaknya' (spasial) secara berurutan.", 
            ha='center', va='center', fontsize=9, style='italic', color=DARK_GRAY)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    
    plt.tight_layout()
    out_path = os.path.join(FIG_DIR, "fig5_cbam_architecture_diagram.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved {out_path}")

# ==============================================================================
# 6. INFERENCE SAMPLES: Extract and Assemble Grid
# ==============================================================================
def extract_sample_inferences():
    print("Generating Figure 6: Sample Inference Grid...")
    pred_path = os.path.join(os.path.dirname(__file__), "runs", "experiments", "all_test_evaluations", "E0_yolo26n", "val_batch0_pred.jpg")
    label_path = os.path.join(os.path.dirname(__file__), "runs", "experiments", "all_test_evaluations", "E0_yolo26n", "val_batch0_labels.jpg")
    
    img_pred = cv2.imread(pred_path)
    img_label = cv2.imread(label_path)
    
    # We want a 2x2 collage of distinct test frames with detections:
    # Cell 0: (0, 0) - top-left
    # Cell 1: (0, 1) - top-mid
    # Cell 2: (1, 0) - mid-left
    # Cell 3: (1, 1) - center
    c0 = img_pred[0:640, 0:640]
    c1 = img_pred[0:640, 640:1280]
    c2 = img_pred[640:1280, 0:640]
    c3 = img_pred[640:1280, 640:1280]
    
    top_row = np.hstack([c0, c1])
    bot_row = np.hstack([c2, c3])
    collage = np.vstack([top_row, bot_row])
    
    out_collage_path = os.path.join(FIG_DIR, "fig6_sample_inference_mosaic.jpg")
    cv2.imwrite(out_collage_path, collage, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"Saved {out_collage_path}")
    
    # Ground Truth vs Prediction Comparison (Cell 0 and Cell 1)
    print("Generating Figure 7: Ground Truth vs Prediction Comparison...")
    lbl0 = img_label[0:640, 0:640]
    prd0 = img_pred[0:640, 0:640]
    
    # Add clear header banner to each
    def add_banner(img, text, bg_color=(26, 54, 93)):
        canvas = np.full((640 + 40, 640, 3), bg_color, dtype=np.uint8)
        cv2.putText(canvas, text, (20, 28), cv2.FONT_HERSHEY_DUPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
        canvas[40:, :] = img
        return canvas
    
    banner_lbl = add_banner(lbl0, "Ground Truth Anotasi Manusia", bg_color=(60, 60, 60))
    banner_prd = add_banner(prd0, "Prediksi Deteksi E0_yolo26n (Test Set)", bg_color=(26, 54, 93))
    
    comp = np.hstack([banner_lbl, banner_prd])
    out_comp_path = os.path.join(FIG_DIR, "fig7_groundtruth_vs_prediction.jpg")
    cv2.imwrite(out_comp_path, comp, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"Saved {out_comp_path}")

    # Large Model Comparison: E0_yolo26x vs E1_yolo26x
    print("Generating Figure 8: Large Model Comparison (E0_yolo26x vs E1_yolo26x)...")
    pred_e0x = cv2.imread(os.path.join(os.path.dirname(__file__), "runs", "experiments", "all_test_evaluations", "E0_yolo26x", "val_batch0_pred.jpg"))
    pred_e1x = cv2.imread(os.path.join(os.path.dirname(__file__), "runs", "experiments", "all_test_evaluations", "E1_yolo26x", "val_batch0_pred.jpg"))
    
    if pred_e0x is not None and pred_e1x is not None:
        c_e0x = pred_e0x[0:640, 0:640]
        c_e1x = pred_e1x[0:640, 0:640]
        banner_e0x = add_banner(c_e0x, "Baseline E0_yolo26x (Enemy mAP: 79.89%)", bg_color=(90, 40, 40))
        banner_e1x = add_banner(c_e1x, "CBAM E1_yolo26x (Enemy mAP: 86.81% [+6.92%])", bg_color=(20, 80, 40))
        comp_x = np.hstack([banner_e0x, banner_e1x])
        out_comp_x = os.path.join(FIG_DIR, "fig8_large_model_cbam_comparison.jpg")
        cv2.imwrite(out_comp_x, comp_x, [cv2.IMWRITE_JPEG_QUALITY, 92])
        print(f"Saved {out_comp_x}")

if __name__ == "__main__":
    generate_heatmap()
    generate_pareto_chart()
    generate_enemy_vs_ally_chart()
    generate_scale_trend_chart()
    generate_cbam_architecture_diagram()
    extract_sample_inferences()
    print("All figures successfully generated in reports/figures/")
