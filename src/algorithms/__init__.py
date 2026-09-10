"""Public API for the ``src.algorithms`` package.

Exports:
    DBO          : Dung Beetle Optimizer main class.
    DBOResult    : Dataclass holding the result of an optimization run.
    BenchmarkFunction : Metadata and callable wrapper for a benchmark function.
    get_benchmark    : Retrieve a BenchmarkFunction by name (case-insensitive).
    list_benchmarks  : Return the list of all registered benchmark names.
    BENCHMARKS       : Registry dict mapping name -> BenchmarkFunction.
"""
from src.algorithms.benchmarks import (
    BENCHMARKS,
    BenchmarkFunction,
    get_benchmark,
    list_benchmarks,
)
from src.algorithms.dbo import DBO, DBOResult

__all__ = [
    "DBO",
    "DBOResult",
    "BenchmarkFunction",
    "get_benchmark",
    "list_benchmarks",
    "BENCHMARKS",
]

