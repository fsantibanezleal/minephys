"""Lane's limiting, balancing and optimum cut-off grades on a grade-tonnage histogram (spec 007 FR-007-15 to -17).

Inside each bin the tonnage is uniform in grade, so the ore fraction x(g) and the recovered metal per unit of
material q(g)
are piecewise linear and quadratic in g; both are evaluated from suffix sums by one binary search. Balancing roots
are found
by bisection on monotone predicates (the smallest grade of a flat stretch is returned).
"""

from __future__ import annotations

from typing import Any, NamedTuple

import numpy as np
import numpy.typing as npt

from .._errors import InputError
from .._validate import as_float_array, check_domain, check_finite, check_rank, check_size
from ._economics import check_prices

MAX_BINS = 100_000

__all__ = ["LaneCutoffs", "lane_cutoff_grades"]

_TIE = 1e-12
_BIND = 1e-9


class LaneCutoffs(NamedTuple):
    """Limiting (g_m, g_c, g_r), balancing (g_mc, g_mr, g_cr) and optimum cut-off grades of Lane's theory."""

    g_m: Any
    g_c: Any
    g_r: Any
    g_mc: Any
    g_mr: Any
    g_cr: Any
    optimum: Any
    value: Any
    binding: tuple[str, ...]


class _Histogram:
    """Ore fraction x(g) and recovered metal per unit of material q(g) of a uniform-in-bin histogram."""

    def __init__(self, edges: npt.NDArray[np.float64], tonnage: npt.NDArray[np.float64], recovery: float) -> None:
        self.edges = edges
        self.tonnage = tonnage
        self.total = float(tonnage.sum())
        self.width = np.diff(edges)
        self.recovery = recovery
        n = tonnage.size
        # suffix sums of the tonnage and of the metal (t (a + b) / 2) of the bins strictly above bin k
        self.mass_above = np.concatenate([np.cumsum(tonnage[::-1])[::-1][1:], [0.0]])
        metal = tonnage * (edges[:-1] + edges[1:]) / 2.0
        self.metal_above = np.concatenate([np.cumsum(metal[::-1])[::-1][1:], [0.0]])
        assert self.mass_above.size == n

    def xq(self, g: float) -> tuple[float, float]:
        e = self.edges
        if g <= e[0]:
            k, lo = 0, e[0]
        elif g >= e[-1]:
            return 0.0, 0.0
        else:
            k = int(np.searchsorted(e, g, side="right")) - 1
            lo = g
        b, w, t = e[k + 1], self.width[k], self.tonnage[k]
        x = self.mass_above[k] + t * (b - lo) / w
        q = self.metal_above[k] + t * (b * b - lo * lo) / (2.0 * w)
        return x / self.total, self.recovery * q / self.total

    def bisect(self, below: Any) -> float:
        """Smallest grade g in [first edge, last edge] with `below(g)` true (monotone predicate false then true)."""
        lo, hi = float(self.edges[0]), float(self.edges[-1])
        if below(lo):
            return lo
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if mid <= lo or mid >= hi:
                break
            if below(mid):
                hi = mid
            else:
                lo = mid
        return hi


def _scalar(value: Any, name: str, **bounds: Any) -> float:
    arr = check_domain(check_finite(as_float_array(value, name), name), name, **bounds)
    if arr.ndim != 0:
        raise InputError(f"argument '{name}' must be a scalar, got shape {tuple(arr.shape)}", argument=name)
    return float(arr)


