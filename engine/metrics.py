"""
WorkForward AI — Metrics Module
Summarizes simulation history into scalar metrics and computes deltas.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from .model import StepSnapshot


@dataclass
class ScenarioMetrics:
    """Aggregated scalar metrics for one scenario run."""
    total_tasks_completed: int
    avg_decision_latency: float
    final_avg_engagement: float
    final_avg_burnout: float
    total_attrition: int
    # Optional distribution stats (for Monte Carlo)
    tasks_p10: Optional[float] = None
    tasks_p50: Optional[float] = None
    tasks_p90: Optional[float] = None
    latency_p10: Optional[float] = None
    latency_p50: Optional[float] = None
    latency_p90: Optional[float] = None
    engagement_p10: Optional[float] = None
    engagement_p50: Optional[float] = None
    engagement_p90: Optional[float] = None
    burnout_p10: Optional[float] = None
    burnout_p50: Optional[float] = None
    burnout_p90: Optional[float] = None
    attrition_p10: Optional[float] = None
    attrition_p50: Optional[float] = None
    attrition_p90: Optional[float] = None


def summarize(history: list[StepSnapshot]) -> ScenarioMetrics:
    """Collapse a simulation run into scalar metrics."""
    if not history:
        return ScenarioMetrics(0, 0, 0, 0, 0)

    total_tasks = sum(s.tasks_completed for s in history)
    latencies = [s.decision_latency for s in history if s.decision_latency > 0]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    last = history[-1]
    # Take mean engagement/burnout over final 10% of run for stability
    tail = max(1, len(history) // 10)
    tail_snaps = history[-tail:]
    final_eng = sum(s.avg_engagement for s in tail_snaps) / len(tail_snaps)
    final_burn = sum(s.avg_burnout for s in tail_snaps) / len(tail_snaps)
    total_attrition = sum(s.attrition_events for s in history)

    return ScenarioMetrics(
        total_tasks_completed=total_tasks,
        avg_decision_latency=avg_latency,
        final_avg_engagement=final_eng,
        final_avg_burnout=final_burn,
        total_attrition=total_attrition,
    )


@dataclass
class MetricsDelta:
    """Reorg minus Baseline for each metric."""
    tasks_delta: int
    tasks_pct: float
    latency_delta: float
    latency_pct: float
    engagement_delta: float
    burnout_delta: float
    attrition_delta: int

    def risk_flags(self) -> list[str]:
        """Return human-readable risk signals."""
        flags = []
        if self.tasks_pct < -5:
            flags.append(f"⚠️  Productivity down {abs(self.tasks_pct):.1f}%")
        if self.latency_delta > 1:
            flags.append(f"⚠️  Decision latency increased by {self.latency_delta:.1f} steps")
        if self.burnout_delta > 0.05:
            flags.append(f"⚠️  Burnout index up {self.burnout_delta:.2f}")
        if self.attrition_delta > 2:
            flags.append(f"⚠️  {self.attrition_delta} additional attrition events")
        if not flags:
            flags.append("✅  No major risk flags detected")
        return flags


def compute_delta(baseline: ScenarioMetrics, reorg: ScenarioMetrics) -> MetricsDelta:
    """Compute reorg − baseline deltas."""
    tasks_delta = reorg.total_tasks_completed - baseline.total_tasks_completed
    tasks_pct = (tasks_delta / max(1, baseline.total_tasks_completed)) * 100

    lat_b = baseline.avg_decision_latency
    lat_r = reorg.avg_decision_latency
    latency_delta = lat_r - lat_b
    latency_pct = ((latency_delta) / max(0.01, lat_b)) * 100 if lat_b else 0.0

    return MetricsDelta(
        tasks_delta=tasks_delta,
        tasks_pct=tasks_pct,
        latency_delta=latency_delta,
        latency_pct=latency_pct,
        engagement_delta=reorg.final_avg_engagement - baseline.final_avg_engagement,
        burnout_delta=reorg.final_avg_burnout - baseline.final_avg_burnout,
        attrition_delta=reorg.total_attrition - baseline.total_attrition,
    )


def timeseries_df(history: list[StepSnapshot]):
    """Convert snapshot list to a dict of lists for easy Plotly consumption."""
    return {
        "step": [s.step for s in history],
        "tasks_completed": [s.tasks_completed for s in history],
        "tasks_blocked": [s.tasks_blocked for s in history],
        "decision_latency": [s.decision_latency for s in history],
        "avg_engagement": [s.avg_engagement for s in history],
        "avg_burnout": [s.avg_burnout for s in history],
        "attrition_events": [s.attrition_events for s in history],
        "active_ics": [s.active_ics for s in history],
    }
