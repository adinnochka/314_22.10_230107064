
import argparse
import csv
import json
import math
import multiprocessing as mp
import statistics
import time
from pathlib import Path
from multiprocessing import shared_memory

import numpy as np

from salt import get_student_params


STUDENT_ID = "230107064"
REPEATS = 3

_shared_memory = None
_matrix = None


def initialize_worker(shm_name, shape):
    global _shared_memory, _matrix

    _shared_memory = shared_memory.SharedMemory(name=shm_name)
    _matrix = np.ndarray(
        shape,
        dtype=np.float64,
        buffer=_shared_memory.buf
    )


def stencil_chunk(bounds):
    start_row, end_row = bounds
    a = _matrix

    # Five-point stencil: four neighbours averaged.
    # The outer boundary is not updated.
    result = 0.25 * (
        a[start_row - 1:end_row - 1, 1:-1]
        + a[start_row + 1:end_row + 1, 1:-1]
        + a[start_row:end_row, :-2]
        + a[start_row:end_row, 2:]
    )

    return float(np.sum(result, dtype=np.float64))


def make_chunks(n, workers):
    interior_rows = n - 2
    chunks = []

    for worker in range(workers):
        start = 1 + (interior_rows * worker) // workers
        end = 1 + (interior_rows * (worker + 1)) // workers

        if start < end:
            chunks.append((start, end))

    return chunks


def reference_checksum(a):
    result = 0.25 * (
        a[:-2, 1:-1]
        + a[2:, 1:-1]
        + a[1:-1, :-2]
        + a[1:-1, 2:]
    )

    return float(np.sum(result, dtype=np.float64))


def run_once(n, workers, seed):
    rng = np.random.default_rng(seed)

    shm = shared_memory.SharedMemory(
        create=True,
        size=n * n * np.dtype(np.float64).itemsize
    )

    try:
        matrix = np.ndarray(
            (n, n),
            dtype=np.float64,
            buffer=shm.buf
        )

        matrix[:] = rng.random((n, n))
        expected = reference_checksum(matrix)

        chunks = make_chunks(n, workers)

        start_time = time.perf_counter()

        with mp.Pool(
            processes=workers,
            initializer=initialize_worker,
            initargs=(shm.name, (n, n))
        ) as pool:
            partial_sums = pool.map(stencil_chunk, chunks)

        elapsed = time.perf_counter() - start_time
        checksum = math.fsum(partial_sums)

        if not math.isclose(
            checksum,
            expected,
            rel_tol=1e-12,
            abs_tol=1e-9
        ):
            raise RuntimeError(
                f"Checksum mismatch: {checksum} vs {expected}"
            )

        return elapsed, checksum

    finally:
        del matrix
        shm.close()
        shm.unlink()


def measure(n, workers, seed):
    times = []
    checksum = None

    for repeat in range(REPEATS):
        elapsed, checksum = run_once(n, workers, seed)
        times.append(elapsed)

        print(
            f"N={n} | P={workers} | "
            f"Run={repeat + 1} | Time={elapsed:.6f}s"
        )

    return statistics.median(times), checksum


def amdahl_serial_fraction(speedup, workers):
    if workers == 1:
        return None

    return (
        (1.0 / speedup) - (1.0 / workers)
    ) / (
        1.0 - (1.0 / workers)
    )


