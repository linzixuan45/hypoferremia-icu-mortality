#!/usr/bin/env python3
"""Canonical AUROC confidence intervals for the Round 2 evaluation design.

The locked MIMIC-IV internal comparison uses DeLong intervals.  The
same-institution temporal sensitivity cohort and the two exploratory Chinese
cohorts use stratified nonparametric bootstrap intervals.  Keeping this policy
in one dependency-light module prevents figure and table generators from
silently selecting different interval methods.
"""
from __future__ import annotations

import re

import numpy as np
from scipy import stats
from sklearn.metrics import roc_auc_score


DEFAULT_BOOTSTRAP_REPLICATES = 2000
DEFAULT_RANDOM_STATE = 42


def _normalise_cohort_key(cohort: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(cohort).lower()).strip()


def ci_method_for_cohort(cohort: str) -> str:
    """Return the locked cohort-specific interval method for a recognised label."""
    key = _normalise_cohort_key(cohort)
    if ("mimic iv" in key or "mimic4" in key) and (
        "internal" in key or "test" in key
    ):
        return "DeLong"
    if (
        "mimic iii" in key
        or "mimic3" in key
        or "temporal" in key
        or "exploratory" in key
        or "usc fah" in key
        or "first affiliated hospital" in key
        or key in {"f3", "nh", "third xiangya", "nanhua"}
    ):
        return "stratified bootstrap"
    raise ValueError(
        f"Unrecognised cohort label {cohort!r}; assign its AUROC interval method explicitly."
    )


def delong_ci(y_true, y_score, alpha: float = 0.05):
    """DeLong-style normal-approximation interval used for internal comparison."""
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    pos, neg = y_score[y_true == 1], y_score[y_true == 0]
    m, n = len(pos), len(neg)
    if m < 5 or n < 5:
        return np.nan, np.nan, np.nan
    all_s = np.concatenate([pos, neg])
    order = np.argsort(all_s)
    sorted_scores = all_s[order]
    rank = np.zeros(m + n)
    i = 0
    while i < m + n:
        k = i
        while k < m + n - 1 and sorted_scores[k + 1] == sorted_scores[k]:
            k += 1
        rank[i : k + 1] = 0.5 * (i + k) + 1
        i = k + 1
    rank_out = np.empty(m + n)
    rank_out[order] = rank
    auc = (np.sum(rank_out[:m]) - m * (m + 1) / 2) / (m * n)
    v10 = np.array(
        [(np.sum(neg < value) + 0.5 * np.sum(neg == value)) / n for value in pos]
    )
    v01 = np.array(
        [(np.sum(pos > value) + 0.5 * np.sum(pos == value)) / m for value in neg]
    )
    se = np.sqrt(
        (np.var(v10, ddof=1) if m > 1 else 0) / m
        + (np.var(v01, ddof=1) if n > 1 else 0) / n
    )
    z_value = stats.norm.ppf(1 - alpha / 2)
    return auc, max(0.0, auc - z_value * se), min(1.0, auc + z_value * se)


def stratified_bootstrap_auc_ci(
    y_true,
    y_score,
    *,
    alpha: float = 0.05,
    n_bootstrap: int = DEFAULT_BOOTSTRAP_REPLICATES,
    random_state: int = DEFAULT_RANDOM_STATE,
):
    """Percentile AUROC CI from class-stratified bootstrap resampling."""
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    pos_idx = np.flatnonzero(y_true == 1)
    neg_idx = np.flatnonzero(y_true == 0)
    if len(pos_idx) < 2 or len(neg_idx) < 2:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(random_state)
    boot = np.empty(n_bootstrap, dtype=float)
    for i in range(n_bootstrap):
        sample_idx = np.concatenate(
            [
                rng.choice(pos_idx, size=len(pos_idx), replace=True),
                rng.choice(neg_idx, size=len(neg_idx), replace=True),
            ]
        )
        boot[i] = roc_auc_score(y_true[sample_idx], y_score[sample_idx])
    lower, upper = np.quantile(boot, [alpha / 2, 1 - alpha / 2])
    return roc_auc_score(y_true, y_score), float(lower), float(upper)


def auroc_ci_for_cohort(
    y_true,
    y_score,
    cohort: str,
    *,
    alpha: float = 0.05,
    n_bootstrap: int = DEFAULT_BOOTSTRAP_REPLICATES,
    random_state: int = DEFAULT_RANDOM_STATE,
):
    """Compute AUROC and CI using the method assigned to ``cohort``."""
    method = ci_method_for_cohort(cohort)
    if method == "DeLong":
        auc, lower, upper = delong_ci(y_true, y_score, alpha=alpha)
    else:
        auc, lower, upper = stratified_bootstrap_auc_ci(
            y_true,
            y_score,
            alpha=alpha,
            n_bootstrap=n_bootstrap,
            random_state=random_state,
        )
    return auc, lower, upper, method
