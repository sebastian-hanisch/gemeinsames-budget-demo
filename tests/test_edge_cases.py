"""Randfälle: Extremwerte der Regler, Invarianten jeder Auswahl, entartete Instanzen."""

import itertools

import numpy as np
import pytest

import gmb_algorithm as A
import gmb_constants as C
import gmb_evaluation as ev
from gmb_scenario import make_instance
from conftest import make

EXTREMES = [
    dict(n=C.N_MIN, m=C.M_MIN, budget=C.BUDGET_MIN, group=C.GROUP_MIN, own=C.OWN_MIN, cross=C.CROSS_MIN),
    dict(n=C.N_MAX, m=C.M_MAX, budget=C.BUDGET_MAX, group=C.GROUP_MAX, own=C.OWN_MAX, cross=C.CROSS_MAX),
    dict(n=C.N_MIN, m=C.M_MAX, budget=C.BUDGET_MAX, group=C.GROUP_MAX, own=C.OWN_MAX, cross=C.CROSS_MIN),
    dict(n=C.N_MAX, m=C.M_MIN, budget=C.BUDGET_MIN, group=C.GROUP_MIN, own=C.OWN_MIN, cross=C.CROSS_MAX),
    dict(n=C.N_MIN, m=C.M_MIN + 1, budget=C.BUDGET_MIN, group=C.GROUP_MAX, own=C.OWN_MAX, cross=C.CROSS_MIN),
]


@pytest.mark.parametrize("extreme", EXTREMES)
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_invariants_at_the_extremes(extreme, seed):
    a = ev.analyse(ev.Settings(seed=seed, **extreme))
    inst = a.inst
    assert inst.n == extreme["n"] and inst.m == extreme["m"] and 1 <= inst.budget
    for rule, o in a.outcomes.items():
        assert list(o.chosen) == sorted(set(o.chosen)), rule
        assert o.spent <= inst.budget and o.spent == int(inst.costs[list(o.chosen)].sum()) and o.unspent == inst.budget - o.spent
        assert o.total <= a.optimum and 0.0 <= o.no_hit <= 1.0, rule
        assert 0.0 <= ev.welfare(a, rule) <= 1.0
        v = a.violations[rule]
        assert (v["jr"] is None) or (v["ejr"] is not None)                          # JR verletzt heißt EJR verletzt (gleiche Gruppe, größere Forderung)
    assert set(a.outcomes["anteile"].chosen) <= set(a.outcomes["ergaenzt"].chosen)
    assert a.violations["anteile"]["jr"] is None and a.violations["ergaenzt"]["jr"] is None
    kind, text = ev.verdict_state(a)
    assert kind in ("warning", "info") and text
    assert len(ev.rule_rows(a)) == len(C.RULES)
    ev.witness_lines(a)


def test_instance_is_a_function_of_its_seed():
    a = make_instance(50, 10, 30, 60, 50, 5, 3)
    b = make_instance(50, 10, 30, 60, 50, 5, 3)
    c = make_instance(50, 10, 30, 60, 50, 5, 4)
    assert (a.approvals == b.approvals).all() and (a.costs == b.costs).all() and a.budget == b.budget
    assert not (a.approvals == c.approvals).all()
    assert a.costs.min() >= C.COST_MIN and a.costs.max() <= C.COST_MAX


def test_instance_shares_follow_the_settings():
    inst = make_instance(100, 16, 30, 60, 90, 0, 5)
    assert int((inst.group == 0).sum()) == 60 and inst.budget == int(round(0.3 * inst.costs.sum()))
    own_rate = inst.approvals[inst.group[:, None] == inst.own[None, :]].mean()
    cross_rate = inst.approvals[inst.group[:, None] != inst.own[None, :]].mean()
    assert own_rate > 0.8 and cross_rate == 0.0


