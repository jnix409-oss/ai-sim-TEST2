"""
WorkForward AI — Monte Carlo Engine
Runs N simulations with varied seeds and aggregates distributions.
"""

from __future__ import annotations
import numpy as np
from typing import Callable
from .model import SimConfig, OrgSim
from .metrics import ScenarioMetrics, summarize


def _percentile(arr: list[float], p: float) -> float:
    return float(np.percentile(arr, p))


def run_monte_carlo(
    cfg_factory: Callable[[int], SimConfig],
    n_runs: int = 100,
) -> ScenarioMetrics:
    """
    Run `n_runs` simulations, each with a different seed.
    Returns a ScenarioMetrics with p10/p50/p90 populated.

    cfg_factory: callable that receives seed (int) → SimConfig
    """
    tasks_list: list[float] = []
    latency_list: list[float] = []
    engagement_list: list[float] = []
    burnout_list: list[float] = []
    attrition_list: list[float] = []

    for seed in range(n_runs):
        cfg = cfg_factory(seed)
        sim = OrgSim(cfg)
        history = sim.run()
        m = summarize(history)
        tasks_list.append(m.total_tasks_completed)
        latency_list.append(m.avg_decision_latency)
        engagement_list.append(m.final_avg_engagement)
        burnout_list.append(m.final_avg_burnout)
        attrition_list.append(m.total_attrition)

    return ScenarioMetrics(
        total_tasks_completed=int(_percentile(tasks_list, 50)),
        avg_decision_latency=_percentile(latency_list, 50),
        final_avg_engagement=_percentile(engagement_list, 50),
        final_avg_burnout=_percentile(burnout_list, 50),
        total_attrition=int(_percentile(attrition_list, 50)),
        tasks_p10=_percentile(tasks_list, 10),
        tasks_p50=_percentile(tasks_list, 50),
        tasks_p90=_percentile(tasks_list, 90),
        latency_p10=_percentile(latency_list, 10),
        latency_p50=_percentile(latency_list, 50),
        latency_p90=_percentile(latency_list, 90),
        engagement_p10=_percentile(engagement_list, 10),
        engagement_p50=_percentile(engagement_list, 50),
        engagement_p90=_percentile(engagement_list, 90),
        burnout_p10=_percentile(burnout_list, 10),
        burnout_p50=_percentile(burnout_list, 50),
        burnout_p90=_percentile(burnout_list, 90),
        attrition_p10=_percentile(attrition_list, 10),
        attrition_p50=_percentile(attrition_list, 50),
        attrition_p90=_percentile(attrition_list, 90),
    )


def mc_risk_score(
    baseline_tasks_list: list[float],
    reorg_tasks_list: list[float],
    threshold_pct: float = 0.10,
) -> float:
    """
    Probability that reorg productivity drops > threshold_pct vs baseline median.
    """
    baseline_median = float(np.median(baseline_tasks_list))
    drop_threshold = baseline_median * (1 - threshold_pct)
    n_drops = sum(1 for t in reorg_tasks_list if t < drop_threshold)
    return n_drops / max(1, len(reorg_tasks_list))


