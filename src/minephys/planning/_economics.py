"""Block values, the break-even cut-off grade, the strip ratio and net present values (spec 007 FR-007-01, -02, -08
to -14)."""

from __future__ import annotations

from typing import Any, NamedTuple

import numpy as np
import numpy.typing as npt

from .._errors import InputError, InputTypeError
from .._validate import (
    as_float_array,
    broadcast_all,
    check_bool,
    check_domain,
    check_finite,
    check_option,
    check_rank,
    check_size,
    finalize,
)
from ._precedence import check_arcs

FloatArray = npt.NDArray[np.float64]

MAX_BLOCKS = 100_000

__all__ = [
    "BlockValue",
    "ScheduleNPV",
    "block_economic_value",
    "breakeven_cutoff_grade",
    "npv",
    "schedule_npv",
    "strip_ratio",
]


class BlockValue(NamedTuple):
    """Value of each block and whether it goes to the plant."""

    value: Any
    processed: Any


class ScheduleNPV(NamedTuple):
    """End-of-period NPV of a schedule and its per-period cash flows."""

    npv: Any
    cash_flows: FloatArray


def check_prices(price: FloatArray, selling_cost: FloatArray) -> None:
    """Domain checks shared by the block-value functions: selling cost >= 0 and price > selling cost."""
    check_domain(selling_cost, "selling_cost", lo=0.0)
    bad = price <= selling_cost
    if bad.any():
        idx = int(np.argmax(bad.ravel()))
        raise InputError(
            f"argument 'price' must be greater than 'selling_cost', got price {float(np.ravel(price)[idx])!r} and "
            f"selling_cost {float(np.ravel(selling_cost)[idx])!r}",
            argument="price",
        )


def _finite(value: Any, name: str, **bounds: Any) -> FloatArray:
    return check_domain(check_finite(as_float_array(value, name), name), name, **bounds)


def block_inputs(
    tonnage: Any,
    grade: Any,
    price: Any,
    selling_cost: Any,
    recovery: Any,
    processing_cost: Any,
    mining_cost: Any,
) -> tuple[FloatArray, ...]:
    """Validated, broadcast block-value inputs (shared by `block_economic_value` and `nested_pits`)."""
    t = _finite(tonnage, "tonnage", lo=0.0)
    g = _finite(grade, "grade", lo=0.0, hi=1.0)
    p = _finite(price, "price")
    sr = _finite(selling_cost, "selling_cost", lo=0.0)
    y = _finite(recovery, "recovery", lo=0.0, hi=1.0, lo_open=True)
    cp = _finite(processing_cost, "processing_cost", lo=0.0)
    cm = _finite(mining_cost, "mining_cost", lo=0.0)
    arrays = broadcast_all(tonnage=t, grade=g, price=p, selling_cost=sr, recovery=y, processing_cost=cp, mining_cost=cm)
    check_prices(arrays[2], arrays[3])
    return arrays


