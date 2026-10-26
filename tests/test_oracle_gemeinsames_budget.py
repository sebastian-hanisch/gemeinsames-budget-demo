"""Orakel-Test gemeinsames-budget-demo: jede Regel und jede Prüfung gegen einen ANDEREN Rechenweg.

* Gleiche Anteile: exakte Bruchrechnung (fractions) mit der Definition „kleinstes ρ mit Σ min(Restgeld, ρ) = Kosten“, ρ durch Aufzählen der Knickstellen.
* Größte Gesamtzustimmung: Aufzählung aller Projektmengen.
* Gierig: Sortierung mit exakten Brüchen (Zustimmungen je Kosten als Fraction).
* JR, EJR, EJR bis auf eins: Aufzählung ALLER Wählergruppen und ALLER Projektmengen auf kleinen Instanzen (die Demo zählt nur die Projektmengen auf).
"""

from fractions import Fraction
from itertools import chain, combinations

import numpy as np
import pytest

import gmb_algorithm as A
from conftest import make


def random_instance(seed, n_range=(3, 8), m_range=(2, 6)):
    rng = np.random.default_rng(seed)
    n = int(rng.integers(*n_range, endpoint=True))
    m = int(rng.integers(*m_range, endpoint=True))
    costs = [int(c) for c in rng.integers(1, 5, size=m, endpoint=True)]
    p = float(rng.choice([0.25, 0.5, 0.75]))
    supporters = [[i for i in range(n) if rng.random() < p] for _ in range(m)]
    budget = int(rng.integers(1, sum(costs), endpoint=True))
    return make(supporters, costs, budget, n), supporters, costs, budget, n


def subsets(items, min_size=0):
    items = list(items)
    return chain.from_iterable(combinations(items, k) for k in range(min_size, len(items) + 1))


# --- Gleiche Anteile mit exakter Bruchrechnung ----------------------------------------------------------------------------------------------

def naive_rho(money, cost):
    """Kleinstes ρ mit Σ min(b, ρ) = cost; None, wenn Σ b < cost. Die Funktion ist stückweise linear: für jede Zahl t von Wählern, die ihr ganzes Restgeld geben, ist ρ = (cost − Σ der t kleinsten) / (k − t)."""
    b = sorted(money)
    if sum(b) < cost:
        return None
    k = len(b)
    for t in range(k):
        rho = (cost - sum(b[:t])) / (k - t)
        if sum(min(x, rho) for x in b) == cost:
            return rho
    return None


def naive_equal_shares(supporters, costs, budget, n):
    money = [Fraction(budget, n)] * n
    bought = []
    while True:
        best = None
        for j, sup in enumerate(supporters):
            if j in bought or not sup:
                continue
            rho = naive_rho([money[i] for i in sup], Fraction(costs[j]))
            if rho is not None and (best is None or rho < best[0]):
                best = (rho, j)
        if best is None:
            return sorted(bought)
        rho, j = best
        for i in supporters[j]:
            money[i] = max(money[i] - rho, Fraction(0))
        bought.append(j)


@pytest.mark.parametrize("seed", range(150))
def test_equal_shares_matches_exact_fractions(seed):
    inst, supporters, costs, budget, n = random_instance(seed)
    assert A.equal_shares(inst) == naive_equal_shares(supporters, costs, budget, n)


def test_naive_rho_by_hand():
    assert naive_rho([Fraction(1, 2), Fraction(1, 2), Fraction(1), Fraction(1)], Fraction(3)) == 1
    assert naive_rho([Fraction(2), Fraction(2)], Fraction(3)) == Fraction(3, 2)
    assert naive_rho([Fraction(1)], Fraction(3)) is None


# --- Größte Gesamtzustimmung durch Aufzählung ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("seed", range(150))
def test_optimal_matches_enumeration(seed):
    inst, supporters, costs, budget, n = random_instance(seed, m_range=(2, 8))
    best = max(sum(len(supporters[j]) for j in W) for W in subsets(range(len(costs))) if sum(costs[j] for j in W) <= budget)
    chosen = A.optimal(inst)
    assert sum(costs[j] for j in chosen) <= budget
    assert sum(len(supporters[j]) for j in chosen) == best


# --- Gierige Regeln mit exakter Sortierung ---------------------------------------------------------------------------------------------------

def naive_greedy(order, costs, budget):
    chosen, spent = [], 0
    for j in order:
        if spent + costs[j] <= budget:
            chosen.append(j)
            spent += costs[j]
    return sorted(chosen)


@pytest.mark.parametrize("seed", range(100))
def test_greedy_rules_match_exact_ordering(seed):
    inst, supporters, costs, budget, n = random_instance(seed)
    m = len(costs)
    by_votes = sorted(range(m), key=lambda j: (-len(supporters[j]), j))
    by_ratio = sorted(range(m), key=lambda j: (-Fraction(len(supporters[j]), costs[j]), j))
    assert A.greedy_votes(inst) == naive_greedy(by_votes, costs, budget)
    assert A.greedy_ratio(inst) == naive_greedy(by_ratio, costs, budget)


