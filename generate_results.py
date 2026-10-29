
import json
import math
import os
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_results(filename):
    path = ROOT / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Missing {filename}. Run its experiment first."
        )

    rows = json.loads(path.read_text(encoding="utf-8"))

    return {
        int(row["workers"]): row
        for row in rows
    }


def fmt(value):
    if value is None:
        return "N/A"
    return f"{value:.4f}"


def make_row(name, data, diagnosis):
    return (
        f"| {name} "
        f"| {fmt(data[1]['runtime_seconds'])} "
        f"| {fmt(data[2]['runtime_seconds'])} "
        f"| {fmt(data[4]['runtime_seconds'])} "
        f"| {fmt(data[2]['karp_flatt'])} "
        f"| {fmt(data[4]['karp_flatt'])} "
        f"| {diagnosis} |"
    )


def main():
    a = load_results("exp_a_results.json")
    b = load_results("exp_b_results.json")
    c = load_results("exp_c_results.json")

    for name, data in [("A", a), ("B", b), ("C", c)]:
        if set(data) != {1, 2, 4}:
            raise ValueError(
                f"Experiment {name} requires P=1,2,4"
            )

    a_e2 = a[2]["karp_flatt"]
    a_e4 = a[4]["karp_flatt"]

    a_ratio = (
        a_e4 / a_e2
        if a_e2 is not None and a_e2 != 0
        else None
    )

    a_pass = (
        a_ratio is not None
        and 0.80 <= a_ratio <= 1.25
    )

    b_pass = (
        b[4]["runtime_seconds"] > b[1]["runtime_seconds"]
        and b[4]["karp_flatt"] > b[2]["karp_flatt"]
    )

    c_efficiency = c[4]["efficiency_percent"]

    c_pass = (
        c[4]["runtime_seconds"] < c[1]["runtime_seconds"]
        and c_efficiency > 70.0
    )

    def status(condition):
        return "PASS" if condition else "NOT MET"

    content = f"""# Karp-Flatt Practice Lab — Results

**Student ID:** 230107064

## Hardware Profile

- Operating system: {platform.platform()}
- Processor: {platform.processor() or "Not reported"}
- Logical CPU cores: {os.cpu_count()}
- Python version: {platform.python_version()}

## Empirical Measurements

All runtimes are medians of three runs.

| Experiment Mode | T1 (s) | T2 (s) | T4 (s) | e(2) | e(4) | Architectural Diagnosis |
|---|---:|---:|---:|---:|---:|---|
{make_row("A: Serial Tail", a, "Intentional sequential delay")}
{make_row("B: Lock Contention", b, "Shared mutex contention")}
{make_row("C: Privatized State", c, "Private counters with final reduction")}

## Verification

- Experiment A: e(4)/e(2) = {fmt(a_ratio)}. Expected range [0.80, 1.25]. **{status(a_pass)}**
- Experiment B: T4 > T1 and e(4) > e(2). **{status(b_pass)}**
- Experiment C: T4 < T1 and E4 > 70%. Measured E4 = {fmt(c_efficiency)}%. **{status(c_pass)}**

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
"""

    output = ROOT / "RESULTS.md"
    output.write_text(content, encoding="utf-8")

    print("RESULTS.md generated successfully")
    print("Experiment A:", status(a_pass))
    print("Experiment B:", status(b_pass))
    print("Experiment C:", status(c_pass))
    print("Saved:", output)


if __name__ == "__main__":
    main()
