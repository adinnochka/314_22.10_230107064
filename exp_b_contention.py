
import json
import multiprocessing as mp
import statistics
import time
from pathlib import Path

WORKERS = [1, 2, 4]
REPEATS = 3
TOTAL_INCREMENTS = 2_000_000

ROOT = Path(__file__).resolve().parent


def contended_worker(counter, lock, iterations):
    for _ in range(iterations):
        with lock:
            counter.value += 1


def run_contended(p):
    iterations = TOTAL_INCREMENTS // p

    counter = mp.Value("i", 0)
    lock = mp.Lock()

    processes = [
        mp.Process(
            target=contended_worker,
            args=(counter, lock, iterations)
        )
        for _ in range(p)
    ]

    start = time.perf_counter()

    for process in processes:
        process.start()

    for process in processes:
        process.join()

    elapsed = time.perf_counter() - start

    for process in processes:
        if process.exitcode != 0:
            raise RuntimeError(
                f"Worker failed: {process.exitcode}"
            )

    expected = p * iterations

    if counter.value != expected:
        raise RuntimeError(
            f"Counter mismatch: "
            f"{counter.value} != {expected}"
        )

    return elapsed, counter.value


def karp_flatt(t1, tp, p):
    if p == 1:
        return None
    return ((p * tp / t1) - 1.0) / (p - 1.0)


def main():
    mp.freeze_support()

    print("EXPERIMENT B — LOCK CONTENTION")
    print("=" * 55)

    rows = []
    baseline = None

    for p in WORKERS:
        times = []

        for run in range(REPEATS):
            elapsed, total = run_contended(p)
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
        e = karp_flatt(baseline, median_time, p)

        rows.append({
            "workers": p,
            "runtime_seconds": median_time,
            "speedup": speedup,
            "karp_flatt": e,
            "final_counter": TOTAL_INCREMENTS
        })

        print(
            f"MEDIAN P={p} | T={median_time:.4f}s | "
            f"S={speedup:.3f} | e={e}"
        )

    output = ROOT / "exp_b_results.json"
    output.write_text(
        json.dumps(rows, indent=2),
        encoding="utf-8"
    )

    print("\nSaved:", output)


if __name__ == "__main__":
    main()
