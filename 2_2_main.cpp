#include <iostream>
#include <iomanip>
#include <cmath>
#include <omp.h>

double func(double x) { return std::exp(-x * x); }

double exact_integral(double a, double b) {
    return 0.5 * std::sqrt(M_PI) * (std::erf(b) - std::erf(a));
}

double integrate_omp(double a, double b, int nsteps) {
    double h = (b - a) / static_cast<double>(nsteps);
    double global_sum = 0.0;
    #pragma omp parallel
    {
        int nthreads = omp_get_num_threads();
        int tid      = omp_get_thread_num();
        int chunk    = nsteps / nthreads;
        int start    = tid * chunk;
        int end      = (tid == nthreads - 1) ? nsteps : start + chunk;
        double local_sum = 0.0;
        for (int i = start; i < end; ++i) {
            double x = a + (i + 0.5) * h;
            local_sum += func(x);
        }
        #pragma omp atomic
        global_sum += local_sum;
    }
    return global_sum * h;
}

double integrate_serial(double a, double b, int nsteps) {
    double h = (b - a) / static_cast<double>(nsteps);
    double sum = 0.0;
    for (int i = 0; i < nsteps; ++i) {
        double x = a + (i + 0.5) * h;
        sum += func(x);
    }
    return sum * h;
}

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <num_threads>\n";
        return 1;
    }
    const double a       = -4.0;
    const double b       =  4.0;
    const int    nsteps  = 40000000;
    const double exact   = exact_integral(a, b);
    const int    nthreads = std::stoi(argv[1]);

    // serial baseline (1 thread)
    omp_set_num_threads(1);
    double t0    = omp_get_wtime();
    double res_s = integrate_serial(a, b, nsteps);
    double t_ser = omp_get_wtime() - t0;
    volatile double dummy = res_s; (void)dummy;

    // parallel
    omp_set_num_threads(nthreads);
    t0 = omp_get_wtime();
    double res_p = integrate_omp(a, b, nsteps);
    double t_par = omp_get_wtime() - t0;

    double speedup = t_ser / t_par;
    double error   = std::abs(res_p - exact);

    // ВАЖНО: пробелы как разделители, без запятых — для парсинга скриптом
    std::cout << std::fixed << std::setprecision(10);
    std::cout << "nsteps=" << nsteps
              << " threads=" << nthreads
              << " T_serial=" << t_ser
              << " T_parallel=" << t_par
              << " Speedup=" << speedup
              << " Error=" << error << "\n";
    return 0;
}
