# Equations catalogue

Licence CC-BY-4.0.

Items: 43
UNVERIFIED: 33

### `comminution_austin_breakage`

- Title: Austin breakage distribution matrix
- Domain: comminution
- Function: `minephys.comminution.austin_breakage`
- Equation:

$$
b_{ij} = B_j(s_i) - B_j(s_{i+1}), \quad B_j(s) = \phi\left(\frac{s}{s_{j+1}}\right)^{\gamma} + (1 - \phi)\left(\frac{s}{s_{j+1}}\right)^{\beta}
$$

- Symbols:
  - `b_{ij}`: fraction of broken class-j material entering finer class i [1]
  - `s_i`: upper size of class i [m]
  - `\phi`: weight of the first term [1]
  - `\gamma`: exponent of the first term [1]
  - `\beta`: exponent of the second term [1]
- Citation: `austin1984ballmilling`, https://search.worldcat.org/search?q=Process+Engineering+of+Size+Reduction+Ball+Milling
- Page: not read (bibliographic, 1984 edition)
- Verification: UNVERIFIED
- Notes: the attribution of the form to Austin is UNVERIFIED; the oracle is the form itself and the column sums

### `comminution_austin_selection`

- Title: Austin selection function
- Domain: comminution
- Function: `minephys.comminution.austin_selection`
- Equation:

$$
S_i = \frac{a\,(x_i/x_0)^{\alpha}}{1 + (x_i/\mu)^{\Lambda}}
$$

- Symbols:
  - `S_i`: selection of class i [1/s]
  - `a`: selection rate at the reference size [1/s]
  - `x_i`: representative class size [m]
  - `x_0`: reference size [m]
  - `\alpha`: size-ratio exponent [1]
  - `\mu`: size above which the rate falls [m]
  - `\Lambda`: steepness of the fall [1]
- Citation: `austin1984ballmilling`, https://search.worldcat.org/search?q=Process+Engineering+of+Size+Reduction+Ball+Milling
- Page: not read (bibliographic, 1984 edition)
- Verification: UNVERIFIED
- Rows: `austin_reference_size`
- Notes: the attribution of the form to Austin is UNVERIFIED; the oracle is the form itself

### `comminution_bond_ball_mill_work_index`

- Title: Bond ball-mill test work index
- Domain: comminution
- Function: `minephys.comminution.bond_ball_mill_work_index`
- Equation:

$$
W_i = \frac{1.1025 \times 44.5}{P_1^{0.23}\,G_{bp}^{0.82}\left(10/\sqrt{P_{80}} - 10/\sqrt{F_{80}}\right)}
$$

- Symbols:
  - `W_i`: ball-mill work index per metric tonne [J/kg]
  - `P_1`: closing screen size [m]
  - `G_{bp}`: grindability (net mass finer than the screen per revolution) [kg]
  - `P_{80}`: test product 80 % passing size [m]
  - `F_{80}`: test feed 80 % passing size [m]
- Citation: `mcivor2016bondgmsg`, http://www.ceecthefuture.org/wp-content/uploads/2015/12/Bond-GMSG-SME-conference.pdf
- Page: p. 10, Annex C1 "Calculations"; test sheet p. 11
- Verification: verified (2026-10-06)
- Rows: `bond_bm_constant`, `bond_bm_exponent_screen`, `bond_bm_exponent_grindability`, `bond_short_ton_to_metric`, `bond_law_coefficient`
- Notes: sizes in micrometres and grindability in g/rev inside the published formula, kWh/t converted to J/kg

### `comminution_bond_energy`

- Title: Bond's third law of comminution
- Domain: comminution
- Function: `minephys.comminution.bond_energy`
- Equation:

$$
W = 10\,W_i\left(\frac{1}{\sqrt{P_{80}}} - \frac{1}{\sqrt{F_{80}}}\right)
$$

- Symbols:
  - `W`: specific comminution energy [J/kg]
  - `W_i`: Bond work index [J/kg]
  - `P_{80}`: product 80 % passing size (micrometres inside the formula) [m]
  - `F_{80}`: feed 80 % passing size (micrometres inside the formula) [m]
- Citation: `mcivor2016bondgmsg`, http://www.ceecthefuture.org/wp-content/uploads/2015/12/Bond-GMSG-SME-conference.pdf
- Page: p. 1, "Calculations"; worked examples p. 2
- Verification: verified (2026-10-06)
- Rows: `bond_law_coefficient`, `bond_min_product_size`
- Notes: the law is homogeneous in the work index, so the result is in the unit of the index

### `comminution_bond_operating_work_index`

- Title: Bond operating work index
- Domain: comminution
- Function: `minephys.comminution.bond_operating_work_index`
- Equation:

