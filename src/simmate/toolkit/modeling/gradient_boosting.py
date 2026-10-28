from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
)

from .base import Predictor


class GradientBoosting(Predictor):
    """
    Adds up a series of small decision trees, each fit to what the ones before it
    got wrong. Often the most accurate on larger datasets, though it doesn't say
    which inputs matter most.
    """

    @classmethod
    def get_model(cls, classify: bool = False):
        model = (
            HistGradientBoostingClassifier
            if classify
            else HistGradientBoostingRegressor
        )
        return model(random_state=0)
