"""Size distributions, the crusher matrix model and the mine-to-mill chain (spec 005 FR-005-24 to FR-005-31).

A cumulative passing curve is given at upper class sizes; classes run coarse to fine and the last class holds
everything below
the grid. Interpolation between curve points is linear in (log x, log P), and linear in (log x, P) where a point has
P = 0.
"""

from __future__ import annotations

from typing import Any, NamedTuple

import numpy as np

from .._errors import InputError
from .._validate import check_option, check_rank, finalize
from ._common import FloatArray, non_negative, positive, scalar, unit_interval, vector
from ._energy import bond_energy, morrell_tumbling_coarse, morrell_tumbling_fine
from ._pbm import check_breakage

__all__ = [
    "ChainResult",
    "class_masses",
    "crusher_matrix_model",
    "cumulative_passing",
    "mine_to_mill_chain",
    "passing_size",
    "whiten_classification",
]

MAX_POINTS = 10_000
MAX_CRUSHER_CLASSES = 2_000
ENERGY_MODELS = ("bond", "morrell")


class ChainResult(NamedTuple):
    """Result of the mine-to-mill chain: crusher product curve, F80, fines fraction, specific energy and throughput."""

    product_passing: FloatArray
    f80: Any
    fines_fraction: Any
    specific_energy: Any
    throughput: Any


def _curve(
    sizes: Any,
    passing: Any,
    *,
    decreasing: bool = False,
    names: tuple[str, str] = ("sizes", "passing"),
    max_size: int = MAX_POINTS,
) -> tuple[FloatArray, FloatArray]:
    """Validated (sizes, passing) of a cumulative curve, returned coarse to fine."""
    sn, pn = names
    s = vector(sizes, sn, min_size=2, max_size=max_size)
    if np.any(s <= 0):
        raise InputError(f"argument '{sn}' must be positive", argument=sn)
    steps = np.diff(s)
    if decreasing:
        if np.any(steps >= 0):
            raise InputError(f"argument '{sn}' must be strictly decreasing (coarse to fine)", argument=sn)
    elif not (np.all(steps < 0) or np.all(steps > 0)):
        raise InputError(f"argument '{sn}' must be strictly monotone", argument=sn)
    p = unit_interval(passing, pn)
    check_rank(p, pn, 1)
    if p.size != s.size:
        raise InputError(f"arguments {sn} and {pn} differ in length: {s.size} and {p.size}", argument=pn)
    if s[0] < s[-1]:
        s, p = s[::-1], p[::-1]
    if np.any(np.diff(p) > 0):
        raise InputError(f"argument '{pn}' must not increase towards finer sizes", argument=pn)
    return s, p


def _interpolate_size(s: FloatArray, p: FloatArray, target: float) -> float:
    """Size at which the curve (coarse to fine) equals `target`: exact at grid points, (log x, log P) between them."""
    hit = np.flatnonzero(p == target)
    if hit.size:
        return float(s[hit[0]])
    i = int(np.argmax((p[:-1] >= target) & (target >= p[1:])))
    lx0, lx1 = np.log(s[i]), np.log(s[i + 1])
    if p[i + 1] > 0:
        lp0, lp1, lt = np.log(p[i]), np.log(p[i + 1]), np.log(target)
    else:  # the finer point has P = 0: interpolate P itself against log x
        lp0, lp1, lt = p[i], p[i + 1], target
    return float(np.exp(lx0 + (lt - lp0) * (lx1 - lx0) / (lp1 - lp0)))


