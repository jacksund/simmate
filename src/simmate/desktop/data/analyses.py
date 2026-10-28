from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
import polars

from simmate.desktop.data.columns import CATEGORY, DATE, NUMBER
from simmate.desktop.data.dataset import ToolkitDataset
from simmate.desktop.data.features import FEATURES, FINGERPRINTS, compute_features
from simmate.toolkit.modeling import (
    GradientBoosting,
    LinearFit,
    RandomForest,
    Ridge,
    TanimotoKnn,
)

PREDICT = "Predict"
STATISTICS = "Statistics"
SAR = "SAR"
PRIORITIZE = "Prioritize"

# The kinds of input an analysis's form can have (see `Setting`)
COLUMN = "column"  # one column
COLUMNS = (
    "columns"  # any number of columns (and maybe fingerprints), picked from a list
)
CHOICE = "choice"
INTEGER = "integer"

# The Featurize panel's fingerprints, which models can take as inputs, by name
FINGERPRINT_FEATURES = {
    feature.name: feature for feature in FEATURES if feature.section == FINGERPRINTS
}

MODELS = {
    "Random forest": RandomForest,
    "Gradient boosting": GradientBoosting,
    "Ridge": Ridge,
    "Tanimoto k-NN": TanimotoKnn,
}

# Bars and tables of results show at most this many rows (e.g. a model's most
# important inputs).
TOP_ROWS = 10


@dataclass
class Setting:
    """One input of an analysis's form in the Analyze panel."""

    key: str  # the argument of the analysis's `run` it's passed as
    label: str
    kind: str  # COLUMN, COLUMNS, CHOICE, or INTEGER
    column_kinds: tuple[str, ...] = ()
    """The kinds of column on offer (COLUMN and COLUMNS)."""
    fingerprints: bool = False
    """(COLUMNS) Whether to offer the Featurize panel's fingerprints too (see
    `FINGERPRINT_FEATURES`), above the columns, when the dataset has molecules."""
    choices: list[str] = field(default_factory=list)  # CHOICE
    default: object = None
    """What it starts at: a column's name (COLUMN), a list of names to tick
    (COLUMNS), a choice, or a number."""
    excluding: str | None = None
    """(COLUMNS) The key of a COLUMN setting (e.g. the column to predict) whose
    column can't be picked. Columns named after it (e.g. "pIC50_pred") are
    unpicked when it changes, so a model never learns from an earlier one's
    predictions."""
    minimum: int = 0  # INTEGER
    maximum: int = 100  # INTEGER
    help: str = ""
    """What it means and how to choose (rich text), behind its "?" button."""


@dataclass
class AnalysisResult:
    """What an analysis gives, shown as a card in the Analyze panel. Every part but
    the title is optional."""

    title: str  # e.g. "Predict pIC50"
    subtitle: str = ""  # e.g. the model used
    scores: list[tuple[str, str]] = field(default_factory=list)
    """Headline numbers, as (name, value) pairs shown as tiles, e.g. ("R²", "0.62")."""
    verdict: tuple[str, str] | None = None
    """How good the result is, in words: a level ("strong", "moderate", "weak", or
    "none") and a few words on why."""
    equation: str | None = None  # e.g. a fit's
    details: list[tuple[str, str]] = field(default_factory=list)
    """Facts about the run, as (label, value) pairs, e.g. ("From", "ECFP4")."""
    confusion: tuple[list[str], np.ndarray] | None = None
    """A classification's labels, and how many rows of each actual label (rows)
    got each predicted label (columns)."""
    bars: list[tuple[str, float]] | None = None
    """Shares of a whole (0 to 1) drawn as bars, largest first, e.g. how much a
    model relies on each input."""
    bars_title: str = ""
    table: polars.DataFrame | None = None
    """Shown as a sortable table."""
    table_rows: list[list[int]] | None = None
    """The dataset rows behind each of the table's rows, which hovering or clicking
    it highlights or selects."""
    columns: polars.DataFrame | None = None
    """To add to the dataset (one value per row), replacing any of the same name."""
    plot: tuple[str, dict] | None = None
    """A plot of the result to offer, as the plot's name (see `PLOT_TYPES`) and its
    settings (see `PlotPanel.apply_config`)."""
    plot_label: str = "Show plot"  # its button's text
    help: str = ""
    """How to read the result (rich text), behind its "?" button."""


