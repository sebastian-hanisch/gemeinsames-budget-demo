"""Verdikte und Tabellen als reine Funktionen: Schwellen und jede Zahl im Text an handgesetzten Werten."""

import math

import pytest

import gmb_constants as C
import gmb_evaluation as ev
from conftest import make


@pytest.fixture
def a_lager(lager):
    return ev.analyse_instance(ev.Settings(), lager)


def test_number_formats():
    assert ev.num(3.0) == "3,0" and ev.num(1234.567, 2) == "1234,57"
    assert ev.pct(0.333) == "33 %" and ev.pct(0.0) == "0 %" and ev.pct(0.1234, 1) == "12,3 %"
    assert ev.pct(None) == "–" and ev.pct(float("nan")) == "–"
    assert ev.label(0) == "P1" and ev.labels((0, 3)) == "P1, P4"


def test_analysis_of_the_hand_instance(a_lager):
    assert a_lager.optimum == 21 and a_lager.minority_share == pytest.approx(0.3)
    assert a_lager.outcomes["anteile"].chosen == (0, 1, 3) and ev.welfare(a_lager, "anteile") == pytest.approx(17 / 21)
    assert ev.violated(a_lager, "stimmen", "jr") and not ev.violated(a_lager, "anteile", "jr") and not ev.violated(a_lager, "anteile", "ejr")


def test_welfare_without_any_approval_is_one():
    inst = make([[], []], costs=[1, 1], budget=2, n=2)
    a = ev.analyse_instance(ev.Settings(), inst)
    assert a.optimum == 0 and ev.welfare(a, "stimmen") == 1.0


def test_rule_rows_by_hand(a_lager):
    rows = {r["Regel"]: r for r in ev.rule_rows(a_lager)}
    assert list(rows) == list(C.RULES.values())
    r = rows[C.RULES["anteile"]]
    assert r["Projekte"] == 3 and r["Ausgaben"] == "9 von 10" and r["Zustimmungen"] == "17 (81 % des Größtmöglichen)"
    assert r["Budget für das kleinere Lager"] == "33 %" and r["Wähler ohne Treffer (kleineres Lager)"] == "0 % (0 %)"
    assert r["Gerechtfertigte Repräsentation (JR)"] == "erfüllt" and r["Erweiterte Repräsentation (EJR)"] == "erfüllt" and r["EJR bis auf ein Projekt"] == "erfüllt"
    g = rows[C.RULES["stimmen"]]
    assert g["Ausgaben"] == "9 von 10" and g["Budget für das kleinere Lager"] == "0 %" and g["Wähler ohne Treffer (kleineres Lager)"] == "30 % (100 %)"
    assert g["Gerechtfertigte Repräsentation (JR)"] == "verletzt" and g["Erweiterte Repräsentation (EJR)"] == "verletzt" and g["EJR bis auf ein Projekt"] == "erfüllt"


def test_witness_lines_by_hand(a_lager):
    lines = ev.witness_lines(a_lager)
    assert len(lines) == 3                                                     # gierig (Zustimmungen), gierig (je Kosten) und die Größte Gesamtzustimmung
    first = lines[0]
    assert first.startswith("**Gierig (Zustimmungen), Gerechtfertigte Repräsentation (JR):**")
    assert "3 Wähler (30 %) stimmen allen Projekten P4 zu (Kosten zusammen 3)" in first and "(3,0 von 10)" in first and "jeder von ihnen hat keines der finanzierten Projekte, denen er zustimmt." in first


def test_witness_lines_name_the_missing_amount():
    inst = make([[0, 1, 2, 3]] * 3, costs=[2, 2, 2], budget=8, n=4)
    a = ev.analyse_instance(ev.Settings(), inst)
    none = {"jr": None, "ejr": None, "ejr1": None}
    a.violations = {rule: dict(none) for rule in C.RULES}
    a.violations["stimmen"] = {"jr": None, "ejr": ((0, 1), 4), "ejr1": None}
    a.violations["kosten"] = {"jr": None, "ejr": None, "ejr1": ((0, 1, 2), 3)}
    first, second = ev.witness_lines(a)
    assert first == ("**Gierig (Zustimmungen), Erweiterte Repräsentation (EJR):** 4 Wähler (100 %) stimmen allen Projekten P1, P2 zu (Kosten zusammen 4); "
                     "ihr Anteil am Budget (8,0 von 8) reicht dafür, doch jeder von ihnen hat weniger als 2 der finanzierten Projekte, denen er zustimmt.")
    assert "EJR bis auf ein Projekt:** 3 Wähler (75 %) stimmen allen Projekten P1, P2, P3 zu" in second and "(6,0 von 8)" in second and "hat weniger als 2 der finanzierten" in second


def test_verdict_state_by_hand(a_lager):
    kind, text = ev.verdict_state(a_lager)
    assert kind == "warning"
    assert text.startswith("Das kleinere Lager stellt 30 % der Wähler. Gierig nach Zustimmungen gibt seinen Projekten 0 % der Ausgaben, gierig nach Zustimmung je Kosten 0 %, gleiche Anteile 33 %.")
    assert "Gerechtfertigte Repräsentation (JR) ist verletzt bei: Gierig (Zustimmungen), Gierig (je Kosten), Größte Gesamtzustimmung." in text
    assert "Gleiche Anteile geben 90 % des Budgets aus (81 % der größtmöglichen Zustimmungen); mit aufgefülltem Rest sind es 90 % und 81 %." in text


