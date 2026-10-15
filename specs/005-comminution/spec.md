# Spec 005 — Comminution: Bond, Morrell, population balance, flotation kinetics and the mine-to-mill chain
Status: Clarified
Tier: M · Parent: 000-foundation · Approved: —
Supersedes/Modifies: (none)

## 1. Intent

`minephys.comminution` gives reference implementations of the classical size-reduction and recovery models that turn
a blast size distribution into mill energy, mill throughput and flotation recovery:

- Bond's third law, the Bond operating work index and the Bond ball-mill test work index;
- the Morrell energy–size relation with the SMC hardness indices $M_{ia}$, $M_{ib}$, $M_{ic}$, $M_{ih}$ and its
  circuit terms ($W_a$, $W_b$, $W_c$, $W_h$, $W_s$);
- the population balance model (selection and breakage functions; batch and perfectly mixed continuous mills);
- first-order, Klimpel and perfectly-mixed-cell flotation kinetics, and the two-product formula;
- a steady-state crusher matrix model and a **mine-to-mill chain** that takes a blast passing curve (for example the
  Swebrec curve of spec 002-blasting) through a crusher to the mill feed size, the specific energy and the throughput
  at a given installed power.

Every equation is implemented from its source, every constant is a cited row of the knowledge table
`knowledge/comminution.yaml` (foundation DC-000-02, served by spec 008-knowledge), and every function validates its
inputs. Each published worked
example that could be read is a test.

**Who benefits:** process engineers and students who need an inspectable, unit-safe chain; PitStudio, which uses the
chain as the exact ground truth of its learned mine-to-mill meta-model (PitStudio spec 017-planning-survey) and as a
live model in the browser through Pyodide.

**Out of scope:** circuit dynamics and control, mill power models (charge, speed, liner), cyclone partition curves,
slurry rheology, froth and entrainment, reagent chemistry, multi-stream mass-balance reconciliation, equipment sizing.
No learned model lives in this library. Results are educational and reference-grade, valid only inside each model's
stated range; they are not design values.

## 2. User stories

### US-005-1 (P1) Energy–size laws
As a process engineer, I want Bond's law, the Bond work indices and the Morrell circuit terms with SI inputs, so that I
can compute specific grinding energy from plant sizes and laboratory indices. Independent test: the published worked
examples of the Bond-efficiency and Morrell-method guidelines reproduce to their published rounding.

### US-005-2 (P1) Population balance grinding
As a student, I want batch and continuous population-balance mills with explicit selection and breakage functions, so
that I can see how a size distribution evolves and check that mass is conserved. Independent test: a three-class
batch mill matches the analytical solution of the batch grinding equation.

### US-005-3 (P2) Flotation kinetics and recovery
As a metallurgist, I want first-order, Klimpel and perfectly-mixed-cell recoveries and the two-product formula, so that
I can compare kinetic assumptions and close a simple mass balance. Independent test: Klimpel's recovery equals the
average of first-order recoveries over a uniform rate distribution, by quadrature.

### US-005-4 (P1) Mine-to-mill chain
As a mining engineer, I want to feed a blast passing curve through a crusher model to the mill and read the feed $F_{80}$,
the fines fraction, the specific energy and the throughput at a given installed power, so that I can see how blasting
moves energy and throughput downstream. Independent test: with an identity crusher and Bond's law, the chain equals
Bond's law evaluated at the closed-form Swebrec $x_{80}$.

### US-005-5 (P2) Cited constants
As a reviewer, I want every constant the module uses to come from a cited knowledge row with page and verification
status, so that I can audit each number. Independent test: changing a knowledge row changes the function result
accordingly.

## 3. Functional requirements (EARS)

Conventions for every row (000-foundation): SI units at the API (FR-000-08; sizes in m, specific energy and work
indices in J/kg, power in W, throughput in kg/s, time in s, rates in 1/s, laboratory grindability in kg per mill
revolution); elementwise functions follow FR-000-07 (scalars give `numpy.float64`, arrays a float64 array of the
broadcast shape); non-finite, shape, size, domain and option errors raise `minephys.InputError` naming the argument
(FR-000-10, FR-000-12 to FR-000-15) and non-numeric arguments `minephys.InputTypeError` (FR-000-11); validity-range
violations emit `minephys.ValidityWarning` (FR-000-16). "µm", "g" and "kWh/t" below are the units in which the sources
publish the equations; each function converts once at its boundary with the factors of the foundation `units` table
(1 µm = 10⁻⁶ m, 1 g = 10⁻³ kg, 1 kWh/t = 3,600 J/kg). Signatures and argument units are those written in each row.

