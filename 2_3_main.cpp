#include <iostream>
#include <iomanip>
#include <cmath>
#include <omp.h>
#include <vector>

const int    N            = 14000;
const double EPS          = 1e-5;
const double TAU          = 0.01;
const double DIAG_VAL     = 2.0;
const double OFF_DIAG_VAL = 1.0;

// Variant 1: separate #pragma omp parallel for per loop
int solve_variant_1(std::vector<double>& x) {
    std::vector<double> Ax(N), residual(N);
    int iterations = 0;
    double norm = 0.0;
    do {
        #pragma omp parallel for schedule(static)
        for (int i = 0; i < N; ++i) {
            double sum = 0.0;
            for (int j = 0; j < N; ++j)
                sum += (i == j ? DIAG_VAL : OFF_DIAG_VAL) * x[j];
            Ax[i] = sum;
        }
        #pragma omp parallel for schedule(static)
        for (int i = 0; i < N; ++i)
            residual[i] = (N + 1.0) - Ax[i];
        #pragma omp parallel for schedule(static)
        for (int i = 0; i < N; ++i)
            x[i] += TAU * residual[i];
        norm = 0.0;
        #pragma omp parallel for reduction(max:norm) schedule(static)
        for (int i = 0; i < N; ++i) {
            double d = std::abs(x[i] - 1.0);
            if (d > norm) norm = d;
        }
        ++iterations;
    } while (norm > EPS);
    return iterations;
}

// Variant 2: single #pragma omp parallel wrapping the full iteration
int solve_variant_2(std::vector<double>& x) {
    std::vector<double> Ax(N), residual(N);
    int iterations = 0;
    double norm = 0.0;
    do {
        #pragma omp parallel
        {
            #pragma omp for schedule(static)
            for (int i = 0; i < N; ++i) {
                double sum = 0.0;
                for (int j = 0; j < N; ++j)
                    sum += (i == j ? DIAG_VAL : OFF_DIAG_VAL) * x[j];
                Ax[i] = sum;
            }
            #pragma omp for schedule(static)
            for (int i = 0; i < N; ++i)
                residual[i] = (N + 1.0) - Ax[i];
            #pragma omp for schedule(static)
            for (int i = 0; i < N; ++i)
                x[i] += TAU * residual[i];
        }
        norm = 0.0;
        #pragma omp parallel for reduction(max:norm) schedule(static)
        for (int i = 0; i < N; ++i) {
            double d = std::abs(x[i] - 1.0);
            if (d > norm) norm = d;
        }
        ++iterations;
    } while (norm > EPS);
    return iterations;
}

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <variant: 1|2> <num_threads>\n";
        return 1;
    }
    int variant    = std::stoi(argv[1]);
    int nthreads   = std::stoi(argv[2]);
    omp_set_num_threads(nthreads);

    std::vector<double> x(N, 0.0);
    double t_start = omp_get_wtime();
    int iters = (variant == 1) ? solve_variant_1(x) : solve_variant_2(x);
    double elapsed = omp_get_wtime() - t_start;

    double max_error = 0.0;
    for (int i = 0; i < N; ++i) {
        double e = std::abs(x[i] - 1.0);
        if (e > max_error) max_error = e;
    }

    std::cout << std::fixed << std::setprecision(6);
    std::cout << "N=" << N
              << " variant=" << variant
              << " threads=" << nthreads
              << " time=" << elapsed
              << " iterations=" << iters
              << " max_error=" << max_error << "\n";
    return 0;
}
