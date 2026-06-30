#!/usr/bin/env python3
"""
Basic usage example for Loop Engineering System
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from docs.orchestration import LoopOrchestrator, LoopConfig, LoopDefinition
from docs.memory import MemoryLayer
from docs.automations import AutomationScheduler
from docs.agents import AgentRegistry, AgentTask
from docs.skills import SkillsEngine
from docs.worktrees import WorktreeManager
from docs.plugins import PluginManager

async def main():
    """Main example function"""
    print("Loop Engineering System - Basic Usage Example")
    print("=" * 50)
    
    # 1. Initialize configuration
    config = LoopConfig()
    print(f"✓ Configuration initialized")
    
    # 2. Initialize memory layer
    memory = MemoryLayer(
        backend="sqlite",
        connection_string="example_loop_state.db"
    )
    print(f"✓ Memory layer initialized with SQLite backend")
    
    # 3. Initialize scheduler
    scheduler = AutomationScheduler(memory)
    print(f"✓ Scheduler initialized")
    
    # 4. Initialize agent registry
    agent_registry = AgentRegistry()
    print(f"✓ Agent registry initialized with {len(agent_registry.agent_types)} agent types")
    
    # 5. Initialize skills engine
    skills_engine = SkillsEngine("./skills")
    print(f"✓ Skills engine initialized")
    
    # 6. Initialize worktree manager
    worktree_manager = WorktreeManager(".")
    print(f"✓ Worktree manager initialized")
    
    # 7. Initialize plugin manager
    plugin_manager = PluginManager("./plugins")
    print(f"✓ Plugin manager initialized")
    
    # 8. Initialize orchestrator
    orchestrator = LoopOrchestrator(config)
    print(f"✓ Orchestrator initialized")
    
    # 9. Define a sample loop
    loop_def = LoopDefinition(
        id="example-loop-001",
        description="Example loop for demonstration",
        discovery_task="Find and analyze sample issues",
        verification_criteria={"tests_pass": True, "lint_clean": True},
        max_retries=3,
        timeout_seconds=300
    )
    print(f"✓ Loop defined: {loop_def.id}")
    
    # 10. Add automation trigger
    automation_id = scheduler.add_cron_trigger(
        loop_id=loop_def.id,
        cron_expr="0 9 * * *",  # Daily at 9 AM
        cooldown=3600
    )
    print(f"✓ Automation scheduled: {automation_id}")
    
    # 11. Create a sample skill
    from docs.skills import SKILL_TEMPLATES
    sample_skill = skills_engine.create_skill_from_template(
        SKILL_TEMPLATES["code_review"]
    )
    print(f"✓ Sample skill created: {sample_skill.name}")
    
    # 12. List available agent types
    agent_types = await agent_registry.get_available_agents()
    print(f"✓ Available agent types: {[a['type'] for a in agent_types]}")
    
    # 13. Save initial state
    await memory.save_state(loop_def.id, {
        "status": "initialized",
        "created_at": "2024-01-01T00:00:00",
        "metadata": {"example": True}
    })
    print(f"✓ Initial state saved")
    
    # 14. Load state back
    state = await memory.load_state(loop_def.id)
    print(f"✓ State loaded: {state.get('status', 'unknown')}")
    
    print("\n" + "=" * 50)
    print("✓ All components initialized successfully!")
    print("\nNext steps:")
    print("1. Implement production storage backends")
    print("2. Add real AI model integrations")
    print("3. Configure external tool plugins")
    print("4. Set up monitoring and logging")
    print("5. Deploy to production environment")

if __name__ == "__main__":
    asyncio.run(main())
