#include <iostream>
#include <iomanip>
#include <cmath>
#include <omp.h>
#include <limits>

// Number of repeated measurements — take the minimum (best) time
static const int N_RUNS = 100;

double func(double x) {
    return std::exp(-x * x);
}

double exact_integral(double a, double b) {
    return 0.5 * std::sqrt(M_PI) * (std::erf(b) - std::erf(a));
}

// ---------- parallel integration with #pragma omp atomic ----------
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

// ---------- serial baseline ----------
double integrate_serial(double a, double b, int nsteps) {
    double h   = (b - a) / static_cast<double>(nsteps);
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
    const int    nsteps  = 40'000'000;
    const double exact   = exact_integral(a, b);
    const int    nthreads = std::stoi(argv[1]);

    // ---- serial: 100 runs, take minimum ----
    double t_serial = std::numeric_limits<double>::max();
    {
        omp_set_num_threads(1);
        for (int r = 0; r < N_RUNS; ++r) {
            double t0  = omp_get_wtime();
            double res = integrate_serial(a, b, nsteps);
            double dt  = omp_get_wtime() - t0;
            volatile double dummy = res; (void)dummy;
            if (dt < t_serial) t_serial = dt;
        }
    }

    // ---- parallel: 100 runs, take minimum ----
    omp_set_num_threads(nthreads);
    double t_parallel  = std::numeric_limits<double>::max();
    double res_parallel = 0.0;
    for (int r = 0; r < N_RUNS; ++r) {
        double t0  = omp_get_wtime();
        double res = integrate_omp(a, b, nsteps);
        double dt  = omp_get_wtime() - t0;
        if (dt < t_parallel) {
            t_parallel  = dt;
            res_parallel = res;
        }
    }

    double speedup = t_serial / t_parallel;
    double error   = std::abs(res_parallel - exact);

    std::cout << std::fixed << std::setprecision(10);
    std::cout << "nsteps=" << nsteps
              << ", threads=" << nthreads
              << ", T_serial="   << t_serial
              << ", T_parallel=" << t_parallel
              << ", Speedup="    << speedup
              << ", Error="      << error << "\n";

    return 0;
}