$$
W_{io} = \frac{W}{10/\sqrt{P_{80}} - 10/\sqrt{F_{80}}}
$$

- Symbols:
  - `W_{io}`: operating work index [J/kg]
  - `W`: measured specific energy [J/kg]
  - `P_{80}`: product 80 % passing size [m]
  - `F_{80}`: feed 80 % passing size [m]
- Citation: `mcivor2016bondgmsg`, http://www.ceecthefuture.org/wp-content/uploads/2015/12/Bond-GMSG-SME-conference.pdf
- Page: p. 1, "Calculations"; worked examples pp. 1-2
- Verification: verified (2026-10-06)
- Rows: `bond_law_coefficient`, `bond_min_product_size`

### `comminution_class_masses`

- Title: Class masses from a cumulative passing curve
- Domain: comminution
- Function: `minephys.comminution.class_masses`
- Equation:

$$
m_i = P(s_i) - P(s_{i+1}) \ (i < n), \qquad m_n = P(s_n)
$$

- Symbols:
  - `m_i`: mass fraction of class i [1]
  - `P`: cumulative passing [1]
  - `s_i`: upper size of class i [m]
- Citation: `ouchterlony2005swebrec`, DOI 10.1179/037178405X44539
- Page: not read (definition)
- Verification: UNVERIFIED

### `comminution_crusher_matrix_model`

- Title: Steady-state crusher matrix model
- Domain: comminution
- Function: `minephys.comminution.crusher_matrix_model`
- Equation:

$$
\mathbf{p} = (I - C)(I - BC)^{-1}\mathbf{f}
$$

- Symbols:
  - `\mathbf{p}`: product mass of each class [kg]
  - `\mathbf{f}`: feed mass of each class [kg]
  - `C`: diagonal matrix of classification probabilities [1]
  - `B`: breakage matrix (strictly lower triangular) [1]
- Citation: `whiten1972crushing`, https://onemine.org/documents/the-simulation-of-crushing-plants-with-models-developed-using-multiple-spline-regression
- Page: not read (bibliographic)
- Verification: UNVERIFIED
- Notes: follows from the steady balance x = f + BCx, p = (I - C)x; the attribution to Whiten is UNVERIFIED

### `comminution_cumulative_passing`

- Title: Cumulative passing from class masses
- Domain: comminution
- Function: `minephys.comminution.cumulative_passing`
- Equation:

$$
P_i = \sum_{k \ge i} m_k
$$

- Symbols:
  - `P_i`: cumulative passing at the upper size of class i [1]
  - `m_k`: mass of class k [1]
- Citation: `ouchterlony2005swebrec`, DOI 10.1179/037178405X44539
- Page: not read (definition)
- Verification: UNVERIFIED

### `comminution_flotation_cell_recovery`

- Title: Recovery of perfectly mixed flotation cells in series
- Domain: comminution
- Function: `minephys.comminution.flotation_cell_recovery`
- Equation:

$$
R = R_\infty\left[1 - (1 + k\tau)^{-N}\right]
$$

- Symbols:
  - `R`: recovery of the bank [1]
  - `R_\infty`: ultimate recovery [1]
  - `k`: rate constant [1/s]
  - `\tau`: mean residence time of one cell [s]
  - `N`: number of cells in series [1]
- Citation: `wills2016`, DOI 10.1016/C2010-0-65478-2
- Page: not read (textbook form)
- Verification: UNVERIFIED
- Notes: derived in spec 005 section 7 by integrating the first-order law against an exponential residence-time distribution

### `comminution_flotation_first_order`

- Title: First-order flotation recovery
- Domain: comminution
- Function: `minephys.comminution.flotation_first_order`
- Equation:

$$
R = R_\infty\left(1 - e^{-kt}\right)
$$

- Symbols:
  - `R`: recovery [1]
  - `R_\infty`: ultimate recovery [1]
  - `k`: rate constant [1/s]
  - `t`: flotation time [s]
- Citation: `wills2016`, DOI 10.1016/C2010-0-65478-2
- Page: not read (textbook form)
- Verification: UNVERIFIED

### `comminution_klimpel_recovery`

- Title: Klimpel flotation recovery
- Domain: comminution
- Function: `minephys.comminution.klimpel_recovery`
- Equation:

$$
R = R_\infty\left[1 - \frac{1 - e^{-kt}}{kt}\right]
$$

- Symbols:
  - `R`: recovery [1]
  - `R_\infty`: ultimate recovery [1]
  - `k`: maximum rate constant [1/s]
  - `t`: flotation time [s]
- Citation: `gharai2016flotation`, DOI 10.1080/08827508.2015.1115991
- Page: not read (review transcription)
- Verification: UNVERIFIED
- Notes: derived in spec 005 section 7 as the mean of the first-order recovery over a uniform rate distribution on [0, k]

