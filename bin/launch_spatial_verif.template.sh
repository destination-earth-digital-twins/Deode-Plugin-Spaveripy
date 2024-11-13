#!/bin/bash
#SBATCH --job-name=spaverif
#SBATCH --output=logs/log-%J.out
#SBATCH --error=logs/err-%J.out
#SBATCH --time=12:00:00
#SBATCH --mem=32G
module load python3/3.11.8-01

VERIF_DIR=""
OBS=""
Case=""
exp_ref=""
exp=""

cd "$VERIF_DIR"
echo "running hourly spatial verification for ${Case} case study"
#python3 main.py --obs "$OBS" --case "$Case" --exp "$exp" --link_obs --run_regrid --run_plot_regrid --run_verif --run_panels
python3 main.py --obs "$OBS" --case "$Case" --exp "$exp_ref" --link_obs --run_regrid --run_plot_regrid --run_verif --run_panels
python3 main.py --obs "$OBS" --case "$Case" --exp "$exp" --exp_ref "$exp_ref" --run_comparison
