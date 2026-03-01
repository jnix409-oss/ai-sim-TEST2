"""
WorkForward AI — Organizational Restructure Simulator
Streamlit UI layer. All simulation logic lives in /engine.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import time
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from engine import (
    OrgSim, build_baseline, build_reorg,
    summarize, compute_delta, timeseries_df,
    run_monte_carlo_pair,
)

# ─────────────────────────────────────────────
# Page config & global CSS
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="WorkForward AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLORS = {
    "baseline": "#4F8EF7",   # steel blue
    "reorg":    "#F76C4F",   # burnt orange
    "accent":   "#1AE8B0",   # mint
    "dark_bg":  "#0F1117",
    "card_bg":  "#1C1F2A",
    "border":   "#2A2D3E",
    "text":     "#E8EAF0",
    "muted":    "#7B7F96",
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
    background-color: {COLORS['dark_bg']};
    color: {COLORS['text']};
}}

/* Hide Streamlit chrome */
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px; }}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: {COLORS['card_bg']};
    border-right: 1px solid {COLORS['border']};
}}
[data-testid="stSidebar"] .stMarkdown h3 {{
    color: {COLORS['accent']};
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
    margin-top: 1.2rem;
}}

/* Metric cards */
.metric-card {{
    background: {COLORS['card_bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.75rem;
}}
.metric-label {{
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {COLORS['muted']};
    margin-bottom: 0.4rem;
}}
.metric-value {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 2rem;
    font-weight: 600;
    line-height: 1;
}}
.metric-delta-pos {{ color: {COLORS['accent']}; font-size: 0.85rem; }}
.metric-delta-neg {{ color: #F76C4F; font-size: 0.85rem; }}
.metric-delta-neu {{ color: {COLORS['muted']}; font-size: 0.85rem; }}

/* Section headers */
.section-header {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 2rem 0 1rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid {COLORS['border']};
}}
.section-header h2 {{
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0;
    color: {COLORS['text']};
}}
.section-pill {{
    background: {COLORS['border']};
    border-radius: 20px;
    padding: 0.15rem 0.7rem;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {COLORS['muted']};
}}

/* Risk badge */
.risk-badge {{
    display: inline-block;
    padding: 0.3rem 0.9rem;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 0.4rem;
}}
.risk-high {{ background: rgba(247,108,79,0.15); border: 1px solid rgba(247,108,79,0.4); color: #F76C4F; }}
.risk-med  {{ background: rgba(255,193,7,0.12); border: 1px solid rgba(255,193,7,0.35); color: #FFC107; }}
.risk-low  {{ background: rgba(26,232,176,0.12); border: 1px solid rgba(26,232,176,0.35); color: {COLORS['accent']}; }}

/* Scenario badge */
.scenario-badge-baseline {{
    display: inline-block;
    background: rgba(79,142,247,0.15);
    border: 1px solid rgba(79,142,247,0.4);
    color: #4F8EF7;
    border-radius: 6px;
    padding: 0.2rem 0.8rem;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
}}
.scenario-badge-reorg {{
    display: inline-block;
    background: rgba(247,108,79,0.15);
    border: 1px solid rgba(247,108,79,0.4);
    color: #F76C4F;
    border-radius: 6px;
    padding: 0.2rem 0.8rem;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
}}

/* Run button */
div[data-testid="stButton"] button {{
    background: linear-gradient(135deg, #4F8EF7 0%, #2A5FC7 100%);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    font-size: 0.95rem;
    padding: 0.7rem 2rem;
    width: 100%;
    transition: all 0.2s ease;
    letter-spacing: 0.03em;
}}
div[data-testid="stButton"] button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(79,142,247,0.35);
}}

/* Plotly chart containers */
.js-plotly-plot {{ border-radius: 12px; }}

/* Delta table */
.delta-table {{ font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; }}

/* Hero header */
.hero {{
    background: linear-gradient(135deg, {COLORS['card_bg']} 0%, #151829 100%);
    border: 1px solid {COLORS['border']};
    border-radius: 16px;
    padding: 1.6rem 2rem;
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.hero-title {{
    font-size: 1.7rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin: 0;
}}
.hero-sub {{
    color: {COLORS['muted']};
    font-size: 0.88rem;
    margin-top: 0.3rem;
}}
.hero-badge {{
    background: rgba(26,232,176,0.12);
    border: 1px solid rgba(26,232,176,0.3);
    border-radius: 8px;
    padding: 0.5rem 1.1rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: {COLORS['accent']};
    letter-spacing: 0.1em;
    text-transform: uppercase;
    white-space: nowrap;
}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Helper: Plotly theme
# ─────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color=COLORS["text"], size=12),
    xaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
    yaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=COLORS["border"]),
    margin=dict(t=40, b=30, l=10, r=10),
)


def styled_plotly(fig, height=320):
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────
# Sidebar inputs
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ WorkForward AI")
    st.markdown("---")

    st.markdown("### 👥 Workforce")
    num_ics = st.slider("Individual Contributors", 10, 300, 60, 5)
    baseline_mgrs = st.slider("Baseline Managers", 3, 40, 12, 1)
    reorg_mgrs = st.slider("Reorg Managers", 3, 40, 8, 1)

    st.markdown("### 🕐 Simulation")
    steps = st.slider("Simulation Steps (days)", 20, 200, 60, 10)
    seed = st.number_input("Random Seed", 0, 9999, 42, 1)

    st.markdown("### ✅ Approval Dynamics")
    tasks_per_step = st.slider("New Tasks / Step", 5, 200, 80, 5,
                                help="Work arriving each step. Set relative to IC count × capacity for realistic load.")
    approval_rate = st.slider("Approval Rate (%)", 0, 80, 30, 5) / 100
    approval_chain_depth = st.slider("Approval Chain Depth", 1, 3, 1)
    mgr_approval_capacity = st.slider("Mgr Approval Capacity / step", 1.0, 15.0, 5.0, 0.5)
    ic_capacity = st.slider("IC Work Capacity / step", 0.5, 8.0, 2.0, 0.5)

    st.markdown("### 🧠 Engagement Dynamics")
    engagement_sensitivity = st.slider("Engagement Sensitivity", 0.01, 0.15, 0.05, 0.01)
    burnout_sensitivity = st.slider("Burnout Sensitivity", 0.01, 0.15, 0.04, 0.01)
    attrition_base_prob = st.slider("Base Attrition Prob / step", 0.001, 0.02, 0.005, 0.001, format="%.3f")
    change_shock = st.slider("Change Shock (reorg dip)", 0.0, 0.4, 0.10, 0.05)

    st.markdown("### 🎲 Monte Carlo")
    run_mc = st.checkbox("Run Monte Carlo", value=False)
    n_runs = st.slider("Simulation Runs", 50, 500, 100, 50, disabled=not run_mc)

    st.markdown("---")
    run_button = st.button("▶  Run Simulation", use_container_width=True)

# ─────────────────────────────────────────────
# Hero header
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
  <div>
    <p class="hero-title">Organizational Restructure Simulator</p>
    <p class="hero-sub">Agent-based · Queue dynamics · Monte Carlo distributions</p>
  </div>
  <div class="hero-badge">WorkForward AI · MVP</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Run on button press (or first load with defaults)
# ─────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = None

if run_button:
    shared_kwargs = dict(
        num_ics=num_ics,
        steps=steps,
        tasks_per_step=tasks_per_step,
        approval_rate=approval_rate,
        approval_chain_depth=approval_chain_depth,
        mgr_approval_capacity=mgr_approval_capacity,
        ic_capacity=ic_capacity,
        engagement_sensitivity=engagement_sensitivity,
        burnout_sensitivity=burnout_sensitivity,
        attrition_base_prob=attrition_base_prob,
    )

    with st.spinner("Running simulations…"):
        t0 = time.time()

        cfg_b = build_baseline(num_managers=baseline_mgrs, seed=seed, **shared_kwargs)
        cfg_r = build_reorg(num_managers=reorg_mgrs, change_shock=change_shock, seed=seed, **shared_kwargs)

        sim_b = OrgSim(cfg_b)
        history_b = sim_b.run()
        metrics_b = summarize(history_b)

        sim_r = OrgSim(cfg_r)
        history_r = sim_r.run()
        metrics_r = summarize(history_r)

        delta = compute_delta(metrics_b, metrics_r)
        ts_b = timeseries_df(history_b)
        ts_r = timeseries_df(history_r)

        # Monte Carlo
        mc_b = mc_r = risk_summary = None
        if run_mc:
            def b_factory(s):
                return build_baseline(num_managers=baseline_mgrs, seed=s, **shared_kwargs)
            def r_factory(s):
                return build_reorg(num_managers=reorg_mgrs, change_shock=change_shock, seed=s, **shared_kwargs)

            mc_b, mc_r, risk_summary = run_monte_carlo_pair(b_factory, r_factory, n_runs)

        elapsed = time.time() - t0

    st.session_state.results = dict(
        metrics_b=metrics_b, metrics_r=metrics_r,
        delta=delta, ts_b=ts_b, ts_r=ts_r,
        mc_b=mc_b, mc_r=mc_r, risk_summary=risk_summary,
        elapsed=elapsed, run_mc=run_mc,
        baseline_mgrs=baseline_mgrs, reorg_mgrs=reorg_mgrs,
        num_ics=num_ics, steps=steps,
    )

# ─────────────────────────────────────────────
# Display results
# ─────────────────────────────────────────────
if st.session_state.results is None:
    st.info("👈  Configure parameters in the sidebar and click **Run Simulation** to begin.")
    st.stop()

R = st.session_state.results
mb, mr, delta = R["metrics_b"], R["metrics_r"], R["delta"]
ts_b, ts_r = R["ts_b"], R["ts_r"]

# Elapsed badge
st.caption(f"⏱ Computed in {R['elapsed']:.2f}s · {R['steps']} steps · {R['num_ics']} ICs")

# ─────────────────────────────────────────────
# KPI cards — Baseline vs Reorg
# ─────────────────────────────────────────────
def delta_html(val, fmt=".0f", invert=False, suffix=""):
    """Render delta with colour + sign."""
    sign = "+" if val >= 0 else ""
    good = val >= 0 if not invert else val <= 0
    cls = "metric-delta-pos" if good else "metric-delta-neg"
    return f'<span class="{cls}">{sign}{val:{fmt}}{suffix}</span>'


def kpi_card(label, b_val, r_val, delta_val, fmt=".0f", invert=False, suffix="", pct_delta=None):
    d_str = f"{delta_val:+{fmt}}{suffix}"
    if pct_delta is not None:
        d_str += f" ({pct_delta:+.1f}%)"
    good = delta_val >= 0 if not invert else delta_val <= 0
    d_cls = "metric-delta-pos" if good else "metric-delta-neg"

    return f"""
