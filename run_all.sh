#!/bin/bash
set -e

RESULTS_FILE="results.csv"
ITERATIONS=100

echo "task,iteration,time_seconds" > $RESULTS_FILE

run_benchmark() {
    local task_name=$1
    local cmake_src=$2
    local build_dir="build_${task_name}"
    
    echo ">>> [${task_name}] Начало сборки..."
    
    # Чистая сборка
    rm -rf $build_dir
    mkdir -p $build_dir
    cd $build_dir
    
    # Копируем нужный CMakeLists.txt под именем CMakeLists.txt
    cp ../$cmake_src ./CMakeLists.txt
    
    # Копируем исходники в папку сборки (так надежнее)
    if [ "$task_name" == "2_2" ]; then
        cp ../2_2_main.cpp .
    elif [ "$task_name" == "2_3" ]; then
        cp ../2_3_main.cpp .
        cp ../2_3_schedule.cpp .
    fi

    # Конфигурация и компиляция
    cmake -DCMAKE_BUILD_TYPE=Release . > /dev/null 2>&1
    make -j$(nproc) > /dev/null 2>&1
    
    # Проверка бинарника
    if [ ! -f "$task_name" ]; then
        echo "ОШИБКА: Бинарный файл '${task_name}' не создан!"
        ls -la
        cd ..
        exit 1
    fi
    
    echo ">>> [${task_name}] Запуск ${ITERATIONS} итераций..."
    
    for ((i=1; i<=ITERATIONS; i++)); do
        # Замер времени через date (работает везде)
        start=$(date +%s.%N)
        ./$task_name > /dev/null 2>&1
        end=$(date +%s.%N)
        
        # Считаем разницу
        duration=$(echo "$end - $start" | bc)
        
        # Пишем в CSV (в родительскую директорию)
        echo "${task_name},${i},${duration}" >> ../$RESULTS_FILE
        
        if [ $((i % 10)) -eq 0 ]; then
            echo "   ...выполнено ${i}/${ITERATIONS}"
        fi
    done
    
    cd ..
    echo ">>> [${task_name}] Готово."
}

# Запускаем обе задачи
run_benchmark "2_2" "2_2_CMakeLists.txt"
run_benchmark "2_3" "2_3_CMakeLists.txt"

echo "========================================="
echo "ВСЕ ЗАВЕРШЕНО! Результаты в ${RESULTS_FILE}"