### `comminution_mine_to_mill_chain`

- Title: Mine-to-mill chain
- Domain: comminution
- Function: `minephys.comminution.mine_to_mill_chain`
- Equation:

$$
P_{crusher} = \mathrm{cumulative}(\mathrm{crusher}(\mathrm{masses}(P_{blast}))), \quad \dot{m} = \frac{P}{W(F_{80} \to P_{80})}
$$

- Symbols:
  - `P_{blast}`: cumulative passing of the blast [1]
  - `F_{80}`: crusher product 80 % passing size [m]
  - `P_{80}`: target final grind [m]
  - `W`: specific energy from F80 to P80 [J/kg]
  - `P`: installed power [W]
  - `\dot{m}`: throughput [kg/s]
- Citation: `mcivor2016bondgmsg`, http://www.ceecthefuture.org/wp-content/uploads/2015/12/Bond-GMSG-SME-conference.pdf
- Page: composition of the component functions (spec 005 FR-005-30)
- Verification: UNVERIFIED
- Notes: a composition of the equations above; its components carry their own status

### `comminution_morrell_crusher`

- Title: Morrell crushing energy
- Domain: comminution
- Function: `minephys.comminution.morrell_crusher`
- Equation:

$$
W_c = S_c K_2 M_{ic}\,4\left(x_2^{f(x_2)} - x_1^{f(x_1)}\right), \quad S_c = \min\left(55\,(x_1 x_2)^{-0.2},\ 1\right)
$$

- Symbols:
  - `W_c`: crushing energy per tonne through the crusher [J/kg]
  - `S_c`: size-dependent factor (1 for tertiary and pebble stages) [1]
  - `K_2`: 1 for a closed circuit and 1.19 for an open one [1]
  - `M_{ic}`: Morrell index Mic [J/kg]
  - `x_1`: feed 80 % passing size [m]
  - `x_2`: product 80 % passing size [m]
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: eqs. B4-B5, pp. 6-7
- Verification: verified (2026-10-06)
- Rows: `morrell_coefficient`, `morrell_f_constant`, `morrell_f_scale`, `morrell_k2_open_circuit`, `morrell_ks_crusher`, `morrell_s_exponent`

### `comminution_morrell_energy`

- Title: Morrell energy-size relation
- Domain: comminution
- Function: `minephys.comminution.morrell_energy`
- Equation:

$$
W = M_i \cdot 4\left(x_2^{f(x_2)} - x_1^{f(x_1)}\right), \quad f(x) = -\left(0.295 + \frac{x}{10^6}\right)
$$

- Symbols:
  - `W`: specific energy [J/kg]
  - `M_i`: Morrell index of the stage [J/kg]
  - `x_1`: feed 80 % passing size (micrometres inside the formula) [m]
  - `x_2`: product 80 % passing size (micrometres inside the formula) [m]
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: eq. 2, p. 2
- Verification: verified (2026-10-06)
- Rows: `morrell_coefficient`, `morrell_f_constant`, `morrell_f_scale`, `morrell_relative_error_sd`

### `comminution_morrell_hpgr`

- Title: Morrell high-pressure grinding roll energy
- Domain: comminution
- Function: `minephys.comminution.morrell_hpgr`
- Equation:

$$
W_h = S_h K_3 M_{ih}\,4\left(x_2^{f(x_2)} - x_1^{f(x_1)}\right), \quad S_h = \min\left(35\,(x_1 x_2)^{-0.2},\ 1\right)
$$

- Symbols:
  - `W_h`: HPGR energy [J/kg]
  - `S_h`: size-dependent factor [1]
  - `K_3`: 1 for a closed circuit and 1.19 for an open one [1]
  - `M_{ih}`: Morrell index Mih [J/kg]
  - `x_1`: feed 80 % passing size [m]
  - `x_2`: product 80 % passing size [m]
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: eq. B6, p. 7; section B.2.3, p. 7
- Verification: verified (2026-10-06)
- Rows: `morrell_coefficient`, `morrell_f_constant`, `morrell_f_scale`, `morrell_k3_open_circuit`, `morrell_ks_hpgr`, `morrell_s_exponent`

### `comminution_morrell_mib`

- Title: Morrell fine-grinding index from the Bond ball-mill test
- Domain: comminution
- Function: `minephys.comminution.morrell_mib`
- Equation:

$$
M_{ib} = \frac{18.18}{P_{100}^{0.295}\,G_{bp}\left(P_{80}^{f(P_{80})} - F_{80}^{f(F_{80})}\right)}
$$