<div class="metric-card">
  <div class="metric-label">{label}</div>
  <div style="display:flex; gap:2rem; align-items:flex-end; flex-wrap:wrap;">
    <div>
      <div style="font-size:0.65rem;color:#7B7F96;margin-bottom:2px;">BASELINE</div>
      <div class="metric-value" style="color:{COLORS['baseline']};">{b_val:{fmt}}{suffix}</div>
    </div>
    <div>
      <div style="font-size:0.65rem;color:#7B7F96;margin-bottom:2px;">REORG</div>
      <div class="metric-value" style="color:{COLORS['reorg']};">{r_val:{fmt}}{suffix}</div>
    </div>
    <div style="padding-bottom:0.3rem;">
      <div style="font-size:0.65rem;color:#7B7F96;margin-bottom:2px;">DELTA</div>
      <div class="{d_cls}" style="font-family:'JetBrains Mono',monospace;font-weight:600;">{d_str}</div>
    </div>
  </div>
</div>"""


st.markdown(f"""
<div class="section-header">
  <h2>📊 Key Performance Metrics</h2>
  <span class="section-pill">Single Run</span>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown(kpi_card(
        "Tasks Completed (Total Productivity)",
        mb.total_tasks_completed, mr.total_tasks_completed, delta.tasks_delta,
        fmt=",d", pct_delta=delta.tasks_pct,
    ), unsafe_allow_html=True)
    st.markdown(kpi_card(
        "Avg Decision Latency (steps)",
        mb.avg_decision_latency, mr.avg_decision_latency, delta.latency_delta,
        fmt=".2f", invert=True,
    ), unsafe_allow_html=True)

