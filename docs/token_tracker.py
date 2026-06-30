# Loop Engineering Architecture - Token Tracker

## Purpose
Track token usage, enforce budget limits, and estimate costs across loops and agents.

```python
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
from collections import defaultdict

class ModelPricing:
    """Token pricing per model (per 1K tokens)"""
    PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    }
    
    @classmethod
    def get_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage"""
        pricing = cls.PRICING.get(model, {"input": 0.03, "output": 0.06})
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost
    
    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token)"""
        return len(text) // 4

@dataclass
class TokenUsage:
    """Single token usage record"""
    agent_id: str
    model: str
    input_tokens: int
    output_tokens: int
    task_id: str = None
    loop_id: str = None
    timestamp: datetime = field(default_factory=datetime.now)
    cost: float = 0.0
    
    def __post_init__(self):
        self.cost = ModelPricing.get_cost(self.model, self.input_tokens, self.output_tokens)

@dataclass
class BudgetConfig:
    """Budget limits configuration"""
    max_tokens_per_run: int = 100000
    max_cost_per_run: float = 5.0
    max_tokens_per_loop: int = 500000
    max_cost_per_loop: float = 25.0
    max_tokens_per_day: int = 2000000
    max_cost_per_day: float = 100.0
    alert_threshold_pct: float = 0.8  # Alert at 80% usage

class TokenTracker:
    def __init__(self, budget: BudgetConfig = None):
        self.budget = budget or BudgetConfig()
        self.usage_history: List[TokenUsage] = []
        self.current_run_tokens = 0
        self.current_run_cost = 0.0
        self.current_loop_tokens = 0
        self.current_loop_cost = 0.0
        self.daily_tokens = 0
        self.daily_cost = 0.0
        self.last_reset_date = datetime.now().date()
        
    def _check_daily_reset(self):
        """Reset daily counters if new day"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_tokens = 0
            self.daily_cost = 0.0
            self.last_reset_date = today
    
    def track_usage(self, agent_id: str, model: str, 
                   input_tokens: int, output_tokens: int,
                   task_id: str = None, loop_id: str = None) -> TokenUsage:
        """Track token usage for an agent call"""
        self._check_daily_reset()
        
        usage = TokenUsage(
            agent_id=agent_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            task_id=task_id,
            loop_id=loop_id
        )
        
        # Update counters
        self.current_run_tokens += input_tokens + output_tokens
        self.current_run_cost += usage.cost
        self.current_loop_tokens += input_tokens + output_tokens
        self.current_loop_cost += usage.cost
        self.daily_tokens += input_tokens + output_tokens
        self.daily_cost += usage.cost
        
        # Store in history
        self.usage_history.append(usage)
        
        return usage
    
    def estimate_and_check(self, model: str, estimated_input: int, 
                          estimated_output: int = 500) -> Dict[str, Any]:
        """Estimate tokens and check against budget before execution"""
        estimated_cost = ModelPricing.get_cost(model, estimated_input, estimated_output)
        estimated_total = estimated_input + estimated_output
        
        warnings = []
        can_proceed = True
        
        # Check run limits
        if self.current_run_tokens + estimated_total > self.budget.max_tokens_per_run:
            warnings.append(f"Run token limit exceeded: {self.current_run_tokens + estimated_total}/{self.budget.max_tokens_per_run}")
            can_proceed = False
        
        if self.current_run_cost + estimated_cost > self.budget.max_cost_per_run:
            warnings.append(f"Run cost limit exceeded: ${self.current_run_cost + estimated_cost:.4f}/${self.budget.max_cost_per_run:.2f}")
            can_proceed = False
        
        # Check loop limits
        if self.current_loop_tokens + estimated_total > self.budget.max_tokens_per_loop:
            warnings.append(f"Loop token limit exceeded: {self.current_loop_tokens + estimated_total}/{self.budget.max_tokens_per_loop}")
            can_proceed = False
        
        if self.current_loop_cost + estimated_cost > self.budget.max_cost_per_loop:
            warnings.append(f"Loop cost limit exceeded: ${self.current_loop_cost + estimated_cost:.4f}/${self.budget.max_cost_per_loop:.2f}")
            can_proceed = False
        
        # Check daily limits
        self._check_daily_reset()
        if self.daily_tokens + estimated_total > self.budget.max_tokens_per_day:
            warnings.append(f"Daily token limit exceeded: {self.daily_tokens + estimated_total}/{self.budget.max_tokens_per_day}")
            can_proceed = False
        
        if self.daily_cost + estimated_cost > self.budget.max_cost_per_day:
            warnings.append(f"Daily cost limit exceeded: ${self.daily_cost + estimated_cost:.4f}/${self.budget.max_cost_per_day:.2f}")
            can_proceed = False
        
        # Check alert thresholds
        if self.current_loop_tokens / self.budget.max_tokens_per_loop > self.budget.alert_threshold_pct:
            warnings.append(f"Loop token usage at {self.current_loop_tokens / self.budget.max_tokens_per_loop * 100:.1f}%")
        
        return {
            "can_proceed": can_proceed,
            "estimated_tokens": estimated_total,
            "estimated_cost": estimated_cost,
            "warnings": warnings,
            "current_usage": self.get_current_usage()
        }
    
    def get_current_usage(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        self._check_daily_reset()
        
        return {
            "run": {
                "tokens": self.current_run_tokens,
                "cost": self.current_run_cost,
                "budget_tokens_pct": (self.current_run_tokens / self.budget.max_tokens_per_run) * 100,
                "budget_cost_pct": (self.current_run_cost / self.budget.max_cost_per_run) * 100
            },
            "loop": {
                "tokens": self.current_loop_tokens,
                "cost": self.current_loop_cost,
                "budget_tokens_pct": (self.current_loop_tokens / self.budget.max_tokens_per_loop) * 100,
                "budget_cost_pct": (self.current_loop_cost / self.budget.max_cost_per_loop) * 100
            },
            "daily": {
                "tokens": self.daily_tokens,
                "cost": self.daily_cost,
                "budget_tokens_pct": (self.daily_tokens / self.budget.max_tokens_per_day) * 100,
                "budget_cost_pct": (self.daily_cost / self.budget.max_cost_per_day) * 100
            }
        }
    
    def reset_run_counters(self):
        """Reset run-level counters (call at start of new run)"""
        self.current_run_tokens = 0
        self.current_run_cost = 0.0
    
    def reset_loop_counters(self):
        """Reset loop-level counters (call at start of new loop)"""
        self.current_loop_tokens = 0
        self.current_loop_cost = 0.0
        self.reset_run_counters()
    
    def get_usage_by_agent(self) -> Dict[str, Dict]:
        """Get usage breakdown by agent"""
        by_agent = defaultdict(lambda: {"tokens": 0, "cost": 0.0, "calls": 0})
        
        for usage in self.usage_history:
            by_agent[usage.agent_id]["tokens"] += usage.input_tokens + usage.output_tokens
            by_agent[usage.agent_id]["cost"] += usage.cost
            by_agent[usage.agent_id]["calls"] += 1
        
        return dict(by_agent)
    
    def get_usage_by_model(self) -> Dict[str, Dict]:
        """Get usage breakdown by model"""
        by_model = defaultdict(lambda: {"tokens": 0, "cost": 0.0, "calls": 0})
        
        for usage in self.usage_history:
            by_model[usage.model]["tokens"] += usage.input_tokens + usage.output_tokens
            by_model[usage.model]["cost"] += usage.cost
            by_model[usage.model]["calls"] += 1
        
        return dict(by_model)
    
    def export_history(self, filepath: str):
        """Export usage history to JSON"""
        data = [
            {
                "agent_id": u.agent_id,
                "model": u.model,
                "input_tokens": u.input_tokens,
                "output_tokens": u.output_tokens,
                "cost": u.cost,
                "task_id": u.task_id,
                "loop_id": u.loop_id,
                "timestamp": u.timestamp.isoformat()
            }
            for u in self.usage_history
        ]
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def select_model(self, task_complexity: str, 
                    role: str = "implementer") -> str:
        """Select appropriate model based on task complexity and role"""
        model_map = {
            "simple": {
                "explorer": "gpt-4o-mini",
                "implementer": "gpt-4o-mini",
                "verifier": "gpt-4o",
                "triage": "gpt-4o-mini"
            },
            "medium": {
                "explorer": "gpt-4o-mini",
                "implementer": "gpt-4o",
                "verifier": "gpt-4o",
                "triage": "gpt-4o-mini"
            },
            "complex": {
                "explorer": "gpt-4o",
                "implementer": "gpt-4o",
                "verifier": "gpt-4o",
                "triage": "gpt-4o"
            },
            "critical": {
                "explorer": "gpt-4o",
                "implementer": "gpt-4o",
                "verifier": "gpt-4o",  # Or claude-3-opus for extra scrutiny
                "triage": "gpt-4o"
            }
        }
        
        return model_map.get(task_complexity, model_map["medium"]).get(role, "gpt-4o")

# Example usage
if __name__ == "__main__":
    # Initialize tracker with budget
    budget = BudgetConfig(
        max_tokens_per_run=50000,
        max_cost_per_run=2.0,
        max_tokens_per_day=500000,
        max_cost_per_day=20.0
    )
    
    tracker = TokenTracker(budget)
    
    # Check before execution
    result = tracker.estimate_and_check(
        model="gpt-4o",
        estimated_input=2000,
        estimated_output=1000
    )
    
    print(f"Can proceed: {result['can_proceed']}")
    print(f"Estimated cost: ${result['estimated_cost']:.4f}")
    print(f"Warnings: {result['warnings']}")
    
    # Track actual usage
    tracker.track_usage(
        agent_id="implementer-001",
        model="gpt-4o",
        input_tokens=2000,
        output_tokens=800,
        task_id="fix-auth-bug",
        loop_id="daily-quality"
    )
    
    # Get usage stats
    print(f"\nCurrent usage: {tracker.get_current_usage()}")
    print(f"By agent: {tracker.get_usage_by_agent()}")