def block_economic_value(
    tonnage: Any,
    grade: Any,
    price: Any,
    selling_cost: Any,
    recovery: Any,
    processing_cost: Any,
    mining_cost: Any,
) -> BlockValue:
    """Economic value of a block and its destination (process or waste).

    Parameters
    ----------
    tonnage : float or array [kg]
        Block mass, >= 0.
    grade : float or array [1]
        Mass fraction of metal in the block, in [0, 1].
    price : float or array [currency/kg of metal]
        Metal price, greater than `selling_cost`.
    selling_cost : float or array [currency/kg of metal]
        Selling cost per kg of metal, >= 0.
    recovery : float or array [1]
        Metallurgical recovery, in (0, 1].
    processing_cost : float or array [currency/kg of ore]
        Processing cost, >= 0.
    mining_cost : float or array [currency/kg of rock]
        Mining cost, >= 0.

    Returns
    -------
    BlockValue
        `value` [currency] and `processed` (boolean, true exactly where the processing margin is positive); arrays
        broadcast, all-scalar inputs give `numpy.float64` and `numpy.bool_`.

    Equation
    --------
    v = max(T [g y (p - s_r) - c_p], 0) - T c_m; the block is processed where T [g y (p - s_r) - c_p] > 0.

    Source
    ------
    lane1988economic (bibliographic, not read): derived form, checked by hand calculation in spec 007 section 3.

    Validity
    --------
    Every formula is homogeneous, so any consistent unit system gives the same value. Not a reserve statement or
    economic
    advice.

    Knowledge rows
    --------------
    none
    """
    t, g, p, sr, y, cp, cm = block_inputs(tonnage, grade, price, selling_cost, recovery, processing_cost, mining_cost)
    margin = t * (g * y * (p - sr) - cp)
    value = np.maximum(margin, 0.0) - t * cm
    processed = margin > 0
    return BlockValue(finalize(value, t, g, p, sr, y, cp, cm), processed[()] if processed.ndim == 0 else processed)


def breakeven_cutoff_grade(processing_cost: Any, price: Any, selling_cost: Any, recovery: Any) -> Any:
    """Break-even cut-off grade: the grade at which the processing margin vanishes.

    Parameters
    ----------
    processing_cost : float or array [currency/kg of ore]
        Processing cost, >= 0.
    price : float or array [currency/kg of metal]
        Metal price, greater than `selling_cost`.
    selling_cost : float or array [currency/kg of metal]
        Selling cost per kg of metal, >= 0.
    recovery : float or array [1]
        Metallurgical recovery, in (0, 1].

    Returns
    -------
    float or array [1]
        Break-even grade as a mass fraction (`numpy.float64` for scalar inputs).

    Equation
    --------
    g_be = c_p / (y (p - s_r)).

    Source
    ------
    lane1988economic (bibliographic, not read): derived form, checked by hand calculation in spec 007 section 3.

    Validity
    --------
    Homogeneous in the currency and mass units; the result can exceed 1 when the processing cost is large, which means
    that no block pays for processing.

    Knowledge rows
    --------------
    none
    """
    cp = _finite(processing_cost, "processing_cost", lo=0.0)
    p = _finite(price, "price")
    sr = _finite(selling_cost, "selling_cost", lo=0.0)
    y = _finite(recovery, "recovery", lo=0.0, hi=1.0, lo_open=True)
    cp, p, sr, y = broadcast_all(processing_cost=cp, price=p, selling_cost=sr, recovery=y)
    check_prices(p, sr)
    return finalize(cp / (y * (p - sr)), cp, p, sr, y)


def _mask(value: Any, name: str) -> npt.NDArray[np.bool_]:
    if isinstance(value, list | tuple):
        value = np.asarray(value)
    return np.asarray(check_bool(value, name))


def strip_ratio(pit: Any, tonnage: Any, is_ore: Any) -> Any:
    """Strip ratio (waste tonnage over ore tonnage) of the blocks selected by a mask.

    Parameters
    ----------
    pit : array of bool [mask]
        Selected blocks (a pit, or `outer & ~inner` for a pushback).
    tonnage : array [kg]
        Block masses, finite and >= 0.
    is_ore : array of bool [mask]
        True for blocks that are ore.

    Returns
    -------
    float [t/t, dimensionless]
        Waste tonnage over ore tonnage of the selected blocks (`numpy.float64`).

    Equation
    --------
    SR = sum_{i in pit, not ore} T_i / sum_{i in pit, ore} T_i.

    Source
    ------
    lane1988economic (bibliographic, not read): definition; hand calculation in spec 007 section 3.

    Validity
    --------
    A selection with zero ore tonnage raises InputError (the ratio is undefined; no inf or nan is returned).

    Knowledge rows
    --------------
    none
    """
    pit_m = _mask(pit, "pit")
    ore_m = _mask(is_ore, "is_ore")
    ton = check_domain(check_finite(as_float_array(tonnage, "tonnage"), "tonnage"), "tonnage", lo=0.0)
    check_rank(pit_m, "pit", 1)  # type: ignore[arg-type]
    check_rank(ton, "tonnage", 1)
    check_rank(ore_m, "is_ore", 1)  # type: ignore[arg-type]
    if pit_m.shape != ton.shape:
        raise InputError(
            f"arguments pit and tonnage must have the same length, got {pit_m.shape} and {ton.shape}", argument="pit"
        )
    if ore_m.shape != ton.shape:
        raise InputError(
            f"arguments is_ore and tonnage must have the same length, got {ore_m.shape} and {ton.shape}",
            argument="is_ore",
        )
    ore = float(np.sum(ton[pit_m & ore_m]))
    if not ore > 0.0:
        raise InputError("the selection has no ore tonnage, so the strip ratio is undefined", argument="pit")
    waste = float(np.sum(ton[pit_m & ~ore_m]))
    return np.float64(waste / ore)


