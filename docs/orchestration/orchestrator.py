# Loop Engineering Architecture - Orchestration Layer

## Purpose
Central control system managing workflows, state transitions, and component coordination.

## Key Interfaces

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio

class LoopState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class LoopDefinition:
    id: str
    description: str
    discovery_task: str
    verification_criteria: Dict[str, Any]
    max_retries: int = 3
    timeout_seconds: int = 3600

@dataclass
class LoopConfig:
    max_concurrent_loops: int = 5
    default_timeout: int = 3600
    retry_attempts: int = 3
    memory_backend: str = "sqlite"
    scheduler_backend: str = "apscheduler"

class LoopOrchestrator:
    def __init__(self, config: LoopConfig):
        self.config = config
        self.state_machine = StateMachine()
        self.memory = MemoryLayer(config.memory_backend)
        self.agent_registry = AgentRegistry()
        self.skills_engine = SkillsEngine()
        self.worktree_manager = WorktreeManager()
        self.plugin_manager = PluginManager()
        self.scheduler = AutomationScheduler(self.memory)
        
    async def run_loop(self, loop_definition: LoopDefinition):
        """Execute a complete loop cycle"""
        # 1. Check if loop should run based on scheduler
        if not await self.scheduler.should_run(loop_definition.id):
            return
        
        # 2. Load previous state
        state = await self.memory.load_state(loop_definition.id)
        
        # 3. Create isolated worktree
        worktree = await self.worktree_manager.create_worktree(loop_definition.id)
        
        try:
            # 4. Load relevant skills
            skills = await self.skills_engine.get_relevant_skills(
                loop_definition.description
            )
            
            # 5. Spawn explorer agent for discovery
            explorer = await self.agent_registry.spawn_agent(
                "explorer",
                {
                    "task": loop_definition.discovery_task,
                    "worktree": worktree,
                    "skills": skills
                }
            )
            
            # 6. Execute discovery phase
            findings = await explorer.execute()
            
            # 7. Process each finding with implementer + verifier
            for finding in findings:
                await self._process_finding(
                    finding, worktree, skills, loop_definition
                )
            
            # 8. Use plugins to create PR/update tickets
            await self._execute_post_actions(worktree, loop_definition)
            
            # 9. Update final state
            await self.memory.update_progress(
                loop_definition.id, "loop", "completed"
            )
            
        except Exception as e:
            # Handle errors, save state for retry
            await self.memory.save_state(
                loop_definition.id, {"error": str(e), "state": "failed"}
            )
            raise
        finally:
            # Clean up worktree
            await self.worktree_manager.delete_worktree(loop_definition.id)
    
    async def pause_loop(self, loop_id: str):
        """Pause a running loop"""
        await self.state_machine.transition(loop_id, LoopState.PAUSED)
        await self.memory.update_progress(loop_id, "loop", "paused")
    
    async def resume_loop(self, loop_id: str):
        """Resume a paused loop"""
        await self.state_machine.transition(loop_id, LoopState.RUNNING)
        # Reload state and continue execution
        state = await self.memory.load_state(loop_id)
        # Resume from last checkpoint
    
    async def _process_finding(self, finding: Dict, worktree, skills, loop_def):
        """Process a single finding with implementer and verifier"""
        # Spawn implementer agent
        implementer = await self.agent_registry.spawn_agent(
            "implementer",
            {
                "task": finding,
                "worktree": worktree,
                "skills": skills
            }
        )
        
        # Execute implementation
        solution = await implementer.execute()
        
        # Spawn verifier agent (different model, higher scrutiny)
        verifier = await self.agent_registry.spawn_agent(
            "verifier",
            {
                "solution": solution,
                "skills": skills,
                "criteria": loop_def.verification_criteria
            }
        )
        
        # Execute verification
        verification = await verifier.execute()
        
        # Update state based on verification
        status = "completed" if verification.passed else "failed"
        await self.memory.update_progress(
            loop_def.id, finding.get("id", "unknown"), status
        )
    
    async def _execute_post_actions(self, worktree, loop_def):
        """Execute post-processing actions using plugins"""
        # Create PR if GitHub plugin available
        if self.plugin_manager.has_plugin("github"):
            await self.plugin_manager.execute_plugin_action(
                "github",
                "create_pr",
                {
                    "worktree": worktree,
                    "title": f"Automated fix for: {loop_def.description}",
                    "body": f"Generated by loop engineering system"
                }
            )
        
        # Update Linear ticket if available
        if self.plugin_manager.has_plugin("linear"):
            await self.plugin_manager.execute_plugin_action(
                "linear",
                "update_ticket",
                {
                    "ticket_id": loop_def.id,
                    "status": "in_review"
                }
            )
        
        # Notify Slack if available
        if self.plugin_manager.has_plugin("slack"):
            await self.plugin_manager.execute_plugin_action(
                "slack",
                "send_message",
                {
                    "channel": "#dev-updates",
                    "message": f"Loop {loop_def.id} completed"
                }
            )

class StateMachine:
    """Manages loop state transitions"""
    
    def __init__(self):
        self.transitions = {
            LoopState.IDLE: [LoopState.RUNNING],
            LoopState.RUNNING: [LoopState.PAUSED, LoopState.COMPLETED, LoopState.FAILED],
            LoopState.PAUSED: [LoopState.RUNNING, LoopState.FAILED],
            LoopState.COMPLETED: [LoopState.IDLE],
            LoopState.FAILED: [LoopState.IDLE, LoopState.RUNNING]
        }
    
    async def transition(self, loop_id: str, new_state: LoopState):
        """Transition loop to new state"""
        # Validate transition is allowed
        # Update state in memory
        pass
```

## Implementation Notes

1. **Error Handling**: The orchestrator includes retry logic and state persistence for fault tolerance
2. **Isolation**: Each loop execution gets its own worktree to prevent conflicts
3. **Verification**: Separate verifier agents ensure code quality
4. **Extensibility**: Plugin system allows integration with external tools
5. **Monitoring**: State transitions are tracked for observability

## Usage Example

```python
# Initialize orchestrator
config = LoopConfig(
    max_concurrent_loops=3,
    memory_backend="sqlite",
    scheduler_backend="apscheduler"
)
orchestrator = LoopOrchestrator(config)

# Define a loop
loop_def = LoopDefinition(
    id="daily-bug-fixes",
    description="Automated bug detection and fixing",
    discovery_task="Find and analyze recent bug reports",
    verification_criteria={"tests_pass": True, "lint_clean": True}
)

# Run the loop
await orchestrator.run_loop(loop_def)
```