with col2:
    st.markdown(kpi_card(
        "Avg Engagement (end of run)",
        mb.final_avg_engagement, mr.final_avg_engagement, delta.engagement_delta,
        fmt=".3f",
    ), unsafe_allow_html=True)
    st.markdown(kpi_card(
        "Avg Burnout (end of run)",
        mb.final_avg_burnout, mr.final_avg_burnout, delta.burnout_delta,
        fmt=".3f", invert=True,
    ), unsafe_allow_html=True)

# Attrition
attr_col, risk_col = st.columns([1, 1])
with attr_col:
    st.markdown(kpi_card(
        "Total Attrition Events",
        mb.total_attrition, mr.total_attrition, delta.attrition_delta,
        fmt="d", invert=True,
    ), unsafe_allow_html=True)

with risk_col:
    flags = delta.risk_flags()
    flag_html = "".join(
        f'<div style="margin:0.25rem 0;font-size:0.82rem;">{f}</div>' for f in flags
    )
    st.markdown(f"""
<div class="metric-card">
  <div class="metric-label">Risk Flags</div>
  <div style="margin-top:0.5rem;">{flag_html}</div>
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Org structure summary
# ─────────────────────────────────────────────
span_b = R["num_ics"] / max(1, R["baseline_mgrs"])
span_r = R["num_ics"] / max(1, R["reorg_mgrs"])

st.markdown(f"""
<div class="metric-card" style="margin-top:0.5rem;">
  <div class="metric-label">Org Structure</div>
  <div style="display:flex;gap:3rem;margin-top:0.5rem;">
    <div>
      <div style="font-size:0.65rem;color:#7B7F96;">BASELINE</div>
      <div style="font-family:'JetBrains Mono',monospace;color:{COLORS['baseline']};">
        {R['baseline_mgrs']} mgrs · {R['num_ics']} ICs · <strong>{span_b:.1f}× span</strong>
      </div>
    </div>
    <div>
      <div style="font-size:0.65rem;color:#7B7F96;">REORG</div>
      <div style="font-family:'JetBrains Mono',monospace;color:{COLORS['reorg']};">
        {R['reorg_mgrs']} mgrs · {R['num_ics']} ICs · <strong>{span_r:.1f}× span</strong>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Time-series charts
# ─────────────────────────────────────────────
st.markdown("""
<div class="section-header">
  <h2>📈 Time-Series Dynamics</h2>
  <span class="section-pill">Over Simulation Steps</span>
</div>
""", unsafe_allow_html=True)

chart_tab1, chart_tab2, chart_tab3, chart_tab4 = st.tabs([
    "🏭 Productivity", "⏳ Decision Latency", "💡 Engagement & Burnout", "🚪 Attrition"
])

with chart_tab1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ts_b["step"], y=ts_b["tasks_completed"],
        name="Baseline", line=dict(color=COLORS["baseline"], width=2.5),
        fill="tozeroy", fillcolor=f"rgba(79,142,247,0.08)",
    ))
    fig.add_trace(go.Scatter(
        x=ts_r["step"], y=ts_r["tasks_completed"],
        name="Reorg", line=dict(color=COLORS["reorg"], width=2.5),
        fill="tozeroy", fillcolor=f"rgba(247,108,79,0.08)",
    ))
    fig.update_layout(title="Tasks Completed per Step", xaxis_title="Step", yaxis_title="Tasks")
    styled_plotly(fig)

