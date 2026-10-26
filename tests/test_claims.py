"""Befunde der README als feste Werte und Bänder: jede Zahl, die dort steht, ist hier an den festen Plänen der App geprüft.

Die Presets sind einzelne Instanzen und deshalb exakt (Prozente auf ganze Zahlen gerundet wie in der App). Die Messreihen sind Mittel über je 100 Instanzen mit
festen Zufalls-Seeds; Bänder von ±8 Prozentpunkten bei Mittelwerten und ±12 bei Anteilen von Instanzen, Nullen und „nie“-Sätze exakt (die Läufe sind deterministisch).
"""

import pytest

import gmb_algorithm as A
import gmb_constants as C
import gmb_evaluation as ev

MEAN = 0.08
SHARE = 0.12


def at(preset):
    return ev.analyse(ev.Settings(**C.PRESETS[preset]))


def pcts(a, rule_key="minority_budget"):
    return {r: ev.pct(getattr(a.outcomes[r], rule_key)) for r in C.RULES}


def jr_violators(a):
    return [r for r in C.RULES if ev.violated(a, r, "jr")]


# --- Presets: einzelne Instanzen -------------------------------------------------------------------------------------------------------------

def test_default_preset():
    a = at("Zwei Lager: gierig oder gleiche Anteile")
    assert a.inst.budget == 15 and int(a.inst.costs.sum()) == 51 and a.optimum == 225
    assert pcts(a) == {"stimmen": "0 %", "kosten": "38 %", "anteile": "29 %", "ergaenzt": "38 %", "optimal": "47 %"}
    assert jr_violators(a) == ["stimmen"] and not any(ev.violated(a, r, "ejr1") for r in C.RULES)
    assert ev.pct(a.outcomes["anteile"].unspent / a.inst.budget) == "53 %" and ev.pct(ev.welfare(a, "anteile")) == "67 %" and ev.pct(ev.welfare(a, "ergaenzt")) == "98 %"
    assert ev.pct(a.outcomes["stimmen"].no_hit_minor) == "78 %" and ev.pct(a.outcomes["anteile"].no_hit_minor) == "22 %"
    assert a.outcomes["anteile"].spent == 7 and a.outcomes["ergaenzt"].spent == 13 and ev.pct(ev.welfare(a, "stimmen")) == "80 %"


def test_closed_camps_preset_where_even_the_exact_rucksack_leaves_the_minority_out():
    a = at("Geschlossene Lager (80 : 20)")
    assert pcts(a) == {"stimmen": "0 %", "kosten": "0 %", "anteile": "18 %", "ergaenzt": "25 %", "optimal": "0 %"}
    assert jr_violators(a) == ["stimmen", "kosten", "optimal"]
    assert {r: ev.pct(a.outcomes[r].no_hit_minor) for r in C.RULES} == {"stimmen": "95 %", "kosten": "90 %", "anteile": "0 %", "ergaenzt": "0 %", "optimal": "90 %"}


def test_preset_where_the_cost_aware_greedy_fails_too():
    a = at("Auch gierig je Kosten scheitert")
    assert pcts(a) == {"stimmen": "0 %", "kosten": "0 %", "anteile": "36 %", "ergaenzt": "31 %", "optimal": "31 %"}
    assert jr_violators(a) == ["stimmen", "kosten"]


def test_tight_budget_preset():
    a = at("Knappes Budget")
    assert pcts(a) == {"stimmen": "0 %", "kosten": "29 %", "anteile": "25 %", "ergaenzt": "29 %", "optimal": "25 %"}
    assert jr_violators(a) == ["stimmen"] and ev.pct(a.outcomes["anteile"].unspent / a.inst.budget) == "50 %"


def test_no_camps_preset_violates_nothing():
    a = at("Keine Lager")
    assert jr_violators(a) == [] and not any(ev.violated(a, r, "ejr") for r in C.RULES)


