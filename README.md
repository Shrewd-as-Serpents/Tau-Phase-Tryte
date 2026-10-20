# Tau-Phase Engine: Design Specification v5

Oct 19, 2026 · @fawn

## 1. Overview

The engine is a deterministic, integer-only state machine. Three entities (Lilah, Lily, Luci) each commit a stance every turn, the order they speak in decides how much each stance counts, and the world responds. Deadlocks, syndromes and singularities are not failures: they are the surfaces the player works on.

**Design principles**

- **Integer-exact.** Every transition is integer arithmetic. Trigonometry and orbit shapes come from baked lookup tables, never from runtime floating point.
- **Order is weight.** Speaking order assigns the weights 1, 3 and 9, so the player steers the world by reordering speakers.
- **Errors are mechanics.** A syndrome, a deadlock or an R = 0 singularity is a state the player can read and exploit.
- **One source of truth.** The master integer X in Z\_540 fixes both the ternary and the vigesimal state.

**Layers**

| Layer | State | Role |
| --- | --- | --- |
| Skeleton | Z\_27 rotor, Z\_20 world register, Z\_540 master ring | Discrete state and its bijections |
| Hex projection | Consensus s, tension (u, v) | Splits agreement from disagreement |
| Nervous system | Phase delta, n = 3 circular window | Stability, singularity |
| Orbit layer | Baked Kepler table | Turns state into continuous motion |
| Syndrome | Delta V mod 20 | Error detection the player can repair or exploit |
| Chromatic compiler | Six-level priority ladder | One unambiguous color per token |
| Levers | Five player actions | The gameplay surface |

This version restores material that was lost between drafts 4 and 5 (the deadlock latch, history freeze, mirror aid, aliasing scope, Scenario A) and adds the hex projection and orbit layer as first-class parts.

## 2. The ternary rotor and hex projection

Three trits, weighted 1, 3 and 9 by speaking order, give 27 states. Seven are deadlocks, twenty are decisive, and projecting them onto a triangle splits every state into consensus (how much they agree) and tension (how they disagree).

**Trits and weights.** Each entity commits t in {-1, 0, +1}. The first mover has weight 1 (T0), the second 3 (T1), the last 9 (T2).

```latex
V = 9\,T_2 + 3\,T_1 + T_0 \in [-13, +13], \qquad T = V \bmod 27
```

The inverse is bal\_27(u), which maps a residue back to \[-13, +13\]. Because 9 > 3 + 1, a non-zero last mover fixes the sign of V and keeps |V| in \[5, 13\]. A last mover at 0 clamps V to \[-4, +4\] (the anchor clamp).

**The 7 + 20 partition.** Let s = T2 + T1 + T0, the unweighted trit sum.

- **Deadlock set Z\_7** (s = 0): V in {-8, -6, -2, 0, +2, +6, +8}. This is the origin plus the six orderings of {-1, 0, +1}.
- **Decisive set D\_20** (s not 0): V in {±1, ±3, ±4, ±5, ±7, ±9, ±10, ±11, ±12, ±13}.

**Hex projection.** Put the three entities on a triangle at 0, 120 and 240 degrees and let each trit push along its own direction. Because the three directions sum to zero, only the differences between trits survive. Using the last mover as the reference:

```latex
u = T_0 - T_2, \quad v = T_1 - T_2, \quad H = u^2 - uv + v^2 = \tfrac12\sum_{i<j}(t_i - t_j)^2
```

The pair (u, v) is the tension coordinate on a hexagonal lattice, and H is its squared distance from the center, an integer. The common part of the trits is the consensus s, which ranges from -3 to +3. Checked by exhaustive enumeration:

- The 27 states land on **19 distinct lattice points**. Eight states share a point with another state because they differ only by a common shift of all three trits.
- Consensus counts for s = -3 ... +3 are 1, 3, 6, 7, 6, 3, 1.

| Tension H | States | Meaning | Where they live |
| --- | --- | --- | --- |
| 0 | 3 | Unanimous, or all neutral | V = 0 (deadlock) and V = ±13 (decisive) |
| 1 | 12 | One entity off by one step | All decisive |
| 3 | 6 | All three trits distinct | All deadlocks |
| 4 | 6 | A 2-versus-1 split with opposite signs | All decisive (V = ±5, ±7, ±11) |

So a three-way disagreement is exactly a deadlock, and every deadlock except the origin has tension 3.

**Why the unison walk works.** Sweeping the last mover through -1, 0, +1 avoids s = 0 only if |T1 + T0| = 2. That leaves exactly two safe lock-ins, (T1, T0) = (+1, +1) or (-1, -1). No other first-two combination stays decisive for all three turns.

## 3. The world register and deadlock as a place

The world register G in {0..19} follows the decisive states through the bijection phi, and a deadlock no longer leaves a hole: G holds still while the player keeps a position on the tension ring.

**Bars and dots.** G splits as Bar = floor(G / 5) in {0..3} and Dot = G mod 5 in {0..4}. Sorting D\_20 in ascending order defines phi(V) = G. Each cell shows V and its trits (T2, T1, T0):

| Bar (G) | Dot 0 | Dot 1 | Dot 2 | Dot 3 | Dot 4 |
| --- | --- | --- | --- | --- | --- |
| 0 (G 0-4) | -13 `---` | -12 `--0` | -11 `--+` | -10 `-0-` | -9 `-00` |
| 1 (G 5-9) | -7 `-+-` | -5 `-++` | -4 `0--` | -3 `0-0` | -1 `00-` |
| 2 (G 10-14) | +1 `00+` | +3 `0+0` | +4 `0++` | +5 `+--` | +7 `+-+` |
| 3 (G 15-19) | +9 `+00` | +10 `+0+` | +11 `++-` | +12 `++0` | +13 `+++` |

