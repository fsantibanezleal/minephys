# Comminution

> Bond's third law, the Morrell energy-size relation and its circuit terms, the population balance mill, flotation
> kinetics, the two-product formula, the crusher matrix model and the mine-to-mill chain of `minephys.comminution`.
> · Part of: [methods](README.md) · Related: [theory](../theory/README.md#comminution--minephyscomminution) ·
> [reference](../reference/README.md) · [data contract](../data-contract/README.md)

![minephys.comminution modules and the mine-to-mill chain](../assets/diagrams/minephys-comminution.svg)

*The chain composes already-published pieces (top row) and adds no new physics; the population balance mill, the
flotation models and the two-product formula (bottom row) stand alone. Every closed-form constant is a row of
`knowledge/comminution.yaml`.*

## What and why

The module turns a blast size distribution into mill energy, mill throughput and flotation recovery. Each equation is
a transcription of its source, every constant is a cited knowledge row read at call time, and each published worked
example that could be read is a test. Results are educational and reference-grade, valid only inside the range of each
model; they are not design values.

Conventions at the API: sizes in m, specific energy and work indices in J/kg, power in W, throughput in kg/s, rates in
1/s, laboratory grindability in kg per mill revolution. The sources publish sizes in micrometres, grindability in g per
revolution and energies in kWh/t; each function converts once at its boundary (1 µm = 10^-6 m, 1 g = 10^-3 kg, 1 kWh/t =
3,600 J/kg, from the knowledge row `kilowatt_hour`).
<!-- impl: src/minephys/comminution/_common.py:24-26 (unit factors), :42 (kwh_per_t_in_si); tests/unit/test_t_005_010_bond.py:26 (KWH_PER_T = 3600) -->

## Energy-size laws

### Bond's third law

$$W = 10\,W_i\left(\frac{1}{\sqrt{P_{80}}} - \frac{1}{\sqrt{F_{80}}}\right)$$

<!-- impl: src/minephys/comminution/_energy.py:46-48 (bracket), :102 (bond_energy) -->

| Symbol | Meaning | Unit in the equation | Unit at the API |
|---|---|---|---|
| $W$ | specific comminution energy | units of $W_i$ | J/kg |
| $W_i$ | Bond work index | kWh/t (the law is homogeneous in $W_i$) | J/kg |
| $F_{80}$, $P_{80}$ | 80 % passing sizes of feed and product | µm | m |
| 10 | row `bond_law_coefficient` | 1 (sizes in µm) | not applicable |

The operating work index inverts the law for a measured energy:

$$W_{io} = \frac{W}{10/\sqrt{P_{80}} - 10/\sqrt{F_{80}}}$$

<!-- impl: src/minephys/comminution/_energy.py:144 (bond_operating_work_index) -->

The ball-mill test work index reads the laboratory result:

$$W_i = \frac{1.1025 \times 44.5}{P_1^{0.23}\,G_{bp}^{0.82}\,\left(10/\sqrt{P_{80}} - 10/\sqrt{F_{80}}\right)}\ \text{kWh/t}$$

<!-- impl: src/minephys/comminution/_energy.py:193-202 (bond_ball_mill_work_index) -->

with $P_1$ the closing screen size (µm), $G_{bp}$ the net grams of product finer than the screen per mill revolution,
$F_{80}$ and $P_{80}$ the test feed and product sizes (µm). The constants 44.5, 0.23, 0.82 and 1.1025 are the rows
`bond_bm_constant`, `bond_bm_exponent_screen`, `bond_bm_exponent_grindability` and `bond_short_ton_to_metric`.

**Source and validity.** The three forms are read on the Bond-efficiency guideline `mcivor2016bondgmsg` (p. 1
"Calculations", worked examples p. 2, ball-mill test Annex C1 p. 10 and the test sheet p. 11), which reproduces Bond's
equations; Bond's originals `bond1952third` and `bond1961crushing` are bibliographic only (not read). The law applies
down to a product size of about 70 µm (row `bond_min_product_size`); a finer `p80` emits `ValidityWarning` and the
result is still returned. The published short-ton factor 1.1025 differs from the exact 1.10231 by 0.01 %, below the
resolution of the test.

### Morrell energy-size relation

$$W = M_i \cdot 4\left(x_2^{f(x_2)} - x_1^{f(x_1)}\right),\qquad f(x) = -\left(0.295 + \frac{x}{10^6}\right)$$

<!-- impl: src/minephys/comminution/_energy.py:205-212 (_size_term, _delta), :250 (morrell_energy) -->

$M_i$ is the SMC hardness index (J/kg at the API), $x_1$ the feed and $x_2$ the product 80 % passing sizes (µm inside,
m at the API); the constants 4, 0.295 and $10^6$ are the rows `morrell_coefficient`, `morrell_f_constant` and
`morrell_f_scale`. The circuit terms of the Morrell method share the bracket $\Delta(x_1, x_2) = 4(x_2^{f(x_2)} -
x_1^{f(x_1)})$:

| Term | Function | Equation | Impl |
|---|---|---|---|
| Coarse tumbling $W_a$ | `morrell_tumbling_coarse` | $K_1 M_{ia}\,\Delta(x_1, 750)$, $K_1 = 0.95$ with a pebble crusher, 1 otherwise; needs $x_1 > 750$ µm | `_energy.py:293` |
| Fine tumbling $W_b$ | `morrell_tumbling_fine` | $M_{ib}\,\Delta(750, P_{80})$; needs $P_{80} < 750$ µm | `_energy.py:334` |
| Crusher $W_c$ | `morrell_crusher` | $S_c K_2 M_{ic}\,\Delta(x_1, x_2)$, $K_2 = 1$ closed or 1.19 open; $S_c = \min(55(x_1x_2)^{-0.2}, 1)$ for stage `"primary"` or `"secondary"`, $S_c = 1$ for `"tertiary"` or `"pebble"` | `_energy.py:337-339, 389` |
| HPGR $W_h$ | `morrell_hpgr` | $S_h K_3 M_{ih}\,\Delta(x_1, x_2)$, $K_3 = 1$ closed or 1.19 open; $S_h = \min(35(x_1x_2)^{-0.2}, 1)$ | `_energy.py:433` |
| Size-distribution correction $W_s$ | `morrell_size_distribution_correction` | $0.19\,M_{ia}\,\Delta(x_1, x_2)$ | `_energy.py:471` |
| Index from the Bond test $M_{ib}$ | `morrell_mib` | $18.18 / (P_{100}^{0.295}\,G_{bp}\,(P_{80}^{f(P_{80})} - F_{80}^{f(F_{80})}))$ kWh/t | `_energy.py:520` |

The rows behind the factors are `morrell_k1_pebble_crusher`, `morrell_k2_open_circuit`, `morrell_k3_open_circuit`,
`morrell_ks_crusher`, `morrell_ks_hpgr`, `morrell_s_exponent`, `morrell_ws_factor`, `morrell_coarse_fine_boundary`
(750 µm), `morrell_mib_constant` and `morrell_mib_screen_exponent`.

**Source and validity.** All are read on the Morrell-method guideline `gmsg2016morrell` (eq. 2 p. 2; eqs. B2 to B6
pp. 6 to 7; section B.2.4 p. 8); `morrell2004alternative`, `morrell2008method` and `morrell2009predicting` are the
primary papers (paywalled, not read). The guideline states a relative error of one standard deviation of 6.5 % (row
`morrell_relative_error_sd`, p. 3) and applies the fine term down to about 45 µm (row `morrell_fine_grind_limit`); a
finer grind emits `ValidityWarning`. The size factor $S_c$ is applied only to primary and secondary stages because the
guideline gives tertiary and pebble crushers unity, and its pebble example, where $S_c$ would be 0.956, does not apply
it. The pebble-crusher recycle fraction is applied by the caller, as in the guideline.

### Worked examples (tests)

Test files are under `tests/unit/`; `KWH` converts kWh/t to J/kg.

| Case | Result | Oracle | Test |
|---|---|---|---|
| Bond, $W_i$ = 15 kWh/t, $F_{80}$ = 2,000 µm, $P_{80}$ = 150 µm | 8.893347 kWh/t = 32,016.05 J/kg | hand calculation | `test_t_005_010_bond.py:40` |
| Rod-ball circuit, 9.5 kWh/t from 19,300 to 1,000 µm and 9.8 kWh/t from 1,000 to 155 µm | 2.32 and 4.77, total 7.09 kWh/t | guideline p. 2 | `test_t_005_010_bond.py:58` |
| Operating work index, 7.0 kWh/t from 2,500 to 212 µm | 14.4 kWh/t | guideline pp. 1 to 2 | `test_t_005_010_bond.py:117` |
| Ball-mill test, $P_1$ = 106 µm, $G_{bp}$ = 1.825 g/rev, $F_{80}$ = 2,746.1 µm, $P_{80}$ = 79.7 µm | 11.028663 kWh/t (10.0 kWh/short ton published as 11.0 kWh/t) | guideline p. 11 | `test_t_005_010_bond.py:129, 141` |
| Morrell, $M_i$ = 20 kWh/t, 2,000 to 150 µm | 9.862056 kWh/t | hand calculation | `test_t_005_012_morrell.py:55-66` |
| $W_a$ at 100 mm with pebble crusher, $M_{ia}$ = 19.4 kWh/t | 9.625169 kWh/t (published 9.6) | Annex C | `test_t_005_012_morrell.py:80-97` |
| $W_b$ at $P_{80}$ = 106 µm, $M_{ib}$ = 18.8 kWh/t | 8.375604 kWh/t (published 8.4) | Annex C | `test_t_005_012_morrell.py:108-116` |
| Pebble crusher 52.5 to 12 mm, open circuit, $M_{ic}$ = 7.2 kWh/t | 1.132374 kWh/t (published 1.13) | Annex C | `test_t_005_012_morrell.py:119-147` |
| $W_s$ (6.5 mm against 100 mm) | 0.888597 kWh/t (published 0.9) | Annex C | `test_t_005_012_morrell.py:190-199` |
| $M_{ib}$ on the Bond test data | 13.976217 kWh/t | hand calculation | `test_t_005_012_morrell.py:202-211` |

The circuit totals of the guideline (18.3, 15.7 and 16.4 kWh/t) are pinned within 0.1 kWh/t because the guideline adds
rounded stage values (`test_t_005_012_morrell.py:225-230`).

## Population balance grinding

Classes are ordered coarse to fine; the last class is the sink (everything below the grid) and has zero selection.
With selection $S_j$ (1/s) and the breakage matrix $B$ ($b_{ij}$, the fraction of broken class-$j$ material entering
finer class $i$, strictly lower triangular, columns with $S_j > 0$ summing to 1), the rate matrix and the batch solution
are

$$A = -\operatorname{diag}(S) + B\,\operatorname{diag}(S),\qquad \mathbf m(t) = e^{At}\,\mathbf m(0)$$

<!-- impl: src/minephys/comminution/_pbm.py:98 (rate matrix), :145 (batch) -->

and the steady-state product of $N$ equal perfectly mixed tanks in series with total mean residence time $\tau$ is

$$\mathbf m_{out} = \left(I - \frac{\tau}{N}A\right)^{-N}\mathbf m_{in}$$

<!-- impl: src/minephys/comminution/_pbm.py:190-191 (pbm_continuous_mill) -->

The matrix exponential is an own Padé(13) scaling-and-squaring (`_pbm.py:45-61`), so no SciPy is needed and repeated
selection values, where an eigen-decomposition fails, are handled. The Austin forms,

$$S_i = \frac{a\,(x_i/x_0)^{\alpha}}{1 + (x_i/\mu)^{\Lambda}},\qquad b_{ij} = B_j(s_i) - B_j(s_{i+1}),\quad B_j(s) = \phi\left(\frac{s}{s_{j+1}}\right)^{\gamma} + (1-\phi)\left(\frac{s}{s_{j+1}}\right)^{\beta}$$

<!-- impl: src/minephys/comminution/_pbm.py:249 (austin_selection), :295-298 (austin_breakage) -->

with $b_{nj} = B_j(s_n)$ for the finest class, make every column $j < n$ sum to 1 by telescoping.

**Limits and UNVERIFIED rows.** Selection and breakage are first order and time-invariant, and breakage into the same
class is not modelled. The attribution of the Austin forms to `austin1984ballmilling` (bibliographic, not read) is
**UNVERIFIED**, as is the row `austin_reference_size` (1 mm); reading it warns. Their tests are hand calculations of the
written forms and the structural properties, which do not depend on the attribution. The batch analytical solution is
`reid1965batch` (paywalled; the oracle is derived by hand in the spec, not read on the paper); the continuous form is
derived from the steady balance of one tank and `austin1984ballmilling` is not read.

**Worked example (test).** Three classes, $S = (0.5, 0.3, 0)/60$ 1/s, $b_{21} = 0.6$, $b_{31} = 0.4$, $b_{32} = 1$,
feed (1, 0, 0): the class masses at 60, 120 and 300 s are (0.606531, 0.201431, 0.192038), (0.367879, 0.271398,
0.360722) and (0.082085, 0.211568, 0.706347) (`tests/unit/test_t_005_020_pbm_batch.py:34-36, 83-95`), checked against
the analytical solution $m_1 = e^{-S_1 t}$, $m_2 = b_{21}S_1/(S_2 - S_1)\,(e^{-S_1 t} - e^{-S_2 t})$
(`test_t_005_020_pbm_batch.py:39-42, 72-80`), the confluent case $S_1 = S_2$ with $m_2 = b_{21}S t e^{-St}$
(`:98-108`) and a fourth-order Runge-Kutta reference (`:45-57`). One tank with $\tau$ = 120 s gives (0.5, 0.1875,
0.3125) (`test_t_005_021_pbm_continuous.py:48-56`).

## Flotation kinetics and two-product recovery

| Model | Equation | Impl |
|---|---|---|
| First order | $R = R_\infty\left(1 - e^{-kt}\right)$ | `_flotation.py:65` |
| Klimpel | $R = R_\infty\left[1 - \dfrac{1 - e^{-kt}}{kt}\right]$ | `_flotation.py:68-76, 115` |
| Equal perfectly mixed cells in series | $R = R_\infty\left[1 - (1 + k\tau)^{-N}\right]$, one cell $R_\infty k\tau/(1 + k\tau)$ | `_flotation.py:159` |
| Two product | $C/F = (f - t)/(c - t)$, $R = c\,(f - t)/\big(f\,(c - t)\big)$ | `_flotation.py:204-205` |

$R_\infty \in (0, 1]$ is the ultimate recovery, $k$ the rate constant (1/s; for Klimpel the maximum rate of a uniform
distribution on $[0, k]$), $t$ the flotation time and $\tau$ the residence time of each cell (s); $f$, $c$ and $t$ in
the two-product formula are feed, concentrate and tailings grades in any one unit, with $0 \le t < f < c$. Klimpel is
the first-order recovery averaged over a uniform rate distribution; for $kt < 1$ the factor is evaluated by a
series so that small $kt$ keeps full precision (`_flotation.py:16-18, 68-76`).

**Source and UNVERIFIED rows.** `wills2016` (textbook, paywalled) and `gharai2016flotation` (review, paywalled) were
not read: the oracles are the derivations (Klimpel as a rate average, the cell form by integrating the first-order law
against an exponential residence-time distribution) and hand calculations, so the attribution of the Klimpel and cell
forms is **UNVERIFIED**.

**Worked examples (tests).** With $R_\infty$ = 0.9, $k$ = 1/60 1/s, $t$ = 300 s: first order 0.893936
(`test_t_005_030_flotation.py:30-37`), Klimpel 0.721213 checked against trapezoid quadrature of the rate average
(`:52-70`), one cell 0.75 (`:92-98`). Two product with $f$ = 1 %, $c$ = 25 %, $t$ = 0.1 %: yield 0.0361446, recovery
0.903614 (`test_t_005_031_two_product.py:30-40`).

## Crusher, size helpers and the mine-to-mill chain

A cumulative passing curve is given at upper class sizes $s_1 > \dots > s_n$; interpolation between points is linear
in $(\ln x, \ln P)$, and in $(\ln x, P)$ where a point has $P = 0$.

| Step | Function | Equation | Impl |
|---|---|---|---|
| Class masses | `class_masses` | $m_i = P(s_i) - P(s_{i+1})$, $m_n = P(s_n)$ | `_size.py:167` |
| Inverse | `cumulative_passing` | $P_i = \sum_{k \ge i} m_k$ | `_size.py:205` |
| Size at a fraction | `passing_size` | log-log interpolation, default fraction 0.8 | `_size.py:76-87, 128` |
| Crusher product | `crusher_matrix_model` | $\mathbf p = (I - C)(I - BC)^{-1}\mathbf f$, solved as $\mathbf x = \mathbf f + BC\mathbf x$, $\mathbf p = (I - C)\mathbf x$ | `_size.py:258-261` |
| Classification | `whiten_classification` | $c = 0$ for $x < k_1$; $1 - \big((k_2 - x)/(k_2 - k_1)\big)^{k_3}$ for $k_1 \le x < k_2$; 1 for $x \ge k_2$ | `_size.py:305-306` |
| Chain | `mine_to_mill_chain` | class masses, crusher, cumulative passing, $F_{80}$ and fines, energy from $F_{80}$ to the target, $\dot m = P/W$ | `_size.py:404-424` |

$C = \operatorname{diag}(c)$ holds the probability $c_i$ that a class-$i$ particle is broken. Because $B$ is strictly
lower triangular, $I - BC$ is unit lower triangular and always invertible, and the total mass is conserved. The chain
reads the Bond energy (`bond_energy`) or the Morrell energy (`morrell_tumbling_coarse` plus `morrell_tumbling_fine`)
from the crusher product $F_{80}$ to the target grind, and returns the throughput

$$\dot m = \frac{P_{\text{installed}}}{W}\quad[\text{kg/s}]$$

<!-- impl: src/minephys/comminution/_size.py:419-424 -->

with $W$ the specific energy (J/kg) and $P_{\text{installed}}$ the installed mill power (W). It returns `ChainResult`
(`product_passing`, `f80`, `fines_fraction`, `specific_energy`, `throughput`).

**Limits and UNVERIFIED rows.** The chain is steady state and one pass; the crusher classification and breakage are
inputs (no closed-side-setting correlation was read on a primary source). The crusher matrix form and its attribution
to Whiten (1972, `whiten1972crushing`, bibliographic, not read) and the classification function form are
**UNVERIFIED**: the oracle is the steady-state balance itself. A Bond target below 70 µm or a Morrell target below
45 µm emits `ValidityWarning`. Typical work-index ranges (about 7 to 25 kWh/t) are UNVERIFIED and never used as
defaults: indices are always inputs. The Swebrec curve used as oracle is `ouchterlony2005swebrec` (paywalled).

**Worked examples (tests).**

- Crusher: feed (0.6, 0.3, 0.1), $c$ = (0.8, 0.4, 0), $b_{21}$ = 0.7, $b_{31}$ = 0.3, $b_{32}$ = 1 gives the product
  (0.12, 0.3816, 0.4984) (`tests/unit/test_t_005_042_crusher.py:35-45`); the classification at the midpoint with
  $k_3$ = 2 is 0.75 (`:94-110`).
- Swebrec: $x_{80} = x_{\max}(x_{50}/x_{\max})^{0.25^{1/b}}$ is 0.70711 m for $x_{50}$ = 0.25 m, $x_{\max}$ = 2 m,
  $b$ = 2, recovered by `passing_size` on a 400-point grid within rtol 2e-3
  (`tests/unit/test_t_005_040_psd.py:41-55`).
- Chain with an identity crusher ($C = 0$) and Bond's law reproduces Bond's law at that closed-form $x_{80}$ within
  rtol 2e-3 (`tests/unit/test_t_005_044_chain.py:174-197`); the three-class chain gives the product passing
  (1.0, 0.88, 0.4984) (`:150-171`); the Bond and Morrell chains equal the hand composition of the component functions
  (`:96-147`).

## Assumptions and limits

- The chain energy is the tumbling-mill energy from the crusher product $F_{80}$ to the target grind.
- Published totals are sums of rounded stage values, so printed totals are compared within 0.1 kWh/t.
- The Morrell coarse term needs a feed coarser than 750 µm and the fine term a grind finer than 750 µm.
- Out of scope: circuit dynamics and control, mill power models, cyclone partition, slurry rheology, froth and
  entrainment, reagent chemistry, mass-balance reconciliation and equipment sizing.

## References

Keys of `knowledge/references.bib`.

1. `mcivor2016bondgmsg`: McIvor, R. E. (2016), GMSG guideline: determining the Bond efficiency of industrial grinding circuits, SME Annual Meeting. http://www.ceecthefuture.org/wp-content/uploads/2015/12/Bond-GMSG-SME-conference.pdf
2. `gmsg2016morrell`: Global Mining Standards and Guidelines Group (2016), Morrell method for determining comminution circuit specific energy. https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
3. `bond1952third`: Bond, F. C., The third theory of comminution (bibliographic only). https://onemine.org/documents/the-third-theory-of-comminution
4. `bond1961crushing`: Bond, F. C., Crushing and grinding calculations (bibliographic only). https://store.smenet.org/20slp36/695
5. `morrell2004alternative`: https://doi.org/10.1016/j.minpro.2003.10.002
6. `morrell2008method`: https://doi.org/10.1016/j.mineng.2007.10.001
7. `morrell2009predicting`: https://doi.org/10.1016/j.mineng.2009.01.005
8. `austin1971rate`: https://doi.org/10.1016/0032-5910(71)80064-5
9. `reid1965batch`: https://doi.org/10.1016/0009-2509(65)80093-8
10. `austin1984ballmilling`: Austin, Klimpel and Luckie, Process Engineering of Size Reduction: Ball Milling (bibliographic only). https://search.worldcat.org/search?q=Process+Engineering+of+Size+Reduction+Ball+Milling
11. `whiten1972crushing`: Whiten (1972), crushing plant simulation (bibliographic only). https://onemine.org/documents/the-simulation-of-crushing-plants-with-models-developed-using-multiple-spline-regression
12. `gharai2016flotation`: https://doi.org/10.1080/08827508.2015.1115991
13. `wills2016`: Wills' Mineral Processing Technology, 8th ed. https://doi.org/10.1016/C2010-0-65478-2
14. `ouchterlony2005swebrec`: https://doi.org/10.1179/037178405X44539
