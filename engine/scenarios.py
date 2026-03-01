"""
WorkForward AI — Scenario Builders
Constructs baseline and reorg SimConfig objects from UI parameters.
"""

from .model import SimConfig


def build_baseline(
    num_ics: int,
    num_managers: int,
    steps: int,
    tasks_per_step: int = 80,
    approval_rate: float = 0.30,
    approval_chain_depth: int = 1,
    mgr_approval_capacity: float = 5.0,
    ic_capacity: float = 2.0,
    engagement_sensitivity: float = 0.05,
    burnout_sensitivity: float = 0.04,
    attrition_base_prob: float = 0.005,
    seed: int = 42,
) -> SimConfig:
    """Baseline scenario — pre-restructure org."""
    return SimConfig(
        num_ics=num_ics,
        num_managers=num_managers,
        steps=steps,
        tasks_per_step=tasks_per_step,
        approval_rate=approval_rate,
        approval_chain_depth=approval_chain_depth,
        mgr_approval_capacity=mgr_approval_capacity,
        ic_capacity=ic_capacity,
        engagement_sensitivity=engagement_sensitivity,
        burnout_sensitivity=burnout_sensitivity,
        attrition_base_prob=attrition_base_prob,
        change_shock=0.0,
        seed=seed,
    )


def build_reorg(
    num_ics: int,
    num_managers: int,
    steps: int,
    tasks_per_step: int = 80,
    approval_rate: float = 0.30,
    approval_chain_depth: int = 1,
    mgr_approval_capacity: float = 5.0,
    ic_capacity: float = 2.0,
    engagement_sensitivity: float = 0.05,
    burnout_sensitivity: float = 0.04,
    attrition_base_prob: float = 0.005,
    change_shock: float = 0.10,
    seed: int = 42,
) -> SimConfig:
    """Reorg scenario — post-restructure org with optional change shock."""
    return SimConfig(
        num_ics=num_ics,
        num_managers=num_managers,
        steps=steps,
        tasks_per_step=tasks_per_step,
        approval_rate=approval_rate,
        approval_chain_depth=approval_chain_depth,
        mgr_approval_capacity=mgr_approval_capacity,
        ic_capacity=ic_capacity,
        engagement_sensitivity=engagement_sensitivity,
        burnout_sensitivity=burnout_sensitivity,
        attrition_base_prob=attrition_base_prob,
        change_shock=change_shock,
        seed=seed,
    )