def test_the_presets_tell_the_stories_in_their_help_texts():
    texts = C.PRESET_HELP
    assert "0 % der Ausgaben" in texts["Zwei Lager: gierig oder gleiche Anteile"] and "29 %" in texts["Zwei Lager: gierig oder gleiche Anteile"]
    assert "18 %" in texts["Geschlossene Lager (80 : 20)"] and "25 %" in texts["Geschlossene Lager (80 : 20)"]
    assert "36 %" in texts["Auch gierig je Kosten scheitert"] and "25 %" in texts["Knappes Budget"]


# --- Reihe 1: Größe des kleineren Lagers ------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def groups():
    return ev.series_groups()


@pytest.fixture(scope="module")
def budgets():
    return ev.series_budgets()


@pytest.fixture(scope="module")
def cohesion():
    return ev.series_cohesion()


def cell(rows, x, rule, key):
    return ev.cell_of(rows, x, rule)[key]


def test_series_groups_minority_budget(groups):
    assert cell(groups, 60, "stimmen", "minority_budget") == pytest.approx(0.05, abs=MEAN)
    assert cell(groups, 60, "kosten", "minority_budget") == pytest.approx(0.37, abs=MEAN) and cell(groups, 60, "anteile", "minority_budget") == pytest.approx(0.39, abs=MEAN)
    assert cell(groups, 90, "stimmen", "minority_budget") == pytest.approx(0.03, abs=MEAN) and cell(groups, 90, "kosten", "minority_budget") == pytest.approx(0.12, abs=MEAN)
    assert cell(groups, 90, "anteile", "minority_budget") == pytest.approx(0.04, abs=MEAN) and cell(groups, 90, "ergaenzt", "minority_budget") == pytest.approx(0.13, abs=MEAN)
    assert cell(groups, 50, "stimmen", "minority_budget") == pytest.approx(0.47, abs=MEAN) and cell(groups, 50, "anteile", "minority_budget") == pytest.approx(0.51, abs=MEAN)


def test_series_groups_voters_without_a_hit(groups):
    assert cell(groups, 90, "stimmen", "no_hit_minor") == pytest.approx(0.60, abs=MEAN) and cell(groups, 90, "anteile", "no_hit_minor") == pytest.approx(0.63, abs=MEAN)
    assert cell(groups, 90, "ergaenzt", "no_hit_minor") == pytest.approx(0.31, abs=MEAN) and cell(groups, 60, "anteile", "no_hit_minor") == pytest.approx(0.16, abs=MEAN)
    assert cell(groups, 90, "kosten", "no_hit_minor") == pytest.approx(0.34, abs=MEAN)


def test_equal_shares_never_violate_the_group_properties_in_any_series(groups, budgets, cohesion):
    for rows in (groups, budgets, cohesion):
        for r in rows:
            if r["rule"] in ("anteile", "ergaenzt"):
                assert r["jr"] == 0.0 and r["ejr"] == 0.0 and r["ejr1"] == 0.0, (r["param"], r["x"], r["rule"])


def test_greedy_by_votes_violates_jr_often_at_uneven_camps(groups):
    assert cell(groups, 60, "stimmen", "jr") == pytest.approx(0.59, abs=SHARE) and cell(groups, 70, "stimmen", "jr") == pytest.approx(0.64, abs=SHARE)
    assert cell(groups, 50, "stimmen", "jr") == pytest.approx(0.13, abs=SHARE) and cell(groups, 90, "stimmen", "jr") == pytest.approx(0.03, abs=SHARE)
    assert all(cell(groups, x, "kosten", "jr") <= 0.08 for x in C.SERIES_GROUPS) and all(cell(groups, x, "optimal", "jr") <= 0.15 for x in C.SERIES_GROUPS)


def test_equal_shares_leave_budget_unspent_and_lose_approvals(groups):
    for x in C.SERIES_GROUPS:
        assert cell(groups, x, "anteile", "unspent") == pytest.approx(0.42, abs=MEAN)
        assert 0.65 <= cell(groups, x, "anteile", "welfare") <= 0.80
        assert cell(groups, x, "ergaenzt", "welfare") >= 0.95 and cell(groups, x, "ergaenzt", "unspent") <= 0.10
        assert cell(groups, x, "optimal", "welfare") == 1.0


