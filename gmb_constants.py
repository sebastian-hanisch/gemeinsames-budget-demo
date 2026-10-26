"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

RULES = {
    "stimmen": "Gierig nach Zustimmungen",
    "kosten": "Gierig nach Zustimmung je Kosten",
    "anteile": "Gleiche Anteile (Equal Shares)",
    "ergaenzt": "Gleiche Anteile, Rest aufgefüllt",
    "optimal": "Größte Gesamtzustimmung (exakt)",
}
RULE_SHORT = {"stimmen": "Gierig (Zustimmungen)", "kosten": "Gierig (je Kosten)", "anteile": "Gleiche Anteile", "ergaenzt": "Gleiche Anteile + Rest", "optimal": "Größte Gesamtzustimmung"}
RULE_TEXT = {
    "stimmen": "Projekte der Reihe nach nach Zahl der Zustimmungen, bis das Geld nicht mehr reicht; zu teure Projekte werden übersprungen.",
    "kosten": "Wie gierig, aber geordnet nach Zustimmungen je Kosteneinheit (das Verfahren der „guten Rucksackfüllung“).",
    "anteile": "Jeder Wähler bekommt denselben Anteil am Budget. Es wird jeweils das Projekt gekauft, dessen Unterstützer den kleinsten gleichen Beitrag je Kopf zahlen müssen; ihre Anteile sinken entsprechend.",
    "ergaenzt": "Zuerst gleiche Anteile; das übrig gebliebene Budget kauft danach noch Projekte nach Zustimmungen je Kosten, solange sie hineinpassen.",
    "optimal": "Die Projektmenge innerhalb des Budgets mit der größten Summe aller Zustimmungen (Rucksack, exakt gerechnet).",
}
EQUAL_SHARES = "anteile"

# Regler (Prozentwerte als ganze Zahlen, damit die Adresszeile eindeutig bleibt)
N_MIN, N_MAX, DEFAULT_N = 20, 200, 100                 # Wähler
M_MIN, M_MAX, DEFAULT_M = 6, 20, 16                    # Projekte
BUDGET_MIN, BUDGET_MAX, DEFAULT_BUDGET = 10, 60, 30    # Budget in Prozent der Gesamtkosten aller Projekte
GROUP_MIN, GROUP_MAX, DEFAULT_GROUP = 50, 90, 60       # Anteil des größeren Lagers an den Wählern in Prozent
OWN_MIN, OWN_MAX, DEFAULT_OWN = 20, 90, 50             # Zustimmungswahrscheinlichkeit für Projekte des eigenen Lagers in Prozent
CROSS_MIN, CROSS_MAX, DEFAULT_CROSS = 0, 50, 5         # Zustimmungswahrscheinlichkeit für Projekte des anderen Lagers in Prozent
SEED_MAX, DEFAULT_SEED = 9999, 10
COST_MIN, COST_MAX = 1, 5                              # Projektkosten, ganzzahlig gleichverteilt

# Feste Messreihen (unabhängig von den Reglern): nie ein einzelner Zufalls-Seed als Befund
SERIES_SEED = 100000
SERIES_RUNS = 100
SERIES_N, SERIES_M = 100, 16
SERIES_OWN = 50
SERIES_GROUPS = (50, 60, 70, 80, 90)                   # Reihe 1: Anteil des größeren Lagers, Budget 30 %, Fremdzustimmung 5 %
SERIES_CROSS, SERIES_BUDGET = 5, 30                    # feste Werte der übrigen Regler in allen Reihen
SERIES_BUDGETS = (10, 20, 30, 40, 50)                  # Reihe 2: Budget, Lager 60 : 40, Fremdzustimmung 5 %
SERIES_GROUP = 60
SERIES_OWNS = (20, 35, 50, 65, 80)                    # Reihe 3: Geschlossenheit (Zustimmung zu eigenen Projekten), Lager 60 : 40, Budget 30 %, Fremdzustimmung 5 %

COLOR_MAJOR = "#4c78a8"
COLOR_MINOR = "#e8a838"
COLOR_FUNDED = "#2F6B65"
COLOR_ALERT = "#c0392b"
RULE_COLORS = {"stimmen": "#4c78a8", "kosten": "#9aa5b1", "anteile": "#2F6B65", "ergaenzt": "#7fb8a6", "optimal": "#b04a3a"}

PRESETS = {
    "Zwei Lager: gierig oder gleiche Anteile": {"n": 100, "m": 16, "budget": 30, "group": 60, "own": 50, "cross": 5, "seed": 10},
    "Geschlossene Lager (80 : 20)": {"n": 100, "m": 16, "budget": 30, "group": 80, "own": 80, "cross": 2, "seed": 30},
    "Auch gierig je Kosten scheitert": {"n": 100, "m": 16, "budget": 40, "group": 60, "own": 80, "cross": 2, "seed": 9},
    "Knappes Budget": {"n": 100, "m": 16, "budget": 15, "group": 70, "own": 50, "cross": 5, "seed": 10},
    "Keine Lager": {"n": 100, "m": 16, "budget": 30, "group": 60, "own": 40, "cross": 40, "seed": 10},
}
PRESET_HELP = {
    "Zwei Lager: gierig oder gleiche Anteile": "Voreinstellung: 100 Wähler in zwei Lagern (60 : 40), jedes Lager stimmt vor allem den eigenen Projekten zu, das Budget beträgt 30 % der Gesamtkosten. Gierig nach Zustimmungen gibt dem kleineren Lager 0 % der Ausgaben und verletzt die Gerechtfertigte Repräsentation; gleiche Anteile geben ihm 29 %.",
    "Geschlossene Lager (80 : 20)": "Das kleinere Lager hat 20 % der Wähler und stimmt fast nur den eigenen Projekten zu (80 %). Beide gierigen Regeln und sogar die exakte Rucksacklösung lassen es ohne ein Wunschprojekt; gleiche Anteile geben seinen Projekten 18 %, mit aufgefülltem Rest 25 % der Ausgaben.",
    "Auch gierig je Kosten scheitert": "Mit geschlossenen Lagern (80 %) und 40 % Budget geht das kleinere Lager auch bei der kostenbewussten Gierigkeit leer aus (0 % der Ausgaben, JR verletzt); gleiche Anteile geben ihm 36 %.",
    "Knappes Budget": "Nur 15 % der Gesamtkosten stehen zur Verfügung: gierig nach Zustimmungen gibt dem kleineren Lager 0 %, gleiche Anteile 25 %, lassen aber die Hälfte des Budgets liegen.",
    "Keine Lager": "Beide Lager stimmen allen Projekten gleich oft zu (40 %): die Lager unterscheiden sich nur noch in der Größe, und keine der fünf Regeln verletzt die Gerechtfertigte Repräsentation.",
}
