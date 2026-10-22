
import subprocess
import sys
from pathlib import Path

JAVA_CODE = r"""
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.ReentrantLock;

public class Task6Benchmark {
    static final int THREADS = 8;
    static final int INCREMENTS = 1_000_000;
    static final long TOTAL_OPS = (long) THREADS * INCREMENTS;

    static int mutexCounter = 0;
    static final ReentrantLock mutex = new ReentrantLock();

    static final AtomicInteger casCounter = new AtomicInteger(0);

    static class Result {
        double milliseconds;
        double throughput;
        int finalCount;

        Result(double ms, double ops, int count) {
            milliseconds = ms;
            throughput = ops;
            finalCount = count;
        }
    }

    static Result benchmark(boolean useCAS)
            throws InterruptedException {

        CountDownLatch ready = new CountDownLatch(THREADS);
        CountDownLatch start = new CountDownLatch(1);
        CountDownLatch done = new CountDownLatch(THREADS);

        Thread[] workers = new Thread[THREADS];

        if (useCAS) {
            casCounter.set(0);
        } else {
            mutexCounter = 0;
        }

        for (int t = 0; t < THREADS; t++) {
            workers[t] = new Thread(() -> {
                ready.countDown();

                try {
                    start.await();

                    for (int i = 0; i < INCREMENTS; i++) {
                        if (useCAS) {
                            int expected;
                            do {
                                expected = casCounter.get();
                            } while (!casCounter.compareAndSet(
                                    expected, expected + 1));
                        } else {
                            mutex.lock();
                            try {
                                mutexCounter++;
                            } finally {
                                mutex.unlock();
                            }
                        }
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                } finally {
                    done.countDown();
                }
            });

            workers[t].start();
        }

        ready.await();

        long begin = System.nanoTime();
        start.countDown();
        done.await();
        long end = System.nanoTime();

        double ms = (end - begin) / 1_000_000.0;
        double throughput = TOTAL_OPS / ((end - begin) / 1e9);

        int count = useCAS
                ? casCounter.get()
                : mutexCounter;

        return new Result(ms, throughput, count);
    }

    public static void main(String[] args)
            throws InterruptedException {

        System.out.println(
            "=== TASK 6P: ATOMIC CAS VS OS MUTEX ==="
        );
        System.out.println("Student ID: 230107064");
        System.out.println("Threads: " + THREADS);
        System.out.println(
            "Increments per thread: " + INCREMENTS
        );
        System.out.println("Total operations: " + TOTAL_OPS);
        System.out.println();

        // JVM warm-up, not included in measurements
        benchmark(false);
        benchmark(true);

        Result mutexResult = benchmark(false);
        Result casResult = benchmark(true);

        double ratio =
            casResult.throughput / mutexResult.throughput;

        System.out.println("=== RESULTS ===");

        System.out.printf(
            "Mutex Execution Time (ms): %.3f%n",
            mutexResult.milliseconds
        );
        System.out.printf(
            "Mutex Throughput (ops/sec): %.2f%n",
            mutexResult.throughput
        );

        System.out.println();

        System.out.printf(
            "Atomic CAS Execution Time (ms): %.3f%n",
            casResult.milliseconds
        );
        System.out.printf(
            "Atomic CAS Throughput (ops/sec): %.2f%n",
            casResult.throughput
        );

        System.out.println();

        System.out.printf(
            "Throughput Ratio (CAS / Mutex): %.4fx%n",
            ratio
        );

        System.out.println();

        System.out.println(
            "Mutex Final Counter: " + mutexResult.finalCount
        );
        System.out.println(
            "CAS Final Counter: " + casResult.finalCount
        );

        boolean passed =
            mutexResult.finalCount == TOTAL_OPS
            && casResult.finalCount == TOTAL_OPS;

        System.out.println(
            "Verification Status: " +
            (passed ? "PASS" : "FAIL")
        );

        if (!passed) {
            System.exit(1);
        }

        System.out.println();
        System.out.println("=== TASK 6P COMPLETED ===");
    }
}
"""


def main():
    folder = Path(__file__).resolve().parent
    java_file = folder / "Task6Benchmark.java"

    java_file.write_text(JAVA_CODE, encoding="utf-8")

    print("Compiling Java benchmark...", flush=True)

    try:
        subprocess.run(
            ["javac", str(java_file)],
            cwd=folder,
            check=True
        )

        print("Running benchmark...", flush=True)
        print()

        subprocess.run(
            ["java", "-cp", str(folder), "Task6Benchmark"],
            cwd=folder,
            check=True
        )

    except FileNotFoundError:
        print("ERROR: Java JDK is not installed or not in PATH.")
        print("Install JDK and verify java and javac commands.")
        sys.exit(1)

    except subprocess.CalledProcessError as error:
        print(f"Benchmark failed: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