# --- Gruppenansprüche durch Aufzählung aller Gruppen und Projektmengen -----------------------------------------------------------------------

def brute_violations(supporters, costs, budget, n, chosen):
    """Für jede nicht leere Wählergruppe S und jede nicht leere Projektmenge T: berechtigt (alle in S stimmen allen in T zu, |S|·B ≥ n·Kosten(T)),
    und dann ist JR verletzt, wenn alle in S kein finanziertes Projekt nach Geschmack haben (u < 1), EJR bei u < |T|, bis auf eins bei u < |T| − 1."""
    approves = [{j for j in range(len(costs)) if i in supporters[j]} for i in range(n)]
    u = [len(approves[i] & set(chosen)) for i in range(n)]
    found = {"jr": False, "ejr": False, "ejr1": False}
    for S in subsets(range(n), 1):
        common = set.intersection(*(approves[i] for i in S))
        for T in subsets(sorted(common), 1):
            if len(S) * budget < n * sum(costs[j] for j in T):
                continue
            if all(u[i] < 1 for i in S):
                found["jr"] = True
            if all(u[i] < len(T) for i in S):
                found["ejr"] = True
            if all(u[i] < len(T) - 1 for i in S):
                found["ejr1"] = True
    return found


def chosen_sets(inst, seed):
    """Die Ausgaben der fünf Regeln und dazu sechs zufällige Projektmengen (die Prüfung verlangt keine Zulässigkeit): so kommen viele verletzte Ansprüche vor, was bei den Regeln allein selten ist."""
    rng = np.random.default_rng(1000 + seed)
    sets = [A.run_rule(rule, inst) for rule in A.RULE_FUNCTIONS]
    for _ in range(6):
        k = int(rng.integers(0, inst.m, endpoint=True))
        sets.append(sorted(int(j) for j in rng.choice(inst.m, size=k, replace=False)))
    return sets


@pytest.mark.parametrize("seed", range(120))
def test_group_violations_match_enumeration_of_all_groups(seed):
    inst, supporters, costs, budget, n = random_instance(seed, n_range=(3, 7), m_range=(2, 5))
    for chosen in chosen_sets(inst, seed):
        got = A.group_violations(inst, chosen)
        want = brute_violations(supporters, costs, budget, n, chosen)
        assert {k: v is not None for k, v in got.items()} == want, (seed, chosen)


def test_the_enumeration_oracle_is_not_vacuous():
    """Das Orakel findet Verstöße (sonst wäre die Gleichheit mit der Demo leer), in jeder der drei Eigenschaften, und es gibt auch Fälle ohne Verstoß."""
    hits = {"jr": 0, "ejr": 0, "ejr1": 0}
    clean = total = 0
    for seed in range(120):
        inst, supporters, costs, budget, n = random_instance(seed, n_range=(3, 7), m_range=(2, 5))
        for chosen in chosen_sets(inst, seed):
            found = brute_violations(supporters, costs, budget, n, chosen)
            for k in hits:
                hits[k] += found[k]
            clean += not any(found.values())
            total += 1
    assert hits["jr"] >= 60 and hits["ejr"] >= hits["jr"] and hits["ejr1"] >= 15 and clean >= 100, (hits, clean, total)


@pytest.mark.parametrize("seed", range(120))
def test_every_witness_is_entitled_and_unsatisfied(seed):
    """Das gelieferte Beispiel stimmt: die gemeldete Zahl von Wählern stimmt allen Projekten der Menge zu, ist berechtigt und hat zu wenig."""
    inst, supporters, costs, budget, n = random_instance(seed, n_range=(3, 8), m_range=(2, 6))
    chosen = [] if seed % 3 == 0 else A.greedy_votes(inst)
    sat = inst.approvals[:, chosen].sum(axis=1) if chosen else np.zeros(n, dtype=int)
    need = {"jr": lambda T: 1, "ejr": len, "ejr1": lambda T: len(T) - 1}
    for key, w in A.group_violations(inst, chosen).items():
        if w is None:
            continue
        T, size = w
        group = [i for i in range(n) if all(inst.approvals[i, j] for j in T) and sat[i] < need[key](T)]
        assert len(group) == size and size * budget >= n * sum(costs[j] for j in T)


# --- Eigenschaften, die aus der Definition folgen --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("seed", range(200))
def test_completion_only_adds_projects(seed):
    inst, *_ = random_instance(seed)
    base, full = A.equal_shares(inst), A.equal_shares_completed(inst)
    assert set(base) <= set(full) and sum(int(inst.costs[j]) for j in full) <= inst.budget


@pytest.mark.parametrize("seed", range(200))
def test_equal_shares_violate_no_group_property_in_random_instances(seed):
    """In diesen zufälligen Instanzen verletzen gleiche Anteile (mit und ohne aufgefüllten Rest) weder JR noch EJR noch EJR bis auf eins (ein Befund, kein Beweis)."""
    inst, *_ = random_instance(seed, n_range=(4, 12), m_range=(3, 8))
    for rule in ("anteile", "ergaenzt"):
        assert A.group_violations(inst, A.run_rule(rule, inst)) == {"jr": None, "ejr": None, "ejr1": None}, (seed, rule)

