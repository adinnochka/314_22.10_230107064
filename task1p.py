
import os
import time
import platform
import numpy as np
import psutil
from numba import njit, prange, set_num_threads, get_num_threads

STUDENT_ID = 230107064
ROWS = 8000
COLS = 8000
REPEATS = 3


@njit(parallel=True)
def row_major_sum(matrix, partial):
    for i in prange(matrix.shape[0]):
        total = 0.0
        for j in range(matrix.shape[1]):
            total += matrix[i, j]
        partial[i] = total


@njit(parallel=True)
def column_major_sum(matrix, partial):
    for j in prange(matrix.shape[1]):
        total = 0.0
        for i in range(matrix.shape[0]):
            total += matrix[i, j]
        partial[j] = total


def benchmark(kernel, matrix, partial):
    times = []

    for _ in range(REPEATS):
        start = time.perf_counter()
        kernel(matrix, partial)
        elapsed_ms = (time.perf_counter() - start) * 1000
        times.append(elapsed_ms)

    return min(times)


def main():
    logical_cores = os.cpu_count() or 1
    physical_cores = psutil.cpu_count(logical=False) or logical_cores

    set_num_threads(physical_cores)

    print("=== TASK 1P: PARALLEL CACHE TRAVERSAL ===")
    print(f"Student ID: {STUDENT_ID}")
    print(f"OS: {platform.platform()}")
    print(f"Logical cores: {logical_cores}")
    print(f"Physical cores: {physical_cores}")
    print(f"Used threads: {get_num_threads()}")
    print(f"Matrix: {ROWS} x {COLS}")
    print("Data type: float64")
    print()

    rng = np.random.default_rng(STUDENT_ID)
    matrix = rng.random((ROWS, COLS), dtype=np.float64)

    row_partial = np.empty(ROWS, dtype=np.float64)
    col_partial = np.empty(COLS, dtype=np.float64)

    # Compile before measuring
    row_major_sum(matrix[:10, :10], np.empty(10))
    column_major_sum(matrix[:10, :10], np.empty(10))

    row_ms = benchmark(row_major_sum, matrix, row_partial)
    col_ms = benchmark(column_major_sum, matrix, col_partial)

    row_total = float(np.sum(row_partial))
    col_total = float(np.sum(col_partial))

    if not np.isclose(row_total, col_total, rtol=1e-10):
        raise RuntimeError("Row and column sums do not match!")

    penalty = col_ms / row_ms

    print(f"Mode A (Row-Major): {row_ms:.3f} ms")
    print(f"Mode B (Column-Major): {col_ms:.3f} ms")
    print(f"Cache penalty factor (B/A): {penalty:.4f}x")
    print(f"Matrix sum (Row): {row_total:.6f}")
    print(f"Matrix sum (Column): {col_total:.6f}")

    print()
    print("=== TASK 1P COMPLETED ===")


if __name__ == "__main__":
    main()
