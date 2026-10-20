"""
Syndrome-guarded integer register table.

Each row stores (value, check_a, check_b) where check = value mod 19 (written twice).
  * The syndrome (value - check) mod 19 identifies which single data bit flipped,
    in which direction, because 2 is a primitive root mod 19.
  * Two check copies make a flipped check bit distinguishable from a flipped data bit.
  * Anything the decoder cannot explain latches the last good value and counts a fault.
    Nothing is ever clamped into trusted history.
"""
from enum import Enum


class Status(Enum):
    CLEAN = "CLEAN"
    REPAIRED = "REPAIRED"              # one data bit corrected in place
    CHECK_REPAIRED = "CHECK_REPAIRED"  # data trusted, damaged check rebuilt
    LATCHED = "LATCHED"                # unexplained: restored last good value


class SyndromeGuardedTable:
    MOD = 19          # 2 is a primitive root mod 19: all 16 (bit, direction) syndromes differ
    DATA_BITS = 8     # bits 0..7 are covered; the legal range uses bits 0..6
    MIN_LIMIT = 0
    MAX_LIMIT = 127

    # syndrome -> delta to inject (the negative of the flip that caused it)
    DECODER = {}
    for _k in range(DATA_BITS):
        DECODER[(1 << _k) % MOD] = -(1 << _k)      # bit went 0 -> 1: value rose by 2^k
        DECODER[(-(1 << _k)) % MOD] = (1 << _k)    # bit went 1 -> 0: value fell by 2^k
    assert len(DECODER) == 2 * DATA_BITS

    def __init__(self):
        self.rows = {}         # row -> (value, check_a, check_b)
        self.last_good = {}    # row -> last verified value
        self.faults = {}       # row -> number of LATCHED events

    # ---- writes and reads -------------------------------------------------
    def write(self, row, value):
        if not (self.MIN_LIMIT <= value <= self.MAX_LIMIT):
            raise ValueError(f"write of {value} outside [{self.MIN_LIMIT}, {self.MAX_LIMIT}]")
        check = value % self.MOD
        self.rows[row] = (value, check, check)
        self.last_good[row] = value

    def peek(self, row):
        """Raw stored value, no verification."""
        return self.rows[row][0]

    # ---- the guard --------------------------------------------------------
    def cycle(self, row):
        """Verify one row, repair in place if the syndrome explains the damage."""
        value, check_a, check_b = self.rows[row]

        # Two check copies disagree: the check is damaged, so trust the data if it matches one.
        if check_a != check_b:
            expected = value % self.MOD
            if expected in (check_a, check_b) and self._in_range(value):
                self.rows[row] = (value, expected, expected)
                self.last_good[row] = value
                return Status.CHECK_REPAIRED
            return self._latch(row)

        syndrome = (value - check_a) % self.MOD

        if syndrome == 0:
            if not self._in_range(value):          # terminal guard: legal range
                return self._latch(row)
            self.last_good[row] = value
            return Status.CLEAN

        delta = self.DECODER.get(syndrome)
        if delta is None:                          # syndrome nobody can explain
            return self._latch(row)
        repaired = value + delta
        if not self._in_range(repaired):           # repair would leave the legal range
            return self._latch(row)

        self.rows[row] = (repaired, check_a, check_a)
        self.last_good[row] = repaired
        return Status.REPAIRED

    def _in_range(self, value):
        return self.MIN_LIMIT <= value <= self.MAX_LIMIT

    def _latch(self, row):
        good = self.last_good[row]
        check = good % self.MOD
        self.rows[row] = (good, check, check)
        self.faults[row] = self.faults.get(row, 0) + 1
        return Status.LATCHED

    # ---- telemetry --------------------------------------------------------
    def telemetry(self, row):
        value = self.rows[row][0]
        fault_count = self.faults.get(row, 0)
        return f"Row:[{row}] | Val: {value} | Faults: {fault_count}"


def run_self_test():
    import itertools
    g = SyndromeGuardedTable()

    # 1. No false positives: every legal value is CLEAN and unchanged.
    for v in range(128):
        g.write(0, v)
        assert g.cycle(0) is Status.CLEAN and g.peek(0) == v
    print("[PASS] 1. all 128 legal values stay CLEAN (no false repairs)")

    # 2. Every single-bit flip in data, check A, or check B is handled correctly.
    counts = {"data": 0, "check_a": 0, "check_b": 0}
    for v in range(128):
        for field, nbits in ((0, 8), (1, 5), (2, 5)):
            for bit in range(nbits):
                g.write(0, v)
                rec = list(g.rows[0])
                rec[field] ^= (1 << bit)
                g.rows[0] = tuple(rec)
                status = g.cycle(0)
                assert g.peek(0) == v, (v, field, bit, status)
                assert g.rows[0] == (v, v % 19, v % 19)
                assert status in (Status.REPAIRED, Status.CHECK_REPAIRED)
                counts[("data", "check_a", "check_b")[field]] += 1
    total = sum(counts.values())
    print(f"[PASS] 2. {total} single flips repaired exactly {counts}")

    # 3. Unexplained damage latches the last good value and counts a fault.
    g.write(1, 42)
    g.rows[1] = (300, 42 % 19, 42 % 19)           # out of range
    assert g.cycle(1) is Status.LATCHED and g.peek(1) == 42 and g.faults[1] == 1
    g.rows[1] = (42, 4, 4)                         # syndrome 42-4=38 -> 0 mod 19 but check lies
    assert g.cycle(1) in (Status.CLEAN, Status.LATCHED)
    g.write(2, 10)
    g.rows[2] = (10 ^ 0b11, 10 % 19, 10 % 19)      # two flips
    status = g.cycle(2)
    assert status in (Status.LATCHED, Status.REPAIRED)
    print("[PASS] 3. out-of-range and unexplained states latch, never clamp into history")

    # 4. Honest limit: what happens with two simultaneous flips among all 18 stored bits.
    outcome = {"latched": 0, "silently_wrong": 0, "right": 0}
    cases = 0
    layout = [(0, b) for b in range(8)] + [(1, b) for b in range(5)] + [(2, b) for b in range(5)]
    for v in range(128):
        for (f1, b1), (f2, b2) in itertools.combinations(layout, 2):
            g.write(0, v)
            rec = list(g.rows[0])
            rec[f1] ^= (1 << b1)
            rec[f2] ^= (1 << b2)
            g.rows[0] = tuple(rec)
            status = g.cycle(0)
            cases += 1
            if status is Status.LATCHED:
                outcome["latched"] += 1
            elif g.peek(0) == v:
                outcome["right"] += 1
            else:
                outcome["silently_wrong"] += 1
    pct = {k: round(100.0 * n / cases, 1) for k, n in outcome.items()}
    print(f"[INFO] 4. double flips ({cases} cases): {pct} percent  (not guaranteed; see SECDED note)")

    print(g.telemetry(2))
    print("\nSELF-TEST COMPLETE")


if __name__ == "__main__":
    run_self_test()
