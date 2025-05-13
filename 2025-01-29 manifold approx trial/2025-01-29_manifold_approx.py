# -*- coding: utf-8 -*-
"""
Created on Wed Jan 29 14:32:42 2025

@author: rotenbergnh
"""

import os
import json
import numpy as np
import sklearn.model_selection
import sklearn.preprocessing
import sklearn.decomposition
import matplotlib.pyplot as plt
import mplcursors
import sys
import datetime
import collections

"""
Inputs:
    - input_json_filepath: json file mapping identifiers to their embeddings vectors
    - cluster_labels_filepath: "None" or filepath to tsv with 2 columns: identifier, cluster_name
    - output_path: "None" if interactive, or path to a directory where images will be outputted

"""

if len(sys.argv) == 1:
    # change these as desired
    input_json_filepath = "processed_materials_embeddings.json"
    cluster_labels_filepath = "None"
    output_path = "tmp"
elif len(sys.argv) == 4:
    input_json_filepath, cluster_labels_filepath, output_path = sys.argv[1:]
else:
    raise Exception("expected len(sys.argv)==4")

# run_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
# global fig_idx
# fig_idx = 0

DISTANCE_METRIC = "cosine"


cluster_labels_dict = collections.defaultdict(lambda: "None") # defaults to None if key not in dict
if cluster_labels_filepath != "None":
    with open(cluster_labels_filepath, 'r') as readfp:
        for line in readfp:
            ID_i, cluster_name_i = line.strip().split('\t')
            cluster_labels_dict[ID_i] = cluster_name_i

### ********** should data be normalized???


rng = np.random.default_rng(0)

with open(input_json_filepath, 'r') as readfp:
    input_data_dict = json.load(readfp)
    
IDs, names, embeddings = input_data_dict['IDs'], input_data_dict['names'], np.asarray(input_data_dict['embeddings'])
cluster_names = np.asarray([cluster_labels_dict[ID] for ID in IDs])

train_emb, val_emb, train_IDs, val_IDs, train_names, val_names, train_cluster_names, val_cluster_names \
    = sklearn.model_selection.train_test_split(embeddings, IDs, names, cluster_names, train_size=0.8, random_state=rng.integers(4294967295))

scaled_embeddings = sklearn.preprocessing.StandardScaler().fit_transform(embeddings)
pca = sklearn.decomposition.PCA(random_state=rng.integers(4294967295))
pca_transformed_embeddings = pca.fit_transform(scaled_embeddings)

# source for PCA and plot code: https://www.youtube.com/watch?v=Lsue2gEM9D0
# copied from Noam's: Clustering v3.5-2023 07 25 developing PUKDEC with tuning.ipynb
# scaler = sklearn.preprocessing.StandardScaler()
# train_emb_scaled = scaler.fit_transform(train_emb)
# val_emb_scaled = scaler.transform(val_emb)
pca = sklearn.decomposition.PCA(n_components=20)
# train_pca_data = pca.fit_transform(train_emb_scaled)
# val_pca_data = pca.transform(val_emb_scaled)

train_pca_data = pca.fit_transform(train_emb)
val_pca_data = pca.transform(val_emb)

percents_variance = pca.explained_variance_ratio_*100
print("Explained variance for each principal component:", pca.explained_variance_ratio_)
labels = ['PC' + str(x+1) for x in range(len(percents_variance))]


def add_cursor_labels(names):
    crs = mplcursors.cursor(hover=True).connect(
        "add", lambda sel: sel.annotation.set_text(names[sel.index]))


# we could use the function below, so that when the code is run on the commandline,
# you don't run add_cursor_labels, which saves time
# def save_fig(dirpath):
#     if dirpath is None or dirpath=="None":
#         # add_cursor_labels
#         plt.show()
#     else:
#         plt.savefig(os.path.join(dirpath, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f') + '.png'))


