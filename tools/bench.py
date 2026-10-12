"""Benchmark runner with a reference-size registry (spec 000 NFR-000-07, T-000-023).

Usage:
  python tools/bench.py --list [--json] [--registry FILE]
  python tools/bench.py --run NAME [--repeat N] [--json] [--registry FILE]
  python tools/bench.py --check [--repeat N] [--json] [--registry FILE]
Budgets (NFR-000-07, CPython 3.14, median of the calls): 1 ms for a `closed_form` scalar call, 50 ms for an
`iterative` or `sampling` call at its reference size. `--run` times one warm-up call and then N calls (default 20);
`--check` runs every case and exits 1 when a median exceeds its budget (the release gate). `--registry FILE` replaces
the built-in registry with `{"cases": [{"name", "callable": "<module>:<attribute>", "args", "kwargs", "kind",
"reference_size"}]}`. Usage errors (unknown case, malformed registry, duplicate names, unknown kind, `--repeat`
outside 1..100000) exit with status 2 and a message, never a traceback.
The built-in registry is the list `BUILTIN` below; each module spec extends it with its reference sizes.
"""

from __future__ import annotations

import argparse
import importlib
import json
import statistics
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

BUDGET_MS = {"closed_form": 1.0, "iterative": 50.0, "sampling": 50.0}
DEFAULT_REPEAT = 20
MAX_REPEAT = 100_000
ROOT = Path(__file__).resolve().parents[1]


class UsageError(Exception):
    """A usage or registry error (exit status 2)."""


Case = dict[str, Any]


def _haulage_segments(n: int) -> dict[str, Any]:
    import numpy as np

    return {
        "mass": np.full(n, 400000.0),
        "length": np.full(n, 100.0),
        "rolling_resistance": np.full(n, 0.03),
        "grade": np.linspace(-0.08, 0.08, n),
    }


def _geotech_slices(n: int) -> dict[str, Any]:
    """Fredlund-Krahn geometry (SI) cut into n slices, with a strength that every method converges on."""
    import numpy as np

    from minephys import geotech

    ft = 0.3048
    cut = geotech.circular_slices(
        np.array([0.0, 60.0, 140.0, 180.0]) * ft,
        np.array([60.0, 60.0, 20.0, 20.0]) * ft,
        120.0 * ft,
        90.0 * ft,
        80.0 * ft,
        n,
        18850.0,
    )
    return {
        "width": cut.width,
        "weight": cut.weight,
        "base_angle": cut.base_angle,
        "pore_pressure": cut.pore_pressure,
        "cohesion": 28700.0,
        "friction_angle": 0.3490658503988659,
    }


def _geotech_monte_carlo() -> dict[str, Any]:
    slices = _geotech_slices(50)
    return {
        "width": slices["width"],
        "weight": slices["weight"],
        "base_angle": slices["base_angle"],
        "pore_pressure": slices["pore_pressure"],
        "cohesion_mean": 28700.0,
        "cohesion_sd": 4000.0,
        "friction_mean": 0.3490658503988659,
        "friction_sd": 0.03,
        "n_samples": 10000,
        "rng": 20261011,
    }


def _geotech_bayesian() -> dict[str, Any]:
    import numpy as np

    t = np.arange(0.0, 7.0) * 86400.0
    return {"t": t, "velocity": 1.0 / (10.0 * (864000.0 - t)), "rng": 20261011, "noise_sd": 43200.0, "n_draws": 10000}


def _comminution_pbm(n_classes: int) -> dict[str, Any]:
    """A population-balance mill of `n_classes` size classes (Austin selection and breakage)."""
    import numpy as np

    from minephys import comminution

    sizes = np.geomspace(1e-3, 1e-5, n_classes)
    selection = comminution.austin_selection(sizes, 0.5, 0.9, 1e-4, 2.0)
    selection[-1] = 0.0
    return {
        "mass": np.full(n_classes, 1.0 / n_classes),
        "selection": selection,
        "breakage": comminution.austin_breakage(sizes, 0.4, 0.8, 3.0),
    }


def _comminution_batch() -> dict[str, Any]:
    import numpy as np

    return {**_comminution_pbm(30), "times": np.array([60.0])}


def _comminution_continuous() -> dict[str, Any]:
    pbm = _comminution_pbm(30)
    return {
        "feed": pbm["mass"],
        "selection": pbm["selection"],
        "breakage": pbm["breakage"],
        "residence_time": 100.0,
        "n_tanks": 10,
    }


