# Theory

> The science behind each planned `minephys` module — the models, their governing relations, their primary sources and
> the limits of their validity — as a skeleton that the build phase fills with one method page per model. · Part of:
> [docs home](../README.md) · Related: [reference](../reference/README.md) ·
> [methods](../methods/README.md) · [data contract](../data-contract/README.md)

## What and why

Each `minephys` model is implemented from its primary source and tested against a worked example from that source.
This page fixes, before any code exists, *which* relations each module implements and *where* they come from. Where a
transcription has not yet been checked against the primary text it is marked **UNVERIFIED — pinned at
specification**; such a form is a target for the specification, not a claim.

**Status: planned.** No model is implemented. Symbols are in SI units unless the source's own units are stated.

## Haulage — `minephys.haulage`

| Model | Relation | Source | Notes |
|---|---|---|---|
| Total resistance | $TR = RR + GR$, with $GR = 100\sin\theta \approx 100\tan\theta$ (percent of gross vehicle weight) | [1] | $RR$ rolling resistance (%); $\theta$ road grade angle |
| Required tractive force | $F = m_{\text{GVW}}\,g\,TR/100 + m_{\text{eff}}\,\dot v + \tfrac12\rho_a C_D A v^2$ | [1] | $m$ in kg, $v$ in m/s, $\rho_a$ air density (kg/m³), $C_D A$ drag area (m²) |
| Rimpull- and retarder-limited speed | steady speed solves $F_{\text{rim}}(v) = F(v)$; power-limited $v \approx \eta P / (m g\,TR/100)$; downhill $P_{\text{ret}} = m g\,\frac{GR-RR}{100}\,v \le P_{\text{ret,max}}$ | [1] | generic truck parameters from academic sources; no proprietary OEM charts |
| Cycle time and loading passes | $T_c = \sum$ (spot, load, haul, dump, return, queue); $n_p = \lceil M / (V_b k_f \rho_{\text{loose}}) \rceil$, $\rho_{\text{loose}} = \rho_{\text{bank}}/(1+s_w)$ | — | $V_b$ heaped bucket volume (m³), $k_f$ fill factor, $s_w$ swell |
| Energy and CO₂ | $E = \int F v\,dt / \eta$; lifting 1 t by 100 m needs $1000 \times 9.81 \times 100\ \text{J} \approx 0.273$ kWh at the wheels | arithmetic | diesel CO₂ factor **UNVERIFIED — pinned at specification** [2] |
| Trolley assist and battery-electric trucks | segment energy with electric drive, regeneration on downgrades | [3][4] | one trolley model of a copper mine: +44 % uphill speed, −16 % travel time, 85 % fuel saving per cycle [3] |
| Match factor | $MF = N_T t_L / (N_L T_c^{\ast})$ | [5] | heterogeneous-fleet extension in [5] |
| Open queue M/M/c | Erlang C: $W_q = C(c,a)/(c\mu-\lambda)$, $a = \lambda/\mu$, $\rho = \lambda/(c\mu) < 1$ | [6] | loader bank with Poisson arrivals |
| Finite-source queue | one shovel, $N$ trucks: $\pi_0 = \big[\sum_{n=0}^{N} \tfrac{N!}{(N-n)!}(\lambda/\mu)^n\big]^{-1}$, throughput $X = \mu(1-\pi_0)$ | [7] | transcription **UNVERIFIED — pinned at specification** |
| Mean value analysis | $W_k(n) = (1 + L_k(n-1))/\mu_k$, $X(n) = n / \sum_k v_k W_k(n)$, $L_k(n) = v_k X(n) W_k(n)$ | [8] | closed product-form networks; haul roads as delay stations |

## Blasting — `minephys.blasting`

