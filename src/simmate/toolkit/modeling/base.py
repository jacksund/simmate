from dataclasses import dataclass

import numpy as np
from scipy.stats import spearmanr
from sklearn import metrics
from sklearn.impute import SimpleImputer
from sklearn.model_selection import (
    GroupKFold,
    KFold,
    StratifiedKFold,
    cross_val_predict,
)
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler


@dataclass
class CrossValidation:
    """What `Predictor.cross_validate` gives for a column of targets."""

    predictions: np.ndarray
    """One per row. Rows with a target get the prediction from the fold that left
    them out (so it's an honest guess), and rows without one get the final model's."""
    known: np.ndarray
    """By row: True where a target was given."""
    metrics: dict[str, float]
    """How well the held-out predictions match the targets: R², MAE, RMSE, and
    Spearman ρ for numbers, or accuracy, balanced accuracy, and ROC AUC (two classes
    only) for labels."""
    estimator: Pipeline
    """The final model, fit on every row with a target."""
    classes: list | None = None
    """The labels, in the order of `probabilities`' columns (labels only)."""
    probabilities: np.ndarray | None = None
    """Each row's probability of each label, held out like `predictions` (labels only)."""
    confusion: np.ndarray | None = None
    """How often each true label (row) was predicted as each label (column), in the
    order of `classes` (labels only)."""
    importances: np.ndarray | None = None
    """Each input's share of the final model's importance (summing to 1), or None
    for models that don't give one."""


class Predictor:
    """
    A base class for models that predict a column (numbers or labels) from a
    matrix of inputs, e.g. molecular properties and/or fingerprint bits, one row
    per molecule.

    Subclasses give their scikit-learn model with `get_model`. It's fit after any
    missing inputs (NaN) are filled with their column's median, and after scaling
    each input when `scale_inputs` is set (for linear models).
    """

    scale_inputs: bool = False

    @classmethod
    def get_model(cls, classify: bool = False):
        raise NotImplementedError("a get_model method must be defined")

    @classmethod
    def get_estimator(cls, classify: bool = False) -> Pipeline:
        # all-empty inputs are kept (as zeros), so importances line up with the inputs
        steps = [SimpleImputer(strategy="median", keep_empty_features=True)]
        if cls.scale_inputs:
            steps.append(StandardScaler())
        return make_pipeline(*steps, cls.get_model(classify))

    @classmethod
    def cross_validate(
        cls,
        features: np.ndarray,
        targets: np.ndarray,
        classify: bool = False,
        n_folds: int = 5,
        groups: np.ndarray | None = None,
        random_state: int = 0,
    ) -> CrossValidation:
        """
        Scores the model by k-fold cross-validation on the rows with a target, then
        fits it on all of them to predict the rest.

        Args:
            features: The inputs, one row per molecule (NaN where missing).
            targets: One per row: numbers (NaN where missing), or labels (None
                where missing) when `classify`.
            classify: Whether the targets are labels rather than numbers.
            n_folds: How many folds to split the rows with a target into.
            groups: One per row, e.g. each molecule's scaffold. Rows of a group are
                kept in the same fold, so the model is scored on groups it hasn't
                seen. Otherwise rows are split at random (keeping each label's share
                in every fold when `classify`).
            random_state: Seeds the random split.

        Returns:
            The predictions, scores, and final model (see `CrossValidation`).
        """
        features = np.asarray(features)
        if classify:
            targets = np.asarray(targets, dtype=object)
            known = np.array([target is not None for target in targets], dtype=bool)
        else:
            targets = np.asarray(targets, dtype=float)
            known = ~np.isnan(targets)
        if not known.any():
            raise ValueError("None of the rows have a target to learn from")
        x, y = features[known], targets[known]
        if classify:
            y = y.astype(str)

        if groups is not None:
            folds = GroupKFold(n_splits=n_folds)
            groups = np.asarray(groups)[known]
        elif classify:
            folds = StratifiedKFold(
                n_splits=n_folds, shuffle=True, random_state=random_state
            )
        else:
            folds = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)
        held_out = cross_val_predict(
            cls.get_estimator(classify),
            x,
            y,
            cv=folds,
            groups=groups,
            method="predict_proba" if classify else "predict",
        )
        estimator = cls.get_estimator(classify).fit(x, y)

        result = CrossValidation(
            predictions=np.full(len(targets), np.nan),
            known=known,
            metrics={},
            estimator=estimator,
        )
        if classify:
            # sorted, as predict_proba's columns are
            classes = estimator.classes_.tolist()
            labels = np.array(classes, dtype=object)[held_out.argmax(axis=1)]
            result.classes = classes
            result.predictions = np.full(len(targets), None, dtype=object)
            result.predictions[known] = labels
            result.probabilities = np.full((len(targets), len(classes)), np.nan)
            result.probabilities[known] = held_out
            if (~known).any():
                result.predictions[~known] = estimator.predict(features[~known])
                result.probabilities[~known] = estimator.predict_proba(features[~known])
            result.confusion = metrics.confusion_matrix(y, labels, labels=classes)
            result.metrics = {
                "accuracy": float(metrics.accuracy_score(y, labels)),
                "balanced_accuracy": float(metrics.balanced_accuracy_score(y, labels)),
            }
            if len(classes) == 2:
                result.metrics["roc_auc"] = float(
                    metrics.roc_auc_score(y == classes[1], held_out[:, 1])
                )
        else:
            result.predictions[known] = held_out
            if (~known).any():
                result.predictions[~known] = estimator.predict(features[~known])
            result.metrics = {
                "r2": float(metrics.r2_score(y, held_out)),
                "mae": float(metrics.mean_absolute_error(y, held_out)),
                "rmse": float(metrics.root_mean_squared_error(y, held_out)),
                "spearman": float(spearmanr(y, held_out).statistic),
            }

        model = estimator[-1]  # the pipeline's last step
        if hasattr(model, "feature_importances_"):
            importances = np.asarray(model.feature_importances_)
        elif hasattr(model, "coef_"):
            # coefficients of scaled inputs are comparable; average over classes
            importances = np.abs(np.atleast_2d(model.coef_)).mean(axis=0)
        else:
            importances = None
        if importances is not None and importances.sum() > 0:
            result.importances = importances / importances.sum()
        return result