with chart_tab2:
    col_a, col_b = st.columns(2)
    with col_a:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ts_b["step"], y=ts_b["decision_latency"],
                                  name="Baseline", line=dict(color=COLORS["baseline"], width=2.5)))
        fig.add_trace(go.Scatter(x=ts_r["step"], y=ts_r["decision_latency"],
                                  name="Reorg", line=dict(color=COLORS["reorg"], width=2.5)))
        fig.update_layout(title="Avg Decision Latency", xaxis_title="Step", yaxis_title="Steps in queue")
        styled_plotly(fig)

    with col_b:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ts_b["step"], y=ts_b["tasks_blocked"],
                                  name="Baseline", line=dict(color=COLORS["baseline"], width=2.5),
                                  fill="tozeroy", fillcolor="rgba(79,142,247,0.08)"))
        fig.add_trace(go.Scatter(x=ts_r["step"], y=ts_r["tasks_blocked"],
                                  name="Reorg", line=dict(color=COLORS["reorg"], width=2.5),
                                  fill="tozeroy", fillcolor="rgba(247,108,79,0.08)"))
        fig.update_layout(title="Approval Queue Backlog", xaxis_title="Step", yaxis_title="Tasks blocked")
        styled_plotly(fig)

with chart_tab3:
    fig = go.Figure()
    # Engagement
    fig.add_trace(go.Scatter(x=ts_b["step"], y=ts_b["avg_engagement"],
                              name="Baseline Engagement", line=dict(color=COLORS["baseline"], width=2.5)))
    fig.add_trace(go.Scatter(x=ts_r["step"], y=ts_r["avg_engagement"],
                              name="Reorg Engagement", line=dict(color=COLORS["reorg"], width=2.5)))
    # Burnout (dashed)
    fig.add_trace(go.Scatter(x=ts_b["step"], y=ts_b["avg_burnout"],
                              name="Baseline Burnout", line=dict(color=COLORS["baseline"], width=1.8, dash="dot")))
    fig.add_trace(go.Scatter(x=ts_r["step"], y=ts_r["avg_burnout"],
                              name="Reorg Burnout", line=dict(color=COLORS["reorg"], width=1.8, dash="dot")))
    fig.update_layout(title="Engagement (solid) & Burnout (dotted)",
                       xaxis_title="Step", yaxis_title="Index (0–1)",
                       yaxis=dict(range=[0, 1.05]))
    styled_plotly(fig, height=360)

