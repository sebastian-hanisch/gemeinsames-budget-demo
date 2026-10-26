"""Gemeinsames Budget: Methode gleicher Anteile - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück der Linie „Abstimmen und Fair Teilen“: Mitglieder stimmen Projekten mit Kosten zu, ein Budget reicht nicht für alle. Fünf Regeln (zwei gierige, gleiche Anteile,
gleiche Anteile mit aufgefülltem Rest, größte Gesamtzustimmung) werden verglichen; geprüft wird, ob berechtigte Gruppen leer ausgehen. Der Kern liegt in gmb_algorithm.py.

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import gmb_constants as C
import gmb_evaluation as ev
from gmb_evaluation import Settings, analyse, num, pct, rule_rows, series_rows, verdict_budgets, verdict_cohesion, verdict_groups, verdict_state, witness_lines
from gmb_layout import dunkles_design, kopf_css
from gmb_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from gmb_visualization import build_comparison, build_projects, build_series

st.set_page_config(page_title="Gemeinsames Budget – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _series_groups():
    return ev.series_groups()


@st.cache_data(show_spinner=False)
def _series_budgets():
    return ev.series_budgets()


@st.cache_data(show_spinner=False)
def _series_cohesion():
    return ev.series_cohesion()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in gmb_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("💶 Gemeinsames Budget: wer bekommt wie viel?")
st.markdown(
    """
Ein Verband hat einen **Investitionstopf**, die Mitglieder stimmen Projekten zu (Zustimmungsstimmen), und jedes Projekt kostet etwas: das Geld reicht nicht für alle.
Die naheliegende Regel kauft die **beliebtesten** Projekte, bis das Budget aufgebraucht ist. Wenn aber ein Lager die Mehrheit hat, sind die Lieblingsprojekte des anderen Lagers nie dabei, **obwohl dessen Wähler einen Teil des Budgets „mitgebracht“ haben**.
Die **Methode gleicher Anteile** (Equal Shares) gibt jedem Wähler denselben Anteil am Budget und lässt jedes Projekt von seinen Unterstützern bezahlen; sie schützt **berechtigte Gruppen**: eine Gruppe, die ein Projekt mit ihrem Anteil bezahlen könnte und ihm geschlossen zustimmt, geht nicht leer aus.
Die Demo vergleicht **fünf Regeln** auf denselben Zufallsinstanzen (zwei Lager, Kosten 1 bis 5) und **prüft die Gruppenansprüche exakt** (alle Gruppen, alle Projektmengen), statt sie nur zu behaupten.
Verwandt: `projektauswahl-demo` (Auswahl mit Voraussetzungen, ohne Wählergruppen), `wahlregeln-demo` (ein Sieger statt eines Budgets).