def test_verdict_state_when_everything_is_fine():
    inst = make([[0, 1, 2, 3]] * 2, costs=[1, 1], budget=2, n=4, group=[0, 0, 0, 1], own=[0, 1])
    a = ev.analyse_instance(ev.Settings(), inst)
    kind, text = ev.verdict_state(a)
    assert kind == "info" and "bei allen fünf Regeln erfüllt" in text


def test_verdict_state_with_no_spending_shows_dashes():
    inst = make([[0, 1]], costs=[5], budget=1, n=2, group=[0, 1], own=[0])
    kind, text = ev.verdict_state(ev.analyse_instance(ev.Settings(), inst))
    assert "gibt seinen Projekten – der Ausgaben" in text


def _rows(param, xs, **by_rule):
    """Messreihen-Zeilen mit festen Werten: by_rule[rule] = {Kennzahl: [Wert je x]}."""
    rows = []
    for i, x in enumerate(xs):
        for rule in C.RULES:
            base = {"minority_budget": 0.1, "no_hit_minor": 0.2, "welfare": 0.9, "unspent": 0.3, "jr": 0.0, "ejr": 0.0, "ejr1": 0.0}
            base.update({k: v[i] for k, v in by_rule.get(rule, {}).items()})
            rows.append({"param": param, "x": x, "rule": rule, "runs": 100, **base})
    return rows


def test_cell_of_and_series_rows():
    rows = _rows("group", (60, 90), anteile={"minority_budget": [0.39, 0.04]})
    assert ev.cell_of(rows, 90, "anteile")["minority_budget"] == 0.04
    table = ev.series_rows(rows, "minority_budget")
    assert [r["Größeres Lager (%)"] for r in table] == [60, 90]
    assert table[0]["Gleiche Anteile"] == "39 %" and table[1]["Gleiche Anteile"] == "4 %" and table[0]["Gierig (Zustimmungen)"] == "10 %"
    assert list(ev.series_rows(_rows("budget", (10,)), "jr")[0])[0] == "Budget (%)"
    assert list(ev.series_rows(_rows("own", (20,)), "jr")[0])[0] == "Zustimmung zu eigenen Projekten (%)"


def test_verdict_groups_by_hand():
    rows = _rows("group", (60, 90), stimmen={"minority_budget": [0.05, 0.03], "no_hit_minor": [0.5, 0.6]}, kosten={"minority_budget": [0.37, 0.12]},
                 anteile={"minority_budget": [0.39, 0.04], "no_hit_minor": [0.16, 0.63]})
    kind, text = ev.verdict_groups(rows)
    assert kind == "info"
    assert text.startswith("Bei 90 : 10 Wählern (Mittel über 100 Instanzen) bekommen die Projekte des kleineren Lagers 3 % der Ausgaben bei gierig nach Zustimmungen, 12 % bei gierig je Kosten und 4 % bei gleichen Anteilen;")
    assert "die Wähler des kleineren Lagers sind 10 %." in text and "60 % (gierig nach Zustimmungen), 63 % (gleiche Anteile)" in text


def test_verdict_budgets_by_hand():
    rows = _rows("budget", (10, 50), stimmen={"jr": [0.22, 0.42]}, optimal={"jr": [0.02, 0.0]}, anteile={"unspent": [0.69, 0.35]})
    kind, text = ev.verdict_budgets(rows)
    assert kind == "info"
    assert "bei 10 % bzw. 50 % Budget: Gierig (Zustimmungen) 22 % bzw. 42 %; Gierig (je Kosten) 0 % bzw. 0 %; Gleiche Anteile 0 % bzw. 0 %; Gleiche Anteile + Rest 0 % bzw. 0 %; Größte Gesamtzustimmung 2 % bzw. 0 %." in text
    assert text.endswith("Unausgegebenes Budget bei gleichen Anteilen: 69 % bzw. 35 %.")


def test_verdict_cohesion_by_hand():
    rows = _rows("own", (20, 80), stimmen={"jr": [0.1, 0.55], "ejr": [0.1, 0.83], "ejr1": [0.0, 0.34]})
    kind, text = ev.verdict_cohesion(rows)
    assert kind == "info" and text.startswith("Bei 80 % Zustimmung zu den eigenen Projekten sind in 100 Instanzen verletzt: Gierig (Zustimmungen) JR 55 %, EJR 83 %, EJR bis auf eins 34 %;")


def test_series_cells_use_consecutive_seeds_and_are_reproducible():
    a = ev._cell(30, 8, 30, 60, 50, 5, runs=4, seed=7)
    b = ev._cell(30, 8, 30, 60, 50, 5, runs=4, seed=7)
    assert a == b and set(a) == set(C.RULES)
    assert a["optimal"]["welfare"] == 1.0 and all(0.0 <= v["unspent"] <= 1.0 for v in a.values())
    assert not math.isnan(a["stimmen"]["minority_budget"])
