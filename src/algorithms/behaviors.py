from __future__ import annotations

import numpy as np


def ball_rolling(
    X,
    f,
    best,
    rng,
    **cfg,
) -> np.ndarray:
    """
    Ball rolling + dancing behavior of the original
    Dung Beetle Optimizer (DBO).

    Parameters
    ----------
    X : np.ndarray
        Current positions of the ball-rolling group,
        shape (n_agents, dim).

    f : np.ndarray
        Fitness values corresponding to X,
        shape (n_agents,).

    best : np.ndarray
        Global best position, shape (dim,).

    rng : np.random.Generator
        Random generator used for reproducibility.

    cfg :
        k : float
            Deflection coefficient, default 0.1.

        b : float
            Influence coefficient, default 0.3.

        X_prev : np.ndarray
            Previous positions. If not supplied, X is used.

        worst : np.ndarray
            Worst position of the whole population.

        obstacle_prob : float
            Probability that an agent encounters an obstacle.
            Default 0.1.

        obstacle_mask : np.ndarray
            Optional boolean mask indicating obstacles.

    Returns
    -------
    np.ndarray
        New candidate positions.
    """

    X = np.asarray(X, dtype=float)
    f = np.asarray(f, dtype=float)
    best = np.asarray(best, dtype=float)

    if X.ndim != 2:
        raise ValueError("X must have shape (n_agents, dim)")

    n_agents, dim = X.shape

    if f.shape != (n_agents,):
        raise ValueError(
            f"f must have shape ({n_agents},), got {f.shape}"
        )

    if best.shape != (dim,):
        raise ValueError(
            f"best must have shape ({dim},), got {best.shape}"
        )

    # Original DBO parameters.
    k = float(cfg.get("k", 0.1))
    b = float(cfg.get("b", 0.3))

    # Historical position required by Eq. (1) and Eq. (2).
    # Keep the old fallback to preserve current dbo.py integration.
    X_prev = np.asarray(
        cfg.get("X_prev", X),
        dtype=float,
    )

    if X_prev.shape != X.shape:
        raise ValueError(
            f"X_prev must have shape {X.shape}, got {X_prev.shape}"
        )

    # ---------------------------------------------------------
    # FIX:
    # Use the population-wide worst position passed by dbo.py.
    #
    # dbo.py calls:
    #
    #     ball_rolling(..., worst=worst_x, ...)
    #
    # If worst is not supplied, fall back to the worst agent
    # inside the current group for standalone behavior tests.
    # ---------------------------------------------------------
    worst_cfg = cfg.get("worst")

    if worst_cfg is None:
        # Original DBO is formulated for minimization:
        # larger fitness means worse solution.
        worst = X[np.argmax(f)].copy()
    else:
        worst = np.asarray(
            worst_cfg,
            dtype=float,
        )

        if worst.shape != (dim,):
            raise ValueError(
                f"worst must have shape ({dim},), "
                f"got {worst.shape}"
            )

    # alpha = +1 or -1
    alpha = rng.choice(
        np.array([-1.0, 1.0]),
        size=(n_agents, 1),
    )

    # Eq. (1): ball rolling
    delta_x = np.abs(X - worst)

    rolled = (
        X
        + alpha * k * X_prev
        + b * delta_x
    )

    # Determine which agents encounter obstacles.
    obstacle_mask_cfg = cfg.get("obstacle_mask")

    if obstacle_mask_cfg is not None:
        obstacle_mask = np.asarray(
            obstacle_mask_cfg,
            dtype=bool,
        )

        if obstacle_mask.shape != (n_agents,):
            raise ValueError(
                "obstacle_mask must have shape "
                f"({n_agents},), got {obstacle_mask.shape}"
            )

    else:
        obstacle_prob = float(
            cfg.get("obstacle_prob", 0.1)
        )

        if not 0.0 <= obstacle_prob <= 1.0:
            raise ValueError(
                "obstacle_prob must be in [0, 1]"
            )

        obstacle_mask = (
            rng.random(n_agents)
            < obstacle_prob
        )

    # Eq. (2): dancing behavior
    theta = rng.uniform(
        0.0,
        np.pi,
        size=(n_agents, 1),
    )

    # tan(theta) becomes unstable near pi / 2.
    cos_theta = np.cos(theta)

    invalid_angle = (
        np.abs(cos_theta) < 1e-12
    )

    safe_theta = np.where(
        invalid_angle,
        0.0,
        theta,
    )

    tan_theta = np.tan(safe_theta)

    tan_theta = np.where(
        invalid_angle,
        0.0,
        tan_theta,
    )

    danced = (
        X
        + tan_theta
        * np.abs(X - X_prev)
    )

    result = np.where(
        obstacle_mask[:, None],
        danced,
        rolled,
    )

    return result