# plot 1: scree plot
def scree_plot(pca, title="Scree plot", figsize=None):
  percents_variance = pca.explained_variance_ratio_*100
  labels = ['PC' + str(x+1) for x in range(pca.n_components_)]
  if figsize: plt.figure(figsize=figsize)
  plt.bar(x=range(1, len(labels)+1), height=percents_variance, tick_label=labels)
  for i in range(len(labels)):
    plt.text(i+1, percents_variance[i] + .5, f"{percents_variance[i]:.2f}", ha='center')
  plt.ylabel("Percentage of explained variance")
  plt.xlabel("Principal component")
  plt.title(title)
  plt.show()
  plt.savefig(os.path.join(output_path, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f') + '.png'))
scree_plot(pca, figsize=(10,5))

# plot 2: cumulative scree plot
def cum_scree_plot(pca, figsize=None):
  if figsize: plt.figure(figsize=figsize)
  labels = ['PC' + str(x+1) for x in range(pca.n_components_)]
  cumulative_explained_variance = [sum(pca.explained_variance_ratio_[:ind+1]) for ind in range(len(labels))]
  plt.plot(range(1, len(labels)+1), cumulative_explained_variance, scaley=False, )
  for i in range(len(labels)):
    plt.text(i+1, cumulative_explained_variance[i] + .01, f"{cumulative_explained_variance[i]:.2f}", ha='center')
  plt.xlabel("Principal component")
  plt.ylabel("Cumulative fraction of explained variance")
  plt.title("Cumulative fraction of variance explained by principal components")
  plt.show()
  plt.savefig(os.path.join(output_path, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f') + '.png'))
cum_scree_plot(pca, (10,5))


def PCA_plots(pca_data, percents_variance, extra_title = "", plot_2D=True, plot_3D=True, figsize_3D = None):
  # 2D:
  if plot_2D:
    plt.scatter(pca_data[:,0], pca_data[:,1], s=4)
    plt.title("2D PCA graph" + extra_title)
    plt.xlabel(f"PC1 - {round(percents_variance[0])}%")
    plt.ylabel(f"PC2 - {round(percents_variance[1])}%")
    add_cursor_labels(train_names)
    plt.show()
    plt.savefig(os.path.join(output_path, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f') + '.png'))

  # 3D:
  if plot_3D:
    if figsize_3D: plt.figure(figsize = figsize_3D)
    ax = plt.axes(projection="3d")
    ax.scatter3D(pca_data[:,0], pca_data[:,1], pca_data[:,2], s=4)
    ax.set_xlabel(f"PC1 - {round(percents_variance[0])}%")
    ax.set_ylabel(f"PC2 - {round(percents_variance[1])}%")
    ax.set_zlabel(f"PC3 - {round(percents_variance[2])}%")
    plt.title("3D PCA graph" + extra_title)
    add_cursor_labels(train_names)
    plt.show()
    plt.savefig(os.path.join(output_path, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f') + '.png'))


PCA_plots(train_pca_data, percents_variance, plot_3D=False)
PCA_plots(train_pca_data, percents_variance, figsize_3D = (14,12), plot_2D=False)

# other manifold learning
import sklearn.manifold

def plot_manifold(model, title, train_data, val_data, train_data_labels, kwargs = {}):

    x, y = model.fit_transform(train_data, **kwargs).T
    plt.figure()
    
    # graph 1
    plt.scatter(x, y, label='train')
    add_cursor_labels(train_names)
    try:
        x_t, y_t = model.transform(val_data).T
        plt.scatter(x_t, y_t, label='validation')
        plt.legend()
    except:
        print("unable to put val/test data on", title)
    
    plt.title(title) # + f" (metric={kwargs.get('metric')})")
    plt.show()
    plt.savefig(os.path.join(output_path, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f') + '.png'))
    
    
    # graph 2
    if len(np.unique(train_data_labels)) > 1:
        plt.figure()
        for cluster_name in np.unique(train_data_labels):
            plt.scatter(x[train_data_labels == cluster_name], y[train_data_labels == cluster_name], label=cluster_name) #, s=4)
        plt.title(title + " by cluster names")
        plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
        plt.show()
        plt.savefig(os.path.join(output_path, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f') + '.png'))

  # # graph 3
  # X2 = df_manifold.dropna(subset = df_cols + ['90days-mRS'])[df_cols].to_numpy()
  # Y2 = df[(df["Dataset"] == "training") & (df["random_group"] < 5.1)].dropna(subset = df_cols + ['90days-mRS'])['90days-mRS'].to_numpy()

  # x, y = model.fit_transform(X2).T
  # for i in range(7):
  #   plt.scatter(x[Y2==i], y[Y2==i], s=4+4*i, label=f"mRS-90 = {i}")
  # plt.title(title + " with mRS-90")
  # plt.legend()
  # # plt.show()
  # plt.savefig(os.path.join(output_path, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f') + '.png'))


# df[QFV_vascular_cols].describe()

# for all techniques, could adjust distance metric, n_components

plot_manifold(sklearn.decomposition.PCA(n_components=2, random_state=0), "PCA", train_emb, val_emb, train_cluster_names)
plot_manifold(sklearn.manifold.MDS(random_state=0), "MDS", train_emb, val_emb, train_cluster_names)
plot_manifold(sklearn.manifold.Isomap(metric=DISTANCE_METRIC), f"Isomap w/ {DISTANCE_METRIC} metric", train_emb, val_emb, train_cluster_names) # could tune n_neighbors
plot_manifold(sklearn.manifold.LocallyLinearEmbedding(random_state=0), "LLE", train_emb, val_emb, train_cluster_names) # could tune n_neighbors
plot_manifold(sklearn.manifold.SpectralEmbedding(random_state=0), "Spectral Embedding", train_emb, val_emb, train_cluster_names) # could tune n_neighbors, gamma
plot_manifold(sklearn.manifold.TSNE(metric=DISTANCE_METRIC, random_state=0), f"TSNE w/ {DISTANCE_METRIC} metric", train_emb, val_emb, train_cluster_names) # could tune perplexity, early exaggeration
plot_manifold(sklearn.manifold.TSNE(random_state=0), "TSNE (default distance metric)", train_emb, val_emb, train_cluster_names) # could tune perplexity, early exaggeration

# tune t-SNE
for perplexity in [5, 10, 60, 80]:
    plot_manifold(sklearn.manifold.TSNE(metric=DISTANCE_METRIC, random_state=0, perplexity=perplexity), 
                  f"TSNE (perplexity={perplexity}, metric={DISTANCE_METRIC})", train_emb, val_emb, train_cluster_names)
