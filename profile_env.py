
import platform
import psutil
import json
import argparse
import subprocess
import re
from pathlib import Path


def get_windows_cpu_info():
    """Read CPU and cache information from Windows CIM."""
    script = r"""
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
    $cache = Get-CimInstance Win32_CacheMemory |
        Select-Object Level, Purpose, InstalledSize
    @{
        Name = $cpu.Name
        MaxClockSpeedMHz = $cpu.MaxClockSpeed
        Manufacturer = $cpu.Manufacturer
        Cache = @($cache)
    } | ConvertTo-Json -Depth 5 -Compress
    """

    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            check=True,
            timeout=20,
        )
        return json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return {}


def get_cache_sizes(cpu_info):
    """Extract reported Windows cache sizes in KB."""
    cache = cpu_info.get("Cache", [])
    if isinstance(cache, dict):
        cache = [cache]

    sizes = {"L1": None, "L2": None, "L3": None}

    for item in cache:
        level = item.get("Level")
        size = item.get("InstalledSize")

        if level == 3:
            sizes["L1"] = size
        elif level == 4:
            sizes["L2"] = size
        elif level == 5:
            sizes["L3"] = size

    return sizes


def main():
    parser = argparse.ArgumentParser(
        description="CS482 hardware environment profiler"
    )
    parser.add_argument("--student-id", required=True)
    args = parser.parse_args()

    cpu_info = get_windows_cpu_info()
    cache_sizes = get_cache_sizes(cpu_info)

    cpu_name = cpu_info.get("Name") or platform.processor()
    cpu_frequency_mhz = cpu_info.get("MaxClockSpeedMHz")

    # Ryzen 7 5800HS: 64-byte cache lines.
    # For other processors, verify this against manufacturer documentation.
    cache_line_size = (
        64 if "Ryzen 7 5800HS" in cpu_name else None
    )

    profile = {
        "student_id": args.student_id,
        "cpu": {
            "model": cpu_name,
            "manufacturer": cpu_info.get("Manufacturer"),
            "architecture": platform.machine(),
            "microarchitecture": (
                "Zen 3" if "Ryzen 7 5800HS" in cpu_name else None
            ),
            "max_clock_mhz": cpu_frequency_mhz,
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
        },
        "cache": {
            "l1_reported_kb": cache_sizes["L1"],
            "l1_data_kb": (
    256 if "Ryzen 7 5800HS" in cpu_name else None
),
            "l2_kb": cache_sizes["L2"],
            "l3_kb": cache_sizes["L3"],
            "cache_line_bytes": cache_line_size,
            "note": (
                "Windows CIM L1 value may combine instruction and data "
                "cache. L1 data cache must be verified separately."
            ),
        },
        "operating_system": {
            "name": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "kernel": platform.uname().version,
            "platform": platform.platform(),
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": platform.python_build(),
            "psutil_version": psutil.__version__,
        },
    }

    results_dir = Path(__file__).resolve().parent.parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / "host_profile.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(profile, file, indent=4, ensure_ascii=False)

    print("Student ID:", args.student_id)
    print("CPU:", cpu_name)
    print("Physical cores:", profile["cpu"]["physical_cores"])
    print("Logical cores:", profile["cpu"]["logical_cores"])
    print("Python:", profile["python"]["version"])
    print("OS:", profile["operating_system"]["platform"])
    print("JSON saved:", output_file)


if __name__ == "__main__":
    main()
