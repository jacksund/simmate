from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import Ridge as sk_Ridge

from .base import Predictor


class Ridge(Predictor):
    """
    A linear model with a penalty on large coefficients, so it copes with many
    inputs (e.g. fingerprint bits). Labels are predicted with logistic regression.
    """

    scale_inputs = True

    @classmethod
    def get_model(cls, classify: bool = False):
        return LogisticRegression(max_iter=1000) if classify else sk_Ridge()
