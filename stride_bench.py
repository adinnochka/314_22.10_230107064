import time
import json
import csv
import statistics
from array import array
from pathlib import Path

from salt import get_student_params

STUDENT_ID = "230107064"

params = get_student_params(STUDENT_ID)
buffer_elements = params["buffer_elements"]

print("Student ID:", STUDENT_ID)
print("Buffer elements:", buffer_elements)

buffer = array("I", [1]) * buffer_elements

print("Buffer created successfully")
print("Buffer size (MB):", len(buffer) * buffer.itemsize / (1024 * 1024))

strides = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
results = []

for stride in strides:
    measurements = []
    accesses = len(range(0, buffer_elements, stride))

    for repeat in range(5):
        start = time.perf_counter()

        total = 0
        for i in range(0, buffer_elements, stride):
            total += buffer[i]

        elapsed = time.perf_counter() - start
        ns_per_access = elapsed * 1_000_000_000 / accesses

        measurements.append(ns_per_access)

    median_ns = statistics.median(measurements)
    median_seconds = median_ns * accesses / 1_000_000_000

    print(
        f"Stride: {stride:4d} | "
        f"Median: {median_ns:.2f} ns/access"
    )

    results.append({
        "stride": stride,
        "accesses": accesses,
        "time_seconds": median_seconds,
        "ns_per_access": median_ns,
    })

output_file = Path(__file__).resolve().parent.parent / "results" / "stride_results.tsv"

with open(output_file, "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=["stride", "accesses", "time_seconds", "ns_per_access"],
        delimiter="\t",
    )
    writer.writeheader()
    writer.writerows(results)

print("TSV saved:", output_file)