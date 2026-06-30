# Loop Engineering Architecture - Metrics and Monitoring

## Purpose
Prometheus-compatible metrics for loop executions, token usage, and errors.

```python
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import time
import json

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"

@dataclass
class Metric:
    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class MetricsCollector:
    """Collect and expose metrics for Prometheus"""
    
    def __init__(self):
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, list] = {}
        self.labels: Dict[str, Dict[str, str]] = {}
    
    def increment_counter(self, name: str, value: float = 1.0, 
                         labels: Dict[str, str] = None):
        """Increment a counter"""
        key = self._make_key(name, labels)
        self.counters[key] = self.counters.get(key, 0) + value
        self.labels[key] = labels or {}
    
    def set_gauge(self, name: str, value: float, 
                 labels: Dict[str, str] = None):
        """Set a gauge value"""
        key = self._make_key(name, labels)
        self.gauges[key] = value
        self.labels[key] = labels or {}
    
    def observe_histogram(self, name: str, value: float,
                         labels: Dict[str, str] = None):
        """Observe a histogram value"""
        key = self._make_key(name, labels)
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)
        self.labels[key] = labels or {}
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Make a unique key from name and labels"""
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{name}{{{label_str}}}"
        return name
    
    def get_prometheus_format(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Counters
        for key, value in self.counters.items():
            labels = self.labels.get(key, {})
            label_str = self._format_labels(labels)
            lines.append(f"{key}{label_str} {value}")
        
        # Gauges
        for key, value in self.gauges.items():
            labels = self.labels.get(key, {})
            label_str = self._format_labels(labels)
            lines.append(f"{key}{label_str} {value}")
        
        # Histograms
        for key, values in self.histograms.items():
            labels = self.labels.get(key, {})
            if values:
                label_str = self._format_labels(labels)
                lines.append(f"{key}_count{label_str} {len(values)}")
                lines.append(f"{key}_sum{label_str} {sum(values)}")
                lines.append(f"{key}_bucket{{le=\"+Inf\"}}{label_str} {len(values)}")
        
        return "\n".join(lines)
    
    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus"""
        if not labels:
            return ""
        label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
        return f"{{{label_str}}}"
    
    def reset(self):
        """Reset all metrics"""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.labels.clear()

# ============================================================
# Pre-defined Metrics
# ============================================================

class LoopMetrics:
    """Pre-defined metrics for loop engineering"""
    
    def __init__(self, collector: MetricsCollector = None):
        self.collector = collector or MetricsCollector()
    
    def record_loop_start(self, loop_id: str):
        """Record loop start"""
        self.collector.increment_counter(
            "loop_executions_total",
            labels={"loop_id": loop_id, "status": "started"}
        )
        self.collector.set_gauge(
            "loop_running",
            1.0,
            labels={"loop_id": loop_id}
        )
    
    def record_loop_complete(self, loop_id: str, success: bool, 
                            duration_seconds: float):
        """Record loop completion"""
        status = "success" if success else "failure"
        self.collector.increment_counter(
            "loop_executions_total",
            labels={"loop_id": loop_id, "status": status}
        )
        self.collector.observe_histogram(
            "loop_duration_seconds",
            duration_seconds,
            labels={"loop_id": loop_id}
        )
        self.collector.set_gauge(
            "loop_running",
            0.0,
            labels={"loop_id": loop_id}
        )
    
    def record_task_complete(self, loop_id: str, task_id: str, 
                            success: bool, duration_seconds: float):
        """Record task completion"""
        status = "success" if success else "failure"
        self.collector.increment_counter(
            "loop_tasks_total",
            labels={"loop_id": loop_id, "status": status}
        )
        self.collector.observe_histogram(
            "loop_task_duration_seconds",
            duration_seconds,
            labels={"loop_id": loop_id}
        )
    
    def record_agent_call(self, agent_type: str, model: str,
                         tokens_used: int, success: bool):
        """Record agent API call"""
        status = "success" if success else "failure"
        self.collector.increment_counter(
            "agent_calls_total",
            labels={"agent_type": agent_type, "model": model, "status": status}
        )
        self.collector.increment_counter(
            "agent_tokens_total",
            value=tokens_used,
            labels={"agent_type": agent_type, "model": model}
        )
    
    def record_validation(self, validation_type: str, success: bool):
        """Record validation result"""
        status = "success" if success else "failure"
        self.collector.increment_counter(
            "validations_total",
            labels={"type": validation_type, "status": status}
        )
    
    def record_error(self, component: str, error_code: str):
        """Record error"""
        self.collector.increment_counter(
            "errors_total",
            labels={"component": component, "error_code": error_code}
        )
    
    def record_worktree(self, operation: str, success: bool):
        """Record worktree operation"""
        status = "success" if success else "failure"
        self.collector.increment_counter(
            "worktree_operations_total",
            labels={"operation": operation, "status": status}
        )
    
    def set_token_usage(self, budget_type: str, used: int, max_tokens: int):
        """Set token usage gauge"""
        self.collector.set_gauge(
            "token_usage_ratio",
            used / max_tokens if max_tokens > 0 else 0,
            labels={"budget": budget_type}
        )
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format"""
        return self.collector.get_prometheus_format()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            "counters": dict(self.collector.counters),
            "gauges": dict(self.collector.gauges),
            "histograms": {
                k: {
                    "count": len(v),
                    "sum": sum(v),
                    "avg": sum(v) / len(v) if v else 0
                }
                for k, v in self.collector.histograms.items()
            }
        }

# ============================================================
# Health Metrics
# ============================================================

class HealthMetrics:
    """System health metrics"""
    
    def __init__(self, collector: MetricsCollector = None):
        self.collector = collector or MetricsCollector()
        self.start_time = time.time()
    
    def record_uptime(self):
        """Record uptime"""
        uptime = time.time() - self.start_time
        self.collector.set_gauge("system_uptime_seconds", uptime)
    
    def record_component_health(self, component: str, healthy: bool):
        """Record component health"""
        self.collector.set_gauge(
            "component_health",
            1.0 if healthy else 0.0,
            labels={"component": component}
        )
    
    def record_queue_size(self, queue_name: str, size: int):
        """Record queue size"""
        self.collector.set_gauge(
            "queue_size",
            size,
            labels={"queue": queue_name}
        )
    
    def record_latency(self, operation: str, latency_ms: float):
        """Record operation latency"""
        self.collector.observe_histogram(
            "operation_latency_ms",
            latency_ms,
            labels={"operation": operation}
        )

# Example usage
if __name__ == "__main__":
    # Initialize metrics
    collector = MetricsCollector()
    loop_metrics = LoopMetrics(collector)
    
    # Record some metrics
    loop_metrics.record_loop_start("daily-quality")
    loop_metrics.record_agent_call("implementer", "gpt-4o", 2500, True)
    loop_metrics.record_validation("tests", True)
    loop_metrics.record_loop_complete("daily-quality", True, 120.5)
    
    # Export Prometheus format
    print("=== Prometheus Format ===")
    print(collector.get_prometheus_format())
    
    # Get summary
    print("\n=== Summary ===")
    print(json.dumps(loop_metrics.get_summary(), indent=2))