with chart_tab4:
    col_a, col_b = st.columns(2)
    with col_a:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=ts_b["step"], y=ts_b["attrition_events"],
                              name="Baseline", marker_color=COLORS["baseline"], opacity=0.85))
        fig.add_trace(go.Bar(x=ts_r["step"], y=ts_r["attrition_events"],
                              name="Reorg", marker_color=COLORS["reorg"], opacity=0.85))
        fig.update_layout(title="Attrition Events per Step", barmode="overlay",
                           xaxis_title="Step", yaxis_title="Exits")
        styled_plotly(fig)

    with col_b:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ts_b["step"], y=ts_b["active_ics"],
                                  name="Baseline ICs", line=dict(color=COLORS["baseline"], width=2.5)))
        fig.add_trace(go.Scatter(x=ts_r["step"], y=ts_r["active_ics"],
                                  name="Reorg ICs", line=dict(color=COLORS["reorg"], width=2.5)))
        fig.update_layout(title="Active IC Headcount Over Time", xaxis_title="Step", yaxis_title="Active ICs")
        styled_plotly(fig)

# ─────────────────────────────────────────────
# Comparison bar charts
# ─────────────────────────────────────────────
st.markdown("""
<div class="section-header">
  <h2>📊 Scenario Comparison</h2>
  <span class="section-pill">Baseline vs Reorg</span>
</div>
""", unsafe_allow_html=True)

comp_cols = st.columns(2)

metrics_labels = ["Tasks Completed", "Avg Latency", "Avg Engagement", "Avg Burnout", "Attrition Events"]
b_vals = [mb.total_tasks_completed, mb.avg_decision_latency, mb.final_avg_engagement, mb.final_avg_burnout, mb.total_attrition]
r_vals = [mr.total_tasks_completed, mr.avg_decision_latency, mr.final_avg_engagement, mr.final_avg_burnout, mr.total_attrition]

with comp_cols[0]:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Tasks Completed"], y=[mb.total_tasks_completed],
                          name="Baseline", marker_color=COLORS["baseline"],
                          text=[f"{mb.total_tasks_completed:,}"], textposition="outside"))
    fig.add_trace(go.Bar(x=["Tasks Completed"], y=[mr.total_tasks_completed],
                          name="Reorg", marker_color=COLORS["reorg"],
                          text=[f"{mr.total_tasks_completed:,}"], textposition="outside"))
    fig.update_layout(title="Total Productivity", barmode="group", showlegend=True,
                       yaxis_title="Tasks")
    styled_plotly(fig, height=280)

