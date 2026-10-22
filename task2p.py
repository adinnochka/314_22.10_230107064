
import math
import random
import threading
import time
import platform

STUDENT_ID = 230107064
THREADS = 4
TOTAL_SAMPLES = 40_000_000
SAMPLES_PER_THREAD = TOTAL_SAMPLES // THREADS


def run_shared_prng():
    shared_rng = random.Random(STUDENT_ID)
    rng_lock = threading.Lock()
    inside_counts = [0] * THREADS

    def worker(thread_index):
        inside = 0

        for _ in range(SAMPLES_PER_THREAD):
            with rng_lock:
                x = shared_rng.random()
                y = shared_rng.random()

            if x * x + y * y <= 1.0:
                inside += 1

        inside_counts[thread_index] = inside

    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(THREADS)
    ]

    start = time.perf_counter()

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    elapsed_ms = (time.perf_counter() - start) * 1000

    total_inside = sum(inside_counts)
    pi_estimate = 4.0 * total_inside / TOTAL_SAMPLES
    error = abs(pi_estimate - math.pi)

    return pi_estimate, error, elapsed_ms


def run_independent_prng():
    inside_counts = [0] * THREADS

    def worker(thread_index):
        seed = STUDENT_ID * 10 + thread_index
        rng = random.Random(seed)
        inside = 0

        for _ in range(SAMPLES_PER_THREAD):
            x = rng.random()
            y = rng.random()

            if x * x + y * y <= 1.0:
                inside += 1

        inside_counts[thread_index] = inside

    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(THREADS)
    ]

    start = time.perf_counter()

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    elapsed_ms = (time.perf_counter() - start) * 1000

    total_inside = sum(inside_counts)
    pi_estimate = 4.0 * total_inside / TOTAL_SAMPLES
    error = abs(pi_estimate - math.pi)

    return pi_estimate, error, elapsed_ms


def main():
    print("=== TASK 2P: PRNG STATE BOTTLENECK ===")
    print(f"Student ID: {STUDENT_ID}")
    print(f"OS: {platform.platform()}")
    print(f"Threads: {THREADS}")
    print(f"Total samples: {TOTAL_SAMPLES:,}")
    print(f"Samples per thread: {SAMPLES_PER_THREAD:,}")
    print(f"Reference PI: {math.pi:.12f}")
    print()

    print("Running shared PRNG with mutex...", flush=True)
    shared_pi, shared_error, shared_ms = run_shared_prng()

    print("Running independent PRNGs...", flush=True)
    independent_pi, independent_error, independent_ms = (
        run_independent_prng()
    )

    speedup = shared_ms / independent_ms

    print()
    print("=== RESULTS ===")
    print(
        f"{'Method':<24}"
        f"{'Estimated PI':>18}"
        f"{'Absolute Error':>20}"
        f"{'Wall Time (ms)':>18}"
    )
    print("-" * 80)

    print(
        f"{'Shared PRNG + Lock':<24}"
        f"{shared_pi:>18.10f}"
        f"{shared_error:>20.10f}"
        f"{shared_ms:>18.3f}"
    )

    print(
        f"{'Independent PRNG':<24}"
        f"{independent_pi:>18.10f}"
        f"{independent_error:>20.10f}"
        f"{independent_ms:>18.3f}"
    )

    print()
    print(f"Speedup (Shared / Independent): {speedup:.4f}x")
    print()
    print("=== TASK 2P COMPLETED ===")


if __name__ == "__main__":
    main()
