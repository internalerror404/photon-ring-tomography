"""Family-stratified two-bridge SMC with bounded hit-and-run slice mutation.

The target lives in the physical unit cube. The initial proposal is the exact
normalized logit-space defensive Student mixture inherited from experiment 005,
transformed to a density in u-space. Mutation is reversible for each frozen
intermediate target: directions are drawn from a fixed symmetric distribution,
then a standard bounded stepping-out/shrinkage slice update is performed along
the corresponding line. Families are never crossed inside a stratum.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import numpy as np
from scipy.special import expit, logit
import smc005

EPS = 1e-12
INTERIOR_EPS = 1e-10


def logq_u(proposal: smc005.Proposal, family: int, u: np.ndarray) -> float:
    """Proposal density with respect to Lebesgue measure on the unit cube."""
    uu = np.clip(np.asarray(u, float), INTERIOR_EPS, 1.0 - INTERIOR_EPS)
    y = logit(uu)
    # q_u(u) = q_y(logit(u)) * |dy/du|; smc005.logjac is log |du/dy|.
    return float(proposal.logq(family, y) - smc005.logjac(y))


def feasible_interval(u: np.ndarray, direction: np.ndarray) -> tuple[float, float]:
    """Largest line interval t for which 0 < u+t*d < 1 (up to EPS)."""
    lo, hi = -np.inf, np.inf
    for x, d in zip(np.asarray(u, float), np.asarray(direction, float)):
        if d > 0:
            lo = max(lo, (EPS - x) / d)
            hi = min(hi, ((1.0 - EPS) - x) / d)
        elif d < 0:
            lo = max(lo, ((1.0 - EPS) - x) / d)
            hi = min(hi, (EPS - x) / d)
    if not np.isfinite(lo) or not np.isfinite(hi) or not lo < 0.0 < hi:
        raise RuntimeError("invalid feasible slice interval")
    return float(lo), float(hi)


@dataclass
class EvalState:
    u: np.ndarray
    logq: float
    logLs: float
    logLn: float
    logtarget: float


class TargetCounter:
    def __init__(self, likelihood: Callable[[int, np.ndarray, bool], float]):
        self.likelihood = likelihood
        self.surrogate_calls = 0
        self.native_calls = 0

    def surrogate(self, family: int, u: np.ndarray) -> float:
        self.surrogate_calls += 1
        return float(self.likelihood(family, u, False))

    def native(self, family: int, u: np.ndarray) -> float:
        self.native_calls += 1
        return float(self.likelihood(family, u, True))


def _state(
    proposal: smc005.Proposal,
    counter: TargetCounter,
    family: int,
    u: np.ndarray,
    bridge: str,
    temperature: float,
    need_native: bool,
) -> EvalState:
    uu = np.clip(np.asarray(u, float), INTERIOR_EPS, 1.0 - INTERIOR_EPS)
    lq = logq_u(proposal, family, uu)
    ls = counter.surrogate(0, uu)
    ln = counter.native(0, uu) if need_native else np.nan
    if bridge == "proposal_to_surrogate":
        lt = (1.0 - temperature) * lq + temperature * ls
    elif bridge == "surrogate_to_native":
        if not np.isfinite(ln):
            raise RuntimeError("native target requested without native likelihood")
        lt = (1.0 - temperature) * ls + temperature * ln
    else:
        raise KeyError(bridge)
    if not np.isfinite(lt):
        raise RuntimeError("nonfinite intermediate target")
    return EvalState(uu, lq, ls, ln, float(lt))


def _direction(
    rng: np.random.Generator,
    dimension: int,
    move_index: int,
    full_chol: np.ndarray,
    block_chol: list[np.ndarray],
) -> tuple[np.ndarray, float, str]:
    """Frozen symmetric direction mixture: 2D blocks, full, then coordinate."""
    blocks = dimension // 2
    slot = move_index % (blocks + 2)
    d = np.zeros(dimension)
    if slot < blocks:
        sl = slice(2 * slot, 2 * slot + 2)
        d[sl] = block_chol[slot] @ rng.normal(size=2)
        width = 0.35
        kind = f"block{slot}"
    elif slot == blocks:
        d = full_chol @ rng.normal(size=dimension)
        width = 0.50
        kind = "full"
    else:
        j = int(rng.integers(dimension))
        d[j] = -1.0 if rng.random() < 0.5 else 1.0
        width = 0.25
        kind = f"coordinate{j}"
    norm = float(np.linalg.norm(d))
    if not np.isfinite(norm) or norm <= 0:
        raise RuntimeError("degenerate slice direction")
    return d / norm, width, kind


def line_slice_move(
    current: EvalState,
    proposal: smc005.Proposal,
    counter: TargetCounter,
    family: int,
    bridge: str,
    temperature: float,
    direction: np.ndarray,
    width: float,
    rng: np.random.Generator,
    max_steps_out: int = 8,
    max_shrink: int = 100,
) -> tuple[EvalState, dict]:
    """One reversible bounded line-slice transition using Neal stepping-out."""
    lower, upper = feasible_interval(current.u, direction)
    logheight = current.logtarget + float(np.log(rng.random()))
    # Randomly positioned initial interval and randomized finite stepping budget.
    left = max(lower, -rng.random() * width)
    right = min(upper, left + width)
    if right <= 0.0:
        right = min(upper, left + width)
    if left >= 0.0:
        left = max(lower, right - width)
    j = int(rng.integers(max_steps_out + 1))
    k = max_steps_out - j
    evaluations = 0
    step_left = 0
    step_right = 0

    while j > 0 and left > lower:
        cand = _state(proposal, counter, family, current.u + left * direction, bridge, temperature, bridge == "surrogate_to_native")
        evaluations += 1
        if cand.logtarget <= logheight:
            break
        left = max(lower, left - width)
        j -= 1
        step_left += 1
    while k > 0 and right < upper:
        cand = _state(proposal, counter, family, current.u + right * direction, bridge, temperature, bridge == "surrogate_to_native")
        evaluations += 1
        if cand.logtarget <= logheight:
            break
        right = min(upper, right + width)
        k -= 1
        step_right += 1

    initial_left, initial_right = left, right
    for shrink in range(max_shrink):
        rr = (float(rng.random()) + np.finfo(float).eps) / (1.0 + 2.0 * np.finfo(float).eps)
        t = float(left + (right - left) * rr)
        cand = _state(proposal, counter, family, current.u + t * direction, bridge, temperature, bridge == "surrogate_to_native")
        evaluations += 1
        if cand.logtarget >= logheight:
            return cand, {
                "evaluations": evaluations,
                "step_left": step_left,
                "step_right": step_right,
                "shrink": shrink,
                "initial_width": initial_right - initial_left,
                "feasible_width": upper - lower,
            }
        if t < 0.0:
            left = t
        else:
            right = t
    raise RuntimeError("slice shrinkage cap exhausted")


def run_slice_smc(
    proposal: smc005.Proposal,
    likelihood: Callable[[int, np.ndarray, bool], float],
    rng: np.random.Generator,
    preconditioner_u: np.ndarray,
    N: int = 128,
    passes: int = 1,
    max_stages: int = 80,
    cess: float = 0.8,
    writer=None,
) -> dict:
    """Two-bridge SMC with family-fixed hit-and-run slice mutation.

    The routine is intended for one normalized family stratum. The evidence is
    conditional on that family; family priors are combined outside this call.
    """
    Q = proposal
    if Q.F != 1 or Q.dim[0] != Q.D:
        raise ValueError("slice SMC requires one fixed family stratum")
    dim = int(Q.D)
    L = np.asarray(preconditioner_u, float)
    if L.shape != (dim, dim):
        raise ValueError("preconditioner shape")
    C = L @ L.T
    eig, vec = np.linalg.eigh((C + C.T) / 2.0)
    C = (vec * np.clip(eig, 1e-8, 4.0)) @ vec.T
    full_chol = np.linalg.cholesky((C + C.T) / 2.0)
    block_chol = []
    for block in range(dim // 2):
        sub = C[2 * block : 2 * block + 2, 2 * block : 2 * block + 2]
        block_chol.append(np.linalg.cholesky((sub + sub.T) / 2.0 + 1e-10 * np.eye(2)))

    counter = TargetCounter(likelihood)
    draws = [Q.one(rng) for _ in range(N)]
    families = np.array([f for f, _ in draws], int)
    if np.any(families != 0):
        raise RuntimeError("conditional proposal emitted unexpected family")
    u = np.clip(np.array([expit(y[:dim]) for _, y in draws]), INTERIOR_EPS, 1.0 - INTERIOR_EPS)
    lq = np.array([logq_u(Q, 0, row) for row in u])
    ls = np.array([counter.surrogate(0, row) for row in u])
    ln = np.full(N, np.nan)
    weights = np.ones(N) / N
    ancestors = np.arange(N)
    log_evidence = 0.0
    allstats = []
    slice_moves = 0
    slice_evaluations = 0
    slice_shrink = 0

    for bridge in ("proposal_to_surrogate", "surrogate_to_native"):
        if bridge == "surrogate_to_native":
            ix = smc005.resample(weights, rng)
            u = u[ix]
            lq = lq[ix]
            ls = ls[ix]
            ancestors = ancestors[ix]
            weights = np.ones(N) / N
            ln = np.array([counter.native(0, row) for row in u])
        temperature = 0.0
        for stage in range(max_stages):
            ratio = ls - lq if bridge == "proposal_to_surrogate" else ln - ls
            if not np.isfinite(ratio).all():
                raise RuntimeError("nonfinite bridge ratio")
            new_temperature = smc005.next_temperature(temperature, weights, ratio, cess)
            delta = new_temperature - temperature
            previous_weights = weights.copy()
            previous_ratio = ratio.copy()
            weights, increment = smc005.normalized(np.log(weights) + delta * ratio)
            log_evidence += increment
            pre_resample_ess = smc005.ess(weights)
            pre_resample_max = float(weights.max())
            resampling_index = np.arange(N)
            if new_temperature < 1.0:
                resampling_index = smc005.resample(weights, rng)
                u = u[resampling_index]
                lq = lq[resampling_index]
                ls = ls[resampling_index]
                ln = ln[resampling_index]
                ancestors = ancestors[resampling_index]
                weights = np.ones(N) / N

            moves_per_particle = passes * (dim // 2 + 2)
            stage_eval_before = counter.surrogate_calls + counter.native_calls
            stage_shrink = 0
            kinds = {}
            for i in range(N):
                if bridge == "proposal_to_surrogate":
                    current_target = (1.0 - new_temperature) * lq[i] + new_temperature * ls[i]
                else:
                    current_target = (1.0 - new_temperature) * ls[i] + new_temperature * ln[i]
                current = EvalState(u[i].copy(), lq[i], ls[i], ln[i], float(current_target))
                for move in range(moves_per_particle):
                    direction, width, kind = _direction(rng, dim, move, full_chol, block_chol)
                    current, rec = line_slice_move(
                        current,
                        Q,
                        counter,
                        0,
                        bridge,
                        new_temperature,
                        direction,
                        width,
                        rng,
                    )
                    kinds[kind] = kinds.get(kind, 0) + 1
                    slice_moves += 1
                    slice_evaluations += rec["evaluations"]
                    slice_shrink += rec["shrink"]
                    stage_shrink += rec["shrink"]
                u[i] = current.u
                lq[i] = current.logq
                ls[i] = current.logLs
                ln[i] = current.logLn

            unique = len({tuple(row) for row in u})
            stat = {
                "bridge": bridge,
                "stage": stage,
                "temperature_before": temperature,
                "temperature": new_temperature,
                "increment": increment,
                "logZ": log_evidence,
                "pre_resample_ess": pre_resample_ess,
                "pre_resample_max_weight": pre_resample_max,
                "slice_moves": N * moves_per_particle,
                "slice_target_evaluations": counter.surrogate_calls + counter.native_calls - stage_eval_before,
                "slice_shrink_steps": stage_shrink,
                "move_kinds": kinds,
                "unique_particles": unique,
                "initial_ancestors": len(np.unique(ancestors)),
            }
            if writer:
                writer(
                    stat,
                    {
                        "u": u.copy(),
                        "logq_u": lq.copy(),
                        "logLs": ls.copy(),
                        "logLn": ln.copy(),
                        "weights": weights.copy(),
                        "previous_weights": previous_weights,
                        "bridge_ratio_before": previous_ratio,
                        "resampling_index": resampling_index,
                        "ancestors": ancestors.copy(),
                    },
                )
            allstats.append(stat)
            temperature = new_temperature
            if temperature == 1.0:
                break
        if temperature != 1.0:
            raise RuntimeError("registered tempering stage cap")

    y = logit(np.clip(u, EPS, 1.0 - EPS))
    return {
        "families": np.zeros(N, int),
        "u": u,
        "x": y,
        "weights": weights,
        "logq_u": lq,
        "logLs": ls,
        "logLn": ln,
        "ancestors": ancestors,
        "log_evidence": log_evidence,
        "stats": allstats,
        "surrogate_calls": counter.surrogate_calls,
        "native_calls": counter.native_calls,
        "slice_moves": slice_moves,
        "slice_evaluations": slice_evaluations,
        "slice_shrink_steps": slice_shrink,
        "ess": smc005.ess(weights),
        "max_weight": float(weights.max()),
        "unique_particles": len({tuple(row) for row in u}),
        "initial_ancestors": len(np.unique(ancestors)),
    }