def passing_size(sizes: Any, passing: Any, fraction: Any = 4 / 5) -> Any:
    """Size at which a cumulative passing curve equals a given fraction.

    Parameters
    ----------
    sizes : array [m]
        Curve sizes (2 to 10,000, positive, strictly monotone in either order).
    passing : array [fraction]
        Cumulative passing at those sizes, in [0, 1], non-decreasing with size.
    fraction : float [fraction]
        Passing fraction wanted (default 0.8, the P80), within the range spanned by the curve.

    Returns
    -------
    float [m]
        The size (`numpy.float64`); a grid size exactly when `fraction` equals its passing value.

    Equation
    --------
    Linear interpolation in (ln x, ln P) between the two bracketing points (in (ln x, P) where a point has P = 0).

    Source
    ------
    ouchterlony2005swebrec (closed-form Swebrec x80 used as the test oracle); interpolation rule from spec 005
    FR-005-24 (section 7).

    Validity
    --------
    Log-log interpolation error on a 400-point log-spaced grid from 10 micrometres is at most 4.3e-4 (spec 005 plan).

    Knowledge rows
    --------------
    none
    """
    s, p = _curve(sizes, passing)
    f = scalar(fraction, "fraction")
    if not p[-1] <= f <= p[0]:
        raise InputError(f"argument 'fraction' must lie in [{p[-1]!r}, {p[0]!r}], got {f!r}", argument="fraction")
    return np.float64(_interpolate_size(s, p, f))


def class_masses(sizes: Any, passing: Any) -> FloatArray:
    """Class mass fractions from a cumulative passing curve on upper class sizes.

    Parameters
    ----------
    sizes : array [m]
        Upper class sizes s_1 > ... > s_n (2 to 10,000, positive, strictly monotone); the result follows the input
        order.
    passing : array [fraction]
        Cumulative passing P(s_i) in [0, 1], non-decreasing with size.

    Returns
    -------
    array [fraction]
        Class masses, aligned with `sizes`.

    Equation
    --------
    m_i = P(s_i) - P(s_(i+1)) for i < n, m_n = P(s_n).

    Source
    ------
    ouchterlony2005swebrec (Swebrec curve used as the test oracle); the conversion is the definition in spec 005
    FR-005-25 (section 7).

    Validity
    --------
    The last class holds everything finer than the last size.

    Knowledge rows
    --------------
    none
    """
    raw_sizes = vector(sizes, "sizes", min_size=2, max_size=MAX_POINTS)
    ascending = bool(raw_sizes[0] < raw_sizes[-1])
    _, p = _curve(sizes, passing)
    m = np.append(p[:-1] - p[1:], p[-1])
    return np.asarray(m[::-1] if ascending else m, dtype=np.float64)


def cumulative_passing(masses: Any) -> FloatArray:
    """Cumulative passing from class masses (the exact inverse of `class_masses`).

    Parameters
    ----------
    masses : array [fraction or kg]
        Class masses, coarse to fine (2 to 10,000, >= 0).

    Returns
    -------
    array [same unit as masses]
        P_i, the mass of class i and of every finer class.

    Equation
    --------
    P_i = sum over k >= i of m_k.

    Source
    ------
    ouchterlony2005swebrec (Swebrec curve used as the test oracle); the sum is the definition in spec 005 FR-005-25
    (section 7).

    Validity
    --------
    None beyond the point limits.

    Knowledge rows
    --------------
    none
    """
    m = non_negative(masses, "masses")
    check_rank(m, "masses", 1)
    if not 2 <= m.size <= MAX_POINTS:
        raise InputError(f"argument 'masses' needs 2 to {MAX_POINTS:,} elements, got {m.size}", argument="masses")
    return np.asarray(np.cumsum(m[::-1])[::-1], dtype=np.float64)