@dataclass
class Analysis:
    """
    One option in the Analyze panel: something worked out from every row of the
    dataset at once. See `ANALYSES`.
    """

    name: str  # as listed in the panel
    section: str
    description: str
    settings: list[Setting]
    run: Callable[..., AnalysisResult]
    """Called on a background thread with the dataset and each setting's value
    (by its key). It mustn't change the dataset: columns to add go in its result."""
    slow: bool = False  # asks first past `SLOW_FEATURE_ROWS` rows, as Featurize does


REGRESSION_HELP = """
<b>How to read this</b><br>
Every score compares the model's predictions for rows it never saw (held out by
cross-validation) with their actual values.
<ul>
<li><b>R²</b>: the share of the variation the model predicts. 1 is perfect, 0 is
no better than guessing the average, and below 0 is worse.</li>
<li><b>MAE</b>: the typical error, in the column's own units.</li>
<li><b>RMSE</b>: like MAE, but large misses count more.</li>
<li><b>Spearman ρ</b>: how well the predictions rank the rows, from 1 (the same
order) to 0 (no relation). This matters most when picking the best compounds.</li>
</ul>
The bars show how much the model relies on each input. The parity plot puts each
row's actual value against its prediction: the closer the points are to a
diagonal line, the better.
"""

CLASSIFICATION_HELP = """
<b>How to read this</b><br>
Every score compares the model's predictions for rows it never saw (held out by
cross-validation) with their actual labels.
<ul>
<li><b>Accuracy</b>: the share of rows given the right label.</li>
<li><b>Balanced accuracy</b>: the average of each label's accuracy, so a rare
label counts as much as a common one. Always guessing the common label of two
scores 50%.</li>
<li><b>ROC AUC</b> (two labels only): how well the model's probabilities tell the
labels apart. 1 is perfect, and 0.5 is no better than chance.</li>
</ul>
The grid counts rows by their actual label (down) and predicted label (across).
The shaded diagonal is the rows it got right.
"""

LINEAR_FIT_HELP = """
<b>How to read this</b><br>
The equation is the straight line (or plane) closest to the data, by least
squares. Each coefficient is how much the fitted column changes for each unit of
that column, with the others held fixed.
<ul>
<li><b>R²</b>: the share of the variation the fit explains, from 0 (none) to 1
(all).</li>
<li><b>Adjusted R²</b>: R² less a penalty for each column used. Compare fits of
different columns with it.</li>
<li><b>p-value</b>: the chance of a coefficient this far from 0 if the column had
no real effect. Below 0.05 is the usual sign that a column matters.</li>
</ul>
Unlike Predict a column, these scores come from the same rows the line was fit
to, so they flatter it.
"""


