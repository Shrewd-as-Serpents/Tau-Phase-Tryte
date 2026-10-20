"""
"Check for zeros": legal words are the kernel of a parity-check map H (H . word = 0).
No expected value is recomputed; the syndrome is read straight off the stored word.

Part 1  group facts about the tryte and the null-sum states
Part 2  the weighted second parity trit asked for last round
Part 3  zero-check codes (binary and ternary) vs the residue designs, same harness
Part 4  an actual syndrome decoder, cross-checked against the ideal decoder
"""
import itertools
import sys
import numpy as np

sys.path.insert(0, ".")
import envelope_study as es

# ---------------------------------------------------------------- part 1
def tryte_facts():
    trits = [-1, 0, 1]
    allw = list(itertools.product(trits, repeat=3))            # (T2, T1, T0)
    V = lambda w: 9 * w[0] + 3 * w[1] + w[2]
    z7 = {w for w in allw if sum(w) == 0}
    k9 = {w for w in allw if sum(w) % 3 == 0}
    unison = {(1, 1, 1), (-1, -1, -1)}
    add_digit = lambda a, b: tuple(((x + y + 1) % 3) - 1 for x, y in zip(a, b))   # digitwise Z3
    add_carry = lambda a, b: ((V(a) + V(b) + 13) % 27) - 13                      # Z27 with carries
    closed_digit_k9 = all(add_digit(a, b) in k9 for a in k9 for b in k9)
    closed_digit_z7 = all(add_digit(a, b) in z7 for a in z7 for b in z7)
    k9_vals = {V(w) for w in k9}
    closed_carry_k9 = all(add_carry_vals in k9_vals for add_carry_vals in
                          (((a + b + 13) % 27) - 13 for a in k9_vals for b in k9_vals))
    print("PART 1  group facts (tryte = 3 trits, one per entity)")
    print(f"  integer null-sum set Z7: {len(z7)} states, V = {sorted(V(w) for w in z7)}")
    print(f"  sum = 0 (mod 3) set K9:  {len(k9)} states;  K9 == Z7 + both unison states: {k9 == z7 | unison}")
    print(f"  K9 closed under digitwise addition (a subgroup of Z3^3): {closed_digit_k9}")
    print(f"  Z7 closed under digitwise addition:                       {closed_digit_z7}")
    print(f"  K9 closed under Z27 addition with carries:                {closed_carry_k9}")
    print(f"  weights 1,3,9 reduced mod 3 = (1,0,0): a value-weighted sum mod 3 sees only T0")


# ---------------------------------------------------------------- GF helpers
def rank_mod(rows, q):
    m = [list(r) for r in rows]
    rk = 0
    for c in range(len(m[0])):
        piv = next((i for i in range(rk, len(m)) if m[i][c] % q), None)
        if piv is None:
            continue
        m[rk], m[piv] = m[piv], m[rk]
        inv = pow(m[rk][c], -1, q)
        m[rk] = [(x * inv) % q for x in m[rk]]
        for i in range(len(m)):
            if i != rk and m[i][c] % q:
                f = m[i][c]
                m[i] = [(a - f * b) % q for a, b in zip(m[i], m[rk])]
        rk += 1
    return rk


def projective_points(r, q):
    pts = []
    for v in itertools.product(range(q), repeat=r):
        nz = next((x for x in v if x), None)
        if nz == 1:
            pts.append(v)
    return pts


def unit(r, i):
    return tuple(1 if j == i else 0 for j in range(r))


def pick_columns(q, r, k, min_dist):
    """Choose k data columns so that, with the r identity check columns, every
    (min_dist-1) columns are linearly independent  =>  code distance >= min_dist."""
    units = [unit(r, i) for i in range(r)]
    cand = [p for p in projective_points(r, q) if p not in units]
    chosen = []

    def indep_ok(cols):
        t = min_dist - 1
        if len(cols) < t:
            return True
        last = cols[-1]
        for others in itertools.combinations(cols[:-1], t - 1):
            if rank_mod(list(others) + [last], q) < t:
                return False
        return True

    def dfs(start):
        if len(chosen) == k:
            return True
        for i in range(start, len(cand)):
            chosen.append(cand[i])
            if indep_ok(units + chosen) and dfs(i + 1):
                return True
            chosen.pop()
        return False

    return list(chosen) if dfs(0) else None