def crusher_matrix_model(feed: Any, classification: Any, breakage: Any) -> FloatArray:
    """Steady-state product of a crusher from the classification and breakage matrices.

    Parameters
    ----------
    feed : array [kg or kg/s]
        Feed mass of each class, coarse to fine (>= 0).
    classification : array [probability]
        Probability c_i, in [0, 1], that a class-i particle is broken; the finest class must be 0.
    breakage : array [fraction]
        Strictly lower-triangular matrix b_ij; each column with c_j > 0 sums to 1 within 1e-12.

    Returns
    -------
    array [same unit as feed]
        Product mass of each class; the total mass is conserved.

    Equation
    --------
    p = (I - C)(I - B C)^(-1) f with C = diag(c), solved as x = f + B C x, p = (I - C) x.

    Source
    ------
    whiten1972crushing (bibliographic, not read; the attribution is UNVERIFIED: the oracle is the steady balance
    itself, spec 005 section 7).

    Validity
    --------
    Up to 2,000 classes; I - B C is unit lower triangular and always invertible.

    Knowledge rows
    --------------
    none
    """
    f = non_negative(feed, "feed")
    c = unit_interval(classification, "classification")
    b = non_negative(breakage, "breakage")
    check_rank(f, "feed", 1)
    check_rank(c, "classification", 1)
    check_rank(b, "breakage", 2)
    n = f.size
    if not 1 <= n <= MAX_CRUSHER_CLASSES:
        raise InputError(f"argument 'feed' needs 1 to {MAX_CRUSHER_CLASSES:,} classes, got {n}", argument="feed")
    if c.size != n:
        raise InputError(
            f"arguments feed and classification differ in length: {n} and {c.size}", argument="classification"
        )
    if c[-1] != 0:
        raise InputError("argument 'classification': the finest class cannot be broken", argument="classification")
    check_breakage(b, n, c)
    x = np.zeros(n)
    for i in range(n):
        x[i] = f[i] + b[i, :i] @ (c[:i] * x[:i])
    return np.asarray((1 - c) * x, dtype=np.float64)


def whiten_classification(sizes: Any, k1: Any, k2: Any, k3: Any) -> Any:
    """Whiten classification function of a crusher.

    Parameters
    ----------
    sizes : float or array [m]
        Particle sizes (> 0).
    k1 : float [m]
        Size below which nothing is broken (>= 0, < k2).
    k2 : float [m]
        Size above which everything is broken (> k1).
    k3 : float [1]
        Shape exponent (> 0).

    Returns
    -------
    float or array [probability]
        Probability c(x) that a particle of size x is broken.

    Equation
    --------
    c = 0 for x < k1; c = 1 - ((k2 - x)/(k2 - k1))^k3 for k1 <= x < k2; c = 1 for x >= k2.

    Source
    ------
    whiten1972crushing (bibliographic, not read; the form and its attribution are UNVERIFIED; spec 005 section 7).

    Validity
    --------
    Evaluated as written; at the midpoint with k3 = 2 it gives 0.75.

    Knowledge rows
    --------------
    none
    """
    x = positive(sizes, "sizes")
    low = scalar(k1, "k1", lo=0)
    high = scalar(k2, "k2", lo=0, lo_open=True)
    shape = scalar(k3, "k3", lo=0, lo_open=True)
    if not low < high:
        raise InputError(f"argument 'k1' must be smaller than 'k2', got {low!r} and {high!r}", argument="k1")
    inside = 1 - (np.clip(high - x, 0, high - low) / (high - low)) ** shape
    out = np.where(x < low, 0, np.where(x >= high, 1, inside))
    return finalize(out, x)


def _passing_at(s: FloatArray, p: FloatArray, size: float) -> float:
    """Cumulative passing at `size` (coarse-to-fine curve): exact at grid sizes, (log x, log P) between them."""
    hit = np.flatnonzero(s == size)
    if hit.size:
        return float(p[hit[0]])
    i = int(np.argmax((s[:-1] >= size) & (size >= s[1:])))
    lx0, lx1, lx = np.log(s[i]), np.log(s[i + 1]), np.log(size)
    if p[i + 1] > 0:
        a, b = np.log(p[i]), np.log(p[i + 1])
        return float(np.exp(a + (lx - lx0) * (b - a) / (lx1 - lx0)))
    return float(p[i] + (lx - lx0) * (p[i + 1] - p[i]) / (lx1 - lx0))