| ID | Pattern | Requirement | Verification |
|---|---|---|---|
| FR-005-01 | Ubiquitous | `bond_energy(work_index, f80, p80)` shall return $W = 10\,W_i\,(1/\sqrt{P_{80}} - 1/\sqrt{F_{80}})$ with $P_{80}$, $F_{80}$ in µm (converted from m) and $W$ in the units of $W_i$ (J/kg), within rtol 1e-12 of the hand calculation. | unit |
| FR-005-02 | Ubiquitous | `bond_operating_work_index(specific_energy, f80, p80)` shall return $W_{io} = W / (10/\sqrt{P_{80}} - 10/\sqrt{F_{80}})$ (sizes in µm, J/kg), within rtol 1e-12 of the hand calculation. | unit |
| FR-005-03 | Ubiquitous | `bond_ball_mill_work_index(closing_screen, grindability, f80, p80)` shall return $1.1025 \times 44.5 / \big(P_1^{0.23}\,G_{bp}^{0.82}\,(10/\sqrt{P_{80}} - 10/\sqrt{F_{80}})\big)$ kWh/t (sizes in µm, $G_{bp}$ in g/rev converted from kg/rev) converted to J/kg, and shall reproduce the published test result 10.0 kWh/short ton = 11.0 kWh/t for $P_1$ = 106 µm, $G_{bp}$ = 1.825 g/rev (1.825 × 10⁻³ kg/rev), $F_{80}$ = 2,746.1 µm, $P_{80}$ = 79.7 µm within ± 0.05 kWh/t (TC-2). | unit |
| FR-005-04 | Unwanted | If an argument of `bond_energy`, `bond_operating_work_index` or `bond_ball_mill_work_index` is NaN, ±inf or ≤ 0, or the arguments are not broadcastable, or $p_{80} \ge f_{80}$ anywhere, then the function shall raise `InputError` naming the argument (a non-numeric argument: `InputTypeError`) and shall return no partial result. | unit (hostile) |
| FR-005-05 | Ubiquitous | `morrell_energy(m_index, x1, x2)` shall return $W = M_i \cdot 4\,\big(x_2^{f(x_2)} - x_1^{f(x_1)}\big)$, $f(x) = -(0.295 + x/10^6)$, with feed $x_1$ and product $x_2$ 80 % passing sizes in µm (converted from m) and $W$ in the units of $M_i$ (J/kg), within rtol 1e-12 of the hand calculation. | unit |
| FR-005-06 | Ubiquitous | `morrell_tumbling_coarse(mia, x1, pebble_crusher)` shall return $W_a = K_1 M_{ia}\,4\,(750^{f(750)} - x_1^{f(x_1)})$ with $K_1$ = 0.95 when `pebble_crusher` is true and 1.0 otherwise, $x_1$ the tumbling-mill feed $F_{80}$ in µm. | unit |
| FR-005-07 | Ubiquitous | `morrell_tumbling_fine(mib, p80)` shall return $W_b = M_{ib}\,4\,(P_{80}^{f(P_{80})} - 750^{f(750)})$ with $P_{80}$ the final grind in µm. | unit |
| FR-005-08 | Ubiquitous | `morrell_crusher(mic, x1, x2, closed_circuit, stage)` shall return $W_c = S_c K_2 M_{ic}\,4\,(x_2^{f(x_2)} - x_1^{f(x_1)})$ with $K_2$ = 1.0 (closed circuit) or 1.19 (open circuit), and $S_c = \min(55\,(x_1 x_2)^{-0.2}, 1)$ (sizes in µm) when `stage` is `"primary"` or `"secondary"` and $S_c = 1$ when `stage` is `"tertiary"` or `"pebble"`. | unit |
| FR-005-09 | Ubiquitous | `morrell_hpgr(mih, x1, x2, closed_circuit)` shall return $W_h = S_h K_3 M_{ih}\,4\,(x_2^{f(x_2)} - x_1^{f(x_1)})$ with $K_3$ = 1.0 (closed) or 1.19 (open) and $S_h = \min(35\,(x_1 x_2)^{-0.2}, 1)$. | unit |
| FR-005-10 | Ubiquitous | `morrell_size_distribution_correction(mia, x1, x2)` shall return $W_s = 0.19\,M_{ia}\,4\,(x_2^{f(x_2)} - x_1^{f(x_1)})$, with $x_1$ the circuit feed and $x_2$ the ball-mill circuit feed (µm). | unit |
| FR-005-11 | Ubiquitous | `morrell_mib(closing_screen, grindability, f80, p80)` shall return $M_{ib} = 18.18 / \big(P_{100}^{0.295}\,G_{bp}\,(P_{80}^{f(P_{80})} - F_{80}^{f(F_{80})})\big)$ kWh/t (sizes in µm, $G_{bp}$ in g/rev converted from kg/rev) converted to J/kg. | unit |
| FR-005-12 | Unwanted | If an argument of a `morrell_*` function is NaN, ±inf or ≤ 0; if the product size is not finer than the feed size; if `morrell_tumbling_coarse` gets $x_1 \le 750$ µm or `morrell_tumbling_fine` gets $P_{80} \ge 750$ µm; or if `stage` is not one of `"primary"`, `"secondary"`, `"tertiary"`, `"pebble"`, then the function shall raise `InputError` naming the argument (non-numeric or non-boolean flags: `InputTypeError`). | unit (hostile) |
| FR-005-13 | Ubiquitous | `pbm_batch_grinding(mass, selection, breakage, times)` shall return the class masses $\mathbf m(t) = e^{At}\,\mathbf m(0)$, $A = -\mathrm{diag}(S) + B\,\mathrm{diag}(S)$, at every requested time (shape `(len(times), n)`), for classes ordered coarse to fine, selection $S_i$ in 1/s and breakage $b_{ij}$ the fraction of broken class-$j$ material entering finer class $i$. | unit + property |
| FR-005-14 | Ubiquitous | `pbm_continuous_mill(feed, selection, breakage, residence_time, n_tanks=1)` shall return the steady-state product of `n_tanks` equal perfectly mixed tanks in series with total mean residence time $\tau$: $\mathbf m_{out} = (I - (\tau/N)A)^{-N}\,\mathbf m_{in}$. | unit + property |
| FR-005-15 | Unwanted | If, in `pbm_batch_grinding` or `pbm_continuous_mill`, the shapes disagree, $n < 2$ or $n > 200$, any entry is NaN, ±inf or negative, `breakage` is not strictly lower triangular, a breakage column $j$ with $S_j > 0$ does not sum to 1 within 1e-12, the last (sink) class has $S_n \ne 0$, a time is negative, $\tau \le 0$, or `n_tanks` is not an integer ≥ 1, then the function shall raise `InputError` naming the argument. | unit (hostile) |
| FR-005-16 | Ubiquitous | `austin_selection(sizes, a, alpha, mu, lam, x0=None)` (with `x0=None` meaning the row `austin_reference_size`, 1 mm) shall return $S_i = a\,(x_i/x_0)^{\alpha} / \big(1 + (x_i/\mu)^{\Lambda}\big)$ in 1/s for representative class sizes $x_i$ (m). | unit |
| FR-005-17 | Ubiquitous | `austin_breakage(sizes, phi, gamma, beta)` shall return the $n \times n$ strictly lower-triangular matrix with $b_{ij} = B_j(s_i) - B_j(s_{i+1})$ for $j < i < n$ and $b_{nj} = B_j(s_n)$, where $B_j(s) = \phi\,(s/s_{j+1})^{\gamma} + (1 - \phi)\,(s/s_{j+1})^{\beta}$ and $s_1 > \dots > s_n$ are the upper sizes of the classes, so that every column $j < n$ sums to 1 within 1e-12. | unit + property |
| FR-005-18 | Unwanted | If `austin_selection` or `austin_breakage` gets sizes that are not strictly decreasing and positive, $\phi \notin (0, 1]$, a non-positive exponent, $a < 0$, $\mu \le 0$, $\Lambda < 0$, or any non-finite value, then the function shall raise `InputError` naming the argument. | unit (hostile) |
| FR-005-19 | Ubiquitous | `flotation_first_order(r_inf, k, t)` shall return $R = R_\infty (1 - e^{-kt})$ ($k$ in 1/s, $t$ in s) within rtol 1e-12. | unit |
| FR-005-20 | Ubiquitous | `klimpel_recovery(r_inf, k, t)` shall return $R = R_\infty\,[1 - (1 - e^{-kt})/(kt)]$, equal to 0 at $t = 0$ and within rtol 1e-12 of the series $R_\infty(u/2 - u^2/6 + u^3/24)$ for $u = kt \in [10^{-12}, 10^{-4}]$ (no cancellation loss). | unit + property |
| FR-005-21 | Ubiquitous | `flotation_cell_recovery(r_inf, k, tau, n_cells=1)` shall return the recovery of `n_cells` equal perfectly mixed cells in series, each of mean residence time $\tau$: $R = R_\infty\,[1 - (1 + k\tau)^{-N}]$, which for one cell is $R_\infty k\tau/(1 + k\tau)$. | unit |
| FR-005-22 | Ubiquitous | `two_product_recovery(feed_grade, concentrate_grade, tail_grade)` shall return the mass yield $C/F = (f - t)/(c - t)$ and the recovery $R = c\,(f - t)/(f\,(c - t))$, both dimensionless, within rtol 1e-12. | unit |
| FR-005-23 | Unwanted | If a flotation function gets $R_\infty \notin (0, 1]$, $k \le 0$, $t < 0$, $\tau \le 0$, `n_cells` not an integer ≥ 1, or a non-finite value, or if `two_product_recovery` gets grades that do not satisfy $0 \le t < f < c$, then the function shall raise `InputError` naming the argument. | unit (hostile) |
| FR-005-24 | Ubiquitous | `passing_size(sizes, passing, fraction=0.8)` shall return the size at which the cumulative passing curve equals `fraction`, interpolating linearly in $(\log x, \log P)$ between the two bracketing points, and shall return a grid size exactly when `fraction` equals its passing value. | unit + property |
| FR-005-25 | Ubiquitous | `class_masses(sizes, passing)` shall convert a cumulative passing curve on upper class sizes $s_1 > \dots > s_n$ into class mass fractions $m_i = P(s_i) - P(s_{i+1})$ ($i < n$) and $m_n = P(s_n)$, and `cumulative_passing(masses)` shall invert it exactly. | unit |
| FR-005-26 | Unwanted | If `passing_size`, `class_masses` or `cumulative_passing` gets sizes that are not strictly monotone and positive, passing values outside [0, 1] or not monotone in size, mismatched lengths, fewer than 2 points, more than 10,000 points, NaN/inf, or a `fraction` outside the range spanned by the curve, then the function shall raise `InputError` naming the argument. | unit (hostile) |
| FR-005-27 | Ubiquitous | `crusher_matrix_model(feed, classification, breakage)` shall return the steady-state crusher product $\mathbf p = (I - C)(I - BC)^{-1}\mathbf f$ for a diagonal classification matrix $C$ (probabilities $c_i \in [0, 1]$ of a class-$i$ particle being broken) and a strictly lower-triangular breakage matrix $B$, conserving total mass within rtol 1e-12. | unit + property |
| FR-005-28 | Ubiquitous | `whiten_classification(sizes, k1, k2, k3)` shall return $c(x) = 0$ for $x < k_1$, $1 - \big((k_2 - x)/(k_2 - k_1)\big)^{k_3}$ for $k_1 \le x < k_2$, and 1 for $x \ge k_2$ ($k_1 < k_2$ in m, $k_3 > 0$). | unit |
| FR-005-29 | Unwanted | If `crusher_matrix_model` gets mismatched shapes, a classification outside [0, 1], a breakage that is not strictly lower triangular or whose column $j$ with $c_j > 0$ does not sum to 1 within 1e-12, a finest class with $c_n > 0$, or negative/non-finite values, or if `whiten_classification` gets $k_1 \ge k_2$, $k_3 \le 0$ or non-finite values, then the function shall raise `InputError` naming the argument. | unit (hostile) |
| FR-005-30 | Event | When `mine_to_mill_chain(sizes, blast_passing, classification, breakage, target_p80, installed_power, energy_model, …)` is called, the module shall compose `class_masses` → `crusher_matrix_model` → `cumulative_passing` → `passing_size` (crusher product $F_{80}$ and the fraction finer than `fines_size`) → specific energy from $F_{80}$ to `target_p80` (`energy_model="bond"`: `bond_energy`; `"morrell"`: `morrell_tumbling_coarse` + `morrell_tumbling_fine`) → throughput $\dot m = P/W$ (kg/s), and shall return all of them, each equal within rtol 1e-12 to the same composition done by hand from the component functions. | unit + property |
| FR-005-31 | Unwanted | If `mine_to_mill_chain` gets an unknown `energy_model`, a `target_p80` not finer than the crusher product $F_{80}$, a non-positive installed power, the indices its energy model needs missing or invalid, or inputs that the component functions reject, then it shall raise `InputError` naming the argument and shall not return a partial result. | unit (hostile) |
| FR-005-32 | Unwanted | If `bond_energy`, `bond_operating_work_index` or `mine_to_mill_chain` (Bond model) gets a product $P_{80}$ below 70 µm (row `bond_min_product_size`), then it shall emit `ValidityWarning` naming `p80`, the bound and the row id, and shall still return the result (FR-000-16). | unit (`pytest.warns`) |
| FR-005-33 | Unwanted | If `morrell_tumbling_fine` or `mine_to_mill_chain` (Morrell model) gets a final grind $P_{80}$ below 45 µm (row `morrell_fine_grind_limit`), then it shall emit `ValidityWarning` naming `p80`, the bound and the row id, and shall still return the result (FR-000-16). | unit (`pytest.warns`) |
| FR-005-34 | Ubiquitous | Every constant in FR-005-01 to FR-005-11, FR-005-32 and FR-005-33 shall be read through `minephys.knowledge.get_value` from its row of `knowledge/comminution.yaml` (§7; foundation FR-000-19), so that replacing a row value in a test fixture changes the function result by the corresponding analytical amount. | contract |

