# Karp-Flatt Practice Lab — Results

**Student ID:** 230107064

## Hardware Profile

- Operating system: Windows-11-10.0.26300-SP0
- Processor: AMD64 Family 25 Model 80 Stepping 0, AuthenticAMD
- Logical CPU cores: 16
- Python version: 3.14.0

## Empirical Measurements

All runtimes are medians of three runs.

| Experiment Mode | T1 (s) | T2 (s) | T4 (s) | e(2) | e(4) | Architectural Diagnosis |
|---|---:|---:|---:|---:|---:|---|
| A: Serial Tail | 11.2954 | 7.3014 | 4.5814 | 0.2928 | 0.2075 | Intentional sequential delay |
| B: Lock Contention | 12.6396 | 32.7368 | 36.9553 | 4.1800 | 3.5650 | Shared mutex contention |
| C: Privatized State | 1.6144 | 1.1479 | 0.7685 | 0.4221 | 0.3014 | Private counters with final reduction |

## Verification

- Experiment A: e(4)/e(2) = 0.7085. Expected range [0.80, 1.25]. **NOT MET**
- Experiment B: T4 > T1 and e(4) > e(2). **NOT MET**
- Experiment C: T4 < T1 and E4 > 70%. Measured E4 = 52.5151%. **NOT MET**

## Architectural Interpretation

Experiment A introduces a fixed 0.40-second sequential delay. This creates a serial component that limits parallel speedup.

Experiment B uses a shared counter protected by a mutex on every increment. Lock acquisition and shared-memory contention can make execution slower as more processes are added.

Experiment C uses private per-process counters and performs a single final reduction, removing per-increment synchronization.

The observations above must be interpreted using the measured results. Failure to reach an expected threshold is reported rather than replaced with a theoretical value.

## Karp-Flatt Formula

Speedup: S(P) = T1 / TP

Karp-Flatt: e(P) = ((P * TP / T1) - 1) / (P - 1)

## Conclusion

The experiments compare fixed algorithmic serialization, shared-lock contention, and state privatization. Their measured Karp-Flatt values provide evidence for identifying the dominant scalability bottleneck.
