# src/algorithms/behaviors.py

from __future__ import annotations

import numpy as np


def ball_rolling(
    X: np.ndarray,
    f: np.ndarray,
    best: np.ndarray,
    rng: np.random.Generator,
    **cfg,
) -> np.ndarray:
    """
    Ball-rolling + dancing behavior of the original DBO.

    Parameters
    ----------
    X:
        Current positions, shape (n_agents, dim).
    f:
        Fitness values corresponding to X.
        Assumes minimization, therefore argmax(f) is the worst agent.
    best:
        Current global best position. Kept in the signature required by the team.
    rng:
        NumPy random Generator.
    cfg:
        k: deflection coefficient, default 0.1.
        b: light-intensity coefficient, default 0.3.
        X_prev: positions of these agents at t-1. If omitted, X is used.
        obstacle_prob: probability of switching to dancing behavior.
    """
    X = np.asarray(X, dtype=float)
    f = np.asarray(f, dtype=float)

    if X.ndim != 2:
        raise ValueError("X must have shape (n_agents, dim)")

    if X.shape[0] == 0:
        return X.copy()

    if f.shape[0] != X.shape[0]:
        raise ValueError("f must contain one fitness value per agent")

    k = float(cfg.get("k", 0.1))
    b = float(cfg.get("b", 0.3))

    # Historical position required by Eq. (1) and Eq. (2).
    X_prev = np.asarray(cfg.get("X_prev", X), dtype=float)

    if X_prev.shape != X.shape:
        raise ValueError("X_prev must have the same shape as X")

    # Original DBO is formulated for minimization.
    worst = X[np.argmax(f)]

    # alpha = +1 or -1.
    alpha = rng.choice(
        np.array([-1.0, 1.0]),
        size=(X.shape[0], 1),
    )

    # Eq. (1): normal ball rolling.
    delta_x = np.abs(X - worst)

    rolled = X + alpha * k * X_prev + b * delta_x

    # Dancing behavior, Eq. (2).
    #
    # TASK_WEEK4 asks for the obstacle branch. Since the fixed signature does
    # not provide an obstacle flag, expose its probability through cfg.
    obstacle_prob = float(cfg.get("obstacle_prob", 0.1))

    obstacle_mask = rng.random((X.shape[0], 1)) < obstacle_prob

    theta = rng.uniform(0.0, np.pi, size=(X.shape[0], 1))

    # The paper specifies no movement at theta = 0, pi/2, pi.
    # Exact equality is essentially impossible with a continuous RNG, but
    # protect the pi/2 singularity numerically.
    tan_theta = np.tan(theta)

    singular = np.isclose(
        np.cos(theta),
        0.0,
        atol=1e-12,
    )

    tan_theta = np.where(singular, 0.0, tan_theta)

    danced = X + tan_theta * np.abs(X - X_prev)

    return np.where(obstacle_mask, danced, rolled)


def reproduction(
    X: np.ndarray,
    best: np.ndarray,
    lb,
    ub,
    t: int,
    max_iter: int,
    rng: np.random.Generator,
    **cfg,
) -> np.ndarray:
    """
    Reproduction / brood-ball behavior.

    The spawning region contracts around the current local best:

        R = 1 - t / max_iter

        Lb* = max(X* * (1 - R), lb)
        Ub* = min(X* * (1 + R), ub)

        B_i(t+1)
            = X*
            + b1 * (B_i(t) - Lb*)
            + b2 * (B_i(t) - Ub*)

    b1 and b2 are independent random vectors.
    """
    X = np.asarray(X, dtype=float)
    best = np.asarray(best, dtype=float)

    if X.ndim != 2:
        raise ValueError("X must have shape (n_agents, dim)")

    if X.shape[0] == 0:
        return X.copy()

    if max_iter <= 0:
        raise ValueError("max_iter must be positive")

    lb = np.broadcast_to(
        np.asarray(lb, dtype=float),
        (X.shape[1],),
    )
    ub = np.broadcast_to(
        np.asarray(ub, dtype=float),
        (X.shape[1],),
    )

    # Paper uses the current local best X* for reproduction.
    # If dbo.py has one, pass local_best=... through cfg.
    local_best = np.asarray(
        cfg.get("local_best", best),
        dtype=float,
    )

    R = 1.0 - float(t) / float(max_iter)
    R = np.clip(R, 0.0, 1.0)

    spawning_lb = np.maximum(
        local_best * (1.0 - R),
        lb,
    )

    spawning_ub = np.minimum(
        local_best * (1.0 + R),
        ub,
    )

    # Independent random vectors b1 and b2.
    b1 = rng.random(X.shape)
    b2 = rng.random(X.shape)

    children = (
        local_best
        + b1 * (X - spawning_lb)
        + b2 * (X - spawning_ub)
    )

    return children