def predict_column(
    dataset: ToolkitDataset,
    target: str,
    inputs: list[str],
    model: str,
    folds: int,
) -> AnalysisResult:
    """Fits `model` to predict `target` from `inputs` (columns and/or fingerprints,
    see `input_matrix`), scored by `folds`-fold cross-validation (see
    `Predictor.cross_validate`). A number column gives a regression, and a category
    column a classification.

    Adds `<target>_pred` (each row's prediction: held out where the row has a
    value, else the final model's), then `<target>_residual` (the value minus its
    prediction) for numbers, or `<target>_probability` (how likely the predicted
    label is) for categories."""
    if not target:
        raise ValueError("Choose a column to predict")
    if not inputs:
        raise ValueError("Choose at least one input in “From”, e.g. ECFP4")
    classify = dataset.columns.kinds[target] == CATEGORY
    features, owners, new = input_matrix(dataset, inputs)
    if classify:
        # labels as text (e.g. "true" for booleans), with nulls kept as missing
        targets = dataset.df[target].cast(polars.String).to_numpy()
    else:
        targets = dataset.columns.numbers(target)
    # rows without a readable structure have no fingerprint, so they're left out
    bits = np.array([owner in FINGERPRINT_FEATURES for owner in owners])
    rows = np.flatnonzero(~np.isnan(features[:, bits]).any(axis=1))
    cv = MODELS[model].cross_validate(
        features[rows], targets[rows], classify=classify, n_folds=folds
    )

    # back onto every row, with nulls for the rows left out
    if classify:
        predictions = np.full(dataset.height, None, dtype=object)
        predictions[rows] = cv.predictions
        probabilities = np.full(dataset.height, np.nan)
        probabilities[rows] = cv.probabilities.max(axis=1)
        columns = {
            f"{target}_pred": predictions.tolist(),
            f"{target}_probability": probabilities,
        }
    else:
        predictions = np.full(dataset.height, np.nan)
        predictions[rows] = cv.predictions
        columns = {
            f"{target}_pred": predictions,
            f"{target}_residual": targets - predictions,
        }
    columns = polars.DataFrame(columns).fill_nan(None)
    if new is not None:
        columns = polars.concat([new, columns], how="horizontal")

    result = AnalysisResult(
        title=f"Predict {target}",
        subtitle=model,
        columns=columns,
        help=CLASSIFICATION_HELP if classify else REGRESSION_HELP,
    )
    if classify:
        metrics = cv.metrics
        result.scores = [
            ("Accuracy", f"{metrics['accuracy']:.0%}"),
            ("Balanced acc.", f"{metrics['balanced_accuracy']:.0%}"),
        ]
        if "roc_auc" in metrics:
            result.scores.append(("ROC AUC", f"{metrics['roc_auc']:.2f}"))
            skill = 2 * metrics["roc_auc"] - 1  # 0 for chance, 1 for perfect
        else:
            chance = 1 / len(cv.classes)
            skill = (metrics["balanced_accuracy"] - chance) / (1 - chance)
        level = _level(skill)
        result.verdict = (
            level,
            {
                "strong": "tells the labels apart well",
                "moderate": "tells the labels apart better than chance",
                "weak": "only a little better than chance",
                "none": "no better than chance",
            }[level],
        )
        result.confusion = (cv.classes, cv.confusion)
    else:
        metrics = cv.metrics
        result.scores = [
            ("R²", f"{metrics['r2']:.2f}"),
            ("MAE", format_number(metrics["mae"])),
            ("RMSE", format_number(metrics["rmse"])),
            ("Spearman ρ", f"{metrics['spearman']:.2f}"),
        ]
        level = _level(metrics["r2"])
        result.verdict = (
            level,
            {
                "strong": f"predicts most of the variation in {target}",
                "moderate": f"picks up the main trends in {target}",
                "weak": "only a little better than guessing the average",
                "none": "worse than guessing the average",
            }[level],
        )
        result.plot = (
            "Scatter",
            {"x": target, "y": f"{target}_pred", "color": "None"},
        )
        result.plot_label = "Show parity plot"

    known = int(cv.known.sum())
    result.details = [
        ("From", join_names(inputs)),
        ("Tested on", f"{known:,} rows, by {folds}-fold cross-validation"),
    ]
    if len(rows) > known:
        result.details.append(("Predicted", f"{len(rows) - known:,} rows missing it"))
    if len(rows) < dataset.height:
        result.details.append(
            ("Left out", f"{dataset.height - len(rows):,} unreadable structures")
        )

    # (a single input's share is always all of it)
    if cv.importances is not None and len(inputs) > 1:
        shares = dict.fromkeys(inputs, 0.0)
        for owner, importance in zip(owners, cv.importances):
            shares[owner] += importance  # e.g. a fingerprint's bits, summed
        result.bars = sorted(shares.items(), key=lambda item: -item[1])[:TOP_ROWS]
        result.bars_title = "What it relies on"
    return result


