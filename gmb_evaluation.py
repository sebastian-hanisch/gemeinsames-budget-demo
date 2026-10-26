"""Auswertung: Einstellungen, Analyse einer Instanz, Tabellen, Verdikte als reine Funktionen (ohne Streamlit) und die festen Messreihen."""

import math
from dataclasses import dataclass

import numpy as np

import gmb_algorithm as A
import gmb_constants as C
from gmb_scenario import Instance, make_instance

PROPERTIES = {"jr": "Gerechtfertigte Repräsentation (JR)", "ejr": "Erweiterte Repräsentation (EJR)", "ejr1": "EJR bis auf ein Projekt"}


def num(x: float, digits: int = 1) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def pct(x, digits: int = 0) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{100 * x:.{digits}f} %".replace(".", ",")


def short_rule(rule: str) -> str:
    return C.RULE_SHORT[rule]


def label(p: int) -> str:
    """Projekte heißen P1 bis Pm (der Index beginnt intern bei 0)."""
    return f"P{p + 1}"


def labels(T) -> str:
    return ", ".join(label(p) for p in T)


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    m: int = C.DEFAULT_M
    budget: int = C.DEFAULT_BUDGET
    group: int = C.DEFAULT_GROUP
    own: int = C.DEFAULT_OWN
    cross: int = C.DEFAULT_CROSS
    seed: int = C.DEFAULT_SEED


@dataclass
class Analysis:
    settings: Settings
    inst: Instance
    outcomes: dict      # Regel -> Outcome
    violations: dict    # Regel -> {jr, ejr, ejr1} (None oder (T, Gruppengröße))
    optimum: int        # größte erreichbare Summe der Zustimmungen
    minority_share: float


def analyse(settings: Settings) -> Analysis:
    return analyse_instance(settings, make_instance(settings.n, settings.m, settings.budget, settings.group, settings.own, settings.cross, settings.seed))


def analyse_instance(settings: Settings, inst: Instance) -> Analysis:
    """Alle Regeln und alle Gruppenprüfungen auf einer gegebenen Instanz (die Tests reichen handgebaute Instanzen herein)."""
    chosen = {rule: A.run_rule(rule, inst) for rule in C.RULES}
    outcomes = {rule: A.evaluate(inst, ch) for rule, ch in chosen.items()}
    violations = {rule: A.group_violations(inst, ch) for rule, ch in chosen.items()}
    return Analysis(settings=settings, inst=inst, outcomes=outcomes, violations=violations, optimum=outcomes["optimal"].total,
                    minority_share=float((inst.group == 1).mean()))


def welfare(a: Analysis, rule: str) -> float:
    """Summe der Zustimmungen im Verhältnis zur größtmöglichen Summe (1 = das Optimum)."""
    return a.outcomes[rule].total / a.optimum if a.optimum else 1.0


def violated(a: Analysis, rule: str, key: str) -> bool:
    return a.violations[rule][key] is not None


def rule_rows(a: Analysis) -> list[dict]:
    """Zeilen für st.table: je Regel eine Zeile."""
    rows = []
    for rule in C.RULES:
        o = a.outcomes[rule]
        row = {
            "Regel": C.RULES[rule],
            "Projekte": len(o.chosen),
            "Ausgaben": f"{o.spent} von {a.inst.budget}",
            "Zustimmungen": f"{o.total} ({pct(welfare(a, rule))} des Größtmöglichen)",
            "Budget für das kleinere Lager": pct(o.minority_budget),
            "Wähler ohne Treffer (kleineres Lager)": f"{pct(o.no_hit)} ({pct(o.no_hit_minor)})",
        }
        for key, name in PROPERTIES.items():
            row[name] = "verletzt" if violated(a, rule, key) else "erfüllt"
        rows.append(row)
    return rows


