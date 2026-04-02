#!/bin/bash
# =============================================================
# run_all.sh  —  сборка, 100 запусков каждой конфигурации,
#                расчёт метрик (min/max/avg/speedup/efficiency)
# =============================================================

set -e
THREADS="1 2 4 7 8 16 20 40"
N_RUNS=100
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ─────────────────────────────────────────────────────────────
# Функция: считает метрики из файла с результатами
# Формат строк: ... T_serial=X T_parallel=Y Speedup=Z ...
# ─────────────────────────────────────────────────────────────
calc_metrics_integrate() {
    local file="$1"
    local threads="$2"
    echo "--- threads=$threads ---"
    grep "threads=$threads " "$file" | awk '
    {
        for(i=1;i<=NF;i++){
            if($i ~ /^T_serial=/)    { split($i,a,"="); ts=a[2] }
            if($i ~ /^T_parallel=/)  { split($i,a,"="); tp=a[2] }
            if($i ~ /^Speedup=/)     { split($i,a,"="); sp=a[2] }
        }
        n++
        sum_ts+=ts; sum_tp+=tp; sum_sp+=sp
        if(n==1 || ts<min_ts) min_ts=ts
        if(n==1 || ts>max_ts) max_ts=ts
        if(n==1 || tp<min_tp) min_tp=tp
        if(n==1 || tp>max_tp) max_tp=tp
        if(n==1 || sp<min_sp) min_sp=sp
        if(n==1 || sp>max_sp) max_sp=sp
    }
    END {
        if(n==0){print "  no data"; exit}
        avg_ts=sum_ts/n; avg_tp=sum_tp/n; avg_sp=sum_sp/n
        printf "  T_serial:   min=%.6f  max=%.6f  avg=%.6f\n", min_ts,max_ts,avg_ts
        printf "  T_parallel: min=%.6f  max=%.6f  avg=%.6f\n", min_tp,max_tp,avg_tp
        printf "  Speedup:    min=%.4f   max=%.4f   avg=%.4f\n", min_sp,max_sp,avg_sp
        printf "  Efficiency: avg=%.4f\n", avg_sp/'"$threads"'
    }'
}

calc_metrics_sla() {
    local file="$1"
    local variant="$2"
    local threads="$3"
    echo "--- variant=$variant threads=$threads ---"
    grep "variant=$variant " "$file" | grep "threads=$threads " | awk '
    {
        for(i=1;i<=NF;i++){
            if($i ~ /^time=/) { split($i,a,"="); t=a[2] }
        }
        n++
        sum_t+=t
        if(n==1 || t<min_t) min_t=t
        if(n==1 || t>max_t) max_t=t
    }
    END {
        if(n==0){print "  no data"; exit}
        avg_t=sum_t/n
        printf "  time: min=%.4f  max=%.4f  avg=%.4f\n", min_t,max_t,avg_t
    }'
}

calc_metrics_schedule() {
    local file="$1"
    local sched="$2"
    local chunk="$3"
    local threads="$4"
    grep "threads=$threads " "$file" | grep "schedule=$sched " | grep "chunk=$chunk " | awk '
    {
        for(i=1;i<=NF;i++){
            if($i ~ /^time=/) { split($i,a,"="); t=a[2] }
        }
        n++; sum_t+=t
        if(n==1 || t<min_t) min_t=t
        if(n==1 || t>max_t) max_t=t
    }
    END {
        if(n==0){printf "  %-8s chunk=%-5d threads=%-3d  no data\n","'"$sched"'",'"$chunk"','"$threads"'; exit}
        printf "  %-8s chunk=%-5d threads=%-3d  min=%.6f  max=%.6f  avg=%.6f\n",
               "'"$sched"'",'"$chunk"','"$threads"', min_t,max_t,sum_t/n
    }'
}

# ─────────────────────────────────────────────────────────────
# 1. СБОРКА
# ─────────────────────────────────────────────────────────────
echo "============================================="
echo " BUILDING"
echo "============================================="

# Task 2
rm -rf "$SCRIPT_DIR/build_2_2"
mkdir  "$SCRIPT_DIR/build_2_2"
cd     "$SCRIPT_DIR/build_2_2"
cmake  "$SCRIPT_DIR/2_2" -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=OFF -Wno-dev > /dev/null
make -j$(nproc) 2>&1 | tail -3
cd "$SCRIPT_DIR"
echo "Task 2 built."

# Task 3
rm -rf "$SCRIPT_DIR/build_2_3"
mkdir  "$SCRIPT_DIR/build_2_3"
cd     "$SCRIPT_DIR/build_2_3"
cmake  "$SCRIPT_DIR/2_3" -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=OFF -Wno-dev > /dev/null
make -j$(nproc) 2>&1 | tail -3
cd "$SCRIPT_DIR"
echo "Task 3 built."

# ─────────────────────────────────────────────────────────────
# 2. ЗАДАНИЕ 2 — численное интегрирование, 100 запусков
# ─────────────────────────────────────────────────────────────
echo ""
echo "============================================="
echo " TASK 2: Numerical Integration (${N_RUNS} runs each)"
echo "============================================="

RAW2="$SCRIPT_DIR/2_2_raw.txt"
> "$RAW2"

for p in $THREADS; do
    echo -n "  threads=$p  (${N_RUNS} runs) ... "
    for ((r=1; r<=N_RUNS; r++)); do
        "$SCRIPT_DIR/build_2_2/integrate" $p >> "$RAW2"
    done
    echo "done"
done

# Сводный файл: одна строка на конфиг (лучшее время из 100)
METRICS2="$SCRIPT_DIR/2_2_results_integrate.txt"
> "$METRICS2"
echo "# threads  T_serial_min  T_parallel_min  Speedup_best  Efficiency" >> "$METRICS2"

