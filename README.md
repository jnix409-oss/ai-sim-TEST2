# WorkForward AI — Organizational Restructure Simulator

> Agent-based · Queue dynamics · Monte Carlo distributions  
> A consulting-grade simulation tool for HR / Org Design / COO teams.

## What it does

Simulates the impact of an organizational restructure across four key dimensions:

| Dimension | Metric |
|---|---|
| 🏭 Productivity | Total tasks completed |
| ⏳ Decision Speed | Avg approval queue latency |
| 💡 People Health | Engagement & burnout indices |
| 🚪 Retention Risk | Probabilistic attrition events |

## Architecture

```
/app.py               ← Streamlit UI (no simulation logic)
/engine/
  __init__.py
  model.py            ← Person, OrgSim, StepSnapshot (pure Python)
  scenarios.py        ← build_baseline(), build_reorg()
  metrics.py          ← summarize(), compute_delta(), timeseries_df()
  monte_carlo.py      ← run_monte_carlo_pair()
/requirements.txt
```

## Simulation model

- **Agents**: Individual Contributors (ICs) + Managers
- **Tasks**: Arrive each step; a configurable fraction needs manager approval
- **Approval queue**: Tasks wait until manager capacity processes them → latency
- **Wellbeing**: Engagement/burnout update based on workload ratio, blocking, and span-of-control
- **Attrition**: Probabilistic each step; rises with high burnout + low engagement
- **Change shock**: Optional engagement dip applied at reorg start

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo → set `app.py` as entry point
4. Click Deploy

## Key inputs

| Parameter | Range | Default |
|---|---|---|
| Individual Contributors | 10–300 | 60 |
| Baseline Managers | 3–40 | 12 |
| Reorg Managers | 3–40 | 8 |
| Simulation Steps | 20–200 | 60 |
| Approval Rate | 0–80% | 30% |
| Change Shock | 0–0.4 | 0.10 |
| Monte Carlo Runs | 50–500 | 100 |

## Monte Carlo outputs

- P10 / P50 / P90 distributions for all metrics
- Risk scores: P(productivity drops >5% or >10%), P(burnout increases), P(attrition increases)
- Overlaid histograms: Baseline vs Reorg distributions

---

Built with ❤️ by WorkForward AI · Streamlit + Plotly + Pure Python engine