def witness_lines(a: Analysis) -> list[str]:
    """Je Regel mit verletzter Eigenschaft ein Beispiel: die Gruppe, ihre Projekte und warum sie berechtigt ist."""
    lines = []
    for rule in C.RULES:
        for key in ("jr", "ejr", "ejr1"):
            w = a.violations[rule][key]
            if w is None:
                continue
            T, size = w
            cost = int(a.inst.costs[list(T)].sum())
            need = {"jr": "hat keines der finanzierten Projekte, denen er zustimmt", "ejr": f"hat weniger als {len(T)} der finanzierten Projekte, denen er zustimmt",
                    "ejr1": f"hat weniger als {len(T) - 1} der finanzierten Projekte, denen er zustimmt"}[key]
            lines.append(
                f"**{short_rule(rule)}, {PROPERTIES[key]}:** {size} Wähler ({pct(size / a.inst.n)}) stimmen allen Projekten {labels(T)} zu (Kosten zusammen {cost}); "
                f"ihr Anteil am Budget ({num(size * a.inst.budget / a.inst.n)} von {a.inst.budget}) reicht dafür, doch jeder von ihnen {need}."
            )
            break  # je Regel das schärfste verletzte Maß, das zuerst in der Reihenfolge steht
    return lines


def verdict_state(a: Analysis) -> tuple[str, str]:
    """Verdikt für die Einstellungen: was das kleinere Lager bekommt, welche Regeln Gruppenansprüche verletzen und was die gleichen Anteile kosten."""
    o = a.outcomes
    s = a.minority_share
    bad = [short_rule(r) for r in C.RULES if violated(a, r, "jr")]
    text = (f"Das kleinere Lager stellt {pct(s)} der Wähler. Gierig nach Zustimmungen gibt seinen Projekten {pct(o['stimmen'].minority_budget)} der Ausgaben, "
            f"gierig nach Zustimmung je Kosten {pct(o['kosten'].minority_budget)}, gleiche Anteile {pct(o['anteile'].minority_budget)}. ")
    if bad:
        text += f"Gerechtfertigte Repräsentation (JR) ist verletzt bei: {', '.join(bad)}. Erfüllt bei den übrigen. "
    else:
        text += "Gerechtfertigte Repräsentation (JR) ist bei allen fünf Regeln erfüllt. "
    text += (f"Gleiche Anteile geben {pct(o['anteile'].spent / a.inst.budget)} des Budgets aus ({pct(welfare(a, 'anteile'))} der größtmöglichen Zustimmungen); "
             f"mit aufgefülltem Rest sind es {pct(o['ergaenzt'].spent / a.inst.budget)} und {pct(welfare(a, 'ergaenzt'))}.")
    return ("warning" if violated(a, "stimmen", "jr") else "info"), text


# --- feste Messreihen -------------------------------------------------------------------------------------------------------------------------

def _cell(n, m, budget, group, own, cross, runs, seed) -> dict:
    """Mittelwerte über `runs` Instanzen (Zufalls-Seeds seed .. seed + runs − 1) für alle Regeln."""
    acc = {rule: {"mb": [], "nhm": [], "w": [], "un": [], "jr": 0, "ejr": 0, "ejr1": 0} for rule in C.RULES}
    for s in range(runs):
        inst = make_instance(n, m, budget, group, own, cross, seed + s)
        outs = {rule: A.evaluate(inst, A.run_rule(rule, inst)) for rule in C.RULES}
        opt = outs["optimal"].total
        for rule in C.RULES:
            o, d = outs[rule], acc[rule]
            if o.minority_budget is not None:
                d["mb"].append(o.minority_budget)
            if not math.isnan(o.no_hit_minor):
                d["nhm"].append(o.no_hit_minor)
            d["w"].append(o.total / opt if opt else 1.0)
            d["un"].append(o.unspent / inst.budget)
            v = A.group_violations(inst, o.chosen)
            for key in ("jr", "ejr", "ejr1"):
                d[key] += v[key] is not None
    out = {}
    for rule, d in acc.items():
        out[rule] = {
            "minority_budget": float(np.mean(d["mb"])) if d["mb"] else float("nan"),
            "no_hit_minor": float(np.mean(d["nhm"])) if d["nhm"] else float("nan"),
            "welfare": float(np.mean(d["w"])), "unspent": float(np.mean(d["un"])),
            "jr": d["jr"] / runs, "ejr": d["ejr"] / runs, "ejr1": d["ejr1"] / runs,
        }
    return out


def _sweep(param: str, values, runs: int, seed: int) -> list[dict]:
    rows = []
    for v in values:
        args = {"budget": C.SERIES_BUDGET, "group": C.SERIES_GROUP, "own": C.SERIES_OWN, "cross": C.SERIES_CROSS}
        args[param] = v
        cell = _cell(C.SERIES_N, C.SERIES_M, args["budget"], args["group"], args["own"], args["cross"], runs, seed)
        for rule in C.RULES:
            rows.append({"param": param, "x": v, "rule": rule, "runs": runs, **cell[rule]})
    return rows


