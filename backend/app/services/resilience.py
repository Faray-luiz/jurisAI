import time
import random
import functools
from typing import Callable, Any, Dict, Optional

class ProviderCircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = "CLOSED"  # "CLOSED", "OPEN", "HALF-OPEN"
        self.failure_count = 0
        self.last_state_change = time.time()

    def record_success(self):
        if self.state != "CLOSED":
            print(f"[CircuitBreaker-{self.name}] State transitioned from {self.state} to CLOSED.")
            self.state = "CLOSED"
        self.failure_count = 0

    def record_failure(self):
        self.failure_count += 1
        print(f"[CircuitBreaker-{self.name}] Recorded failure #{self.failure_count}.")
        if self.state == "CLOSED" and self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.last_state_change = time.time()
            print(f"[CircuitBreaker-{self.name}] State transitioned from CLOSED to OPEN. Breaker will remain open for {self.recovery_timeout} seconds.")
        elif self.state == "HALF-OPEN" or self.state == "OPEN":
            self.state = "OPEN"
            self.last_state_change = time.time()
            print(f"[CircuitBreaker-{self.name}] HALF-OPEN test or subsequent call failed. State transitioned back to OPEN.")

    def allow_request(self) -> bool:
        if self.state == "CLOSED":
            return True
        
        now = time.time()
        if self.state == "OPEN":
            if now - self.last_state_change >= self.recovery_timeout:
                self.state = "HALF-OPEN"
                self.last_state_change = now
                print(f"[CircuitBreaker-{self.name}] Recovery timeout elapsed. State transitioned to HALF-OPEN. Testing next request.")
                return True
            return False
            
        if self.state == "HALF-OPEN":
            return True
            
        return False

# Global registry of breakers
_breakers: Dict[str, ProviderCircuitBreaker] = {}

def get_breaker(provider_name: str) -> ProviderCircuitBreaker:
    if provider_name not in _breakers:
        _breakers[provider_name] = ProviderCircuitBreaker(provider_name)
    return _breakers[provider_name]

def execute_with_retry_and_breaker(provider_name: str, max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator/wrapper that enforces Circuit Breaker checks and implements 
    Exponential Backoff with random jitter.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            breaker = get_breaker(provider_name)
            
            if not breaker.allow_request():
                raise RuntimeError(f"Circuit breaker for provider '{provider_name}' is OPEN. Request blocked.")
                
            delay = base_delay
            for attempt in range(max_retries):
                try:
                    res = func(*args, **kwargs)
                    breaker.record_success()
                    return res
                except Exception as e:
                    print(f"[Resilience-{provider_name}] Attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        breaker.record_failure()
                        raise e
                    
                    jitter = random.uniform(0, 0.1 * delay)  # Keep jitter reasonably bounded
                    sleep_time = delay + jitter
                    print(f"[Resilience-{provider_name}] Sleeping for {sleep_time:.2f}s before retrying...")
                    time.sleep(sleep_time)
                    delay *= 2
            
        return wrapper
    return decorator