| Model | Relation | Source | Notes |
|---|---|---|---|
| Kuznetsov mean size | $x_{50} = A\,K^{-0.8}\,Q^{1/6}\,(115/RWS)^{19/30}$ (cm) | [9] | $K$ powder factor (kg/m³), $Q$ charge per hole (kg), $RWS$ relative weight strength (ANFO = 100), $A$ rock factor; exponents **UNVERIFIED — pinned at specification** |
| Rosin–Rammler (Kuz-Ram) | $R(x) = \exp[-\ln 2\,(x/x_{50})^n]$ | [9] | uniformity index $n$ (Cunningham) and rock-factor constant **UNVERIFIED — pinned at specification** [10] |
| Swebrec / KCO | $P(x) = \big\{1 + [\ln(x_{\max}/x)/\ln(x_{\max}/x_{50})]^b\big\}^{-1}$, $0 < x \le x_{\max}$ | [11][12] | better fines than Rosin–Rammler; links blasting and crushing |
| Peak particle velocity | $PPV = K_s (D/\sqrt{W})^{-\beta}$ | [13][14] | $D$ distance, $W$ maximum charge per delay; $K_s$, $\beta$ fitted per site; US limits are in [14] |
| Flyrock | $m\dot{\mathbf v} = -mg\hat{\mathbf z} - \tfrac12\rho_a C_D A\,|\mathbf v|\,\mathbf v$; drag-free bound $R = v_0^2 \sin 2\theta_0 / g$ | [15] | ballistic flight from the launch velocity |

## Geotechnics — `minephys.geotech`

| Model | Relation | Source | Notes |
|---|---|---|---|
| Generalised Hoek–Brown | $\sigma_1 = \sigma_3 + \sigma_{ci}(m_b\sigma_3/\sigma_{ci} + s)^a$, $m_b = m_i e^{(GSI-100)/(28-14D)}$, $s = e^{(GSI-100)/(9-3D)}$, $a = \tfrac12 + \tfrac16(e^{-GSI/15} - e^{-20/3})$ | [16][17] | $D$ disturbance factor; open-pit $D$ guidance **UNVERIFIED — pinned at specification** |
| Limit equilibrium | Bishop simplified (moment equilibrium, circular surfaces), Spencer (force and moment equilibrium, parallel interslice forces) | [18][19][20] | Bishop transcription **UNVERIFIED — pinned at specification**; Monte-Carlo probability of failure over inputs |
| Inverse velocity | for Voight's $\ddot\Omega = A\dot\Omega^{\alpha}$ with $\alpha \approx 2$: $1/v = A(t_f - t)$, so $t_f$ is the intercept of a line fit | [21][22] | noise amplification in $1/v$; filtering trades lag for noise [23] |
| Bayesian time to failure | posterior of $t_f$ from the inverse-velocity line | — | formulation fixed in the specification |
| Slope-radar line-of-sight model | displacement projected on the radar line of sight plus phase noise | [24] | analytical model of ground-based SAR interferometry, not a sensor simulation |

## Bulk handling — `minephys.bulk`

| Model | Relation | Source | Notes |
|---|---|---|---|
| Beverloo discharge | $Q = C\,\rho_b\sqrt{g}\,(D_o - k\,d)^{5/2}$ | [25][26] | exponent 5/2 and $C \approx 0.56$ reproduced by a Hertz–Mindlin DEM [26]; textbook $C$, $k$ ranges **UNVERIFIED — pinned at specification** |
| Repose geometry | cone of base radius $r$ at repose angle $\varphi$: $V = \tfrac{\pi}{3} r^3 \tan\varphi$ | arithmetic | stockpile volumes; the repose angle is a calibration target [27] |
| Conveyor power (CEMA) | effective tension $T_e$ from idler, flexure, lift and accessory terms; $P = T_e V$ | [28] | standard is paywalled; only the public form is implemented; transcription **UNVERIFIED — pinned at specification** |
| Bed blending (Gy) | idealised $\sigma^2_{\text{out}} \approx \sigma^2_{\text{in}}/N$ for $N$ layers | [29] | real inputs are autocorrelated; variance reduction from variogram-based simulation |

## Comminution — `minephys.comminution`

| Model | Relation | Source | Notes |
|---|---|---|---|
| Bond | $W = 10\,W_i\,(1/\sqrt{P_{80}} - 1/\sqrt{F_{80}})$ (kWh/t, sizes in µm) | [30] | $W_i$ Bond work index |
| Morrell | whole-circuit energy–size relation from the SMC test | [31] | constants **UNVERIFIED — pinned at specification** |
| Population balance | $dm_i/dt = -S_i m_i + \sum_{j<i} b_{ij} S_j m_j$ | [32] | selection function $S_i$, breakage distribution $b_{ij}$ |
| Flotation kinetics | first order $R = R_\infty(1 - e^{-kt})$; Klimpel $R = R_\infty[1 - (1 - e^{-kt})/(kt)]$ | [33] | transcription **UNVERIFIED — pinned at specification** |
| Two-product recovery | $R = c(f-t) / [f(c-t)]$ | [34] | $f, c, t$ feed, concentrate and tail grades |

