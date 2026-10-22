
import time
import threading
from queue import Queue

STUDENT_ID = 230107064
TOTAL_ITEMS = 1000
WORKERS = 4
CHUNK_SIZE = 1


def process_item(i):
    time.sleep(0.0001 * (i % 20))


def run_static():
    completion_times = [0.0] * WORKERS
    threads = []
    block_size = TOTAL_ITEMS // WORKERS

    def worker(worker_id):
        start_index = worker_id * block_size
        end_index = (
            TOTAL_ITEMS
            if worker_id == WORKERS - 1
            else start_index + block_size
        )

        for i in range(start_index, end_index):
            process_item(i)

        completion_times[worker_id] = time.perf_counter()

    start = time.perf_counter()

    for worker_id in range(WORKERS):
        thread = threading.Thread(
            target=worker,
            args=(worker_id,)
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    elapsed_ms = (time.perf_counter() - start) * 1000
    delta_ms = (
        max(completion_times) - min(completion_times)
    ) * 1000

    return elapsed_ms, delta_ms, completion_times


def run_dynamic():
    task_queue = Queue()
    completion_times = [0.0] * WORKERS
    threads = []

    for i in range(TOTAL_ITEMS):
        task_queue.put(i)

    def worker(worker_id):
        while True:
            try:
                i = task_queue.get_nowait()
            except Exception:
                break

            process_item(i)
            task_queue.task_done()

        completion_times[worker_id] = time.perf_counter()

    start = time.perf_counter()

    for worker_id in range(WORKERS):
        thread = threading.Thread(
            target=worker,
            args=(worker_id,)
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    elapsed_ms = (time.perf_counter() - start) * 1000
    delta_ms = (
        max(completion_times) - min(completion_times)
    ) * 1000

    return elapsed_ms, delta_ms, completion_times


def main():
    print("=== TASK 4: SCHEDULING UNDER SKEW ===")
    print(f"Student ID: {STUDENT_ID}")
    print(f"Total items: {TOTAL_ITEMS}")
    print(f"Workers: {WORKERS}")
    print(f"Dynamic chunk size: {CHUNK_SIZE}")
    print("Workload: sleep(0.0001 * (i % 20))")
    print()

    static_time, static_delta, static_finish = run_static()
    dynamic_time, dynamic_delta, dynamic_finish = run_dynamic()

    print(
        f"{'Strategy':<22}"
        f"{'Total Time (ms)':>18}"
        f"{'Finish Delta (ms)':>20}"
    )
    print("-" * 60)

    print(
        f"{'A: Static':<22}"
        f"{static_time:>18.3f}"
        f"{static_delta:>20.3f}"
    )

    print(
        f"{'B: Dynamic':<22}"
        f"{dynamic_time:>18.3f}"
        f"{dynamic_delta:>20.3f}"
    )

    print()
    print("Individual worker finish times (ms from start):")

    for name, finish_times in [
        ("Static", static_finish),
        ("Dynamic", dynamic_finish)
    ]:
        first = min(finish_times)

        print(f"{name}:")
        for worker_id, finish in enumerate(finish_times):
            print(
                f"  Worker {worker_id}: "
                f"{(finish - first) * 1000:.3f} ms after first finish"
            )

    print()
    print("=== TASK 4 COMPLETED ===")


if __name__ == "__main__":
    main()
