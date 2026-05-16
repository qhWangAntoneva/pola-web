"""Detailed dip_test benchmark at various sizes and bootstrap counts."""
import sys
import time
import numpy as np

sys.path.insert(0, r'C:\Users\lenovos\Polarization-CBW')
from pola.bandwidth import _compute_dip_statistic, dip_test

print("=== Single _compute_dip_statistic (vectorized) ===")
for n in [50, 100, 200, 400]:
    x = np.random.default_rng(42).uniform(0, 1, n)
    t0 = time.time()
    d = _compute_dip_statistic(x)
    t1 = time.time()
    print("n=%d: dip=%.6f time=%.4fs | WASM(5x)=%.2fs | WASM(10x)=%.2fs" % (
        n, d, t1-t0, (t1-t0)*5, (t1-t0)*10))

print("\n=== dip_test variable n_boot (uniform n=100) ===")
x = np.random.default_rng(42).uniform(0, 1, 100)
for n_boot in [10, 20, 50, 99]:
    t0 = time.time()
    r = dip_test(x, n_boot=n_boot, random_state=42)
    t1 = time.time()
    print("n=100 n_boot=%d: dip=%.6f time=%.2fs | WASM(5x)=%.1fs" % (
        n_boot, r.dip, t1-t0, (t1-t0)*5))

print("\n=== dip_test n=50, n_boot=99 (fastest viable config) ===")
x = np.random.default_rng(42).uniform(0, 1, 50)
t0 = time.time()
r = dip_test(x, n_boot=99, random_state=42)
t1 = time.time()
print("n=50 n_boot=99: time=%.3fs | WASM(5x)=%.1fs" % (t1-t0, (t1-t0)*5))

print("\n=== Subsample strategy test: n=400 subsample to n=100 ===")
x_big = np.random.default_rng(42).uniform(0, 1, 400)
t0 = time.time()
x_sub = np.random.default_rng(42).choice(x_big, 100, replace=False)
t1 = time.time()
t2 = time.time()
r = dip_test(x_sub, n_boot=50, random_state=42)
t3 = time.time()
print("subsample+test: subsample_time=%.4fs test_time=%.3fs total=%.3fs | WASM(5x)=%.1fs" % (
    t1-t0, t3-t2, t3-t0, (t3-t0)*5))

print("\n=== Bimodal sample (worst case, no early exit) ===")
rng = np.random.default_rng(42)
x_bi = np.concatenate([rng.normal(-2, 0.3, 200), rng.normal(2, 0.3, 200)])
# Test 3 configurations
for cfg_n, cfg_nboot in [(200, 20), (200, 50), (100, 50)]:
    if len(x_bi) > cfg_n:
        x_use = np.random.default_rng(42).choice(x_bi, cfg_n, replace=False)
    else:
        x_use = x_bi
    t0 = time.time()
    r = dip_test(x_use, n_boot=cfg_nboot, random_state=42)
    t1 = time.time()
    print("bimodal subsample=%d n_boot=%d: dip=%.6f p=%.4f time=%.1fs | WASM(5x)=%.1fs" % (
        cfg_n, cfg_nboot, r.dip, r.p_value, t1-t0, (t1-t0)*5))
