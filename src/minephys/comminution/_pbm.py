"""Population balance grinding: batch and continuous mills and the Austin selection and breakage forms (spec 005
FR-005-13 to -18).

Classes are ordered coarse to fine; the last class is the sink (everything below the grid) and has zero selection.
With the
selection S_j (1/s) and the breakage matrix B (b_ij, strictly lower triangular), the rate matrix is A = -diag(S) + B
diag(S).
The matrix exponential is an own Pade(13) scaling-and-squaring (NumPy only), valid for repeated selection values
where an
eigen-decomposition fails.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .._errors import InputError
from .._validate import check_rank
from ._common import FloatArray, count, non_negative, row, scalar, vector

__all__ = ["austin_breakage", "austin_selection", "pbm_batch_grinding", "pbm_continuous_mill"]

MAX_CLASSES = 200
_SUM_TOL = 10**-12
_PADE = (
    64764752532480000,
    32382376266240000,
    7771770303897600,
    1187353796428800,
    129060195264000,
    10559470521600,
    670442572800,
    33522128640,
    1323241920,
    40840800,
    960960,
    16380,
    182,
    1,
)


def _expm(m: FloatArray) -> FloatArray:
    """Matrix exponential by Pade(13) with scaling and squaring (Higham 2005), threshold 5 for the 1-norm."""
    n = m.shape[0]
    norm = float(np.max(np.sum(np.abs(m), axis=0)))
    squarings = 0 if norm <= 5 else int(np.ceil(np.log2(norm / 5)))
    a = m / 2**squarings
    b = [float(c) for c in _PADE]
    ident = np.eye(n)
    a2 = a @ a
    a4 = a2 @ a2
    a6 = a4 @ a2
    u = a @ (a6 @ (b[13] * a6 + b[11] * a4 + b[9] * a2) + b[7] * a6 + b[5] * a4 + b[3] * a2 + b[1] * ident)
    v = a6 @ (b[12] * a6 + b[10] * a4 + b[8] * a2) + b[6] * a6 + b[4] * a4 + b[2] * a2 + b[0] * ident
    r = np.linalg.solve(v - u, v + u)
    for _ in range(squarings):
        r = r @ r
    return np.tril(r)  # the rate matrix is lower triangular, and so is its exponential


def check_breakage(breakage: FloatArray, n: int, active: FloatArray, name: str = "breakage") -> None:
    """Shape, strict lower triangularity and unit column sums (for the columns where `active` > 0) of a breakage
    matrix."""
    if breakage.shape != (n, n):
        raise InputError(f"argument '{name}' must have shape {(n, n)}, got {tuple(breakage.shape)}", argument=name)
    if np.any(np.triu(breakage) != 0):
        raise InputError(f"argument '{name}' must be strictly lower triangular", argument=name)
    sums = breakage.sum(axis=0)
    off = (active > 0) & (np.abs(sums - 1) > _SUM_TOL)
    if off.any():
        j = int(np.argmax(off))
        raise InputError(f"argument '{name}': column {j} sums to {float(sums[j])!r}, not 1", argument=name)


def _mill(mass: Any, selection: Any, breakage: Any, mass_name: str) -> tuple[FloatArray, FloatArray]:
    """Validated (mass, rate matrix A) of a mill; every error names the argument involved."""
    m = non_negative(mass, mass_name)
    s = non_negative(selection, "selection")
    b = non_negative(breakage, "breakage")
    check_rank(m, mass_name, 1)
    check_rank(s, "selection", 1)
    check_rank(b, "breakage", 2)
    n = m.size
    if not 2 <= n <= MAX_CLASSES:
        raise InputError(f"argument '{mass_name}' needs 2 to {MAX_CLASSES} classes, got {n}", argument=mass_name)
    if s.size != n:
        raise InputError(
            f"arguments {mass_name} and selection differ in length: {n} and {s.size}", argument="selection"
        )
    if b.shape != (n, n):
        raise InputError(f"argument 'breakage' must have shape {(n, n)}, got {tuple(b.shape)}", argument="breakage")
    if s[-1] != 0:
        raise InputError("argument 'selection': the last (sink) class must have zero selection", argument="selection")
    check_breakage(b, n, s)
    return m, (b - np.eye(n)) * s[None, :]


def pbm_batch_grinding(mass: Any, selection: Any, breakage: Any, times: Any) -> FloatArray:
    """Batch grinding: class masses at the requested times from the population balance equation.

    Parameters
    ----------
    mass : array [kg]
        Class masses at t = 0, coarse to fine (2 to 200 classes, >= 0).
    selection : array [1/s]
        Selection (breakage rate) S_j of each class, >= 0; the last (sink) class must be 0.
    breakage : array [fraction]
        Strictly lower-triangular matrix b_ij, the fraction of broken class-j material entering finer class i; each
        column
        with S_j > 0 sums to 1 within 1e-12.
    times : array [s]
        Instants (1-D, >= 0), in any order.

    Returns
    -------
    array [kg], shape (len(times), n)
        Row k holds the class masses at times[k].

    Equation
    --------
    m(t) = expm(A t) m(0), A = -diag(S) + B diag(S).

    Source
    ------
    reid1965batch (analytical solution of the batch grinding equation, not read: the oracle is derived in spec 005
    section
    7); austin1971rate (rate-process form, bibliographic).

    Validity
    --------
    First-order, time-invariant selection and breakage; breakage into the same class is not modelled.

    Knowledge rows
    --------------
    none
    """
    m, rate = _mill(mass, selection, breakage, "mass")
    t = non_negative(times, "times")
    check_rank(t, "times", 1)
    if t.size < 1:
        raise InputError("argument 'times' needs at least 1 element, got 0", argument="times")
    return np.asarray([_expm(rate * ti) @ m for ti in t], dtype=np.float64)


def pbm_continuous_mill(feed: Any, selection: Any, breakage: Any, residence_time: Any, n_tanks: Any = 1) -> FloatArray:
    """Steady-state product of perfectly mixed tanks in series.

    Parameters
    ----------
    feed : array [kg/s]
        Feed rate of each class, coarse to fine (2 to 200 classes, >= 0).
    selection : array [1/s]
        Selection S_j of each class, >= 0; the last (sink) class must be 0.
    breakage : array [fraction]
        Strictly lower-triangular matrix b_ij; each column with S_j > 0 sums to 1 within 1e-12.
    residence_time : float [s]
        Total mean residence time tau (> 0), split equally between the tanks.
    n_tanks : int [count]
        Number of equal perfectly mixed tanks in series (>= 1).

    Returns
    -------
    array [kg/s]
        Product rate of each class.

    Equation
    --------
    m_out = (I - (tau/N) A)^(-N) m_in, A = -diag(S) + B diag(S).

    Source
    ------
    austin1984ballmilling (bibliographic, not read): the form is derived in spec 005 section 7 from the steady
    balance of one
    tank; reid1965batch for the batch limit.

    Validity
    --------
    As N grows the product tends to the batch result at t = tau; mass is conserved.

    Knowledge rows
    --------------
    none
    """
    m, rate = _mill(feed, selection, breakage, "feed")
    tau = scalar(residence_time, "residence_time", lo=0, lo_open=True)
    n = count(n_tanks, "n_tanks")
    step = np.eye(m.size) - (tau / n) * rate
    return np.asarray(np.linalg.matrix_power(np.linalg.inv(step), n) @ m, dtype=np.float64)


def _sizes(value: Any, minimum: int = 1) -> FloatArray:
    s = vector(value, "sizes", min_size=minimum, max_size=MAX_CLASSES)
    if np.any(s <= 0):
        raise InputError("argument 'sizes' must be positive", argument="sizes")
    if np.any(np.diff(s) >= 0):
        raise InputError("argument 'sizes' must be strictly decreasing (coarse to fine)", argument="sizes")
    return s


def austin_selection(sizes: Any, a: Any, alpha: Any, mu: Any, lam: Any, x0: Any = None) -> FloatArray:
    """Austin selection function of a ball mill.

    Parameters
    ----------
    sizes : array [m]
        Representative class sizes x_i, positive and strictly decreasing.
    a : float [1/s]
        Selection rate at the reference size (>= 0).
    alpha : float [1]
        Exponent of the size ratio (> 0).
    mu : float [m]
        Size above which the selection rate falls (> 0).
    lam : float [1]
        Steepness of the fall (>= 0).
    x0 : float or None [m]
        Reference size (> 0); None reads the knowledge row austin_reference_size (UNVERIFIED, so reading it warns).

    Returns
    -------
    array [1/s]
        Selection S_i of each class.

    Equation
    --------
    S_i = a (x_i/x0)^alpha / (1 + (x_i/mu)^lam).

    Source
    ------
    austin1984ballmilling (bibliographic, not read; the attribution of the form is UNVERIFIED); austin1971rate.

    Validity
    --------
    The form is evaluated as written; its attribution to Austin was not read, so the oracle is the form itself.

    Knowledge rows
    --------------
    austin_reference_size
    """
    s = _sizes(sizes)
    rate = scalar(a, "a", lo=0)
    exponent = scalar(alpha, "alpha", lo=0, lo_open=True)
    top = scalar(mu, "mu", lo=0, lo_open=True)
    steep = scalar(lam, "lam", lo=0)
    ref = row("austin_reference_size") if x0 is None else scalar(x0, "x0", lo=0, lo_open=True)
    return np.asarray(rate * (s / ref) ** exponent / (1 + (s / top) ** steep), dtype=np.float64)


def austin_breakage(sizes: Any, phi: Any, gamma: Any, beta: Any) -> FloatArray:
    """Austin breakage distribution matrix.

    Parameters
    ----------
    sizes : array [m]
        Upper class sizes s_1 > ... > s_n (2 to 200, positive).
    phi : float [fraction]
        Weight of the first term, in (0, 1].
    gamma : float [1]
        Exponent of the first term (> 0).
    beta : float [1]
        Exponent of the second term (> 0).

    Returns
    -------
    array [fraction], shape (n, n)
        Strictly lower-triangular b_ij; each column j < n sums to 1.

    Equation
    --------
    b_ij = B_j(s_i) - B_j(s_(i+1)) for j < i < n, b_nj = B_j(s_n), B_j(s) = phi (s/s_(j+1))^gamma + (1 - phi)
    (s/s_(j+1))^beta.

    Source
    ------
    austin1984ballmilling (bibliographic, not read; the attribution of the form is UNVERIFIED); austin1971rate.

    Validity
    --------
    The form is evaluated as written; the column sums are exactly 1 by telescoping.

    Knowledge rows
    --------------
    none
    """
    s = _sizes(sizes, minimum=2)
    weight = scalar(phi, "phi", lo=0, lo_open=True, hi=1)
    g = scalar(gamma, "gamma", lo=0, lo_open=True)
    bt = scalar(beta, "beta", lo=0, lo_open=True)
    n = s.size
    out = np.zeros((n, n))
    for j in range(n - 1):
        ratio = s[j + 1 :] / s[j + 1]
        cum = weight * ratio**g + (1 - weight) * ratio**bt  # B_j(s_i) for i > j
        out[j + 1 :, j] = cum - np.append(cum[1:], 0)
    return out