def _rate(rate: Any) -> float:
    arr = check_finite(as_float_array(rate, "rate"), "rate")
    if arr.ndim != 0:
        raise InputError(f"argument 'rate' must be a scalar, got shape {tuple(arr.shape)}", argument="rate")
    if not float(arr) > -1.0:
        raise InputError(f"argument 'rate' must be > -1, got {float(arr)!r}", argument="rate")
    return float(arr)


def npv(cash_flows: Any, rate: Any, timing: str = "end") -> Any:
    """Net present value of a cash-flow series.

    Parameters
    ----------
    cash_flows : array [currency]
        One cash flow per period (1-D, at least one).
    rate : float [1]
        Discount rate per period, > -1.
    timing : str [option]
        "end" (flow t discounted by (1 + r)^(t + 1), 0-based t) or "start" (by (1 + r)^t).

    Returns
    -------
    float [currency]
        The net present value (`numpy.float64`).

    Equation
    --------
    NPV = sum_{t=1}^{T} CF_t / (1 + r)^t for "end"; sum_{t=0}^{T-1} CF_t / (1 + r)^t for "start".

    Source
    ------
    lane1988economic (bibliographic, not read): definition; annuity formula by hand calculation in spec 007 section 3.

    Validity
    --------
    Rates down to just above -1 are accepted; the series length is limited only by memory.

    Knowledge rows
    --------------
    none
    """
    cf = check_finite(as_float_array(cash_flows, "cash_flows"), "cash_flows")
    r = _rate(rate)
    check_option(timing, "timing", ("end", "start"))
    check_rank(cf, "cash_flows", 1)
    check_size(cf, "cash_flows", min_size=1)
    shift = 1 if timing == "end" else 0
    t = np.arange(shift, cf.size + shift, dtype=np.float64)
    return np.float64(np.sum(cf / (1.0 + r) ** t))


def _periods(value: Any) -> npt.NDArray[np.int64]:
    arr = np.asarray(value)
    if arr.dtype.kind not in "iu":
        raise InputTypeError(f"argument 'periods' must be an integer array, got dtype {arr.dtype}", argument="periods")
    check_rank(arr, "periods", 1)  # type: ignore[arg-type]
    if arr.size and int(arr.max()) > np.iinfo(np.int64).max:
        raise InputError("argument 'periods' is out of range", argument="periods")
    if arr.size and int(arr.min()) < -1:
        raise InputError(f"argument 'periods' must be >= -1, got {int(arr.min())}", argument="periods")
    return arr.astype(np.int64)


