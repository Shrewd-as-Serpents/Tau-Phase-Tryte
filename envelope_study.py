"""
Envelope study: does a second, differently-based "source of truth" widen the set of
errors a register can survive?

Every scheme is a CODEWORD SET: the 128 legal values 0..127, each stored as a row of
cells.  A cell has a radix (2 = bit, 3 = trit, 20 = base-20 digit).  A fault changes
one cell to a different symbol (new = old + s mod radix, s != 0).

Because the legal set is just 128 rows, the guarantees follow exactly from the
minimum Hamming distance d_min between rows:
    detect any  d_min-1 faults,   correct any  t = (d_min-1)//2 faults.
Outcomes for k faults are then measured (exhaustive for k<=2, sampled above that)
with a bounded-distance decoder: accept the unique nearest codeword if it is within
t cells, otherwise trap (restore last good).  "Silent wrong" = decoder accepted a
value that is not the truth.
"""
import itertools
import math
import numpy as np

N_VALUES = 128
RNG = np.random.default_rng(20261019)


# ------------------------------------------------------------------ encoders
def bits(x, n):
    return [(x >> i) & 1 for i in range(n)]


def trits(x, n):
    return [(x // 3 ** i) % 3 for i in range(n)]


def nbits_for(m):
    return max(1, math.ceil(math.log2(m)))


def ntrits_for(m):
    n = 1
    while 3 ** n < m:
        n += 1
    return n


def binary_scheme(moduli, copies=2, parity=True, data_bits=8):
    """Binary value + residue check fields (one field per modulus, written `copies` times)."""
    rows, radices = [], None
    for v in range(N_VALUES):
        cells = bits(v, data_bits)
        for _ in range(copies):
            for m in moduli:
                cells += bits(v % m, nbits_for(m))
        if parity:
            cells.append(sum(cells) & 1)
        rows.append(cells)
    return np.array(rows, dtype=np.int16), np.full(len(rows[0]), 2)


def find_ternary_modulus():
    """Smallest m whose residues separate every (trit position, signed shift) fault."""
    for m in range(5, 200):
        deltas = [(s * 3 ** k) % m for k in range(5) for s in (1, 2, -1, -2)]
        if 0 not in deltas and len(set(deltas)) == len(deltas):
            return m
    return None


def ternary_scheme(mt, copies=2, parity=True):
    nt = ntrits_for(mt)
    rows = []
    for v in range(N_VALUES):
        cells = trits(v, 5)
        for _ in range(copies):
            cells += trits(v % mt, nt)
        if parity:
            cells.append((-sum(cells)) % 3)          # total trit sum == 0 mod 3
        rows.append(cells)
    return np.array(rows, dtype=np.int16), np.full(len(rows[0]), 3)


def raw_binary():
    return np.array([bits(v, 7) for v in range(N_VALUES)], dtype=np.int16), np.full(7, 2)


def raw_ternary():
    return np.array([trits(v, 5) for v in range(N_VALUES)], dtype=np.int16), np.full(5, 3)


def concat(a, b):
    return np.hstack([a[0], b[0]]), np.concatenate([a[1], b[1]])


def crt540(base20_cell=False):
    """The engine's own ring: x mod 20 (binary or one base-20 digit) and x mod 27 (3 trits = tryte)."""
    rows, radices = [], None
    for v in range(N_VALUES):
        r20, r27 = v % 20, v % 27
        cells = ([r20] if base20_cell else bits(r20, 5)) + trits(r27, 3)
        rows.append(cells)
    rad = ([20] if base20_cell else [2] * 5) + [3] * 3
    return np.array(rows, dtype=np.int16), np.array(rad)


# ------------------------------------------------------------------ decoding
def distances(obs, C):
    return (obs[:, None, :] != C[None, :, :]).sum(2)          # N x 128


def decode(obs, C, t, chunk=4000):
    """Unique nearest codeword within t cells -> value, else -1 (trap)."""
    out = np.empty(len(obs), dtype=np.int16)
    for i in range(0, len(obs), chunk):
        d = distances(obs[i:i + chunk], C)
        mn = d.min(1)
        unique = (d == mn[:, None]).sum(1) == 1
        ok = (mn <= t) & unique
        out[i:i + chunk] = np.where(ok, d.argmin(1), -1)
    return out


def dmin_of(C):
    d = distances(C, C)
    d[np.arange(len(C)), np.arange(len(C))] = 99
    return int(d.min())


# ------------------------------------------------------------------ fault injection
def exhaustive(C, rad, k):
    """All k-cell fault patterns x all shifts x all 128 truths."""
    n = C.shape[1]
    vs, obs = [], []
    for cells in itertools.combinations(range(n), k):
        for shifts in itertools.product(*[range(1, rad[c]) for c in cells]):
            o = C.copy()
            for c, s in zip(cells, shifts):
                o[:, c] = (o[:, c] + s) % rad[c]
            obs.append(o)
            vs.append(np.arange(N_VALUES))
    return np.concatenate(vs), np.concatenate(obs)


def sampled(C, rad, k, count):
    n = C.shape[1]
    v = RNG.integers(0, N_VALUES, count)
    o = C[v].copy()
    for i in range(count):
        cells = RNG.choice(n, k, replace=False)
        for c in cells:
            o[i, c] = (o[i, c] + RNG.integers(1, rad[c])) % rad[c]
    return v, o


def faults(C, rad, k, count=60000, exhaustive_limit=700000):
    n = C.shape[1]
    total = math.comb(n, k) * N_VALUES * np.prod([1 + 0 for _ in range(k)])
    # rough size estimate for the exhaustive path
    est = math.comb(n, k) * N_VALUES * (float(np.mean(rad - 1)) ** k)
    if est <= exhaustive_limit:
        return exhaustive(C, rad, k) + ("exhaustive",)
    v, o = sampled(C, rad, k, count)
    return v, o, "sampled"


def classify(v, dec):
    trapped = dec == -1
    right = dec == v
    silent = ~trapped & ~right
    n = len(v)
    return 100 * right.sum() / n, 100 * trapped.sum() / n, 100 * silent.sum() / n


# ------------------------------------------------------------------ study
def part_decoder(C, t):
    return lambda obs: decode(obs, C, t)


def run():
    mt = find_ternary_modulus()
    print(f"smallest modulus separating all 20 ternary single-trit faults: {mt}")

    # --- locatability of single faults, by check modulus --------------------
    print("\nSINGLE-FAULT LOCATABILITY (distinct syndromes / faults to tell apart)")
    bin_deltas = [s * (1 << k) for k in range(8) for s in (1, -1)]
    ter_deltas = [s * 3 ** k for k in range(5) for s in (1, 2, -1, -2)]
    for name, mod in (("mod 19", 19), ("mod 20 (4x5)", 20), ("mod 28 (7x4)", 28),
                      ("mod 30 (5x6)", 30), (f"mod {mt}", mt)):
        b = len({d % mod for d in bin_deltas})
        t = len({d % mod for d in ter_deltas})
        z = any(d % mod == 0 for d in bin_deltas)
        zt = any(d % mod == 0 for d in ter_deltas)
        print(f"  {name:14s} binary bit flips: {b:2d}/{len(bin_deltas)}"
              f"{' (a flip is INVISIBLE)' if z else ''}"
              f"   ternary trit faults: {t:2d}/{len(ter_deltas)}{' (a fault is INVISIBLE)' if zt else ''}")

    # --- schemes -------------------------------------------------------------
    A19 = binary_scheme([19])
    A30 = binary_scheme([5, 6])
    A28 = binary_scheme([7, 4])
    B = ternary_scheme(mt)
    schemes = {
        "raw binary (7b)": raw_binary(),
        "raw ternary (5t)": raw_ternary(),
        "binary x ternary raw (7b+5t)": concat(raw_binary(), raw_ternary()),
        "CRT540 bits+tryte (5b+3t)": crt540(False),
        "CRT540 base20+tryte (1x20+3t)": crt540(True),
        "A19  bin+mod19+SECDED": A19,
        "A30  bin+CRT(5,6)+par": A30,
        "A28  bin+CRT(7,4)+par": A28,
        "B    ter+check+trit-par": B,
        "A19 + B joint decode": concat(A19, B),
    }

    print("\nSTORAGE AND GUARANTEES (from minimum distance of the 128 legal rows)")
    print(f"  {'scheme':32s} {'cells':>5s} {'info bits':>9s} {'d_min':>5s}  detects  corrects")
    info = {}
    for name, (C, rad) in schemes.items():
        dm = dmin_of(C)
        t = (dm - 1) // 2
        bitsinfo = float(np.sum(np.log2(rad)))
        info[name] = (dm, t)
        print(f"  {name:32s} {C.shape[1]:5d} {bitsinfo:9.1f} {dm:5d}  {dm - 1:>7d}  {t:>8d}")

    print("\nOUTCOMES for k simultaneous cell faults  (right / trapped / SILENT WRONG, %)")
    print("  decoder: unique nearest codeword within t cells, else trap")
    for k in (1, 2, 3, 4):
        print(f"\n  k = {k}")
        for name, (C, rad) in schemes.items():
            v, o, how = faults(C, rad, k)
            dm, t = info[name]
            dec = decode(o, C, t)
            r, tr, s = classify(v, dec)
            print(f"    {name:32s} {r:6.1f} / {tr:6.1f} / {s:6.2f}   [{how}, n={len(v)}]")

    # --- two independent sources + arbitration ------------------------------
    print("\nTWO INDEPENDENT SOURCES, each decoded alone, then arbitrated")
    nA = A19[0].shape[1]
    tA = (dmin_of(A19[0]) - 1) // 2
    tB = (dmin_of(B[0]) - 1) // 2
    CAB, radAB = concat(A19, B)
    for k in (1, 2, 3, 4):
        v, o, how = faults(CAB, radAB, k, count=120000)
        a = decode(o[:, :nA], A19[0], tA)
        b = decode(o[:, nA:], B[0], tB)
        both = (a != -1) & (b != -1)
        agree = both & (a == b)
        lenient = np.where(agree, a, np.where(both, -1, np.where(a != -1, a, b)))
        strict = np.where(agree, a, -1)
        print(f"\n  k = {k}  [{how}, n={len(v)}]")
        for label, dec in (("A alone", a), ("B alone", b),
                           ("arbitrated, lenient (one good source wins)", lenient),
                           ("arbitrated, strict  (both must agree)", strict)):
            r, tr, s = classify(v, dec)
            print(f"    {label:44s} {r:6.1f} / {tr:6.1f} / {s:6.2f}")

        # where do the sources fail on their own, and who rescues whom?
        a_silent = (a != -1) & (a != v)
        b_silent = (b != -1) & (b != v)
        if a_silent.any():
            print(f"    A silent-wrong cases: {a_silent.sum():6d} -> after lenient arbitration "
                  f"silent {(lenient[a_silent] != -1).__and__(lenient[a_silent] != v[a_silent]).sum():6d}"
                  f", trapped {(lenient[a_silent] == -1).sum():6d}, right {(lenient[a_silent] == v[a_silent]).sum():6d}")
        if b_silent.any():
            print(f"    B silent-wrong cases: {b_silent.sum():6d} -> after lenient arbitration "
                  f"silent {(lenient[b_silent] != -1).__and__(lenient[b_silent] != v[b_silent]).sum():6d}"
                  f", trapped {(lenient[b_silent] == -1).sum():6d}, right {(lenient[b_silent] == v[b_silent]).sum():6d}")
        both_silent_same = both & (a == b) & (a != v)
        print(f"    both sources wrong AND identical (the true common-mode hole): {both_silent_same.sum()}")


if __name__ == "__main__":
    run()
