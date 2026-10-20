# Core Engine Architecture & State Machine Specification

This document defines the complete, flavor-neutral mathematical architecture of the engine: its discrete state registers (**The Skeleton**), its phase and circular-statistics telemetry (**The Nervous System**), its priority-ordered token compiler (**The Chromatic Interface**), and its interactive state-manipulation levers (**Core Gameplay Mechanics**).

---

## 1. The Skeleton: Discrete Coprime State Registers

The foundational state machine is built on pure integer and modular arithmetic with zero floating-point dependencies. It consists of two coprime inner registers enclosed within a master Chinese Remainder Theorem (CRT) ring.

### A. The Ternary Consensus Rotor ($\bmod 27$) & The 3-Fold Triangular Projection
Three autonomous conversational entities—**Lilah, Lily, and Luci**—act as a dynamic 3-trit balanced ternary register (**1 tryte**). 
*   **Individual Stances (Trits):** In any given turn cycle, each entity commits to a discrete value $t \in \{-1, 0, +1\}$.
*   **Turn-Order Positional Weighting ($3^0, 3^1, 3^2$):** The entities do not hold fixed weights; their weights are determined strictly by the **speaking order** in the current cycle:
    *   **1st Mover ($T_0$):** Weight $3^0 = 1$ (micro-adjustment).
    *   **2nd Mover ($T_1$):** Weight $3^1 = 3$ (regional offset).
    *   **3rd / Last Mover ($T_2$):** Weight $3^2 = 9$ (regime commitment).
*   **Signed Consensus Value ($V \in [-13, +13]$):**
    $$V = 9 T_2 + 3 T_1 + 1 T_0$$
    This yields $27$ total states: the zero origin ($V = 0$) and **13 non-zero absolute magnitudes** ($|V| \in \{1, \dots, 13\}$), each existing in positive ($+$) or negative ($-$) polarity.

*   **The 3-Fold Triangle Projection & Hexagonal Lattice ($19$ Distinct Points):**
    Projecting the three trits $(T_2, T_1, T_0)$ onto the vertices of an equilateral triangle at $0^\circ$, $120^\circ$, and $240^\circ$ maps the $27$ tryte states onto **$19$ distinct points on a hexagonal lattice**. Each state splits into two orthogonal channels:
    1.  **Consensus ($s$):** The unweighted trit sum $s = T_2 + T_1 + T_0 \in [-3, +3]$. This directly defines the $7$ null-sum deadlocks ($s = 0$) versus the $20$ decisive states ($s \neq 0$).
    2.  **Tension ($H$):** The hexagonal displacement vector measuring internal disagreement, independent of turn order. The squared distance from center is given by the pure integer formula:
        $$\text{Dist}^2 = \frac{1}{2}\sum_{i < j} (t_i - t_j)^2 \in \{0, 1, 3, 4\}$$

*   **The $7 + 20$ Partition (Defined by Explicit Exclusion):**
    The $27$ total states of $\mathbb{Z}_{27}$ partition into two disjoint subsets $\mathcal{Z}_7$ and $\mathcal{D}_{20}$:
    1.  **The $7$ Null-Sum / Deadlock States ($\mathcal{Z}_7$):** Defined explicitly as the set of states whose unweighted trit sum equals zero ($s = 0$). This comprises the origin $(0,0,0)$ ($V = 0$) and the $6$ permutations of $\{-1, 0, +1\}$ where all three trits are mutually distinct:
        $$\mathcal{Z}_7 = \{ -8, -6, -2, 0, +2, +6, +8 \}$$
    2.  **The $20$ Decisive States ($\mathcal{D}_{20}$):** Defined by strict exclusion as $\mathcal{D}_{20} = [-13, +13] \setminus \mathcal{Z}_7$. Equivalently, $\mathcal{D}_{20}$ consists of all states whose unweighted trit sum is non-zero ($s \neq 0$):
        $$\mathcal{D}_{20} = \{ \pm 1, \pm 3, \pm 4, \pm 5, \pm 7, \pm 9, \pm 10, \pm 11, \pm 12, \pm 13 \}$$

---

### B. The Vigesimal Spatial/State Register ($\bmod 20$), Bijection $\phi$, and $\mathcal{Z}_7$ Spatial Latch
The environment and player-accessible state registers operate on a Base-20 (vigesimal) counter $G \in \{0, 1, \dots, 19\}$.
*   **Bitwise / Sub-Base Decomposition ($20 = 4 \times 5$):**
    Every state $G$ decomposes via integer division and modulo into two sub-registers:
    *   **Major Index ("Bars"):** $B = \lfloor G / 5 \rfloor \in \{0, 1, 2, 3\}$.
    *   **Minor Index ("Dots"):** $D = G \bmod 5 \in \{0, 1, 2, 3, 4\}$.
