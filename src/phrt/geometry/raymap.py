"""The registered RayMap record and its HDF5 schema.

One file per (geometry, order, profile).  The schema is the contract between
the physics environment, which owns AART and writes these files, and the
analysis environment, which owns the operators and only ever reads them.  It
depends on nothing but numpy and h5py so both environments can import it.

Conventions, stated once and enforced here
------------------------------------------
``delay``
    Retarded age in units of GM/c^3, **non-negative, increasing into the
    past**, measured from the most recent emission the map contains.  AART
    reports a Boyer-Lindquist coordinate time ``t`` that is large and negative
    (the photon left the source long before it reached the observer at t=0),
    and deeper orders reach further back.  The conversion is

        delay = t_reference - t_aart,     t_reference = max over the map of t

    so delay = 0 is the most recent emission and larger delay is older.  This
    matches ``phrt.operators.structured``, where order n samples ages
    [n*D, n*D+W), and is the *opposite* sign from AART's raw ``t``.

``source_phi``
    Wrapped to [0, 2*pi).  AART returns an unwrapped winding angle that
    accumulates over half-orbits, which is the right thing for tracing and the
    wrong thing for evaluating an azimuthal Fourier basis.  The unwrapped value
    is preserved as ``winding_phi`` so nothing is lost.

``pixel_area``
    Quadrature weight per ray in units of M^2. For AART's Cartesian per-band
    grid this is dx_n^2, constant within a band and different between bands.
    Never assume a uniform area across orders: the adaptive grid uses a
    different dx for every lensing band, and treating the point count as the
    weight silently reweights the deep orders by orders of magnitude.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

SCHEMA_VERSION = "phrt-raymap/1"

FIELDS = ("alpha", "beta", "source_r", "source_phi", "winding_phi", "delay",
          "coordinate_time", "redshift", "transfer_weight", "pixel_area",
          "radial_sign", "valid")


@dataclass(frozen=True)
class RayMap:
    geometry_id: str
    order: int
    spin: float
    inclination_deg: float
    profile: str
    alpha: np.ndarray
    beta: np.ndarray
    source_r: np.ndarray
    source_phi: np.ndarray
    winding_phi: np.ndarray
    delay: np.ndarray
    coordinate_time: np.ndarray
    redshift: np.ndarray
    transfer_weight: np.ndarray
    pixel_area: np.ndarray
    radial_sign: np.ndarray
    valid: np.ndarray
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        n = self.alpha.size
        for name in FIELDS:
            arr = getattr(self, name)
            if arr.size != n:
                raise ValueError(f"{name} has {arr.size} entries, expected {n}")
        if self.delay[self.valid].size and float(self.delay[self.valid].min()) < -1e-9:
            raise ValueError("delay must be non-negative on valid rays")

    @property
    def n_rays(self) -> int:
        return int(self.alpha.size)

    @property
    def n_valid(self) -> int:
        return int(self.valid.sum())

    def subset(self, sel: np.ndarray) -> "RayMap":
        d = {k: (v[sel] if isinstance(v, np.ndarray) else v)
             for k, v in asdict(self).items() if k != "metadata"}
        return RayMap(**d, metadata=dict(self.metadata))

    def summary(self) -> dict[str, Any]:
        v = self.valid
        def rng(a):
            return [float(np.min(a[v])), float(np.max(a[v]))] if v.any() else [float("nan")] * 2
        return {
            "geometry_id": self.geometry_id, "order": self.order,
            "spin": self.spin, "inclination_deg": self.inclination_deg,
            "profile": self.profile, "n_rays": self.n_rays, "n_valid": self.n_valid,
            "valid_fraction": self.n_valid / max(self.n_rays, 1),
            "source_r_range": rng(self.source_r),
            "delay_range": rng(self.delay),
            "redshift_range": rng(self.redshift),
            "pixel_area": float(np.unique(self.pixel_area)[0])
            if np.unique(self.pixel_area).size == 1 else -1.0,
            "total_quadrature_area": float(np.sum(self.pixel_area[v])),
        }


def write(rm: RayMap, path: str | Path) -> Path:
    import h5py

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(p, "w") as f:
        meta = f.create_group("meta")
        meta.attrs["schema"] = SCHEMA_VERSION
        meta.attrs["geometry_id"] = rm.geometry_id
        meta.attrs["order"] = rm.order
        meta.attrs["spin"] = rm.spin
        meta.attrs["inclination_deg"] = rm.inclination_deg
        meta.attrs["profile"] = rm.profile
        meta.attrs["convention_json"] = json.dumps({
            "delay": "retarded age, non-negative, increasing into the past, "
                     "delay = t_reference - t_aart with t_reference the maximum "
                     "coordinate time in the map",
            "source_phi": "wrapped to [0, 2pi); winding_phi keeps the unwrapped value",
            "pixel_area": "dx_n^2 in M^2, constant within a band, different between bands",
            "units": "length GM/c^2, time GM/c^3",
        })
        meta.attrs["metadata_json"] = json.dumps(rm.metadata, default=str)
        rays = f.create_group("rays")
        for name in FIELDS:
            rays.create_dataset(name, data=getattr(rm, name), compression="gzip",
                                compression_opts=4)
    return p


def read(path: str | Path) -> RayMap:
    import h5py

    with h5py.File(path, "r") as f:
        m = f["meta"].attrs
        if m["schema"] != SCHEMA_VERSION:
            raise ValueError(f"unexpected schema {m['schema']!r}")
        arrays = {k: f["rays"][k][:] for k in FIELDS}
        return RayMap(
            geometry_id=str(m["geometry_id"]), order=int(m["order"]),
            spin=float(m["spin"]), inclination_deg=float(m["inclination_deg"]),
            profile=str(m["profile"]),
            metadata=json.loads(m["metadata_json"]), **arrays)


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# registered validity rule
# ---------------------------------------------------------------------------
EMISSION_R_OUTER = 50.0
"""Outer edge of the modelled equatorial emission region, in M.

Declared before any pilot output was inspected.  Rays landing outside it are
not errors: they are photons that miss the source, and the declared source
model assigns them no emission.  AART returns source radii up to 1e5 M for
rays that graze the band edge, and admitting those would let a handful of rays
dominate every quadrature sum."""


def horizon_radius(spin: float) -> float:
    return float(1.0 + np.sqrt(max(1.0 - spin ** 2, 0.0)))


def validity(source_r: np.ndarray, source_phi: np.ndarray, coordinate_time: np.ndarray,
             spin: float, band_mask: np.ndarray,
             r_outer: float = EMISSION_R_OUTER) -> np.ndarray:
    """The registered validity rule, applied identically to every order.

    A ray is retained when it is inside its lensing band, all three landing
    coordinates are finite, and it lands within the declared emission annulus.
    No criterion here refers to agreement with anything, so it cannot be used
    to drop rays that disagree with a cross-check.
    """
    finite = np.isfinite(source_r) & np.isfinite(source_phi) & np.isfinite(coordinate_time)
    inside = (source_r > horizon_radius(spin)) & (source_r <= r_outer)
    return np.asarray(band_mask, dtype=bool) & finite & inside