def reproduction(
    X,
    best,
    lb,
    ub,
    t,
    max_iter,
    rng,
    **cfg,
) -> np.ndarray:
    """
    Reproduction behavior of DBO.

    R = 1 - t / max_iter

    Lb* = max(best * (1 - R), lb)
    Ub* = min(best * (1 + R), ub)

    B_i(t+1)
        = best
          + b1 * (B_i - Lb*)
          + b2 * (B_i - Ub*)
    """

    X = np.asarray(X, dtype=float)
    best = np.asarray(best, dtype=float)

    if X.ndim != 2:
        raise ValueError(
            "X must have shape (n_agents, dim)"
        )

    _, dim = X.shape

    if best.shape != (dim,):
        raise ValueError(
            f"best must have shape ({dim},), got {best.shape}"
        )

    lb = np.asarray(lb, dtype=float)
    ub = np.asarray(ub, dtype=float)

    if lb.ndim == 0:
        lb = np.full(dim, float(lb))

    if ub.ndim == 0:
        ub = np.full(dim, float(ub))

    if lb.shape != (dim,):
        raise ValueError(
            f"lb must have shape ({dim},), got {lb.shape}"
        )

    if ub.shape != (dim,):
        raise ValueError(
            f"ub must have shape ({dim},), got {ub.shape}"
        )

    if max_iter <= 0:
        raise ValueError(
            "max_iter must be greater than 0"
        )

    # Local best may be supplied by the optimizer.
    local_best = np.asarray(
        cfg.get("local_best", best),
        dtype=float,
    )

    if local_best.shape != (dim,):
        raise ValueError(
            f"local_best must have shape ({dim},), "
            f"got {local_best.shape}"
        )

    R = 1.0 - float(t) / float(max_iter)
    R = np.clip(R, 0.0, 1.0)

    # Eq. (3)
    spawn_lb = np.maximum(
        local_best * (1.0 - R),
        lb,
    )

    spawn_ub = np.minimum(
        local_best * (1.0 + R),
        ub,
    )

    # Independent random vectors.
    b1 = rng.random(X.shape)
    b2 = rng.random(X.shape)

    # Eq. (4)
    offspring = (
        local_best
        + b1 * (X - spawn_lb)
        + b2 * (X - spawn_ub)
    )

    return offspring


def foraging(
    X,
    best,
    lb,
    ub,
    t,
    max_iter,
    rng,
    **cfg,
) -> np.ndarray:
    """
    Foraging behavior of DBO.

    R = 1 - t / max_iter

    Lbb = max(best * (1 - R), lb)
    Ubb = min(best * (1 + R), ub)

    x_i(t+1)
        = x_i(t)
          + C1 * (x_i - Lbb)
          + C2 * (x_i - Ubb)
    """

    X = np.asarray(X, dtype=float)
    best = np.asarray(best, dtype=float)

    if X.ndim != 2:
        raise ValueError(
            "X must have shape (n_agents, dim)"
        )

    n_agents, dim = X.shape

    if best.shape != (dim,):
        raise ValueError(
            f"best must have shape ({dim},), got {best.shape}"
        )

    lb = np.asarray(lb, dtype=float)
    ub = np.asarray(ub, dtype=float)

    if lb.ndim == 0:
        lb = np.full(dim, float(lb))

    if ub.ndim == 0:
        ub = np.full(dim, float(ub))

    if lb.shape != (dim,):
        raise ValueError(
            f"lb must have shape ({dim},), got {lb.shape}"
        )

    if ub.shape != (dim,):
        raise ValueError(
            f"ub must have shape ({dim},), got {ub.shape}"
        )

    if max_iter <= 0:
        raise ValueError(
            "max_iter must be greater than 0"
        )

    R = 1.0 - float(t) / float(max_iter)
    R = np.clip(R, 0.0, 1.0)

    # Eq. (5)
    forage_lb = np.maximum(
        best * (1.0 - R),
        lb,
    )

    forage_ub = np.minimum(
        best * (1.0 + R),
        ub,
    )

    # C1 is Gaussian.
    C1 = rng.normal(
        loc=0.0,
        scale=1.0,
        size=(n_agents, 1),
    )

    # C2 is a uniform random vector.
    C2 = rng.random(X.shape)

    # Eq. (6)
    result = (
        X
        + C1 * (X - forage_lb)
        + C2 * (X - forage_ub)
    )

    return result


