"""Kern von Hand: jede Regel und jede Prüfung an Mini-Instanzen, mit der Rechnung im Kommentar."""

import math

import numpy as np
import pytest

import gmb_algorithm as A
from conftest import make


def test_greedy_by_votes_skips_what_does_not_fit():
    # Kosten 3, 2, 2, Budget 4; Zustimmungen 5, 4, 3. Nach Zustimmungen: P1 (3) passt, danach passt nichts mehr (3 + 2 > 4) -> [0].
    inst = make([[0, 1, 2, 3, 4], [0, 1, 2, 3], [0, 1, 2]], costs=[3, 2, 2], budget=4, n=5)
    assert A.greedy_votes(inst) == [0]
    # Zustimmungen je Kosten: 5/3, 4/2, 3/2 -> P2 (2), dann P1 passt nicht (2 + 3 > 4), dann P3 (2 + 2 = 4) -> [1, 2]
    assert A.greedy_ratio(inst) == [1, 2]
    # Optimum: {P2, P3} = 7 Zustimmungen gegen {P1} = 5
    assert A.optimal(inst) == [1, 2]


def test_ties_go_to_the_smaller_index():
    inst = make([[0, 1], [0, 1], [0, 1]], costs=[2, 2, 2], budget=4, n=2)         # drei gleiche Projekte, Platz für zwei
    assert A.greedy_votes(inst) == [0, 1] and A.greedy_ratio(inst) == [0, 1] and A.equal_shares(inst) == [0, 1]


def test_equal_shares_by_hand_lager(lager):
    # je Wähler 1. P1: 7 Unterstützer zahlen 3/7; P4: 3 Unterstützer zahlen 1 -> zuerst P1 (kleineres ρ, Gleichstand mit P2 -> kleinerer Index);
    # die sieben Wähler haben danach 1 − 3/7 = 4/7, P2 kostet wieder 3/7 -> gekauft; danach haben sie 1/7 und P3 (3) ist unbezahlbar; P4 mit ρ = 1 -> gekauft.
    assert A.equal_shares(lager) == [0, 1, 3]
    assert A.greedy_votes(lager) == [0, 1, 2] and A.greedy_ratio(lager) == [0, 1, 2]
    assert A.optimal(lager) == [0, 1, 2]
    assert A.equal_shares_completed(lager) == [0, 1, 3]     # Rest 10 − 9 = 1: P3 (3) passt nicht hinein


def test_equal_shares_completed_fills_the_rest():
    # Vier Wähler, Budget 5 (je 1,25); P1 (Kosten 2) von allen; P2 (Kosten 3) nur von Wähler 0.
    # Gleiche Anteile: P1 ρ = 0,5 -> gekauft (Rest je 0,75); P2: Wähler 0 hat 0,75 < 3 -> unbezahlbar. Ausgegeben 2 von 5.
    # Auffüllen: P2 (3) passt in das Restbudget 3 -> gekauft.
    inst = make([[0, 1, 2, 3], [0]], costs=[2, 3], budget=5, n=4)
    assert A.equal_shares(inst) == [0]
    assert A.equal_shares_completed(inst) == [0, 1]


def test_contribution_by_hand():
    # Restgeld 0,5, 0,5, 1, 1 und Kosten 3: 0,5 + 0,5 + 1 + 1 = 3 gelingt nur mit ρ = 1; Kosten 4 reichen nicht (Summe 3).
    assert A._contribution(np.array([0.5, 0.5, 1.0, 1.0]), 3.0) == pytest.approx(1.0)
    assert A._contribution(np.array([0.5, 0.5, 1.0, 1.0]), 4.0) is None
    assert A._contribution(np.array([2.0, 2.0]), 3.0) == pytest.approx(1.5)           # beide zahlen gleich viel


def test_unaffordable_and_unsupported_projects_are_never_bought():
    inst = make([[], [0]], costs=[1, 5], budget=3, n=2)      # P1 hat keine Unterstützer; P2 kostet 5 > Budget 3 (und mehr als das Geld seines Unterstützers, 1,5)
    assert A.equal_shares(inst) == []
    assert A.optimal(inst) == []                             # ein Projekt ohne Zustimmung verbessert den Wert nicht und wird nicht genommen
    assert A.greedy_votes(inst) == [0]                       # die gierige Regel kauft es trotzdem (Zustimmungen 0, passt noch): Reihenfolge P2 (1 Zustimmung, passt nicht), P1


def test_budget_smaller_than_every_cost():
    inst = make([[0, 1], [0, 1]], costs=[3, 4], budget=2, n=2)
    for rule in A.RULE_FUNCTIONS:
        assert A.run_rule(rule, inst) == []
    o = A.evaluate(inst, [])
    assert o.spent == 0 and o.unspent == 2 and o.total == 0 and o.minority_budget is None and o.no_hit == 1.0