## Environment — `minephys.environment`

| Model | Relation | Source | Notes |
|---|---|---|---|
| Unpaved-road dust (AP-42 §13.2.2) | $E = k(s/12)^a(W/3)^b$ (lb per vehicle-mile), $E_{\text{ext}} = E\,(365-P)/365$ | [35] | constants and applicability ranges **UNVERIFIED — pinned at specification**; large haul trucks sit at or beyond the fitted weight range |
| Gaussian plume | $C = \dfrac{Q}{2\pi u\sigma_y\sigma_z} e^{-y^2/2\sigma_y^2}\big[e^{-(z-H)^2/2\sigma_z^2} + e^{-(z+H)^2/2\sigma_z^2}\big]$ | [36] | Pasquill classes A–F; $\sigma$ coefficients **UNVERIFIED — pinned at specification**; a road is a line source |
| Dust attenuation for lidar (Beer–Lambert) | two-way transmittance $T^2 = \exp(-2\int\sigma_{\text{ext}}\,ds)$ per return | [37] | calibrated to a mining dust study: dust starts to affect measurements below 71–74 % transmittance, and retroreflective targets are ranged down to 2 % [37] |

## Planning — `minephys.planning`

| Model | Relation | Source | Notes |
|---|---|---|---|
| Ultimate pit | $\max \sum_i v_i x_i$ s.t. $x_i \le x_j$ for each precedence arc, $x \in \{0,1\}$; solved as a minimum cut | [38][39] | small instances only (the library is not an optimiser for full block models) |
| Cut-off grade (Lane) | mine-limited $g_m = h / ((s - r)y)$ plus plant- and market-limited cut-offs | [40] | transcription **UNVERIFIED — pinned at specification** |
| Test instances | MineLib problem formats and reference values | [41] | share-alike licence of the data; used only as optional tests |

## Knowledge — `minephys.knowledge`

