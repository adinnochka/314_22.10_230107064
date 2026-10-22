
import os
import sys
import time
import platform
import numpy as np
from numba import njit, prange, set_num_threads

STUDENT_ID = 230107064
N = 2_000_000
WORKERS = 8


@njit
def serial_prefix_scan(arr):
    output = np.empty(arr.size, dtype=np.int64)

    running_sum = 0
    for i in range(arr.size):
        running_sum += arr[i]
        output[i] = running_sum

    return output


@njit(parallel=True)
def parallel_prefix_scan(arr, workers):
    n = arr.size
    output = np.empty(n, dtype=np.int64)
    chunk_sums = np.zeros(workers, dtype=np.int64)

    # PASS 1: Local prefix sums
    for worker in prange(workers):
        start = worker * n // workers
        end = (worker + 1) * n // workers

        running_sum = 0

        for i in range(start, end):
            running_sum += arr[i]
            output[i] = running_sum

        chunk_sums[worker] = running_sum

    # Compute offsets for each chunk
    offsets = np.zeros(workers, dtype=np.int64)
    running_offset = 0

    for worker in range(workers):
        offsets[worker] = running_offset
        running_offset += chunk_sums[worker]

    # PASS 2: Apply offsets in parallel
    for worker in prange(workers):
        start = worker * n // workers
        end = (worker + 1) * n // workers

        offset = offsets[worker]

        for i in range(start, end):
            output[i] += offset

    return output


def main():
    set_num_threads(WORKERS)

    rng = np.random.default_rng(STUDENT_ID)
    arr = rng.integers(1, 11, size=N, dtype=np.int64)

    print("=== TASK 3P: PARALLEL PREFIX SCAN ===")
    print(f"Student ID: {STUDENT_ID}")
    print(f"OS: {platform.platform()}")
    print(f"Logical cores: {os.cpu_count()}")
    print(f"Workers: {WORKERS}")
    print(f"Array size: {N:,}")
    print("Input values: integers from 1 to 10")
    print()

    # Compile functions before timing
    warmup = np.array([1, 2, 3, 4], dtype=np.int64)
    serial_prefix_scan(warmup)
    parallel_prefix_scan(warmup, WORKERS)

    # Serial benchmark
    start = time.perf_counter()
    serial_output = serial_prefix_scan(arr)
    serial_ms = (time.perf_counter() - start) * 1000

    # Parallel benchmark
    start = time.perf_counter()
    parallel_output = parallel_prefix_scan(arr, WORKERS)
    parallel_ms = (time.perf_counter() - start) * 1000

    speedup = serial_ms / parallel_ms

    print(f"Serial Time (ms): {serial_ms:.3f}")
    print(f"Parallel Time (ms): {parallel_ms:.3f}")
    print(f"Speedup: {speedup:.4f}x")

    # Required verification
    try:
        assert parallel_output[-1] == serial_output[-1]
        assert np.array_equal(parallel_output, serial_output)
    except AssertionError:
        print("Verification Status: FAIL")
        sys.exit(1)

    print("Verification Status: PASS")
    print(f"Final Prefix Sum: {parallel_output[-1]}")
    print()
    print("=== TASK 3P COMPLETED ===")


if __name__ == "__main__":
    main()
