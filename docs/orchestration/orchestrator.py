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
        self.security = SecurityHardening()  # Add security layer
        self.token_tracker = TokenTracker()  # Add token tracking
        
    async def run_loop(self, loop_definition: LoopDefinition, 
                      user_id: str = None, user_input: str = None):
        """Execute a complete loop cycle"""
        # SECURITY: Validate input if provided
        if user_id and user_input:
            validation = self.security.validate_loop_input(
                user_id, loop_definition.id, user_input
            )
            if not validation["valid"]:
                raise SecurityError(f"Input validation failed: {validation['error']}")
        
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
            # SECURITY: Log error without exposing sensitive details
            error_msg = self.security.secrets_manager.redact_secrets(str(e))
            await self.memory.save_state(
                loop_definition.id, {"error": error_msg, "state": "failed"}
            )
            raise
        finally:
            # Clean up worktree
            await self.worktree_manager.delete_worktree(loop_definition.id)
    
    async def _process_finding(self, finding: Dict, worktree, skills, loop_def):
        """Process a single finding with implementer and verifier"""
        # Spawn implementer agent (maker)
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
        
        # SECURITY: Sanitize solution before passing to verifier
        sanitized_solution = self.security.sanitize_agent_output(
            json.dumps(solution) if isinstance(solution, dict) else str(solution)
        )
        
        # Spawn verifier agent (checker) with sanitized output only
        # CONTEXT ISOLATION: Verifier does NOT see implementer's reasoning
        verifier = await self.agent_registry.spawn_agent(
            "verifier",
            {
                "solution": sanitized_solution,
                "skills": skills,
                "criteria": loop_def.verification_criteria
                # NOTE: Do NOT pass implementation_result["reasoning"]
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
        # SECURITY: Wrap plugin calls in try/except for graceful degradation
        try:
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
        except Exception as e:
            # Log but don't fail - graceful degradation
            print(f"Warning: GitHub plugin failed: {e}")
        
        try:
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
        except Exception as e:
            print(f"Warning: Linear plugin failed: {e}")
        
        try:
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
        except Exception as e:
            print(f"Warning: Slack plugin failed: {e}")

class StateMachine:
    """Manages loop state transitions with validation"""
    
    def __init__(self):
        self.transitions = {
            LoopState.IDLE: [LoopState.RUNNING],
            LoopState.RUNNING: [LoopState.PAUSED, LoopState.COMPLETED, LoopState.FAILED],
            LoopState.PAUSED: [LoopState.RUNNING, LoopState.FAILED],
            LoopState.COMPLETED: [LoopState.IDLE],
            LoopState.FAILED: [LoopState.IDLE, LoopState.RUNNING]
        }
        self.state_history: Dict[str, List[Dict]] = {}  # loop_id -> history
    
    async def transition(self, loop_id: str, new_state: LoopState, 
                        memory_layer=None) -> bool:
        """Transition loop to new state with validation
        
        Returns True if transition succeeded, False otherwise
        """
        # Get current state
        current_state = await self._get_current_state(loop_id, memory_layer)
        
        # Validate transition
        if not self._is_valid_transition(current_state, new_state):
            # Log invalid transition attempt
            self._log_transition(loop_id, current_state, new_state, valid=False)
            return False
        
        # Record transition in history
        self._log_transition(loop_id, current_state, new_state, valid=True)
        
        # Update state in memory
        if memory_layer:
            await memory_layer.save_state(loop_id, {
                "status": new_state.value,
                "previous_state": current_state.value if current_state else None,
                "transition_at": datetime.now().isoformat()
            })
        
        return True
    
    def _is_valid_transition(self, current: LoopState, new: LoopState) -> bool:
        """Check if transition is valid"""
        if current is None:
            # Allow initial transition to RUNNING
            return new == LoopState.RUNNING
        
        allowed = self.transitions.get(current, [])
        return new in allowed
    
    async def _get_current_state(self, loop_id: str, memory_layer=None) -> LoopState:
        """Get current state from memory"""
        if memory_layer:
            state = await memory_layer.load_state(loop_id)
            status = state.get("status", "idle")
            try:
                return LoopState(status)
            except ValueError:
                return LoopState.IDLE
        return LoopState.IDLE
    
    def _log_transition(self, loop_id: str, from_state: LoopState, 
                       to_state: LoopState, valid: bool):
        """Log state transition"""
        if loop_id not in self.state_history:
            self.state_history[loop_id] = []
        
        self.state_history[loop_id].append({
            "from": from_state.value if from_state else None,
            "to": to_state.value,
            "valid": valid,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_history(self, loop_id: str) -> List[Dict]:
        """Get state transition history for a loop"""
        return self.state_history.get(loop_id, [])
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