def _comminution_chain() -> dict[str, Any]:
    """The mine-to-mill chain over 400 sizes (identity crusher, Bond energy)."""
    import numpy as np

    sizes = np.geomspace(2.0, 1e-5, 400)
    passing = 1.0 / (1.0 + (np.log(2.0 / sizes) / np.log(8.0)) ** 2)
    return {
        "sizes": sizes,
        "blast_passing": passing,
        "classification": np.zeros(400),
        "breakage": np.zeros((400, 400)),
        "target_p80": 1e-4,
        "installed_power": 1e7,
        "energy_model": "bond",
        "work_index": 5.4e7,
        "fines_size": float(sizes[200]),
    }


def _environment_plume_grid() -> dict[str, Any]:
    """Gaussian plume over a 1,000 x 1,000 receptor grid."""
    import numpy as np

    return {
        "q": 1e-3,
        "u": 3.0,
        "y": np.linspace(-500.0, 500.0, 1000)[:, None],
        "z": np.linspace(0.0, 100.0, 1000)[None, :],
        "h": 5.0,
        "sigma_y": 40.0,
        "sigma_z": 20.0,
    }


def _planning_grid() -> dict[str, Any]:
    """A 6 x 6 x 6 block grid with the '1-5' precedence pattern."""
    import numpy as np

    from minephys import planning

    shape = (6, 6, 6)
    n = 6 * 6 * 6
    return {
        "arcs": planning.regular_grid_precedence(shape, "1-5"),
        "n": n,
        "values": np.linspace(-2.0, 3.0, n),
    }


def _planning_mincut() -> dict[str, Any]:
    grid = _planning_grid()
    return {"values": grid["values"], "arcs": grid["arcs"]}


def _planning_nested() -> dict[str, Any]:
    import numpy as np

    grid = _planning_grid()
    n = grid["n"]
    return {
        "tonnage": np.full(n, 1000.0),
        "grade": np.linspace(0.0, 0.02, n),
        "price": 8000.0,
        "selling_cost": 500.0,
        "recovery": 0.9,
        "processing_cost": 10.0,
        "mining_cost": 2.0,
        "arcs": grid["arcs"],
        "revenue_factors": np.array([0.5, 0.7, 0.9, 1.1, 1.3]),
    }


def _planning_lane() -> dict[str, Any]:
    """Lane's cut-off grades over 50 grade bins."""
    import numpy as np

    return {
        "grade_edges": np.linspace(0.0, 0.025, 51),
        "tonnage": np.full(50, 2.0e5),
        "price": 8000.0,
        "selling_cost": 500.0,
        "recovery": 0.9,
        "processing_cost": 10.0,
        "mining_cost": 2.0,
        "fixed_cost": 1.0e6,
        "mine_capacity": 8.0e6,
        "plant_capacity": 6.0e6,
        "market_capacity": 1.0e5,
    }


def _case(name: str, kind: str, size: dict[str, Any], kwargs: Callable[[], dict[str, Any]] | dict[str, Any]) -> Case:
    module, function = name.split(".", 1)
    return {
        "name": name,
        "callable": f"minephys.{module}:{function}",
        "kwargs": kwargs,
        "kind": kind,
        "reference_size": size,
    }