def linear_scheme(q, digits_of, k, r, cols):
    """Systematic codewords: data digits then r check digits with H . word = 0."""
    D = np.array(cols, dtype=int).T                      # r x k
    rows = []
    for v in range(es.N_VALUES):
        d = np.array(digits_of(v), dtype=int)
        c = (-(D @ d)) % q
        rows.append(list(d) + list(c))
    H = np.hstack([D, np.eye(r, dtype=int)]) % q
    return np.array(rows, dtype=np.int16), np.full(k + r, q), H


# ---------------------------------------------------------------- part 2
def weighted_extra_trit_scheme(mt):
    """Earlier ternary design plus a second parity trit  sum(i * t_i) mod 3."""
    rows = []
    for v in range(es.N_VALUES):
        cells = es.trits(v, 5)
        for _ in range(2):
            cells += es.trits(v % mt, es.ntrits_for(mt))
        p1 = (-sum(cells)) % 3
        p2 = (-sum((i + 1) * t for i, t in enumerate(cells))) % 3
        rows.append(cells + [p1, p2])
    return np.array(rows, dtype=np.int16), np.full(len(rows[0]), 3)


# ---------------------------------------------------------------- reporting
def outcomes(name, C, rad, ks=(1, 2, 3, 4), count=60000):
    dm = es.dmin_of(C)
    t = (dm - 1) // 2
    line = f"  {name:34s} {C.shape[1]:3d} cells  d={dm}  "
    res = []
    for k in ks:
        v, o, how = es.faults(C, rad, k, count=count)
        r, tr, s = es.classify(v, es.decode(o, C, t))
        res.append(f"k{k}: {r:5.1f}/{tr:5.1f}/{s:5.2f}")
    print(line + "  ".join(res))


