
import os
import time
import platform
import numpy as np
from numba import njit, prange, set_num_threads, get_num_threads

STUDENT_ID = 230107064

SIZES = [100, 1_000, 10_000, 100_000, 1_000_000, 10_000_000]
A = 2.5
B = 1.75
REPEATS = 7


@njit
def serial_vector(x, y, a, b):
    for i in range(x.size):
        y[i] = a * x[i] + b


@njit(parallel=True)
def parallel_vector(x, y, a, b):
    for i in prange(x.size):
        y[i] = a * x[i] + b


def measure(function, x, y):
    times = []

    for _ in range(REPEATS):
        start = time.perf_counter()
        function(x, y, A, B)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)

    return min(times)


def main():
    available_cores = os.cpu_count() or 1
    set_num_threads(min(available_cores, 64))
    used_threads = get_num_threads()

    print("=== TASK 5: OVERHEAD CROSSOVER POINT ===")
    print(f"Student ID: {STUDENT_ID}")
    print(f"OS: {platform.platform()}")
    print(f"CPU: {platform.processor() or platform.machine()}")
    print(f"Available logical cores: {available_cores}")
    print(f"Parallel threads: {used_threads}")
    print(f"Operation: y[i] = {A} * x[i] + {B}")
    print(f"Repeats per method: {REPEATS}")
    print("Timing method: minimum wall-clock time")
    print()

    # Compile functions before measurements
    warm_x = np.ones(100, dtype=np.float64)
    warm_y = np.empty_like(warm_x)

    serial_vector(warm_x, warm_y, A, B)
    parallel_vector(warm_x, warm_y, A, B)

    results = []

    print(
        f"{'N':>12} "
        f"{'Serial (ms)':>15} "
        f"{'Parallel (ms)':>17} "
        f"{'Speedup':>12} "
        f"{'Faster':>12}"
    )
    print("-" * 75)

    for n in SIZES:
        rng = np.random.default_rng(STUDENT_ID)
        x = rng.random(n, dtype=np.float64)
        y_serial = np.empty_like(x)
        y_parallel = np.empty_like(x)

        serial_ms = measure(serial_vector, x, y_serial)
        parallel_ms = measure(parallel_vector, x, y_parallel)

        if not np.allclose(y_serial, y_parallel):
            raise RuntimeError(f"Incorrect parallel result at N={n}")

        speedup = serial_ms / parallel_ms
        faster = "PARALLEL" if speedup > 1 else "SERIAL"

        results.append((n, serial_ms, parallel_ms, speedup))

        print(
            f"{n:>12,} "
            f"{serial_ms:>15.6f} "
            f"{parallel_ms:>17.6f} "
            f"{speedup:>12.4f} "
            f"{faster:>12}"
        )

    print()
    print("=== CROSSOVER ANALYSIS ===")

    transitions = []

    for i in range(1, len(results)):
        previous_n, _, _, previous_speedup = results[i - 1]
        current_n, _, _, current_speedup = results[i]

        if previous_speedup <= 1 and current_speedup > 1:
            transitions.append((previous_n, current_n))

    if transitions:
        for low, high in transitions:
            print(
                f"Observed crossover range: "
                f"{low:,} < N <= {high:,}"
            )
    else:
        print("No slower-to-faster crossover detected in tested sizes.")

    print()
    print("=== TASK 5 COMPLETED ===")


if __name__ == "__main__":
    main()
