"""
Does a second source of truth pay for itself, and does width change the answer?

Part 1  bit accounting at 7, 16 and 32 bits
Part 2  a plain binary code with the SAME number of physical bits (distance only)
Part 3  whole-source failure: one source is wiped, the other keeps some faults
"""
import math
import random
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, ".")
from two_source_guard import TwoSourceGuardedTable, Status


def secded_bits(width):
    r = 2
    while width + r > 2 ** (r - 1):
        r += 1
    return width + r


def best_binary_distance(n, k, iters=3000, restarts=4, seed=7):
    """Hill-climb a systematic [n, k] binary code; returns the best minimum distance FOUND."""
    rng = np.random.default_rng(seed)
    r = n - k
    msgw = np.zeros(1, dtype=np.uint64)

    def weights(P):
        par = np.zeros(1, dtype=np.uint64)
        pc = np.zeros(1, dtype=np.uint64)
        for i in range(k):
            par = np.concatenate([par, par ^ P[i]])
            pc = np.concatenate([pc, pc + np.uint64(1)])
        w = pc + np.bitwise_count(par).astype(np.uint64)
        w = w[1:]
        d = int(w.min())
        return d, int((w == d).sum())

    best = (0, 0)
    for _ in range(restarts):
        P = rng.integers(1, 1 << r, size=k, dtype=np.uint64)
        cur = weights(P)
        for _ in range(iters):
            i = int(rng.integers(0, k))
            old = P[i]
            P[i] = np.uint64(rng.integers(1, 1 << r))
            new = weights(P)
            if (new[0], -new[1]) >= (cur[0], -cur[1]):
                cur = new
            else:
                P[i] = old
        if (cur[0], -cur[1]) > (best[0], -best[1]):
            best = cur
    return best[0]


def part1():
    print("PART 1  bit accounting  (payload W bits; trits stored as 2 physical bits, or packed)")
    print(f"  {'W':>3s} {'SEC-DED alone':>14s} {'two-source phys':>16s} {'two-source packed':>18s} {'x payload':>10s}  guaranteed")
    for w in (7, 16, 32):
        a = TwoSourceGuardedTable(w).accounting()
        print(f"  {w:3d} {secded_bits(w):10d} bits {a['physical_bits']:12d} bits {a['packed_bits']:14d} bits"
              f" {a['overhead_x']:9.2f}x  fixes 2, never silent at 3")
    print("  the second source is a full second copy of the value, so it costs about 2x payload"
          " at ANY width;\n  only the check bits shrink with width")


def part2():
    print("\nPART 2  plain binary code with the same physical bits (distance found by search; a lower bound on what exists)")
    print(f"  {'W':>3s} {'bits':>5s} {'two-source d':>13s} {'binary-only d found':>20s}  binary-only corrects / never silent")
    for w in (7, 16):
        n = TwoSourceGuardedTable(w).physical_bits()
        d = best_binary_distance(n, w, iters=2500 if w == 7 else 700, restarts=3 if w == 7 else 2)
        print(f"  {w:3d} {n:5d} {6:13d} {d:20d}  {(d - 1) // 2} / {(d - 1) - (d - 1) // 2}")


def part3(width=16, trials=3000, seed=11):
    print(f"\nPART 3  one whole source wiped (width {width}); the other source keeps f random faults")
    rng = random.Random(seed)
    for deg in (False, True):
        g = TwoSourceGuardedTable(width, degraded=deg)
        nb, P = g.nb, g.physical_bits()
        print(f"  policy: {'trust a clean source alone (degraded)' if deg else 'strict (joint distance 2)'}")
        for wiped, lo, hi, other in (("binary source wiped", 0, nb, range(nb, P)),
                                     ("ternary source wiped", nb, P, range(0, nb))):
            for f in (0, 1, 2):
                out = Counter()
                for _ in range(trials):
                    v = rng.randrange(1 << width)
                    g.write(0, v)
                    for p in range(lo, hi):
                        if rng.random() < 0.5:
                            g.rows[0] ^= 1 << p
                    g.flip_bits(0, rng.sample(list(other), f))
                    st = g.cycle(0)
                    out["trapped" if st is Status.TRAPPED else ("right" if g.last_good[0] == v else "SILENT_WRONG")] += 1
                print(f"    {wiped:22s} f={f}: " + ", ".join(f"{a} {100 * b / trials:5.1f}%" for a, b in sorted(out.items())))


if __name__ == "__main__":
    part1()
    part2()
    part3()