def mine_to_mill_chain(
    sizes: Any,
    blast_passing: Any,
    classification: Any,
    breakage: Any,
    target_p80: Any,
    installed_power: Any,
    energy_model: str,
    *,
    work_index: Any = None,
    mia: Any = None,
    mib: Any = None,
    fines_size: Any,
) -> ChainResult:
    """Mine-to-mill chain: blast curve through a crusher to the mill feed size, specific energy and throughput.

    Parameters
    ----------
    sizes : array [m]
        Upper class sizes, strictly decreasing (coarse to fine, 2 to 2,000).
    blast_passing : array [fraction]
        Cumulative passing of the blast at `sizes`.
    classification : array [probability]
        Crusher classification c_i (finest class 0).
    breakage : array [fraction]
        Crusher breakage matrix (strictly lower triangular, unit columns where c_j > 0).
    target_p80 : float [m]
        Final grind of the mill (> 0, finer than the crusher product F80).
    installed_power : float [W]
        Installed mill power (> 0).
    energy_model : str [option]
        "bond" (needs `work_index`) or "morrell" (needs `mia` and `mib`, no pebble crusher).
    work_index : float [J/kg]
        Bond work index (> 0), for the "bond" model.
    mia : float [J/kg]
        Morrell index M_ia (> 0), for the "morrell" model.
    mib : float [J/kg]
        Morrell index M_ib (> 0), for the "morrell" model.
    fines_size : float [m]
        Size at which the fines fraction of the crusher product is read (within the grid).

    Returns
    -------
    ChainResult
        `product_passing` [fraction] (cumulative passing of the crusher product at `sizes`), `f80` [m], `fines_fraction`
        [fraction], `specific_energy` [J/kg] and `throughput` [kg/s] = installed_power / specific_energy.

    Equation
    --------
    class_masses -> crusher_matrix_model -> cumulative_passing -> passing_size (F80, fines) -> bond_energy or
    morrell_tumbling_coarse + morrell_tumbling_fine from F80 to the target -> throughput = P / W.

    Source
    ------
    mcivor2016bondgmsg p. 1 (Bond energy); gmsg2016morrell eqs. B2-B3, p. 6 (Morrell); whiten1972crushing (crusher
    model,
    UNVERIFIED); ouchterlony2005swebrec (test oracle).

    Validity
    --------
    Steady state, one pass; the crusher classification and breakage are inputs. A Bond target below 70 micrometres or a
    Morrell target below 45 micrometres emits ValidityWarning.

    Knowledge rows
    --------------
    none
    """
    s, passing = _curve(
        sizes, blast_passing, decreasing=True, names=("sizes", "blast_passing"), max_size=MAX_CRUSHER_CLASSES
    )
    model = check_option(energy_model, "energy_model", ENERGY_MODELS)
    target = scalar(target_p80, "target_p80", lo=0, lo_open=True)
    power = scalar(installed_power, "installed_power", lo=0, lo_open=True)
    fines = scalar(fines_size, "fines_size", lo=0, lo_open=True)
    indices = {"work_index": work_index, "mia": mia, "mib": mib}
    needed = ("work_index",) if model == "bond" else ("mia", "mib")
    values = {}
    for name in needed:
        if indices[name] is None:
            raise InputError(f"argument '{name}' is required by energy_model {model!r}", argument=name)
        values[name] = scalar(indices[name], name, lo=0, lo_open=True)
    product = crusher_matrix_model(class_masses(s, passing), classification, breakage)
    curve = cumulative_passing(product)
    if not curve[-1] <= 4 / 5 <= curve[0]:
        raise InputError(
            "argument 'blast_passing' does not reach 80 % passing, so F80 is undefined", argument="blast_passing"
        )
    f80 = _interpolate_size(s, curve, 4 / 5)
    if not target < f80:
        raise InputError(
            f"argument 'target_p80' must be finer than the crusher product F80 ({f80!r} m)", argument="target_p80"
        )
    if not s[-1] <= fines <= s[0]:
        raise InputError(
            f"argument 'fines_size' must lie within the size grid [{s[-1]!r}, {s[0]!r}]", argument="fines_size"
        )
    if model == "bond":
        energy = bond_energy(values["work_index"], f80, target)
    else:
        energy = morrell_tumbling_coarse(values["mia"], f80, False) + morrell_tumbling_fine(values["mib"], target)
    w = np.float64(energy)
    return ChainResult(curve, np.float64(f80), np.float64(_passing_at(s, curve, fines)), w, np.float64(power / w))