with comp_cols[1]:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Latency", "Burnout", "Attrition"],
                          y=[mb.avg_decision_latency, mb.final_avg_burnout, mb.total_attrition],
                          name="Baseline", marker_color=COLORS["baseline"]))
    fig.add_trace(go.Bar(x=["Latency", "Burnout", "Attrition"],
                          y=[mr.avg_decision_latency, mr.final_avg_burnout, mr.total_attrition],
                          name="Reorg", marker_color=COLORS["reorg"]))
    fig.update_layout(title="Risk Indicators", barmode="group")
    styled_plotly(fig, height=280)

# ─────────────────────────────────────────────
# Delta table
# ─────────────────────────────────────────────
st.markdown("""
<div class="section-header">
  <h2>🔢 Delta Summary Table</h2>
  <span class="section-pill">Reorg − Baseline</span>
</div>
""", unsafe_allow_html=True)

df_delta = pd.DataFrame({
    "Metric": ["Tasks Completed", "Avg Decision Latency", "Avg Engagement", "Avg Burnout", "Total Attrition"],
    "Baseline": [
        f"{mb.total_tasks_completed:,}",
        f"{mb.avg_decision_latency:.3f}",
        f"{mb.final_avg_engagement:.3f}",
        f"{mb.final_avg_burnout:.3f}",
        str(mb.total_attrition),
    ],
    "Reorg": [
        f"{mr.total_tasks_completed:,}",
        f"{mr.avg_decision_latency:.3f}",
        f"{mr.final_avg_engagement:.3f}",
        f"{mr.final_avg_burnout:.3f}",
        str(mr.total_attrition),
    ],
    "Delta": [
        f"{delta.tasks_delta:+,} ({delta.tasks_pct:+.1f}%)",
        f"{delta.latency_delta:+.3f} ({delta.latency_pct:+.1f}%)",
        f"{delta.engagement_delta:+.3f}",
        f"{delta.burnout_delta:+.3f}",
        f"{delta.attrition_delta:+d}",
    ],
    "Direction": ["↑ better" if delta.tasks_delta >= 0 else "↓ worse",
                   "↑ better" if delta.latency_delta <= 0 else "↓ worse",
                   "↑ better" if delta.engagement_delta >= 0 else "↓ worse",
                   "↑ better" if delta.burnout_delta <= 0 else "↓ worse",
                   "↑ better" if delta.attrition_delta <= 0 else "↓ worse"],
})

st.dataframe(
    df_delta,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Metric": st.column_config.TextColumn(width="medium"),
        "Direction": st.column_config.TextColumn(width="small"),
    }
)