## 4. Correctness properties

Generators (Hypothesis, `thresholds.yaml` `property_tests`: 200 examples in CI, 2,000 at release): sizes log-uniform in
[10 µm, 1 m]; indices log-uniform in [3,600, 3.6 × 10⁵] J/kg (1–100 kWh/t); rates log-uniform in [10⁻⁴, 1] 1/s;
times uniform in [0, 10⁴] s; float64 throughout.

| ID | Property (for all …) | Input domain / generator | Tolerance |
|---|---|---|---|
| P-005-01 | Bond monotonicity: $W$ strictly decreases when $F_{80}$ decreases towards $P_{80}$ and strictly increases when $P_{80}$ decreases, for fixed $W_i$. | sizes with $P_{80} < F_{80}$ | TC-0 (strict inequality) |
| P-005-02 | Bond scaling: $W(\lambda W_i, F, P) = \lambda\,W(W_i, F, P)$, and the inverse: `bond_operating_work_index(bond_energy(Wi, F, P), F, P)` $= W_i$. | $\lambda \in [10^{-3}, 10^3]$ | TC-1 |
| P-005-03 | Bond and Morrell path additivity: for any $F > M > P$, $W(F \to P) = W(F \to M) + W(M \to P)$ with one index (both laws telescope). | sizes as above | rtol 1e-11 (TC-1 widened ×10: three evaluations are summed) |
| P-005-04 | Morrell consistency: with $M_{ia} = M_{ib} = M_i$ and $K_1 = 1$, $W_a(x_1) + W_b(P_{80}) =$ `morrell_energy(Mi, x1, P80)` for $x_1 > 750$ µm $> P_{80}$; $W_c$ with $S_c = K_2 = 1$ equals `morrell_energy`. | sizes straddling 750 µm | rtol 1e-11 (as P-005-03) |
| P-005-05 | Morrell monotonicity and scaling: $W$ is linear in $M_i$ and strictly increases as $x_2$ decreases. | as above | TC-1; TC-0 (strict) |
| P-005-06 | PBM mass conservation: $\sum_i m_i(t) = \sum_i m_i(0)$ and $m_i(t) \ge 0$ (batch); $\sum \mathbf m_{out} = \sum \mathbf m_{in}$ (continuous). | $n \in [2, 30]$, valid $S$, $B$ | atol 1e-12 × total; $m_i \ge -10^{-14}$ |
| P-005-07 | PBM semigroup and linearity: $\mathbf m(t_1 + t_2) = $ batch(batch($\mathbf m_0$, $t_1$), $t_2$) and batch($a\mathbf m_0 + b\mathbf m_0'$) $= a\,$batch($\mathbf m_0$) $+ b\,$batch($\mathbf m_0'$). | $a, b \ge 0$ | rtol 1e-10, atol 1e-13 (matrix exponential, $S_{\max} t \le 50$) |
| P-005-08 | PBM exact decay of the top class: $m_1(t) = m_1(0)\,e^{-S_1 t}$; time-scale invariance: scaling $S$ by $\lambda$ and $t$ by $1/\lambda$ leaves $\mathbf m$ unchanged. | as above | TC-1 / rtol 1e-10 |
| P-005-09 | Continuous mill limits: $\tau \to 0$ gives $\mathbf m_{in}$; as `n_tanks` grows the product converges to the batch result at $t = \tau$, with error non-increasing from $N$ = 1, 2, 4, …, 1,024 and below 1e-3 × total at $N$ = 1,024. | $\tau S_{\max} \le 10$ | as stated |
| P-005-10 | Flotation ordering: $0 \le R_{\text{Klimpel}}(k, t) \le R_{\text{first}}(k, t) \le R_\infty$ and $R_{\text{cell}}(k, \tau{=}t, N{=}1) \le R_{\text{first}}(k, t)$; all non-decreasing in $t$. | $kt \in [0, 50]$ | TC-0 ordering with atol 1e-15 |
| P-005-11 | Flotation time-scale invariance: every kinetic recovery depends on $k$ and $t$ only through $kt$ (or $k\tau$): $R(\lambda k, t/\lambda) = R(k, t)$. Many-cell limit: $R_{\text{cell}}(k, \tau/N, N) \to R_{\text{first}}(k, \tau)$ as $N \to \infty$ (error < 1e-3 at $N$ = 1,000 for $k\tau \le 5$). | $\lambda \in [10^{-3}, 10^3]$ | TC-1 |
| P-005-12 | Two-product unit invariance and consistency: multiplying all three grades by $\lambda$ (percent vs fraction) leaves yield and recovery unchanged, and $R = (C/F)\,c/f$. | $0 \le t < f < c \le 1$ | TC-1 |
| P-005-13 | Crusher model: mass conservation; $C = 0$ returns the feed exactly; the product is linear in the feed; with $c_1 = 1$ the coarsest class leaves the product completely. | $n \in [2, 40]$ | TC-1; TC-0 for $C = 0$ |
| P-005-14 | `passing_size` equivariance and monotonicity: scaling all sizes by $\lambda$ scales the result by $\lambda$; the result is non-decreasing in `fraction`. | $\lambda \in [10^{-3}, 10^3]$ | TC-1 |
| P-005-15 | Chain: scaling `installed_power` by $\lambda$ scales the throughput by $\lambda$ and leaves $F_{80}$ and $W$ unchanged; scaling the blast feed mass leaves every output unchanged; with $C = 0$ and `energy_model="bond"` the chain equals `bond_energy(Wi, x80, P80)` with the Swebrec closed-form $x_{80} = x_{\max}(x_{50}/x_{\max})^{0.25^{1/b}}$. | Swebrec $x_{50} \in [0.05, 1]$ m, $x_{\max} \in [2x_{50}, 5]$ m, $b \in [1, 4]$; 400 log-spaced sizes from 10 µm to $x_{\max}$ | TC-1 (scaling); rtol 2e-3 on $x_{80}$ and $W$ (log-log interpolation error on that grid is ≤ 4.3e-4, hand-checked) |