def foraging(
    X: np.ndarray,
    best: np.ndarray,
    lb,
    ub,
    t: int,
    max_iter: int,
    rng: np.random.Generator,
    **cfg,
) -> np.ndarray:
    """
    Foraging behavior of small dung beetles.

        R = 1 - t / max_iter

        Lb^b = max(X^b * (1 - R), lb)
        Ub^b = min(X^b * (1 + R), ub)

        x_i(t+1)
            = x_i(t)
            + C1 * (x_i(t) - Lb^b)
            + C2 * (x_i(t) - Ub^b)

    C1 follows a Gaussian distribution.
    C2 is a random vector in (0, 1).
    """
    X = np.asarray(X, dtype=float)
    best = np.asarray(best, dtype=float)

    if X.ndim != 2:
        raise ValueError("X must have shape (n_agents, dim)")

    if X.shape[0] == 0:
        return X.copy()

    if max_iter <= 0:
        raise ValueError("max_iter must be positive")

    lb = np.broadcast_to(
        np.asarray(lb, dtype=float),
        (X.shape[1],),
    )
    ub = np.broadcast_to(
        np.asarray(ub, dtype=float),
        (X.shape[1],),
    )

    R = 1.0 - float(t) / float(max_iter)
    R = np.clip(R, 0.0, 1.0)

    forage_lb = np.maximum(
        best * (1.0 - R),
        lb,
    )

    forage_ub = np.minimum(
        best * (1.0 + R),
        ub,
    )

    # C1 is normally distributed.
    # One random value for each agent is sufficient and broadcasts over dim.
    C1 = rng.normal(
        loc=0.0,
        scale=1.0,
        size=(X.shape[0], 1),
    )

    # C2 is a random 1 x D vector in the original formulation.
    # Generate per-agent vectors to keep all agents stochastic and vectorized.
    C2 = rng.random(X.shape)

    return (
        X
        + C1 * (X - forage_lb)
        + C2 * (X - forage_ub)
    )


def thieving(
    X: np.ndarray,
    best: np.ndarray,
    rng: np.random.Generator,
    **cfg,
) -> np.ndarray:
    """
    Thieving behavior.

        x_i(t+1)
            = Xb
            + S * g *
              (|x_i(t) - X*| + |x_i(t) - Xb|)

    where:
        Xb = global best,
        X* = current local best,
        g  = Gaussian random vector,
        S  = 0.5 in the original DBO.
    """
    X = np.asarray(X, dtype=float)
    best = np.asarray(best, dtype=float)

    if X.ndim != 2:
        raise ValueError("X must have shape (n_agents, dim)")

    if X.shape[0] == 0:
        return X.copy()

    S = float(cfg.get("S", 0.5))

    # Eq. (7) needs both global-best Xb and local-best X*.
    # Because the team's signature exposes only `best`, allow dbo.py to
    # provide the local best via cfg.
    local_best = np.asarray(
        cfg.get("local_best", best),
        dtype=float,
    )

    g = rng.normal(
        loc=0.0,
        scale=1.0,
        size=X.shape,
    )

    distance = (
        np.abs(X - local_best)
        + np.abs(X - best)
    )

    return best + S * g * distance


# ---------------------------------------------------------------------------
# Xue & Shen (2023), original DBO formulas
#
# Eq. (1) Ball rolling:
# x_i(t+1) = x_i(t) + alpha*k*x_i(t-1) + b*|x_i(t) - Xw|
#
# Eq. (2) Dancing:
# x_i(t+1) = x_i(t)
#            + tan(theta)*|x_i(t) - x_i(t-1)|
#
# Eq. (3)-(4) Reproduction:
# R = 1 - t/Tmax
# Lb* = max(X*(1-R), Lb)
# Ub* = min(X*(1+R), Ub)
# B_i(t+1) = X*
#            + b1*(B_i(t)-Lb*)
#            + b2*(B_i(t)-Ub*)
#
# Eq. (5)-(6) Foraging:
# Lb^b = max(Xb(1-R), Lb)
# Ub^b = min(Xb(1+R), Ub)
# x_i(t+1) = x_i(t)
#            + C1*(x_i(t)-Lb^b)
#            + C2*(x_i(t)-Ub^b)
#
# Eq. (7) Thieving:
# x_i(t+1) = Xb
#            + S*g*(|x_i(t)-X*| + |x_i(t)-Xb|)
#
# Recommended original DBO parameters:
# k = 0.1, b = 0.3, S = 0.5
# ---------------------------------------------------------------------------