import nbformat

with open('model_analysis.ipynb', 'r') as f:
    nb = nbformat.read(f, as_version=4)

new_markdown = nbformat.v4.new_markdown_cell("""## Validation: Ward Hierarchical Clustering

To validate the similarity findings, we apply Ward hierarchical clustering on the properly weighted primary embedding. This will allow us to see if Brás and its top matches naturally fall into the same urban typology cluster.""")

new_code = nbformat.v4.new_code_cell("""from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
import scipy.cluster.hierarchy as sch

# Iterate through k=3 to 8 as specified in the implementation plan
print("\\n--- WARD CLUSTERING: SILHOUETTE SCORES ---")
silhouette_scores = {}
for k in range(3, 9):
    ward = AgglomerativeClustering(n_clusters=k, linkage='ward')
    labels = ward.fit_predict(E_df.values)
    score = silhouette_score(E_df.values, labels)
    silhouette_scores[k] = score
    print(f"k={k} clusters: Silhouette Score = {score:.4f}")

# Choose the k with the highest silhouette score
best_k = max(silhouette_scores, key=silhouette_scores.get)
print(f"\\nOptimal number of clusters (highest silhouette score): {best_k}")

# Fit final model with best_k
ward_final = AgglomerativeClustering(n_clusters=best_k, linkage='ward')
cluster_labels = ward_final.fit_predict(E_df.values)

# Add cluster labels to our DataFrame
df['cluster'] = cluster_labels

# 1. Analyze Brás's Cluster
bras_cluster = df.loc[bras_id, 'cluster']
print(f"\\nBrás is in Cluster {bras_cluster}. Other districts in this cluster:")
bras_cluster_members = df[df['cluster'] == bras_cluster][['district_name']].copy()
bras_cluster_members['equal_weight_rank'] = res['rank']
# Fill rank 0 for Brás itself
bras_cluster_members.loc[bras_id, 'equal_weight_rank'] = 0
bras_cluster_members = bras_cluster_members.sort_values('equal_weight_rank')
display(bras_cluster_members)

# 2. Plot Dendrogram
plt.figure(figsize=(15, 7))
plt.title('Ward Hierarchical Clustering Dendrogram (Primary Embedding)')
dendrogram = sch.dendrogram(sch.linkage(E_df.values, method='ward'), 
                            labels=df['district_name'].values,
                            leaf_rotation=90, 
                            leaf_font_size=8)
plt.ylabel('Euclidean distances')
plt.tight_layout()
plt.show()

# 3. Plot PCA with Cluster Labels
pca_df['cluster'] = cluster_labels
plt.figure(figsize=(10, 8))
# We use a distinct color palette for the clusters
palette = sns.color_palette('tab10', n_colors=best_k)

for c in range(best_k):
    cluster_data = pca_df[pca_df['cluster'] == c]
    sns.scatterplot(data=cluster_data, x='PC1', y='PC2', color=palette[c], s=60, label=f'Cluster {c}')

# Highlight Brás
sns.scatterplot(data=bras_df, x='PC1', y='PC2', color='black', s=250, marker='*', edgecolor='white', label='Brás')
plt.text(bras_df['PC1'].values[0] + 0.1, bras_df['PC2'].values[0] + 0.1, 'Brás', weight='bold', color='black')

plt.title(f'Districts Projected onto PC1 and PC2 (Colored by Ward Clusters, k={best_k})')
plt.legend()
plt.tight_layout()
plt.show()""")

nb.cells.extend([new_markdown, new_code])

with open('model_analysis.ipynb', 'w') as f:
    nbformat.write(nb, f)

print("Notebook updated with Ward clustering!")
