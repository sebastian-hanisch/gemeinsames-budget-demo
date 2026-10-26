"""Kern: vier Auswahlregeln für ein gemeinsames Budget mit Zustimmungsstimmen, Kennzahlen und die Prüfung auf berechtigte Gruppen.

Eine Regel bekommt die Instanz (Zustimmungen, ganzzahlige Kosten, ganzzahliges Budget) und liefert die Liste der finanzierten Projekte (aufsteigend).
Gleichstände entscheidet immer der kleinere Projektindex.
"""

from dataclasses import dataclass

import numpy as np

EPS = 1e-9          # Geldbeträge: Rundungsfehler unterhalb dieser Grenze zählen als 0
RHO_EPS = 1e-12     # zwei Beiträge je Kopf gelten als gleich, wenn sie sich um weniger unterscheiden


def support(inst) -> np.ndarray:
    """Zahl der Zustimmungen je Projekt."""
    return inst.approvals.sum(axis=0)


def greedy(inst, key) -> list:
    """Projekte nach `key` absteigend (Gleichstand: kleinerer Index), jeweils kaufen, wenn es noch ins Budget passt."""
    order = np.argsort(-np.asarray(key, dtype=float), kind="stable")
    chosen, spent = [], 0
    for p in order:
        if spent + int(inst.costs[p]) <= inst.budget:
            chosen.append(int(p))
            spent += int(inst.costs[p])
    return sorted(chosen)


def greedy_votes(inst) -> list:
    return greedy(inst, support(inst))


def greedy_ratio(inst) -> list:
    return greedy(inst, support(inst) / inst.costs)


def equal_shares(inst) -> list:
    """Methode gleicher Anteile (Equal Shares, „Rule X“) bei Zustimmungsstimmen.

    Jeder Wähler bekommt budget / n. Ein Projekt kostet cost und wird von seinen Unterstützern bezahlt; ρ ist der kleinste Beitrag je Kopf, bei dem
    die Unterstützer zusammen cost aufbringen, wobei niemand mehr als sein Restgeld zahlt (min(Restgeld, ρ)). Es wird immer das Projekt mit dem kleinsten ρ
    gekauft (Gleichstand: kleinerer Index), bis kein Projekt mehr bezahlbar ist."""
    n = inst.n
    money = np.full(n, inst.budget / n)
    open_projects = list(range(inst.m))
    chosen = []
    while True:
        best = None
        for p in open_projects:
            sup = np.flatnonzero(inst.approvals[:, p])
            cost = float(inst.costs[p])
            if len(sup) == 0 or money[sup].sum() < cost - EPS:
                continue
            rho = _contribution(np.sort(money[sup]), cost)
            if rho is None:
                continue
            if best is None or rho < best[0] - RHO_EPS:
                best = (rho, p, sup)
        if best is None:
            break
        rho, p, sup = best
        money[sup] = np.maximum(money[sup] - rho, 0.0)
        chosen.append(p)
        open_projects.remove(p)
    return sorted(chosen)


def _contribution(money_sorted, cost):
    """Kleinster Beitrag ρ je Kopf mit Σ min(Restgeld, ρ) ≥ cost; `money_sorted` aufsteigend. None, wenn das Geld nicht reicht."""
    k = len(money_sorted)
    paid = 0.0
    for idx, have in enumerate(money_sorted):
        share = (cost - paid) / (k - idx)
        if share <= have + RHO_EPS:
            return share
        paid += have
    return None


def optimal(inst) -> list:
    """Projektmenge innerhalb des Budgets mit der größten Summe der Zustimmungen (Rucksack, ganzzahlige Kosten, exakt per dynamischer Optimierung).

    Rekonstruktion von hinten: Projekt j gehört zur Lösung, wenn es den Wert gegenüber der Tabelle ohne j verbessert (Gleichstand: j wird nicht genommen)."""
    value = support(inst)
    cap = inst.budget
    table = np.zeros((inst.m + 1, cap + 1), dtype=np.int64)
    for j in range(1, inst.m + 1):
        c = int(inst.costs[j - 1])
        table[j] = table[j - 1]
        if c <= cap:
            table[j, c:] = np.maximum(table[j - 1, c:], table[j - 1, : cap + 1 - c] + int(value[j - 1]))
    chosen, w = [], cap
    for j in range(inst.m, 0, -1):
        if table[j, w] != table[j - 1, w]:
            chosen.append(j - 1)
            w -= int(inst.costs[j - 1])
    return sorted(chosen)


def equal_shares_completed(inst) -> list:
    """Gleiche Anteile, danach wird das übrig gebliebene Budget aufgefüllt: die noch nicht gekauften Projekte nach Zustimmungen je Kosten, solange sie ins Restbudget passen.

    Das Auffüllen kauft nur zusätzliche Projekte; die Zufriedenheit jedes Wählers kann dadurch nicht sinken."""
    chosen = equal_shares(inst)
    spent = int(inst.costs[chosen].sum()) if chosen else 0
    ratio = support(inst) / inst.costs
    for p in np.argsort(-ratio, kind="stable"):
        if int(p) not in chosen and spent + int(inst.costs[p]) <= inst.budget:
            chosen.append(int(p))
            spent += int(inst.costs[p])
    return sorted(chosen)


