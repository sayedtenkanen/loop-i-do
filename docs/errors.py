# Loop Engineering Architecture - Structured Error Types

## Purpose
Define error hierarchy for better error handling, logging, and debugging.

```python
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCode(Enum):
    # Loop errors (1xxx)
    LOOP_TIMEOUT = 1001
    LOOP_MAX_RETRIES = 1002
    LOOP_STATE_CORRUPTED = 1003
    LOOP_CANCELED = 1004
    
    # Agent errors (2xxx)
    AGENT_TIMEOUT = 2001
    AGENT_RATE_LIMITED = 2002
    AGENT_MODEL_ERROR = 2003
    AGENT_INVALID_RESPONSE = 2004
    AGENT_CONTEXT_TOO_LONG = 2005
    
    # Worktree errors (3xxx)
    WORKTREE_CREATE_FAILED = 3001
    WORKTREE_MERGE_CONFLICT = 3002
    WORKTREE_TIMEOUT = 3003
    WORKTREE_LOCK_FAILED = 3004
    
    # Validation errors (4xxx)
    VALIDATION_FAILED = 4001
    TESTS_FAILED = 4002
    LINT_FAILED = 4003
    SECURITY_FAILED = 4004
    TYPE_CHECK_FAILED = 4005
    
    # Plugin errors (5xxx)
    PLUGIN_NOT_FOUND = 5001
    PLUGIN_CONNECTION_FAILED = 5002
    PLUGIN_TIMEOUT = 5003
    PLUGIN_AUTH_FAILED = 5004
    
    # Memory errors (6xxx)
    MEMORY_READ_FAILED = 6001
    MEMORY_WRITE_FAILED = 6002
    MEMORY_CORRUPTED = 6003
    
    # Token errors (7xxx)
    TOKEN_BUDGET_EXCEEDED = 7001
    TOKEN_LIMIT_EXCEEDED = 7002

@dataclass
class LoopError(Exception):
    """Base exception for loop engineering system"""
    error_code: ErrorCode
    message: str
    severity: ErrorSeverity
    component: str
    context: Dict[str, Any] = None
    timestamp: datetime = None
    recoverable: bool = True
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "severity": self.severity.value,
            "component": self.component,
            "context": self.context or {},
            "timestamp": self.timestamp.isoformat(),
            "recoverable": self.recoverable
        }

@dataclass
class AgentError(LoopError):
    """Error in agent execution"""
    agent_id: str = None
    agent_type: str = None
    model: str = None
    tokens_used: int = 0
    
    def __post_init__(self):
        self.component = "agent"
        super().__post_init__()

@dataclass
class ValidationError(LoopError):
    """Error in validation phase"""
    validation_type: str = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        self.component = "validator"
        super().__post_init__()

@dataclass
class WorktreeError(LoopError):
    """Error in worktree operations"""
    task_id: str = None
    worktree_path: str = None
    
    def __post_init__(self):
        self.component = "worktree"
        super().__post_init__()

@dataclass
class PluginError(LoopError):
    """Error in plugin operations"""
    plugin_name: str = None
    action: str = None
    
    def __post_init__(self):
        self.component = "plugin"
        super().__post_init__()

@dataclass
class MemoryError(LoopError):
    """Error in memory/state operations"""
    operation: str = None
    
    def __post_init__(self):
        self.component = "memory"
        super().__post_init__()

@dataclass
class TokenBudgetExceeded(LoopError):
    """Token budget exceeded"""
    budget_type: str = None  # run, loop, daily
    current_tokens: int = 0
    max_tokens: int = 0
    
    def __post_init__(self):
        self.error_code = ErrorCode.TOKEN_BUDGET_EXCEEDED
        self.severity = ErrorSeverity.HIGH
        self.component = "token_tracker"
        self.recoverable = False
        super().__post_init__()

# ============================================================
# Error Factory
# ============================================================

class ErrorFactory:
    """Factory for creating structured errors"""
    
    @staticmethod
    def agent_timeout(agent_id: str, timeout: int) -> AgentError:
        return AgentError(
            error_code=ErrorCode.AGENT_TIMEOUT,
            message=f"Agent {agent_id} timed out after {timeout}s",
            severity=ErrorSeverity.HIGH,
            agent_id=agent_id,
            context={"timeout": timeout}
        )
    
    @staticmethod
    def validation_failed(validation_type: str, details: Dict) -> ValidationError:
        return ValidationError(
            error_code=ErrorCode.VALIDATION_FAILED,
            message=f"Validation failed: {validation_type}",
            severity=ErrorSeverity.MEDIUM,
            validation_type=validation_type,
            details=details
        )
    
    @staticmethod
    def tests_failed(failures: int, errors: int) -> ValidationError:
        return ValidationError(
            error_code=ErrorCode.TESTS_FAILED,
            message=f"Tests failed: {failures} failures, {errors} errors",
            severity=ErrorSeverity.HIGH,
            validation_type="tests",
            details={"failures": failures, "errors": errors}
        )
    
    @staticmethod
    def plugin_connection_failed(plugin_name: str, error: str) -> PluginError:
        return PluginError(
            error_code=ErrorCode.PLUGIN_CONNECTION_FAILED,
            message=f"Plugin {plugin_name} connection failed: {error}",
            severity=ErrorSeverity.MEDIUM,
            plugin_name=plugin_name,
            recoverable=True
        )
    
    @staticmethod
    def worktree_merge_conflict(task_id: str, files: list) -> WorktreeError:
        return WorktreeError(
            error_code=ErrorCode.WORKTREE_MERGE_CONFLICT,
            message=f"Merge conflict for task {task_id} in files: {files}",
            severity=ErrorSeverity.HIGH,
            task_id=task_id,
            context={"conflicting_files": files}
        )
    
    @staticmethod
    def token_budget_exceeded(budget_type: str, current: int, max_tokens: int) -> TokenBudgetExceeded:
        return TokenBudgetExceeded(
            message=f"Token budget exceeded ({budget_type}): {current}/{max_tokens}",
            budget_type=budget_type,
            current_tokens=current,
            max_tokens=max_tokens
        )
```

## Usage Examples

```python
from errors import ErrorFactory, LoopError

# Create specific errors
try:
    # Agent execution
    raise ErrorFactory.agent_timeout("impl-001", 300)
except AgentError as e:
    print(f"Agent error: {e.message}")
    print(f"Severity: {e.severity.value}")
    print(f"Recoverable: {e.recoverable}")

# Validation failure
error = ErrorFactory.tests_failed(failures=3, errors=1)
print(error.to_dict())

# Plugin connection
error = ErrorFactory.plugin_connection_failed("github", "Connection refused")
if error.recoverable:
    # Try fallback or continue in degraded mode
    pass
```