def linear_fit(dataset: ToolkitDataset, y: str, x: list[str]) -> AnalysisResult:
    """Fits `y` to the `x` columns by least squares (see `LinearFit`), adding the
    fit's values as `<y>_fit`."""
    if not y:
        raise ValueError("Choose a column to fit")
    if not x:
        raise ValueError("Choose at least one column in “To”")
    features, _, _ = input_matrix(dataset, x)
    fit = LinearFit.fit(features, dataset.columns.numbers(y), x, target_name=y)
    level = _level(fit.r2)
    return AnalysisResult(
        title=f"Fit {y}",
        subtitle="Linear fit",
        scores=[
            ("R²", f"{fit.r2:.2f}"),
            ("Adjusted R²", f"{fit.adjusted_r2:.2f}"),
            ("Rows", f"{fit.n:,}"),
        ],
        verdict=(
            level,
            {
                "strong": f"explains most of the variation in {y}",
                "moderate": f"explains some of the variation in {y}",
                "weak": f"explains little of the variation in {y}",
                "none": f"explains none of the variation in {y}",
            }[level],
        ),
        equation=fit.equation,
        table=polars.DataFrame(
            {
                "Term": fit.terms,
                "Coefficient": fit.coefficients,
                "p-value": fit.p_values,
            }
        ),
        columns=polars.DataFrame({f"{y}_fit": fit.predictions}).fill_nan(None),
        plot=("Scatter", {"x": y, "y": f"{y}_fit", "color": "None"}),
        plot_label="Show parity plot",
        help=LINEAR_FIT_HELP,
    )


ANALYSES = [
    Analysis(
        "Predict a column",
        PREDICT,
        "Trains a model to predict one column from a fingerprint and/or other "
        "columns, tests it on rows it hasn't seen, then adds its predictions as "
        "columns.",
        settings=[
            Setting(
                "target",
                "Predict",
                COLUMN,
                column_kinds=(NUMBER, CATEGORY),
                default="pIC50",
                help="<b>The column to predict.</b> A number column (e.g. pIC50) "
                "predicts a value for each row. A category column (e.g. active or "
                "inactive) predicts a label.<br><br>Rows missing a value aren't "
                "learned from, but they still get a prediction, so this also fills "
                "in compounds that haven't been measured.",
            ),
            Setting(
                "inputs",
                "From",
                COLUMNS,
                column_kinds=(NUMBER, DATE),
                fingerprints=True,
                default=["ECFP4"],
                excluding="target",
                help="<b>What the model learns from.</b> A fingerprint describes "
                "each structure as bits, one for each small piece of it. "
                "<b>ECFP4</b> is a strong default for most activity and property "
                "data.<br><br>You can add number columns too (e.g. cLogP), or use "
                "columns alone for data without structures. Leave out columns "
                "worked out from the one you're predicting, as they'd let the "
                "model cheat.",
            ),
            Setting(
                "model",
                "Model",
                CHOICE,
                choices=list(MODELS),
                help="<b>How the model learns.</b> Not sure? Start with Random "
                "forest, then try the others and compare their scores."
                "<ul>"
                "<li><b>Random forest</b>: a good first choice. It averages many "
                "decision trees, needs no tuning, and shows which inputs matter.</li>"
                "<li><b>Gradient boosting</b>: often the most accurate with "
                "thousands of rows, but can overfit small datasets.</li>"
                "<li><b>Ridge</b>: a straight-line model. Fast and hard to "
                "overfit, but misses curved trends. A good baseline.</li>"
                "<li><b>Tanimoto k-NN</b>: predicts each molecule from its 5 most "
                "similar ones. Simple to trust, but it takes fingerprints only.</li>"
                "</ul>",
            ),
            Setting(
                "folds",
                "Folds",
                INTEGER,
                default=5,
                minimum=2,
                maximum=20,
                help="<b>How the model is tested.</b> The rows are split into this "
                "many groups (folds). Each group is predicted by a model trained on "
                "all the others, so every score comes from rows the model never "
                "saw.<br><br>5 is standard. More folds train on more rows each "
                "time, but take longer. Use fewer if you have very few rows.",
            ),
        ],
        run=predict_column,
        slow=True,
    ),
    Analysis(
        "Linear fit",
        PREDICT,
        "Fits a column to a straight line (or plane) of others, giving the "
        "equation and how much each column matters. Adds the fit's values as a "
        "column.",
        settings=[
            Setting(
                "y",
                "Fit",
                COLUMN,
                column_kinds=(NUMBER,),
                default="pIC50",
                help="<b>The column to fit</b>, e.g. pIC50. Rows missing it, or any "
                "column it's fit to, are left out.",
            ),
            Setting(
                "x",
                "To",
                COLUMNS,
                column_kinds=(NUMBER,),
                default=[],
                excluding="y",
                help="<b>The columns to fit it to.</b> Pick a few you expect to "
                "matter: each adds a term to the equation. For many columns or a "
                "fingerprint, use Predict a column instead.",
            ),
        ],
        run=linear_fit,
    ),
]