def run_monte_carlo_pair(
    baseline_factory: Callable[[int], SimConfig],
    reorg_factory: Callable[[int], SimConfig],
    n_runs: int = 100,
) -> tuple[ScenarioMetrics, ScenarioMetrics, dict]:
    """
    Run matched Monte Carlo for both scenarios (same seeds).
    Returns (baseline_mc, reorg_mc, risk_summary).
    """
    tasks_b: list[float] = []
    latency_b: list[float] = []
    eng_b: list[float] = []
    burn_b: list[float] = []
    attr_b: list[float] = []

    tasks_r: list[float] = []
    latency_r: list[float] = []
    eng_r: list[float] = []
    burn_r: list[float] = []
    attr_r: list[float] = []

    for seed in range(n_runs):
        # Baseline
        cfg_b = baseline_factory(seed)
        sim_b = OrgSim(cfg_b)
        m_b = summarize(sim_b.run())
        tasks_b.append(m_b.total_tasks_completed)
        latency_b.append(m_b.avg_decision_latency)
        eng_b.append(m_b.final_avg_engagement)
        burn_b.append(m_b.final_avg_burnout)
        attr_b.append(m_b.total_attrition)

        # Reorg
        cfg_r = reorg_factory(seed)
        sim_r = OrgSim(cfg_r)
        m_r = summarize(sim_r.run())
        tasks_r.append(m_r.total_tasks_completed)
        latency_r.append(m_r.avg_decision_latency)
        eng_r.append(m_r.final_avg_engagement)
        burn_r.append(m_r.final_avg_burnout)
        attr_r.append(m_r.total_attrition)

    def pcts(lst: list[float]) -> ScenarioMetrics:
        return ScenarioMetrics(
            total_tasks_completed=int(_percentile(lst, 50)),
            avg_decision_latency=0,
            final_avg_engagement=0,
            final_avg_burnout=0,
            total_attrition=0,
        )

    baseline_mc = ScenarioMetrics(
        total_tasks_completed=int(_percentile(tasks_b, 50)),
        avg_decision_latency=_percentile(latency_b, 50),
        final_avg_engagement=_percentile(eng_b, 50),
        final_avg_burnout=_percentile(burn_b, 50),
        total_attrition=int(_percentile(attr_b, 50)),
        tasks_p10=_percentile(tasks_b, 10), tasks_p50=_percentile(tasks_b, 50), tasks_p90=_percentile(tasks_b, 90),
        latency_p10=_percentile(latency_b, 10), latency_p50=_percentile(latency_b, 50), latency_p90=_percentile(latency_b, 90),
        engagement_p10=_percentile(eng_b, 10), engagement_p50=_percentile(eng_b, 50), engagement_p90=_percentile(eng_b, 90),
        burnout_p10=_percentile(burn_b, 10), burnout_p50=_percentile(burn_b, 50), burnout_p90=_percentile(burn_b, 90),
        attrition_p10=_percentile(attr_b, 10), attrition_p50=_percentile(attr_b, 50), attrition_p90=_percentile(attr_b, 90),
    )

    reorg_mc = ScenarioMetrics(
        total_tasks_completed=int(_percentile(tasks_r, 50)),
        avg_decision_latency=_percentile(latency_r, 50),
        final_avg_engagement=_percentile(eng_r, 50),
        final_avg_burnout=_percentile(burn_r, 50),
        total_attrition=int(_percentile(attr_r, 50)),
        tasks_p10=_percentile(tasks_r, 10), tasks_p50=_percentile(tasks_r, 50), tasks_p90=_percentile(tasks_r, 90),
        latency_p10=_percentile(latency_r, 10), latency_p50=_percentile(latency_r, 50), latency_p90=_percentile(latency_r, 90),
        engagement_p10=_percentile(eng_r, 10), engagement_p50=_percentile(eng_r, 50), engagement_p90=_percentile(eng_r, 90),
        burnout_p10=_percentile(burn_r, 10), burnout_p50=_percentile(burn_r, 50), burnout_p90=_percentile(burn_r, 90),
        attrition_p10=_percentile(attr_r, 10), attrition_p50=_percentile(attr_r, 50), attrition_p90=_percentile(attr_r, 90),
    )

    risk_summary = {
        "productivity_drop_10pct_prob": mc_risk_score(tasks_b, tasks_r, 0.10),
        "productivity_drop_5pct_prob": mc_risk_score(tasks_b, tasks_r, 0.05),
        "burnout_increase_prob": sum(1 for b, r in zip(burn_b, burn_r) if r > b) / n_runs,
        "attrition_increase_prob": sum(1 for b, r in zip(attr_b, attr_r) if r > b) / n_runs,
        "n_runs": n_runs,
        # Raw arrays for distribution charts
        "_tasks_b": tasks_b,
        "_tasks_r": tasks_r,
        "_latency_b": latency_b,
        "_latency_r": latency_r,
        "_eng_b": eng_b,
        "_eng_r": eng_r,
        "_burn_b": burn_b,
        "_burn_r": burn_r,
        "_attr_b": attr_b,
        "_attr_r": attr_r,
    }

    return baseline_mc, reorg_mc, risk_summary
