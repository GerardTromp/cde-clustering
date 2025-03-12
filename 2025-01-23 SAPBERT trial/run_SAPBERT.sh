#!/bin/bash

# command-line args:
#    1: directory of xml files

source /home/rotenbergnh/bert_env/bin/activate

SAPBERT_PATH="${BASE_PATH}/SAPBERT"
python "${SAPBERT_PATH}/2024-11-29_normalize_SAPBERT_for_pipeline.py" "${SAPBERT_PATH}/cell_types.tsv" "${SAPBERT_PATH}/cell_types_manual.tsv" . "${SAPBERT_PATH}/ABBR_XML_DIR" $RESULTS_DIR $RESULTS_DIR 0.45