*   **Explicit Order-Preserving Bijection ($\phi: \mathcal{D}_{20} \leftrightarrow \mathbb{Z}_{20}$):**
    Sorting the $20$ decisive states of $\mathcal{D}_{20}$ in strictly ascending order defines a canonical, invertibly exact bijection $\phi(V) = G \in \{0, \dots, 19\}$:

| $G = \phi(V)$ | $0$ | $1$ | $2$ | $3$ | $4$ | $5$ | $6$ | $7$ | $8$ | $9$ | $10$ | $11$ | $12$ | $13$ | $14$ | $15$ | $16$ | $17$ | $18$ | $19$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Decisive $V \in \mathcal{D}_{20}$** | $-13$ | $-12$ | $-11$ | $-10$ | $-9$ | $-7$ | $-5$ | $-4$ | $-3$ | $-1$ | $+1$ | $+3$ | $+4$ | $+5$ | $+7$ | $+9$ | $+10$ | $+11$ | $+12$ | $+13$ |

*   **Antipodal Complement Symmetry:** Because $\mathcal{D}_{20}$ is symmetric around $0$, $\phi$ satisfies the exact complement identity for all $V \in \mathcal{D}_{20}$:
    $$\phi(-V) = 19 - \phi(V)$$
*   **World Register Behavior During a $\mathcal{Z}_7$ Deadlock (Consensus $s = 0$ Line):**
    Because $\phi(V)$ is undefined for $V \in \mathcal{Z}_7$, deadlock states ($s = 0$) occupy the **Consensus Zero Line**, where the spatial world register latches its primary integer $G_{t-1}$ while opening a secondary movement channel along the **Hexagonal Tension coordinate ($H$)**, allowing lateral state shifts without polluting the primary position.

---

### C. The Master Ring & CRT Bus ($\bmod 540$)
Because $\gcd(27, 20) = 1$, the Chinese Remainder Theorem guarantees an isomorphism $\mathbb{Z}_{27} \times \mathbb{Z}_{20} \cong \mathbb{Z}_{540}$.
*   **Exact State Reconstruction ($\bmod 540$):**
    Given any ternary state $T = V \bmod 27 \in \{0, \dots, 26\}$ and any vigesimal state $G \in \{0, \dots, 19\}$, the combined system state is a single integer $X \in \{0, \dots, 539\}$:
    $$X = (460 \cdot T + 81 \cdot G) \bmod 540$$
*   **The T-Rescaled Mirror Ring ($T \to 2P - T$):**
    Lifting the ternary rotor onto a $27$-point cycle allows any pivot state $P$ to define an exact modular involution:
    $$\mathcal{M}_{27}(T;\, P) = (2 P - T) \bmod 27$$

---

## 2. The Nervous System: $\tau$-Phase Interference, Elliptic Orbits & Error Syndromes

To project discrete ring counters into continuous wave mechanics, the engine maps every modulus $M \in \{20, 27, 540\}$ onto the unit circle using $\tau = 2\pi$:
$$\theta_M(x) = \left(\frac{x}{M} \bmod 1\right)\tau$$

