"""
plot_results.py  —  строит графики для заданий 2 и 3
Запуск: python3 plot_results.py
"""

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


def load_table(filename, skip_comments=True):
    rows = []
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line or (skip_comments and line.startswith("#")):
                continue
            rows.append(list(map(float, line.split())))
    return rows


# ──────────────────────────────────────────────────────────────
# Task 2 — Numerical Integration
# Формат: threads  T_serial_min  T_parallel_min  Speedup_best  Efficiency
# ──────────────────────────────────────────────────────────────
try:
    rows2 = load_table("2_2_results_integrate.txt")
    thr2  = [r[0] for r in rows2]
    ts2   = [r[1] for r in rows2]
    tp2   = [r[2] for r in rows2]
    sp2   = [r[3] for r in rows2]
    eff2  = [r[4] for r in rows2]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Task 2 — Numerical Integration  (nsteps = 40 000 000, best of 100 runs)",
                 fontweight="bold")
    p_lin = list(range(1, int(max(thr2)) + 1))

    # Execution time
    ax = axes[0]
    ax.plot(thr2, ts2, "s--", color="gray",      linewidth=1.5, label="Serial (1 thread)")
    ax.plot(thr2, tp2, "o-",  color="steelblue", linewidth=2,   label="Parallel")
    ax.set_xlabel("Number of threads (p)")
    ax.set_ylabel("Time, sec")
    ax.set_title("Execution Time")
    ax.legend()
    ax.xaxis.set_major_locator(ticker.FixedLocator(thr2))

    # Speedup
    ax = axes[1]
    ax.plot(p_lin, p_lin, "k--", linewidth=1.2, label="Linear speedup")
    ax.plot(thr2, sp2, "o-", color="steelblue", linewidth=2, label="nsteps = 40 000 000")
    ax.set_xlabel("Number of threads (p)")
    ax.set_ylabel("Speedup $S_p$")
    ax.set_title("Speedup")
    ax.legend()
    ax.xaxis.set_major_locator(ticker.FixedLocator(thr2))

    # Efficiency
    ax = axes[2]
    ax.axhline(1.0, color="k", linestyle="--", linewidth=1.2, label="Ideal")
    ax.plot(thr2, eff2, "o-", color="steelblue", linewidth=2, label="nsteps = 40 000 000")
    ax.set_xlabel("Number of threads (p)")
    ax.set_ylabel("Efficiency $E_p$")
    ax.set_title("Efficiency")
    ax.set_ylim(0, 1.15)
    ax.legend()
    ax.xaxis.set_major_locator(ticker.FixedLocator(thr2))

    plt.tight_layout()
    plt.savefig("speedup_integrate.pdf", bbox_inches="tight")
    plt.close()
    print("Saved: speedup_integrate.pdf")

except FileNotFoundError as e:
    print(f"[WARN] Skipping task 2 plot: {e}")


