"""Abbildungen: Aufbau, gesperrte Achsen, Werte an der Hand-Instanz, Randfälle ohne Ausgaben."""

import numpy as np
import pytest

import gmb_constants as C
import gmb_evaluation as ev
import gmb_visualization as V
from conftest import make


@pytest.fixture
def a_lager(lager):
    return ev.analyse_instance(ev.Settings(), lager)


def locked(fig):
    return all(ax.fixedrange for ax in fig.select_xaxes()) and all(ax.fixedrange for ax in fig.select_yaxes())


def test_projects_figure_by_hand(a_lager):
    fig = V.build_projects(a_lager)
    bars = [t for t in fig.data if t.type == "bar"]
    assert [b.name for b in bars] == ["Zustimmungen größeres Lager", "Zustimmungen kleineres Lager"]
    assert list(bars[0].x) == ["P1 · 3", "P2 · 3", "P3 · 3", "P4 · 3"]
    assert list(bars[0].y) == [7, 7, 7, 0] and list(bars[1].y) == [0, 0, 0, 3]
    heat = next(t for t in fig.data if t.type == "heatmap")
    assert list(heat.y) == [C.RULE_SHORT[r] for r in C.RULES]
    assert np.array(heat.z).tolist() == [[1, 1, 1, 0], [1, 1, 1, 0], [1, 1, 0, 1], [1, 1, 0, 1], [1, 1, 1, 0]]       # gierig, gierig, Anteile, Anteile + Rest, Optimum
    assert locked(fig)


def test_comparison_figure_by_hand(a_lager):
    fig = V.build_comparison(a_lager)
    bars = [t for t in fig.data if t.type == "bar"]
    assert [round(float(v), 3) for v in bars[0].y] == [0.0, 0.0, 0.333, 0.333, 0.0]
    assert [round(float(v), 3) for v in bars[1].y] == [1.0, 1.0, 0.0, 0.0, 1.0]
    lines = [s for s in fig.layout.shapes if s.type == "line"]
    assert len(lines) == 1 and lines[0].y0 == pytest.approx(0.3)                      # Anteil der Wähler des kleineren Lagers
    assert locked(fig)


def test_comparison_without_spending_or_minority_voters():
    inst = make([[0, 1]], costs=[5], budget=1, n=3, group=[0, 0, 0], own=[0])
    fig = V.build_comparison(ev.analyse_instance(ev.Settings(), inst))
    bars = [t for t in fig.data if t.type == "bar"]
    assert all(float(v) == 0.0 for v in bars[0].y) and all(float(v) == 0.0 for v in bars[1].y)         # nichts ausgegeben, kein kleineres Lager: Nullen statt Lücken


def rows(param, xs):
    return [{"param": param, "x": x, "rule": rule, "runs": 10, "minority_budget": 0.3, "jr": 0.1, "unspent": 0.4} for x in xs for rule in C.RULES]


def test_series_figure_has_one_line_per_rule_and_the_reference_for_the_group_series():
    fig = V.build_series(rows("group", (60, 90)), "minority_budget", "Anteil")
    assert [t.name for t in fig.data] == [C.RULE_SHORT[r] for r in C.RULES] + ["Anteil der Wähler des kleineren Lagers"]
    assert list(fig.data[-1].y) == [0.4, 0.1] and list(fig.data[0].x) == [60, 90]
    assert locked(fig)
    other = V.build_series(rows("budget", (10, 20)), "jr", "JR")
    assert len(other.data) == len(C.RULES) and other.layout.xaxis.title.text == V.AXIS_TITLES["budget"]
    assert V.build_series(rows("group", (60,)), "jr", "JR").data[-1].name != "Anteil der Wähler des kleineren Lagers"      # die Bezugslinie nur für die Ausgaben


def test_series_axis_range_follows_ymax():
    fig = V.build_series(rows("own", (20, 80)), "unspent", "Anteil", ymax=1.1)
    assert tuple(fig.layout.yaxis.range) == (0, 1.1)