**Antipodal symmetry.** Negating all three trits reflects the register:

```latex
\phi(-V) = 19 - \phi(V), \qquad \text{Bar} \mapsto 3 - \text{Bar}, \quad \text{Dot} \mapsto 4 - \text{Dot}
```

Every mechanism therefore has an exact mirror twin: the room at G has a counterpart at 19 - G.

**World position is a pair.** The world holds (G, L), where L = (u, v) is the live tension coordinate from section 2. G is the primary position and moves only through decisive states. L is always defined, even in a deadlock.

**Deadlock behavior.** Each turn the engine takes one of two branches.

1. **V in D\_20.** Clear F\_deadlock. In a free-sync room G becomes phi(V). In a syndrome-locked room G stays at G\_lock until the syndrome is solved. Push T into the n = 3 history window.
2. **V in Z\_7.** Set F\_deadlock to 1. G keeps its previous value. The history window is frozen, so deadlocks never pollute the circular statistics. The syndrome is NULL. The master state X still exists, built from the current T and the latched G. Control passes to the Purple handler.

During a deadlock the player is not stuck at a point. All six non-origin deadlocks are orderings of {-1, 0, +1} with tension 3, so reordering the speakers walks the player around the six-point tension ring while G stays put. Reordering alone can never leave the ring, which is why a deadlock needs at least one changed stance to escape. The origin (0, 0, 0) sits at the center of that ring.

## 4. The master ring and the pivot mirror

Because 27 and 20 share no factor, the pair (T, G) packs into one integer X in Z\_540, and the mod-27 mirror T -> 2P - T turns every 120-degree triad into a one-step puzzle.

**CRT bus.** Any ternary state T in {0..26} and vigesimal state G in {0..19} combine uniquely:

```latex
X = (460\,T + 81\,G) \bmod 540, \qquad T = X \bmod 27, \quad G = X \bmod 20
```

The constants are the CRT idempotents: 460 is 1 mod 27 and 0 mod 20, and 81 is 0 mod 27 and 1 mod 20.

**Angular units.** One mod-540 step is 2/3 degree (40 arcminutes). One ternary tooth is 20 steps (13 degrees 20 minutes), one vigesimal tooth is 27 steps (18 degrees), and a 120-degree triad step is exactly 9 ternary teeth, the weight of the last mover.

**The mod-1080 ring is only a unit change.** Earlier drafts called mod 1080 a double-cover mirror ring. It is not: the embedding y = 40 T is just Z\_27 rescaled, so every mirror on it is a mirror on Z\_27. Its one real use is display, since 1080 gives three ticks per whole degree. This draft keeps it as an optional rendering unit and drops it from the logic.

**Pivot mirror.** For any pivot state P on the ternary rotor:

```latex
\mathcal{M}(T;\,P) = (2P - T) \bmod 27
```

It is an involution that fixes P. Negating all three trits is the special case P = 0.

**Triads.** Moving by 9 teeth changes only the last mover's trit. So {P - 9, P, P + 9} is always the same (T1, T0) with T2 taking all three values, and the pivot mirror turns either end into the other. The 27 states split into 9 such triads:

- 7 triads contain at least one deadlock state.
- 2 triads are fully decisive: (T1, T0) = (+1, +1) with V in {-5, +4, +13}, and (-1, -1) with V in {-13, -4, +5}.

This is the structure behind the unison walk in section 9. A mirror pulse can only be committed if its result is decisive, so it works only on those two triads.

## 5. The nervous system: phase and circular stability

Two gauges read the machine: a phase delta that drifts every step, and a circular-statistics window over the last three committed states. Both run on integers and a baked table.

**Phase delta.** Each modulus M maps to the unit circle by theta\_M(x) = (x / M) tau, with tau = 2 pi. The Z\_20 grid and Z\_27 rotor drift apart at an exact rate:

```latex
\Delta\theta(x) = \left(\tfrac{x}{20} - \tfrac{x}{27}\right)\tau = \tfrac{7x}{540}\,\tau \pmod{\tau}
```

- One step shifts the phase by 7/540 tau (4 degrees 40 minutes).
- A full ternary cycle (27 steps) leaves Gear 20 at 27 mod 20 = 7, a vernier precession of +0.35 tau (126 degrees).
- Three ternary cycles (81 steps) land one vigesimal tooth ahead, +0.05 tau (18 degrees).

Regimes are decided on the integer r = (7x) mod 540, with no floating point:

| Regime | Phase delta | Integer r | Share of cycle | Effect |
| --- | --- | --- | --- | --- |
| Constructive | under 0.15 tau or over 0.85 tau | r < 81 or r > 459 | 30% | Structural lock, low friction, stable harmonics |
| Quadrature | 0.15 to 0.36 tau, 0.64 to 0.85 tau | 81-194 or 346-459 | 42% | Peak kinetic transfer, active transitions |
| Destructive | 0.36 to 0.64 tau | 195-345 | 28% | Cancellation, maximum resistance, inverted rules |

**Circular stability window.** Over the last n = 3 committed decisive states, with positions x\_i on a ring of size M:

```latex
C = \tfrac1n\sum \cos\tfrac{\tau x_i}{M}, \quad S = \tfrac1n\sum \sin\tfrac{\tau x_i}{M}, \quad R = \sqrt{C^2 + S^2}, \quad \sigma = \frac{\sqrt{-2\ln R}}{\tau}
```