- Symbols:
  - `M_{ib}`: Morrell index Mib [J/kg]
  - `P_{100}`: closing screen size [m]
  - `G_{bp}`: grindability (net mass finer than the screen per revolution) [kg]
  - `P_{80}`: test product 80 % passing size [m]
  - `F_{80}`: test feed 80 % passing size [m]
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: eq. 1, p. 2
- Verification: verified (2026-10-06)
- Rows: `morrell_mib_constant`, `morrell_mib_screen_exponent`, `morrell_f_constant`, `morrell_f_scale`
- Notes: kWh/t and g/rev inside the published formula, converted to J/kg

### `comminution_morrell_size_distribution_correction`

- Title: Morrell size-distribution correction energy
- Domain: comminution
- Function: `minephys.comminution.morrell_size_distribution_correction`
- Equation:

$$
W_s = 0.19\,M_{ia}\,4\left(x_2^{f(x_2)} - x_1^{f(x_1)}\right)
$$

- Symbols:
  - `W_s`: size-distribution correction energy [J/kg]
  - `M_{ia}`: Morrell index Mia [J/kg]
  - `x_1`: circuit feed 80 % passing size [m]
  - `x_2`: ball-mill circuit feed 80 % passing size [m]
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: section B.2.4, p. 8
- Verification: verified (2026-10-06)
- Rows: `morrell_coefficient`, `morrell_f_constant`, `morrell_f_scale`, `morrell_ws_factor`

### `comminution_morrell_tumbling_coarse`

- Title: Morrell coarse tumbling-mill energy
- Domain: comminution
- Function: `minephys.comminution.morrell_tumbling_coarse`
- Equation:

$$
W_a = K_1 M_{ia}\,4\left(750^{f(750)} - x_1^{f(x_1)}\right)
$$

- Symbols:
  - `W_a`: coarse tumbling-mill energy [J/kg]
  - `K_1`: 0.95 with a pebble crusher and 1 otherwise [1]
  - `M_{ia}`: Morrell index Mia [J/kg]
  - `x_1`: tumbling-mill feed 80 % passing size [m]
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: eqs. B2-B3, p. 6
- Verification: verified (2026-10-06)
- Rows: `morrell_coefficient`, `morrell_f_constant`, `morrell_f_scale`, `morrell_coarse_fine_boundary`, `morrell_k1_pebble_crusher`

### `comminution_morrell_tumbling_fine`

- Title: Morrell fine tumbling-mill energy
- Domain: comminution
- Function: `minephys.comminution.morrell_tumbling_fine`
- Equation:

$$
W_b = M_{ib}\,4\left(P_{80}^{f(P_{80})} - 750^{f(750)}\right)
$$

- Symbols:
  - `W_b`: fine tumbling-mill energy [J/kg]
  - `M_{ib}`: Morrell index Mib [J/kg]
  - `P_{80}`: final grind 80 % passing size [m]
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: eqs. B2-B3, p. 6; section B.1, p. 6
- Verification: verified (2026-10-06)
- Rows: `morrell_coefficient`, `morrell_f_constant`, `morrell_f_scale`, `morrell_coarse_fine_boundary`, `morrell_fine_grind_limit`

### `comminution_passing_size`

- Title: Passing size by log-log interpolation
- Domain: comminution
- Function: `minephys.comminution.passing_size`
- Equation:

$$
\ln x_p = \ln x_i + \left(\ln p - \ln P_i\right)\frac{\ln x_{i+1} - \ln x_i}{\ln P_{i+1} - \ln P_i}
$$

- Symbols:
  - `x_p`: size at the wanted passing fraction [m]
  - `p`: wanted passing fraction [1]
  - `x_i`: bracketing curve sizes [m]
  - `P_i`: cumulative passing at the bracketing sizes [1]
- Citation: `ouchterlony2005swebrec`, DOI 10.1179/037178405X44539
- Page: not read (the Swebrec closed form is the test oracle)
- Verification: UNVERIFIED

### `comminution_pbm_batch_grinding`

- Title: Batch grinding population balance
- Domain: comminution
- Function: `minephys.comminution.pbm_batch_grinding`
- Equation:

$$
\mathbf{m}(t) = e^{At}\,\mathbf{m}(0), \quad A = -\operatorname{diag}(S) + B\operatorname{diag}(S)
$$

- Symbols:
  - `\mathbf{m}`: class masses coarse to fine [kg]
  - `S`: selection (breakage rate) of each class [1/s]
  - `B`: breakage matrix (strictly lower triangular) [1]
  - `t`: grinding time [s]
- Citation: `reid1965batch`, DOI 10.1016/0009-2509(65)80093-8
- Page: not read (bibliographic)
- Verification: UNVERIFIED
- Notes: the analytical three-class solution is derived in spec 005 section 7 and is the test oracle

### `comminution_pbm_continuous_mill`

- Title: Perfectly mixed continuous mill, tanks in series
- Domain: comminution
- Function: `minephys.comminution.pbm_continuous_mill`
- Equation:

