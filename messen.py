"""Einmalige Messung der README-Zahlen (nicht Teil der App): feste Pläne, Ausgabe auf stdout."""

import sys
import time

sys.path.insert(0, ".")
import gmb_constants as C
import gmb_evaluation as ev

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

t0 = time.time()
print("PRESETS")
for name, p in C.PRESETS.items():
    a = ev.analyse(ev.Settings(**p))
    print(name, "| Budget", a.inst.budget, "von", int(a.inst.costs.sum()), "| Wähler", int((a.inst.group == 0).sum()), ":", int((a.inst.group == 1).sum()), "| Optimum", a.optimum)
    for r in ev.rule_rows(a):
        print("   ", r)
    print("   ", ev.verdict_state(a)[1])

for title, fn, key_list in (("REIHE 1 (Lagergröße)", ev.series_groups, ("minority_budget", "no_hit_minor", "welfare", "unspent", "jr", "ejr", "ejr1")),
                            ("REIHE 2 (Budget)", ev.series_budgets, ("jr", "ejr", "ejr1", "unspent", "welfare", "minority_budget")),
                            ("REIHE 3 (Geschlossenheit)", ev.series_cohesion, ("jr", "ejr", "ejr1", "welfare", "unspent", "minority_budget", "no_hit_minor"))):
    rows = fn()
    print(title, rows[0]["runs"], "Instanzen je Zelle")
    for key in key_list:
        print(" ", key)
        for r in ev.series_rows(rows, key):
            print("    ", r)
    print(" ", fn.__name__, "->", {"verdict": None})
print("sec", round(time.time() - t0, 1))
