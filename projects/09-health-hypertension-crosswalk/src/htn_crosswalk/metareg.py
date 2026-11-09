"""Random effects meta-regression with the DerSimonian and Laird moment estimator.

Each observation i is a paired logit difference y_i with known sampling
variance v_i. The model is

    y_i = x_i' beta + u_i + e_i,   u_i ~ N(0, tau^2),   e_i ~ N(0, v_i),

where tau^2 is residual heterogeneity of each cell and cycle observation not
explained by the covariates (one u_i per row, as in metafor rma).
This is the linear, untrimmed special case of the GBD MR-BRT crosswalk model.
The moment estimator follows Raudenbush (2009), as in metafor rma(method="DL"):

    Q_E   = sum_i w_i (y_i - x_i' b_FE)^2,       w_i = 1 / v_i
    tau^2 = max(0, (Q_E - (k - p)) / (tr W - tr[(X'WX)^-1 X'W^2 X]))
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MetaRegression:
    """Fitted coefficients, their covariance and the between study variance."""

    beta: np.ndarray
    cov: np.ndarray
    tau2: float
    q_e: float
    k: int
    names: tuple[str, ...]

    @property
    def se(self) -> np.ndarray:
        return np.sqrt(np.diag(self.cov))

    def predict(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Mean prediction and its variance from coefficient uncertainty only."""
        x = np.atleast_2d(x)
        return x @ self.beta, np.einsum("ij,jk,ik->i", x, self.cov, x)


def fit_dl(y: np.ndarray, v: np.ndarray, x: np.ndarray, names: tuple[str, ...]) -> MetaRegression:
    """Fit the DerSimonian and Laird random effects meta-regression."""
    y = np.asarray(y, dtype=float)
    v = np.asarray(v, dtype=float)
    x = np.asarray(x, dtype=float)
    k, p = x.shape
    if k <= p:
        raise ValueError("Need more observations than coefficients")

    w = 1.0 / v
    xtwx_inv = np.linalg.inv(x.T @ (w[:, None] * x))
    beta_fe = xtwx_inv @ x.T @ (w * y)
    q_e = float(np.sum(w * (y - x @ beta_fe) ** 2))
    denom = w.sum() - np.trace(xtwx_inv @ x.T @ ((w**2)[:, None] * x))
    tau2 = max(0.0, (q_e - (k - p)) / denom)

    w_re = 1.0 / (v + tau2)
    cov = np.linalg.inv(x.T @ (w_re[:, None] * x))
    beta = cov @ x.T @ (w_re * y)
    return MetaRegression(beta=beta, cov=cov, tau2=tau2, q_e=q_e, k=k, names=names)