$$
\mathbf{m}_{out} = \left(I - \frac{\tau}{N}A\right)^{-N}\mathbf{m}_{in}
$$

- Symbols:
  - `\mathbf{m}`: class mass flows coarse to fine [kg/s]
  - `A`: rate matrix -diag(S) + B diag(S) [1/s]
  - `\tau`: total mean residence time [s]
  - `N`: number of equal tanks in series [1]
- Citation: `austin1984ballmilling`, https://search.worldcat.org/search?q=Process+Engineering+of+Size+Reduction+Ball+Milling
- Page: not read (bibliographic, 1984 edition)
- Verification: UNVERIFIED
- Notes: derived in spec 005 section 7 from the steady balance of one tank

### `comminution_two_product_recovery`

- Title: Two-product formula
- Domain: comminution
- Function: `minephys.comminution.two_product_recovery`
- Equation:

$$
\frac{C}{F} = \frac{f - t}{c - t}, \quad R = \frac{c\,(f - t)}{f\,(c - t)}
$$

- Symbols:
  - `C/F`: mass yield of the concentrate [1]
  - `R`: recovery of the valuable component [1]
  - `f`: feed grade [1]
  - `c`: concentrate grade [1]
  - `t`: tailings grade [1]
- Citation: `wills2016`, DOI 10.1016/C2010-0-65478-2
- Page: not read (textbook form)
- Verification: UNVERIFIED
- Notes: the grades share any one unit

### `comminution_whiten_classification`

- Title: Whiten classification function
- Domain: comminution
- Function: `minephys.comminution.whiten_classification`
- Equation:

$$
c(x) = \begin{cases} 0 & x < k_1 \\ 1 - \left(\frac{k_2 - x}{k_2 - k_1}\right)^{k_3} & k_1 \le x < k_2 \\ 1 & x \ge k_2 \end{cases}
$$

- Symbols:
  - `c`: probability that a particle is broken [1]
  - `x`: particle size [m]
  - `k_1`: size below which nothing is broken [m]
  - `k_2`: size above which everything is broken [m]
  - `k_3`: shape exponent [1]
- Citation: `whiten1972crushing`, https://onemine.org/documents/the-simulation-of-crushing-plants-with-models-developed-using-multiple-spline-regression
- Page: not read (bibliographic)
- Verification: UNVERIFIED
- Notes: the form and its attribution to Whiten are UNVERIFIED

### `environment_ap42_unpaved_emission_factor`

- Title: AP-42 unpaved industrial road emission factor
- Domain: environment
- Function: `minephys.environment.ap42_unpaved_emission_factor`
- Equation:

$$
E = k\left(\frac{s}{12}\right)^{a}\left(\frac{W}{3}\right)^{b}
$$

- Symbols:
  - `E`: size-specific emission factor [g/VKT]
  - `k`: particle size multiplier [lb/VMT]
  - `s`: surface material silt content [percent]
  - `W`: mean vehicle weight [short tons]
  - `a`: silt exponent [1]
  - `b`: weight exponent [1]
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: section 13.2.2, unpaved roads at industrial sites
- Verification: UNVERIFIED
- Rows: `ap42_industrial_k_pm25`, `ap42_industrial_a_pm25`, `ap42_industrial_b_pm25`, `ap42_silt_reference`, `ap42_weight_reference`
- Notes: coefficient rows are read from the section; the assembled form is pinned against the section worked values in the tests

### `environment_beer_lambert_transmittance`

- Title: Beer-Lambert transmittance
- Domain: environment
- Function: `minephys.environment.beer_lambert_transmittance`
- Equation:

$$
T = \exp(-\beta L)
$$

- Symbols:
  - `T`: one-way transmittance [1]
  - `\beta`: extinction coefficient [1/m]
  - `L`: path length [m]
- Citation: `bohren1983absorption`, DOI 10.1002/9783527618156
- Page: not read (bibliographic)
- Verification: UNVERIFIED

### `environment_finite_line_source_plume`

- Title: Finite line-source plume by crosswind integration
- Domain: environment
- Function: `minephys.environment.finite_line_source_plume`
- Equation:

$$
C = \frac{Q_l}{2\sqrt{2\pi}\,u\,\sigma_z}\left[\mathrm{erf}\!\left(\frac{y_2 - y}{\sqrt{2}\sigma_y}\right) - \mathrm{erf}\!\left(\frac{y_1 - y}{\sqrt{2}\sigma_y}\right)\right]\left[\exp\left(-\frac{(z-h)^2}{2\sigma_z^2}\right) + \exp\left(-\frac{(z+h)^2}{2\sigma_z^2}\right)\right]
$$

