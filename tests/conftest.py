"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gmb_scenario import Instance  # noqa: E402


def make(supporters, costs, budget, n, group=None, own=None) -> Instance:
    """Instanz aus den Unterstützern je Projekt: supporters[j] ist die Menge der Wähler (0 .. n − 1), die Projekt j zustimmen."""
    m = len(costs)
    approvals = np.zeros((n, m), dtype=bool)
    for j, voters in enumerate(supporters):
        for i in voters:
            approvals[i, j] = True
    return Instance(
        approvals=approvals, costs=np.array(costs), budget=budget,
        group=np.zeros(n, dtype=int) if group is None else np.array(group), own=np.zeros(m, dtype=int) if own is None else np.array(own),
    )


@pytest.fixture
def lager():
    """10 Wähler: 0 bis 6 größeres Lager, 7 bis 9 kleineres. Projekte P1 bis P3 (Kosten 3) gehören dem größeren Lager (nur diese Wähler stimmen zu), P4 (Kosten 3) dem kleineren. Budget 10.

    Handrechnung: gierig kauft P1, P2, P3 (je 7 Zustimmungen, zusammen 9 Kosten) und lässt das kleinere Lager leer ausgehen; gleiche Anteile
    (je Wähler 1) kaufen P1 (ρ = 3/7), P2 (ρ = 3/7) und P4 (ρ = 1)."""
    big = list(range(7))
    return make([big, big, big, [7, 8, 9]], costs=[3, 3, 3, 3], budget=10, n=10, group=[0] * 7 + [1] * 3, own=[0, 0, 0, 1])