Swapping one state changes the mean resultant by up to 2/3, so a single injected state is a strong move.

| Regime | R | sigma | Meaning |
| --- | --- | --- | --- |
| Coherent lock | above 0.85 | under 0.091 tau | Tightly grouped, predictable. A long run at R = 1 raises a stagnation warning |
| Dynamic spread | 0.35 to 0.85 | 0.091 to 0.231 tau | Normal variance |
| High wobble | under 0.35 | over 0.231 tau | Scattered, instability grows with sigma |

**Integer evaluation.** Two 540-entry signed 16-bit tables hold cos and sin scaled by 2^14 = 16384. A state on ring M indexes the table at (540 / M) x mod 540, so M = 27 uses 20x and M = 20 uses 27x. With sums over the three entries:

```latex
R^2 = \frac{C_{\text{sum}}^2 + S_{\text{sum}}^2}{9\cdot 2^{28}}
```

Before taking the logarithm, clamp R to \[0.000001, 1\]. Table rounding makes R slightly exceed 1 for identical states (up to about 1.00004), which would otherwise crash the square root.

**Singularity (R = 0).** The primary trigger is combinatorial and order-independent: every pair of states differs by M/3 or 2M/3 (this needs 3 to divide M, so it applies on M = 27 and 540). A backup trigger fires when C\_sum^2 + S\_sum^2 is below epsilon = 64. No division by zero or ln(0) ever occurs. Measured bounds:

- Exact triads round to a squared norm of at most 1 across all 180 triads on the 540 table. The plus-or-minus 0.5 rounding bound gives at most 2.
- The nearest non-singular window has squared norm 36,101 on M = 540 and 14,466,042 on M = 27.

Epsilon = 64 therefore catches every rounding artifact with no false positives.

## 6. The orbit layer

The orbit layer turns state into continuous motion: consensus sets the orbit's size, tension sets how stretched it is, and the syndrome kicks its phase. Logic reads only integers from a baked table, so the motion is exact and replayable.

**Inputs.** The three mappings below are defaults chosen for this draft (see section 11); each can be swapped without touching the rest.

| Quantity | Rule | Values |
| --- | --- | --- |
| Semi-major axis a | 1 + abs(s) | 1, 2, 3, 4 (a deadlock has s = 0, so a = 1 and the orbit never collapses) |
| Eccentricity e | H / 5 | 0, 0.2, 0.6, 0.8 for H = 0, 1, 3, 4 |
| Mean anomaly index m | (7x + 20 \* burn) mod 540 | 7x is the phase delta of section 5; burn = delta V while a syndrome is unresolved, else 0 |

Using the phase delta as the clock means the orbit advances at the same rate as the vernier drift. A burn of delta V shifts the phase by delta V ternary teeth (20 ticks each), so the syndrome literally kicks the orbit.

**Baked tables.** Kepler's equation has no closed form, so it is solved once offline and shipped as integers. Four rows (one per H in {0, 1, 3, 4}) of 540 entries each:

```latex
M = E - e\sin E, \qquad \nu = 2\arctan\!\Big(\sqrt{\tfrac{1+e}{1-e}}\tan\tfrac E2\Big), \qquad \tfrac{r}{a} = 1 - e\cos E
```

- **NU\[H\]\[m\]** is the true anomaly in 540-tick units, rounded to the nearest tick.
- **RHO\[H\]\[m\]** is r / a in Q.14 fixed point (16384 means 1.0).
- The world position in polar form is angle NU\[H\]\[m\] and radius a \* RHO\[H\]\[m\] / 16384, both integers. A renderer may convert to Cartesian with floats, but no gameplay comparison may.

**Verified properties.** The tables total 8,640 bytes and were generated with a Newton solver, then checked:

- Every table value sits at least 0.00008 away from a rounding boundary, so any correct math library rebuilds identical tables.
- Row H = 0 is the identity with constant radius. Every row has NU\[0\] = 0 and NU\[270\] = 270, and is mirror-symmetric: NU\[540 - m\] + NU\[m\] is 0 mod 540.
- Radius runs from (1 - e) to (1 + e) times a.
- The orbit speeds up near the close point and nearly stalls at the far point, as shown below.

| H | e | Largest deviation from the mean clock | Fastest advance per tick | Radius range (times a) |
| --- | --- | --- | --- | --- |
| 0 | 0 | 0 ticks | 1 | 1.00 |
| 1 | 0.2 | 35 ticks | 2 | 0.80 to 1.20 |
| 3 | 0.6 | 108 ticks | 5 | 0.40 to 1.60 |
| 4 | 0.8 | 154 ticks | 15 | 0.20 to 1.80 |

SHA-256 of the table bytes (NU rows then RHO rows, little-endian 16-bit, rows in order H = 0, 1, 3, 4): `0751765e175c5af981839cde57b0d6f8974217bd6125ca953abd31ec1ac786eb`.

**What it means in play.** The sharpest disagreement (H = 4, a 2-versus-1 split) gives the sharpest moments: a long near-stall followed by a sweep at 15 times the mean speed. A deadlock (H = 3) is not calm; it runs an elongated orbit. Unanimity (H = 0) is a perfect circle.

## 7. Error syndromes and aliasing

A syndrome tells the player which mover is out of step and by how much. It is exact for a single-mover, single-step error and deliberately ambiguous beyond that, and the ambiguity is a puzzle surface.

**Computation.** The environment holds an expected state G, so V\_exp = phi^-1(G). The engine finds the signed distance inside Z\_27 first, and only then reduces mod 20, so the 26-to-0 wraparound never corrupts it:

```latex
\Delta V = \operatorname{bal}_{27}\big((T_{act} - T_{exp}) \bmod 27\big) \in [-13, +13], \qquad S_{err} = \Delta V \bmod 20
```

A syndrome exists only when V\_act is decisive. If the actual state falls in Z\_7 the syndrome is NULL and the token shows Purple. Of the 78 single-step, single-mover changes that can start from a decisive state, 30 land in Z\_7 and show a deadlock, not a syndrome.

**Scope of unique identification.** Delta V spans 27 values and S\_err only 20 residues.

- Delta V = 0 gives S\_err = 0, and S\_err = 0 happens only for Delta V = 0. This was checked across all 400 pairs of decisive states, so a zero-syndrome lock has no alias.
- |Delta V| of 6 or less maps one-to-one (S\_err in 0..6 or 14..19).
- S\_err in 7..13 is two-to-one: Delta V = r or Delta V = r - 20.
- Single-mover, single-step errors are always distinct: Delta V in {+1, -1, +3, -3, +9, -9} gives S\_err in {1, 19, 3, 17, 9, 11}. This was confirmed over every such change starting from a decisive state.

| Class | S\_err | Delta V | Diagnosis |
| --- | --- | --- | --- |
| Phase-locked | 0 | 0 | Rotor matches the world state |
| 1st-mover drift | 1 or 19 | +1 or -1 | Unique, micro-correction |
| 2nd-mover shift | 3 or 17 | +3 or -3 | Unique, buffered regional shift |
| Last-mover or alias | 9 or 11 | +9 or -11 (for 9); -9 or +11 (for 11) | Last-mover override, or a multi-mover alias |
| Compound desync | 2, 4, 5, 6, 7, 8, 10, 12, 13, 14, 15, 16, 18 | other values | Several movers, or a full polarity flip |

**Aliasing cases.**

- **Multi-mover.** A shift of +9 +3 -1 = +11 gives S\_err = 11, the same as a single last-mover step of -9.
- **Full flip.** A last-mover flip of two trit steps is 18, which wraps in Z\_27 to -9 or +9. So a flip looks like an opposite single step before the mod-20 reduction even happens.
- **Dual-register locks.** Ordinary diagnostics read only S\_err, which allows the exploits below. A high-precision lock reads the signed Delta V alongside S\_err whenever S\_err is in 7..13.

**Alias table for a lock at G = 12 (V\_exp = +4).** For each non-zero target dial reading in 7..13, both states that produce it:

| S\_err | Delta V positive | State | Delta V negative | State |
| --- | --- | --- | --- | --- |
| 7 | +7 | +11 `++-` | -13 | -9 `-00` |
| 8 | +8 | +12 `++0` | -12 | -8 (deadlock) |
| 9 | +9 | +13 `+++` | -11 | -7 `-+-` |
| 10 | +10 | -13 `---` | -10 | -6 (deadlock) |
| 11 | +11 | -12 `--0` | -9 | -5 `-++` |
| 12 | +12 | -11 `--+` | -8 | -4 `0--` |
| 13 | +13 | -10 `-0-` | -7 | -3 `0-0` |

For this lock, dial readings 8 and 10 have only one usable state, because the other alias is a deadlock. Alias puzzles should be designed against this table, not assumed to be two-way.

**Trit saturation.** A trit cannot leave {-1, 0, +1}. A mover at +1 can shift by -1 or -2, a mover at 0 by -1 or +1, and a mover at -1 by +1 or +2. Some "add one" repairs are therefore unavailable, and puzzles must account for that.

## 8. The chromatic compiler

Every token an entity speaks gets exactly one color from a six-rule ladder, evaluated top to bottom, and the ladder leaves no unmapped case. Color is a readout of the math, so the player can read the machine from the dialogue.

**Channels.** Telemetry splits in two so simultaneous conditions never fight:

1. **Token color** (this ladder): per token, from the speaker's trit, the syndrome, the singularity flags and the phase regime.
2. **Background world shader**: driven continuously by the phase delta and stability R. V sets global intensity and polarity, sigma drives camera shake, and the orbit of section 6 drives ambient motion.

**The ladder.** Let t be the speaker's trit.

| Priority | Color | Condition (first match wins) | Meaning |
| --- | --- | --- | --- |
| 1 | Purple | V in Z\_7, or the R = 0 singularity (combinatorial triad or norm below epsilon) | Deadlock or three-way cancellation. G latches, local rules invert |
| 2 | Yellow | S\_err not in {0, 1, 19} | Syndrome alert: 2nd or last mover shifted, or a compound desync |
| 3 | Green | S\_err in {1, 19}, or (S\_err = 0 and t = +1 and phase is Constructive) | Phase-locked: a micro-drift is self-correcting, or constructive alignment is confirmed |
| 4 | Blue | S\_err = 0 and t = 0 | Anchor: the entity commits weight 0 |
| 5 | Orange | S\_err = 0 and t = +1 (phase not Constructive) | Catalyst: positive weight under shear |
| 6 | Red | S\_err = 0 and t = -1 | Restrictor: negative weight, rising resistance |

**Why it is total.** After rules 1 and 2, S\_err is in {0, 1, 19}. For 1 or 19, Green fires whatever t is. For S\_err = 0, t = 0 is Blue, t = +1 is Green or Orange depending only on the phase, and t = -1 is Red. Every combination resolves to one color.

**Note on rooms.** In a free-sync room the expected state always equals the actual state, so S\_err is always 0 and the ladder reduces to trit color plus phase. Yellow and the S\_err = 1 or 19 form of Green appear only in syndrome-locked rooms.

This draft restores the "constructive +1" clause of rule 3 that was lost in draft 5.

