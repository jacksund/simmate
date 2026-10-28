from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from .base import Predictor


class RandomForest(Predictor):
    """
    Averages many decision trees, each fit to a random sample of the rows. A good
    default: it needs no tuning, handles fingerprint bits and properties alike,
    and says which inputs matter most.
    """

    @classmethod
    def get_model(cls, classify: bool = False):
        model = RandomForestClassifier if classify else RandomForestRegressor
        return model(n_estimators=200, n_jobs=-1, random_state=0)
