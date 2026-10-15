"""Ultimate pit as a maximum-weight closure, solved as a minimum s-t cut by an own Dinic max-flow (spec 007 FR-007-04
to -07).

The network has the blocks 0..n-1, the source n and the sink n + 1; arcs s -> i (capacity v_i) for v_i > 0, i -> t
(capacity
-v_i) for v_i < 0 and i -> j (infinite) for every precedence arc. The pit is the set reachable from s in the final
residual
network, which is the smallest source side of a minimum cut and so the smallest maximum-weight closure. The algorithm is
iterative (no recursion, for Pyodide) and uses plain Python lists in the hot loops.
"""

from __future__ import annotations

from typing import Any, NamedTuple

import numpy as np
import numpy.typing as npt

from .._validate import as_float_array, check_domain, check_finite, check_rank, check_size
from ._economics import MAX_BLOCKS, block_inputs
from ._precedence import check_arcs

__all__ = ["UltimatePit", "nested_pits", "ultimate_pit_mincut"]


class UltimatePit(NamedTuple):
    """Boolean pit mask and its value (the sum of the values of the selected blocks)."""

    mask: npt.NDArray[np.bool_]
    value: Any


def _closure_mask(values: npt.NDArray[np.float64], arcs: npt.NDArray[np.int64]) -> npt.NDArray[np.bool_]:
    """Smallest maximum-weight closed set of the blocks (values: float64, arcs: validated int64 (m, 2))."""
    n = int(values.size)
    s, t = n, n + 1
    pos = np.flatnonzero(values > 0)
    neg = np.flatnonzero(values < 0)
    if pos.size == 0:
        return np.zeros(n, dtype=bool)
    tails = np.concatenate([arcs[:, 0], np.full(pos.size, s, dtype=np.int64), neg])
    heads = np.concatenate([arcs[:, 1], pos, np.full(neg.size, t, dtype=np.int64)])
    caps = np.concatenate([np.full(arcs.shape[0], np.inf), values[pos], -values[neg]])
    e = tails.size
    # half-edges 0..e-1 forward, e..2e-1 reverse; sort them by tail node into a CSR layout
    tail_all = np.concatenate([tails, heads])
    order = np.argsort(tail_all, kind="stable")
    inverse = np.empty(2 * e, dtype=np.int64)
    inverse[order] = np.arange(2 * e, dtype=np.int64)
    head_l = np.concatenate([heads, tails])[order].tolist()
    rev_l = inverse[(order + e) % (2 * e)].tolist()
    cap = np.concatenate([caps, np.zeros(e)])[order].tolist()
    n_nodes = n + 2
    start = np.concatenate([[0], np.cumsum(np.bincount(tail_all, minlength=n_nodes))]).tolist()
    level: list[int] = []
    while True:
        level = [-1] * n_nodes
        level[s] = 0
        queue = [s]
        found = False
        for u in queue:
            lu = level[u] + 1
            for k in range(start[u], start[u + 1]):
                if cap[k] > 0.0:
                    v = head_l[k]
                    if level[v] < 0:
                        level[v] = lu
                        queue.append(v)
                        if v == t:
                            found = True
            if found:
                break
        if not found:
            break
        _blocking_flow(cap, head_l, rev_l, start, level, s, t)
    return np.asarray(level[:n], dtype=np.int64) >= 0


def _blocking_flow(
    cap: list[float], head: list[int], rev: list[int], start: list[int], level: list[int], s: int, t: int
) -> None:
    """Saturate the level graph with an iterative depth-first search and current-arc pointers."""
    it = start[:]
    path: list[int] = []
    nodes = [s]
    u = s
    while True:
        if u == t:
            flow = min(cap[k] for k in path)
            cut = -1
            for idx, k in enumerate(path):
                cap[k] -= flow
                cap[rev[k]] += flow
                if cut < 0 and cap[k] <= 0.0:
                    cut = idx
            del path[cut:]
            del nodes[cut + 1 :]
            u = nodes[-1]
            continue
        k = it[u]
        end = start[u + 1]
        lu = level[u] + 1
        while k < end and not (cap[k] > 0.0 and level[head[k]] == lu):
            k += 1
        it[u] = k
        if k < end:
            path.append(k)
            u = head[k]
            nodes.append(u)
        else:
            if u == s:
                return
            level[u] = -1
            path.pop()
            nodes.pop()
            u = nodes[-1]
            it[u] += 1


def _check_values(values: Any) -> npt.NDArray[np.float64]:
    v = as_float_array(values, "values")
    check_rank(v, "values", 1)
    check_size(v, "values", min_size=1, max_size=MAX_BLOCKS)
    return check_finite(v, "values")