## 9. Player levers

The player has six levers, and each one is a piece of the math above made tangible: reordering speakers, clamping extremes, mirroring a room, repairing or exploiting a syndrome, walking a triad, and steering tension.

| Lever | What the player does | What the math does |
| --- | --- | --- |
| 1. Turn-order interception | Reorders who speaks first, second and last | Permutes the weights 1, 3, 9 |
| 2. Anchor clamp | Baits the last mover into 0 | T2 = 0 confines V to \[-4, +4\] |
| 3. Antipodal mirror | Inverts every speaker's stance | V to -V, G to 19 - G |
| 4. Syndrome puzzles | Shifts speakers to cancel or exploit a dial reading | Adds +-1, +-3, +-9 to Delta V |
| 5. Unison walk and pivot mirror | Holds two movers, cycles the last | Visits a 120-degree triad, firing R = 0 |
| 6. Tension steering | Moves dissenters toward or away from the group | Changes H, hence orbit shape |

### 1. Turn-order interception

With fixed stances {+1, +1, -1}, only the order changes the world:

- The -1 speaker last: V = -5, G = 6 (restrictor regime).
- The -1 speaker in the middle: V = +7, G = 14.
- The -1 speaker first: V = +11, G = 17 (high catalyst regime).

No mind changed, yet the world swings by 16 points. The stances {+1, 0, -1} behave differently: all six orderings are deadlocks (V in -8, -6, -2, +2, +6, +8), so reordering cannot escape. The player must first shift one stance, for example Lily from 0 to +1, and then choose the order.

### 2. Anchor clamp

A last mover at 0 removes the 9-weight term. When all three align in hostility (-1, -1, -1), V = -13, the lethal tier. Getting the last mover to a neutral statement gives V = 0 + 3(-1) + (-1) = -4, which clamps the world to V in \[-4, +4\], or G in {7, ..., 12}.

### 3. Antipodal mirror

A room stuck at G = 2 (V = -11, trits `--+`) whose exit needs G = 17 does not have to be solved from scratch. Because 2 + 17 = 19, inverting every stance to `++-` gives V = +11, which is G = 17 in a single move.

### 4. Syndrome puzzles

A locked mechanism at G = 12 (V\_exp = +4, trits `0++`) displays S\_err.

- **Scenario A, exact repair.** Noise drops the entities to V\_act = -3 (`0-0`), so Delta V = -7 and S\_err = 13. To reach S\_err = 0 the player needs Delta V = 0. The 2nd mover goes from -1 to +1 (+2 steps, +6) and the 1st mover from 0 to +1 (+1), injecting +7 and restoring V = +4.
- **Scenario B, alias exploit.** An overload conduit wants S\_err = 13, and a dialogue constraint locks the 2nd mover at T1 = 0. That blocks the obvious state V = -3 (it needs T1 = -1). But S\_err = 13 also accepts Delta V = +13, which is V\_act = bal\_27(4 + 13) = -10, trits `-0-`. Its T1 is 0, so it obeys the lock, and the conduit opens.

Section 7 has the full alias table for this lock.

### 5. Unison walk and pivot mirror

On the Z\_27 rotor, 120 degrees is exactly 9 teeth, one last-mover step. Holding the first two movers and cycling the last through -1, 0, +1 visits three states 120 degrees apart. That fires the R = 0 singularity on the third turn if the walk never touches Z\_7. As section 2 shows, this holds only for (T1, T0) = (+1, +1) or (-1, -1).

| Walk | T2 | V | T | LUT index | G |
| --- | --- | --- | --- | --- | --- |
| Positive, (T1, T0) = (+1, +1) | -1 | -5 | 22 | 440 | 6 |
|  | 0 | +4 | 4 | 80 | 12 |
|  | +1 | +13 | 13 | 260 | 19 |
| Negative, (T1, T0) = (-1, -1) | -1 | -13 | 14 | 280 | 0 |
|  | 0 | -4 | 23 | 460 | 7 |
|  | +1 | +5 | 5 | 100 | 13 |

Any turn order works, and every pair differs by 9 or 18 teeth (180 or 360 table ticks). Trying it with (T1, T0) = (+1, 0) fails: the last mover at -1 gives V = -6, a deadlock, on the first turn.

**Pivot mirror aid.** In a chamber with a mirror resonator, the player commits the T2 = 0 pivot (V = +4 or -4) and one extreme. The resonator reflects the extreme across the pivot and commits the missing third state. From pivot V = +4 (T = 4) and extreme V = +13 (T = 13), the reflection is 2 \* 4 - 13 = -5 (T = 22), completing the triad in two turns plus one pulse.

### 6. Tension steering

Tension H sets orbit eccentricity (section 6), so shifting dissent reshapes the world's motion. The state V = -11 (`--+`) is a 2-versus-1 split with H = 4. Moving the dissenter from +1 to 0 gives V = -12 (`--0`) with H = 1, a far gentler orbit. Bringing all three to the same stance gives H = 0, a circle. In a deadlock the same lever works laterally: reordering walks the six-point tension ring without changing G.

## 10. The per-turn pipeline

One turn is one pass through nine steps, in this order. The order matters: the history window must take the new state before the singularity check, and deadlock must be decided before any syndrome is computed.