## 5. Non-functional requirements and success criteria

| ID | Statement | Threshold | Measured by |
|---|---|---|---|
| NFR-005-01 | `minephys.comminution` imports only the standard library, NumPy, PyYAML and `minephys` modules (no SciPy, networkx, pandas; foundation NFR-000-05). | 0 other top-level modules imported | contract test (subprocess import audit) |
| NFR-005-02 | Latency (foundation NFR-000-07): closed forms on scalars; `pbm_batch_grinding` at the reference size (30 classes, 10 times), `pbm_continuous_mill` (30 classes, 10 tanks) and `mine_to_mill_chain` (400 sizes). | ≤ 1 ms and ≤ 50 ms median respectively | `tools/bench.py` |
| NFR-005-03 | One worked-example oracle per function family runs in the Pyodide smoke subset (foundation FR-000-25). | 100 % pass | Pyodide job |
| NFR-005-04 | Every public function's docstring is a model card (foundation FR-000-09): equation, units in brackets, source key and page, validity, knowledge rows. | 100 % of `__all__` | foundation model-card audit |
| SC-005-01 | Published worked examples reproduce: the Morrell-method guideline Annex C (13 stage values and 3 circuit totals) and the Bond-efficiency guideline (14 values: 1 black-box, 5 rod–ball, 6 SAG–ball, 2 ball-mill test). | each within half a unit of its last published digit | unit tests |
| SC-005-02 | Mutation score on `minephys.comminution`. | ≥ 0.80 (`mutation.numerical_core_min`) | mutation run |