def series_groups(runs: int = C.SERIES_RUNS, seed: int = C.SERIES_SEED) -> list[dict]:
    """Reihe 1: Anteil des größeren Lagers an den Wählern."""
    return _sweep("group", C.SERIES_GROUPS, runs, seed)


def series_budgets(runs: int = C.SERIES_RUNS, seed: int = C.SERIES_SEED) -> list[dict]:
    """Reihe 2: Budget in Prozent der Gesamtkosten."""
    return _sweep("budget", C.SERIES_BUDGETS, runs, seed)


def series_cohesion(runs: int = C.SERIES_RUNS, seed: int = C.SERIES_SEED) -> list[dict]:
    """Reihe 3: Geschlossenheit der Lager (Zustimmung zu den eigenen Projekten)."""
    return _sweep("own", C.SERIES_OWNS, runs, seed)


def cell_of(rows: list[dict], x, rule: str) -> dict:
    return next(r for r in rows if r["x"] == x and r["rule"] == rule)


def series_rows(rows: list[dict], key: str, formatter=pct) -> list[dict]:
    """Zeilen für st.table: je Wert des Reglers eine Zeile, je Regel eine Spalte."""
    out = []
    for x in dict.fromkeys(r["x"] for r in rows):
        row = {{"group": "Größeres Lager (%)", "budget": "Budget (%)", "own": "Zustimmung zu eigenen Projekten (%)"}[rows[0]["param"]]: x}
        for rule in C.RULES:
            row[short_rule(rule)] = formatter(cell_of(rows, x, rule)[key])
        out.append(row)
    return out


def verdict_groups(rows: list[dict]) -> tuple[str, str]:
    """Verdikt der Reihe 1: beim ungleichsten Verhältnis, was das kleinere Lager an Ausgaben bekommt."""
    x = max(r["x"] for r in rows)
    r = {rule: cell_of(rows, x, rule) for rule in C.RULES}
    text = (f"Bei {x} : {100 - x} Wählern (Mittel über {rows[0]['runs']} Instanzen) bekommen die Projekte des kleineren Lagers {pct(r['stimmen']['minority_budget'])} der Ausgaben bei gierig nach Zustimmungen, "
            f"{pct(r['kosten']['minority_budget'])} bei gierig je Kosten und {pct(r['anteile']['minority_budget'])} bei gleichen Anteilen; die Wähler des kleineren Lagers sind {100 - x} %. "
            f"Wähler des kleineren Lagers ohne finanziertes Wunschprojekt: {pct(r['stimmen']['no_hit_minor'])} (gierig nach Zustimmungen), {pct(r['anteile']['no_hit_minor'])} (gleiche Anteile).")
    return "info", text


def verdict_budgets(rows: list[dict]) -> tuple[str, str]:
    """Verdikt der Reihe 2: Anteil der Instanzen mit verletzter Gerechtfertigter Repräsentation je Regel bei kleinstem und größtem Budget."""
    lo, hi = min(r["x"] for r in rows), max(r["x"] for r in rows)
    parts = [f"{short_rule(rule)} {pct(cell_of(rows, lo, rule)['jr'])} bzw. {pct(cell_of(rows, hi, rule)['jr'])}" for rule in C.RULES]
    return "info", (f"Anteil der Instanzen mit verletzter Gerechtfertigter Repräsentation (JR) bei {lo} % bzw. {hi} % Budget: " + "; ".join(parts) + ". "
                    f"Unausgegebenes Budget bei gleichen Anteilen: {pct(cell_of(rows, lo, 'anteile')['unspent'])} bzw. {pct(cell_of(rows, hi, 'anteile')['unspent'])}.")


def verdict_cohesion(rows: list[dict]) -> tuple[str, str]:
    """Verdikt der Reihe 3: bei der größten Geschlossenheit die Verletzungen von JR und EJR je Regel."""
    x = max(r["x"] for r in rows)
    parts = [f"{short_rule(rule)} JR {pct(cell_of(rows, x, rule)['jr'])}, EJR {pct(cell_of(rows, x, rule)['ejr'])}, EJR bis auf eins {pct(cell_of(rows, x, rule)['ejr1'])}" for rule in C.RULES]
    return "info", f"Bei {x} % Zustimmung zu den eigenen Projekten sind in {rows[0]['runs']} Instanzen verletzt: " + "; ".join(parts) + "."