def thieving(
    X,
    best,
    rng,
    **cfg,
) -> np.ndarray:
    """
    Thieving behavior of DBO.

    x_i(t+1)
        = best
          + S * g *
            (
                |x_i - local_best|
                +
                |x_i - best|
            )
    """

    X = np.asarray(X, dtype=float)
    best = np.asarray(best, dtype=float)

    if X.ndim != 2:
        raise ValueError(
            "X must have shape (n_agents, dim)"
        )

    _, dim = X.shape

    if best.shape != (dim,):
        raise ValueError(
            f"best must have shape ({dim},), got {best.shape}"
        )

    # Original DBO parameter.
    S = float(
        cfg.get("S", 0.5)
    )

    local_best = np.asarray(
        cfg.get("local_best", best),
        dtype=float,
    )

    if local_best.shape != (dim,):
        raise ValueError(
            f"local_best must have shape ({dim},), "
            f"got {local_best.shape}"
        )

    # Gaussian random vector.
    g = rng.normal(
        loc=0.0,
        scale=1.0,
        size=X.shape,
    )

    # Eq. (7)
    result = (
        best
        + S
        * g
        * (
            np.abs(X - local_best)
            + np.abs(X - best)
        )
    )

    return result


# ============================================================
# ORIGINAL DBO FORMULAS
# ============================================================
#
# Eq. (1) - Ball rolling
#
# x_i(t+1)
#   = x_i(t)
#     + alpha * k * x_i(t-1)
#     + b * |x_i(t) - X_w|
#
#
# Eq. (2) - Dancing
#
# x_i(t+1)
#   = x_i(t)
#     + tan(theta)
#       * |x_i(t) - x_i(t-1)|
#
#
# Eq. (3) - Reproduction region
#
# R = 1 - t / T_max
#
# Lb* = max(X* * (1 - R), Lb)
# Ub* = min(X* * (1 + R), Ub)
#
#
# Eq. (4) - Reproduction
#
# B_i(t+1)
#   = X*
#     + b1 * (B_i(t) - Lb*)
#     + b2 * (B_i(t) - Ub*)
#
#
# Eq. (5) - Foraging region
#
# Lbb = max(X_best * (1 - R), Lb)
# Ubb = min(X_best * (1 + R), Ub)
#
#
# Eq. (6) - Foraging
#
# x_i(t+1)
#   = x_i(t)
#     + C1 * (x_i(t) - Lbb)
#     + C2 * (x_i(t) - Ubb)
#
#
# Eq. (7) - Thieving
#
# x_i(t+1)
#   = X_best
#     + S * g *
#       (
#           |x_i(t) - X*|
#           +
#           |x_i(t) - X_best|
#       )
#
#
# Original baseline parameters:
#
# k = 0.1
# b = 0.3
# S = 0.5
#
# Notes:
# - All randomness comes from the provided numpy Generator.
# - Population splitting belongs to dbo.py.
# - Boundary clipping belongs to dbo.py.
# - Dimension is obtained from X.shape.
# ============================================================