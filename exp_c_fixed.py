
import json
import multiprocessing as mp
import statistics
import time
from pathlib import Path

WORKERS = [1, 2, 4]
REPEATS = 3
TOTAL_INCREMENTS = 20_000_000

ROOT = Path(__file__).resolve().parent


def private_worker(iterations):
    local_sum = 0

    for _ in range(iterations):
        local_sum += 1

    return local_sum


def run_privatized(p):
    iterations = TOTAL_INCREMENTS // p

    tasks = [iterations] * p

    start = time.perf_counter()

    with mp.Pool(processes=p) as pool:
        partial_results = pool.map(
            private_worker,
            tasks
        )

    total = sum(partial_results)

    elapsed = time.perf_counter() - start

    expected = iterations * p

    if total != expected:
        raise RuntimeError(
            f"Counter mismatch: {total} != {expected}"
        )

    return elapsed, total


def karp_flatt(t1, tp, p):
    if p == 1:
        return None
    return ((p * tp / t1) - 1.0) / (p - 1.0)


def main():
    mp.freeze_support()

    print("EXPERIMENT C — PRIVATIZATION FIX")
    print("=" * 55)

    rows = []
    baseline = None

    for p in WORKERS:
        times = []

        for run in range(REPEATS):
            elapsed, total = run_privatized(p)
            times.append(elapsed)

            print(
                f"P={p} | Run={run + 1} | "
                f"Time={elapsed:.4f}s | "
                f"Counter={total}"
            )

        median_time = statistics.median(times)

        if p == 1:
            baseline = median_time

        speedup = baseline / median_time
        efficiency = 100.0 * speedup / p
        e = karp_flatt(baseline, median_time, p)

        rows.append({
            "workers": p,
            "runtime_seconds": median_time,
            "speedup": speedup,
            "efficiency_percent": efficiency,
            "karp_flatt": e,
            "final_counter": TOTAL_INCREMENTS
        })

        print(
            f"MEDIAN P={p} | T={median_time:.4f}s | "
            f"S={speedup:.3f} | "
            f"E={efficiency:.2f}% | e={e}"
        )

    output = ROOT / "exp_c_results.json"
    output.write_text(
        json.dumps(rows, indent=2),
        encoding="utf-8"
    )

    print("\nSaved:", output)


if __name__ == "__main__":
    main()
