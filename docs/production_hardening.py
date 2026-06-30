# Loop Engineering Architecture - Production Hardening

## Purpose
Circuit breaker, rate limiting, dead letter queue, and health checks for production use.

```python
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import time
import json
from collections import deque

# ============================================================
# Circuit Breaker
# ============================================================

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if recovered

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5      # Failures before opening
    recovery_timeout: int = 60      # Seconds before trying again
    half_open_max_calls: int = 3    # Calls to test in half-open
    success_threshold: int = 2      # Successes to close from half-open

class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        
    def can_execute(self) -> bool:
        """Check if call is allowed"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.config.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.config.half_open_max_calls
        
        return False
    
    def record_success(self):
        """Record a successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def record_failure(self):
        """Record a failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.half_open_calls = 0
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
    
    def get_status(self) -> Dict:
        """Get circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }

# ============================================================
# Rate Limiter
# ============================================================

@dataclass
class RateLimiterConfig:
    max_calls: int = 10
    time_window: int = 60  # seconds
    burst_size: int = 5    # Allow short bursts

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, name: str, config: RateLimiterConfig = None):
        self.name = name
        self.config = config or RateLimiterConfig()
        self.tokens = self.config.burst_size
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Try to acquire a token"""
        async with self._lock:
            self._refill()
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
    
    async def wait_for_token(self, timeout: float = 30.0) -> bool:
        """Wait for a token to become available"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if await self.acquire():
                return True
            await asyncio.sleep(0.1)
        
        return False
    
    def _refill(self):
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on time elapsed
        new_tokens = elapsed * (self.config.max_calls / self.config.time_window)
        self.tokens = min(self.config.burst_size, self.tokens + new_tokens)
        self.last_refill = now
    
    def get_status(self) -> Dict:
        """Get rate limiter status"""
        return {
            "name": self.name,
            "tokens_available": int(self.tokens),
            "max_tokens": self.config.burst_size,
            "refill_rate": self.config.max_calls / self.config.time_window
        }

# ============================================================
# Dead Letter Queue
# ============================================================

@dataclass
class DeadLetter:
    """A failed task that couldn't be processed"""
    task_id: str
    loop_id: str
    error: str
    task_data: Dict
    failed_at: datetime
    retry_count: int
    max_retries: int
    queue_name: str = "default"

class DeadLetterQueue:
    """Queue for tasks that permanently failed"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.queue: deque = deque(maxlen=max_size)
        self._storage_path = None
    
    def add(self, dead_letter: DeadLetter):
        """Add a dead letter to the queue"""
        self.queue.append(dead_letter)
        
        # Also persist to disk if path configured
        if self._storage_path:
            self._persist_to_disk(dead_letter)
    
    def get(self) -> Optional[DeadLetter]:
        """Get next dead letter"""
        if self.queue:
            return self.queue.popleft()
        return None
    
    def peek(self) -> Optional[DeadLetter]:
        """peek at next dead letter without removing"""
        if self.queue:
            return self.queue[0]
        return None
    
    def size(self) -> int:
        """Get queue size"""
        return len(self.queue)
    
    def retry_all(self) -> List[DeadLetter]:
        """Get all dead letters for retry (resets retry count)"""
        letters = list(self.queue)
        self.queue.clear()
        return letters
    
    def get_by_loop(self, loop_id: str) -> List[DeadLetter]:
        """Get dead letters for a specific loop"""
        return [dl for dl in self.queue if dl.loop_id == loop_id]
    
    def clear(self):
        """Clear all dead letters"""
        self.queue.clear()
    
    def _persist_to_disk(self, dead_letter: DeadLetter):
        """Persist dead letter to disk"""
        import os
        os.makedirs(self._storage_path, exist_ok=True)
        
        filename = f"{dead_letter.loop_id}_{dead_letter.task_id}_{dead_letter.failed_at.timestamp()}.json"
        filepath = os.path.join(self._storage_path, filename)
        
        data = {
            "task_id": dead_letter.task_id,
            "loop_id": dead_letter.loop_id,
            "error": dead_letter.error,
            "task_data": dead_letter.task_data,
            "failed_at": dead_letter.failed_at.isoformat(),
            "retry_count": dead_letter.retry_count,
            "max_retries": dead_letter.max_retries,
            "queue_name": dead_letter.queue_name
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_status(self) -> Dict:
        """Get queue status"""
        return {
            "size": len(self.queue),
            "max_size": self.max_size,
            "by_loop": {}
        }

# ============================================================
# Health Check
# ============================================================

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheckResult:
    component: str
    status: HealthStatus
    message: str
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

class HealthChecker:
    """Health check system for loop components"""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.results: Dict[str, HealthCheckResult] = {}
    
    def register_check(self, component: str, check_func: Callable):
        """Register a health check function"""
        self.checks[component] = check_func
    
    async def run_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks"""
        results = {}
        
        for component, check_func in self.checks.items():
            start_time = time.time()
            try:
                result = await check_func()
                latency = (time.time() - start_time) * 1000
                
                results[component] = HealthCheckResult(
                    component=component,
                    status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                    message="OK" if result else "Check failed",
                    latency_ms=latency
                )
            except Exception as e:
                latency = (time.time() - start_time) * 1000
                results[component] = HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                    latency_ms=latency
                )
        
        self.results = results
        return results
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health"""
        if not self.results:
            return HealthStatus.UNKNOWN
        
        statuses = [r.status for r in self.results.values()]
        
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.DEGRADED
    
    def get_status_report(self) -> Dict:
        """Get detailed health report"""
        return {
            "overall": self.get_overall_status().value,
            "components": {
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "latency_ms": result.latency_ms,
                    "timestamp": result.timestamp.isoformat()
                }
                for name, result in self.results.items()
            }
        }

# ============================================================
# Retry Handler with Exponential Backoff
# ============================================================

@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

class RetryHandler:
    """Retry handler with exponential backoff"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
    
    async def execute_with_retry(self, func: Callable, *args, 
                                circuit_breaker: CircuitBreaker = None,
                                **kwargs) -> Any:
        """Execute function with retry logic"""
        import random
        
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            # Check circuit breaker
            if circuit_breaker and not circuit_breaker.can_execute():
                raise RuntimeError(f"Circuit breaker {circuit_breaker.name} is open")
            
            try:
                result = await func(*args, **kwargs)
                
                # Record success
                if circuit_breaker:
                    circuit_breaker.record_success()
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Record failure
                if circuit_breaker:
                    circuit_breaker.record_failure()
                
                # Don't retry on last attempt
                if attempt == self.config.max_retries:
                    break
                
                # Calculate delay with exponential backoff
                delay = min(
                    self.config.base_delay * (self.config.exponential_base ** attempt),
                    self.config.max_delay
                )
                
                # Add jitter
                if self.config.jitter:
                    delay *= (0.5 + random.random())
                
                await asyncio.sleep(delay)
        
        raise last_exception

# ============================================================
# Graceful Degradation Manager
# ============================================================

class GracefulDegradation:
    """Handle non-critical failures without killing the loop"""
    
    def __init__(self):
        self.failed_components: Dict[str, List[Exception]] = {}
        self.degraded_mode = False
    
    async def execute_with_fallback(self, component: str, 
                                   primary_func: Callable,
                                   fallback_func: Callable = None,
                                   *args, **kwargs) -> Any:
        """Execute with fallback for graceful degradation"""
        try:
            return await primary_func(*args, **kwargs)
        except Exception as e:
            # Log the failure
            if component not in self.failed_components:
                self.failed_components[component] = []
            self.failed_components[component].append(e)
            
            # Try fallback if available
            if fallback_func:
                try:
                    return await fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    # Both failed, enter degraded mode
                    self.degraded_mode = True
                    raise RuntimeError(
                        f"Both primary and fallback failed for {component}: "
                        f"Primary: {e}, Fallback: {fallback_error}"
                    )
            else:
                # No fallback, enter degraded mode
                self.degraded_mode = True
                raise
    
    def is_degraded(self) -> bool:
        """Check if system is in degraded mode"""
        return self.degraded_mode
    
    def get_failed_components(self) -> Dict[str, int]:
        """Get count of failures per component"""
        return {k: len(v) for k, v in self.failed_components.items()}
    
    def reset(self):
        """Reset degradation state"""
        self.failed_components.clear()
        self.degraded_mode = False

# ============================================================
# Production Hardening Bundle
# ============================================================

class ProductionHardening:
    """Bundle of production hardening components"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.dead_letter_queue = DeadLetterQueue()
        self.health_checker = HealthChecker()
        self.retry_handler = RetryHandler()
        self.degradation_manager = GracefulDegradation()
    
    def add_circuit_breaker(self, name: str, config: CircuitBreakerConfig = None):
        """Add a circuit breaker"""
        self.circuit_breakers[name] = CircuitBreaker(name, config)
    
    def add_rate_limiter(self, name: str, config: RateLimiterConfig = None):
        """Add a rate limiter"""
        self.rate_limiters[name] = RateLimiter(name, config)
    
    async def execute_protected(self, component: str, func: Callable,
                               *args, **kwargs) -> Any:
        """Execute with all protections applied"""
        # Get circuit breaker
        circuit_breaker = self.circuit_breakers.get(component)
        
        # Get rate limiter
        rate_limiter = self.rate_limiters.get(component)
        if rate_limiter:
            if not await rate_limiter.wait_for_token(timeout=30):
                raise RuntimeError(f"Rate limit exceeded for {component}")
        
        # Execute with retry and circuit breaker
        return await self.retry_handler.execute_with_retry(
            func, *args, circuit_breaker=circuit_breaker, **kwargs
        )
    
    def add_dead_letter(self, task_id: str, loop_id: str, error: str,
                       task_data: Dict, retry_count: int, max_retries: int):
        """Add a dead letter to the queue"""
        dead_letter = DeadLetter(
            task_id=task_id,
            loop_id=loop_id,
            error=error,
            task_data=task_data,
            failed_at=datetime.now(),
            retry_count=retry_count,
            max_retries=max_retries
        )
        self.dead_letter_queue.add(dead_letter)
    
    def get_status(self) -> Dict:
        """Get overall production status"""
        return {
            "circuit_breakers": {
                name: cb.get_status() 
                for name, cb in self.circuit_breakers.items()
            },
            "rate_limiters": {
                name: rl.get_status()
                for name, rl in self.rate_limiters.items()
            },
            "dead_letter_queue": self.dead_letter_queue.get_status(),
            "health": self.health_checker.get_status_report(),
            "degraded": self.degradation_manager.is_degraded(),
            "failed_components": self.degradation_manager.get_failed_components()
        }

# Example usage
if __name__ == "__main__":
    # Initialize production hardening
    hardening = ProductionHardening()
    
    # Add circuit breaker for agent calls
    hardening.add_circuit_breaker("agent_calls", CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60
    ))
    
    # Add rate limiter for LLM API
    hardening.add_rate_limiter("llm_api", RateLimiterConfig(
        max_calls=10,
        time_window=60
    ))
    
    # Register health checks
    async def check_database():
        return True  # Check DB connection
    
    async def check_redis():
        return True  # Check Redis connection
    
    hardening.health_checker.register_check("database", check_database)
    hardening.health_checker.register_check("redis", check_redis)
    
    # Run health checks
    asyncio.run(hardening.health_checker.run_checks())
    
    # Get status
    print(json.dumps(hardening.get_status(), indent=2, default=str))
