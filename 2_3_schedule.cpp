// schedule.cpp
// Исследование влияния schedule(static|dynamic|guided) и chunk_size.
// Запуск: ./sla_schedule <num_threads> <schedule: static|dynamic|guided> <chunk_size>

#include <iostream>
#include <iomanip>
#include <cmath>
#include <omp.h>
#include <vector>
#include <string>

const int    N             = 14000;
const int    FIXED_ITERS   = 10;
const double TAU           = 0.01;   // БАГ БЫЛ: несоответствие с main.cpp, исправлено
const double DIAG_VAL      = 2.0;
const double OFF_DIAG_VAL  = 1.0;

void run_iterations(std::vector<double>& x, int niters) {
    std::vector<double> Ax(N), residual(N);
    const double b_val = N + 1.0;

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
            x[i] += TAU * residual[i];
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

    omp_sched_t sched_kind;
    if      (sched_name == "static")  sched_kind = omp_sched_static;
    else if (sched_name == "dynamic") sched_kind = omp_sched_dynamic;
    else if (sched_name == "guided")  sched_kind = omp_sched_guided;
    else {
        std::cerr << "Unknown schedule: " << sched_name << "\n";
        return 1;
    }

    omp_set_num_threads(nthreads);
    omp_set_schedule(sched_kind, chunk);

    // прогрев кэша
    {
        std::vector<double> xw(N, 0.0);
        run_iterations(xw, 2);
    }

    // замер
    std::vector<double> x(N, 0.0);
    double t0      = omp_get_wtime();
    run_iterations(x, FIXED_ITERS);
    double elapsed = omp_get_wtime() - t0;

    // ВАЖНО: пробелы как разделители, без запятых — для парсинга скриптом
    std::cout << std::fixed << std::setprecision(8);
    std::cout << "threads=" << nthreads
              << " schedule=" << sched_name
              << " chunk="    << chunk
              << " iters="    << FIXED_ITERS
              << " time="     << elapsed << "\n";
    return 0;
}