echo ""
echo "=== METRICS (Task 2) ==="
for p in $THREADS; do
    calc_metrics_integrate "$RAW2" "$p"
    # Записываем best-time строку для графиков
    grep "threads=$p " "$RAW2" | awk -v thr=$p '
    {
        for(i=1;i<=NF;i++){
            if($i ~ /^T_serial=/)   { split($i,a,"="); ts=a[2] }
            if($i ~ /^T_parallel=/) { split($i,a,"="); tp=a[2] }
            if($i ~ /^Speedup=/)    { split($i,a,"="); sp=a[2] }
        }
        n++
        if(n==1 || tp<best_tp){ best_tp=tp; best_ts=ts; best_sp=sp }
    }
    END { printf "%d %.10f %.10f %.10f %.6f\n", thr, best_ts, best_tp, best_sp, best_sp/thr }
    ' >> "$METRICS2"
done

echo ""
echo "Raw data -> $RAW2"
echo "Best-time summary -> $METRICS2"

# ─────────────────────────────────────────────────────────────
# 3. ЗАДАНИЕ 3 — СЛАУ, 3 запуска (30 сек каждый — 100 нереально)
# ─────────────────────────────────────────────────────────────
SLA_RUNS=3
echo ""
echo "============================================="
echo " TASK 3: SLA Simple Iteration (${SLA_RUNS} runs each)"
echo " (3 runs: each solve takes ~30s on 1 thread)"
echo "============================================="

RAW3="$SCRIPT_DIR/2_3_raw.txt"
> "$RAW3"

for variant in 1 2; do
    for p in $THREADS; do
        echo -n "  variant=$variant threads=$p  (${SLA_RUNS} runs) ... "
        for ((r=1; r<=SLA_RUNS; r++)); do
            "$SCRIPT_DIR/build_2_3/sla_solve" $variant $p >> "$RAW3"
        done
        echo "done"
    done
done

# Сводный файл для графиков
METRICS3="$SCRIPT_DIR/2_3_results.txt"
> "$METRICS3"
echo "# variant  threads  time_min  speedup  efficiency" >> "$METRICS3"

echo ""
echo "=== METRICS (Task 3) ==="
for variant in 1 2; do
    # Время на 1 потоке для расчёта ускорения
    T1=$(grep "variant=$variant " "$RAW3" | grep "threads=1 " | awk '
        { for(i=1;i<=NF;i++) if($i~/^time=/){split($i,a,"="); t=a[2]; if(NR==1||t<min)min=t} }
        END{print min}')
    for p in $THREADS; do
        calc_metrics_sla "$RAW3" "$variant" "$p"
        grep "variant=$variant " "$RAW3" | grep "threads=$p " | awk -v var=$variant -v thr=$p -v t1=$T1 '
        {
            for(i=1;i<=NF;i++) if($i~/^time=/){split($i,a,"="); t=a[2]; if(NR==1||t<min)min=t}
        }
        END {
            sp = t1/min
            printf "%d %d %.6f %.4f %.4f\n", var, thr, min, sp, sp/thr
        }' >> "$METRICS3"
    done
done

echo ""
echo "Raw data -> $RAW3"
echo "Best-time summary -> $METRICS3"

# ─────────────────────────────────────────────────────────────
# 4. ЗАДАНИЕ 3 — исследование schedule, 100 запусков
# ─────────────────────────────────────────────────────────────
echo ""
echo "============================================="
echo " TASK 3: Schedule Research (${N_RUNS} runs each)"
echo "============================================="

FIXED_THREADS=8   # фиксируем число потоков для исследования schedule
SCHEDULES="static dynamic guided"
CHUNKS="10 25 50 100"

RAW_SCHED="$SCRIPT_DIR/2_3_schedule_raw.txt"
> "$RAW_SCHED"

for sched in $SCHEDULES; do
    for chunk in $CHUNKS; do
        echo -n "  schedule=$sched chunk=$chunk threads=$FIXED_THREADS  (${N_RUNS} runs) ... "
        for ((r=1; r<=N_RUNS; r++)); do
            "$SCRIPT_DIR/build_2_3/sla_schedule" $FIXED_THREADS $sched $chunk >> "$RAW_SCHED"
        done
        echo "done"
    done
done

METRICS_SCHED="$SCRIPT_DIR/2_3_schedule_results.txt"
> "$METRICS_SCHED"
echo "# schedule  chunk  threads  time_min  time_avg" >> "$METRICS_SCHED"

echo ""
echo "=== METRICS (Schedule Research, threads=$FIXED_THREADS) ==="
for sched in $SCHEDULES; do
    echo "  Schedule: $sched"
    for chunk in $CHUNKS; do
        calc_metrics_schedule "$RAW_SCHED" "$sched" "$chunk" "$FIXED_THREADS"
        grep "threads=$FIXED_THREADS " "$RAW_SCHED" | grep "schedule=$sched " | grep "chunk=$chunk " | awk \
            -v s=$sched -v c=$chunk -v thr=$FIXED_THREADS '
            { for(i=1;i<=NF;i++) if($i~/^time=/){split($i,a,"="); t=a[2]; n++; sum+=t; if(n==1||t<min)min=t} }
            END { printf "%s %d %d %.8f %.8f\n", s, c, thr, min, sum/n }
        ' >> "$METRICS_SCHED"
    done
done

echo ""
echo "Raw data -> $RAW_SCHED"
echo "Summary   -> $METRICS_SCHED"

echo ""
echo "============================================="
echo " ALL DONE. Now run:  python3 plot_results.py"
echo "============================================="
