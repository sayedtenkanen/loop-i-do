# Loop Engineering Configuration Schema

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from enum import Enum

class StorageBackend(str, Enum):
    SQLITE = "sqlite"
    REDIS = "redis"
    POSTGRESQL = "postgresql"
    JSON = "json"

class SchedulerBackend(str, Enum):
    APSCHEDULER = "apscheduler"
    CELERY = "celery"
    CRON = "cron"

class AgentConfig(BaseModel):
    model: str = Field(default="gpt-4", description="LLM model to use")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, ge=1)
    timeout: int = Field(default=300, ge=1)
    retry_attempts: int = Field(default=3, ge=0)
    tools: List[str] = Field(default_factory=list)

class OrchestratorConfig(BaseModel):
    max_concurrent_loops: int = Field(default=5, ge=1)
    default_timeout: int = Field(default=3600, ge=1)
    retry_attempts: int = Field(default=3, ge=0)
    enable_monitoring: bool = True
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

class MemoryConfig(BaseModel):
    backend: StorageBackend = StorageBackend.SQLITE
    connection_string: str = "sqlite:///loop_state.db"
    cache_ttl: int = Field(default=300, ge=0)
    backup_enabled: bool = True
    backup_interval: int = Field(default=3600, ge=0)

class SchedulerConfig(BaseModel):
    backend: SchedulerBackend = SchedulerBackend.APSCHEDULER
    max_workers: int = Field(default=10, ge=1)
    check_interval: int = Field(default=60, ge=1)
    enable_event_triggers: bool = True

class AgentsConfig(BaseModel):
    explorer: AgentConfig = Field(default_factory=lambda: AgentConfig(
        model="gpt-4-mini",
        temperature=0.1,
        max_tokens=1000,
        tools=["read_file", "search_code", "analyze_dependencies"]
    ))
    implementer: AgentConfig = Field(default_factory=lambda: AgentConfig(
        model="gpt-4",
        temperature=0.3,
        max_tokens=4000,
        tools=["write_file", "edit_file", "run_tests", "create_commit"]
    ))
    verifier: AgentConfig = Field(default_factory=lambda: AgentConfig(
        model="gpt-4",
        temperature=0.0,
        max_tokens=2000,
        tools=["run_tests", "lint_code", "check_security", "verify_dependencies"]
    ))
    triage: AgentConfig = Field(default_factory=lambda: AgentConfig(
        model="gpt-4-mini",
        temperature=0.2,
        max_tokens=1000,
        tools=["read_issues", "analyze_logs", "classify_priority"]
    ))

class WorktreeConfig(BaseModel):
    base_path: str = "./worktrees"
    auto_cleanup: bool = True
    max_age_hours: int = Field(default=24, ge=1)
    max_concurrent: int = Field(default=10, ge=1)
    cleanup_interval: int = Field(default=3600, ge=0)

class PluginConfig(BaseModel):
    directory: str = "./plugins"
    enabled: List[str] = Field(default_factory=lambda: ["github", "linear", "slack"])
    auto_load: bool = True
    hot_reload: bool = False

class SkillsConfig(BaseModel):
    directory: str = "./skills"
    auto_discover: bool = True
    cache_skills: bool = True
    max_skill_size: int = Field(default=1048576, ge=1)

class MonitoringConfig(BaseModel):
    enable_metrics: bool = True
    metrics_port: int = Field(default=9090, ge=1024, le=65535)
    enable_tracing: bool = True
    trace_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    enable_logging: bool = True
    log_format: str = Field(default="json", pattern="^(json|text)$")

class SecurityConfig(BaseModel):
    enable_secrets_management: bool = True
    secrets_backend: str = Field(default="env", pattern="^(env|vault|aws)$")
    enable_audit_logging: bool = True
    max_concurrent_agents: int = Field(default=20, ge=1)

class PerformanceConfig(BaseModel):
    enable_connection_pooling: bool = True
    max_pool_size: int = Field(default=20, ge=1)
    enable_caching: bool = True
    cache_backend: str = Field(default="redis", pattern="^(redis|memcached|local)$")
    cache_connection_string: str = "redis://localhost:6379"

class DevelopmentConfig(BaseModel):
    debug_mode: bool = False
    enable_profiling: bool = False
    profiling_output: str = "./profiles"
    enable_hot_reloading: bool = False

class LoopConfig(BaseModel):
    """Main configuration schema for loop engineering system"""
    orchestration: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    worktrees: WorktreeConfig = Field(default_factory=WorktreeConfig)
    plugins: PluginConfig = Field(default_factory=PluginConfig)
    skills: SkillsConfig = Field(default_factory=SkillsConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    development: DevelopmentConfig = Field(default_factory=DevelopmentConfig)

# Validation helpers
def validate_config(config_dict: Dict[str, Any]) -> LoopConfig:
    """Validate configuration dictionary and return LoopConfig"""
    try:
        return LoopConfig(**config_dict)
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}")

def get_default_config() -> Dict[str, Any]:
    """Get default configuration as dictionary"""
    config = LoopConfig()
    return config.dict()

# Environment variable mapping
ENV_VAR_MAPPING = {
    "LOOP_ORCHESTRATION_MAX_CONCURRENT": ("orchestration", "max_concurrent_loops", int),
    "LOOP_ORCHESTRATION_TIMEOUT": ("orchestration", "default_timeout", int),
    "LOOP_MEMORY_BACKEND": ("memory", "backend", str),
    "LOOP_MEMORY_CONNECTION": ("memory", "connection_string", str),
    "LOOP_SCHEDULER_BACKEND": ("scheduler", "backend", str),
    "LOOP_AGENTS_EXPLORER_MODEL": ("agents", "explorer", "model", str),
    "LOOP_AGENTS_IMPLEMENTER_MODEL": ("agents", "implementer", "model", str),
    "LOOP_AGENTS_VERIFIER_MODEL": ("agents", "verifier", "model", str),
    "LOOP_WORKTREES_BASE_PATH": ("worktrees", "base_path", str),
    "LOOP_PLUGINS_DIRECTORY": ("plugins", "directory", str),
    "LOOP_SKILLS_DIRECTORY": ("skills", "directory", str),
    "LOOP_MONITORING_METRICS_PORT": ("monitoring", "metrics_port", int),
    "LOOP_SECURITY_MAX_CONCURRENT": ("security", "max_concurrent_agents", int),
    "LOOP_DEVELOPMENT_DEBUG": ("development", "debug_mode", bool),
}

def load_config_from_env(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Load configuration from environment variables"""
    import os
    
    for env_var, path in ENV_VAR_MAPPING.items():
        value = os.getenv(env_var)
        if value is not None:
            # Apply environment variable to config
            current = config_dict
            for key in path[:-2]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Convert type
            target_type = path[-1]
            if target_type == bool:
                value = value.lower() in ('true', '1', 'yes')
            elif target_type == int:
                value = int(value)
            elif target_type == float:
                value = float(value)
            
            current[path[-2]] = value
    
    return config_dict

# Example configuration validation
if __name__ == "__main__":
    # Example usage
    config_dict = get_default_config()
    
    # Modify some values
    config_dict["orchestration"]["max_concurrent_loops"] = 10
    config_dict["agents"]["explorer"]["model"] = "gpt-4-turbo"
    
    # Validate
    config = validate_config(config_dict)
    print("Configuration validated successfully!")
    print(f"Max concurrent loops: {config.orchestration.max_concurrent_loops}")
    print(f"Explorer model: {config.agents.explorer.model}")
