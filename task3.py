
import os
import time
import platform
import threading
import numpy as np
import psutil
from numba import njit

STUDENT_ID = 230107064
ITERATIONS = 50_000_000

PHYSICAL_CORES = psutil.cpu_count(logical=False)
if not PHYSICAL_CORES:
    raise RuntimeError("Cannot detect physical CPU cores")

N = PHYSICAL_CORES


@njit(nogil=True)
def unpadded_worker(shared_counts, index, iterations):
    for _ in range(iterations):
        shared_counts[index] += 1


@njit(nogil=True)
def local_worker(shared_counts, index, iterations):
    local_count = 0
    for _ in range(iterations):
        local_count += 1
    shared_counts[index] = local_count


def benchmark(worker_function):
    shared_counts = np.zeros(N, dtype=np.int64)
    barrier = threading.Barrier(N + 1)

    def worker(index):
        barrier.wait()
        worker_function(shared_counts, index, ITERATIONS)

    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(N)
    ]

    for thread in threads:
        thread.start()

    start = time.perf_counter()
    barrier.wait()

    for thread in threads:
        thread.join()

    elapsed_ms = (time.perf_counter() - start) * 1000

    expected = N * ITERATIONS
    actual = int(shared_counts.sum())

    if actual != expected:
        raise RuntimeError(
            f"Incorrect result: {actual}, expected {expected}"
        )

    return elapsed_ms, actual


def main():
    print("=== TASK 3: FALSE SHARING PROFILE ===")
    print(f"Student ID: {STUDENT_ID}")
    print(f"OS: {platform.platform()}")
    print(f"Logical cores: {os.cpu_count()}")
    print(f"Physical cores: {N}")
    print(f"Worker threads: {N}")
    print(f"Iterations per thread: {ITERATIONS:,}")
    print()

    # Compile both functions before timing
    warmup = np.zeros(N, dtype=np.int64)
    unpadded_worker(warmup, 0, 1)
    local_worker(warmup, 0, 1)

    unpadded_ms, unpadded_sum = benchmark(unpadded_worker)
    local_ms, local_sum = benchmark(local_worker)

    ratio = unpadded_ms / local_ms if local_ms > 0 else float("inf")

    print(f"{'Method':<24} {'Wall Time (ms)':>18}")
    print("-" * 44)
    print(f"{'Unpadded Shared':<24} {unpadded_ms:>18.3f}")
    print(f"{'Padded/Local':<24} {local_ms:>18.3f}")
    print("-" * 44)

    print(f"Unpadded sum: {unpadded_sum}")
    print(f"Local sum: {local_sum}")
    print(f"Execution ratio: {ratio:.4f}x")
    print()
    print("=== TASK 3 COMPLETED ===")


if __name__ == "__main__":
    main()