def _builtin() -> list[Case]:
    cases: list[Case] = []
    add = cases.append

    def trolley() -> dict[str, Any]:
        import numpy as np

        return {**_haulage_segments(1000), "on_trolley": np.arange(1000) % 2 == 0, "diesel_efficiency": 0.35, "electric_efficiency": 0.9}

    def mva() -> dict[str, Any]:
        import numpy as np

        return {
            "population": 200,
            "service_time": np.linspace(30.0, 300.0, 10),
            "visit_ratio": np.ones(10),
            "station_type": ["queue"] * 9 + ["delay"],
        }

    closed = {
        "haulage.grade_resistance": {"grade": 0.1},
        "haulage.total_resistance": {"rolling_resistance": 0.02, "grade": 0.1},
        "haulage.required_force": {"mass": 4e5, "total_resistance": 0.12},
        "haulage.rimpull_limited_speed": {"power": 1.8e6, "mass": 4e5, "total_resistance": 0.12},
        "haulage.retarder_limited_speed": {"retarder_power": 2.5e6, "mass": 4e5, "rolling_resistance": 0.02, "grade": -0.1},
        "haulage.loose_density": {"bank_density": 2700.0, "swell": 0.35},
        "haulage.loading_passes": {"target_payload": 216000.0, "bucket_volume": 40.0, "fill_factor": 0.9, "loose_density": 2000.0},
        "haulage.segment_travel_time": {"length": 3000.0, "speed": 4.0},
        "haulage.cycle_time": {"spot_load": 60.0, "load": 240.0, "haul_travel": 900.0, "spot_dump": 90.0, "dump": 45.0, "return_travel": 600.0},
        "haulage.segment_energy": {"mass": 4e5, "length": 3000.0, "rolling_resistance": 0.02, "grade": 0.1},
        "haulage.fuel_use": {"source_energy": 4e9, "fuel_energy_density": 36e9},
        "haulage.co2_from_diesel": {"fuel_volume": 0.112},
        "haulage.co2_from_electricity": {"energy": 1.5e9, "grid_intensity": 1e-7},
        "haulage.match_factor": {"n_trucks": 6, "n_loaders": 1, "load_time": 240.0, "cycle_time": 1440.0},
    }
    for name, kwargs in closed.items():
        add(_case(name, "closed_form", {"inputs": "scalar"}, kwargs))
    blasting = {
        "blasting.charge_per_hole": {"explosive_density": 850.0, "hole_diameter": 0.25, "charge_length": 7.2},
        "blasting.powder_factor": {"charge": 300.4, "burden": 6.0, "spacing": 7.0, "bench_height": 12.0},
        "blasting.kuznetsov_x50": {"rock_factor": 7.0, "powder_factor": 0.596, "charge": 300.4, "rws": 100.0, "variant": "cunningham2005"},
        "blasting.rock_factor": {"rmd": 50.0, "rdi": 17.5, "hf": 10.0},
        "blasting.hardness_factor": {"youngs_modulus": 30e9, "ucs": 150e6},
        "blasting.rock_density_influence": {"density": 2700.0},
        "blasting.uniformity_index": {"burden": 6.0, "spacing": 7.0, "hole_diameter": 0.25, "drilling_deviation": 0.3, "charge_length": 7.2, "bench_height": 12.0},
        "blasting.rosin_rammler_passing": {"size": 0.5, "x50": 0.3, "n": 1.1},
        "blasting.rosin_rammler_size": {"passing": 0.8, "x50": 0.3, "n": 1.1},
        "blasting.swebrec_passing": {"size": 0.5, "x50": 0.3, "xmax": 1.5, "b": 2.5},
        "blasting.swebrec_size": {"passing": 0.8, "x50": 0.3, "xmax": 1.5, "b": 2.5},
        "blasting.kco_undulation": {"n": 1.1, "x50": 0.3, "xmax": 1.5},
        "blasting.kco_distribution": {"size": 0.5, "x50": 0.3, "xmax": 1.5, "n": 1.1},
        "blasting.scaled_distance": {"distance": 300.0, "charge_per_delay": 150.0},
        "blasting.ppv_scaled_distance": {"distance": 300.0, "charge_per_delay": 150.0, "k_site": 1.0, "beta": 1.6},
        "blasting.ppv_limit": {"distance": 304.8},
        "blasting.max_charge_per_delay": {"distance": 304.8},
        "blasting.flyrock_range_no_drag": {"launch_speed": 40.0, "launch_angle": 0.7853981633974483},
        "blasting.flyrock_range_lundborg": {"hole_diameter": 0.127},
    }
    for name, kwargs in blasting.items():
        add(_case(name, "closed_form", {"inputs": "scalar"}, kwargs))
    add(
        _case(
            "blasting.flyrock_trajectory",
            "iterative",
            {"launch_speed": 40, "launch_angle_deg": 45, "diameter": 0.1, "time_step": 0.001},
            {
                "launch_speed": 40.0,
                "launch_angle": 0.7853981633974483,
                "diameter": 0.1,
                "rock_density": 2650.0,
                "drag_coefficient": 0.47,
                "air_density": 1.2,
            },
        )
    )
    geotech = {
        "geotech.hoek_brown_parameters": {"gsi": 50.0, "mi": 10.0, "disturbance": 0.0},
        "geotech.hoek_brown_sigma1": {"sigma3": 1.0e6, "sigma_ci": 50.0e6, "mb": 1.676772, "s": 3.86592e-3, "a": 0.505734},
        "geotech.hoek_brown_uniaxial_strength": {"sigma_ci": 50.0e6, "s": 3.86592e-3, "a": 0.505734},
        "geotech.hoek_brown_tensile_strength": {"sigma_ci": 50.0e6, "mb": 1.676772, "s": 3.86592e-3},
        "geotech.hoek_brown_rock_mass_strength": {"sigma_ci": 50.0e6, "mb": 1.676772, "s": 3.86592e-3, "a": 0.505734},
        "geotech.equivalent_mohr_coulomb": {"sigma_ci": 50.0e6, "mb": 1.676772, "s": 3.86592e-3, "a": 0.505734, "sigma3_max": 2.0e6},
        "geotech.sigma3_max": {"sigma_cm": 3.0e6, "unit_weight": 27000.0, "height": 100.0, "application": "slope"},
        "geotech.required_samples": {"pof": 0.05, "relative_error": 0.1},
        "geotech.los_phase": {"los_displacement": 0.002, "wavelength": 0.0175},
        "geotech.wrap_phase": {"phase": 4.0},
        "geotech.los_from_phase": {"phase": 1.0, "wavelength": 0.0175},
        "geotech.max_unambiguous_los_step": {"wavelength": 0.0175},
    }
    for name, kwargs in geotech.items():
        add(_case(name, "closed_form", {"inputs": "scalar"}, kwargs))
    add(_case("geotech.bishop_simplified_fos", "iterative", {"slices": 200}, lambda: _geotech_slices(200)))
    add(_case("geotech.spencer_fos", "iterative", {"slices": 200}, lambda: _geotech_slices(200)))
    add(_case("geotech.monte_carlo_fos", "sampling", {"samples": 10000, "slices": 50}, _geotech_monte_carlo))
    add(_case("geotech.bayesian_ttf", "sampling", {"draws": 10000, "samples": 7}, _geotech_bayesian))
    bulk = {
        "bulk.beverloo_discharge": {"orifice_diameter": 0.3, "particle_diameter": 0.02, "bulk_density": 1600.0, "discharge_coefficient": 0.56, "annulus_coefficient": 1.5},
        "bulk.repose_cone_height": {"base_radius": 30.0, "repose_angle": 0.6457718232379019},
        "bulk.repose_cone_volume": {"base_radius": 30.0, "repose_angle": 0.6457718232379019},
        "bulk.repose_ridge_volume": {"base_half_width": 30.0, "repose_angle": 0.6457718232379019, "length": 100.0, "end_cones": True},
        "bulk.conveyor_capacity": {"load_area": 0.25, "belt_speed": 4.0, "bulk_density": 1600.0},
        "bulk.cema_effective_tension": {"length": 1000.0, "lift": 30.0, "belt_weight": 300.0, "material_weight": 1362.0347, "kt": 1.0, "kx": 10.0, "ky": 0.03},
        "bulk.conveyor_power": {"effective_tension": 105222.08, "belt_speed": 4.0, "drive_efficiency": 0.9},
        "bulk.gy_fundamental_sampling_error": {"sample_mass": 1.0, "lot_mass": 1000.0, "top_size": 0.01, "mineralogical_factor": 1.0e4, "shape_factor": 0.5, "granulometric_factor": 0.25, "liberation_factor": 0.1},
    }
    for name, kwargs in bulk.items():
        add(_case(name, "closed_form", {"inputs": "scalar"}, kwargs))
    add(_case("bulk.gy_blending_variance", "closed_form", {"inputs": "scalar", "n_layers": 10000000}, {"input_variance": 1.0, "n_layers": 10000000, "lag1_correlation": 0.9}))
    add(_case("bulk.variance_reduction_ratio", "closed_form", {"inputs": "scalar", "n_layers": 10000000}, {"n_layers": 10000000, "lag1_correlation": 0.9}))
    add(_case("haulage.cycle_energy", "iterative", {"segments": 1000}, lambda: {**_haulage_segments(1000), "efficiency": 0.35}))
    add(_case("haulage.bev_cycle_energy", "iterative", {"segments": 1000}, lambda: {**_haulage_segments(1000), "drive_efficiency": 0.85, "regen_efficiency": 0.6}))
    add(_case("haulage.trolley_cycle_energy", "iterative", {"segments": 1000}, trolley))
    add(_case("haulage.mmc_queue", "iterative", {"servers": 10000}, {"arrival_rate": 90.0, "service_rate": 0.01, "servers": 10000}))
    add(_case("haulage.finite_source_queue", "iterative", {"trucks": 100000}, {"n_trucks": 100000, "travel_rate": 0.001, "service_rate": 1.0}))
    add(_case("haulage.mean_value_analysis", "iterative", {"population": 200, "stations": 10}, mva))
    comminution = {
        "comminution.bond_energy": {"work_index": 5.4e7, "f80": 1.0e-2, "p80": 1.0e-4},
        "comminution.morrell_energy": {"m_index": 7.0e7, "x1": 1.0e-2, "x2": 1.0e-4},
        "comminution.flotation_first_order": {"r_inf": 0.9, "k": 0.005, "t": 600.0},
    }
    for name, kwargs in comminution.items():
        add(_case(name, "closed_form", {"inputs": "scalar"}, kwargs))
    add(_case("comminution.pbm_batch_grinding", "iterative", {"classes": 30, "times": 1}, _comminution_batch))
    add(_case("comminution.pbm_continuous_mill", "iterative", {"classes": 30, "tanks": 10}, _comminution_continuous))
    add(_case("comminution.mine_to_mill_chain", "iterative", {"sizes": 400}, _comminution_chain))
    environment = {
        "environment.ap42_unpaved_emission_factor": {
            "silt_fraction": 0.1,
            "mean_weight": 263083.57,
            "size_class": "PM10",
        },
        "environment.precipitation_correction": {"emission_factor": 0.0028, "wet_days": 100},
        "environment.beer_lambert_transmittance": {"extinction": 0.01, "path_length": 30.0},
    }
    for name, kwargs in environment.items():
        add(_case(name, "closed_form", {"inputs": "scalar"}, kwargs))
    add(_case("environment.gaussian_plume", "iterative", {"receptors": "1000 x 1000"}, _environment_plume_grid))
    planning = {
        "planning.block_economic_value": {
            "tonnage": 1000.0,
            "grade": 0.01,
            "price": 8000.0,
            "selling_cost": 500.0,
            "recovery": 0.9,
            "processing_cost": 10.0,
            "mining_cost": 2.0,
        },
        "planning.npv": {"cash_flows": [-100.0, 40.0, 50.0, 60.0], "rate": 0.1},
    }
    for name, kwargs in planning.items():
        add(_case(name, "closed_form", {"inputs": "scalar"}, kwargs))
    add(_case("planning.ultimate_pit_mincut", "iterative", {"grid": "6 x 6 x 6", "arcs": "1-5"}, _planning_mincut))
    add(
        _case(
            "planning.nested_pits",
            "iterative",
            {"grid": "6 x 6 x 6", "arcs": "1-5", "revenue_factors": 5},
            _planning_nested,
        )
    )
    add(_case("planning.lane_cutoff_grades", "iterative", {"bins": 50}, _planning_lane))
    # Knowledge (spec 008 NFR-008-02): the warm call is registered here (closed form, <= 1 ms, served from the cache);
    # the cold load-and-validate of all packaged knowledge has a 0.5 s budget that this registry has no kind for, so it
    # is measured by tests/unit/test_t_008_061_bench_registry.py in fresh interpreters (cold <= 0.5 s, warm <= 1 ms).
    add(
        _case(
            "knowledge.get_parameter",
            "closed_form",
            {"inputs": "scalar", "cache": "warm"},
            {"id": "bond_law_coefficient"},
        )
    )
    return cases


