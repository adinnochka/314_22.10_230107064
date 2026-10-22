
import os
import platform
import time
import numpy as np
from concurrent.futures import ProcessPoolExecutor

STUDENT_ID = 230107064
N = 20_000_000
P = 0.95


def partial_sum(chunk):
    total = 0.0
    for value in chunk:
        total += float(value)
    return total


def parallel_sum(data, workers):
    chunks = np.array_split(data, workers)

    with ProcessPoolExecutor(max_workers=workers) as executor:
        partial_results = executor.map(partial_sum, chunks)
        return sum(partial_results)


def main():
    max_cores = os.cpu_count() or 1
    worker_counts = list(dict.fromkeys([1, 2, 4, max_cores, max_cores * 2]))

    rng = np.random.default_rng(STUDENT_ID)
    data = rng.random(N, dtype=np.float64)

    print("=== TASK 2: MULTI-CORE SCALING VS AMDAHL'S LAW ===")
    print(f"Student ID: {STUDENT_ID}")
    print(f"OS: {platform.platform()}")
    print(f"CPU: {platform.processor() or platform.machine()}")
    print(f"Logical cores: {max_cores}")
    print(f"Array size: {N}")
    print(f"Parallel fraction P: {P}")
    print()

    print(f"{'Cores':<10} {'Wall Time (ms)':<18} {'Speedup':<12} {'Amdahl Upper Bound':<20}")
    print("-" * 65)

    baseline_time = None

    for workers in worker_counts:
        start = time.perf_counter()

        if workers == 1:
            result = partial_sum(data)
        else:
            result = parallel_sum(data, workers)

        elapsed_ms = (time.perf_counter() - start) * 1000

        if baseline_time is None:
            baseline_time = elapsed_ms

        speedup = baseline_time / elapsed_ms

        amdahl = 1 / ((1 - P) + P / workers)

        print(
            f"{workers:<10} "
            f"{elapsed_ms:<18.3f} "
            f"{speedup:<12.4f} "
            f"{amdahl:<20.4f}"
        )

        print(f"  Sum check: {result:.6f}")

    print()
    print("=== TASK 2 COMPLETED ===")


if __name__ == "__main__":
    main()