RULE_FUNCTIONS = {"stimmen": greedy_votes, "kosten": greedy_ratio, "anteile": equal_shares, "ergaenzt": equal_shares_completed, "optimal": optimal}


def run_rule(rule, inst) -> list:
    if rule not in RULE_FUNCTIONS:
        raise ValueError(rule)
    return RULE_FUNCTIONS[rule](inst)


@dataclass(frozen=True)
class Outcome:
    """Kennzahlen einer Auswahl. `minority_budget`: Anteil der Ausgaben für Projekte des kleineren Lagers (None, wenn nichts ausgegeben wurde)."""

    chosen: tuple
    spent: int
    unspent: int
    total: int                # Summe aller Zustimmungen zu den finanzierten Projekten
    mean_major: float         # Zustimmungen je Wähler im größeren Lager
    mean_minor: float         # und im kleineren
    minority_budget: object
    no_hit: float             # Anteil der Wähler mit mindestens einer Zustimmung, von deren Projekten keines finanziert wird
    no_hit_minor: float       # dasselbe im kleineren Lager (nan, wenn dort niemand zugestimmt hat)
    voters_with_approval: int


def evaluate(inst, chosen) -> Outcome:
    chosen = tuple(sorted(int(p) for p in chosen))
    idx = list(chosen)
    spent = int(inst.costs[idx].sum()) if idx else 0
    sat = inst.approvals[:, idx].sum(axis=1) if idx else np.zeros(inst.n, dtype=int)
    minor, major = inst.group == 1, inst.group == 0
    has = inst.approvals.any(axis=1)
    miss = has & (sat == 0)
    minority_spent = sum(int(inst.costs[p]) for p in idx if inst.own[p] == 1)
    n_has_minor = int((has & minor).sum())
    return Outcome(
        chosen=chosen, spent=spent, unspent=inst.budget - spent, total=int(sat.sum()),
        mean_major=float(sat[major].mean()) if major.any() else float("nan"), mean_minor=float(sat[minor].mean()) if minor.any() else float("nan"),
        minority_budget=None if spent == 0 else minority_spent / spent,
        no_hit=float(miss.sum() / max(1, has.sum())), no_hit_minor=float((miss & minor).sum() / n_has_minor) if n_has_minor else float("nan"),
        voters_with_approval=int(has.sum()),
    )


def group_violations(inst, chosen) -> dict:
    """Prüft die Berechtigung von Gruppen EXAKT (alle Projektmengen T, alle Gruppen).

    Eine Gruppe S mit Projektmenge T ist berechtigt, wenn alle Mitglieder jedem Projekt in T zustimmen und |S| · Budget ≥ n · Kosten(T) gilt (die Gruppe
    „zahlt“ T mit ihrem Anteil am Budget). Für gegebenes T ist die gefährdetste Gruppe die der Unterstützer von T, deren Zufriedenheit u (Zahl
    finanzierter Projekte, denen sie zustimmen) unter der Forderung bleibt; deshalb genügt es, T aufzuzählen (Tiefensuche, Zweige ohne genug Unterstützer
    fallen weg: mehr Projekte heißt höhere Kosten und weniger Unterstützer).
      jr   (Gerechtfertigte Repräsentation): kein Mitglied hat ein finanziertes Projekt, dem es zustimmt (u < 1)
      ejr  (erweitert): kein Mitglied hat mindestens |T| finanzierte Projekte nach seinem Geschmack (u < |T|)
      ejr1 (erweitert bis auf ein Projekt, so in dieser Demo definiert): kein Mitglied hat mindestens |T| − 1 (u < |T| − 1)
    Rückgabe je Eigenschaft: None (erfüllt) oder (T, Größe der gefährdeten Gruppe) mit dem kleinsten |T|, dann lexikographisch kleinstem T."""
    n, m, budget = inst.n, inst.m, inst.budget
    idx = list(chosen)
    sat = inst.approvals[:, idx].sum(axis=1) if idx else np.zeros(n, dtype=int)
    found = {"jr": None, "ejr": None, "ejr1": None}

    def consider(key, T, size):
        cur = found[key]
        if cur is None or (len(T), T) < (len(cur[0]), cur[0]):
            found[key] = (T, size)

    def dfs(start, T, mask, cost):
        for j in range(start, m):
            c = cost + int(inst.costs[j])
            mk = mask & inst.approvals[:, j]
            if int(mk.sum()) * budget < n * c:
                continue
            T2 = T + (j,)
            for key, need in (("jr", 1), ("ejr", len(T2)), ("ejr1", len(T2) - 1)):
                size = int((mk & (sat < need)).sum())
                if size * budget >= n * c:
                    consider(key, T2, size)
            dfs(j + 1, T2, mk, c)

    dfs(0, (), np.ones(n, dtype=bool), 0)
    return found
