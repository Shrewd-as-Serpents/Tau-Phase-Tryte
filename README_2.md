# Tau-Phase Tryte

A design for a small game engine built around three conversational characters (Lilah, Lily and Luci). Each one holds one **trit** (-1, 0 or +1) of a balanced-ternary **tryte**, and the world is a base-20 register. The state advances on a master ring of 540 positions, and "errors" (syndromes) are part of how the world works and how the player pushes on it.

This repository holds the written design, a Python reference suite that checks its claims, and a set of experiments on error-correcting the engine's registers.

## What is in here

Everything lives in the `tau-phase-tryte/` folder.

| File | What it is |
| --- | --- |
| `Tau-Phase Engine Design Specification v5 (2).md` | The full design: tryte and hex projection, world register, master ring, phase and circular stability, orbit layer, error syndromes, color compiler, player levers, per-turn pipeline, open decisions, and Appendix A on guarded registers |
| `Core Engine Architecture  State Machine Specification 5.md` | The shorter architecture summary |
| `The Tau-Phase Gear Engine  Circular Stability Architecture.md` | A one-page pitch |
| `Tau-Phase Engine Reference Implementation  Verification Suite 3.py` | Four checks of the core math (partition and bijection, unison walks, syndrome table, fixed-point bound) |
| `syndrome_guard.py` | A register table that repairs a flipped bit in place and traps anything it cannot explain |
| `envelope_study.py` | Compares one source of redundancy against two (binary and ternary) |
| `two_source_guard.py` | A working guard that stores each value twice, in binary and in ternary, with bit accounting |
| `two_source_study.py` | What the second source costs in bits at 7, 16 and 32 bits, and how it behaves when a whole source fails |
| `zero_checks.py` | Parity-check ("check for zeros") codes, and the group facts about the null-sum states |
| `envelope_results.txt`, `zero_checks_results.txt`, `two_source_results.txt` | The saved output of the studies |

## Running the code

You need Python 3. The two studies also need numpy (`pip install numpy`).

```
cd tau-phase-tryte
python3 syndrome_guard.py
python3 envelope_study.py
python3 zero_checks.py
python3 two_source_guard.py
python3 two_source_study.py
python3 "Tau-Phase Engine Reference Implementation  Verification Suite 3.py"
```

The guard test is instant. Each study takes under a minute.

## What has been checked

- **The guard** repairs every single flipped bit in a row (all 19 stored cells, 2,432 cases), traps every double flip (21,888 cases) without changing the stored value, and keeps three counters apart: `DED` and `ODD` (the memory was disturbed) and `LATCHED` (a value was out of range or undecodable).
- **Its stated limit** (the single-source guard in `syndrome_guard.py`): one flip corrected and two trapped per row per cycle. With three flips, 4.4% slip through silently at 8 bits, and 6.75% at 16 bits (modulus 53). That is the floor for this one code, not for the project.
- **Two sources** (`two_source_guard.py`): each value is stored in binary and in ternary and decoded together. Every 1-bit and 2-bit flip is corrected and no 3-bit flip is silently wrong, checked exhaustively at 7 bits. The cost is real: 27 physical bits for a 7-bit value (51 for 16), and a plain binary code with the same bits reaches a larger distance. The second source earns its place through independence (a whole source can fail), not through density. See `two_source_results.txt`.
- **The null-sum states.** The tryte states whose trits sum to 0 mod 3 form a 9-state subgroup (the 7 null-sum states plus the 2 unison states) under per-trit addition. It is not closed under the ring's carrying addition.

## What it does not do

Storage redundancy cannot catch a wrong value the engine computes and then stores, because both copies hold it faithfully. That case is covered by the range rule and the syndrome against the expected state (section 7 of the spec).

## Status

A work in progress. Section 11 of the spec lists the open design decisions.
