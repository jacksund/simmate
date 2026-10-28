import numpy as np
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.pipeline import Pipeline, make_pipeline

from .base import CrossValidation, Predictor


class TanimotoKnn(Predictor):
    """
    Predicts each molecule from its 5 most similar molecules by Tanimoto
    similarity, weighting closer ones more. It takes fingerprint bits alone, as
    Tanimoto similarity compares bits (it's the Jaccard index of their on bits).
    """

    @classmethod
    def get_estimator(cls, classify: bool = False) -> Pipeline:
        # bits are never missing or scaled, so the model is the only step
        model = KNeighborsClassifier if classify else KNeighborsRegressor
        return make_pipeline(model(n_neighbors=5, weights="distance", metric="jaccard"))

    @classmethod
    def cross_validate(cls, features: np.ndarray, *args, **kwargs) -> CrossValidation:
        features = np.asarray(features, dtype=float)
        if not np.isin(features, (0, 1)).all():
            raise ValueError(
                "Tanimoto k-NN compares fingerprint bits, so its inputs must be a "
                "fingerprint alone"
            )
        return super().cross_validate(features.astype(bool), *args, **kwargs)
