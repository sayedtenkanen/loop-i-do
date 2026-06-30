# Loop Engineering Architecture - Agent Registry

## Purpose
Manage different agent types with specific roles and capabilities.

## Key Interfaces

```python
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass
from abc import ABC, abstractmethod
from datetime import datetime
import asyncio
import uuid

@dataclass
class AgentConfig:
    model: str = "gpt-4"
    temperature: float = 0.3
    max_tokens: int = 4000
    timeout: int = 300
    retry_attempts: int = 3
    tools: List[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class AgentTask:
    task_id: str
    description: str
    context: Dict[str, Any]
    created_at: datetime
    status: str = "pending"
    result: Dict[str, Any] = None
    error: str = None

class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, agent_id: str, config: AgentConfig):
        self.agent_id = agent_id
        self.config = config
        self.created_at = datetime.now()
        self.status = "idle"
    
    @abstractmethod
    async def execute(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a task"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get agent capabilities"""
        pass
    
    def get_status(self) -> Dict:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "config": {
                "model": self.config.model,
                "temperature": self.config.temperature
            }
        }

class ExplorerAgent(BaseAgent):
    """Read-only analysis agent for discovery"""
    
    def __init__(self, agent_id: str, config: AgentConfig = None):
        super().__init__(agent_id, config or AgentConfig(
            model="gpt-4-mini",
            temperature=0.1,
            max_tokens=1000
        ))
    
    async def execute(self, task: AgentTask) -> Dict[str, Any]:
        """Execute exploration task"""
        self.status = "running"
        
        try:
            # Analysis logic here
            result = {
                "findings": [],
                "summary": "Analysis complete",
                "confidence": 0.85
            }
            
            self.status = "completed"
            return result
            
        except Exception as e:
            self.status = "failed"
            raise
    
    def get_capabilities(self) -> List[str]:
        return ["analysis", "read-only", "discovery"]

class ImplementerAgent(BaseAgent):
    """Code writing agent for implementation"""
    
    def __init__(self, agent_id: str, config: AgentConfig = None):
        super().__init__(agent_id, config or AgentConfig(
            model="gpt-4",
            temperature=0.3,
            max_tokens=4000
        ))
    
    async def execute(self, task: AgentTask) -> Dict[str, Any]:
        """Execute implementation task"""
        self.status = "running"
        
        try:
            # Implementation logic here
            result = {
                "files_changed": [],
                "tests_written": 0,
                "summary": "Implementation complete"
            }
            
            self.status = "completed"
            return result
            
        except Exception as e:
            self.status = "failed"
            raise
    
    def get_capabilities(self) -> List[str]:
        return ["coding", "implementation", "testing"]

class VerifierAgent(BaseAgent):
    """Review/validation agent with higher scrutiny"""
    
    def __init__(self, agent_id: str, config: AgentConfig = None):
        super().__init__(agent_id, config or AgentConfig(
            model="gpt-4",
            temperature=0.0,  # Lower temperature for more consistent verification
            max_tokens=2000
        ))
    
    async def execute(self, task: AgentTask) -> Dict[str, Any]:
        """Execute verification task"""
        self.status = "running"
        
        try:
            # Verification logic here
            result = {
                "passed": True,
                "issues": [],
                "score": 0.9,
                "summary": "Verification passed"
            }
            
            self.status = "completed"
            return result
            
        except Exception as e:
            self.status = "failed"
            raise
    
    def get_capabilities(self) -> List[str]:
        return ["verification", "review", "validation"]

class TriageAgent(BaseAgent):
    """Issue classification and prioritization"""
    
    def __init__(self, agent_id: str, config: AgentConfig = None):
        super().__init__(agent_id, config or AgentConfig(
            model="gpt-4-mini",
            temperature=0.2,
            max_tokens=1000
        ))
    
    async def execute(self, task: AgentTask) -> Dict[str, Any]:
        """Execute triage task"""
        self.status = "running"
        
        try:
            # Triage logic here
            result = {
                "priority": "high",
                "category": "bug",
                "assignee": None,
                "summary": "Issue triaged"
            }
            
            self.status = "completed"
            return result
            
        except Exception as e:
            self.status = "failed"
            raise
    
    def get_capabilities(self) -> List[str]:
        return ["triage", "classification", "prioritization"]

class AgentRegistry:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_types: Dict[str, Type[BaseAgent]] = {
            "explorer": ExplorerAgent,
            "implementer": ImplementerAgent,
            "verifier": VerifierAgent,
            "triage": TriageAgent
        }
        self.agent_configs: Dict[str, AgentConfig] = {}
    
    def register_agent_type(self, agent_type: str, agent_class: Type[BaseAgent]):
        """Register a new agent type"""
        self.agent_types[agent_type] = agent_class
    
    def register_agent_config(self, agent_type: str, config: AgentConfig):
        """Register configuration for an agent type"""
        self.agent_configs[agent_type] = config
    
    async def spawn_agent(self, agent_type: str, task_context: Dict[str, Any]) -> BaseAgent:
        """Create and initialize an agent"""
        agent_class = self.agent_types.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Generate unique agent ID
        agent_id = f"{agent_type}-{uuid.uuid4().hex[:8]}"
        
        # Get configuration
        config = self.agent_configs.get(agent_type, AgentConfig())
        
        # Create agent instance
        agent = agent_class(agent_id, config)
        
        # Register agent
        self.agents[agent_id] = agent
        
        return agent
    
    async def get_agent_status(self, agent_id: str) -> Dict:
        """Get current status of an agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return {"error": f"Agent {agent_id} not found"}
        
        return agent.get_status()
    
    async def terminate_agent(self, agent_id: str):
        """Terminate a running agent"""
        agent = self.agents.get(agent_id)
        if agent:
            agent.status = "terminated"
            # Cleanup resources if needed
    
    async def get_available_agents(self) -> List[Dict]:
        """Get list of available agent types"""
        return [
            {
                "type": agent_type,
                "capabilities": agent_class(None, AgentConfig()).get_capabilities()
            }
            for agent_type, agent_class in self.agent_types.items()
        ]
    
    async def get_active_agents(self) -> List[Dict]:
        """Get list of active agents"""
        return [
            agent.get_status()
            for agent in self.agents.values()
            if agent.status in ["running", "idle"]
        ]
    
    def create_custom_agent(self, agent_type: str, agent_class: Type[BaseAgent],
                           config: AgentConfig = None):
        """Create a custom agent type"""
        self.agent_types[agent_type] = agent_class
        if config:
            self.agent_configs[agent_type] = config

# Example custom agent
class SecurityReviewerAgent(BaseAgent):
    """Specialized security review agent"""
    
    def __init__(self, agent_id: str, config: AgentConfig = None):
        super().__init__(agent_id, config or AgentConfig(
            model="gpt-4",
            temperature=0.0,
            max_tokens=3000
        ))
    
    async def execute(self, task: AgentTask) -> Dict[str, Any]:
        """Execute security review"""
        self.status = "running"
        
        try:
            # Security analysis logic
            result = {
                "vulnerabilities": [],
                "security_score": 0.95,
                "recommendations": [],
                "summary": "Security review complete"
            }
            
            self.status = "completed"
            return result
            
        except Exception as e:
            self.status = "failed"
            raise
    
    def get_capabilities(self) -> List[str]:
        return ["security", "vulnerability-analysis", "compliance"]
```

