"""
Syndrome-guarded integer register table, SECDED edition.

Each row stores (value, check_a, check_b, parity):
  value    8-bit data, legal range 0..127
  check_*  value mod 19, written twice (2 is a primitive root mod 19, so every
           single data-bit flip in either direction has its own syndrome)
  parity   even parity over all 18 other bits

Fault model (stated, not hand-waved): at most TWO flipped cells per row per cycle.
  * 1 flip  -> corrected in place (data, either check, or the parity cell)
  * 2 flips -> always trapped, never repaired from a guess
  * 3+ flips-> not guaranteed. Some are trapped, some miscorrect (SECDED limit).

Nothing is ever clamped into trusted history. Anything unexplained restores the
last good value and is counted under the kind of failure it was.
"""
from collections import Counter
from enum import Enum


class Status(Enum):
    CLEAN = "CLEAN"
    REPAIRED = "REPAIRED"                  # one data bit corrected in place
    CHECK_REPAIRED = "CHECK_REPAIRED"      # data trusted, damaged check rebuilt
    PARITY_REPAIRED = "PARITY_REPAIRED"    # only the parity cell was damaged, rebuilt
    LATCHED = "LATCHED"                    # semantic: out of range / undecodable single
    DED = "DED"                            # physical: even-weight multi-flip trapped
    ODD_UNCORRECTABLE = "ODD"              # physical: odd-weight (>=3) multi-flip trapped


TRAPS = (Status.LATCHED, Status.DED, Status.ODD_UNCORRECTABLE)


class SyndromeGuardedTable:
    MOD = 19
    DATA_BITS = 8
    MIN_LIMIT = 0
    MAX_LIMIT = 127

    DECODER = {}      # syndrome -> delta to inject (negative of the causing flip)
    for _k in range(DATA_BITS):
        DECODER[(1 << _k) % MOD] = -(1 << _k)
        DECODER[(-(1 << _k)) % MOD] = (1 << _k)
    assert len(DECODER) == 2 * DATA_BITS

    def __init__(self):
        self.rows = {}        # row -> (value, check_a, check_b, parity)
        self.last_good = {}   # row -> last verified value
        self.counts = {}      # row -> Counter of Status names (every outcome)

    # ---- helpers ----------------------------------------------------------
    @staticmethod
    def _parity(value, check_a, check_b):
        bits = (value & 0xFF) | ((check_a & 0x1F) << 8) | ((check_b & 0x1F) << 13)
        return bin(bits).count("1") & 1

    def _store(self, row, value):
        c = value % self.MOD
        self.rows[row] = (value, c, c, self._parity(value, c, c))
        self.last_good[row] = value

    def _in_range(self, value):
        return self.MIN_LIMIT <= value <= self.MAX_LIMIT

    @staticmethod
    def _one_bit(x):
        return x > 0 and (x & (x - 1)) == 0

    def _note(self, row, status):
        self.counts.setdefault(row, Counter())[status.name] += 1
        return status

    def _trap(self, row, status):
        self._store(row, self.last_good[row])      # restore, never clamp
        return self._note(row, status)

    # ---- writes and reads -------------------------------------------------
    def write(self, row, value):
        if not self._in_range(value):
            raise ValueError(f"write of {value} outside [{self.MIN_LIMIT}, {self.MAX_LIMIT}]")
        self._store(row, value)

    def peek(self, row):
        return self.rows[row][0]

    # ---- the guard --------------------------------------------------------
    def cycle(self, row):
        value, ca, cb, stored_parity = self.rows[row]
        parity_bad = self._parity(value, ca, cb) != stored_parity   # odd number of flips
        checks_differ = ca != cb
        checks_invalid = ca >= self.MOD or cb >= self.MOD      # a 5-bit field can hold 19..31
        syndrome = (value - ca) % self.MOD

        if not parity_bad:
            # Even number of flips (0, 2, ...). Any anomaly with matching parity is a
            # multi-flip, so it is trapped before the decoder can mistake it for one.
            if checks_differ or checks_invalid or syndrome != 0:
                return self._trap(row, Status.DED)
            if not self._in_range(value):
                return self._trap(row, Status.LATCHED)
            self.last_good[row] = value
            return self._note(row, Status.CLEAN)

        # Odd number of flips (1, 3, ...). Treat as one flip and see if exactly one
        # explanation fits; otherwise it is an uncorrectable odd-weight failure.
        if checks_differ:
            expected = value % self.MOD
            # one copy must match the data, the other must be exactly ONE bit away from it
            good, bad = (ca, cb) if ca == expected else (cb, ca)
            if good == expected and self._one_bit(bad ^ expected) and self._in_range(value):
                self._store(row, value)
                return self._note(row, Status.CHECK_REPAIRED)
            return self._trap(row, Status.ODD_UNCORRECTABLE)

        if checks_invalid:
            return self._trap(row, Status.ODD_UNCORRECTABLE)

        if syndrome == 0:
            # data and checks agree; the only thing wrong is the parity cell itself
            if not self._in_range(value):
                return self._trap(row, Status.LATCHED)
            self._store(row, value)
            return self._note(row, Status.PARITY_REPAIRED)

        delta = self.DECODER.get(syndrome)
        if delta is None:
            return self._trap(row, Status.ODD_UNCORRECTABLE)
        repaired = value + delta
        # The syndrome claims "bit k flipped". That is only believable if undoing it
        # really changes exactly one bit; integer add/subtract can carry across several.
        if not self._one_bit(repaired ^ value) or repaired % self.MOD != ca:
            return self._trap(row, Status.ODD_UNCORRECTABLE)
        if not self._in_range(repaired):
            return self._trap(row, Status.LATCHED)
        self._store(row, repaired)
        return self._note(row, Status.REPAIRED)

    # ---- telemetry --------------------------------------------------------
    def telemetry(self, row):
        c = self.counts.get(row, Counter())
        return (f"Row:[{row}] | Val: {self.rows[row][0]}"
                f" | LATCHED: {c['LATCHED']} | DED: {c['DED']} | ODD: {c['ODD']}"
                f" | repaired: {c['REPAIRED'] + c['CHECK_REPAIRED'] + c['PARITY_REPAIRED']}")

    def faults(self, row):
        c = self.counts.get(row, Counter())
        return {"latched": c["LATCHED"], "ded": c["DED"], "odd": c["ODD"]}