1. **Commit.** The three entities speak in order and commit trits (T0, T1, T2). Compute V = 9 T2 + 3 T1 + T0 and T = V mod 27. Increment the step counter x.
2. **Deadlock gate.** If V is in Z\_7, set F\_deadlock to 1, latch G, freeze the history window and set S\_err to NULL. Otherwise clear F\_deadlock.
3. **World and syndrome.** For a decisive V in a free-sync room, set G = phi(V). In a syndrome-locked room, compute Delta V and S\_err against G\_lock, and release the lock only when Delta V = 0.
4. **Hex projection.** Compute consensus s, tension coordinate (u, v) and H (always defined, even in a deadlock).
5. **History window.** Push T into the n = 3 window if V is decisive. A mirror pulse may instead synthesize the third state (section 4).
6. **Master ring and phase.** Compute X = (460 T + 81 G) mod 540 and r = (7x) mod 540, then classify the phase regime.
7. **Circular telemetry.** Index the table at 20 T for each window state, sum the cos and sin entries, compute R and sigma, and test the singularity (combinatorial triad, or norm below 64).
8. **Orbit.** Take a = 1 + abs(s), the row for H, and m = (7x + 20 \* burn) mod 540. Read NU and RHO to get the polar position.
9. **Compile and dispatch.** Run the six-rule ladder for each token, then update the shaders, camera shake and audio from phase, R, sigma, V and the orbit.

## 11. Verification and open decisions

Most claims in this draft were checked by exhaustive enumeration while writing it, but the reference suite does not yet cover the new material, and six design choices are still yours to make.

**Checked while writing this draft.**

- The 27 states land on 19 hex points, with tension counts 1, 6, 6, 6 for H = 0, 1, 3, 4. Tension 3 occurs only in deadlocks.
- The unison rule: the walk avoids Z\_7 only for (T1, T0) = (+1, +1) or (-1, -1). The 27 states split into 9 triads, 7 touching Z\_7, 2 fully decisive.
- The pivot mirror completes a triad for every pivot.
- Syndrome scope: S\_err = 0 only for Delta V = 0; the 1-to-1 and 2-to-1 ranges; the alias table for G = 12; 30 of 78 single-step changes land in Z\_7.
- The orbit tables: rounding margin, symmetry, radius range, checksum.
- Table bounds: exact triads round to a squared norm of at most 1, the nearest non-singular window is 36,101 on M = 540.

**To add to the reference suite.** Draft 5's script dropped the stateful engine, the deadlock latch, the phase regimes and the mirror. Restore those, and add tests for each bullet above, the ladder's totality, the deadlock-ring walk, and the pipeline order of section 10. Keep the two draft-5 fixes: no `{0..19}` inside an f-string, and the R clamp.

**Open decisions.**

| Decision | Default in this draft | Alternatives |
| --- | --- | --- |
| Orbit size from consensus | a = 1 + abs(s) | a = abs(s) with a floor, or a fixed size per room |
| Eccentricity from tension | e = H / 5 | A hand-tuned table per H, or a per-room scale |
| Orbit clock | m = 7x + 20 \* burn | Advance by x alone, or let a burn change speed instead of phase |
| Mirror pulse | Counts as one committed turn | A free action that does not advance x |
| History window at room entry | Three copies of the entry state, so R starts at 1 | Start empty and require three real commits |
| Stagnation warning | Fires after a long run at R = 1; length not set | Pick a number of turns, or tie it to the phase regime |

## Appendix A. Syndrome-guarded registers

The engine's syndrome idea also protects ordinary integer state from bit flips and out-of-bounds values: each register stores redundancy beside its value, a syndrome identifies the damage, and anything unexplained latches instead of guessing. In the self-test it repairs every single-bit flip, traps every double flip, and never writes a guess into trusted history.

**How it maps onto the engine**

| Engine concept | Guard equivalent |
| --- | --- |
| Expected state G and S\_err = Delta V mod 20 | Stored check and syndrome = (value - check) mod 19 |
| Weights +-1, +-3, +-9 are distinct mod 20 | Flips of +-2^k are distinct mod 19, because 2 is a primitive root mod 19 |
| Inject the opposite of Delta V to cancel it | Inject the negative of the decoded delta in place |
| Z\_7 latch with F\_deadlock | LATCHED: restore the last good value and count a fault |
| Boundary-safe Delta V before projection | Range test on the result, never a clamp |
| Purple handler | The caller treats LATCHED like Purple |
| Dual-register lock | Two copies of the check |

**Record layout.** Each row holds (value, check A, check B, parity) in 8 + 5 + 5 + 1 = 19 bits. Both checks equal value mod 19, and the parity cell is even parity over the other 18 bits, when the row is healthy. The stated fault model is at most two flipped cells per row per cycle.

**One verification cycle**

1. Recompute the parity over the value and both checks. A mismatch means an odd number of cells flipped.
2. Parity matches (zero or two flips). If the checks disagree, a check is not a valid residue, or the syndrome (value - check) mod 19 is nonzero, two cells flipped: report DED and restore the last good value. Otherwise the row is CLEAN, or LATCHED if the value is out of range.
3. Parity mismatches (one flip). Checks that disagree with one copy matching the value and the other one bit away: rebuild and report CHECK\_REPAIRED. Agreeing checks with syndrome zero: only the parity cell is damaged, rebuild it and report PARITY\_REPAIRED. Otherwise look the syndrome up in the decoder.
4. Accept a decoder repair only if undoing the claimed flip changes exactly one bit, the result is in range, and the result mod 19 equals the check. Anything else is ODD\_UNCORRECTABLE, or LATCHED when the result leaves the range.

**Rules**

