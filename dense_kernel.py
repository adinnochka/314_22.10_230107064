import time
import statistics
import json
import numpy as np
from pathlib import Path

from salt import get_student_params

STUDENT_ID = "230107064"

params = get_student_params(STUDENT_ID)
N = params["N"]
seed = params["seed"]

print("Student ID:", STUDENT_ID)
print("Matrix size N:", N)
print("Random seed:", seed)

rng = np.random.default_rng(seed)

A = rng.random((N, N), dtype=np.float64)
B = rng.random((N, N), dtype=np.float64)

print("Matrix A shape:", A.shape)
print("Matrix B shape:", B.shape)
print("Matrix A size (MiB):", A.nbytes / (1024 * 1024))
print("Matrix B size (MiB):", B.nbytes / (1024 * 1024))

# Warm-up: exclude first-run initialization from measurements
C = A @ B

times = []

for repeat in range(5):
    start = time.perf_counter()

    C = A @ B

    elapsed = time.perf_counter() - start
    times.append(elapsed)

    print(f"Run {repeat + 1}: {elapsed:.6f} seconds")

median_time = statistics.median(times)

print("Result matrix shape:", C.shape)
print("Median multiplication time:", round(median_time, 6), "seconds")
print("Result checksum:", float(np.sum(C)))

flops = 2 * N ** 3
gflops = flops / median_time / 1e9

print("Total FLOPs:", flops)
print("Performance (GFLOPS):", round(gflops, 2))

results = {
    "student_id": STUDENT_ID,
    "matrix_size": N,
    "seed": seed,
    "repetitions": 5,
    "execution_times_seconds": times,
    "median_time_seconds": median_time,
    "total_flops": flops,
    "performance_gflops": gflops,
    "checksum": float(np.sum(C)),
    "method": "NumPy matrix multiplication"
}

output_file = (
    Path(__file__).resolve().parent.parent
    / "results"
    / "dense_kernel_results.json"
)

output_file.parent.mkdir(parents=True, exist_ok=True)

with open(output_file, "w", encoding="utf-8") as file:
    json.dump(results, file, indent=4)

print("JSON saved:", output_file)