# ─────────────────────────────────────────────
# Monte Carlo section
# ─────────────────────────────────────────────
if R["run_mc"] and R["mc_b"] is not None:
    mc_b, mc_r, rs = R["mc_b"], R["mc_r"], R["risk_summary"]

    st.markdown(f"""
<div class="section-header">
  <h2>🎲 Monte Carlo Analysis</h2>
  <span class="section-pill">{rs['n_runs']} Runs · P10 / P50 / P90</span>
</div>
""", unsafe_allow_html=True)

    # Risk scores
    r1, r2, r3, r4 = st.columns(4)
    def risk_cls(p):
        return "risk-high" if p > 0.5 else ("risk-med" if p > 0.25 else "risk-low")

    r1.markdown(f"""<div class="metric-card"><div class="metric-label">Prob. Productivity Drop >10%</div>
<div class="risk-badge {risk_cls(rs['productivity_drop_10pct_prob'])}">{rs['productivity_drop_10pct_prob']:.0%}</div></div>""", unsafe_allow_html=True)
    r2.markdown(f"""<div class="metric-card"><div class="metric-label">Prob. Productivity Drop >5%</div>
<div class="risk-badge {risk_cls(rs['productivity_drop_5pct_prob'])}">{rs['productivity_drop_5pct_prob']:.0%}</div></div>""", unsafe_allow_html=True)
    r3.markdown(f"""<div class="metric-card"><div class="metric-label">Prob. Burnout Increases</div>
<div class="risk-badge {risk_cls(rs['burnout_increase_prob'])}">{rs['burnout_increase_prob']:.0%}</div></div>""", unsafe_allow_html=True)
    r4.markdown(f"""<div class="metric-card"><div class="metric-label">Prob. Attrition Increases</div>
<div class="risk-badge {risk_cls(rs['attrition_increase_prob'])}">{rs['attrition_increase_prob']:.0%}</div></div>""", unsafe_allow_html=True)

    # Distribution charts
    mc_tab1, mc_tab2, mc_tab3, mc_tab4 = st.tabs([
        "🏭 Productivity Dist.", "⏳ Latency Dist.", "💡 Engagement Dist.", "🔥 Burnout Dist."
    ])

    def dist_fig(arr_b, arr_r, label, unit=""):
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=arr_b, name="Baseline", nbinsx=25,
            marker_color=COLORS["baseline"], opacity=0.65,
        ))
        fig.add_trace(go.Histogram(
            x=arr_r, name="Reorg", nbinsx=25,
            marker_color=COLORS["reorg"], opacity=0.65,
        ))
        # P50 lines
        fig.add_vline(x=float(np.median(arr_b)), line=dict(color=COLORS["baseline"], dash="dash", width=2),
                       annotation_text=f"B·P50 {np.median(arr_b):.1f}", annotation_position="top left")
        fig.add_vline(x=float(np.median(arr_r)), line=dict(color=COLORS["reorg"], dash="dash", width=2),
                       annotation_text=f"R·P50 {np.median(arr_r):.1f}", annotation_position="top right")
        fig.update_layout(barmode="overlay", title=f"{label} Distribution ({rs['n_runs']} runs)",
                           xaxis_title=unit, yaxis_title="Count")
        return fig

    with mc_tab1:
        styled_plotly(dist_fig(rs["_tasks_b"], rs["_tasks_r"], "Tasks Completed", "Tasks"), height=350)

    with mc_tab2:
        styled_plotly(dist_fig(rs["_latency_b"], rs["_latency_r"], "Decision Latency", "Steps"), height=350)

    with mc_tab3:
        styled_plotly(dist_fig(rs["_eng_b"], rs["_eng_r"], "Avg Engagement", "Index"), height=350)

    with mc_tab4:
        styled_plotly(dist_fig(rs["_burn_b"], rs["_burn_r"], "Avg Burnout", "Index"), height=350)

    # Percentile table
    st.markdown("#### 📋 Percentile Summary Table")
    df_mc = pd.DataFrame({
        "Metric": ["Tasks Completed", "Decision Latency", "Engagement", "Burnout", "Attrition"],
        "Baseline P10": [f"{mc_b.tasks_p10:,.0f}", f"{mc_b.latency_p10:.2f}", f"{mc_b.engagement_p10:.3f}", f"{mc_b.burnout_p10:.3f}", f"{mc_b.attrition_p10:.0f}"],
        "Baseline P50": [f"{mc_b.tasks_p50:,.0f}", f"{mc_b.latency_p50:.2f}", f"{mc_b.engagement_p50:.3f}", f"{mc_b.burnout_p50:.3f}", f"{mc_b.attrition_p50:.0f}"],
        "Baseline P90": [f"{mc_b.tasks_p90:,.0f}", f"{mc_b.latency_p90:.2f}", f"{mc_b.engagement_p90:.3f}", f"{mc_b.burnout_p90:.3f}", f"{mc_b.attrition_p90:.0f}"],
        "Reorg P10": [f"{mc_r.tasks_p10:,.0f}", f"{mc_r.latency_p10:.2f}", f"{mc_r.engagement_p10:.3f}", f"{mc_r.burnout_p10:.3f}", f"{mc_r.attrition_p10:.0f}"],
        "Reorg P50": [f"{mc_r.tasks_p50:,.0f}", f"{mc_r.latency_p50:.2f}", f"{mc_r.engagement_p50:.3f}", f"{mc_r.burnout_p50:.3f}", f"{mc_r.attrition_p50:.0f}"],
        "Reorg P90": [f"{mc_r.tasks_p90:,.0f}", f"{mc_r.latency_p90:.2f}", f"{mc_r.engagement_p90:.3f}", f"{mc_r.burnout_p90:.3f}", f"{mc_r.attrition_p90:.0f}"],
    })
    st.dataframe(df_mc, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f'<p style="color:{COLORS["muted"]};font-size:0.75rem;text-align:center;">'
    'WorkForward AI · Organizational Restructure Simulator · MVP · '
    'Engine: agent-based + queue dynamics · '
    '<a href="https://github.com" style="color:{COLORS[\'accent\']};">GitHub</a>'
    '</p>',
    unsafe_allow_html=True,
)
