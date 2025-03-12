#!/bin/bash

# activate python environment
source /home/rotenbergnh/bert_env/bin/activate

# save embeddings from SAPBERT in a json
python 2025-01-29_SAPBERT_for_CDE_clusters.py ../sample_cde_batch_2025_02_20.tsv 2025-03-12_SAPBERT_trial_embeddings-IDENTICAL_noam.json

# run manifold approximation analysis; create a folder to save plots
python 2025-01-29_manifold_approx.py 2025-03-12_SAPBERT_trial_embeddings-IDENTICAL_noam.json ../sample_cde_clusters_manual.tsv 2025-03-12_plot_IDENTICAL_noam