BUILTIN: list[Case] = _builtin()


def _validate(cases: Any, source: str) -> list[Case]:
    if not isinstance(cases, list):
        raise UsageError(f"{source}: 'cases' must be a list")
    seen: set[str] = set()
    out: list[Case] = []
    for i, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            raise UsageError(f"{source}: case {i} is not an object")
        for key in ("name", "callable", "kind"):
            if not isinstance(case.get(key), str) or not case[key]:
                raise UsageError(f"{source}: case {i} needs a non-empty string '{key}'")
        name = case["name"]
        if "." not in name or name.startswith(".") or name.endswith("."):
            raise UsageError(f"{source}: case name {name!r} must look like '<module>.<function>'")
        if name in seen:
            raise UsageError(f"{source}: duplicate case name {name!r}")
        seen.add(name)
        if case["kind"] not in BUDGET_MS:
            raise UsageError(f"{source}: case {name!r} has unknown kind {case['kind']!r}; use {', '.join(BUDGET_MS)}")
        if ":" not in case["callable"]:
            raise UsageError(f"{source}: case {name!r}: callable must be '<module>:<attribute>'")
        if "args" in case and not isinstance(case["args"], list):
            raise UsageError(f"{source}: case {name!r}: 'args' must be a list")
        if "kwargs" in case and not (isinstance(case["kwargs"], dict) or callable(case["kwargs"])):
            raise UsageError(f"{source}: case {name!r}: 'kwargs' must be an object")
        size = case.get("reference_size", {})
        if not isinstance(size, dict):
            raise UsageError(f"{source}: case {name!r}: 'reference_size' must be an object")
        out.append(case)
    return out


