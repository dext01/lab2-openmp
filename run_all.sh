#!/bin/bash
# =============================================================
# run_all.sh
# ИСПРАВЛЕНЫ БАГИ:
# 1. Скрипт сам создаёт папки 2_2/ и 2_3/ из плоской структуры репо
# 2. TAU согласован между main.cpp и schedule.cpp
# 3. Формат вывода без запятых (пробелы как разделители)
# 4. N_RUNS=50
# =============================================================

set -e

THREADS="1 2 4 7 8 16 20 40"
N_RUNS=50       # запусков для task2 и schedule
SLA_RUNS=3      # запусков для task3 SLA (каждый ~30 сек на 1 потоке)
FIXED_THREADS=8 # фиксированные потоки для исследования schedule

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ─────────────────────────────────────────────────────────────
# БАГ 1 ИСПРАВЛЕН: создаём структуру папок из плоских файлов репо
# ─────────────────────────────────────────────────────────────
echo "============================================="
echo " SETUP: creating directory structure"
echo "============================================="

mkdir -p "$SCRIPT_DIR/2_2" "$SCRIPT_DIR/2_3"

# Копируем файлы в нужные папки
cp "$SCRIPT_DIR/2_2_main.cpp"       "$SCRIPT_DIR/2_2/main.cpp"
cp "$SCRIPT_DIR/2_2_CMakeLists.txt" "$SCRIPT_DIR/2_2/CMakeLists.txt"
cp "$SCRIPT_DIR/2_3_main.cpp"       "$SCRIPT_DIR/2_3/main.cpp"
cp "$SCRIPT_DIR/2_3_CMakeLists.txt" "$SCRIPT_DIR/2_3/CMakeLists.txt"
cp "$SCRIPT_DIR/2_3_schedule.cpp"   "$SCRIPT_DIR/2_3/schedule.cpp"

echo "Directory structure ready:"
echo "  2_2/: $(ls $SCRIPT_DIR/2_2/)"
echo "  2_3/: $(ls $SCRIPT_DIR/2_3/)"

# ─────────────────────────────────────────────────────────────
# СБОРКА
# ─────────────────────────────────────────────────────────────
echo ""
echo "============================================="
echo " BUILDING"
echo "============================================="

# Task 2
rm -rf "$SCRIPT_DIR/build_2_2" && mkdir "$SCRIPT_DIR/build_2_2"
cd "$SCRIPT_DIR/build_2_2"
cmake "$SCRIPT_DIR/2_2" -DCMAKE_BUILD_TYPE=Release -Wno-dev 2>&1 | tail -2
make -j$(nproc) 2>&1 | tail -3
echo "Task 2 built OK: $(ls $SCRIPT_DIR/build_2_2/integrate 2>/dev/null && echo integrate)"

# Task 3
rm -rf "$SCRIPT_DIR/build_2_3" && mkdir "$SCRIPT_DIR/build_2_3"
cd "$SCRIPT_DIR/build_2_3"
cmake "$SCRIPT_DIR/2_3" -DCMAKE_BUILD_TYPE=Release -Wno-dev 2>&1 | tail -2
make -j$(nproc) 2>&1 | tail -3
echo "Task 3 built OK: $(ls $SCRIPT_DIR/build_2_3/ | tr '\n' ' ')"

cd "$SCRIPT_DIR"

# Проверяем что всё собралось
for bin in build_2_2/integrate build_2_3/sla_solve build_2_3/sla_schedule; do
    if [ ! -f "$SCRIPT_DIR/$bin" ]; then
        echo "ERROR: $SCRIPT_DIR/$bin not found! Aborting."
        exit 1
    fi
done
echo "All binaries present. Starting measurements..."

# ─────────────────────────────────────────────────────────────
# ЗАДАНИЕ 2 — численное интегрирование, 50 запусков
# ─────────────────────────────────────────────────────────────
echo ""
echo "============================================="
echo " TASK 2: Numerical Integration (${N_RUNS} runs each)"
echo "============================================="

RAW2="$SCRIPT_DIR/2_2_raw.txt"
> "$RAW2"   # очищаем старые данные

for p in $THREADS; do
    echo -n "  threads=$p  [${N_RUNS} runs] ... "
    for ((r=1; r<=N_RUNS; r++)); do
        "$SCRIPT_DIR/build_2_2/integrate" $p >> "$RAW2"
    done
    echo "done"
done

echo "Raw data -> $RAW2  ($(wc -l < $RAW2) lines)"

# ─────────────────────────────────────────────────────────────
# ЗАДАНИЕ 3 — СЛАУ, 3 запуска (30 сек каждый на 1 потоке)
# ─────────────────────────────────────────────────────────────
echo ""
echo "============================================="
echo " TASK 3: SLA Simple Iteration (${SLA_RUNS} runs each)"
echo " Note: 1-thread run takes ~30s each"
echo "============================================="

RAW3="$SCRIPT_DIR/2_3_raw.txt"
> "$RAW3"

for variant in 1 2; do
    for p in $THREADS; do
        echo -n "  variant=$variant threads=$p  [${SLA_RUNS} runs] ... "
        for ((r=1; r<=SLA_RUNS; r++)); do
            "$SCRIPT_DIR/build_2_3/sla_solve" $variant $p >> "$RAW3"
        done
        echo "done"
    done
done

echo "Raw data -> $RAW3  ($(wc -l < $RAW3) lines)"

# ─────────────────────────────────────────────────────────────
# ЗАДАНИЕ 3 — исследование schedule, 50 запусков
# ─────────────────────────────────────────────────────────────
echo ""
echo "============================================="
echo " TASK 3: Schedule Research"
echo " threads=$FIXED_THREADS, ${N_RUNS} runs each"
echo " schedules: static/dynamic/guided, chunks: 10/25/50/100"
echo "============================================="

RAW_SCHED="$SCRIPT_DIR/2_3_schedule_raw.txt"
> "$RAW_SCHED"

for sched in static dynamic guided; do
    for chunk in 10 25 50 100; do
        echo -n "  schedule=$sched chunk=$chunk [${N_RUNS} runs] ... "
        for ((r=1; r<=N_RUNS; r++)); do
            "$SCRIPT_DIR/build_2_3/sla_schedule" $FIXED_THREADS $sched $chunk >> "$RAW_SCHED"
        done
        echo "done"
    done
done

echo "Raw data -> $RAW_SCHED  ($(wc -l < $RAW_SCHED) lines)"

echo ""
echo "============================================="
echo " ALL DONE!"
echo " Run:  python3 plot_results.py"
echo " PDFs: speedup_integrate.pdf  lab2_graphs.pdf  schedule_research.pdf"
echo "============================================="