- Symbols:
  - `C`: concentration [kg/m^3]
  - `Q_l`: emission rate per unit length [kg/(s m)]
  - `y_1, y_2`: crosswind ends of the segment [m]
- Citation: `turner1970workbook`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: not read (bibliographic)
- Verification: UNVERIFIED
- Rows: `isc3_lid_uniform_ratio`

### `environment_gaussian_plume`

- Title: Gaussian point-source plume with ground reflection
- Domain: environment
- Function: `minephys.environment.gaussian_plume`
- Equation:

$$
C = \frac{Q}{2\pi u \sigma_y \sigma_z}\exp\left(-\frac{y^2}{2\sigma_y^2}\right)\left[\exp\left(-\frac{(z-h)^2}{2\sigma_z^2}\right) + \exp\left(-\frac{(z+h)^2}{2\sigma_z^2}\right)\right]
$$

- Symbols:
  - `C`: concentration [kg/m^3]
  - `Q`: emission rate [kg/s]
  - `u`: wind speed [m/s]
  - `h`: source height [m]
- Citation: `turner1970workbook`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: not read (bibliographic)
- Verification: UNVERIFIED

### `environment_lidar_dust_return`

- Title: Lidar return state through dust
- Domain: environment
- Function: `minephys.environment.lidar_dust_return`
- Equation:

$$
T = \exp\left(-\int_0^D \beta\,ds\right), \quad \mathrm{state} = \begin{cases} \mathrm{unaffected} & T \ge T_{onset} \\ \mathrm{degraded} & T_{min} \le T < T_{onset} \\ \mathrm{lost} & T < T_{min} \end{cases}
$$

- Symbols:
  - `T`: one-way transmittance [1]
  - `T_{onset}`: transmittance below which dust affects the lidar [1]
  - `T_{min}`: transmittance below which the target is lost [1]
- Citation: `phillips2017dust`, DOI 10.1002/rob.21701
- Page: abstract, J. Field Robotics 34(5)
- Verification: UNVERIFIED
- Rows: `lidar_dust_onset_transmittance`, `lidar_dust_min_transmittance_retroreflective`, `lidar_dust_min_transmittance_low_reflectivity`
- Notes: applying the published thresholds to the one-way transmittance is an UNVERIFIED interpretation

### `environment_line_source_plume`

- Title: Infinite crosswind line-source plume
- Domain: environment
- Function: `minephys.environment.line_source_plume`
- Equation:

$$
C = \frac{Q_l}{\sqrt{2\pi}\,u\,\sigma_z}\left[\exp\left(-\frac{(z-h)^2}{2\sigma_z^2}\right) + \exp\left(-\frac{(z+h)^2}{2\sigma_z^2}\right)\right]
$$

- Symbols:
  - `C`: concentration [kg/m^3]
  - `Q_l`: emission rate per unit length [kg/(s m)]
  - `u`: wind speed [m/s]
- Citation: `turner1970workbook`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: not read (bibliographic)
- Verification: UNVERIFIED

### `environment_mass_extinction_coefficient`

- Title: Mass extinction coefficient of spherical particles
- Domain: environment
- Function: `minephys.environment.mass_extinction_coefficient`
- Equation:

$$
k_m = \frac{3 Q_{ext}}{2 \rho_p D}
$$

- Symbols:
  - `k_m`: mass extinction coefficient [m^2/kg]
  - `Q_{ext}`: extinction efficiency [1]
  - `\rho_p`: particle density [kg/m^3]
  - `D`: particle diameter [m]
- Citation: `bohren1983absorption`, DOI 10.1002/9783527618156
- Page: not read (bibliographic)
- Verification: UNVERIFIED
- Rows: `extinction_efficiency_large_particle`
- Notes: the large-particle limit Q_ext = 2 is UNVERIFIED

### `environment_pasquill_sigmas`

- Title: Pasquill-Gifford dispersion coefficients
- Domain: environment
- Function: `minephys.environment.pasquill_sigmas`
- Equation:

$$
\sigma_y = 465.11628\,x\,\tan(0.017453293\,(c - d \ln x)), \qquad \sigma_z = a\,x^{b}
$$

- Symbols:
  - `\sigma_y`: lateral dispersion coefficient [m]
  - `\sigma_z`: vertical dispersion coefficient [m]
  - `x`: downwind distance [km]
  - `a`: sigma z coefficient of the distance band [1]
  - `b`: sigma z exponent of the distance band [1]
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Tables 1-1 to 1-4
- Verification: UNVERIFIED
- Rows: `isc3_sigma_y_scale`, `isc3_deg_to_rad`, `isc3_sigma_z_cap`, `isc3_urban_min_distance`
- Notes: the coefficient rows are read from the tables; the assembled form is UNVERIFIED until checked against the tabulated values

### `environment_precipitation_correction`