# ──────────────────────────────────────────────────────────────
# Task 3 — SLA (Variants 1 & 2)
# Формат: variant  threads  time_min  speedup  efficiency
# ──────────────────────────────────────────────────────────────
try:
    rows3 = load_table("2_3_results.txt")
    v1 = [r for r in rows3 if r[0] == 1]
    v2 = [r for r in rows3 if r[0] == 2]

    thr1  = [r[1] for r in v1];  t1  = [r[2] for r in v1]
    sp1   = [r[3] for r in v1];  eff1 = [r[4] for r in v1]
    thr2b = [r[1] for r in v2];  t2  = [r[2] for r in v2]
    sp2b  = [r[3] for r in v2];  eff2b = [r[4] for r in v2]

    all_thr = sorted(set(thr1 + thr2b))
    p_lin   = list(range(1, int(max(all_thr)) + 1))
    colors  = {"v1": "steelblue", "v2": "darkorange"}

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Task 3 — SLA Simple Iteration  (N = 14 000, best of 3 runs)",
                 fontweight="bold")

    # Execution time
    ax = axes[0]
    ax.plot(thr1,  t1,  "o-", color=colors["v1"], linewidth=2, label="Variant 1")
    ax.plot(thr2b, t2,  "s-", color=colors["v2"], linewidth=2, label="Variant 2")
    ax.set_xlabel("Threads (p)")
    ax.set_ylabel("Time T(p), sec")
    ax.set_title("Execution Time")
    ax.legend()
    ax.xaxis.set_major_locator(ticker.FixedLocator(all_thr))

    # Speedup
    ax = axes[1]
    ax.plot(p_lin, p_lin, "k--", linewidth=1.2, label="Linear")
    ax.plot(thr1,  sp1,  "o-", color=colors["v1"], linewidth=2, label="Variant 1")
    ax.plot(thr2b, sp2b, "s-", color=colors["v2"], linewidth=2, label="Variant 2")
    ax.set_xlabel("Threads (p)")
    ax.set_ylabel("Speedup S(p)")
    ax.set_title("Speedup")
    ax.legend()
    ax.xaxis.set_major_locator(ticker.FixedLocator(all_thr))

    # Efficiency
    ax = axes[2]
    ax.axhline(1.0, color="k", linestyle="--", linewidth=1.2, label="Ideal")
    ax.plot(thr1,  eff1,  "o-", color=colors["v1"], linewidth=2, label="Variant 1")
    ax.plot(thr2b, eff2b, "s-", color=colors["v2"], linewidth=2, label="Variant 2")
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


# ──────────────────────────────────────────────────────────────
# Task 3 — Schedule Research
# Формат: schedule  chunk  threads  time_min  time_avg
# ──────────────────────────────────────────────────────────────
try:
    sched_data = {}
    with open("2_3_schedule_results.txt") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            sched, chunk, threads = parts[0], int(parts[1]), int(parts[2])
            t_min, t_avg = float(parts[3]), float(parts[4])
            key = (sched, chunk)
            sched_data[key] = {"min": t_min, "avg": t_avg, "threads": threads}

    schedules = ["static", "dynamic", "guided"]
    chunks    = [10, 25, 50, 100]
    colors_s  = {"static": "steelblue", "dynamic": "darkorange", "guided": "forestgreen"}

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Task 3 — Schedule Research  (N = 14 000, 8 threads, best of 100 runs)",
                 fontweight="bold")

    x      = np.arange(len(chunks))
    width  = 0.25
    labels = [str(c) for c in chunks]

    # Min time grouped bar chart
    ax = axes[0]
    for idx, sched in enumerate(schedules):
        vals = [sched_data.get((sched, c), {}).get("min", 0) for c in chunks]
        ax.bar(x + idx * width, vals, width, label=sched, color=colors_s[sched], alpha=0.85)
    ax.set_xlabel("Chunk size")
    ax.set_ylabel("Min time, sec")
    ax.set_title("Min Execution Time by Schedule & Chunk")
    ax.set_xticks(x + width)
    ax.set_xticklabels(labels)
    ax.legend()

    # Avg time
    ax = axes[1]
    for idx, sched in enumerate(schedules):
        vals = [sched_data.get((sched, c), {}).get("avg", 0) for c in chunks]
        ax.bar(x + idx * width, vals, width, label=sched, color=colors_s[sched], alpha=0.85)
    ax.set_xlabel("Chunk size")
    ax.set_ylabel("Avg time, sec")
    ax.set_title("Avg Execution Time by Schedule & Chunk")
    ax.set_xticks(x + width)
    ax.set_xticklabels(labels)
    ax.legend()

    plt.tight_layout()
    plt.savefig("schedule_research.pdf", bbox_inches="tight")
    plt.close()
    print("Saved: schedule_research.pdf")

except FileNotFoundError as e:
    print(f"[WARN] Skipping schedule plot: {e}")

print("Done.")