# ---------------------------------------------------------------------------
def _flip(g, row, cells):
    """Flip stored cells: (field, bit) with field 0=value 1=check_a 2=check_b 3=parity."""
    rec = list(g.rows[row])
    for field, bit in cells:
        rec[field] ^= (1 << bit)
    g.rows[row] = tuple(rec)


LAYOUT = ([(0, b) for b in range(8)] + [(1, b) for b in range(5)]
          + [(2, b) for b in range(5)] + [(3, 0)])


def run_self_test():
    import itertools
    g = SyndromeGuardedTable()

    # 1. No false positives.
    for v in range(128):
        g.write(0, v)
        assert g.cycle(0) is Status.CLEAN and g.peek(0) == v
    print("[PASS] 1. all 128 legal values stay CLEAN")

    # 2. Every single flip in ALL 19 cells (parity cell included) is repaired exactly.
    seen = Counter()
    for v in range(128):
        for cell in LAYOUT:
            g.write(0, v)
            _flip(g, 0, [cell])
            st = g.cycle(0)
            assert g.peek(0) == v and g.rows[0] == (v, v % 19, v % 19, g._parity(v, v % 19, v % 19)), (v, cell, st)
            assert st in (Status.REPAIRED, Status.CHECK_REPAIRED, Status.PARITY_REPAIRED), (v, cell, st)
            seen[st.name] += 1
    print(f"[PASS] 2. {sum(seen.values())} single flips repaired exactly, record rebuilt: {dict(seen)}")

    # 3. Regression: a damaged parity cell must not poison the NEXT single flip.
    g.write(0, 10)
    _flip(g, 0, [(3, 0)])
    assert g.cycle(0) is Status.PARITY_REPAIRED
    _flip(g, 0, [(0, 2)])
    assert g.cycle(0) is Status.REPAIRED and g.peek(0) == 10
    print("[PASS] 3. parity-cell damage is rebuilt; a later single flip is still repaired, not called DED")

    # 4. Every double flip over all 19 cells is trapped and the value is restored.
    outcome = Counter()
    for v in range(128):
        for a, b in itertools.combinations(LAYOUT, 2):
            g.write(0, v)
            _flip(g, 0, [a, b])
            st = g.cycle(0)
            assert st in TRAPS, (v, a, b, st)
            assert g.peek(0) == v                       # last good restored
            outcome[st.name] += 1
    print(f"[PASS] 4. {sum(outcome.values())} double flips: all trapped, value intact: {dict(outcome)}")

    # 5. Counters are separate: DED, LATCHED and ODD never share a bucket.
    t = SyndromeGuardedTable()
    t.write(0, 42); _flip(t, 0, [(0, 0), (0, 1)]); assert t.cycle(0) is Status.DED
    t.write(1, 42); t.rows[1] = (200, 200 % 19, 200 % 19, t._parity(200, 200 % 19, 200 % 19))
    assert t.cycle(1) is Status.LATCHED
    assert t.faults(0) == {"latched": 0, "ded": 1, "odd": 0}
    assert t.faults(1) == {"latched": 1, "ded": 0, "odd": 0}
    print("[PASS] 5. DED and LATCHED are counted separately")
    print("       ", t.telemetry(0))
    print("       ", t.telemetry(1))

    # 6. Honest limit: three flips are not guaranteed.
    out = Counter()
    for v in range(128):
        for cells in itertools.combinations(LAYOUT, 3):
            g.write(0, v)
            _flip(g, 0, list(cells))
            st = g.cycle(0)
            if st in TRAPS:
                out["trapped"] += 1
            elif g.peek(0) == v:
                out["right"] += 1
            else:
                out["SILENT_WRONG"] += 1
    n = sum(out.values())
    print(f"[INFO] 6. triple flips ({n} cases): "
          + ", ".join(f"{k} {100.0 * c / n:.1f}%" for k, c in out.items())
          + "  (outside the stated fault model)")
    print("\nSELF-TEST COMPLETE")


if __name__ == "__main__":
    run_self_test()