def lane_cutoff_grades(
    grade_edges: Any,
    tonnage: Any,
    price: Any,
    selling_cost: Any,
    recovery: Any,
    processing_cost: Any,
    mining_cost: Any,
    fixed_cost: Any,
    mine_capacity: Any,
    plant_capacity: Any,
    market_capacity: Any,
    opportunity_cost: Any = 0.0,
) -> LaneCutoffs:
    """Lane's limiting and balancing cut-off grades and the optimum cut-off for given capacities.

    Parameters
    ----------
    grade_edges : array [1]
        Strictly increasing, non-negative bin edges (mass fractions), n + 1 values for n bins (1 to 100,000 bins).
    tonnage : array [kg]
        Mass of each bin (n values, >= 0, not all zero); uniform in grade inside a bin.
    price : float [currency/kg of metal]
        Metal price s, greater than `selling_cost`.
    selling_cost : float [currency/kg of metal]
        Selling cost r per kg of metal, >= 0.
    recovery : float [1]
        Metallurgical recovery y, in (0, 1].
    processing_cost : float [currency/kg of ore]
        Processing cost h, >= 0.
    mining_cost : float [currency/kg of material]
        Mining cost m, >= 0.
    fixed_cost : float [currency/s]
        Fixed cost f per unit time, >= 0.
    mine_capacity : float [kg/s]
        Mine capacity M of material, > 0.
    plant_capacity : float [kg/s]
        Plant capacity C of ore, > 0.
    market_capacity : float [kg/s of metal]
        Market capacity R of metal, > 0.
    opportunity_cost : float [currency/s]
        Opportunity cost F per unit time, >= 0 (an input; the life-of-mine iteration is out of scope).

    Returns
    -------
    LaneCutoffs
        `g_m`, `g_c`, `g_r` (None when the market denominator is <= 0), the balancing `g_mc`, `g_mr`, `g_cr` (None when
        no root lies in the grade range) [1], the optimum `optimum` [1], its `value` [currency per unit of material
        and time basis of the capacities] and `binding`, a tuple of "mine", "plant", "market".

    Equation
    --------
    V(g) = (s - r) q(g) - h x(g) - m - (f + F) max(1/M, x(g)/C, q(g)/R); g_m = h/((s - r) y);
    g_c = (h + (f + F)/C)/((s - r) y); g_r = h/((s - r - (f + F)/R) y); g_mc: x = C/M; g_mr: q = R/M; g_cr: q/x = R/C.

    Source
    ------
    lane1964choosing and lane1988economic (bibliographic, not read: the limiting cut-offs are derived forms);
    cetin2013gridsearch pp. 660 and 663 (the controlling-capacity rule).

    Validity
    --------
    Optimum = best of the in-range limiting and balancing cut-offs and the range ends (smallest grade on ties within
    1e-12
    relative); the brute-force grid of the tests is the oracle. At most 100,000 bins. Any consistent mass and time units
    give the same grades.

    Knowledge rows
    --------------
    none
    """
    edges = check_finite(as_float_array(grade_edges, "grade_edges"), "grade_edges")
    ton = check_finite(as_float_array(tonnage, "tonnage"), "tonnage")
    s = _scalar(price, "price")
    r = _scalar(selling_cost, "selling_cost", lo=0.0)
    y = _scalar(recovery, "recovery", lo=0.0, hi=1.0, lo_open=True)
    h = _scalar(processing_cost, "processing_cost", lo=0.0)
    m = _scalar(mining_cost, "mining_cost", lo=0.0)
    f = _scalar(fixed_cost, "fixed_cost", lo=0.0)
    cap_m = _scalar(mine_capacity, "mine_capacity", lo=0.0, lo_open=True)
    cap_c = _scalar(plant_capacity, "plant_capacity", lo=0.0, lo_open=True)
    cap_r = _scalar(market_capacity, "market_capacity", lo=0.0, lo_open=True)
    big_f = _scalar(opportunity_cost, "opportunity_cost", lo=0.0)
    check_prices(np.asarray(s), np.asarray(r))
    check_rank(edges, "grade_edges", 1)
    check_rank(ton, "tonnage", 1)
    check_size(edges, "grade_edges", min_size=2, max_size=MAX_BINS + 1)
    if ton.size != edges.size - 1:
        raise InputError(
            f"argument 'tonnage' needs one value per bin ({edges.size - 1}), got {ton.size}", argument="tonnage"
        )
    check_domain(ton, "tonnage", lo=0.0)
    check_domain(edges, "grade_edges", lo=0.0)
    if (np.diff(edges) <= 0).any():
        raise InputError("argument 'grade_edges' must be strictly increasing", argument="grade_edges")
    if not ton.sum() > 0:
        raise InputError("argument 'tonnage' must not be all zero", argument="tonnage")

    hist = _Histogram(edges, ton, y)
    net = s - r
    fixed = f + big_f
    g_m = h / (net * y)
    g_c = (h + fixed / cap_c) / (net * y)
    denom = net - fixed / cap_r
    g_r = h / (denom * y) if denom > 0 else None

    g_lo, g_hi = float(edges[0]), float(edges[-1])
    b_top = float(edges[1:][ton > 0][-1])

    def x_of(g: float) -> float:
        return hist.xq(g)[0]

    def q_of(g: float) -> float:
        return hist.xq(g)[1]

    c_over_m = cap_c / cap_m
    r_over_m = cap_r / cap_m
    r_over_c = cap_r / cap_c
    g_mc = hist.bisect(lambda g: x_of(g) <= c_over_m) if 0.0 < c_over_m <= 1.0 else None
    q_start = q_of(g_lo)
    g_mr = hist.bisect(lambda g: q_of(g) <= r_over_m) if 0.0 < r_over_m <= q_start else None

    def ratio_reached(g: float) -> bool:
        x, q = hist.xq(g)
        return x <= 0.0 or q >= r_over_c * x

    g_cr = hist.bisect(ratio_reached) if q_start <= r_over_c < y * b_top else None

    def objective(g: float) -> tuple[float, float, float, float]:
        x, q = hist.xq(g)
        times = (1.0 / cap_m, x / cap_c, q / cap_r)
        return net * q - h * x - m - fixed * max(times), *times

    candidates = [g_lo, g_hi]
    candidates.extend(g for g in (g_m, g_c, g_r, g_mc, g_mr, g_cr) if g is not None and g_lo <= g <= g_hi)
    scored = [(objective(g), g) for g in candidates]
    best = max(sc[0][0] for sc in scored)
    tol = _TIE * abs(best)
    optimum = min(g for sc, g in scored if sc[0] >= best - tol)
    v_star, *times = objective(optimum)
    top = max(times)
    binding = tuple(
        name for name, tm in zip(("mine", "plant", "market"), times, strict=True) if tm >= top * (1.0 - _BIND)
    )

    def out(value: float | None) -> Any:
        return None if value is None else np.float64(value)

    return LaneCutoffs(
        out(g_m), out(g_c), out(g_r), out(g_mc), out(g_mr), out(g_cr), np.float64(optimum), np.float64(v_star), binding
    )