## 6. Data contracts

| ID | Artifact | Schema | Producer → Consumer |
|---|---|---|---|
| DC-005-01 | `src/minephys/knowledge/comminution.yaml` (rows of §7) | `contracts/knowledge-table.schema.json` (foundation DC-000-02) | this spec → `minephys.comminution`, knowledge export, docs generator, PitStudio knowledge pages |
| DC-005-02 | comminution entries of `src/minephys/knowledge/catalogue/equations.yaml` (one per model of FR-005-01 to FR-005-28) | `contracts/knowledge-equations.schema.json` (spec 008 DC-008-01) | this spec → knowledge export → PitStudio equation explorer |

## 7. Edge cases and assumptions

**Knowledge rows** (`knowledge/comminution.yaml`, foundation DC-000-02). "Verified (date)" means read on the cited
document on that date during specification; each verified row is pinned by a `@pytest.mark.knowledge` test (foundation
FR-000-21), first by the knowledge task's transcription test and then by the worked-example tests. The structural
factors 1 (closed circuit, no pebble crusher, no size correction) are allowed literals (FR-000-19), not rows.

| Row id | Value | Units as published | Role | Citation · page | Status | Symbol |
|---|---|---|---|---|---|---|
| `bond_law_coefficient` | 10 | 1 (with sizes in µm) | model_constant | `mcivor2016bondgmsg` · p. 1, "Calculations"; worked examples p. 2 | verified (2026-10-06) | `bond_energy`, `bond_operating_work_index` |
| `bond_min_product_size` | 70 | µm | limit | `mcivor2016bondgmsg` · p. 1 ("applies down to approximately 70 µm") | verified (2026-10-06) | `bond_energy`, `bond_operating_work_index` |
| `bond_bm_constant` | 44.5 | kWh/short ton | model_constant | `mcivor2016bondgmsg` · p. 10, Annex C1 "Calculations" | verified (2026-10-06) | `bond_ball_mill_work_index` |
| `bond_bm_exponent_screen` | 0.23 | 1 | model_constant | same | verified (2026-10-06) | same |
| `bond_bm_exponent_grindability` | 0.82 | 1 | model_constant | same | verified (2026-10-06) | same |
| `bond_short_ton_to_metric` | 1.1025 | (kWh/t)/(kWh/st) | conversion | same ("Multiply by 1.1025 for kWh/mt") | verified (2026-10-06) | same |
| `morrell_coefficient` | 4 | 1 | model_constant | `gmsg2016morrell` · eq. 2, p. 2 | verified (2026-10-06) | all `morrell_*` energy functions |
| `morrell_f_constant` | 0.295 | 1 | model_constant | same | verified (2026-10-06) | same |
| `morrell_f_scale` | 1000000 | µm | model_constant | same | verified (2026-10-06) | same |
| `morrell_coarse_fine_boundary` | 750 | µm | model_constant | `gmsg2016morrell` · eqs. B2–B3, p. 6 | verified (2026-10-06) | `morrell_tumbling_coarse`, `morrell_tumbling_fine` |
| `morrell_fine_grind_limit` | 45 | µm | limit | `gmsg2016morrell` · §B.1, p. 6 ("approximately 45 µm") | verified (2026-10-06) | `morrell_tumbling_fine` |
| `morrell_k1_pebble_crusher` | 0.95 | 1 | model_constant | `gmsg2016morrell` · eq. B2, p. 6 | verified (2026-10-06) | `morrell_tumbling_coarse` |
| `morrell_k2_open_circuit` | 1.19 | 1 | model_constant | `gmsg2016morrell` · eq. B4, p. 6 | verified (2026-10-06) | `morrell_crusher` |
| `morrell_k3_open_circuit` | 1.19 | 1 | model_constant | `gmsg2016morrell` · eq. B6, p. 7 | verified (2026-10-06) | `morrell_hpgr` |
| `morrell_ks_crusher` | 55 | 1 | model_constant | `gmsg2016morrell` · eq. B5, p. 7 | verified (2026-10-06) | `morrell_crusher` |
| `morrell_ks_hpgr` | 35 | 1 | model_constant | `gmsg2016morrell` · §B.2.3, p. 7 | verified (2026-10-06) | `morrell_hpgr` |
| `morrell_s_exponent` | −0.2 | 1 | model_constant | `gmsg2016morrell` · eq. B5, p. 7 | verified (2026-10-06) | `morrell_crusher`, `morrell_hpgr` |
| `morrell_ws_factor` | 0.19 | 1 | model_constant | `gmsg2016morrell` · §B.2.4, p. 8 | verified (2026-10-06) | `morrell_size_distribution_correction` |
| `morrell_mib_constant` | 18.18 | kWh/t | model_constant | `gmsg2016morrell` · eq. 1, p. 2 | verified (2026-10-06) | `morrell_mib` |
| `morrell_mib_screen_exponent` | 0.295 | 1 | model_constant | same | verified (2026-10-06) | `morrell_mib` |
| `morrell_relative_error_sd` | 0.065 | 1 | limit | `gmsg2016morrell` · p. 3 ("1 standard deviation is 6.5 % of the relative errors") | verified (2026-10-06) | model card of `morrell_energy` |
| `austin_reference_size` | 0.001 | m | model_constant | `austin1984ballmilling` · page not read | UNVERIFIED | `austin_selection` default `x0` (warns on use, spec 008 FR-008-12) |

