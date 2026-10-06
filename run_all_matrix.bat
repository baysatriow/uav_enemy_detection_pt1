@echo off

:: -----------------------------------------------------------------------------
:: YOLO26 CBAM Complete Matrix Training Runner (E0-E5 across all model scales)
:: Scales: n (nano), s (small), m (medium), l (large), x (xlarge)
:: Total: 30 training runs
:: -----------------------------------------------------------------------------

cd /d "%~dp0"

echo =====================================================================
echo  YOLO26 CBAM EXPERIMENT MATRIX RUNNER (ALL SCALES: n, s, m, l, x)
echo =====================================================================

:: Set Roboflow API Key
if "%ROBOFLOW_API_KEY%"=="" (
    set ROBOFLOW_API_KEY=2oeGI3QWbiYo6HNrErIp
    echo [*] Configured ROBOFLOW_API_KEY.
) else (
    echo [*] Using existing ROBOFLOW_API_KEY from environment.
)

for %%S in (n s m l x) do (
    echo.
    echo =====================================================================
    echo  STARTING MODEL SCALE: %%S [Experiments E0 to E5]
    echo =====================================================================
    python experiments\scripts\run_matrix.py --model-size %%S
)

echo.
echo =====================================================================
echo  ALL 30 TRAINING RUNS COMPLETED!
echo  Running E6 final analysis and ranking...
echo =====================================================================

python experiments\scripts\analyze_e6.py --metric val_map50 --split test

echo.
echo [DONE] Matrix execution complete. Results saved in runs/experiments/
pause
