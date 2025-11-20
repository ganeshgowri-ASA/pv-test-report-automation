"""
Performance profiling script for PV Test Report Automation.

Usage:
    python optimization/profile_performance.py --module src.ingestion.excel_parser
    python optimization/profile_performance.py --function parse_excel --iterations 100
"""
import cProfile
import pstats
import io
import argparse
import time
from pathlib import Path
import sys
from typing import Callable, Any


class PerformanceProfiler:
    """Performance profiling utility."""

    def __init__(self, output_dir: str = "optimization/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def profile_function(self, func: Callable, *args, **kwargs) -> dict:
        """
        Profile a function's performance.

        Args:
            func: Function to profile
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Dictionary with profiling results
        """
        profiler = cProfile.Profile()

        # Profile the function
        start_time = time.time()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        end_time = time.time()

        # Get statistics
        stats_io = io.StringIO()
        stats = pstats.Stats(profiler, stream=stats_io)
        stats.sort_stats('cumulative')
        stats.print_stats(20)  # Top 20 functions

        return {
            "duration": end_time - start_time,
            "result": result,
            "stats": stats_io.getvalue()
        }

    def profile_module(self, module_name: str):
        """
        Profile an entire module.

        Args:
            module_name: Name of module to profile
        """
        profiler = cProfile.Profile()

        # Import and profile module
        profiler.enable()
        __import__(module_name)
        profiler.disable()

        # Save results
        output_file = self.output_dir / f"{module_name.replace('.', '_')}_profile.txt"
        with open(output_file, 'w') as f:
            stats = pstats.Stats(profiler, stream=f)
            stats.sort_stats('cumulative')
            stats.print_stats()

        print(f"Profile saved to: {output_file}")

    def benchmark_function(self, func: Callable, iterations: int = 100,
                          *args, **kwargs) -> dict:
        """
        Benchmark a function over multiple iterations.

        Args:
            func: Function to benchmark
            iterations: Number of iterations
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Dictionary with benchmark results
        """
        durations = []

        for _ in range(iterations):
            start_time = time.time()
            func(*args, **kwargs)
            end_time = time.time()
            durations.append(end_time - start_time)

        return {
            "iterations": iterations,
            "min": min(durations),
            "max": max(durations),
            "mean": sum(durations) / len(durations),
            "total": sum(durations)
        }

    def profile_with_line_profiler(self, func: Callable):
        """
        Profile function line-by-line (requires line_profiler package).

        Args:
            func: Function to profile
        """
        try:
            from line_profiler import LineProfiler

            profiler = LineProfiler()
            profiler.add_function(func)
            profiler.enable()
            func()
            profiler.disable()
            profiler.print_stats()
        except ImportError:
            print("line_profiler not installed. Install with: pip install line_profiler")


def profile_database_queries():
    """Profile database query performance."""
    print("Profiling database queries...")

    # Example queries to profile
    queries = [
        "SELECT * FROM reports WHERE created_at > NOW() - INTERVAL '7 days'",
        "SELECT COUNT(*) FROM reports GROUP BY standard",
        "SELECT * FROM equipment WHERE calibration_date < NOW()"
    ]

    for query in queries:
        start = time.time()
        # Execute query (placeholder)
        time.sleep(0.01)  # Simulate query execution
        duration = time.time() - start
        print(f"Query: {query[:50]}... took {duration*1000:.2f}ms")


def profile_file_processing():
    """Profile file processing performance."""
    print("Profiling file processing...")

    file_sizes = [1, 10, 50, 100]  # MB
    for size in file_sizes:
        start = time.time()
        # Simulate file processing
        time.sleep(size * 0.01)
        duration = time.time() - start
        print(f"Processing {size}MB file took {duration:.2f}s")


def profile_report_generation():
    """Profile report generation performance."""
    print("Profiling report generation...")

    report_types = ["simple", "standard", "comprehensive"]
    for report_type in report_types:
        start = time.time()
        # Simulate report generation
        time.sleep(0.5 if report_type == "simple" else 1.5)
        duration = time.time() - start
        print(f"Generating {report_type} report took {duration:.2f}s")


def main():
    """Main entry point for profiling script."""
    parser = argparse.ArgumentParser(description="Profile application performance")
    parser.add_argument("--module", help="Module to profile")
    parser.add_argument("--function", help="Function to profile")
    parser.add_argument("--iterations", type=int, default=100,
                       help="Number of iterations for benchmarking")
    parser.add_argument("--database", action="store_true",
                       help="Profile database queries")
    parser.add_argument("--files", action="store_true",
                       help="Profile file processing")
    parser.add_argument("--reports", action="store_true",
                       help="Profile report generation")

    args = parser.parse_args()

    profiler = PerformanceProfiler()

    if args.module:
        profiler.profile_module(args.module)
    elif args.database:
        profile_database_queries()
    elif args.files:
        profile_file_processing()
    elif args.reports:
        profile_report_generation()
    else:
        print("Running all profiling tasks...")
        profile_database_queries()
        profile_file_processing()
        profile_report_generation()


if __name__ == "__main__":
    main()