**Worked examples read on the sources** (the oracles of SC-005-01):

- Morrell-method guideline, Annex C (pp. 11–12), indices $M_{ia}$ = 19.4, $M_{ib}$ = 18.8, $M_{ic}$ = 7.2, $M_{ih}$ = 13.9
  kWh/t, circuit feed 100 mm, final $P_{80}$ = 106 µm. SABC: $W_a$ = 9.6, $W_b$ = 8.4, pebble crusher (52.5 → 12 mm,
  open circuit) $W_c$ = 1.13 per crusher tonne, 0.3 per new-feed tonne at 25 % recycle, total 18.3 kWh/t.
  HPGR/ball: secondary crusher (100 → 35 mm, closed, $S_c$ = 0.68) 0.4, HPGR (35 → 4 mm, closed, $S_h$ = 0.82) 2.4,
  $W_a$ (4 mm) 4.5, $W_b$ 8.4, total 15.7. Crushing/ball: secondary (open) 0.5, tertiary (35 → 6.5 mm, $S_c$ = 1.17
  → 1) 1.1, $W_a$ (6.5 mm) 5.5, $W_b$ 8.4, $W_s$ 0.9, total 16.4 kWh/t.
- Bond-efficiency guideline (pp. 1–2, 10–11): $W_{io}$ = 7.0 / (10/√212 − 10/√2,500) = 14.4 kWh/t;
  rod–ball standard circuit 9.5 × (10/√1,000 − 10/√19,300) = 2.32, 9.8 × (10/√155 − 10/√1,000) = 4.77, total 7.09,
  standard work index 9.70, operating work index 8.56 / (…) = 11.7; SAG–ball 16.0 → 0.9, 14.5 → 3.4, 13.8 → 8.0,
  total 12.3, standard 14.1, operating 14.6 / (…) = 16.8 kWh/t; ball-mill test sheet 10.0 kWh/st, 11.0 kWh/t.

