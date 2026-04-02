"""
plot_results.py
Строит графики для заданий 2 и 3.

Запуск:  python3 plot_results.py

Ожидаемые файлы рядом со скриптом:
  2_2_results_integrate.txt
  2_3_results_v1.txt
  2_3_results_v2.txt

Выходные PDF:
  speedup_integrate.pdf
  lab2_graphs.pdf
"""

import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

plt.rcParams.update({
    "font.size": 12,
    "axes.grid": True,
    "grid.linestyle": "--",
    "grid.alpha": 0.5,
    "figure.dpi": 150,
})

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def parse_integrate(filename):
    """
    Parse lines like:
    nsteps=40000000, threads=8, T_serial=0.1, T_parallel=0.02, Speedup=5.0, Error=2.7e-08
    """
    threads, t_ser, t_par, speedup = [], [], [], []
    with open(filename) as f:
        for line in f:
            m = re.search(
                r"threads=(\d+).*T_serial=([\d.]+).*T_parallel=([\d.]+).*Speedup=([\d.]+)",
                line)
            if m:
                threads.append(int(m.group(1)))
                t_ser.append(float(m.group(2)))
                t_par.append(float(m.group(3)))
                speedup.append(float(m.group(4)))
    return threads, t_ser, t_par, speedup


def parse_sla(filename):
    """
    Parse lines like:
    N=14000, variant=1, threads=4, time=7.92, iterations=144, max_error=0.0
    """
    threads, times, iters = [], [], []
    with open(filename) as f:
        for line in f:
            m = re.search(
                r"threads=(\d+).*time=([\d.]+).*iterations=(\d+)",
                line)
            if m:
                threads.append(int(m.group(1)))
                times.append(float(m.group(2)))
                iters.append(int(m.group(3)))
    return threads, times, iters


def linear(p_list):
    return list(range(1, max(p_list) + 1))


# ──────────────────────────────────────────────────────────────
# Task 2 — Numerical Integration
# ──────────────────────────────────────────────────────────────

try:
    thr2, ts2, tp2, sp2 = parse_integrate("2_2_results_integrate.txt")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("Task 2 — Numerical Integration (nsteps = 40 000 000)", fontweight="bold")

    # Left: execution time
    ax = axes[0]
    ax.plot(thr2, ts2, "s--", color="gray",  label="Serial (1 thread, min of 100 runs)")
    ax.plot(thr2, tp2, "o-",  color="steelblue", linewidth=2, label="Parallel (min of 100 runs)")
    ax.set_xlabel("Number of threads (p)")
    ax.set_ylabel("Time, sec")
    ax.set_title("Execution Time")
    ax.legend()
    ax.xaxis.set_major_locator(ticker.FixedLocator(thr2))

    # Right: speedup
    ax = axes[1]
    p_lin = list(range(1, max(thr2) + 1))
    ax.plot(p_lin, p_lin, "k--", linewidth=1.2, label="Linear speedup")
    ax.plot(thr2, sp2, "o-", color="steelblue", linewidth=2, label="nsteps = 40 000 000")
    ax.set_xlabel("Number of threads (p)")
    ax.set_ylabel("Speedup $S_p$")
    ax.set_title("Speedup vs Number of Threads")
    ax.legend()
    ax.xaxis.set_major_locator(ticker.FixedLocator(thr2))

    plt.tight_layout()
    plt.savefig("speedup_integrate.pdf", bbox_inches="tight")
    plt.close()
    print("Saved: speedup_integrate.pdf")

except FileNotFoundError as e:
    print(f"[WARN] Skipping task 2 plot: {e}")


# ──────────────────────────────────────────────────────────────
# Task 3 — SLA (Simple Iteration, Variants 1 & 2)
# ──────────────────────────────────────────────────────────────

try:
    thr1, t1, _ = parse_sla("2_3_results_v1.txt")
    thr2b, t2, _ = parse_sla("2_3_results_v2.txt")

    # Serial baseline = time at 1 thread
    T1_ser = t1[0]
    T2_ser = t2[0]

    sp1 = [T1_ser / t for t in t1]
    sp2b = [T2_ser / t for t in t2]

    eff1 = [s / p for s, p in zip(sp1,  thr1)]
    eff2 = [s / p for s, p in zip(sp2b, thr2b)]

    all_thr = sorted(set(thr1 + thr2b))
    p_lin   = list(range(1, max(all_thr) + 1))

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Task 3 — SLA Simple Iteration (N = 14 000, min of 3 runs)", fontweight="bold")

    colors = {"v1": "steelblue", "v2": "darkorange"}

    # ── Execution time ──
    ax = axes[0]
    ax.plot(thr1,  t1, "o-", color=colors["v1"], linewidth=2, label="Variant 1")
    ax.plot(thr2b, t2, "s-", color=colors["v2"], linewidth=2, label="Variant 2")
    ax.set_xlabel("Threads (p)")
    ax.set_ylabel("Time T(p), sec")
    ax.set_title("Execution Time")
    ax.legend()
    ax.xaxis.set_major_locator(ticker.FixedLocator(all_thr))

    # ── Speedup ──
    ax = axes[1]
    ax.plot(p_lin, p_lin, "k--", linewidth=1.2, label="Linear")
    ax.plot(thr1,  sp1,  "o-", color=colors["v1"], linewidth=2, label="Variant 1")
    ax.plot(thr2b, sp2b, "s-", color=colors["v2"], linewidth=2, label="Variant 2")
    ax.set_xlabel("Threads (p)")
    ax.set_ylabel("Speedup S(p)")
    ax.set_title("Speedup")
    ax.legend()
    ax.xaxis.set_major_locator(ticker.FixedLocator(all_thr))

    # ── Efficiency ──
    ax = axes[2]
    ax.axhline(1.0, color="k", linestyle="--", linewidth=1.2, label="Ideal")
    ax.plot(thr1,  eff1, "o-", color=colors["v1"], linewidth=2, label="Variant 1")
    ax.plot(thr2b, eff2, "s-", color=colors["v2"], linewidth=2, label="Variant 2")
    ax.set_xlabel("Threads (p)")
    ax.set_ylabel("Efficiency E(p)")
    ax.set_title("Efficiency")
    ax.set_ylim(0, 1.1)
    ax.legend()
    ax.xaxis.set_major_locator(ticker.FixedLocator(all_thr))

    plt.tight_layout()
    plt.savefig("lab2_graphs.pdf", bbox_inches="tight")
    plt.close()
    print("Saved: lab2_graphs.pdf")

except FileNotFoundError as e:
    print(f"[WARN] Skipping task 3 plot: {e}")

print("Done.")
