"""
Memory profiling utilities.

Usage:
    python -m memory_profiler optimization/memory_profiler.py
"""
import sys
import gc
import tracemalloc
from typing import Any, Callable
from functools import wraps


class MemoryProfiler:
    """Memory profiling utility."""

    def __init__(self):
        self.snapshots = []

    def start(self):
        """Start memory profiling."""
        tracemalloc.start()

    def stop(self):
        """Stop memory profiling."""
        tracemalloc.stop()

    def take_snapshot(self, label: str = ""):
        """Take a memory snapshot."""
        snapshot = tracemalloc.take_snapshot()
        self.snapshots.append((label, snapshot))
        return snapshot

    def compare_snapshots(self, snapshot1_idx: int = 0, snapshot2_idx: int = 1):
        """Compare two snapshots to find memory growth."""
        if len(self.snapshots) < 2:
            print("Need at least 2 snapshots to compare")
            return

        label1, snapshot1 = self.snapshots[snapshot1_idx]
        label2, snapshot2 = self.snapshots[snapshot2_idx]

        print(f"\nMemory Growth: {label1} -> {label2}")
        print("=" * 80)

        top_stats = snapshot2.compare_to(snapshot1, 'lineno')

        for stat in top_stats[:10]:
            print(stat)

    def get_current_memory_usage(self) -> dict:
        """Get current memory usage."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()

        return {
            "rss_mb": mem_info.rss / 1024 / 1024,  # Resident Set Size
            "vms_mb": mem_info.vms / 1024 / 1024,  # Virtual Memory Size
            "percent": process.memory_percent()
        }

    def print_top_allocations(self, limit: int = 10):
        """Print top memory allocations."""
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')

        print(f"\nTop {limit} Memory Allocations:")
        print("=" * 80)

        for stat in top_stats[:limit]:
            print(f"{stat.size / 1024:.1f} KB - {stat.traceback}")


def profile_memory(func: Callable) -> Callable:
    """
    Decorator to profile memory usage of a function.

    Example:
        @profile_memory
        def memory_intensive_function():
            large_list = [0] * 1000000
            return large_list
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get initial memory
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        # Run function
        result = func(*args, **kwargs)

        # Get final memory
        snapshot2 = tracemalloc.take_snapshot()

        # Compare
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')

        print(f"\nMemory profile for {func.__name__}:")
        print("=" * 80)
        for stat in top_stats[:5]:
            print(stat)

        tracemalloc.stop()

        return result

    return wrapper


# Example memory-intensive functions to profile
@profile_memory
def process_large_file():
    """Example function that processes large data."""
    # Simulate processing large file
    large_data = []
    for i in range(100000):
        large_data.append({
            "id": i,
            "voltage": 35.2 + i * 0.001,
            "current": 8.5 + i * 0.0001,
            "power": 299.2 + i * 0.01
        })

    # Process data
    total = sum(d["power"] for d in large_data)

    # Cleanup
    del large_data
    gc.collect()

    return total


@profile_memory
def generate_report():
    """Example function that generates report."""
    # Simulate report generation
    report_data = {
        "title": "Test Report",
        "measurements": [{"v": i, "c": i*0.1} for i in range(10000)],
        "metadata": {"generated_at": "2024-01-15"}
    }

    # Process report
    result = len(str(report_data))

    return result


def analyze_memory_leaks():
    """Analyze potential memory leaks."""
    print("\nAnalyzing Memory Leaks...")
    print("=" * 80)

    profiler = MemoryProfiler()
    profiler.start()

    # Take initial snapshot
    profiler.take_snapshot("Initial")

    # Simulate operations that might leak memory
    leaked_objects = []
    for i in range(100):
        # This would leak if we don't clean up
        data = [0] * 10000
        leaked_objects.append(data)

    profiler.take_snapshot("After allocations")

    # Compare snapshots
    profiler.compare_snapshots(0, 1)

    # Cleanup
    leaked_objects.clear()
    gc.collect()

    profiler.take_snapshot("After cleanup")
    profiler.compare_snapshots(1, 2)

    profiler.stop()


def monitor_memory_during_operation():
    """Monitor memory usage during operation."""
    import time
    import psutil
    import os

    process = psutil.Process(os.getpid())

    print("\nMonitoring Memory During Operation...")
    print("=" * 80)
    print(f"{'Time':>8} {'RSS (MB)':>12} {'VMS (MB)':>12} {'Percent':>10}")
    print("-" * 80)

    for i in range(5):
        # Simulate some work
        temp_data = [0] * (100000 * (i + 1))

        mem_info = process.memory_info()
        rss_mb = mem_info.rss / 1024 / 1024
        vms_mb = mem_info.vms / 1024 / 1024
        percent = process.memory_percent()

        print(f"{i:>8} {rss_mb:>12.2f} {vms_mb:>12.2f} {percent:>9.2f}%")

        time.sleep(0.5)
        del temp_data


def main():
    """Run memory profiling examples."""
    print("MEMORY PROFILING REPORT")
    print("=" * 80)

    # Example 1: Profile functions
    print("\n1. Processing large file...")
    process_large_file()

    print("\n2. Generating report...")
    generate_report()

    # Example 2: Analyze memory leaks
    print("\n3. Analyzing memory leaks...")
    analyze_memory_leaks()

    # Example 3: Monitor memory during operation
    print("\n4. Monitoring memory...")
    monitor_memory_during_operation()

    # Print final memory usage
    profiler = MemoryProfiler()
    current_memory = profiler.get_current_memory_usage()
    print("\nFinal Memory Usage:")
    print("=" * 80)
    print(f"RSS: {current_memory['rss_mb']:.2f} MB")
    print(f"VMS: {current_memory['vms_mb']:.2f} MB")
    print(f"Percent: {current_memory['percent']:.2f}%")


if __name__ == "__main__":
    main()
