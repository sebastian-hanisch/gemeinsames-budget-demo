"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import gmb_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_projects(a):
    """Oben: Zustimmungen je Projekt, getrennt nach Lagern; unten: welche Regel welches Projekt finanziert (dunkel = finanziert)."""
    inst = a.inst
    names = [f"P{p + 1} · {int(inst.costs[p])}" for p in range(inst.m)]
    major = inst.approvals[inst.group == 0].sum(axis=0)
    minor = inst.approvals[inst.group == 1].sum(axis=0)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.55, 0.45], vertical_spacing=0.06)
    fig.add_trace(go.Bar(x=names, y=major, name="Zustimmungen größeres Lager", marker_color=C.COLOR_MAJOR, hovertemplate="%{x}: %{y} Zustimmungen<extra>größeres Lager</extra>"), row=1, col=1)
    fig.add_trace(go.Bar(x=names, y=minor, name="Zustimmungen kleineres Lager", marker_color=C.COLOR_MINOR, hovertemplate="%{x}: %{y} Zustimmungen<extra>kleineres Lager</extra>"), row=1, col=1)
    fig.update_layout(barmode="stack")
    rules = list(C.RULES)
    z = [[1 if p in a.outcomes[rule].chosen else 0 for p in range(inst.m)] for rule in rules]
    fig.add_trace(go.Heatmap(z=z, x=names, y=[C.RULE_SHORT[r] for r in rules], colorscale=[[0, "rgba(128,128,128,0.12)"], [1, C.COLOR_FUNDED]], showscale=False, xgap=2, ygap=2,
                             hovertemplate="%{y}: %{x} – %{z:d} (1 = finanziert)<extra></extra>"), row=2, col=1)
    fig.update_yaxes(title_text="Zustimmungen", row=1, col=1)
    fig.update_yaxes(autorange="reversed", row=2, col=1)
    fig.update_xaxes(tickangle=-45, title_text="Projekt · Kosten", row=2, col=1)
    return _base(fig, height=520)


def build_comparison(a):
    """Zwei Balkengruppen je Regel: Anteil der Ausgaben für Projekte des kleineren Lagers (mit dem Anteil seiner Wähler als Linie) und Wähler ohne finanziertes Wunschprojekt im kleineren Lager."""
    rules = list(C.RULES)
    names = [C.RULE_SHORT[r] for r in rules]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Ausgaben für Projekte des kleineren Lagers", "Wähler des kleineren Lagers ohne finanziertes Wunschprojekt"), horizontal_spacing=0.12)
    mb = [a.outcomes[r].minority_budget or 0.0 for r in rules]
    fig.add_trace(go.Bar(x=names, y=mb, marker_color=[C.RULE_COLORS[r] for r in rules], text=[f"{100 * v:.0f} %" for v in mb], textposition="outside", showlegend=False,
                         hovertemplate="%{x}: %{y:.1%}<extra></extra>"), row=1, col=1)
    fig.add_hline(y=a.minority_share, line_dash="dash", line_color=C.COLOR_ALERT, annotation_text=f"Anteil der Wähler {100 * a.minority_share:.0f} %", annotation_position="top left", row=1, col=1)
    nh = [0.0 if a.outcomes[r].no_hit_minor != a.outcomes[r].no_hit_minor else a.outcomes[r].no_hit_minor for r in rules]
    fig.add_trace(go.Bar(x=names, y=nh, marker_color=[C.RULE_COLORS[r] for r in rules], text=[f"{100 * v:.0f} %" for v in nh], textposition="outside", showlegend=False,
                         hovertemplate="%{x}: %{y:.1%}<extra></extra>"), row=1, col=2)
    fig.update_yaxes(range=[0, 1.15], tickformat=".0%")
    fig.update_xaxes(tickangle=-25)
    return _base(fig, height=380)


AXIS_TITLES = {"group": "Anteil des größeren Lagers an den Wählern (%)", "budget": "Budget (% der Gesamtkosten)", "own": "Zustimmung zu den eigenen Projekten (%)"}


def build_series(rows, key, ytitle, ymax=1.05):
    """Eine Linie je Regel über den Reglerwerten der Reihe; key: minority_budget, jr, ejr, ejr1, welfare, unspent, no_hit_minor."""
    fig = go.Figure()
    for rule in C.RULES:
        pts = [r for r in rows if r["rule"] == rule]
        fig.add_trace(go.Scatter(x=[r["x"] for r in pts], y=[r[key] for r in pts], mode="lines+markers", name=C.RULE_SHORT[rule], line=dict(color=C.RULE_COLORS[rule], width=2),
                                 hovertemplate="%{x}: %{y:.1%}<extra>" + C.RULE_SHORT[rule] + "</extra>"))
    if key == "minority_budget" and rows[0]["param"] == "group":      # Bezug: der Anteil der Wähler des kleineren Lagers
        xs = list(dict.fromkeys(r["x"] for r in rows))
        fig.add_trace(go.Scatter(x=xs, y=[(100 - x) / 100 for x in xs], mode="lines", name="Anteil der Wähler des kleineren Lagers", line=dict(color=C.COLOR_ALERT, width=1.5, dash="dash"),
                                 hovertemplate="%{x}: %{y:.0%}<extra>Anteil der Wähler</extra>"))
    fig.update_xaxes(title_text=AXIS_TITLES[rows[0]["param"]], type="category")
    fig.update_yaxes(title_text=ytitle, range=[0, ymax], tickformat=".0%")
    return _base(fig, height=340)