- Redundancy is required. A range rule alone detects only what leaves the range, and repairing from it is a guess.
- Out-of-range is a latch, not a clamp. A clamp turns a fault into a plausible wrong number and, if committed, poisons the fallback.
- Only verified values reach last\_good.
- The guard returns a status instead of raising, so the loop keeps running and the caller decides the color.
- A repair must be explainable as one flipped bit. An integer delta that carries across several bits is rejected, because it means the syndrome was produced by something other than a single flip.
- Count by kind. DED and ODD say the memory itself was disturbed (Purple-class). LATCHED says a value was out of range or undecodable. They are separate counters and separate statuses.

**Class**

```python
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

    def write(self, row, value):
        if not self._in_range(value):
            raise ValueError(f"write of {value} outside [{self.MIN_LIMIT}, {self.MAX_LIMIT}]")
        self._store(row, value)

    def peek(self, row):
        return self.rows[row][0]

    def cycle(self, row):
        value, ca, cb, stored_parity = self.rows[row]
        parity_bad = self._parity(value, ca, cb) != stored_parity   # odd number of flips
        checks_differ = ca != cb
        checks_invalid = ca >= self.MOD or cb >= self.MOD      # a 5-bit field can hold 19..31
        syndrome = (value - ca) % self.MOD

        if not parity_bad:
            # even flips: any anomaly with matching parity is a multi-flip, trapped
            # before the decoder can mistake it for a single one
            if checks_differ or checks_invalid or syndrome != 0:
                return self._trap(row, Status.DED)
            if not self._in_range(value):
                return self._trap(row, Status.LATCHED)
            self.last_good[row] = value
            return self._note(row, Status.CLEAN)

        # odd flips: accept only if exactly one single-flip explanation fits
        if checks_differ:
            expected = value % self.MOD
            good, bad = (ca, cb) if ca == expected else (cb, ca)
            if good == expected and self._one_bit(bad ^ expected) and self._in_range(value):
                self._store(row, value)
                return self._note(row, Status.CHECK_REPAIRED)
            return self._trap(row, Status.ODD_UNCORRECTABLE)

        if checks_invalid:
            return self._trap(row, Status.ODD_UNCORRECTABLE)

        if syndrome == 0:
            # data and checks agree; only the parity cell is wrong
            if not self._in_range(value):
                return self._trap(row, Status.LATCHED)
            self._store(row, value)
            return self._note(row, Status.PARITY_REPAIRED)

        delta = self.DECODER.get(syndrome)
        if delta is None:
            return self._trap(row, Status.ODD_UNCORRECTABLE)
        repaired = value + delta
        if not self._one_bit(repaired ^ value) or repaired % self.MOD != ca:
            return self._trap(row, Status.ODD_UNCORRECTABLE)
        if not self._in_range(repaired):
            return self._trap(row, Status.LATCHED)
        self._store(row, repaired)
        return self._note(row, Status.REPAIRED)

    def faults(self, row):
        c = self.counts.get(row, Counter())
        return {"latched": c["LATCHED"], "ded": c["DED"], "odd": c["ODD_UNCORRECTABLE"]}
```

**Verified by the self-test**

- All 128 legal values stay CLEAN, so there are no false repairs.
- All 2,432 single flips over all 19 cells are repaired exactly and the record is rebuilt: 1,024 in the data, 1,280 in the two checks, 128 in the parity cell.
- A damaged parity cell is rebuilt, and a later single flip is still repaired instead of being reported as a double error.
- All 21,888 double flips (every pair of cells, every value) are trapped as DED with the value intact.
- Out-of-range and unexplained states restore the last good value and are counted under their own kind.
- A single copy of the check is not enough. With one copy, 620 of 640 check-bit flips caused a wrong repair of good data. That is why the check is stored twice.
- Against an ideal nearest-codeword decoder, the guard gives the same answer on all 148,352 patterns of one, two and three flips.

**Limits.** The guarantee is one flip corrected and two flips trapped per row per cycle. Three flips are not guaranteed: of 124,032 triple-flip cases, 95.6% were trapped and 4.4% were silently wrong, which is the floor for a code of minimum distance 4. More than that needs a longer code or a second source (A.2).

**Where it could guard the engine.** The world register G, the three history window entries and the step counter are small integers that every turn depends on. Whether to wrap them is a design decision (section 11): the cost is 10 extra bits per register and one cycle call per turn.

### A.2 Zero checks and a second source

A legal word can be defined as the kernel of a check map, so verifying means testing that the syndrome is zero on the stored word, with no expected value recomputed. The mod-19 residue is one such map; a parity-check matrix over bits or trits is a cheaper one. A second representation in a different base widens the envelope: when two sources encode the same value, the distances between legal words add, 4 + 3 = 7 for the binary and ternary designs below.

**Where the null-sum states sit.** The 27 trytes split into three cosets by the sum T2 + T1 + T0 mod 3, and the zero coset K9 holds 9 states: the seven Z7 null-sum states plus the two unison states. K9 is a subgroup under digitwise addition, one trit per entity. It is not closed under Z27 addition with carries, and Z7 alone is not closed under either. So zero checks belong to the per-entity trit group, not to the carrying ring. The turn-order weights 1, 3, 9 are all 0 mod 3 except the first, so a value-weighted sum mod 3 would see only T0; the check must be digitwise.

**Tryte check cost.** One check trit c = -(T2 + T1 + T0) mod 3 makes the four-trit sum zero (4 trits, minimum distance 2): it detects one wrong entity but cannot say which. Three check trits give 6 trits per tryte at distance 3 and correct one wrong entity. Four give 7 trits at distance 4 (SEC-DED).

