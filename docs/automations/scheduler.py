# Loop Engineering Architecture - Automations Scheduler

## Purpose
Time-based and event-based trigger system for loop execution.

## Key Interfaces

```python
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
from enum import Enum

class TriggerType(Enum):
    CRON = "cron"
    INTERVAL = "interval"
    EVENT = "event"
    MANUAL = "manual"

@dataclass
class TriggerConfig:
    trigger_type: TriggerType
    cron_expression: str = None  # For cron triggers
    interval_seconds: int = None  # For interval triggers
    event_type: str = None  # For event triggers
    max_executions: int = None  # Optional limit
    cooldown_seconds: int = 0  # Minimum time between executions

@dataclass
class Automation:
    id: str
    loop_id: str
    trigger: TriggerConfig
    enabled: bool = True
    last_executed: datetime = None
    execution_count: int = 0
    next_scheduled: datetime = None

class AutomationScheduler:
    def __init__(self, memory_layer):
        self.memory = memory_layer
        self.automations: Dict[str, Automation] = {}
        self.event_listeners: Dict[str, List[Callable]] = {}
        self.running = False
        
    def add_cron_trigger(self, loop_id: str, cron_expr: str, 
                        max_executions: int = None, cooldown: int = 0):
        """Add scheduled trigger with cron expression"""
        automation_id = f"cron-{loop_id}-{datetime.now().timestamp()}"
        
        automation = Automation(
            id=automation_id,
            loop_id=loop_id,
            trigger=TriggerConfig(
                trigger_type=TriggerType.CRON,
                cron_expression=cron_expr,
                max_executions=max_executions,
                cooldown_seconds=cooldown
            )
        )
        
        self.automations[automation_id] = automation
        return automation_id
    
    def add_interval_trigger(self, loop_id: str, interval_seconds: int,
                            max_executions: int = None, cooldown: int = 0):
        """Add interval-based trigger"""
        automation_id = f"interval-{loop_id}-{datetime.now().timestamp()}"
        
        automation = Automation(
            id=automation_id,
            loop_id=loop_id,
            trigger=TriggerConfig(
                trigger_type=TriggerType.INTERVAL,
                interval_seconds=interval_seconds,
                max_executions=max_executions,
                cooldown_seconds=cooldown
            )
        )
        
        self.automations[automation_id] = automation
        return automation_id
    
    def add_event_trigger(self, loop_id: str, event_type: str,
                         max_executions: int = None, cooldown: int = 0):
        """Add event-based trigger"""
        automation_id = f"event-{loop_id}-{event_type}"
        
        automation = Automation(
            id=automation_id,
            loop_id=loop_id,
            trigger=TriggerConfig(
                trigger_type=TriggerType.EVENT,
                event_type=event_type,
                max_executions=max_executions,
                cooldown_seconds=cooldown
            )
        )
        
        self.automations[automation_id] = automation
        
        # Register event listener
        if event_type not in self.event_listeners:
            self.event_listeners[event_type] = []
        
        self.event_listeners[event_type].append(
            lambda: self._trigger_automation(automation_id)
        )
        
        return automation_id
    
    async def should_run(self, automation_id: str) -> bool:
        """Check if automation should run based on schedule"""
        automation = self.automations.get(automation_id)
        if not automation or not automation.enabled:
            return False
        
        # Check max executions
        if (automation.trigger.max_executions and 
            automation.execution_count >= automation.trigger.max_executions):
            return False
        
        # Check cooldown
        if automation.last_executed:
            time_since_last = datetime.now() - automation.last_executed
            if time_since_last.total_seconds() < automation.trigger.cooldown_seconds:
                return False
        
        # Check trigger condition
        if automation.trigger.trigger_type == TriggerType.CRON:
            return self._should_run_cron(automation.trigger.cron_expression)
        
        elif automation.trigger.trigger_type == TriggerType.INTERVAL:
            return self._should_run_interval(
                automation.last_executed, 
                automation.trigger.interval_seconds
            )
        
        elif automation.trigger.trigger_type == TriggerType.EVENT:
            # Event triggers are handled by event listeners
            return False
        
        return False
    
    async def execute_scheduled_loop(self, automation_id: str):
        """Execute a loop based on schedule"""
        automation = self.automations.get(automation_id)
        if not automation:
            raise ValueError(f"Automation {automation_id} not found")
        
        # Update execution metadata
        automation.last_executed = datetime.now()
        automation.execution_count += 1
        
        # Calculate next scheduled time
        if automation.trigger.trigger_type == TriggerType.CRON:
            automation.next_scheduled = self._next_cron_time(
                automation.trigger.cron_expression
            )
        elif automation.trigger.trigger_type == TriggerType.INTERVAL:
            automation.next_scheduled = datetime.now() + timedelta(
                seconds=automation.trigger.interval_seconds
            )
        
        # Save state
        await self.memory.save_automation_state(automation)
        
        # Execute the loop
        await self._execute_loop(automation.loop_id)
    
    async def _trigger_automation(self, automation_id: str):
        """Trigger an automation manually or by event"""
        automation = self.automations.get(automation_id)
        if automation and automation.enabled:
            await self.execute_scheduled_loop(automation_id)
    
    async def _execute_loop(self, loop_id: str):
        """Execute a loop - to be implemented by orchestrator"""
        # This would call the orchestrator's run_loop method
        pass
    
    def _should_run_cron(self, cron_expression: str) -> bool:
        """Check if cron expression matches current time"""
        # Implementation would parse cron expression
        # and check against current time
        return True  # Placeholder
    
    def _should_run_interval(self, last_executed: datetime, 
                            interval_seconds: int) -> bool:
        """Check if interval has passed"""
        if not last_executed:
            return True
        
        time_since_last = datetime.now() - last_executed
        return time_since_last.total_seconds() >= interval_seconds
    
    def _next_cron_time(self, cron_expression: str) -> datetime:
        """Calculate next cron execution time"""
        # Implementation would parse cron expression
        # and calculate next execution time
        return datetime.now() + timedelta(hours=1)  # Placeholder
    
    async def start(self):
        """Start the scheduler"""
        self.running = True
        while self.running:
            # Check all automations
            for automation_id, automation in self.automations.items():
                if await self.should_run(automation_id):
                    await self.execute_scheduled_loop(automation_id)
            
            # Sleep for a short interval
            await asyncio.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
    
    def get_automation_status(self, automation_id: str) -> Dict:
        """Get status of an automation"""
        automation = self.automations.get(automation_id)
        if not automation:
            return {"error": "Automation not found"}
        
        return {
            "id": automation.id,
            "loop_id": automation.loop_id,
            "enabled": automation.enabled,
            "execution_count": automation.execution_count,
            "last_executed": automation.last_executed.isoformat() if automation.last_executed else None,
            "next_scheduled": automation.next_scheduled.isoformat() if automation.next_scheduled else None
        }
```

## Implementation Notes

1. **Cron Parsing**: Use `croniter` library for cron expression parsing
2. **Event System**: Implement with Python's `asyncio` events or external message queue
3. **Persistence**: Store automation states in memory layer for durability
4. **Concurrency**: Use asyncio for non-blocking schedule checking
5. **Monitoring**: Track execution metrics for observability

## Example Usage

```python
# Initialize scheduler
scheduler = AutomationScheduler(memory_layer)

# Add daily CI failure triage
scheduler.add_cron_trigger(
    loop_id="daily-ci-triage",
    cron_expr="0 9 * * *",  # Every day at 9 AM
    cooldown=3600  # 1 hour cooldown
)

# Add hourly code quality check
scheduler.add_interval_trigger(
    loop_id="hourly-code-quality",
    interval_seconds=3600,  # Every hour
    max_executions=24  # Max 24 times
)

# Add event-based trigger for new issues
scheduler.add_event_trigger(
    loop_id="new-issue-handler",
    event_type="github.issue.opened"
)

# Start scheduler
await scheduler.start()
```