Not a model: the loader and validator of the cited parameter tables and the bibliography that every module reads. The
row format is described in [reference](../reference/README.md#knowledge-tables).

## Assumptions and limits

- Every model is classical and reference-grade; empirical regressions (Kuz-Ram, PPV site laws, AP-42) are valid only in
  the ranges of their data.
- Paywalled standards are cited and their public forms implemented; their text is not reproduced.
- Results are educational, not design values.

## References

1. Soofastaei, A. et al. (2016), haul-truck energy and total resistance, IJMST 26(2). https://doi.org/10.1016/j.ijmst.2015.12.015
2. US EPA, "GHG Emission Factors Hub" (2025). https://www.epa.gov/system/files/documents/2025-01/ghg-emission-factors-hub-2025.pdf
3. Valenzuela Cruzat, J. and Valenzuela, M. A. (2018), trolley assist for mining trucks, IEEE TIA 54(4). https://doi.org/10.1109/tia.2018.2823261
4. Lindgren, L. et al. (2022), battery-electric haul trucks with electric roads, Energies 15(13). https://doi.org/10.3390/en15134871
5. Burt, C. N. and Caccetta, L. (2007), match factor for heterogeneous fleets, IJMRE 21(4). https://doi.org/10.1080/17480930701388606
6. "M/M/c queue" — Erlang C and waiting times. https://en.wikipedia.org/wiki/M/M/c_queue
7. Carmichael, D. G. (1986), shovel–truck queues, Construction Management and Economics 4(2). https://doi.org/10.1080/01446198600000013
8. "Mean value analysis" — closed-network recursion. https://en.wikipedia.org/wiki/Mean_value_analysis
9. Kuznetsov, V. M. (1973), mean fragment size from blasting, Soviet Mining Science 9. https://doi.org/10.1007/BF02506177
10. Cunningham, C. V. B. (2005), "The Kuz-Ram fragmentation model — 20 years on" (bibliographic). https://www.scirp.org/reference/referencespapers?referenceid=4120306
11. Ouchterlony, F. (2005), the Swebrec function, Mining Technology 114(1). https://doi.org/10.1179/037178405X44539
12. Mutinda, E. K. et al. (2021), KCO model, JSAIMM 121(3). https://doi.org/10.17159/2411-9717/1401/2021
13. Siskind, D. E. et al. (1980), USBM RI 8507. https://www.osti.gov/biblio/6777883
14. 30 CFR § 816.67. https://www.law.cornell.edu/cfr/text/30/816.67
15. Szendrei, T. and Tose, S. (2023), flyrock models, JSAIMM 122(12). https://doi.org/10.17159/2411-9717/1873/2022
16. Hoek, E. and Brown, E. T. (2019), Hoek–Brown criterion and GSI — 2018 edition, JRMGE 11(3). https://doi.org/10.1016/j.jrmge.2018.08.001
17. Itasca, Hoek–Brown model documentation. https://docs.itascacg.com/itasca900/common/models/hoek/doc/modelhoek.html
18. Bishop, A. W. (1955), the slip circle, Géotechnique 5(1). https://doi.org/10.1680/geot.1955.5.1.7
19. Spencer, E. (1967), parallel inter-slice forces, Géotechnique 17(1). https://doi.org/10.1680/geot.1967.17.1.11
20. GeoEngineer, "Slope stability: the Spencer method of slices". https://www.geoengineer.org/education/slope-stability/slope-stability-the-spencer-method-of-slices
21. Voight, B. (1989), rate-dependent material failure, Science 243. https://doi.org/10.1126/science.243.4888.200
22. Rose, N. D. and Hungr, O. (2007), inverse-velocity forecasting in open pits, IJRMMS 44(2). https://doi.org/10.1016/j.ijrmms.2006.07.014
23. Dick, G. J. et al. (2015), time-of-failure analysis with slope-stability radar, Can. Geotech. J. 52(4). https://doi.org/10.1139/cgj-2014-0028
24. Monserrat, O., Crosetto, M. and Luzi, G. (2014), "A review of ground-based SAR interferometry for deformation measurement", ISPRS J. 93. https://doi.org/10.1016/j.isprsjprs.2014.04.001
25. Beverloo, W. A., Leniger, H. A. and van de Velde, J. (1961), Chemical Engineering Science. https://doi.org/10.1016/0009-2509(61)85030-6
26. DEM validation of Beverloo's law (Hertz–Mindlin, C = 0.56, exponent 5/2). https://arxiv.org/html/2512.03698v1
27. Coetzee, C. J. (2017), calibration of the discrete element method, Powder Technology 310. https://doi.org/10.1016/j.powtec.2017.01.015
28. CEMA, "Belt Conveyors for Bulk Materials", 7th ed. (errata summary). https://www.cemanet.org/wp-content/uploads/2015/04/BBK-7th-Edition-Errata-Summary-Pages-as-of-Feb1-2015-SEC.pdf
29. Gy, P. (1981), bed blending from the theory of sampling, Int. J. Miner. Process. 8. https://doi.org/10.1016/0301-7516(81)90013-2
30. Bond, F. C. (1952), "The third theory of comminution", Trans. AIME 193 (bibliographic). https://www.scirp.org/reference/referencespapers?referenceid=3600515
31. Morrell, S. (2004), an alternative energy–size relationship, Int. J. Miner. Process. 74. https://doi.org/10.1016/j.minpro.2003.10.002
32. Austin, L. G. (1971), grinding as a rate process, Powder Technology 5. https://doi.org/10.1016/0032-5910(71)80064-5
33. Gharai, M. and Venugopal, R. (2016), flotation modelling overview. https://doi.org/10.1080/08827508.2015.1115991
34. Wills' Mineral Processing Technology, 8th ed. (2016). https://doi.org/10.1016/C2010-0-65478-2
35. US EPA, AP-42 §13.2.2 "Unpaved Roads" (November 2006). https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
36. "Atmospheric dispersion modeling" — Gaussian plume with ground reflection. https://en.wikipedia.org/wiki/Atmospheric_dispersion_modeling
37. Phillips, T. G., Guenther, N. and McAree, P. R. (2017), "When the dust settles: the four behaviors of LiDAR in the presence of fine airborne particulates", Journal of Field Robotics 34(5). https://doi.org/10.1002/rob.21701
38. Lerchs and Grossmann (1965), maximum closure for open-pit design (context). https://www.researchgate.net/publication/280082017_Pseudoflow_New_Life_for_Lerchs-Grossmann_Pit_Optimisation
39. Hochbaum, D. S. (2008), the pseudoflow algorithm, Operations Research 56(4). https://doi.org/10.1287/opre.1080.0524
40. Lane, K. F. (1964), "Choosing the optimum cut-off grade" (bibliographic). https://www.scirp.org/reference/referencespapers?referenceid=1929843
41. Espinoza, D. et al. (2013), MineLib, Annals of Operations Research 206(1). https://doi.org/10.1007/s10479-012-1258-3