### A. Phase-Delta Interference ($\Delta\theta$) & Elliptic Orbit Eccentricity
When the system advances along a sequence of steps $x$, the relative phase angle between the Vigesimal Grid ($M=20$) and the Ternary Rotor ($M=27$) is:
$$\Delta\theta(x) = \left(\theta_{20}(x) - \theta_{27}(x)\right) \bmod \tau = \left(\frac{7x}{540} \bmod 1\right)\tau$$
*   **Single-Step Phase Shift:** Each unit increment $\Delta x = 1$ shifts the relative phase by $\frac{7}{540}\tau = 4^\circ 40'$.
*   **Elliptic Orbit Mapping:** The phase difference $\Delta\theta$ and the hexagonal tension $H$ drive an **elliptic orbit generator** (computed via a deterministic integer lookup table for Kepler's equation):
    *   **Consensus ($s$)** sets the semi-major axis (mean orbit radius).
    *   **Tension ($H$)** sets the orbit eccentricity ($e \in [0, 1)$), transforming a circular orbit into an ellipse when entities disagree.
    *   **Syndrome Delta-V ($\Delta V$)** acts as a maneuver burn vector modifying orbital velocity.

---

### B. Mardia Circular Standard Deviation ($\sigma_{\text{rotations}}$) & Deterministic LUTs
Over a rolling history window of **$n = 3$ committed decisive states** $\{x_1, x_2, x_3\}$, the engine measures state dispersion using Mardia's circular standard deviation:
$$C = \frac{1}{n}\sum_{i=1}^{n} \cos\left(\frac{\tau \cdot x_i}{M}\right), \quad S = \frac{1}{n}\sum_{i=1}^{n} \sin\left(\frac{\tau \cdot x_i}{M}\right)$$
$$R = \min\left(1.0, \sqrt{C^2 + S^2}\right), \quad \sigma_{\text{rotations}} = \frac{\sqrt{-2\ln(R)}}{\tau}$$
*   **Deterministic Fixed-Point LUT Stride & Clamping:** Indices are precomputed via signed 16-bit integer tables (`COS_LUT`, `SIN_LUT` scaled by $2^{14}$). $R$ is strictly clamped to $[0.000001, 1.0]$ before evaluating $\ln(R)$ to prevent domain errors.
*   **Order-Independent Combinatorial Singularity:**
    $$\forall i \neq j \in \{1,2,3\},\quad (x_i - x_j) \bmod M \in \left\{\frac{M}{3},\; \frac{2M}{3}\right\} \quad \text{OR} \quad C_{\text{sum}}^2 + S_{\text{sum}}^2 < \epsilon_{\text{int}} \quad (\epsilon_{\text{int}} = 64)$$
    When satisfied, the engine triggers a deterministic **Symmetry-Break Singularity**.

---

### C. Boundary-Safe Modulo-20 Error Syndrome ($S_{\text{err}}$)
To prevent the $26 \to 0$ wraparound in $\mathbb{Z}_{27}$ from corrupting the Modulo-20 syndrome, the engine computes the **signed balanced perturbation $\Delta V \in [-13, +13]$** inside $\mathbb{Z}_{27}$ first:
$$\Delta V = \text{bal}_{27}\left((T_{\text{act}} - T_{\text{exp}}) \bmod 27\right) \in [-13, +13]$$
$$S_{\text{err}} = \Delta V \bmod 20 \in \{0, 1, \dots, 19\}$$

---

## 3. The Chromatic Interface: Strict Priority Compiler

When an entity emits a token with local trit $t_i \in \{-1, 0, +1\}$, the compiler assigns its color using the first matching rule:

| Priority | Syntax Color | Exclusive Trigger Condition (Evaluated Top-to-Bottom) | Functional Meaning in the Engine |
| :--- | :--- | :--- | :--- |
| **1 (Highest)** | **Purple** | $V \in \mathcal{Z}_7$ ($s = 0$) **OR** Combinatorial $120^\circ$ Triad **OR** $C_{\text{sum}}^2 + S_{\text{sum}}^2 < \epsilon_{\text{int}}$ | **Singularity / Exception:** Null-sum deadlock or circular cancellation; latches $G$ and opens tension channel. |
| **2** | **Yellow** | $S_{\text{err}} \notin \{0, 1, 19\}$ | **Syndrome Alert / Desync:** Non-zero syndrome covering multi-trit desynchronizations. |
| **3** | **Green** | $S_{\text{err}} \in \{1, 19\}$ | **Phase-Locked / Reparative:** Auto-corrects $\pm 1$ micro-drift. |
| **4** | **Blue** | $S_{\text{err}} == 0$ and $t_i == 0$ | **Immutable / Anchor:** Entity commits weight $0$, clamping target parameter. |
| **5** | **Orange** | $S_{\text{err}} == 0$ and $t_i == +1$ | **Catalyst / Kinetic:** Entity applies positive weight under shear. |
| **6 (Lowest)** | **Red** | $S_{\text{err}} == 0$ and $t_i == -1$ | **Restrictor / Dampener:** Entity applies negative weight. |

---

## 4. Player-Facing Mathematical Levers (Core Gameplay Mechanics)

1.  **Turn-Order Interception:** Permuting speaking order among Lilah, Lily, and Luci alters the $9T_2 + 3T_1 + T_0$ commitment.
2.  **The Unison-Locked Triad Walk ($R \to 0$):** To sweep the Last Mover through $\{-1, 0, +1\}$ without hitting $\mathcal{Z}_7$, the first two movers must be locked in unison: **$(T_1, T_0) = (+1, +1)$** ($V \in \{-5, +4, +13\}$) or **$(-1, -1)$** ($V \in \{-13, -4, +5\}$).
3.  **Non-Zero Dial Aliasing Exploits ($S_{\text{target}} \in [7, 13]$):** Leveraging the $2$-to-$1$ pigeonhole overlap where $S_{\text{target}} = 13$ accepts both $\Delta V = -7$ ($V_{\text{act}} = -3$) and $\Delta V = +13$ ($V_{\text{alias}} = -10$).