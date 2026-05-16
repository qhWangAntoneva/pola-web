"""Benchmark the vectorized _compute_dip_statistic."""
import sys
import time
import numpy as np

sys.path.insert(0, r'C:\Users\lenovos\Polarization-CBW')
from pola.bandwidth import _compute_dip_statistic, dip_test

# 1. Correctness: small data
x_small = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
d = _compute_dip_statistic(x_small)
print('n=5 dip=%.6f' % d)

# 2. Uniform data, increasing sizes
for n in [10, 20, 50, 100, 200]:
    x = np.random.default_rng(42).uniform(0, 1, n)
    t0 = time.time()
    d = _compute_dip_statistic(x)
    t1 = time.time()
    print('uniform n=%d dip=%.6f time=%.4fs' % (n, d, t1 - t0))

# 3. Bimodal data (400 points)
rng = np.random.default_rng(42)
x_bimodal = np.concatenate([rng.normal(-2, 0.3, 200), rng.normal(2, 0.3, 200)])
t0 = time.time()
d = _compute_dip_statistic(x_bimodal)
t1 = time.time()
print('bimodal n=400 dip=%.6f time=%.4fs' % (d, t1 - t0))

# 4. dip_test with 99 bootstraps on bimodal data
t0 = time.time()
result = dip_test(x_bimodal, n_boot=99, random_state=42)
t1 = time.time()
print('dip_test n=400 n_boot=99: dip=%.6f p=%.4f n_boot=%d n_extreme=%d time=%.3fs' % (
    result.dip, result.p_value, result.n_boot, result.n_extreme, t1 - t0))

print('ALL VECTORIZED TESTS PASSED')