**Assumptions and edge cases**

- Published totals are sums of rounded stage values (for example 15.62 kWh/t computed, 15.7 published). Stage values
  are compared with ± 0.05 kWh/t (± 0.005 where two decimals are published); totals with ± 0.1 kWh/t.
- Bond's law publishes $W_i$ in kWh per short ton in its original; the law is homogeneous in $W_i$, so the function
  returns $W$ in the units of $W_i$. Only the ball-mill test equation carries the short-ton → tonne factor, and it uses
  the published 1.1025 (the exact factor is 1.10231; the 0.01 % difference is below the test's resolution).
- $W_a$ and $W_s$ use the 750 µm boundary; $W_a$ is only defined for feeds coarser than 750 µm and $W_b$ for grinds
  finer than 750 µm (FR-005-12). The pebble-crusher recycle fraction is applied by the caller, as in the guideline.
- Sizes at the API are in metres; the conversion to µm happens once per call ($x_{\mu m} = 10^6 x_m$).
- PBM classes are ordered coarse to fine; the last class is the sink (everything below the grid) and has $S_n = 0$.
  Breakage into the same class is not modelled ($B$ strictly lower triangular). Selection and breakage are
  time-invariant and first order.
- The Austin selection and breakage forms are taken from the standard reference text; their attribution is
  **UNVERIFIED** (the text was not read). Their tests are hand calculations of the forms written in FR-005-16/17 and the
  structural properties (column sums, monotonicity), which do not depend on the attribution. The functions have no
  defaults besides `x0`, which is marked UNVERIFIED.
- The crusher matrix model $\mathbf p = (I - C)(I - BC)^{-1}\mathbf f$ follows from the steady-state balance
  $\mathbf x = \mathbf f + BC\mathbf x$, $\mathbf p = (I - C)\mathbf x$; its attribution to Whiten (1972), and the
  classification function form, are **UNVERIFIED**. The oracle is the balance itself (hand calculation), not the
  attribution. Because $B$ is strictly lower triangular, $I - BC$ is unit lower triangular and always invertible.
- Klimpel's form is derived here (average of $1 - e^{-k't}$ over $k' \in [0, k]$) and the cell form by integrating the
  first-order law against an exponential residence-time distribution; the review transcription in
  `gharai2016flotation` is **UNVERIFIED** (not read), so the oracles are the derivations.
