# Gemeinsames Budget: Methode gleicher Anteile – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-gemeinsames-budget-demo.streamlit.app/)** -->

Stück der Linie **Abstimmen und Fair Teilen** (Konzepte-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“). Verwandt: [wahlregeln-demo](https://github.com/sebastian-hanisch/wahlregeln-demo) (ein Sieger statt eines Budgets), [taktisch-waehlen-demo](https://github.com/sebastian-hanisch/taktisch-waehlen-demo) und [wahlaxiome-demo](https://github.com/sebastian-hanisch/wahlaxiome-demo) (dort geht es um Eigenschaften von Regeln und ihre Gegenbeispiele) sowie `projektauswahl-demo` (Auswahl mit Voraussetzungen, aber ohne Wählergruppen).
Die Demo fragt: **Ein Verband hat einen Investitionstopf, die Mitglieder stimmen Projekten mit Kosten zu, das Geld reicht nicht für alle – wer bekommt etwas, und was kostet es, wenn man berechtigten Gruppen etwas garantiert?** Verglichen werden fünf Regeln auf denselben Zufallsinstanzen mit zwei Lagern: zwei gierige Regeln, die **Methode gleicher Anteile** (Equal Shares), dieselbe Methode mit aufgefülltem Rest und die exakte Rucksacklösung mit der größten Gesamtzustimmung.
Dazu kommt eine **exakte Prüfung der Gruppenansprüche**: für jede Wählergruppe und jede Projektmenge, die sie mit ihrem Anteil am Budget bezahlen könnte und der sie geschlossen zustimmt, wird geprüft, ob die Auswahl ihr etwas gibt.

Der Kern ist eigener Code (`numpy`): die fünf Regeln, die Kennzahlen und die Prüfung der Gruppenansprüche. Ein unabhängiges Orakel in den Tests rechnet die Methode gleicher Anteile mit exakten Brüchen, die Rucksacklösung durch Aufzählung und die Gruppenansprüche durch Aufzählung aller Gruppen.

## Warum dieses Problem

Die naheliegende Regel kauft die **beliebtesten** Projekte, bis das Budget aufgebraucht ist. Hat ein Lager die Mehrheit, kommen die Lieblingsprojekte des anderen Lagers nie dran, obwohl dessen Wähler einen Teil des Geldes mitgebracht haben. Die Demo zeigt, **wie schlimm das ist** (in den Standardinstanzen bekommt das kleinere Lager im Mittel 5 % der Ausgaben, seine Wähler stellen 40 %), und trennt es von einem zweiten, **weniger bekannten Befund**: schon eine **kostenbewusste** gierige Regel (Zustimmungen je Kosteneinheit) behebt das in diesem Modell fast vollständig. Die Methode gleicher Anteile ist dann nicht „besser im Mittel“, sondern **die Regel mit einer Garantie**: sie verletzt die Gruppenansprüche in keiner der 1 500 gemessenen Instanzen, die kostenbewusste Gierigkeit und die exakte Rucksacklösung dagegen in einzelnen (siehe Befunde).
Der Preis ist sichtbar: die reine Methode gleicher Anteile lässt in diesem Modell **26 bis 75 % des Budgets liegen** und erreicht nur etwa 40 bis 84 % der größtmöglichen Zustimmungen; mit aufgefülltem Rest sind es 97 bis 99 %, ohne dass die Garantie verloren geht.

## Modell

**Instanz.** n Wähler in zwei Lagern (der Anteil des größeren Lagers ist ein Regler), m Projekte mit ganzzahligen Kosten 1 bis 5 (gleichverteilt), Budget = Anteil der Gesamtkosten, gerundet, mindestens 1. Die letzten m ÷ 2 Projekte gehören dem kleineren Lager. Jeder Wähler stimmt jedem Projekt des **eigenen** Lagers mit Wahrscheinlichkeit „eigene Zustimmung“ zu, jedem Projekt des **anderen** Lagers mit „fremder Zustimmung“; der Nutzen eines Wählers ist die Zahl der finanzierten Projekte, denen er zustimmt.
**Regeln.** *Gierig nach Zustimmungen:* Projekte nach Zahl der Zustimmungen, kaufen, wenn es noch ins Budget passt. *Gierig je Kosten:* nach Zustimmungen je Kosteneinheit. *Gleiche Anteile:* jeder Wähler bekommt Budget / n; ein Projekt kostet ρ je Unterstützer, wobei ρ der kleinste Beitrag ist, bei dem die Unterstützer zusammen die Kosten aufbringen (wer weniger Restgeld hat, zahlt sein Restgeld); gekauft wird das Projekt mit dem kleinsten ρ, bis keines mehr bezahlbar ist. *Gleiche Anteile, Rest aufgefüllt:* danach kaufen die verbliebenen Mittel noch Projekte nach Zustimmungen je Kosten. *Größte Gesamtzustimmung:* die Summe aller Zustimmungen ist größtmöglich (Rucksack, exakt). Gleichstände entscheidet der kleinere Projektindex.
**Gruppenansprüche.** Eine Gruppe S und eine Projektmenge T sind **berechtigt**, wenn alle in S allen Projekten in T zustimmen und |S| · Budget ≥ n · Kosten(T) gilt. **JR** (gerechtfertigte Repräsentation): in jeder berechtigten (S, T) hat mindestens ein Mitglied ein finanziertes Projekt, dem es zustimmt. **EJR** (erweitert): mindestens eines hat |T| davon. **EJR bis auf ein Projekt:** mindestens eines hat |T| − 1 davon (so **in dieser Demo definiert**, siehe Grenzen).
Formeln und Lesehilfe stehen im 📐-Expander der App.

## Methodik

- **Kern** (`gmb_algorithm.py`): die fünf Regeln, Kennzahlen (`evaluate`), die Gruppenprüfung (`group_violations`, Tiefensuche über die Projektmengen; Zweige, deren Unterstützer schon für sich nicht reichen, entfallen, weil weitere Projekte die Kosten erhöhen und die Unterstützer verringern, die Prüfung ist trotzdem **exakt**).
- **Szenario und Auswertung** (`gmb_scenario.py`, `gmb_evaluation.py`): Instanz aus Einstellungen und Zufalls-Seed, Tabelle je Regel, Beispiele für verletzte Ansprüche in Worten, drei Messreihen mit festem Programm (je Zelle 100 Instanzen, Zufalls-Seeds 100000 bis 100099), alle Verdikte als reine Funktionen.
- **Oberfläche** (`app.py`): fünf Schnellstart-Szenarien, sechs Regler und der Zufalls-Seed, Ergebnis (Tabelle, zwei Balkendiagramme, welche Regel welches Projekt kauft), Kernfrage mit Verdikt, drei Reiter mit Messreihen, Annahmen und Formeln.

## Befunde (gemessen, keine Behauptungen)

Die Presets sind einzelne Instanzen und deshalb exakt. Die Messreihen sind Mittel über je 100 Instanzen (100 Wähler, 16 Projekte). **Die Zufallszahlen eines `numpy`-Generators sind nicht über Versionen stabil**: die Tests prüfen für die Reihen deshalb Bänder um diese Zahlen (±8 Prozentpunkte bei Mittelwerten, ±12 bei Anteilen von Instanzen); Nullen und „nie“-Aussagen sind in den festen Läufen exakt.

| Frage | Befund | Test |
|---|---|---|
| Stimmt der Kern? | Gleiche Anteile gleich einer **exakten Bruchrechnung** (150 kleine Instanzen), Rucksacklösung gleich der **Aufzählung aller Projektmengen** (150), beide gierigen Regeln gleich einer Sortierung mit exakten Brüchen (100), JR, EJR und EJR bis auf eins gleich der **Aufzählung aller Gruppen und Projektmengen** (120 Instanzen, alle fünf Regeln), jedes gemeldete Beispiel stimmt (berechtigte Gruppengröße, zu wenig finanziert, 120). Handrechnungen mit Rechnung im Kommentar. | `test_oracle_gemeinsames_budget.py`, `test_algorithm.py` |
| Standardfall (60 : 40, 30 % Budget, Zufalls-Seed 10) | Anteil der Ausgaben für Projekte des kleineren Lagers: gierig nach Zustimmungen **0 %**, gierig je Kosten 38 %, **gleiche Anteile 29 %**, mit Rest 38 %, Rucksack 47 %. JR verletzt nur bei gierig nach Zustimmungen (78 % der Wähler des kleineren Lagers ohne Treffer, bei gleichen Anteilen 22 %). Gleiche Anteile geben 7 von 15 Einheiten aus (67 % der größtmöglichen Zustimmungen), mit Rest 13 von 15 (98 %). | `test_claims.py::test_default_preset` |
| Wo scheitert auch die kostenbewusste Gierigkeit? | Bei **geschlossenen Lagern** (80 % Zustimmung zu eigenen Projekten, 20 % Wähler im kleineren Lager, Zufalls-Seed 30): gierig nach Zustimmungen, gierig je Kosten **und die exakte Rucksacklösung** geben dem kleineren Lager 0 % der Ausgaben (JR verletzt, 90 bis 95 % seiner Wähler ohne Treffer); gleiche Anteile 18 %, mit Rest 25 %, **kein** Wähler des kleineren Lagers ohne Treffer. Mit 60 : 40 und 40 % Budget (Zufalls-Seed 9) scheitern beide gierigen Regeln. | `test_claims.py::test_closed_camps_preset_where_even_the_exact_rucksack_leaves_the_minority_out`, `…::test_preset_where_the_cost_aware_greedy_fails_too` |
| Wie viel Budget bekommt das kleinere Lager (Reihe 1, Mittel)? | Bei 60 : 40: gierig nach Zustimmungen **5 %**, gierig je Kosten 37 %, gleiche Anteile **39 %**, Rucksack 32 % (seine Wähler: 40 %). Bei 80 : 20: 3 %, 17 %, 15 %. Bei **90 : 10: 3 %, 12 %, gleiche Anteile nur 4 %**, mit Rest 13 % (seine Wähler: 10 %). | `test_claims.py::test_series_groups_minority_budget` |
| Warum bekommt ein kleines Lager so wenig? | Ein Anspruch besteht nur für Gruppen, die ein Projekt **geschlossen** unterstützen und mit ihrem Anteil bezahlen können. Bei 90 : 10 und 50 % Zustimmung zu den eigenen Projekten stimmt von zehn Wählern jeweils nur etwa die Hälfte einem Projekt zu: keine Gruppe ist berechtigt, und die reine Methode gleicher Anteile lässt **63 %** der Wähler des kleineren Lagers ohne Treffer (gierig je Kosten 34 %, mit aufgefülltem Rest 31 %). | `test_claims.py::test_series_groups_voters_without_a_hit` |
| Wie oft verletzt eine Regel die gerechtfertigte Repräsentation? | **Gierig nach Zustimmungen** in 13 % (50 : 50), 59 % (60 : 40), **64 %** (70 : 30), 34 % (80 : 20), 3 % (90 : 10) der Instanzen; über das Budget (10 bis 50 %) 22 bis 66 %. **Gierig je Kosten** in 0 bis 3 %, die **exakte Rucksacklösung** in 0 bis 7 %. **Gleiche Anteile und gleiche Anteile mit Rest in keiner der 1 500 Instanzen** der drei Reihen (JR, EJR und EJR bis auf eins). | `test_claims.py::test_greedy_by_votes_violates_jr_often_at_uneven_camps`, `…::test_equal_shares_never_violate_the_group_properties_in_any_series`, `…::test_series_budgets` |
| Wie hängt es von der Geschlossenheit ab (Reihe 3)? | Bei wachsender Zustimmung zu den eigenen Projekten (20 bis 80 %) verletzt gierig nach Zustimmungen EJR in **10, 36, 61, 75, 83 %** der Instanzen und EJR bis auf eins in 0, 0, 0, 9, **34 %**. Gierig je Kosten verletzt EJR höchstens in 1 %, die Rucksacklösung höchstens in 4 %; **EJR bis auf eins** verletzt außer gierig nach Zustimmungen **keine** Regel in einer der 1 500 Instanzen. | `test_claims.py::test_series_cohesion`, `…::test_ejr1_is_only_violated_by_greedy_by_votes` |
| Was kostet die Garantie? | Die reine Methode gleicher Anteile gibt **26 bis 75 %** des Budgets nicht aus (bei 10 % Budget 69 %, bei 50 % Budget 35 %; mit zunehmender Geschlossenheit weniger) und erreicht 40 bis 84 % der größtmöglichen Zustimmungen (Standard: 71 %). Mit aufgefülltem Rest bleiben 2 bis 8 % ungenutzt, die Zustimmungen liegen bei **97 bis 99 %** des Möglichen, die Garantie bleibt. Die kostenbewusste Gierigkeit erreicht ebenfalls 97 bis 99 %. | `test_claims.py::test_equal_shares_leave_budget_unspent_and_lose_approvals`, `…::test_series_budgets`, `…::test_series_cohesion` |
| Schnellstart-Szenarien | Standardfall, geschlossene Lager (80 : 20), „auch gierig je Kosten scheitert“ (60 : 40, 40 % Budget), knappes Budget (15 %: gierig nach Zustimmungen 0 %, gleiche Anteile 25 %, die Hälfte des Budgets bleibt liegen), keine Lager (alle Regeln erfüllen JR). | `test_claims.py::test_the_presets_tell_the_stories_in_their_help_texts`, `…::test_tight_budget_preset`, `…::test_no_camps_preset_violates_nothing` |

## Ehrliche Grenzen

- **Zwei Lager, unabhängige Zustimmungen im Lager.** Echte Zustimmungen sind selten so glatt; berechtigte Gruppen entstehen in diesem Modell nur, wenn die Zustimmung zu den eigenen Projekten hoch ist (Reihe 3). Die Anteile gelten für dieses Modell, nicht für echte Beteiligungsdaten. Ein Nutzen proportional zu den Kosten oder kardinale Bewertungen sind nicht abgebildet.
- **Die Definitionen sind unsere, die Prüfung ist exakt.** JR und EJR sind hier für Gruppen mit gemeinsam zugestimmten Projekten und dem Budgetanteil der Gruppe als Berechtigung geprüft. **„EJR bis auf ein Projekt“ ist in dieser Demo als „mindestens |T| − 1“ festgelegt**; die Quelle (Peters, Pierczyński, Skowron, NeurIPS 2021; nur der Abstract gelesen) formuliert die Garantie für additive Nutzen anders. Dass die Methode gleicher Anteile hier nie verletzt, ist ein **Befund in 1 500 Instanzen** und in 200 kleinen Zufallsinstanzen, kein Beweis.
- **Gleiche Anteile geben nicht das ganze Budget aus.** Das Auffüllen ist hier ein einfacher Rucksackschritt nach Zustimmungen je Kosten, nicht die in der Literatur beschriebene Variante (Erhöhung des Budgets je Wähler, bis das Geld ausgegeben ist).
- **Die Rucksacklösung ist exakt, aber nicht eindeutig.** Bei gleicher Gesamtzustimmung wird eine feste Lösung gewählt (siehe Kern); andere gleichwertige Lösungen können Gruppenansprüche anders treffen.
- **Eine Stichprobe von 100 Instanzen je Zelle.** Kleine Unterschiede zwischen Regeln sind kein Befund; die Bänder in den Tests sind entsprechend weit.
- **Ehrliche Zustimmung.** Wer die Zählregel kennt, kann strategisch zustimmen; hier stimmen alle nach Wahrscheinlichkeit, nicht nach Kalkül.
- **Literatur** (aus Abstracts, nicht im Original geprüft): Peters, Pierczyński, Skowron, *Proportional Participatory Budgeting with Additive Utilities*, NeurIPS 2021.

## Befunde und Korrekturen gegenüber dem Plan

- **Port:** 9192 (9170 bis 9191 sind vergeben).
- **Fünf statt zwei Regeln.** Der Plan nannte „gierig gegen gleiche Anteile“. Die Messung zeigte, dass die gierige Regel nach Zustimmungen ein **schwacher Gegner** ist: schon die kostenbewusste Gierigkeit verteilt das Budget fast so gerecht wie gleiche Anteile. Deshalb stehen beide gierigen Regeln da, dazu die exakte Rucksacklösung, und der Unterschied wird dort gesucht, wo er liegt: **in der Garantie** (JR, EJR), nicht im Mittel.
- **Die Vormessung hatte die Kosten der Garantie verschwiegen.** Dort stand „Gesamtzustimmung nur −3 %“; das war gegen die gierige Regel nach Zustimmungen. **Gegen das Optimum** erreicht die reine Methode gleicher Anteile 40 bis 84 %, und sie lässt in der Regel 26 bis 75 % des Budgets liegen; die Regel „gleiche Anteile mit Rest“ ist deshalb neu.
- **Vormessung (200 Wähler, 20 Projekte):** 2,3 % gegen 38,7 % der Ausgaben für das kleinere Lager. Die App (100 Wähler, 16 Projekte) misst 5 % gegen 39 %.
- **„Kein Wunschprojekt“ umgerechnet:** der Plan nannte 24,2 % gegen 7,1 % aller Wähler. Die App zählt nur Wähler mit mindestens einer Zustimmung und weist die Zahl für das kleinere Lager getrennt aus (Standard: 78 % gegen 22 %).
- **Das Lager 90 : 10 zeigt keinen Vorteil für gleiche Anteile** (4 % gegen 12 % bei gierig je Kosten): sein Anspruch besteht nur bei hoher Geschlossenheit. Deshalb steht dort kein Schnellstart, sondern ein Satz in den Befunden; das Preset „Geschlossene Lager (80 : 20)“ zeigt den Fall, in dem der Anspruch greift.
- **Reglerspanne:** Wähler 20 bis 200, Projekte 6 bis 20, Budget 10 bis 60 %, größeres Lager 50 bis 90 %, Zustimmung zu eigenen 20 bis 90 %, zu fremden 0 bis 50 %.

## Verifikation

- **Kern:** jede Regel und jede Prüfung an Mini-Instanzen von Hand (gierig überspringt, was nicht passt; Gleichstand zum kleineren Index; gleiche Anteile an der Instanz mit zwei Lagern, ρ-Berechnung, Auffüllen; Rucksack mit Rekonstruktion; Gruppenansprüche an der Schwelle, bei Gleichheit berechtigt; kleinste Projektmenge zuerst).
- **Orakel:** exakte Bruchrechnung für gleiche Anteile, Aufzählung aller Projektmengen für den Rucksack, exakte Sortierung für beide gierigen Regeln, Aufzählung aller Gruppen und Projektmengen für JR, EJR und EJR bis auf eins (mit Nichtleere-Prüfung des Orakels), Prüfung jedes gemeldeten Beispiels, Auffüllen kauft nur dazu, gleiche Anteile verletzen JR nie auf zufälligen Instanzen.
- **Verdikte:** reine Funktionen, jeder Zweig und jede Zahl im Text an handgesetzten Werten (`tests/test_verdicts.py`), Randfälle an den Reglergrenzen (`tests/test_edge_cases.py`).
- **Presets, Layout, Oberfläche:** wie in allen Demos (Presets vollständig und im Regelbereich, keines auf einem Reglerrand, kein Preset entsteht durch Änderung eines einzigen Reglers, Schnellstart oben, aktives Preset hervorgehoben, AppTest jeder Button und jeder Regler an den Rändern, Footer, Laufzeit-Importe).
- **Mutationsprüfung** (`tools/mutate_demo.py`): 71 Stellen im Kern `gmb_algorithm.py`, **65 gefangen**, **6 als äquivalent festgehalten**, keine Zeitüberschreitung. Der erste Lauf ließ 8 überleben: zwei trafen eine überflüssige Absicherung in `evaluate` (die Indexierung mit einer leeren Liste ist in `numpy` zulässig), die entfernt wurde; sechs sind äquivalent: `<` statt `<=` an den beiden Toleranzgrenzen für ρ (die Grenze ist ein einzelner Gleitkommawert, vor dem schon die Toleranz 1e-12 steht), `<` statt `<=` beim Vergleich zweier Beispiele (jede Projektmenge wird nur einmal besucht), die Vorprüfung „das Geld der Unterstützer reicht“ in `equal_shares` (`_contribution` verwirft denselben Fall mit `None`, zwei Mutanten) und eine überzählige Zeile der Rucksacktabelle.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `gmb_algorithm.py` | Kern: fünf Regeln, Kennzahlen, Prüfung der Gruppenansprüche |
| `gmb_constants.py` | Regler-Grenzen, feste Pläne, Farben, Presets |
| `gmb_evaluation.py` | Analyse einer Instanz, Tabelle, Beispiele in Worten, Messreihen, Verdikte |
| `gmb_layout.py` | Fester Kopf (Stylesheet) |
| `gmb_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `gmb_scenario.py` | Instanz mit zwei Lagern |
| `gmb_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `messen.py` | Einmalige Messung der Zahlen in dieser README (nicht Teil der App) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Mini-Instanzen, Kern, Orakel, Verdikte, Randfälle, Presets, Abbildungen, Layout, AppTest, Footer, Laufzeit-Importe, Claims |

## Bewusst nicht umgesetzt

- **Mehrere Sieger statt eines Budgets** (Komitee-Wahl mit Proportionalität): ein anderes Problem mit gleichen Kosten je Projekt.
- **Nutzen proportional zu den Kosten, kardinale Bewertungen, Projekte mit mehreren Ausprägungen:** die Zustimmung zählt hier 0 oder 1.
- **Echte Beteiligungsdaten** (etwa aus Pabulib): die Demo zeigt das Verfahren am Zufallsmodell, nicht den Alltag einer Bürgerbeteiligung.
- **Das Auffüllen aus der Literatur** (Erhöhung des Budgets je Wähler, bis das Geld ausgegeben ist): hier nur ein einfacher Rucksackschritt.
- **Strategisches Zustimmen:** die Zustimmungen sind ehrlich.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
