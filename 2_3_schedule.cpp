// 2_3_schedule.cpp
// Исследование влияния параметров schedule на производительность.
// Фиксируем число потоков и chunk_size, тестируем static/dynamic/guided.
// Запуск: ./sla_schedule <num_threads> <schedule_type> <chunk_size>
// schedule_type: 0=static, 1=dynamic, 2=guided
// chunk_size: 10, 25, 50, 100  (для guided — игнорируется, но передаём для единообразия)

#include <iostream>
#include <iomanip>
#include <cmath>
#include <omp.h>
#include <vector>
#include <string>

const int    N            = 14000;
const int    FIXED_ITERS  = 10;      // фиксируем число итераций для чистого замера
const double DIAG_VAL     = 2.0;
const double OFF_DIAG_VAL = 1.0;

// Один шаг метода простой итерации с заданным schedule через OMP_SCHEDULE (runtime)
void run_iterations(std::vector<double>& x, int niters) {
    std::vector<double> Ax(N), residual(N);
    const double b_val = N + 1.0;
    const double tau   = 0.01;

    for (int it = 0; it < niters; ++it) {
        #pragma omp parallel for schedule(runtime)
        for (int i = 0; i < N; ++i) {
            double sum = 0.0;
            for (int j = 0; j < N; ++j)
                sum += (i == j ? DIAG_VAL : OFF_DIAG_VAL) * x[j];
            Ax[i] = sum;
        }
        #pragma omp parallel for schedule(runtime)
        for (int i = 0; i < N; ++i)
            residual[i] = b_val - Ax[i];
        #pragma omp parallel for schedule(runtime)
        for (int i = 0; i < N; ++i)
            x[i] += tau * residual[i];
    }
}

int main(int argc, char** argv) {
    if (argc < 4) {
        std::cerr << "Usage: " << argv[0]
                  << " <num_threads> <schedule: static|dynamic|guided> <chunk_size>\n";
        return 1;
    }

    int         nthreads   = std::stoi(argv[1]);
    std::string sched_name = argv[2];
    int         chunk      = std::stoi(argv[3]);

    // Устанавливаем schedule через runtime API
    omp_sched_t sched_kind;
    if      (sched_name == "static")  sched_kind = omp_sched_static;
    else if (sched_name == "dynamic") sched_kind = omp_sched_dynamic;
    else if (sched_name == "guided")  sched_kind = omp_sched_guided;
    else {
        std::cerr << "Unknown schedule: " << sched_name << "\n";
        return 1;
    }

    omp_set_num_threads(nthreads);
    omp_set_schedule(sched_kind, chunk);   // устанавливает schedule(runtime) поведение

    // прогрев
    {
        std::vector<double> x(N, 0.0);
        run_iterations(x, 2);
    }

    // замер
    std::vector<double> x(N, 0.0);
    double t0      = omp_get_wtime();
    run_iterations(x, FIXED_ITERS);
    double elapsed = omp_get_wtime() - t0;

    std::cout << std::fixed << std::setprecision(8);
    std::cout << "threads=" << nthreads
              << " schedule=" << sched_name
              << " chunk=" << chunk
              << " iters=" << FIXED_ITERS
              << " time=" << elapsed << "\n";
    return 0;
}