# --- Reihe 2: Budget -------------------------------------------------------------------------------------------------------------------------

def test_series_budgets(budgets):
    assert [cell(budgets, x, "stimmen", "jr") for x in (10, 20, 30, 40, 50)] == pytest.approx([0.22, 0.66, 0.59, 0.62, 0.42], abs=SHARE)
    assert [cell(budgets, x, "anteile", "unspent") for x in (10, 20, 30, 40, 50)] == pytest.approx([0.69, 0.51, 0.42, 0.38, 0.35], abs=MEAN)
    assert [cell(budgets, x, "anteile", "welfare") for x in (10, 20, 30, 40, 50)] == pytest.approx([0.41, 0.63, 0.71, 0.76, 0.78], abs=MEAN)
    assert all(cell(budgets, x, "kosten", "jr") == 0.0 for x in C.SERIES_BUDGETS)
    assert all(cell(budgets, x, "optimal", "jr") <= 0.08 for x in C.SERIES_BUDGETS)


# --- Reihe 3: Geschlossenheit ----------------------------------------------------------------------------------------------------------------

def test_series_cohesion(cohesion):
    assert [cell(cohesion, x, "stimmen", "ejr") for x in C.SERIES_OWNS] == pytest.approx([0.10, 0.36, 0.61, 0.75, 0.83], abs=SHARE)
    assert [cell(cohesion, x, "stimmen", "ejr1") for x in C.SERIES_OWNS] == pytest.approx([0.0, 0.0, 0.0, 0.09, 0.34], abs=SHARE)
    assert all(cell(cohesion, x, "kosten", "ejr") <= 0.06 for x in C.SERIES_OWNS) and all(cell(cohesion, x, "optimal", "ejr") <= 0.12 for x in C.SERIES_OWNS)
    assert [cell(cohesion, x, "anteile", "unspent") for x in C.SERIES_OWNS] == pytest.approx([0.75, 0.57, 0.42, 0.34, 0.26], abs=MEAN)
    assert [cell(cohesion, x, "anteile", "welfare") for x in C.SERIES_OWNS] == pytest.approx([0.40, 0.60, 0.71, 0.78, 0.84], abs=MEAN)
    assert [cell(cohesion, x, "stimmen", "no_hit_minor") for x in C.SERIES_OWNS] == pytest.approx([0.47, 0.50, 0.53, 0.55, 0.47], abs=MEAN)
    assert cell(cohesion, 80, "anteile", "no_hit_minor") == pytest.approx(0.01, abs=0.05) and cell(cohesion, 20, "anteile", "no_hit_minor") == pytest.approx(0.62, abs=MEAN)


def test_ejr1_is_only_violated_by_greedy_by_votes(groups, budgets, cohesion):
    for rows in (groups, budgets, cohesion):
        for r in rows:
            if r["rule"] != "stimmen":
                assert r["ejr1"] == 0.0, (r["param"], r["x"], r["rule"])
    assert cell(cohesion, 80, "stimmen", "ejr1") == pytest.approx(0.34, abs=SHARE) and cell(cohesion, 65, "stimmen", "ejr1") == pytest.approx(0.09, abs=SHARE)


def test_the_series_use_the_documented_seeds():
    assert C.SERIES_SEED == 100000 and C.SERIES_RUNS == 100 and (C.SERIES_N, C.SERIES_M) == (100, 16)
    first = ev._cell(C.SERIES_N, C.SERIES_M, 30, 60, 50, 5, runs=1, seed=C.SERIES_SEED)
    from gmb_scenario import make_instance
    inst = make_instance(C.SERIES_N, C.SERIES_M, 30, 60, 50, 5, C.SERIES_SEED)
    assert first["stimmen"]["unspent"] == A.evaluate(inst, A.greedy_votes(inst)).unspent / inst.budget
