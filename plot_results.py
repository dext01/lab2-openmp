"""
plot_results.py — парсит сырые данные, считает метрики, строит 3 PDF.
Запуск: python3 plot_results.py
"""

import os, statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

plt.rcParams.update({
    "font.size": 12, "axes.grid": True,
    "grid.linestyle": "--", "grid.alpha": 0.5, "figure.dpi": 150,
})


def parse_file(filename):
    """Парсит строки формата key=value key=value ..."""
    rows = []
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                d = {}
                for token in line.split():
                    if "=" in token:
                        k, v = token.split("=", 1)
                        try:    d[k] = float(v)
                        except: d[k] = v
                if d:
                    rows.append(d)
            except Exception as e:
                print(f"  [WARN] skip: {line!r} ({e})")
    return rows


def filt(rows, **kw):
    return [r for r in rows if all(r.get(k) == v for k, v in kw.items())]


def met(vals):
    if not vals: return None
    return dict(min=min(vals), max=max(vals),
                avg=statistics.mean(vals),
                stdev=statistics.stdev(vals) if len(vals)>1 else 0,
                n=len(vals))


# ──────────────────────────────────────────────────────────────
# TASK 2 — Numerical Integration
# ──────────────────────────────────────────────────────────────
print("=" * 55)
print("TASK 2 — Numerical Integration")
print("=" * 55)

try:
    rows2 = parse_file("2_2_raw.txt")
    print(f"  Loaded {len(rows2)} rows")

    threads_list = sorted(set(int(r["threads"]) for r in rows2))

    # Базовое время serial = min из всех строк
    t_ser_base = min(r["T_serial"] for r in rows2)

    thr2, tp_min_l, tp_avg_l, sp_l, eff_l = [], [], [], [], []

    print(f"\n  {'p':>4} {'n':>4} {'Tser_min':>10} {'Tpar_min':>10} "
          f"{'Tpar_avg':>10} {'Speedup':>9} {'Eff':>7}")
    print("  " + "-"*60)

    for p in threads_list:
        pr   = filt(rows2, threads=float(p))
        tp_m = met([r["T_parallel"] for r in pr])
        if not tp_m: continue

        sp  = t_ser_base / tp_m["min"]
        eff = sp / p

        thr2.append(p)
        tp_min_l.append(tp_m["min"])
        tp_avg_l.append(tp_m["avg"])
        sp_l.append(sp)
        eff_l.append(eff)

        print(f"  {p:>4} {tp_m['n']:>4} {t_ser_base:>10.6f} {tp_m['min']:>10.6f} "
              f"{tp_m['avg']:>10.6f} {sp:>9.4f} {eff:>7.4f}")

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Task 2 — Numerical Integration  (nsteps=40 000 000, best of 50 runs)",
                 fontweight="bold")
    p_lin = list(range(1, max(thr2)+1))

    ax = axes[0]
    ax.axhline(t_ser_base, color="gray", ls="--", lw=1.5,
               label=f"Serial min={t_ser_base:.4f}s")
    ax.plot(thr2, tp_min_l, "o-",  color="steelblue", lw=2, label="Parallel (min)")
    ax.plot(thr2, tp_avg_l, "o--", color="steelblue", lw=1, alpha=0.45, label="Parallel (avg)")
    ax.set_xlabel("Threads (p)"); ax.set_ylabel("Time, sec")
    ax.set_title("Execution Time"); ax.legend(fontsize=10)
    ax.xaxis.set_major_locator(ticker.FixedLocator(thr2))

    ax = axes[1]
    ax.plot(p_lin, p_lin, "k--", lw=1.2, label="Linear")
    ax.plot(thr2, sp_l, "o-", color="steelblue", lw=2, label="Speedup")
    ax.set_xlabel("Threads (p)"); ax.set_ylabel("Speedup $S_p$")
    ax.set_title("Speedup"); ax.legend()
    ax.xaxis.set_major_locator(ticker.FixedLocator(thr2))

    ax = axes[2]
    ax.axhline(1.0, color="k", ls="--", lw=1.2, label="Ideal")
    ax.plot(thr2, eff_l, "o-", color="steelblue", lw=2, label="Efficiency")
    ax.set_xlabel("Threads (p)"); ax.set_ylabel("Efficiency $E_p$")
    ax.set_title("Efficiency"); ax.set_ylim(0, 1.15); ax.legend()
    ax.xaxis.set_major_locator(ticker.FixedLocator(thr2))

    plt.tight_layout()
    plt.savefig("speedup_integrate.pdf", bbox_inches="tight")
    plt.close()
    print("\n  Saved: speedup_integrate.pdf")

except FileNotFoundError:
    print("  [SKIP] 2_2_raw.txt not found")


# ──────────────────────────────────────────────────────────────
# TASK 3 — SLA
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("TASK 3 — SLA Simple Iteration")
print("=" * 55)