def input_matrix(
    dataset: ToolkitDataset, inputs: list[str]
) -> tuple[np.ndarray, list[str], polars.DataFrame | None]:
    """
    The inputs of a model, one row per dataset row, with NaN where missing.
    `inputs` are names of number or date columns (as `DataColumns.numbers` gives
    them, e.g. dates as epoch seconds) and/or of fingerprints (one of
    `FINGERPRINT_FEATURES`, as 0/1 bits, or NaN where a structure can't be read).

    Fingerprints are read from the dataset's column of them (packed into bytes, as
    the Featurize panel adds them) when there is one, and otherwise computed.

    Returns the matrix, the input each of its columns comes from (e.g. "ECFP4" for
    each of its bits), and the computed fingerprints' columns (or None), for adding
    to the dataset.
    """
    fingerprints = [
        FINGERPRINT_FEATURES[n] for n in inputs if n in FINGERPRINT_FEATURES
    ]
    if fingerprints and not dataset.has_molecules:
        raise ValueError("Fingerprints need a column of molecules (as SMILES)")
    missing = [f for f in fingerprints if f.key not in dataset.df.columns]
    new = None
    if missing:
        smiles = dataset.df[dataset.molecule_column].to_list()
        new = compute_features(smiles, [(feature, None) for feature in missing])

    blocks, owners = [], []
    for name in inputs:
        if name not in FINGERPRINT_FEATURES:
            blocks.append(dataset.columns.numbers(name)[:, None])
            owners.append(name)
            continue
        key = FINGERPRINT_FEATURES[name].key
        column = new[key] if new is not None and key in new.columns else dataset.df[key]
        present = column.is_not_null().to_numpy()
        packed = np.stack(
            [np.frombuffer(value, dtype=np.uint8) for value in column.drop_nulls()]
        )
        bits = np.full((len(column), packed.shape[1] * 8), np.nan)
        bits[present] = np.unpackbits(packed, axis=1)
        blocks.append(bits)
        owners += [name] * bits.shape[1]
    return np.hstack(blocks), owners, new


def join_names(names: list[str], most: int = 5) -> str:
    """Names as a list in a sentence, e.g. "cLogP, TPSA, and ECFP4", naming at most
    `most` of them."""
    if len(names) > most:
        names = [*names[:most], f"{len(names) - most} more"]
    if len(names) <= 2:
        return " and ".join(names)
    return f"{', '.join(names[:-1])}, and {names[-1]}"


def format_number(value: float) -> str:
    """A number rounded for reading, e.g. 6.11, 0.00618, 2.13e-105, or 1,234."""
    return f"{value:,.0f}" if abs(value) >= 1000 else f"{value:.3g}"


def _level(skill: float) -> str:
    """How good a score from 0 (no better than guessing) to 1 (perfect), like R²,
    is: "strong", "moderate", "weak", or "none"."""
    if skill >= 0.6:
        return "strong"
    if skill >= 0.3:
        return "moderate"
    if skill >= 0:
        return "weak"
    return "none"
