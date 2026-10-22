
import os
import time
import platform
import multiprocessing as mp
from multiprocessing import shared_memory

import numpy as np

STUDENT_ID = 230107064
SIZES = [100_000, 1_000_000, 10_000_000]
REPEATS = 3


def pipe_worker(connection):
    try:
        while True:
            message = connection.recv()

            if message is None:
                break

            arr = message
            connection.send((arr.size, float(arr[0]), float(arr[-1])))
    finally:
        connection.close()


def shared_worker(connection):
    try:
        while True:
            message = connection.recv()

            if message is None:
                break

            name, shape, dtype_str = message
            shm = shared_memory.SharedMemory(name=name)

            try:
                arr = np.ndarray(
                    shape,
                    dtype=np.dtype(dtype_str),
                    buffer=shm.buf
                )
                result = (
                    arr.size,
                    float(arr[0]),
                    float(arr[-1])
                )
                connection.send(result)
                del arr
            finally:
                shm.close()
    finally:
        connection.close()


def benchmark_pipe(arr):
    parent, child = mp.Pipe()
    process = mp.Process(target=pipe_worker, args=(child,))
    process.start()
    child.close()

    times = []

    try:
        for _ in range(REPEATS):
            start = time.perf_counter()

            parent.send(arr)
            result = parent.recv()

            elapsed_ms = (time.perf_counter() - start) * 1000

            assert result == (
                arr.size,
                float(arr[0]),
                float(arr[-1])
            )

            times.append(elapsed_ms)
    finally:
        parent.send(None)
        process.join()
        parent.close()

    return min(times)


def benchmark_shared(arr):
    shm = shared_memory.SharedMemory(
        create=True,
        size=arr.nbytes
    )

    parent, child = mp.Pipe()
    process = mp.Process(target=shared_worker, args=(child,))

    try:
        shared_arr = np.ndarray(
            arr.shape,
            dtype=arr.dtype,
            buffer=shm.buf
        )

        shared_arr[:] = arr
        process.start()
        child.close()

        times = []

        for _ in range(REPEATS):
            start = time.perf_counter()

            parent.send((
                shm.name,
                arr.shape,
                arr.dtype.str
            ))

            result = parent.recv()

            elapsed_ms = (time.perf_counter() - start) * 1000

            assert result == (
                arr.size,
                float(arr[0]),
                float(arr[-1])
            )

            times.append(elapsed_ms)

        return min(times)

    finally:
        if process.is_alive():
            parent.send(None)

        process.join()
        parent.close()

        del shared_arr
        shm.close()
        shm.unlink()


def main():
    print("=== TASK 4P: IPC VS SHARED MEMORY ===")
    print(f"Student ID: {STUDENT_ID}")
    print(f"OS: {platform.platform()}")
    print(f"Logical cores: {os.cpu_count()}")
    print(f"Repeats: {REPEATS}")
    print("Data type: float64")
    print()

    print(
        f"{'N':>12}"
        f"{'Pipe IPC (ms)':>18}"
        f"{'Shared Memory (ms)':>22}"
        f"{'Ratio A/B':>15}"
    )
    print("-" * 70)

    rng = np.random.default_rng(STUDENT_ID)

    for n in SIZES:
        arr = rng.random(n, dtype=np.float64)

        pipe_ms = benchmark_pipe(arr)
        shared_ms = benchmark_shared(arr)

        ratio = pipe_ms / shared_ms

        print(
            f"{n:>12,}"
            f"{pipe_ms:>18.3f}"
            f"{shared_ms:>22.3f}"
            f"{ratio:>15.4f}"
        )

    print()
    print("Note: Shared-memory timing excludes the initial")
    print("copy into shared memory and allocation cost.")
    print("It measures access and synchronization overhead.")
    print()
    print("=== TASK 4P COMPLETED ===")


if __name__ == "__main__":
    mp.freeze_support()
    main()