- `two_product_recovery` requires $t < f < c$; real assays outside this order (sampling error) are rejected rather than
  returning a recovery outside [0, 1].
- Typical work-index ranges (≈ 7–25 kWh/t) are **UNVERIFIED** and are never used as defaults; indices are always
  inputs.
- The mine-to-mill chain is steady state and one-pass; the crusher's classification and breakage are inputs (no
  closed-side-setting correlation is assumed). Its energy is the tumbling-mill energy from the crusher product $F_{80}$
  to the target grind.

**Bibliography keys used** (entries of `knowledge/references.bib`, foundation DC-000-03; `access` is `open` for the two
guidelines, `bibliographic-only` for `bond1952third`, `bond1961crushing`, `austin1984ballmilling` and
`whiten1972crushing`, and `paywalled` for the others): `mcivor2016bondgmsg` (McIvor, R. E. (2016),
"GMSG guideline: determining the Bond efficiency of industrial grinding circuits", SME Annual Meeting, Preprint 16-033,
http://www.ceecthefuture.org/wp-content/uploads/2015/12/Bond-GMSG-SME-conference.pdf), `gmsg2016morrell` (Global Mining
Standards and Guidelines Group (2016), "Morrell method for determining comminution circuit specific energy and assessing
energy utilization efficiency of existing circuits",
https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf),
`bond1952third` (bibliographic), `bond1961crushing` (bibliographic), `morrell2004alternative`
(https://doi.org/10.1016/j.minpro.2003.10.002), `morrell2008method` (https://doi.org/10.1016/j.mineng.2007.10.001),
`morrell2009predicting` (https://doi.org/10.1016/j.mineng.2009.01.005), `austin1971rate`
(https://doi.org/10.1016/0032-5910(71)80064-5), `reid1965batch` (https://doi.org/10.1016/0009-2509(65)80093-8),
`austin1984ballmilling` (bibliographic), `whiten1972crushing` (bibliographic), `gharai2016flotation`
(https://doi.org/10.1080/08827508.2015.1115991), `wills2016` (https://doi.org/10.1016/C2010-0-65478-2),
`ouchterlony2005swebrec` (https://doi.org/10.1179/037178405X44539).

## 8. Clarifications log

- Resolved: the docs list the planned functions `bond_energy`, `morrell_energy`, `pbm_batch_grinding`,
  `flotation_first_order`, `klimpel_recovery`, `two_product_recovery`. This spec keeps those names and adds the
  Morrell circuit terms, the Bond work-index functions, the continuous mill, the Austin forms, the cell recovery, the
  crusher model and the chain; the reference page is updated with the added names in the build phase.
- Resolved (UNVERIFIED pinned): the Morrell constants 4, 0.295 and 10⁶, marked "UNVERIFIED — pinned at
  specification" in the docs, were read on the Morrell-method guideline (eq. 2, p. 2) and are now verified rows; the
  guideline's three worked circuits are the oracles. The guideline's typographical slips (a "35 µm" secondary product
  that is 35 mm; "160" for 106 µm in C.2.4; "1,000,000" for 100,000 µm in C.3.5) were resolved from the exponents it
  prints and the results it reports.
- Resolved: Bond's law and the ball-mill test equation, cited only bibliographically in the docs, were read on the
  Bond-efficiency guideline preprint, which reproduces Bond's 1961 equations; the 1952 and 1961 originals remain
  bibliographic.
- Resolved: the docs' Morrell form writes $W_i = M_i \cdot 4(\dots)$ in one place and $W = M_i \cdot 4(\dots)$ in
  another; the guideline's symbol is $W$ (specific energy), which this spec uses.
- Resolved: the mine-to-mill meta-model (learned, R² ≥ 0.95 acceptance) is a PitStudio model, not part of this
  library; this spec provides the analytical chain it is trained against.
- Resolved (foundation alignment): errors are `InputError` / `InputTypeError` and validity bounds warn with
  `ValidityWarning`; arguments are SI only, so the laboratory grindability is passed in kg per revolution (the sources'
  g/rev is converted inside) and no kWh/t helper is added here (the foundation `units` helpers cover J ↔ kWh and kg ↔ t);
  the two published lower size limits (70 µm for Bond's law, about 45 µm for the Morrell fine term) become `limit`
  rows that warn; tolerances cite the foundation classes TC-0 to TC-2.

## 9. Changes (only for features that modify earlier behaviour)
### ADDED Requirements
(none — new module)
### MODIFIED Requirements
(none)
### REMOVED Requirements
(none)
