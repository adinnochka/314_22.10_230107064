
import os
import time
import hashlib
import platform
from concurrent.futures import ThreadPoolExecutor

STUDENT_ID = 230107064

TOTAL_TASKS = 10_000
HASH_REPEATS = 500
DATA_SIZE = 1024


def cpu_task(task_index):
    data = (
        f"{STUDENT_ID}-{task_index}".encode()
        .ljust(DATA_SIZE, b"x")[:DATA_SIZE]
    )

    digest = data

    for _ in range(HASH_REPEATS):
        digest = hashlib.sha256(digest).digest()

    return digest


def run_benchmark(pool_size):
    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=pool_size) as executor:
        results = list(
            executor.map(cpu_task, range(TOTAL_TASKS))
        )

    elapsed_ms = (time.perf_counter() - start) * 1000

    if len(results) != TOTAL_TASKS:
        raise RuntimeError("Missing task results")

    return elapsed_ms


def main():
    cores = os.cpu_count() or 1

    pool_sizes = list(dict.fromkeys([
        1,
        max(1, cores // 2),
        cores,
        cores * 2,
        cores * 4,
        cores * 16,
        256
    ]))

    print("=== TASK 5P: THREAD OVERSUBSCRIPTION ===")
    print(f"Student ID: {STUDENT_ID}")
    print(f"OS: {platform.platform()}")
    print(f"Logical cores: {cores}")
    print(f"Total tasks: {TOTAL_TASKS:,}")
    print(f"Input size: {DATA_SIZE} bytes")
    print(f"SHA-256 iterations per task: {HASH_REPEATS}")
    print(f"Pool sizes: {pool_sizes}")
    print()

    print(
        f"{'Pool Size':>12}"
        f"{'Execution Time (ms)':>23}"
        f"{'Speedup':>15}"
        f"{'Status':>24}"
    )
    print("-" * 74)

    baseline = None
    previous_time = None
    first_worsening = None

    for pool_size in pool_sizes:
        elapsed_ms = run_benchmark(pool_size)

        if baseline is None:
            baseline = elapsed_ms

        speedup = baseline / elapsed_ms

        if previous_time is None:
            status = "BASELINE"
        elif elapsed_ms > previous_time:
            status = "WORSENING"

            if first_worsening is None:
                first_worsening = pool_size
        else:
            status = "IMPROVED"

        print(
            f"{pool_size:>12}"
            f"{elapsed_ms:>23.3f}"
            f"{speedup:>15.4f}"
            f"{status:>24}"
        , flush=True)

        previous_time = elapsed_ms

    print()
    print("=== OVERSUBSCRIPTION ANALYSIS ===")

    if first_worsening is not None:
        print(
            f"First observed worsening at pool size: "
            f"{first_worsening}"
        )
    else:
        print(
            "No worsening detected across tested pool sizes."
        )

    print(
        "Note: Worsening is based on measured execution "
        "time compared with the preceding tested pool size."
    )
    print(
        "Thread scheduling, GIL contention and context "
        "switching may contribute to performance changes."
    )

    print()
    print("=== TASK 5P COMPLETED ===")


if __name__ == "__main__":
    main()