- Title: AP-42 wet-day correction of an annual emission factor
- Domain: environment
- Function: `minephys.environment.precipitation_correction`
- Equation:

$$
E_{ext} = E\,\frac{365 - P}{365}
$$

- Symbols:
  - `E_ext`: annual average emission factor [g/VKT]
  - `E`: dry-condition emission factor [g/VKT]
  - `P`: number of days with at least 0.254 mm of precipitation [d]
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: section 13.2.2, extrapolation to annual averages
- Verification: UNVERIFIED
- Rows: `ap42_wet_day_threshold`, `ap42_days_per_year`

### `environment_watering_control_efficiency`

- Title: Control efficiency of watering by the moisture ratio
- Domain: environment
- Function: `minephys.environment.watering_control_efficiency`
- Equation:

$$
C = \mathrm{interp}(M;\ m_i,\ c_i)
$$

- Symbols:
  - `C`: control efficiency [percent]
  - `M`: ratio of watered to uncontrolled surface moisture [1]
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: section 13.2.2, control efficiency versus moisture ratio
- Verification: UNVERIFIED
- Rows: `ap42_watering_m_1`, `ap42_watering_m_2`, `ap42_watering_m_3`, `ap42_watering_m_4`, `ap42_watering_ce_1`, `ap42_watering_ce_2`, `ap42_watering_ce_3`, `ap42_watering_ce_4`
- Notes: the interpolation between the tabulated points is a spec 006 choice

### `planning_block_economic_value`

- Title: Block economic value with the process-or-waste destination
- Domain: planning
- Function: `minephys.planning.block_economic_value`
- Equation:

$$
v = \max\big(T\,[\,g\,y\,(p - s_r) - c_p\,],\ 0\big) - T\,c_m
$$

- Symbols:
  - `v`: economic value of the block [currency]
  - `T`: block tonnage [kg]
  - `g`: block grade (mass fraction) [1]
  - `y`: metallurgical recovery [1]
  - `p`: metal price [currency/kg]
  - `s_r`: selling cost per kg of metal [currency/kg]
  - `c_p`: processing cost per kg of ore [currency/kg]
  - `c_m`: mining cost per kg of rock [currency/kg]
- Citation: `lane1988economic`, https://matdisc.unitech.ac.pg/Record/1665
- Page: not read (bibliographic); derived form
- Verification: UNVERIFIED
- Notes: the block is sent to the plant exactly when its processing margin is positive; the form is derived in spec 007 and checked by hand calculation

### `planning_breakeven_cutoff_grade`

- Title: Break-even cut-off grade
- Domain: planning
- Function: `minephys.planning.breakeven_cutoff_grade`
- Equation:

$$
g_{be} = \frac{c_p}{y\,(p - s_r)}
$$

- Symbols:
  - `g_{be}`: break-even grade [1]
  - `c_p`: processing cost per kg of ore [currency/kg]
  - `y`: metallurgical recovery [1]
  - `p`: metal price [currency/kg]
  - `s_r`: selling cost per kg of metal [currency/kg]
- Citation: `lane1988economic`, https://matdisc.unitech.ac.pg/Record/1665
- Page: not read (bibliographic); derived form
- Verification: UNVERIFIED
- Notes: the grade at which the processing margin of the block vanishes (spec 007 FR-007-02)

### `planning_closure_mincut_reduction`

- Title: Reduction of the maximum closure to a minimum s-t cut
- Domain: planning
- Function: `minephys.planning.ultimate_pit_mincut`
- Equation:

$$
c(s, i) = v_i \ (v_i > 0), \quad c(i, t) = -v_i \ (v_i < 0), \quad c(i, j) = \infty \ ((i, j) \in A), \quad C^\ast = \{\, i : i \text{ reachable from } s \text{ in the residual network} \,\}
$$

- Symbols:
  - `c`: arc capacity of the s-t network [currency]
  - `s`: source node [1]
  - `t`: sink node [1]
  - `C^\ast`: smallest maximum-value closure [1]
- Citation: `picard1976closure`, DOI 10.1287/mnsc.22.11.1268
- Page: not read (the abstract was read); the reduction is re-derived in spec 007
- Verification: UNVERIFIED
- Notes: the minimum cut with the smallest source side gives the smallest optimal closure

### `planning_lane_cutoff_grades`

- Title: Lane limiting, balancing and optimum cut-off grades
- Domain: planning
- Function: `minephys.planning.lane_cutoff_grades`
- Equation:

$$
V(g) = (s - r)\,q(g) - h\,x(g) - m - (f + F)\max\!\left(\tfrac{1}{M},\ \tfrac{x(g)}{C},\ \tfrac{q(g)}{R}\right), \quad g_m = \frac{h}{(s - r)\,y}, \quad g_c = \frac{h + (f + F)/C}{(s - r)\,y}, \quad g_r = \frac{h}{\big(s - r - (f + F)/R\big)\,y}
$$