def schedule_npv(
    periods: Any,
    block_values: Any,
    rate: Any,
    arcs: Any = None,
    tonnage: Any = None,
    capacities: Any = None,
) -> ScheduleNPV:
    """Per-period cash flows and end-of-period NPV of a block schedule, with precedence and capacity checks.

    Parameters
    ----------
    periods : array of int [period index]
        Period of each block (>= 0), or -1 for a block that is not mined.
    block_values : array [currency]
        Value of each block.
    rate : float [1]
        Discount rate per period, > -1.
    arcs : array of int [block index pairs], optional
        Precedence arcs (i, j), "mining i requires j"; checked when given.
    tonnage : array [kg], optional
        Block masses; with `capacities`, the mined mass of each period is checked.
    capacities : array [kg per period], optional
        Mining capacity of each period (one entry per period of the schedule).

    Returns
    -------
    ScheduleNPV
        `npv` [currency] (end-of-period discounting, `numpy.float64`) and `cash_flows` [currency per period] (float64,
        length max(periods) + 1).

    Equation
    --------
    CF_t = sum of the values of the blocks mined in period t; NPV = sum_t CF_t / (1 + r)^(t + 1).

    Source
    ------
    lane1988economic (bibliographic, not read): definition; hand aggregation in spec 007 section 3.

    Validity
    --------
    A check and an evaluation, not an optimiser: the first violated arc or period raises InputError. A schedule that
    mines
    nothing has empty cash flows and zero NPV. At most 100,000 blocks and 2,000,000 arcs.

    Knowledge rows
    --------------
    none
    """
    per = _periods(periods)
    check_size(per.astype(np.float64), "periods", min_size=1, max_size=MAX_BLOCKS)
    values = check_finite(as_float_array(block_values, "block_values"), "block_values")
    check_rank(values, "block_values", 1)
    if values.shape != per.shape:
        raise InputError(
            f"arguments periods and block_values must have the same length, got {per.shape} and {values.shape}",
            argument="block_values",
        )
    r = _rate(rate)
    n_periods = int(per.max()) + 1
    ton = cap = None
    if (tonnage is None) != (capacities is None):
        missing = "capacities" if capacities is None else "tonnage"
        raise InputError(f"argument '{missing}' is required together with its partner", argument=missing)
    if tonnage is not None:
        ton = check_domain(check_finite(as_float_array(tonnage, "tonnage"), "tonnage"), "tonnage", lo=0.0)
        check_rank(ton, "tonnage", 1)
        if ton.shape != per.shape:
            raise InputError(
                f"arguments tonnage and periods must have the same length, got {ton.shape} and {per.shape}",
                argument="tonnage",
            )
        cap = check_domain(check_finite(as_float_array(capacities, "capacities"), "capacities"), "capacities", lo=0.0)
        check_rank(cap, "capacities", 1)
        if cap.size != n_periods:
            raise InputError(
                f"argument 'capacities' needs one entry per period ({n_periods}), got {cap.size}", argument="capacities"
            )
    if arcs is not None:
        a = check_arcs(arcs, per.size)
        i, j = a[:, 0], a[:, 1]
        bad = (per[i] >= 0) & ((per[j] < 0) | (per[j] > per[i]))
        if bad.any():
            k = int(np.argmax(bad))
            raise InputError(
                f"precedence violated by arc ({int(i[k])}, {int(j[k])}): block {int(i[k])} is mined in period "
                f"{int(per[i[k]])} but block {int(j[k])} in period {int(per[j[k]])}",
                argument="arcs",
            )
    mined = per >= 0
    cash = np.bincount(per[mined], weights=values[mined], minlength=n_periods).astype(np.float64)
    if ton is not None and cap is not None:
        used = np.bincount(per[mined], weights=ton[mined], minlength=n_periods)
        over = used > cap
        if over.any():
            k = int(np.argmax(over))
            raise InputError(
                f"capacity of period {k} exceeded: {float(used[k])!r} mined against {float(cap[k])!r}",
                argument="capacities",
            )
    if cash.size == 0:
        return ScheduleNPV(np.float64(0.0), cash)
    return ScheduleNPV(npv(cash, r), cash)
