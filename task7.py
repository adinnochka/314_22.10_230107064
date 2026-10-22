
import os
import time
import platform
import numpy as np
from numba import njit, prange, set_num_threads

STUDENT_ID = 230107064
N = 30_000_000
REPEATS = 5


@njit(parallel=True)
def memory_kernel(a, b):
    for i in prange(a.size):
        b[i] = a[i]


@njit(parallel=True)
def compute_kernel(a, b):
    for i in prange(a.size):
        b[i] = (
            np.sin(a[i]) * np.cos(a[i])
            + np.tan(a[i])
        )


def benchmark(kernel, a, b, threads):
    set_num_threads(threads)
    times = []

    for _ in range(REPEATS):
        start = time.perf_counter()
        kernel(a, b)
        elapsed_ms = (time.perf_counter() - start) * 1000
        times.append(elapsed_ms)

    return min(times)


def main():
    max_cores = os.cpu_count() or 1
    counts = list(dict.fromkeys([1, 2, max_cores]))

    print("=== TASK 7: ARITHMETIC INTENSITY VS MEMORY ===")
    print(f"Student ID: {STUDENT_ID}")
    print(f"OS: {platform.platform()}")
    print(f"CPU: {platform.processor() or platform.machine()}")
    print(f"Logical cores: {max_cores}")
    print(f"Array size: {N:,} float64 elements")
    print(f"Repeats: {REPEATS}")
    print()

    rng = np.random.default_rng(STUDENT_ID)
    a = rng.random(N, dtype=np.float64)
    b = np.empty_like(a)

    # Compile both kernels before benchmarking
    set_num_threads(1)
    memory_kernel(a[:100], b[:100])
    compute_kernel(a[:100], b[:100])

    results = {}

    for name, kernel in [
        ("Memory-Bound", memory_kernel),
        ("Compute-Bound", compute_kernel)
    ]:
        print(f"--- {name} ---")
        print(
            f"{'Cores':>8} "
            f"{'Time (ms)':>14} "
            f"{'Speedup':>12} "
            f"{'Efficiency':>14}"
        )
        print("-" * 54)

        baseline = None
        results[name] = {}

        for threads in counts:
            elapsed = benchmark(kernel, a, b, threads)

            if baseline is None:
                baseline = elapsed

            speedup = baseline / elapsed
            efficiency = speedup / threads

            results[name][threads] = (
                elapsed, speedup, efficiency
            )

            print(
                f"{threads:>8} "
                f"{elapsed:>14.3f} "
                f"{speedup:>12.4f} "
                f"{efficiency:>14.4f}"
            )

        print()

    memory_eff = results["Memory-Bound"][max_cores][2]
    compute_eff = results["Compute-Bound"][max_cores][2]

    print("=== SCALING ANALYSIS ===")
    print(f"Memory kernel efficiency: {memory_eff:.4f}")
    print(f"Compute kernel efficiency: {compute_eff:.4f}")

    if memory_eff < compute_eff:
        print(
            "Memory-Bound kernel stalled more strongly "
            "in scaling, consistent with memory bandwidth saturation."
        )
    elif memory_eff > compute_eff:
        print(
            "Compute-Bound kernel scaled less efficiently. "
            "Memory bandwidth saturation was not established "
            "by this comparison."
        )
    else:
        print(
            "Both kernels showed equal scaling efficiency. "
            "Memory bandwidth saturation was not established."
        )

    print()
    print("=== TASK 7 COMPLETED ===")


if __name__ == "__main__":
    main()
