"""
WorkForward AI — Core Simulation Engine
Agent-based + queue-based hybrid org restructure simulator.
Pure Python, no Streamlit dependency.
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SimConfig:
    """All tunable parameters for one simulation run."""
    # Workforce
    num_ics: int = 50
    num_managers: int = 10
    # Time
    steps: int = 60
    # Work
    tasks_per_step: int = 80          # new tasks arriving each step
    ic_capacity: float = 2.0          # tasks an IC can complete per step
    # Approval
    approval_rate: float = 0.30       # fraction of tasks needing approval
    approval_chain_depth: int = 1     # how many managers must approve
    mgr_approval_capacity: float = 5.0  # approvals a manager handles per step
    # Engagement / burnout
    engagement_sensitivity: float = 0.05   # how fast workload hits engagement
    burnout_sensitivity: float = 0.04      # how fast overwork accumulates burnout
    recovery_rate: float = 0.03            # burnout recovery per step when not blocked
    # Attrition
    attrition_base_prob: float = 0.005     # base quit prob per step per agent
    attrition_burnout_weight: float = 0.02
    attrition_engagement_weight: float = 0.01
    # Change shock (reorg-specific; 0 = no shock)
    change_shock: float = 0.0         # engagement penalty applied at step 0
    # Random seed
    seed: Optional[int] = 42


@dataclass
class Person:
    """An agent — either IC or manager."""
    pid: int
    role: str                        # "ic" | "manager"
    engagement: float = 0.85
    burnout: float = 0.10
    workload: float = 0.0            # tasks assigned this step
    active: bool = True              # False = attrited

    def effective_capacity(self, base_capacity: float) -> float:
        """Capacity reduced by burnout and low engagement."""
        modifier = max(0.1, self.engagement * (1 - 0.5 * self.burnout))
        return base_capacity * modifier

    def update_wellbeing(
        self,
        workload_ratio: float,          # workload / capacity
        blocked_ratio: float,           # fraction of tasks blocked in queue
        span_of_control: float,         # ICs per manager (managers only)
        cfg: SimConfig,
    ) -> None:
        """Update engagement & burnout each step."""
        # Overwork → burnout up, engagement down
        overwork = max(0.0, workload_ratio - 1.0)
        self.burnout = min(1.0, self.burnout + overwork * cfg.burnout_sensitivity)

        # Blocking frustration → engagement down
        frustration = blocked_ratio * cfg.engagement_sensitivity
        self.engagement = max(0.0, self.engagement - frustration)

        # Manager span-of-control stress
        if self.role == "manager" and span_of_control > 8:
            span_stress = (span_of_control - 8) * 0.003
            self.burnout = min(1.0, self.burnout + span_stress)

        # Recovery when not overloaded
        if workload_ratio < 0.8:
            self.burnout = max(0.0, self.burnout - cfg.recovery_rate)
            self.engagement = min(1.0, self.engagement + cfg.recovery_rate * 0.5)

    def check_attrition(self, cfg: SimConfig) -> bool:
        """Return True if this agent leaves this step."""
        if not self.active:
            return False
        prob = (
            cfg.attrition_base_prob
            + cfg.attrition_burnout_weight * self.burnout
            - cfg.attrition_engagement_weight * self.engagement
        )
        prob = max(0.0, min(1.0, prob))
        return random.random() < prob


@dataclass
class StepSnapshot:
    """Metrics captured at a single simulation step."""
    step: int
    tasks_completed: int
    tasks_blocked: int
    decision_latency: float          # avg steps tasks spent in approval queue
    avg_engagement: float
    avg_burnout: float
    attrition_events: int
    active_ics: int
    active_managers: int


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

class OrgSim:
    """
    Discrete-step organisation simulator.

    Usage::
        sim = OrgSim(cfg)
        snapshots = sim.run()
    """

    def __init__(self, cfg: SimConfig) -> None:
        self.cfg = cfg
        random.seed(cfg.seed)

        # Build agents
        self.ics: list[Person] = [
            Person(pid=i, role="ic", engagement=random.gauss(0.82, 0.08))
            for i in range(cfg.num_ics)
        ]
        self.managers: list[Person] = [
            Person(pid=1000 + i, role="manager", engagement=random.gauss(0.78, 0.08))
            for i in range(cfg.num_managers)
        ]

        # Clamp initial values
        for p in self.all_agents():
            p.engagement = min(1.0, max(0.1, p.engagement))

        # Apply change shock immediately
        if cfg.change_shock > 0:
            for p in self.all_agents():
                p.engagement = max(0.1, p.engagement - cfg.change_shock)

        # Approval queue: list of (task_id, age_in_queue)
        self._approval_queue: list[dict] = []
        self._task_counter = 0
        self.history: list[StepSnapshot] = []

    def all_agents(self) -> list[Person]:
        return self.ics + self.managers

    def run(self) -> list[StepSnapshot]:
        for step in range(self.cfg.steps):
            snap = self._step(step)
            self.history.append(snap)
        return self.history

    def _step(self, step: int) -> StepSnapshot:
        cfg = self.cfg
        active_ics = [p for p in self.ics if p.active]
        active_mgrs = [p for p in self.managers if p.active]

        if not active_ics:
            # Edge case: everyone left
            return StepSnapshot(
                step=step, tasks_completed=0, tasks_blocked=len(self._approval_queue),
                decision_latency=0, avg_engagement=0, avg_burnout=1,
                attrition_events=0, active_ics=0, active_managers=len(active_mgrs),
            )

        # 1. Generate new tasks
        new_tasks = cfg.tasks_per_step
        needs_approval_count = int(new_tasks * cfg.approval_rate)
        direct_tasks = new_tasks - needs_approval_count

        # Tasks needing approval → queue
        for _ in range(needs_approval_count):
            self._approval_queue.append({"id": self._task_counter, "age": 0, "depth_remaining": cfg.approval_chain_depth})
            self._task_counter += 1

        # 2. Process approval queue (managers drain it)
        total_mgr_capacity = sum(
            p.effective_capacity(cfg.mgr_approval_capacity) for p in active_mgrs
        ) if active_mgrs else 0.0

        approvals_this_step = min(int(total_mgr_capacity), len(self._approval_queue))
        approved_latencies: list[float] = []
        for i in range(approvals_this_step):
            task = self._approval_queue.pop(0)
            approved_latencies.append(task["age"])
        # Age remaining queue
        for t in self._approval_queue:
            t["age"] += 1

        tasks_blocked = len(self._approval_queue)
        avg_latency = float(sum(approved_latencies) / len(approved_latencies)) if approved_latencies else (
            float(self._approval_queue[0]["age"]) if self._approval_queue else 0.0
        )

        # 3. ICs complete direct tasks + approved tasks
        total_ic_capacity = sum(
            p.effective_capacity(cfg.ic_capacity) for p in active_ics
        )
        tasks_available = direct_tasks + approvals_this_step
        tasks_completed = min(int(total_ic_capacity), tasks_available)

        # 4. Update wellbeing
        span = len(active_ics) / max(1, len(active_mgrs))
        blocked_ratio = tasks_blocked / max(1, len(self._approval_queue) + approvals_this_step + direct_tasks)

        for p in active_ics:
            p.workload = tasks_available / max(1, len(active_ics))
            capacity = p.effective_capacity(cfg.ic_capacity)
            workload_ratio = p.workload / max(0.01, capacity)
            p.update_wellbeing(workload_ratio, blocked_ratio, span, cfg)

        for p in active_mgrs:
            mgr_load = needs_approval_count / max(1, len(active_mgrs))
            workload_ratio = mgr_load / max(0.01, cfg.mgr_approval_capacity)
            p.update_wellbeing(workload_ratio, blocked_ratio, span, cfg)

        # 5. Attrition
        attrition_events = 0
        for p in active_ics + active_mgrs:
            if p.check_attrition(cfg):
                p.active = False
                attrition_events += 1

        # 6. Snapshot
        all_active = [p for p in self.all_agents() if p.active]
        avg_eng = sum(p.engagement for p in all_active) / max(1, len(all_active))
        avg_burn = sum(p.burnout for p in all_active) / max(1, len(all_active))

        return StepSnapshot(
            step=step,
            tasks_completed=tasks_completed,
            tasks_blocked=tasks_blocked,
            decision_latency=avg_latency,
            avg_engagement=avg_eng,
            avg_burnout=avg_burn,
            attrition_events=attrition_events,
            active_ics=len([p for p in self.ics if p.active]),
            active_managers=len([p for p in self.managers if p.active]),
        )