- Symbols:
  - `s`: metal price [currency/kg]
  - `r`: selling cost per kg of metal [currency/kg]
  - `y`: metallurgical recovery [1]
  - `h`: processing cost per kg of ore [currency/kg]
  - `m`: mining cost per kg of material [currency/kg]
  - `f`: fixed cost per unit time [currency/s]
  - `F`: opportunity cost per unit time [currency/s]
  - `M, C, R`: mine, plant and market capacities [kg/s]
  - `x(g), q(g)`: ore fraction and recovered metal per unit of material [1]
- Citation: `lane1964choosing`, https://www.scirp.org/reference/referencespapers?referenceid=1929843
- Page: not read (bibliographic); derived forms
- Verification: UNVERIFIED
- Notes: derived from the controlling-capacity rule read on cetin2013gridsearch pp. 660 and 663; the brute-force grid is the test oracle

### `planning_nested_pits`

- Title: Nested pits over revenue factors
- Domain: planning
- Function: `minephys.planning.nested_pits`
- Equation:

$$
v_i(\lambda) = \max\big(T_i\,[\,\lambda\,g_i\,y\,(p - s_r) - c_p\,],\ 0\big) - T_i\,c_m
$$

- Symbols:
  - `\lambda`: revenue factor [1]
  - `T_i`: tonnage of block i [kg]
  - `g_i`: grade of block i [1]
- Citation: `hochbaum2008pseudoflow`, DOI 10.1287/opre.1080.0524
- Page: not read (abstract only); the parametric form is derived in spec 007
- Verification: UNVERIFIED
- Notes: the pits are solved one revenue factor at a time; the parametric pseudoflow algorithm is not implemented

### `planning_npv`

- Title: Net present value of a cash-flow series
- Domain: planning
- Function: `minephys.planning.npv`
- Equation:

$$
NPV = \sum_{t=1}^{T} \frac{CF_t}{(1 + r)^t}
$$

- Symbols:
  - `CF_t`: cash flow of period t [currency]
  - `r`: discount rate per period [1]
  - `T`: number of periods [1]
- Citation: `lane1988economic`, https://matdisc.unitech.ac.pg/Record/1665
- Page: not read (bibliographic); definition
- Verification: UNVERIFIED
- Notes: end-of-period discounting; start-of-period is available

### `planning_schedule_npv`

- Title: Schedule NPV from per-period aggregation of block values
- Domain: planning
- Function: `minephys.planning.schedule_npv`
- Equation:

$$
CF_t = \sum_{i:\ \tau_i = t} v_i, \qquad NPV = \sum_{t} \frac{CF_t}{(1 + r)^{t+1}}
$$

- Symbols:
  - `\tau_i`: period in which block i is mined [1]
  - `v_i`: value of block i [currency]
- Citation: `lane1988economic`, https://matdisc.unitech.ac.pg/Record/1665
- Page: not read (bibliographic); definition
- Verification: UNVERIFIED
- Notes: a check and an evaluation, not an optimiser (spec 007 section 7)

### `planning_strip_ratio`

- Title: Strip ratio of a pit or pushback
- Domain: planning
- Function: `minephys.planning.strip_ratio`
- Equation:

$$
SR = \frac{\sum_{i \in P,\ \neg ore} T_i}{\sum_{i \in P,\ ore} T_i}
$$

- Symbols:
  - `SR`: strip ratio [1]
  - `P`: selected blocks [1]
  - `T_i`: tonnage of block i [kg]
- Citation: `lane1988economic`, https://matdisc.unitech.ac.pg/Record/1665
- Page: not read (bibliographic); definition
- Verification: UNVERIFIED
- Notes: waste tonnage over ore tonnage of the selected blocks

### `planning_ultimate_pit_closure`

- Title: Ultimate pit as a maximum-value closure of the block precedence graph
- Domain: planning
- Function: `minephys.planning.ultimate_pit_mincut`
- Equation:

$$
\max_{C \subseteq V} \sum_{i \in C} v_i \quad \text{s.t.} \quad i \in C,\ (i, j) \in A \Rightarrow j \in C
$$

- Symbols:
  - `v_i`: economic value of block i [currency]
  - `C`: closure (the set of mined blocks) [1]
  - `A`: precedence arcs (mining block i requires block j) [1]
- Citation: `lerchs1965optimum`, https://www.researchgate.net/publication/280082017_Pseudoflow_New_Life_for_Lerchs-Grossmann_Pit_Optimisation
- Page: not read (bibliographic)
- Verification: UNVERIFIED
- Notes: the closure definition is read on picard1976closure (abstract); exhaustive enumeration is the test oracle