def main():
    mp.freeze_support()

    parser = argparse.ArgumentParser()
    parser.add_argument("--student-id", default=STUDENT_ID)
    parser.add_argument("--bandwidth-gbps", type=float)
    parser.add_argument("--peak-gflops", type=float)
    args = parser.parse_args()

    params = get_student_params(args.student_id)

    n_base = params["N"]
    seed = params["seed"]

    physical_cores = mp.cpu_count()

    try:
        import psutil
        physical_cores = psutil.cpu_count(logical=False) or physical_cores
    except ImportError:
        pass

    workers_list = []
    p = 1

    while p <= physical_cores:
        workers_list.append(p)
        p *= 2

    results = []

    print("CS482 - Milestone 3")
    print("Student ID:", args.student_id)
    print("Base N:", n_base)
    print("Seed:", seed)
    print("Worker counts:", workers_list)

    print("\n=== STRONG SCALING ===")

    strong_baseline = None
    serial_fractions = []

    for workers in workers_list:
        elapsed, checksum = measure(
            n_base,
            workers,
            seed
        )

        if workers == 1:
            strong_baseline = elapsed

        speedup = strong_baseline / elapsed
        efficiency = 100.0 * speedup / workers

        serial_fraction = amdahl_serial_fraction(
            speedup,
            workers
        )

        if (
            serial_fraction is not None
            and serial_fraction > 0
        ):
            serial_fractions.append(serial_fraction)

        ceiling = (
            1.0 / serial_fraction
            if serial_fraction is not None
            and serial_fraction > 0
            else None
        )

        results.append({
            "student_id": args.student_id,
            "scaling_type": "strong",
            "workers": workers,
            "matrix_n": n_base,
            "work_elements": (n_base - 2) ** 2,
            "median_seconds": elapsed,
            "speedup": speedup,
            "efficiency_percent": efficiency,
            "serial_fraction": serial_fraction,
            "speedup_ceiling": ceiling,
            "checksum": checksum
        })

        print(
            f"STRONG P={workers} | "
            f"Median={elapsed:.6f}s | "
            f"Speedup={speedup:.3f} | "
            f"Efficiency={efficiency:.2f}%"
        )

    print("\n=== WEAK SCALING ===")

    base_work = (n_base - 2) ** 2

    for workers in workers_list:
        n_weak = math.ceil(n_base * math.sqrt(workers))

        elapsed, checksum = measure(
            n_weak,
            workers,
            seed
        )

        current_work = (n_weak - 2) ** 2

        scaled_speedup = (
            workers * base_work * strong_baseline
        ) / (
            current_work * elapsed
        )

        weak_efficiency = (
            100.0 * scaled_speedup / workers
        )

        results.append({
            "student_id": args.student_id,
            "scaling_type": "weak",
            "workers": workers,
            "matrix_n": n_weak,
            "work_elements": current_work,
            "median_seconds": elapsed,
            "speedup": scaled_speedup,
            "efficiency_percent": weak_efficiency,
            "serial_fraction": None,
            "speedup_ceiling": None,
            "checksum": checksum
        })

        print(
            f"WEAK P={workers} | "
            f"N={n_weak} | "
            f"Median={elapsed:.6f}s | "
            f"Scaled speedup={scaled_speedup:.3f}"
        )

    results_dir = (
        Path(__file__).resolve().parent.parent / "results"
    )
    results_dir.mkdir(parents=True, exist_ok=True)

    tsv_file = results_dir / "scaling_metrics.tsv"

    fields = [
        "student_id",
        "scaling_type",
        "workers",
        "matrix_n",
        "work_elements",
        "median_seconds",
        "speedup",
        "efficiency_percent",
        "serial_fraction",
        "speedup_ceiling",
        "checksum"
    ]

    with open(
        tsv_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fields,
            delimiter="\t"
        )
        writer.writeheader()
        writer.writerows(results)

    # Theoretical model for the chosen four-neighbour stencil:
    # 3 additions + 1 multiplication = 4 FLOPs per cell.
    # 4 double-precision reads = 32 bytes per cell.
    # This is a simplified traffic model, not measured DRAM traffic.
    flops_per_cell = 4
    bytes_per_cell = 32

    arithmetic_intensity = (
        flops_per_cell / bytes_per_cell
    )

    bandwidth = args.bandwidth_gbps
    peak_compute = args.peak_gflops

    roofline_memory_ceiling = (
        arithmetic_intensity * bandwidth
        if bandwidth is not None
        else None
    )

    if bandwidth is not None and peak_compute is not None:
        regime = (
            "Memory-Bandwidth Bound"
            if roofline_memory_ceiling < peak_compute
            else "Compute Bound"
        )
    else:
        regime = "Undetermined: hardware ceilings not supplied"

    roofline = {
        "student_id": args.student_id,
        "kernel": "four-neighbour 2D stencil with reduction",
        "matrix_n": n_base,
        "flops_per_cell": flops_per_cell,
        "model_bytes_per_cell": bytes_per_cell,
        "theoretical_arithmetic_intensity_flops_per_byte": (
            arithmetic_intensity
        ),
        "peak_memory_bandwidth_gbps": bandwidth,
        "peak_compute_gflops": peak_compute,
        "memory_roof_gflops": roofline_memory_ceiling,
        "classification": regime,
        "strong_baseline_seconds": strong_baseline,
        "positive_empirical_serial_fractions": serial_fractions,
        "notes": (
            "Timing includes Windows process-pool startup and "
            "IPC overhead. The traffic model counts four logical "
            "double-precision neighbour reads per output cell; "
            "actual DRAM traffic and NumPy temporary allocations "
            "may differ due to caching. Supply independently "
            "verified hardware bandwidth and compute ceilings "
            "before interpreting the Roofline classification."
        )
    }

    json_file = results_dir / "roofline_summary.json"

    with open(
        json_file,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(roofline, file, indent=4)

    print("\n=== MILESTONE 3 COMPLETED ===")
    print("TSV saved:", tsv_file)
    print("JSON saved:", json_file)
    print("Arithmetic intensity:", arithmetic_intensity)
    print("Roofline regime:", regime)


if __name__ == "__main__":
    main()