def test_instance_has_two_nonempty_groups_at_the_group_bounds():
    for n in (C.N_MIN, C.N_MAX):
        for group in (C.GROUP_MIN, C.GROUP_MAX):
            inst = make_instance(n, 8, 30, group, 50, 5, 1)
            assert 1 <= int((inst.group == 1).sum()) < n


def test_everybody_approves_everything_every_rule_buys_by_cost_or_support():
    inst = make([list(range(4))] * 3, costs=[3, 1, 2], budget=3, n=4)
    assert A.greedy_votes(inst) == [0]                      # alle gleich beliebt: der kleinste Index zuerst (P1 kostet 3)
    assert A.greedy_ratio(inst) == [1, 2]                   # je Kosten: P2 (4/1), P3 (4/2) zuerst
    assert A.equal_shares(inst) == [1, 2]                   # ρ: P2 0,25, P3 0,5, P1 0,75; nach P2 und P3 ist alles Geld ausgegeben (0,25 + 0,5 = 0,75 je Wähler)
    assert A.optimal(inst) == [1, 2]                        # 8 Zustimmungen für Kosten 3 gegen 4 für P1


def test_a_single_voter_buys_whatever_fits():
    inst = make([[0], [0], [0]], costs=[2, 2, 2], budget=5, n=1)
    assert A.equal_shares(inst) == [0, 1]                   # Restgeld 5 → 3 → 1: das dritte Projekt (2) ist unbezahlbar
    assert A.equal_shares_completed(inst) == [0, 1]         # Restbudget 1 < 2


def test_no_project_is_supported_by_anybody():
    inst = make([[], [], []], costs=[1, 2, 3], budget=3, n=3)
    for rule in C.RULES:
        o = A.evaluate(inst, A.run_rule(rule, inst))
        assert o.total == 0
    assert A.run_rule("optimal", inst) == [] and A.run_rule("anteile", inst) == []
    assert A.group_violations(inst, []) == {"jr": None, "ejr": None, "ejr1": None}


def test_zero_budget_entitles_nobody():
    inst = make([[0, 1]], costs=[1], budget=0, n=2)
    assert A.group_violations(inst, []) == {"jr": None, "ejr": None, "ejr1": None}      # |S|·0 ≥ n·1 gilt nie


def test_groups_exactly_at_the_threshold_are_entitled():
    # n = 4, Budget 4, ein Projekt der Kosten 1 mit genau einem Unterstützer: 1 · 4 ≥ 4 · 1 -> berechtigt (Gleichheit zählt)
    inst = make([[0]], costs=[1], budget=4, n=4)
    assert A.group_violations(inst, [])["jr"] == ((0,), 1)
    inst = make([[0]], costs=[2], budget=4, n=4)             # 1 · 4 < 4 · 2: nicht berechtigt
    assert A.group_violations(inst, [])["jr"] is None


def test_equal_budget_costs_and_ties_are_stable_under_float_rounding():
    # 3 Wähler, Budget 1 (je 1/3), 3 gleiche Projekte der Kosten 1/3 · 1 ... nur ganze Kosten: 3 Wähler, Budget 3, Projekte Kosten 1, Unterstützer je ein Wähler
    inst = make([[0], [1], [2]], costs=[1, 1, 1], budget=3, n=3)
    assert A.equal_shares(inst) == [0, 1, 2]
    inst = make([[0, 1, 2]] * 7, costs=[1] * 7, budget=3, n=3)           # 7 gleiche Projekte, Geld für 3: die ersten drei (Gleichstand, kleinere Indizes)
    assert A.equal_shares(inst) == [0, 1, 2]


def test_grid_of_small_settings_never_raises():
    for n, m, g in itertools.product((C.N_MIN, 33), (C.M_MIN, 7, 8), (C.GROUP_MIN, C.GROUP_MAX)):
        a = ev.analyse(ev.Settings(n=n, m=m, group=g, budget=C.BUDGET_MIN, own=50, cross=5, seed=2))
        assert np.isfinite([o.total for o in a.outcomes.values()]).all()
