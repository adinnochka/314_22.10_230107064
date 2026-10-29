
import json
import math
import multiprocessing as mp
import statistics
import time
from pathlib import Path

WORKERS = [1, 2, 4]
REPEATS = 3
TOTAL_CHUNKS = 16
CHUNK_SIZE = 2_000_000
SERIAL_DELAY = 0.40

ROOT = Path(__file__).resolve().parent


def heavy_math(n):
    return sum(
        math.sin(i) * math.cos(i)
        for i in range(1, n)
    )


def run_experiment(workers):
    start = time.perf_counter()

    time.sleep(SERIAL_DELAY)

    with mp.Pool(processes=workers) as pool:
        values = pool.map(
            heavy_math,
            [CHUNK_SIZE] * TOTAL_CHUNKS
        )

    elapsed = time.perf_counter() - start
    return elapsed, math.fsum(values)


def karp_flatt(t1, tp, p):
    if p == 1:
        return None
    return ((p * tp / t1) - 1.0) / (p - 1.0)


def main():
    mp.freeze_support()

    print("EXPERIMENT A — SERIAL TAIL")
    print("=" * 55)

    rows = []
    baseline = None
    reference_checksum = None

    for p in WORKERS:
        times = []
        checksums = []

        for run in range(REPEATS):
            elapsed, checksum = run_experiment(p)
            times.append(elapsed)
            checksums.append(checksum)

            print(
                f"P={p} | Run={run + 1} | "
                f"Time={elapsed:.4f}s"
            )

        if not all(
            math.isclose(
                value,
                checksums[0],
                rel_tol=1e-12,
                abs_tol=1e-9
            )
            for value in checksums
        ):
            raise RuntimeError("Checksum mismatch")

        if reference_checksum is None:
            reference_checksum = checksums[0]
        elif not math.isclose(
            checksums[0],
            reference_checksum,
            rel_tol=1e-12,
            abs_tol=1e-9
        ):
            raise RuntimeError("Cross-worker checksum mismatch")

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
            "checksum": checksums[0]
        })

        print(
            f"MEDIAN P={p} | T={median_time:.4f}s | "
            f"S={speedup:.3f} | e={e}"
        )

    output = ROOT / "exp_a_results.json"
    output.write_text(
        json.dumps(rows, indent=2),
        encoding="utf-8"
    )

    print("\nSaved:", output)


if __name__ == "__main__":
    main()
