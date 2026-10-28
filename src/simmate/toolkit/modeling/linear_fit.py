from dataclasses import dataclass

import numpy as np
from scipy.stats import t as t_distribution


@dataclass
class LinearFit:
    """
    A least-squares fit of a column to a straight line (or plane) of others, e.g.
    `pIC50 = 0.42·cLogP − 0.010·TPSA + 5.1`, with each term's standard error and
    p-value. Make one with `LinearFit.fit`.
    """

    target_name: str
    terms: list[str]
    """The inputs' names, then "intercept"."""
    coefficients: np.ndarray
    """One per term."""
    std_errors: np.ndarray
    """One per term."""
    p_values: np.ndarray
    """One per term: the chance of a coefficient this far from zero if the term
    had no effect (two-sided t-test)."""
    r2: float
    adjusted_r2: float
    """R², penalized for each term added."""
    n: int
    """How many rows were fit (those with no missing values)."""
    predictions: np.ndarray
    """One per row, or NaN where an input is missing."""

    @classmethod
    def fit(
        cls,
        features: np.ndarray,
        target: np.ndarray,
        names: list[str],
        target_name: str = "y",
    ) -> "LinearFit":
        """
        Fits `target` to the columns of `features` (one row per molecule) by least
        squares. Rows with any missing value (NaN) are left out of the fit.

        Args:
            features: The inputs, one column per name in `names`.
            target: One value per row.
            names: The inputs' names, as shown in the equation.
            target_name: The target's name, as shown in the equation.
        """
        features = np.asarray(features, dtype=float)
        target = np.asarray(target, dtype=float)
        # a column of ones for the intercept
        design = np.column_stack([features, np.ones(len(features))])
        complete = np.isfinite(design).all(axis=1)
        rows = complete & np.isfinite(target)
        x, y = design[rows], target[rows]
        n, n_terms = x.shape
        dof = n - n_terms  # degrees of freedom
        if dof <= 0:
            raise ValueError(
                f"A fit of {n_terms - 1} column(s) needs more than {n_terms} rows "
                f"with every value, and there are {n}"
            )

        coefficients, *_ = np.linalg.lstsq(x, y, rcond=None)
        residuals = y - x @ coefficients
        rss = residuals @ residuals  # residual sum of squares
        variance = rss / dof
        std_errors = np.sqrt(np.diag(variance * np.linalg.pinv(x.T @ x)))
        with np.errstate(divide="ignore", invalid="ignore"):  # a perfect fit
            t_values = coefficients / std_errors
        p_values = 2 * t_distribution.sf(np.abs(t_values), dof)

        total = np.sum((y - y.mean()) ** 2)
        r2 = 1 - rss / total if total else np.nan
        predictions = np.full(len(target), np.nan)
        predictions[complete] = design[complete] @ coefficients
        return cls(
            target_name=target_name,
            terms=[*names, "intercept"],
            coefficients=coefficients,
            std_errors=std_errors,
            p_values=p_values,
            r2=float(r2),
            adjusted_r2=float(1 - (1 - r2) * (n - 1) / dof),
            n=n,
            predictions=predictions,
        )

    @property
    def equation(self) -> str:
        """The fit as an equation, e.g. `pIC50 = 0.42·cLogP − 0.010·TPSA + 5.1`."""
        text = f"{self.target_name} ="
        for i, (term, coefficient) in enumerate(zip(self.terms, self.coefficients)):
            sign = "−" if coefficient < 0 else "+"
            value = f"{abs(coefficient):.3g}"
            part = value if term == "intercept" else f"{value}·{term}"
            if i == 0:
                text += f" {'−' if coefficient < 0 else ''}{part}"
            else:
                text += f" {sign} {part}"
        return text