def arbitrated(parts, ks=(1, 2, 3, 4), count=60000, label=""):
    """Each part decodes alone; one good source wins, disagreement traps."""
    full_C = np.hstack([p[0] for p in parts])
    full_rad = np.concatenate([p[1] for p in parts])
    cuts = np.cumsum([0] + [p[0].shape[1] for p in parts])
    ts = [(es.dmin_of(p[0]) - 1) // 2 for p in parts]
    line = f"  {label:34s} {full_C.shape[1]:3d} cells  arb    "
    res = []
    for k in ks:
        v, o, how = es.faults(full_C, full_rad, k, count=count)
        decs = [es.decode(o[:, cuts[i]:cuts[i + 1]], parts[i][0], ts[i]) for i in range(len(parts))]
        a, b = decs
        both = (a != -1) & (b != -1)
        agree = both & (a == b)
        lenient = np.where(agree, a, np.where(both, -1, np.where(a != -1, a, b)))
        r, tr, s = es.classify(v, lenient)
        res.append(f"k{k}: {r:5.1f}/{tr:5.1f}/{s:5.2f}")
    print(line + "  ".join(res))


# ---------------------------------------------------------------- part 4
class ZeroSyndromeDecoder:
    """Syndrome-only decoder for a systematic code over GF(q).  No expected value is computed."""

    def __init__(self, q, H, k, legal_max=127):
        self.q, self.H, self.k, self.legal_max = q, H % q, k, legal_max
        self.r, self.n = H.shape
        # syndrome -> (position, magnitude to subtract)
        self.table = {}
        for j in range(self.n):
            for a in range(1, q):
                s = tuple((a * self.H[:, j]) % q)
                self.table[s] = (j, a)

    def value_of(self, word):
        return sum(int(d) * self.q ** i for i, d in enumerate(word[:self.k]))

    def decode(self, word):
        word = np.array(word, dtype=int).copy()
        s = tuple((self.H @ word) % self.q)
        if not any(s):
            status = "CLEAN"
        elif s in self.table:
            j, a = self.table[s]
            word[j] = (word[j] - a) % self.q
            status = "CORRECTED"
        else:
            return None, "DETECTED"
        v = self.value_of(word)
        return (v, status) if v <= self.legal_max else (None, "RANGE")


def cross_check(name, C, rad, H, q, k):
    dec = ZeroSyndromeDecoder(q, H, k)
    dm = es.dmin_of(C)
    t = (dm - 1) // 2
    bad = 0
    total = 0
    for kk in (1, 2, 3):
        v, o, how = es.faults(C, rad, kk, count=40000)
        ideal = es.decode(o, C, t)
        for i in range(len(v)):
            got, _ = dec.decode(o[i])
            got = -1 if got is None else got
            total += 1
            bad += int(got != ideal[i])
    print(f"  {name:34s} syndrome decoder vs ideal decoder: {total} patterns, mismatches {bad}")


# ---------------------------------------------------------------- main
def main():
    tryte_facts()

    mt = es.find_ternary_modulus()
    print("\nPART 2  the weighted second parity trit (earlier ternary design, 5 trits + 2x mod-22 check)")
    print("  columns: cells, min distance, then right/trapped/SILENT % at k faults")
    B = es.ternary_scheme(mt)
    outcomes("B  (sum-parity trit only)", *B, ks=(1, 2, 3))
    Bw = weighted_extra_trit_scheme(mt)
    outcomes("B + weighted parity trit", *Bw, ks=(1, 2, 3))

    print("\nPART 3  zero-check (parity-check matrix) codes, same harness")
    bin_digits = lambda v: es.bits(v, 7)
    ter_digits = lambda v: es.trits(v, 5)
    schemes = {}
    for label, q, digits, k, r, dmin in (
            ("BIN SEC   (4 check bits)", 2, bin_digits, 7, 4, 3),
            ("BIN SEC-DED (5 check bits)", 2, bin_digits, 7, 5, 4),
            ("TER SEC   (3 check trits)", 3, ter_digits, 5, 3, 3),
            ("TER SEC-DED (4 check trits)", 3, ter_digits, 5, 4, 4)):
        cols = pick_columns(q, r, k, dmin)
        if cols is None:
            print(f"  {label}: no column set exists")
            continue
        C, rad, H = linear_scheme(q, digits, k, r, cols)
        schemes[label] = (C, rad, H, q, k)
        print(f"  {label}: data columns {cols}")
    print("  columns: cells, min distance, then right/trapped/SILENT % at k faults")
    for label, (C, rad, H, q, k) in schemes.items():
        outcomes(label, C, rad)

    print("\n  residue designs for comparison")
    A19 = es.binary_scheme([19])
    outcomes("A19  bin + mod19 x2 + parity", *A19)
    outcomes("B    ter + mod22 x2 + parity", *B)

    print("\n  two sources")
    bs = schemes["BIN SEC   (4 check bits)"]
    ts = schemes["TER SEC   (3 check trits)"]
    bd = schemes["BIN SEC-DED (5 check bits)"]
    td = schemes["TER SEC-DED (4 check trits)"]
    j1 = es.concat(bs[:2], ts[:2])
    outcomes("joint: BIN SEC + TER SEC (19 cells)", *j1)
    arbitrated([bs[:2], ts[:2]], label="arbitrated: BIN SEC + TER SEC")
    j2 = es.concat(bd[:2], td[:2])
    outcomes("joint: SEC-DED + SEC-DED (21 cells)", *j2)
    arbitrated([bd[:2], td[:2]], label="arbitrated: SECDED + SECDED")

    print("\nPART 4  syndrome-only decoders")
    for label, (C, rad, H, q, k) in schemes.items():
        cross_check(label, C, rad, H, q, k)

    print("\n  tryte-only codes (3 trits, the three entities) and their check cost")
    tryte_words = lambda cols, r: es.np.array(
        [list(es.trits(v, 3)) + list((-(np.array(cols).T @ np.array(es.trits(v, 3)))) % 3) for v in range(27)],
        dtype=np.int16) if cols else None
    one = [(1,), (1,), (1,)]                      # distance 2: a repeated column is fine
    C1 = tryte_words(one, 1)
    print(f"  one check trit  c = -(T2+T1+T0) mod 3:  4 trits, d_min = {es.dmin_of(C1)}  (detects 1 wrong entity, cannot say which)")
    for r, dmin in ((3, 3), (4, 4)):
        cols = pick_columns(3, r, 3, dmin)
        Ct = tryte_words(cols, r)
        print(f"  {r} check trits: {3 + r} trits, d_min = {es.dmin_of(Ct)}  columns {cols}")


if __name__ == "__main__":
    main()
