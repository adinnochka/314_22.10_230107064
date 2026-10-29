
import csv
import ctypes
import multiprocessing as mp
import statistics
import time
from pathlib import Path

from salt import get_student_params


STUDENT_ID = "230107064"

REPEATS = 3
TOTAL_UPDATES = 2_000_000
WORKER_COUNTS = [1, 2, 4, 8]

CACHE_LINE_BYTES = 64
ELEMENT_BYTES = ctypes.sizeof(ctypes.c_longlong)
PADDING_STEP = CACHE_LINE_BYTES // ELEMENT_BYTES


def update_counter(shared, index, iterations):
    for _ in range(iterations):
        shared[index] += 1


def run_experiment(workers, padded):
    spacing = PADDING_STEP if padded else 1

    shared_size = (workers - 1) * spacing + 1

    shared = mp.RawArray(
        ctypes.c_longlong,
        shared_size
    )

    iterations = TOTAL_UPDATES // workers

    processes = []

    start = time.perf_counter()

    for worker_id in range(workers):
        index = worker_id * spacing

        process = mp.Process(
            target=update_counter,
            args=(shared, index, iterations)
        )

        processes.append(process)
        process.start()

    for process in processes:
        process.join()

        if process.exitcode != 0:
            raise RuntimeError(
                f"Worker failed: exit code {process.exitcode}"
            )

    elapsed = time.perf_counter() - start

    actual_total = sum(
        shared[worker_id * spacing]
        for worker_id in range(workers)
    )

    expected_total = iterations * workers

    if actual_total != expected_total:
        raise RuntimeError(
            f"Incorrect result: {actual_total} != {expected_total}"
        )

    return elapsed


def karp_flatt(speedup, workers):
    if workers == 1:
        return 0.0

    if speedup <= 0:
        return None

    numerator = (1.0 / speedup) - (1.0 / workers)
    denominator = 1.0 - (1.0 / workers)

    return numerator / denominator


def main():
    mp.freeze_support()

    params = get_student_params(STUDENT_ID)

    print("CS482 - Milestone 2")
    print("False Sharing and Karp-Flatt Analysis")
    print("Student ID:", STUDENT_ID)
    print("N:", params["N"])
    print("Seed:", params["seed"])
    print("Total updates:", TOTAL_UPDATES)
    print("Repetitions:", REPEATS)
    print("-" * 65)

    results = []

    for padded in [False, True]:
        mode = "padded" if padded else "unpadded"

        print("\nMode:", mode)

        baseline_time = None

        for workers in WORKER_COUNTS:
            times = []

            for repeat in range(REPEATS):
                elapsed = run_experiment(workers, padded)
                times.append(elapsed)

                print(
                    f"Workers={workers} "
                    f"Run={repeat + 1} "
                    f"Time={elapsed:.6f}s"
                )

            median_time = statistics.median(times)

            if workers == 1:
                baseline_time = median_time

            speedup = baseline_time / median_time
            efficiency = speedup / workers

            serial_fraction = karp_flatt(
                speedup,
                workers
            )

            results.append({
                "student_id": STUDENT_ID,
                "mode": mode,
                "workers": workers,
                "total_updates": TOTAL_UPDATES,
                "repetitions": REPEATS,
                "median_time_seconds": median_time,
                "speedup": speedup,
                "efficiency": efficiency,
                "karp_flatt": serial_fraction,
            })

            print(
                f"MEDIAN | Workers={workers} "
                f"Time={median_time:.6f}s "
                f"Speedup={speedup:.3f} "
                f"Efficiency={efficiency:.3f} "
                f"Karp-Flatt={serial_fraction:.6f}"
            )

    results_dir = (
        Path(__file__).resolve().parent.parent / "results"
    )

    results_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        results_dir / "false_sharing_karp_flatt.tsv"
    )

    fieldnames = [
        "student_id",
        "mode",
        "workers",
        "total_updates",
        "repetitions",
        "median_time_seconds",
        "speedup",
        "efficiency",
        "karp_flatt",
    ]

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            delimiter="\t"
        )

        writer.writeheader()
        writer.writerows(results)

    print("\n" + "=" * 65)
    print("Milestone 2 experiment completed.")
    print("TSV saved:", output_file)


if __name__ == "__main__":
    main()
