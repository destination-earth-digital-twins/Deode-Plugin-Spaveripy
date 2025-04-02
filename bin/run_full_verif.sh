#!/bin/bash
# Script: run_full_verif.sh
# Description: Automates the process of verification and comparison with Global DT.
# Usage: ./run_full_verif.sh -u <ecfs_user> -c <case> -o <obs>
set -x
# initialise arguments
ECFS_USER=""
GENERAL_CASE=""
OBS_VERIF=""

usage() {
  echo "Usage: $0 -u <ecfs_user> -c <case> -o <obs>"
  echo "Example: $0 -u aut6432 -c CY46h1_HARMONIE_AROME_nwp_ESP_20241029_conve_2_20241029 -o IMERG_pcp -y YY -m MM -d DD -t TYPE -n NUMBER -s CSC"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case $1 in
    -u)
      ECFS_USER="$2"
      shift 2
      ;;
    -c)
      GENERAL_CASE="$2"
      shift 2
      ;;
    -o)
      OBS_VERIF="$2"
      shift 2
      ;;
    -y)
      YY="$2"
      shift 2
      ;;
    -m)
      MM="$2"
      shift 2
      ;;
    -d)
      DD="$2"
      shift 2
      ;;
    -t)
      TYPE="$2"
      shift 2
      ;;
    -n)
      NUMBER="$2"
      shift 2
      ;;
    -s)
      CSC="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      usage
      ;;
  esac
done

if [[ -z "$ECFS_USER" || -z "$GENERAL_CASE" || -z "$OBS_VERIF" ]]; then
  echo "Error: Missing required arguments"
  usage
fi

# source environment variables from verif_plugin.toml
plugin_toml=verif_plugin.toml
export $(grep -E '^\s*[A-Z_]+\s*=' $plugin_toml | sed -E 's/\s*=\s*/=/' | tr -d '"' | awk '{print $1}')

if [[ -z "$TOMLS_DIR" || -z "$PLUGIN_DIR" || -z "$DW_DIR" || -z "$TOOL_DIR" || -z "$LAUNCHS_DIR" ]]; then
  echo "Error: Missing required environment"
  exit 1
fi



# constants
SOURCE_DIR="ec:/$ECFS_USER/DE_NWP/deode/$YY/$MM/$DD/00/$TYPE/$NUMBER/$CSC/"
#SOURCE_DIR="/ec/res4/scratch/$ECFS_USER/deode"
SRC_FILENAME="$SOURCE_DIR/config.toml"
#SRC_FILENAME="$SOURCE_DIR/$GENERAL_CASE/archive/config.toml"
DEST_FILENAME="$TOMLS_DIR/$YY/$DD/$MM/$TYPE/$NUMBER/$CSC/$GENERAL_CASE.toml"
VERIF_CONF="$PLUGIN_DIR/verif_configuration"
VERIF_PLUGIN_TOML="$PLUGIN_DIR/verif_plugin.toml"
VERIF_TOML="$TOMLS_DIR/$YY/$DD/$MM/$TYPE/$NUMBER/$CSC/${GENERAL_CASE}_verif.toml"
TASK="updateref"
TASK_LOG="$LAUNCHS_DIR/$TASK.log"
LAUNCH_TEMPLATE_SCRIPT="$PLUGIN_DIR/bin/launch_spatial_verif.template.sh"

mkdir -p $TOMLS_DIR/$YY/$DD/$MM/$TYPE/$NUMBER/$CSC/
# Perform the copy
ecp "$SRC_FILENAME" "$DEST_FILENAME"
#cp "$SRC_FILENAME" "$DEST_FILENAME"

# Replace arguments
sed -i "2c\\$DEST_FILENAME" "$VERIF_CONF"
sed -i "s/^\(  VERIF_OBS = \).*/\1\"$OBS_VERIF\"/" "$VERIF_PLUGIN_TOML"
sed -i "s/^\(  ECFS_USER = \).*/\1\"$ECFS_USER\"/" "$VERIF_PLUGIN_TOML"

# Start suite
cd "$DW_DIR"
poetry run deode case "?$VERIF_CONF" -o "$VERIF_TOML" --start-suite

# Update config exp_ref
poetry run deode run --config-file "$VERIF_TOML" --task "$TASK" --template "$DW_DIR/deode/templates/stand_alone.py" --job "$TASK.job" --output "$TASK_LOG"

# wait 60 s to finish the task and get the info of the DW's case
sleep 60
CASE=$(grep "CASE VALUE:" "$TASK_LOG" | awk '{print $3}')
EXP=$(grep "EXP VALUE:" "$TASK_LOG" | awk '{print $3}')
EXP_REF=$(grep "EXP REF VALUE:" "$TASK_LOG" | awk '{print $4}')

# perform verification for reference experiment and run comparison
LAUNCH_SCRIPT="$LAUNCHS_DIR/launch_spatial_verif_${CASE}.sh"
mkdir -p $LAUNCHS_DIR   # Create this dir if it doesn't exist
cp "$LAUNCH_TEMPLATE_SCRIPT" "$LAUNCH_SCRIPT"
sed -i "1a #SBATCH --chdir=$LAUNCHS_DIR" "$LAUNCH_SCRIPT"
sed -i "s|^VERIF_DIR=\".*\"|VERIF_DIR=\"$TOOL_DIR\"|" "$LAUNCH_SCRIPT"
sed -i "s/^OBS=\"[^\"]*\"/OBS=\"$OBS_VERIF\"/" "$LAUNCH_SCRIPT"
sed -i "s/^Case=\"[^\"]*\"/Case=\"$CASE\"/" "$LAUNCH_SCRIPT"
sed -i "s/^exp_ref=\"[^\"]*\"/exp_ref=\"$EXP_REF\"/" "$LAUNCH_SCRIPT"
sed -i "s/^exp=\"[^\"]*\"/exp=\"$EXP\"/" "$LAUNCH_SCRIPT"

cd "$LAUNCHS_DIR"
sbatch "$LAUNCH_SCRIPT"
