
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
RESULTS = ROOT / "results"

STUDENT_ID = "230107064"

sys.path.insert(0, str(SRC))

from salt import get_student_params


checks = []
failures = []
warnings = []


def record(status, name, message):
    checks.append({
        "status": status,
        "name": name,
        "message": message,
    })

    print(f"[{status}] {name}: {message}")

    if status == "FAIL":
        failures.append(name)
    elif status == "WARN":
        warnings.append(name)


def load_json(filename):
    path = RESULTS / filename

    if not path.is_file():
        raise FileNotFoundError(str(path))

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_tsv(filename):
    path = RESULTS / filename

    if not path.is_file():
        raise FileNotFoundError(str(path))

    with path.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as file:
        return list(csv.DictReader(file, delimiter="\t"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def numeric(value):
    result = float(value)
    require(math.isfinite(result), "Non-finite number")
    return result


def check_m0():
    try:
        actual = get_student_params(STUDENT_ID)
        saved = load_json("salted_params.json")
        host = load_json("host_profile.json")

        require(
            int(actual["N"]) == int(saved["N"]),
            "Salted matrix dimension mismatch"
        )

        require(
            int(actual["seed"]) == int(saved["seed"]),
            "Salted random seed mismatch"
        )

        require(
            isinstance(host, dict) and bool(host),
            "Host profile is empty"
        )

        record(
            "PASS",
            "M0",
            f"Host profile exists; N={actual['N']}, "
            f"seed={actual['seed']}"
        )

    except Exception as exc:
        record("FAIL", "M0", str(exc))


def check_m1():
    try:
        stride = load_tsv("stride_results.tsv")
        dense = load_json("dense_kernel_results.json")

        require(len(stride) > 0, "Stride dataset is empty")
        require(bool(dense), "Dense kernel result is empty")

        record(
            "PASS",
            "M1 files",
            "Stride and dense-kernel datasets are present"
        )

    except Exception as exc:
        record("FAIL", "M1 files", str(exc))

    try:
        interchange = load_json("loop_interchange.json")

        require(
            bool(interchange),
            "Loop interchange results are empty"
        )

        record(
            "PASS",
            "M1 loop interchange",
            "Comparison result file exists"
        )

    except Exception as exc:
        record(
            "FAIL",
            "M1 loop interchange",
            str(exc)
        )

    record(
        "WARN",
        "M1 numerical verification",
        "Presence of result files does not prove that "
        "i-j-k and i-k-j outputs agree within 1e-12. "
        "The actual arrays or a reproducible comparison "
        "are required."
    )


def check_m2():
    try:
        rows = load_tsv(
            "false_sharing_karp_flatt.tsv"
        )

        expected_pairs = {
            (mode, p)
            for mode in ("unpadded", "padded")
            for p in (1, 2, 4, 8)
        }

        actual_pairs = set()

        for row in rows:
            mode = row["mode"]
            p = int(row["workers"])

            actual_pairs.add((mode, p))

            elapsed = numeric(
                row["median_time_seconds"]
            )

            speedup = numeric(row["speedup"])
            efficiency = numeric(row["efficiency"])

            require(elapsed > 0, "Non-positive runtime")
            require(speedup > 0, "Non-positive speedup")

            require(
                math.isclose(
                    efficiency,
                    speedup / p,
                    rel_tol=1e-8,
                    abs_tol=1e-8
                ),
                "M2 efficiency formula mismatch"
            )

            if p > 1:
                measured = numeric(row["karp_flatt"])

                calculated = (
                    (1 / speedup) - (1 / p)
                ) / (
                    1 - (1 / p)
                )

                require(
                    math.isclose(
                        measured,
                        calculated,
                        rel_tol=1e-7,
                        abs_tol=1e-7
                    ),
                    "Karp-Flatt formula mismatch"
                )

        require(
            actual_pairs == expected_pairs,
            "Missing or unexpected M2 worker/mode pairs"
        )

        record(
            "PASS",
            "M2 metrics",
            "Unpadded/padded rows and formulas verified"
        )

    except Exception as exc:
        record("FAIL", "M2 metrics", str(exc))

    record(
        "WARN",
        "M2 counter verification",
        "TSV data does not include every final counter "
        "value or the privatized implementation. "
        "Exact P*K correctness cannot be independently "
        "verified from the saved results."
    )


def check_m3():
    try:
        rows = load_tsv("scaling_metrics.tsv")
        roofline = load_json("roofline_summary.json")

        expected_pairs = {
            (mode, p)
            for mode in ("strong", "weak")
            for p in (1, 2, 4, 8)
        }

        actual_pairs = set()

        base_n = int(
            get_student_params(STUDENT_ID)["N"]
        )

        strong_baseline = None

        for row in rows:
            mode = row["scaling_type"]
            p = int(row["workers"])
            n = int(row["matrix_n"])

            actual_pairs.add((mode, p))

            elapsed = numeric(row["median_seconds"])
            speedup = numeric(row["speedup"])
            efficiency = numeric(
                row["efficiency_percent"]
            )
            checksum = numeric(row["checksum"])

            require(elapsed > 0, "Non-positive runtime")
            require(speedup > 0, "Non-positive speedup")

            if mode == "strong":
                require(
                    n == base_n,
                    "Strong scaling dimension mismatch"
                )

                if p == 1:
                    strong_baseline = elapsed

            elif mode == "weak":
                expected_n = math.ceil(
                    base_n * math.sqrt(p)
                )

                require(
                    n == expected_n,
                    "Weak scaling dimension mismatch"
                )
            else:
                raise ValueError(
                    "Unknown scaling type"
                )

            require(
                math.isfinite(checksum),
                "Invalid checksum"
            )

            require(
                math.isclose(
                    efficiency,
                    100.0 * speedup / p,
                    rel_tol=1e-7,
                    abs_tol=1e-7
                ),
                "M3 efficiency formula mismatch"
            )

        require(
            actual_pairs == expected_pairs,
            "Missing or unexpected M3 worker/mode pairs"
        )

        require(
            strong_baseline is not None,
            "Missing baseline"
        )

        for row in rows:
            mode = row["scaling_type"]
            p = int(row["workers"])
            elapsed = numeric(row["median_seconds"])

            if mode == "strong":
                expected_speedup = (
                    strong_baseline / elapsed
                )
            else:
                current_work = int(
                    row["work_elements"]
                )
                base_work = (base_n - 2) ** 2

                expected_speedup = (
                    p * base_work * strong_baseline
                ) / (
                    current_work * elapsed
                )

            require(
                math.isclose(
                    numeric(row["speedup"]),
                    expected_speedup,
                    rel_tol=1e-7,
                    abs_tol=1e-7
                ),
                "M3 speedup formula mismatch"
            )

        ai = numeric(
            roofline[
                "theoretical_arithmetic_intensity_flops_per_byte"
            ]
        )

        flops = numeric(
            roofline["flops_per_cell"]
        )

        bytes_per_cell = numeric(
            roofline["model_bytes_per_cell"]
        )

        require(
            math.isclose(
                ai,
                flops / bytes_per_cell,
                rel_tol=1e-12
            ),
            "Roofline arithmetic intensity mismatch"
        )

        record(
            "PASS",
            "M3 metrics",
            "Strong/weak dimensions, formulas and "
            "arithmetic intensity verified"
        )

        if (
            roofline.get("peak_memory_bandwidth_gbps")
            is None
            or roofline.get("peak_compute_gflops")
            is None
        ):
            record(
                "WARN",
                "M3 roofline",
                "Hardware peak bandwidth or compute "
                "ceiling is missing; bound classification "
                "is not established"
            )

    except Exception as exc:
        record("FAIL", "M3 metrics", str(exc))

    record(
        "WARN",
        "M3 numerical verification",
        "Saved checksums are finite, but independent "
        "single-thread reference arrays are needed "
        "for full numerical verification."
    )


def make_receipt():
    RESULTS.mkdir(
        parents=True,
        exist_ok=True
    )

    source_files = [
        "host_profile.json",
        "salted_params.json",
        "stride_results.tsv",
        "dense_kernel_results.json",
        "loop_interchange.json",
        "false_sharing_karp_flatt.tsv",
        "scaling_metrics.tsv",
        "roofline_summary.json",
    ]

    file_digests = {}

    for filename in source_files:
        path = RESULTS / filename

        if path.is_file():
            file_digests[filename] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()

    payload = {
        "student_id": STUDENT_ID,
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "status": (
            "FAIL" if failures
            else "WARN" if warnings
            else "PASS"
        ),
        "checks": checks,
        "file_sha256": file_digests,
        "note": (
            "Local integrity receipt, not the "
            "official course verification signature. "
            "File hashes cover raw file bytes, not "
            "salted rounded numerical arrays."
        )
    }

    canonical = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":")
    ).encode("utf-8")

    payload["receipt_sha256"] = hashlib.sha256(
        canonical
    ).hexdigest()

    receipt_path = (
        RESULTS / "verification_receipt.sig"
    )

    receipt_path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    return receipt_path


def main():
    print("=" * 65)
    print("CS482 - MILESTONE 4")
    print("LOCAL VERIFICATION")
    print("=" * 65)

    check_m0()
    check_m1()
    check_m2()
    check_m3()

    receipt = make_receipt()

    print("\n" + "=" * 65)
    print("VERIFICATION SUMMARY")
    print("=" * 65)

    print(
        "PASS:",
        sum(c["status"] == "PASS" for c in checks)
    )

    print("WARN:", len(warnings))
    print("FAIL:", len(failures))

    print("Receipt:", receipt)

    if failures:
        print(
            "\nRESULT: INCOMPLETE / FAILED CHECKS"
        )
        return 1

    if warnings:
        print(
            "\nRESULT: PARTIAL VERIFICATION"
        )
        return 0

    print("\nRESULT: ALL LOCAL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