def load_registry(path: Path | None) -> list[Case]:
    if path is None:
        return _validate(BUILTIN, "built-in registry")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except OSError as err:
        raise UsageError(f"{path}: cannot read the registry: {err.strerror}") from None
    except (json.JSONDecodeError, UnicodeDecodeError) as err:
        raise UsageError(f"{path}: not valid JSON: {err}") from None
    if not isinstance(document, dict) or "cases" not in document:
        raise UsageError(f"{path}: the registry must be an object with a 'cases' list")
    return _validate(document["cases"], str(path))


def describe(case: Case) -> Case:
    module, function = case["name"].split(".", 1)
    return {
        "name": case["name"],
        "module": module,
        "function": function,
        "kind": case["kind"],
        "reference_size": case.get("reference_size", {}),
        "budget_ms": BUDGET_MS[case["kind"]],
    }


def resolve(case: Case) -> tuple[Callable[..., Any], list[Any], dict[str, Any]]:
    module_name, attribute = case["callable"].split(":", 1)
    try:
        target = getattr(importlib.import_module(module_name), attribute)
    except ImportError as err:
        raise UsageError(f"case {case['name']!r}: cannot import {module_name!r}: {err}") from None
    except AttributeError:
        raise UsageError(f"case {case['name']!r}: {module_name!r} has no attribute {attribute!r}") from None
    kwargs = case.get("kwargs", {})
    return target, list(case.get("args", [])), kwargs() if callable(kwargs) else dict(kwargs)