| Scheme (7-bit register, 128 legal values) | Cells | Min distance | Silent wrong, 2 faults | Silent wrong, 3 faults |
| --- | --- | --- | --- | --- |
| Binary, mod 19 twice, parity (A.1) | 19 | 4 | 0% | 4.4% |
| Ternary, mod 22 twice, sum-parity trit | 12 | 3 | 4.3% | 1.6% |
| Same plus weighted second parity trit | 13 | 3 | 0.15% | 0.95% |
| Binary zero-check SEC-DED (5 check bits) | 12 | 4 | 0% | 70.9% |
| Ternary zero-check SEC-DED (4 check trits) | 9 | 4 | 0% | 14.0% |
| Binary SEC + ternary SEC, decoded jointly | 19 | 6 | 0% (both fixed) | 0% (all trapped) |
| SEC-DED + SEC-DED, decoded jointly | 21 | 8 | 0% (both fixed) | 0% (all fixed) |
| Raw binary + raw ternary, no checks | 12 | 2 | 0.76% | 0.63% |

**Reading the table.**

- At the same cell count, two bases beat the residue guard: the 19-cell joint code corrects two faults and traps three, where the 19-cell residue code corrects one and misses 4.4% of triples. A cell is not a bit, though. On binary hardware the joint code costs 27 bits, and a plain binary code of 27 bits reaches distance 10 or more (found by search) against 6 here. A.3 has the full accounting.
- Compact single codes are fragile outside their model: the 12-cell binary SEC-DED passes 70.9% of triples silently because most syndromes are in use. More check bits in the same base fix that more cheaply per bit than a second copy does.
- The cheapest useful second source is a raw copy in the other base. It needs no checks and detects every single fault, since a bit flip and a trit change never produce the same value.
- Decode jointly. Letting each source repair itself and trusting whichever succeeds is safe up to three faults but leaks 1.6% silent errors at four, when one source miscorrects and the other traps. Requiring agreement never leaks but gives up repair.

**Moduli must match the base.** Mod 19 separates all 16 single bit flips of an 8-bit value; mod 22 is the smallest that separates all 20 single-trit faults, and mod 19 separates only 14 of them. The products 5 x 6 and 7 x 4 separate only 10 of 16 bit flips, and values 30 or 28 apart look identical, so they detect but cannot locate. They would work for a register of about five bits. The engine's own ring (base-20 digit and tryte) has minimum distance 1: every pair is a legal state, so it detects nothing by itself. Limiting legal values to 128 of the 540 states traps 81% to 88% of single faults by range alone, but 12% to 19% still pass silently.

**What no second source fixes.** A wrong value computed by the engine and then stored is encoded faithfully in both representations. That case is covered by the range rule and the syndrome against the expected state (section 7), not by storage redundancy.

### A.3 The two-source guard and what it costs in bits

The joint binary and ternary code is built as a working guard (two\_source\_guard.py). Source A is a binary single-error-correcting code and source B a ternary one, each decodable alone. A repair is accepted only if the observed word is within two damaged cells of exactly one candidate value; anything else restores the last good value. A trit takes two physical bits, so one flipped bit damages at most one cell and the cell guarantees hold for physical bit flips.

| Payload | SEC-DED alone | Two-source, 2 bits per trit | Two-source, packed trits | Plain binary code of the same physical bits (distance found) |
| --- | --- | --- | --- | --- |
| 7 bits | 12 bits | 27 bits (3.9x) | 24 bits | 10 |
| 16 bits | 22 bits | 51 bits (3.2x) | 45 bits | 13 |
| 32 bits | 39 bits | 88 bits (2.8x) | 78 bits | not searched |

**Measured behavior.** At 7 bits, all 3,456 single flips and all 44,928 double flips over the 27 physical bits are corrected, and none of the 374,400 triple flips is silently wrong (25,600 of them damage only two cells and are corrected). At 16 bits, random flips of one or two bits are all corrected, and the leak beyond the guarantee is small: 4 flips pass silently 0.013% of the time, against 0.148% at 7 bits.

**Does width rescue the idea?** Partly. The check bits grow slowly, so the overhead falls from 3.9x to 2.8x and the leak beyond the guarantee shrinks. But the second source is a full second copy of the value, so it costs about twice the payload at any width, and a plain binary code with the same physical bits reaches a far larger distance (13 against 6 at 16 bits). For random bit flips, spending the bits on a longer single-base code is the better buy.

**What a second source does buy.** Independence. If a whole bank or lane fails, the other source still holds a complete, separately decodable copy. The strict guard handles this safely by trapping. A degraded mode that trusts the one source with a zero syndrome recovers the value when the survivor is undamaged (96.8% to 100% in the test), but it is wrong about 3% of the time when the wiped binary source happens to look clean (about 1 in 2^5), and it cannot recover if the survivor has even one fault. Use it only where a source can fail whole, and treat DEGRADED as a flag to scrub.

**The 16-bit residue guard.** Modulus 53 works: 2 is a primitive root mod 53 (order 52), and all 32 single-bit syndromes are distinct. With the parity cell the row is 16 + 6 + 6 + 1 = 29 bits. Single flips are all repaired and double flips all trapped. Triples leak 6.75% (against 4.4% at 8 bits), because 32 of the 52 nonzero syndromes are in use. Without the parity cell, double flips pass silently 19.3% of the time.


# Tau-Phase Tryte

A design for a small game engine built around three conversational characters (Lilah, Lily and Luci). Each one holds one **trit** (-1, 0 or +1) of a balanced-ternary **tryte**, and the world is a base-20 register. The state advances on a master ring of 540 positions, and "errors" (syndromes) are part of how the world works and how the player pushes on it.

This repository holds the written design, a Python reference suite that checks its claims, and a set of experiments on error-correcting the engine's registers.

## What is in here

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
#   d i s c i p l i n e d - t r i t - c l o c k  
 