\# CS482 — Parallel Computing \& Performance Optimization



\*\*Student ID:\*\* 230107064



\## Laboratory Practicum



This project investigates memory hierarchy, cache locality, false sharing, parallel scaling, and performance modeling on a multicore CPU.



\*\*Milestone 0 — Environment Profiling:\*\* Hardware topology and student-specific parameters are recorded.



\*\*Milestone 1 — Memory Locality:\*\* Memory stride behavior and dense numerical computation are benchmarked.



\*\*Milestone 2 — False Sharing:\*\* Shared counters are evaluated using unpadded and cache-line-padded memory layouts. Speedup, parallel efficiency, and the Karp–Flatt metric are calculated.



\*\*Milestone 3 — Scaling and Roofline:\*\* A two-dimensional stencil computation is evaluated using strong and weak scaling. Amdahl's Law, scaled speedup, and theoretical arithmetic intensity are analyzed.



\*\*Milestone 4 — Verification:\*\* A local verification script checks result-file presence, selected numerical relationships, and file integrity. The verification receipt records both successful checks and unresolved requirements.



\## Execution



Run each experiment from the project directory:



```powershell

py src/profile\_env.py

py src/stride\_bench.py

py src/dense\_kernel.py

py src/false\_sharing.py

py src/scaling\_study.py

py verify\_outputs.py

```



\## Results



Experimental datasets are stored in the `results/` directory.



\## Limitations



Measured performance includes Python and operating-system overhead. The Roofline classification requires verified hardware performance ceilings. Full numerical validation and the official course verification procedure must be completed separately before claiming full compliance.

