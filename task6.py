
import threading
import time
import platform

STUDENT_ID = 230107064
THREADS = 4
INCREMENTS = 2_000_000
EXPECTED = THREADS * INCREMENTS

counter = 0
lock = threading.Lock()


def unsafe_worker():
    global counter

    for i in range(INCREMENTS):
        current = counter

        # Encourage a context switch to expose the race
        if i % 1000 == 0:
            time.sleep(0)

        counter = current + 1


def safe_worker():
    global counter

    for i in range(INCREMENTS):
        with lock:
            counter += 1


def run_benchmark(worker):
    global counter
    counter = 0

    threads = [
        threading.Thread(target=worker)
        for _ in range(THREADS)
    ]

    start = time.perf_counter()

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    elapsed_ms = (time.perf_counter() - start) * 1000

    return counter, elapsed_ms


def main():
    print("=== TASK 6: RACE CONDITION FORENSICS ===")
    print(f"Student ID: {STUDENT_ID}")
    print(f"OS: {platform.platform()}")
    print(f"Threads: {THREADS}")
    print(f"Increments per thread: {INCREMENTS:,}")
    print()

    unsafe_actual, unsafe_time = run_benchmark(unsafe_worker)
    safe_actual, safe_time = run_benchmark(safe_worker)

    lost = EXPECTED - unsafe_actual
    lost_percentage = (lost / EXPECTED) * 100

    penalty_ms = safe_time - unsafe_time
    penalty_ratio = (
        safe_time / unsafe_time
        if unsafe_time > 0
        else float("inf")
    )

    print(f"Expected final value: {EXPECTED:,}")
    print()
    print("UNSAFE (WITHOUT LOCK)")
    print(f"Actual final value: {unsafe_actual:,}")
    print(f"Lost updates: {lost:,}")
    print(f"Lost percentage: {lost_percentage:.4f}%")
    print(f"Wall time: {unsafe_time:.3f} ms")
    print()
    print("SAFE (WITH LOCK)")
    print(f"Actual final value: {safe_actual:,}")
    print(f"Wall time: {safe_time:.3f} ms")
    print()
    print("SYNCHRONIZATION OVERHEAD")
    print(f"Time penalty: {penalty_ms:.3f} ms")
    print(f"Time ratio (safe/unsafe): {penalty_ratio:.4f}x")

    if safe_actual != EXPECTED:
        raise RuntimeError("Synchronization failed!")

    print()
    print("=== TASK 6 COMPLETED ===")


if __name__ == "__main__":
    main()
