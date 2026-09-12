"""Fixed numerical probes from authenticated R2 V4 source; not a movie experiment."""
import numpy as np

def smoothstep5(x: np.ndarray) -> np.ndarray:
    y = np.clip(np.asarray(x, dtype=float), 0.0, 1.0)
    return y**3 * (10.0 - 15.0 * y + 6.0 * y**2)

def old_window(tau: np.ndarray) -> np.ndarray:
    """Compact C2 plateau: zero >=-6 or <=-31; one on [-29,-10]."""
    tau = np.asarray(tau, dtype=float)
    return smoothstep5((tau + 31.0) / 2.0) * smoothstep5((-tau - 6.0) / 4.0)

def background_scene(family: str, pars: dict[str, float], r: np.ndarray, p: np.ndarray, t: np.ndarray) -> np.ndarray:
    phase = pars["phase"] + pars["speed"] * t
    if family == "single_hotspot":
        radial = np.exp(-0.5 * ((r - pars["r0"]) / pars["rw"]) ** 2)
        return pars["amp"] * radial * np.exp(pars["kappa"] * (np.cos(p - phase) - 1.0))
    if family == "double_hotspot":
        radial1 = np.exp(-0.5 * ((r - pars["r0"]) / pars["rw"]) ** 2)
        radial2 = np.exp(-0.5 * ((r - pars["r1"]) / pars["rw1"]) ** 2)
        h1 = radial1 * np.exp(pars["kappa"] * (np.cos(p - phase) - 1.0))
        h2 = radial2 * np.exp(pars["kappa1"] * (np.cos(p - phase - pars["offset"]) - 1.0))
        return pars["amp"] * (h1 + pars["ratio"] * h2) / (1.0 + pars["ratio"])
    if family == "flare_drift":
        env = 0.32 + 0.68 * np.exp(-0.5 * ((t + 8.0) / pars["st"]) ** 2)
        rc = pars["r0"] + pars["drdt"] * (t + 14.0)
        return pars["amp"] * env * np.exp(
            -0.5 * ((r - rc) / pars["rw"]) ** 2
            + pars["kappa"] * (np.cos(p - phase) - 1.0)
        )
    raise KeyError(family)

def draw_background(family: str, rng: np.random.Generator) -> dict[str, float]:
    base = {
        "phase": float(rng.uniform(-np.pi, np.pi)),
        "speed": float(rng.uniform(0.035, 0.09)),
        "r0": float(rng.uniform(7.5, 11.2)),
        "rw": float(rng.uniform(0.8, 1.4)),
        "kappa": float(rng.uniform(1.4, 2.8)),
        "amp": float(rng.uniform(0.12, 0.24)),
    }
    if family == "double_hotspot":
        base.update(
            r1=float(rng.uniform(8.8, 12.2)),
            rw1=float(rng.uniform(0.8, 1.4)),
            kappa1=float(rng.uniform(1.2, 2.6)),
            offset=float(rng.uniform(1.5, 3.5)),
            ratio=float(rng.uniform(0.55, 0.9)),
        )
    elif family == "flare_drift":
        base.update(st=float(rng.uniform(8.0, 12.0)), drdt=float(rng.uniform(-0.04, 0.04)))
    return base

def draw_feature_pair(family: str, rng: np.random.Generator) -> dict[str, float]:
    p = {
        "phase": float(rng.uniform(-np.pi, np.pi)),
        "amp": float(rng.uniform(0.35, 0.55)),
        "r0": float(rng.uniform(7.3, 11.7)),
        "rw": float(rng.uniform(0.30, 0.60)),
        "kappa": float(rng.uniform(9.0, 15.0)),
        "speed": float(rng.uniform(0.05, 0.16)),
        "dr": float(rng.uniform(0.25, 0.70)),
        "bend": float(rng.uniform(0.15, 0.50)),
        "delta": float(rng.uniform(0.65, 1.35)),
        "shear": float(rng.uniform(0.35, 0.80)),
        "sep": float(rng.uniform(0.50, 1.10)),
    }
    return p

def feature_movie(family: str, pars: dict[str, float], sibling: int, r: np.ndarray, p: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Positive old feature. sibling is -1 or +1 and selects a natural alternative."""
    s = float(sibling)
    win = old_window(t)
    amp = pars["amp"]
    phase0 = pars["phase"] + pars["speed"] * (t + 18.0)
    if family == "narrow_hotspot":
        rc = pars["r0"] + 0.18 * pars["dr"] * np.sin(0.12 * (t + 18.0))
        pc = phase0 + s * 0.5 * pars["delta"]
        return amp * win * np.exp(-0.5 * ((r - rc) / pars["rw"]) ** 2 + pars["kappa"] * (np.cos(p - pc) - 1.0))
    if family == "shearing_spiral":
        pc = phase0 + s * pars["shear"] * (r - pars["r0"])
        return amp * win * np.exp(-0.5 * ((r - pars["r0"]) / pars["rw"]) ** 2 + pars["kappa"] * (np.cos(p - pc) - 1.0))
    if family == "split_merge":
        sep = pars["sep"] * (0.5 + 0.5 * np.cos(np.pi * (t + 18.0) / 12.0))
        axis = phase0 + (0.0 if sibling < 0 else 0.5 * np.pi)
        h1 = np.exp(-0.5 * ((r - pars["r0"]) / pars["rw"]) ** 2 + pars["kappa"] * (np.cos(p - axis - sep) - 1.0))
        h2 = np.exp(-0.5 * ((r - pars["r0"]) / pars["rw"]) ** 2 + pars["kappa"] * (np.cos(p - axis + sep) - 1.0))
        return amp * win * 0.5 * (h1 + h2)
    if family == "radial_plume":
        rc = pars["r0"] + s * pars["dr"] * np.tanh((t + 18.0) / 6.0)
        pc = phase0 + s * pars["bend"] * (r - rc)
        width = pars["rw"] * (1.0 + 0.25 * np.sin(0.12 * (t + 18.0)))
        return amp * win * np.exp(-0.5 * ((r - rc) / width) ** 2 + pars["kappa"] * (np.cos(p - pc) - 1.0))
    raise KeyError(family)

def specifications(seed):
    rng=np.random.default_rng(seed)
    out=[dict(id='constant',kind='constant')]
    for family in ('single_hotspot','double_hotspot','flare_drift'):
        for i in range(8):
            out.append(dict(id=f'background_{family}_{i}',kind='background',family=family,params=draw_background(family,rng)))
    for family in ('narrow_hotspot','shearing_spiral','split_merge','radial_plume'):
        for i in range(8):
            pars=draw_feature_pair(family,rng)
            for sibling in (-1,1):
                out.append(dict(id=f'feature_{family}_{i}_{sibling}',kind='feature',family=family,params=pars,sibling=sibling))
    return out

def make(spec):
    if spec['kind']=='constant':return lambda r,p,t:np.ones_like(r)
    if spec['kind']=='background':return lambda r,p,t:background_scene(spec['family'],spec['params'],r,p,t)
    return lambda r,p,t:feature_movie(spec['family'],spec['params'],spec['sibling'],r,p,t)