def ultimate_pit_mincut(values: Any, arcs: Any) -> UltimatePit:
    """Ultimate pit: the smallest maximum-weight closed set of a block precedence graph, by a minimum s-t cut.

    Parameters
    ----------
    values : array [currency]
        Economic value of each block (1-D, 1 to 100,000 blocks).
    arcs : array of int [block index pairs, shape (m, 2)]
        Precedence arcs (i, j), "mining block i requires block j"; at most 2,000,000, no self-arcs.

    Returns
    -------
    UltimatePit
        `mask` (boolean array, true for the blocks of the pit) and `value` [currency] (`numpy.float64`, the sum of the
        values of the selected blocks).

    Equation
    --------
    max over closed sets C of sum_{i in C} v_i; the pit is the source side reachable from s in the residual network of
    the s-t network with capacities v_i (s to i), -v_i (i to t) and infinity (precedence arcs).

    Source
    ------
    picard1976closure (definition of a maximal closure, abstract); lerchs1965optimum (bibliographic, not read); the
    reduction is re-derived in spec 007 section 7.

    Validity
    --------
    At most 100,000 blocks and 2,000,000 arcs. Tests compare the result with exhaustive enumeration (up to 16 blocks)
    and
    with networkx minimum cuts (not a runtime dependency). Exact mask equality is guaranteed for integer values of
    magnitude up to 2**30; real values agree in value within 1e-9 of the sum of absolute values.

    Knowledge rows
    --------------
    none
    """
    v = _check_values(values)
    a = check_arcs(arcs, int(v.size))
    mask = _closure_mask(v, a)
    return UltimatePit(mask, np.float64(v[mask].sum()))


def nested_pits(
    tonnage: Any,
    grade: Any,
    price: Any,
    selling_cost: Any,
    recovery: Any,
    processing_cost: Any,
    mining_cost: Any,
    arcs: Any,
    revenue_factors: Any,
) -> npt.NDArray[np.bool_]:
    """Nested pits: the ultimate pit of every revenue factor.

    Parameters
    ----------
    tonnage : array [kg]
        Block masses, >= 0 (1-D, at most 100,000 blocks).
    grade : array [1]
        Block grades as mass fractions, in [0, 1].
    price : float [currency/kg of metal]
        Metal price, greater than `selling_cost`.
    selling_cost : float [currency/kg of metal]
        Selling cost per kg of metal, >= 0.
    recovery : float [1]
        Metallurgical recovery, in (0, 1].
    processing_cost : float [currency/kg of ore]
        Processing cost, >= 0.
    mining_cost : float [currency/kg of rock]
        Mining cost, >= 0.
    arcs : array of int [block index pairs, shape (m, 2)]
        Precedence arcs as in `ultimate_pit_mincut`.
    revenue_factors : array [1]
        Revenue factors lambda >= 0 (1-D, at least one), in any order.

    Returns
    -------
    array of bool [mask, shape (len(revenue_factors), n_blocks)]
        One pit mask per revenue factor, in the order given.

    Equation
    --------
    v_i(lambda) = max(T_i [lambda g_i y (p - s_r) - c_p], 0) - T_i c_m, each pit as in `ultimate_pit_mincut`.

    Source
    ------
    hochbaum2008pseudoflow (context: nested cuts, abstract); the per-factor form is derived in spec 007 section 3.

    Validity
    --------
    At most 100,000 blocks and 2,000,000 arcs; every factor is solved from scratch (no parametric speed-up). Pits grow
    with lambda (tests check nesting) and the pit of lambda = 0 is empty when every mining cost is positive.

    Knowledge rows
    --------------
    none
    """
    t, g, p, sr, y, cp, cm = block_inputs(tonnage, grade, price, selling_cost, recovery, processing_cost, mining_cost)
    t = np.atleast_1d(t)
    g = np.atleast_1d(g)
    for name, arr in (("tonnage", t), ("grade", g)):
        check_rank(arr, name, 1)
        check_size(arr, name, min_size=1, max_size=MAX_BLOCKS)
    t, g = np.broadcast_arrays(t, g)
    a = check_arcs(arcs, int(t.size))
    lam = check_domain(
        check_finite(as_float_array(revenue_factors, "revenue_factors"), "revenue_factors"), "revenue_factors", lo=0.0
    )
    lam = np.atleast_1d(lam)
    check_rank(lam, "revenue_factors", 1)
    check_size(lam, "revenue_factors", min_size=1)
    unit_margin = g * y * (p - sr)
    out = np.empty((lam.size, t.size), dtype=bool)
    for k, factor in enumerate(lam):
        v = np.maximum(t * (factor * unit_margin - cp), 0.0) - t * cm
        out[k] = _closure_mask(v, a)
    return out