## Agent Team Patterns

```python
class AgentTeam:
    """Orchestrate multiple agents working together"""
    
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
    
    async def implement_and_verify(self, task: AgentTask) -> Dict:
        """Implementer + Verifier team pattern"""
        # Spawn implementer
        implementer = await self.registry.spawn_agent("implementer", task.context)
        
        # Execute implementation
        implementation_result = await implementer.execute(task)
        
        # Create verification task
        verification_task = AgentTask(
            task_id=f"verify-{task.task_id}",
            description=f"Verify implementation: {task.description}",
            context={
                "implementation": implementation_result,
                "original_task": task.context
            },
            created_at=datetime.now()
        )
        
        # Spawn verifier
        verifier = await self.registry.spawn_agent("verifier", verification_task.context)
        
        # Execute verification
        verification_result = await verifier.execute(verification_task)
        
        return {
            "implementation": implementation_result,
            "verification": verification_result,
            "passed": verification_result.get("passed", False)
        }
    
    async def explore_implement_verify(self, task: AgentTask) -> Dict:
        """Explorer + Implementer + Verifier team pattern"""
        # Explorer phase
        explorer = await self.registry.spawn_agent("explorer", task.context)
        exploration_result = await explorer.execute(task)
        
        # Implementation phase
        implementation_task = AgentTask(
            task_id=f"implement-{task.task_id}",
            description=f"Implement based on exploration",
            context={
                "exploration": exploration_result,
                "original_task": task.context
            },
            created_at=datetime.now()
        )
        
        implementer = await self.registry.spawn_agent("implementer", implementation_task.context)
        implementation_result = await implementer.execute(implementation_task)
        
        # Verification phase
        verification_task = AgentTask(
            task_id=f"verify-{task.task_id}",
            description=f"Verify implementation",
            context={
                "implementation": implementation_result,
                "exploration": exploration_result
            },
            created_at=datetime.now()
        )
        
        verifier = await self.registry.spawn_agent("verifier", verification_task.context)
        verification_result = await verifier.execute(verification_task)
        
        return {
            "exploration": exploration_result,
            "implementation": implementation_result,
            "verification": verification_result,
            "passed": verification_result.get("passed", False)
        }
```

## Implementation Notes

1. **Agent Lifecycle**: Agents are spawned, execute tasks, and are cleaned up
2. **Configuration**: Each agent type has default configurations that can be overridden
3. **Team Patterns**: Multiple agents can work together in defined patterns
4. **Custom Agents**: Extensible system allows creating specialized agent types
5. **Monitoring**: Agent status is tracked throughout execution

## Example Usage

```python
# Initialize registry
registry = AgentRegistry()

# Spawn an explorer agent
explorer = await registry.spawn_agent("explorer", {"task": "analyze codebase"})

# Execute task
result = await explorer.execute(AgentTask(
    task_id="exploration-1",
    description="Find potential bugs",
    context={"path": "/src"},
    created_at=datetime.now()
))

# Create custom agent type
registry.create_custom_agent("security", SecurityReviewerAgent)

# Use agent team pattern
team = AgentTeam(registry)
result = await team.implement_and_verify(task)
```
