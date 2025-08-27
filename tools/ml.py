from sklearn.decomposition import PCA

def pca_nd(data, n=2):
    normalized_df=(data - data.min()) / (data.max() - data.min()).astype(float)
    pca = PCA(n_components=n)
    pca.fit(normalized_df)
    output = pca.transform(normalized_df)
    weights =  pca.components_
    variance = pca.explained_variance_ratio_

    return output, weights, variance