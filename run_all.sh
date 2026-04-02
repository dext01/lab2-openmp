#!/bin/bash
# =============================================================
# run_all.sh  —  сборка и запуск заданий 2 и 3
# Запускать из корневой папки проекта:
#   bash run_all.sh
# =============================================================

THREADS="1 2 4 7 8 16 20 40"

# ─────────────────────────────────────────────
# Задание 2: численное интегрирование
# ─────────────────────────────────────────────
echo "=== Building task 2 (integrate) ==="
rm -rf build_2_2 && mkdir build_2_2 && cd build_2_2
cmake ../2_2 -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-O3 -march=native -DNDEBUG" > /dev/null
make -j
cd ..

echo "=== Running task 2 ==="
> 2_2_results_integrate.txt
for p in $THREADS; do
    echo -n "  threads=$p ... "
    ./build_2_2/integrate $p >> 2_2_results_integrate.txt
    echo "done"
done
echo "Results -> 2_2_results_integrate.txt"

# ─────────────────────────────────────────────
# Задание 3: СЛАУ (метод простой итерации)
# N_RUNS=3 внутри кода; каждый прогон ~30-1 сек
# ─────────────────────────────────────────────
echo ""
echo "=== Building task 3 (SLA) ==="
rm -rf build_2_3 && mkdir build_2_3 && cd build_2_3
cmake ../2_3 -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-O3 -march=native -DNDEBUG" > /dev/null
make -j
cd ..

echo "=== Running task 3 variant 1 (this will take a while) ==="
> 2_3_results_v1.txt
for p in $THREADS; do
    echo -n "  variant=1 threads=$p ... "
    ./build_2_3/sla_solve 1 $p >> 2_3_results_v1.txt
    echo "done"
done
echo "Results -> 2_3_results_v1.txt"

echo "=== Running task 3 variant 2 ==="
> 2_3_results_v2.txt
for p in $THREADS; do
    echo -n "  variant=2 threads=$p ... "
    ./build_2_3/sla_solve 2 $p >> 2_3_results_v2.txt
    echo "done"
done
echo "Results -> 2_3_results_v2.txt"

echo ""
echo "All done! Now run:  python3 plot_results.py"
