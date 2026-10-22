
import os
import platform
import time
import math
import numpy as np
from threadpoolctl import threadpool_limits

STUDENT_ID = 230107064
N = 20_000_000

print("=== TASK 1: HARDWARE PROBE & SERIAL BASELINE ===")
print(f"Student ID: {STUDENT_ID}")
print(f"OS: {platform.platform()}")
print(f"CPU / Platform: {platform.processor() or platform.machine()}")
print(f"Logical CPU cores: {os.cpu_count()}")
print(f"Array size: {N}")
print("Data type: float64")

rng = np.random.default_rng(STUDENT_ID)
data = rng.random(N, dtype=np.float64)

with threadpool_limits(limits=1):
    start = time.perf_counter()

    total = 0.0
    for value in data:
        total += float(value)

    mean = total / N

    squared_diff_sum = 0.0
    for value in data:
        diff = float(value) - mean
        squared_diff_sum += diff * diff

    std_dev = math.sqrt(squared_diff_sum / N)
    elapsed_ms = (time.perf_counter() - start) * 1000

print(f"Sum: {total:.6f}")
print(f"Standard deviation: {std_dev:.6f}")
print(f"Execution time: {elapsed_ms:.3f} ms")
print("Execution mode: Serial (single thread)")
print("===============================================")