def test_unknown_rule_raises(lager):
    with pytest.raises(ValueError):
        A.run_rule("x", lager)


def test_optimal_reconstruction_and_exact_budget():
    # Kosten 2, 3, 4, Budget 6: {P1, P3} = 6 Kosten mit Zustimmungen 3 + 5 = 8 gegen {P2} = 4 und {P1, P2} = 7 -> [0, 2]
    inst = make([[0, 1, 2], [0, 1, 2, 3], [0, 1, 2, 3, 4]], costs=[2, 3, 4], budget=6, n=5)
    assert A.optimal(inst) == [0, 2]
    assert A.evaluate(inst, [0, 2]).total == 8


def test_evaluate_by_hand(lager):
    o = A.evaluate(lager, [0, 1, 3])
    assert o.spent == 9 and o.unspent == 1 and o.total == 7 + 7 + 3
    assert o.minority_budget == pytest.approx(3 / 9)                       # P4 gehört dem kleineren Lager
    assert o.mean_major == pytest.approx(2.0) and o.mean_minor == pytest.approx(1.0)
    assert o.no_hit == 0.0 and o.no_hit_minor == 0.0
    g = A.evaluate(lager, [0, 1, 2])
    assert g.minority_budget == 0.0 and g.no_hit == pytest.approx(0.3) and g.no_hit_minor == pytest.approx(1.0)      # alle drei Wähler des kleineren Lagers ohne Treffer


def test_no_hit_ignores_voters_without_any_approval():
    inst = make([[0], [0]], costs=[1, 1], budget=1, n=4)                   # Wähler 1 bis 3 stimmen nie zu
    o = A.evaluate(inst, [0])
    assert o.voters_with_approval == 1 and o.no_hit == 0.0


def test_no_hit_minor_is_nan_without_approvals_in_the_minority():
    inst = make([[0, 1]], costs=[1], budget=1, n=3, group=[0, 0, 1], own=[0])
    assert math.isnan(A.evaluate(inst, [0]).no_hit_minor)


def test_jr_violation_by_hand(lager):
    # Gierig: [P1, P2, P3]. Die Wähler 7 bis 9 stimmen P4 zu (Kosten 3); ihr Anteil am Budget: 3 · 10 = 30 ≥ n · Kosten = 10 · 3 = 30, also berechtigt; keiner hat ein finanziertes Projekt.
    v = A.group_violations(lager, [0, 1, 2])
    assert v["jr"] == ((3,), 3) and v["ejr"] == ((3,), 3) and v["ejr1"] is None
    assert A.group_violations(lager, [0, 1, 3]) == {"jr": None, "ejr": None, "ejr1": None}


def test_group_just_below_its_entitlement_is_not_protected():
    # Wie oben, aber das Budget 9: 3 · 9 = 27 < 30 -> die drei Wähler sind nicht mehr berechtigt, ihr Projekt zu bekommen.
    inst = make([list(range(7))] * 3 + [[7, 8, 9]], costs=[3, 3, 3, 3], budget=9, n=10)
    assert A.group_violations(inst, [0, 1, 2])["jr"] is None


def test_ejr_needs_as_many_projects_as_the_group_could_pay():
    # 4 Wähler, Budget 8; alle stimmen P1 und P2 zu (Kosten 2 und 2): zusammen 4 ≤ 8, die Gruppe aller vier ist zu {P1, P2} berechtigt. Finanziert wird nur P1:
    # JR erfüllt (jeder hat eines), EJR verletzt (jeder hat 1 < 2), EJR bis auf eins erfüllt (1 ≥ 2 − 1).
    inst = make([[0, 1, 2, 3], [0, 1, 2, 3]], costs=[2, 2], budget=8, n=4)
    v = A.group_violations(inst, [0])
    assert v["jr"] is None and v["ejr"] == ((0, 1), 4) and v["ejr1"] is None
    assert A.group_violations(inst, [0, 1]) == {"jr": None, "ejr": None, "ejr1": None}


def test_ejr1_violation_needs_a_group_that_deserves_three():
    # Alle fünf Wähler stimmen P1, P2, P3 zu (Kosten je 1), Budget 10: berechtigt zu allen dreien. Finanziert wird nur P1: u = 1.
    # Schon {P1, P2} verletzt EJR (1 < 2); bis auf eins (1 < |T| − 1) erst mit {P1, P2, P3} (1 < 2).
    inst = make([[0, 1, 2, 3, 4]] * 3, costs=[1, 1, 1], budget=10, n=5)
    v = A.group_violations(inst, [0])
    assert v["ejr"] == ((0, 1), 5)
    assert v["ejr1"] == ((0, 1, 2), 5)
