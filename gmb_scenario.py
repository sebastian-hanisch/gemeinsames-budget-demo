"""Szenario: eine Budget-Instanz mit zwei Wählerlagern, Projekten mit ganzzahligen Kosten und Zustimmungen."""

from dataclasses import dataclass

import numpy as np

import gmb_constants as C


@dataclass(eq=False)
class Instance:
    """approvals: (n, m) Wahrheitswerte; costs: (m,) ganze Zahlen; budget: ganze Zahl; group: (n,) 0 = größeres, 1 = kleineres Lager; own: (m,) Lager, dem das Projekt gehört."""

    approvals: np.ndarray
    costs: np.ndarray
    budget: int
    group: np.ndarray
    own: np.ndarray

    @property
    def n(self) -> int:
        return self.approvals.shape[0]

    @property
    def m(self) -> int:
        return self.approvals.shape[1]


def make_instance(n, m, budget_pct, group_pct, own_pct, cross_pct, seed) -> Instance:
    """Zwei Lager: die ersten round(group_pct % · n) Wähler gehören zum größeren Lager, die letzten m // 2 Projekte dem kleineren.

    Zuerst werden die Kosten gezogen (gleichverteilt von COST_MIN bis COST_MAX), dann die Zustimmungen: eigene Projekte mit
    Wahrscheinlichkeit own_pct, Projekte des anderen Lagers mit cross_pct. Budget = budget_pct % der Gesamtkosten, gerundet, mindestens 1."""
    rng = np.random.default_rng(seed)
    n_major = min(n - 1, max(1, int(round(group_pct * n / 100))))
    group = np.array([0] * n_major + [1] * (n - n_major))
    own = np.array([0] * (m - m // 2) + [1] * (m // 2))
    costs = rng.integers(C.COST_MIN, C.COST_MAX + 1, size=m)
    prob = np.where(group[:, None] == own[None, :], own_pct / 100, cross_pct / 100)
    approvals = rng.random((n, m)) < prob
    budget = max(1, int(round(budget_pct / 100 * costs.sum())))
    return Instance(approvals=approvals, costs=costs, budget=budget, group=group, own=own)