try:
    rows3 = parse_file("2_3_raw.txt")
    print(f"  Loaded {len(rows3)} rows")

    threads_list = sorted(set(int(r["threads"]) for r in rows3))
    results3 = {}

    for var in [1, 2]:
        t1_rows = filt(rows3, variant=float(var), threads=1.0)
        t1_base = min(r["time"] for r in t1_rows) if t1_rows else None
        print(f"\n  Variant {var}  (T1_base={t1_base:.4f}s)")
        print(f"  {'p':>4} {'n':>3} {'T_min':>9} {'T_avg':>9} {'T_max':>9} {'Sp':>8} {'Eff':>7}")
        print("  " + "-"*55)
        for p in threads_list:
            pr = filt(rows3, variant=float(var), threads=float(p))
            tm = met([r["time"] for r in pr])
            if not tm: continue
            sp  = t1_base / tm["min"]
            eff = sp / p
            results3[(var, p)] = {**tm, "sp": sp, "eff": eff}
            print(f"  {p:>4} {tm['n']:>3} {tm['min']:>9.4f} {tm['avg']:>9.4f} "
                  f"{tm['max']:>9.4f} {sp:>8.4f} {eff:>7.4f}")

    colors = {1: "steelblue", 2: "darkorange"}
    labels = {1: "Variant 1 (separate omp parallel for)",
              2: "Variant 2 (single omp parallel)"}
    p_lin  = list(range(1, max(threads_list)+1))

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Task 3 — SLA Simple Iteration  (N=14 000, best of 3 runs)",
                 fontweight="bold")

    for ax, key, ylabel, title in zip(
        axes,
        ["min", "sp", "eff"],
        ["Time T(p), sec", "Speedup S(p)", "Efficiency E(p)"],
        ["Execution Time", "Speedup", "Efficiency"]
    ):
        if key == "sp":
            ax.plot(p_lin, p_lin, "k--", lw=1.2, label="Linear")
        if key == "eff":
            ax.axhline(1.0, color="k", ls="--", lw=1.2, label="Ideal")
        for var in [1, 2]:
            thr = [p for p in threads_list if (var,p) in results3]
            vals = [results3[(var,p)][key] for p in thr]
            ax.plot(thr, vals, "o-" if var==1 else "s-",
                    color=colors[var], lw=2, label=labels[var])
        ax.set_xlabel("Threads (p)"); ax.set_ylabel(ylabel)
        ax.set_title(title); ax.legend(fontsize=9)
        ax.xaxis.set_major_locator(ticker.FixedLocator(threads_list))
        if key == "eff": ax.set_ylim(0, 1.1)

    plt.tight_layout()
    plt.savefig("lab2_graphs.pdf", bbox_inches="tight")
    plt.close()
    print("\n  Saved: lab2_graphs.pdf")

except FileNotFoundError:
    print("  [SKIP] 2_3_raw.txt not found")


# ──────────────────────────────────────────────────────────────
# TASK 3 — Schedule Research
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("TASK 3 — Schedule Research")
print("=" * 55)

try:
    rows_s = parse_file("2_3_schedule_raw.txt")
    print(f"  Loaded {len(rows_s)} rows")

    schedules = ["static", "dynamic", "guided"]
    chunks    = [10, 25, 50, 100]
    colors_s  = {"static": "steelblue", "dynamic": "darkorange", "guided": "forestgreen"}

    sched_res = {}
    print(f"\n  {'Schedule':>10} {'Chunk':>6} {'n':>4} {'T_min':>10} {'T_avg':>10} {'T_max':>10}")
    print("  " + "-"*55)

    for sched in schedules:
        for chunk in chunks:
            pr = [r for r in rows_s
                  if r.get("schedule") == sched and int(r.get("chunk",0)) == chunk]
            tm = met([r["time"] for r in pr])
            if not tm:
                print(f"  {sched:>10} {chunk:>6}  no data")
                continue
            sched_res[(sched, chunk)] = tm
            print(f"  {sched:>10} {chunk:>6} {tm['n']:>4} "
                  f"{tm['min']:>10.6f} {tm['avg']:>10.6f} {tm['max']:>10.6f}")

    if not sched_res:
        raise ValueError("no data")

    x      = np.arange(len(chunks))
    width  = 0.25
    labels_c = [str(c) for c in chunks]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Task 3 — Schedule Research  (N=14 000, 8 threads, 50 runs)",
                 fontweight="bold")

    for ax, metric, title in zip(axes, ["min", "avg"], ["Min Time", "Avg Time"]):
        for idx, sched in enumerate(schedules):
            vals = [sched_res.get((sched,c), {}).get(metric, 0) for c in chunks]
            bars = ax.bar(x + idx*width, vals, width, label=sched,
                          color=colors_s[sched], alpha=0.85)
            for bar, v in zip(bars, vals):
                if v > 0:
                    ax.text(bar.get_x() + bar.get_width()/2,
                            bar.get_height() + 0.001,
                            f"{v:.3f}", ha="center", va="bottom", fontsize=8)
        ax.set_xlabel("Chunk size"); ax.set_ylabel("Time, sec")
        ax.set_title(f"{title} by Schedule & Chunk")
        ax.set_xticks(x + width); ax.set_xticklabels(labels_c)
        ax.legend()

    plt.tight_layout()
    plt.savefig("schedule_research.pdf", bbox_inches="tight")
    plt.close()
    print("\n  Saved: schedule_research.pdf")

except (FileNotFoundError, ValueError) as e:
    print(f"  [SKIP] {e}")

print("\nAll done!")"""
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
