import psutil
import time
from typing import Dict

class SystemMetrics:
    @staticmethod
    def collect() -> Dict:
        """Collect system-level metrics"""
        return {
            "timestamp": time.time(),
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent
        }

def track_latency(func):
    """Decorator to track function latency"""
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        latency = time.perf_counter() - start
        return {
            "result": result,
            "latency_ms": latency * 1000
        }
    return wrapper