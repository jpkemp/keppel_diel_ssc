from sklearn.decomposition import PCA
from sklearn.preprocessing import scale

def pca_nd(data, n=2):
    # df = (data - data.min()) / (data.max() - data.min()).astype(float)
    df = scale(data)
    pca = PCA(n_components=n)
    pca.fit(df)
    output = pca.transform(df)
    weights =  pca.components_
    variance = pca.explained_variance_ratio_

    return output, weights, variance