def run_case(case: Case, repeat: int) -> Case:
    target, args, kwargs = resolve(case)
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        target(*args, **kwargs)  # warm-up (lazy table reads, caches)
        samples = []
        for _ in range(repeat):
            start = time.perf_counter()
            target(*args, **kwargs)
            samples.append((time.perf_counter() - start) * 1000.0)
    median = statistics.median(samples)
    budget = BUDGET_MS[case["kind"]]
    return {"name": case["name"], "repeat": repeat, "median_ms": median, "budget_ms": budget, "passed": median <= budget}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true")
    mode.add_argument("--run", metavar="NAME")
    mode.add_argument("--check", action="store_true")
    ap.add_argument("--repeat", type=int, default=DEFAULT_REPEAT)
    ap.add_argument("--registry", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv[1:])
    sys.path.insert(0, str(ROOT / "src"))
    try:
        if not 1 <= args.repeat <= MAX_REPEAT:
            raise UsageError(f"--repeat must be between 1 and {MAX_REPEAT}, got {args.repeat}")
        cases = load_registry(args.registry)
        if args.list:
            out: Any = [describe(c) for c in cases]
            print(json.dumps(out, indent=2) if args.json else "\n".join(f"{c['name']}  {c['kind']}  {c['budget_ms']} ms" for c in out))
            return 0
        if args.run:
            match = [c for c in cases if c["name"] == args.run]
            if not match:
                raise UsageError(f"unknown case {args.run!r}; use --list")
            result = run_case(match[0], args.repeat)
            print(json.dumps(result) if args.json else f"{result['name']}: median {result['median_ms']:.4f} ms (budget {result['budget_ms']} ms)")
            return 0
        results = [run_case(c, args.repeat) for c in cases]
        ok = all(r["passed"] for r in results)
        if args.json:
            print(json.dumps({"results": results, "passed": ok}, indent=2))
        else:
            for r in results:
                print(f"{'ok  ' if r['passed'] else 'FAIL'} {r['name']}: {r['median_ms']:.4f} ms (budget {r['budget_ms']} ms)")
        return 0 if ok else 1
    except UsageError as err:
        print(f"bench: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