Weiter unten: der Abschnitt **🔬 Messreihen**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So wird gerechnet", expanded=True):
    st.markdown(
        """
1. **Instanz:** zwei Lager (die letzten Projekte gehören dem kleineren Lager, die übrigen dem größeren). Jeder Wähler stimmt den Projekten des **eigenen** Lagers mit der eingestellten Wahrscheinlichkeit zu, denen des **anderen** Lagers mit der kleineren. Kosten 1 bis 5, ganzzahlig; das Budget ist ein Anteil der Gesamtkosten.
2. **Gierig nach Zustimmungen** kauft die Projekte der Reihe nach nach Zahl der Zustimmungen; **gierig je Kosten** nach Zustimmungen je Kosteneinheit; **größte Gesamtzustimmung** ist die exakte Rucksacklösung.
3. **Gleiche Anteile:** jeder Wähler bekommt Budget geteilt durch Wählerzahl. Ein Projekt kostet ρ je Unterstützer, wenn alle den gleichen Beitrag ρ zahlen (wer weniger Geld hat, zahlt sein Restgeld). Gekauft wird das Projekt mit dem **kleinsten ρ**; danach ist das Geld seiner Unterstützer entsprechend gesunken. Das wiederholt sich, bis kein Projekt mehr bezahlbar ist. **Mit aufgefülltem Rest** kauft das übrige Budget danach noch Projekte nach Zustimmungen je Kosten.
4. **Gruppenansprüche:** eine Gruppe von Wählern ist **berechtigt** zu einer Projektmenge T, wenn alle ihr zustimmen und ihr Anteil am Budget die Kosten von T deckt. JR: mindestens ein Mitglied hat ein finanziertes Projekt nach seinem Geschmack. EJR: mindestens eines hat |T| davon. EJR bis auf ein Projekt: mindestens eines hat |T| − 1.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    n = st.slider("Wähler", *bounds("n_slider"), key="n_slider", help="Zahl der abstimmenden Mitglieder.")
    m = st.slider("Projekte", *bounds("m_slider"), key="m_slider", help="Zahl der Projekte; die letzte Hälfte gehört dem kleineren Lager, Kosten 1 bis 5.")
    budget = st.slider("Budget (% der Gesamtkosten)", *bounds("budget_slider"), key="budget_slider", help="Wie viel Prozent der Kosten aller Projekte zusammen zur Verfügung stehen.")
    group = st.slider("Größeres Lager (% der Wähler)", *bounds("group_slider"), key="group_slider", help="Bei 50 sind beide Lager gleich groß.")
    own = st.slider("Zustimmung zu eigenen Projekten (%)", *bounds("own_slider"), key="own_slider", help="Wahrscheinlichkeit, mit der ein Wähler einem Projekt seines Lagers zustimmt (je höher, desto geschlossener das Lager).")
    cross = st.slider("Zustimmung zu fremden Projekten (%)", *bounds("cross_slider"), key="cross_slider", help="Wahrscheinlichkeit für Projekte des anderen Lagers. Gleich der Zustimmung zu eigenen Projekten: es gibt keine Lager mehr.")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz ziehen", width="stretch", on_click=randomize_seed)

sync_query_params({"n_slider": int(n), "m_slider": int(m), "budget_slider": int(budget), "group_slider": int(group), "own_slider": int(own), "cross_slider": int(cross), "seed_input": int(seed)})

settings = Settings(n=int(n), m=int(m), budget=int(budget), group=int(group), own=int(own), cross=int(cross), seed=int(seed))
with st.spinner("Rechne die fünf Regeln und prüfe alle Gruppen …"):
    a = _analysis(settings)
inst = a.inst

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
m1, m2, m3 = st.columns(3)
m1.metric("Budget", f"{inst.budget} von {int(inst.costs.sum())}", delta=f"{settings.budget} % der Gesamtkosten", delta_color="off")
m2.metric("Wähler je Lager", f"{int((inst.group == 0).sum())} : {int((inst.group == 1).sum())}", delta=f"{pct(a.minority_share)} im kleineren Lager", delta_color="off")
m3.metric("Größte Gesamtzustimmung", f"{a.optimum}", delta=f"{len(a.outcomes['optimal'].chosen)} Projekte", delta_color="off")
st.table(rule_rows(a))
st.plotly_chart(build_comparison(a), width="stretch", key="comparison_chart")
st.markdown("**Welche Projekte welche Regel kauft** (Spalten: Projekt · Kosten; unten dunkel = finanziert)")
st.plotly_chart(build_projects(a), width="stretch", key="projects_chart")
lines = witness_lines(a)
if lines:
    st.markdown("**Beispiele für verletzte Gruppenansprüche**")
    for line in lines:
        st.markdown("- " + line)

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wer bekommt etwas, und was kostet der Schutz?")
kind, text = verdict_state(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Messreihen ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Messreihen")
st.caption(f"Feste Programme, unabhängig von den Reglern ({C.SERIES_N} Wähler, {C.SERIES_M} Projekte). Jede Reihe rechnet auf Klick in einigen Sekunden; je Zelle {C.SERIES_RUNS} Instanzen mit den Zufalls-Seeds {C.SERIES_SEED} bis {C.SERIES_SEED + C.SERIES_RUNS - 1}.")
tab1, tab2, tab3 = st.tabs(["Wie groß ist das kleinere Lager?", "Wie groß ist das Budget?", "Wie geschlossen sind die Lager?"])
with tab1:
    st.markdown(f"**Anteil der Ausgaben für das kleinere Lager** bei wachsendem Größenunterschied (Budget {C.SERIES_BUDGET} %, Zustimmung eigene {C.SERIES_OWN} %, fremde {C.SERIES_CROSS} %).")
    if st.button("Reihe rechnen", key="groups_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe (einige Sekunden) …"):
            _series_groups()
        st.session_state["groups_done"] = time.perf_counter() - t0
    if "groups_done" in st.session_state:
        rows = _series_groups()
        st.plotly_chart(build_series(rows, "minority_budget", "Ausgaben für Projekte des kleineren Lagers"), width="stretch", key="groups_chart")
        st.plotly_chart(build_series(rows, "no_hit_minor", "Wähler des kleineren Lagers ohne Treffer"), width="stretch", key="groups_nohit_chart")
        st.table(series_rows(rows, "minority_budget"))
        kind, text = verdict_groups(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['groups_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")
with tab2:
    st.markdown(f"**Wie oft ist die Gerechtfertigte Repräsentation (JR) verletzt?** Anteil der Instanzen bei wachsendem Budget (Lager {C.SERIES_GROUP} : {100 - C.SERIES_GROUP}, Zustimmung eigene {C.SERIES_OWN} %, fremde {C.SERIES_CROSS} %).")
    if st.button("Reihe rechnen", key="budgets_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe (einige Sekunden) …"):
            _series_budgets()
        st.session_state["budgets_done"] = time.perf_counter() - t0
    if "budgets_done" in st.session_state:
        rows = _series_budgets()
        st.plotly_chart(build_series(rows, "jr", "Anteil der Instanzen mit verletzter JR"), width="stretch", key="budgets_jr_chart")
        st.plotly_chart(build_series(rows, "unspent", "nicht ausgegebenes Budget"), width="stretch", key="budgets_unspent_chart")
        st.table(series_rows(rows, "jr"))
        kind, text = verdict_budgets(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['budgets_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")
with tab3:
    st.markdown(f"**Je geschlossener ein Lager, desto mehr kann eine Gruppe beanspruchen.** Anteil der Instanzen mit verletztem EJR (Lager {C.SERIES_GROUP} : {100 - C.SERIES_GROUP}, Budget {C.SERIES_BUDGET} %, Fremdzustimmung {C.SERIES_CROSS} %).")
    if st.button("Reihe rechnen", key="cohesion_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe (einige Sekunden) …"):
            _series_cohesion()
        st.session_state["cohesion_done"] = time.perf_counter() - t0
    if "cohesion_done" in st.session_state:
        rows = _series_cohesion()
        st.plotly_chart(build_series(rows, "ejr", "Anteil der Instanzen mit verletztem EJR"), width="stretch", key="cohesion_ejr_chart")
        st.plotly_chart(build_series(rows, "welfare", "Zustimmungen im Verhältnis zum Größtmöglichen", ymax=1.1), width="stretch", key="cohesion_welfare_chart")
        st.table(series_rows(rows, "ejr"))
        kind, text = verdict_cohesion(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['cohesion_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Zwei Lager, unabhängige Zustimmungen im Lager** | Echte Zustimmungen sind selten so glatt; Gruppen mit gemeinsamen Projekten entstehen hier nur, wenn die Zustimmung zu eigenen Projekten hoch ist. Die Anteile in den Messreihen gelten für dieses Modell. | diese Demo (Regler und Messreihe 3) |
| **Zustimmung zählt als Nutzen, jedes Projekt gleich viel** | Ein Projekt für 5 Einheiten zählt wie eines für 1. Mit Nutzen proportional zu den Kosten würden die Regeln anders ordnen. | diese Demo |
| **Gleiche Anteile geben nicht das ganze Budget aus** | Je nach Lage bleibt ein großer Teil liegen (Reihe 2 zeigt es). Deshalb steht die Regel mit aufgefülltem Rest daneben; das Auffüllen ist hier ein einfacher Rucksackschritt, nicht die in der Literatur beschriebene Variante. | diese Demo |
| **Die Prüfung ist exakt, die Definition ist unsere** | JR und EJR werden hier für Gruppen mit gemeinsam zugestimmten Projekten geprüft, mit dem Budgetanteil der Gruppe als Berechtigung. „EJR bis auf ein Projekt“ ist in dieser Demo als „Zahl der Projekte in T minus eins“ festgelegt, nicht als die Definition der Quelle. | diese Demo (Definitionen im Kern) |
| **Eine Stichprobe von 100 Instanzen je Zelle** | Die Anteile der Reihen sind Mittel über 100 Instanzen; kleine Unterschiede zwischen Regeln sind kein Befund. | diese Demo (Messreihen) |
| **Ehrliche Zustimmung** | Wer weiß, wie gezählt wird, kann strategisch zustimmen; hier stimmen alle nach Wahrscheinlichkeit, nicht nach Kalkül. | `taktisch-waehlen-demo` (für Wahlen) |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Instanz.** $n$ Wähler, $m$ Projekte mit Kosten $c_j \in \{1,\dots,5\}$, Budget $B$; $A_i \subseteq \{1,\dots,m\}$ sind die Projekte, denen Wähler $i$ zustimmt. Eine Auswahl $W$ muss $\sum_{j \in W} c_j \le B$ erfüllen; der Nutzen von Wähler $i$ ist $u_i(W) = |A_i \cap W|$.

**Größte Gesamtzustimmung.** $\max_W \sum_i u_i(W)$ unter der Budgetgrenze, ein Rucksackproblem; mit ganzzahligen Kosten exakt per dynamischer Optimierung über die Budgetwerte $0, \dots, B$.

**Gleiche Anteile.** Jeder Wähler startet mit $b_i = B/n$. In jeder Runde ist für ein nicht gekauftes Projekt $j$ mit Unterstützern $N_j = \{i : j \in A_i\}$ der Beitrag $\rho_j$ die kleinste Zahl mit $\sum_{i \in N_j} \min(b_i, \rho_j) \ge c_j$ (falls $\sum_{i\in N_j} b_i \ge c_j$). Gekauft wird das Projekt mit dem kleinsten $\rho_j$ (Gleichstand: kleinster Index), und $b_i \leftarrow \max(b_i - \rho_j, 0)$ für alle $i \in N_j$.

**Berechtigte Gruppen.** Eine Gruppe $S$ und eine Projektmenge $T \subseteq \bigcap_{i \in S} A_i$ sind berechtigt, wenn $|S| \cdot B \ge n \cdot c(T)$. Eine Auswahl $W$ erfüllt
- **JR**, wenn in jeder berechtigten $(S, T)$ mit $T \ne \emptyset$ ein $i \in S$ mit $u_i(W) \ge 1$ existiert,
- **EJR**, wenn dort ein $i \in S$ mit $u_i(W) \ge |T|$ existiert,
- **EJR bis auf ein Projekt** (Festlegung dieser Demo), wenn dort ein $i \in S$ mit $u_i(W) \ge |T| - 1$ existiert.

**Prüfung.** Für festes $T$ ist die gefährdetste Gruppe $\{i : T \subseteq A_i,\ u_i(W) < \text{Forderung}\}$; es genügt, alle $T$ aufzuzählen. Zweige, in denen die Unterstützer von $T$ schon für sich $|N_T| \cdot B < n \cdot c(T)$ erreichen, entfallen, weil weitere Projekte die Kosten erhöhen und die Unterstützer verringern.

**Literatur** (aus Abstracts, nicht im Original geprüft): Peters, Pierczyński, Skowron, *Proportional Participatory Budgeting with Additive Utilities*, NeurIPS 2021: die Methode gleicher Anteile erfüllt erweiterte gerechtfertigte Repräsentation bis auf ein Projekt bei additiven Nutzen und rechnet in polynomialer Zeit; Pabulib sammelt reale Abstimmungsdaten zu gemeinsamen Budgets.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
