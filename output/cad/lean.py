"""2D (YZ) rigid-body check of a bite resting on the clip rails, free to shift in Y and
lean about X (the stacking axis: a whole stack can lean together without its faces
sliding, so face friction does not stop it).

For each bite size: the gravity rest pose (lowest centre of mass, walls at ±BORE_W/2),
and the lowest point of the bite in that pose.  Used by verify.py §9.11 to show how far
below CUP_TOP_Z a leaning bite's bottom corner can hang when it reaches the receiver.
"""
import math
from functools import lru_cache
import numpy as np
from scipy.optimize import minimize_scalar
import params as P


def _outline(W, H, R, step=0.02):
    """Dense outline of a W x H rounded rectangle (corner radius R), centred on (0, 0)."""
    a, b = W / 2 - R, H / 2 - R
    corners = ((a, -b, -90), (a, b, 0), (-a, b, 90), (-a, -b, 180))
    arcs = []
    for cx, cz, t0 in corners:
        t = np.radians(np.linspace(t0, t0 + 90, max(8, int(math.pi / 2 * R / step))))
        arcs.append(np.c_[cx + R * np.cos(t), cz + R * np.sin(t)])
    pts = []
    for i, arc in enumerate(arcs):
        pts.append(arc)
        nxt = arcs[(i + 1) % 4][0]
        n = max(2, int(np.hypot(*(nxt - arc[-1])) / step))
        pts.append(np.linspace(arc[-1], nxt, n, endpoint=False)[1:])
    return np.vstack(pts)


def rail_profile(y):
    """Top of the support under the bite at |Y|: groove gap, rail R0.5 inner edge, rail top."""
    ay = np.abs(y)
    s = np.full_like(ay, P.BORE_BOT_Z)          # floor/groove region: far below any bite
    r, yi = P.RAIL_EDGE_R, P.RAIL_IN_Y
    m = (ay >= yi) & (ay < yi + r)
    s[m] = P.RAIL_TOP_Z - r + np.sqrt(np.maximum(r * r - (ay[m] - (yi + r)) ** 2, 0))
    s[ay >= yi + r] = P.RAIL_TOP_Z
    return s


def _pose(rp, y):
    """Centre height of the bite resting on the rails at shift y (None if it hits a wall)."""
    Y = rp[:, 0] + y
    hw = P.BORE_W / 2
    if Y.max() > hw + 1e-9 or Y.min() < -hw - 1e-9:
        return None
    zc = float(np.max(rail_profile(Y) - rp[:, 1]))
    return zc, zc + float(rp[:, 1].min()), float(Y[np.argmin(rp[:, 1])])


def _contacts(b: P.Bite, y, zc, th_deg, tol=2e-3, walls=None):
    """Exact contacts of the posed bite with the walls and the rails.  The rounded bite is its
    inner rectangle (W-2R x H-2R) grown by R, so every contact normal runs from the support to
    the nearest point of that rectangle.  Returns (name, Y, Z, unit normal into the bite)."""
    a, h = b.W / 2 - b.R, b.H / 2 - b.R
    c, s = math.cos(math.radians(th_deg)), math.sin(math.radians(th_deg))
    to_w = lambda u, v: (u * c - v * s + y, u * s + v * c + zc)
    to_l = lambda Y, Z: ((Y - y) * c + (Z - zc) * s, -(Y - y) * s + (Z - zc) * c)
    verts = [to_w(u, v) for u in (-a, a) for v in (-h, h)]
    hw = P.BORE_W / 2
    out = []
    # walls: walls=(touch -Y, touch +Y) from the y bounds of the search, else a tolerance
    vy = max(verts, key=lambda q: q[0])
    if (walls[1] if walls else vy[0] + b.R >= hw - tol):
        out.append(("wall+1", vy[0] + b.R, vy[1], (-1.0, 0.0)))
    vy = min(verts, key=lambda q: q[0])
    if (walls[0] if walls else vy[0] - b.R <= -hw + tol):
        out.append(("wall-1", vy[0] - b.R, vy[1], (1.0, 0.0)))
    low = min(verts, key=lambda q: q[1])                    # floor of the gap between the rails
    if abs(low[0]) < P.RAIL_IN_Y and low[1] - b.R <= P.BORE_BOT_Z + tol:
        out.append(("floor", low[0], P.BORE_BOT_Z, (0.0, 1.0)))
    r, yi = P.RAIL_EDGE_R, P.RAIL_IN_Y
    for side in (+1, -1):                                   # rail R0.5 edges, else the flat top
        E = (side * (yi + r), P.RAIL_TOP_Z - r)
        u, v = to_l(*E)
        Q = to_w(max(-a, min(a, u)), max(-h, min(h, v)))
        d = math.hypot(Q[0] - E[0], Q[1] - E[1])
        n = ((Q[0] - E[0]) / d, (Q[1] - E[1]) / d)
        if d - (b.R + r) < tol and n[1] >= 0 and side * n[0] <= 1e-9:
            out.append(("rail%+d" % side, E[0] + r * n[0], E[1] + r * n[1], n))
            continue
        low = min(verts, key=lambda q: q[1])                # lowest corner on the flat rail top
        if side * low[0] >= yi + r and abs(low[1] - b.R - P.RAIL_TOP_Z) < tol:
            out.append(("rail%+d" % side, low[0], P.RAIL_TOP_Z, (0.0, 1.0)))
    return out


def normal_forces(contacts, com):
    """Frictionless static equilibrium (2-D) under unit weight at com: the normal force at each
    contact, in units of the bite's weight.  With 4+ contacts the split is statically
    indeterminate: the largest total (the worst case for drag) is returned."""
    A = np.zeros((3, len(contacts)))
    for j, (_, y, z, (ny, nz)) in enumerate(contacts):
        A[0, j], A[1, j] = ny, nz
        A[2, j] = (y - com[0]) * nz - (z - com[1]) * ny     # moment about the CoM
    rhs = np.array([0.0, 1.0, 0.0])
    if len(contacts) > 3:
        from scipy.optimize import linprog
        r = linprog(-np.ones(len(contacts)), A_eq=A, b_eq=rhs, bounds=[(0, None)] * len(contacts))
        if r.status == 0:
            return r.x, float(np.abs(A @ r.x - rhs).max())
    sol, *_ = np.linalg.lstsq(A, rhs, rcond=None)
    return sol, float(np.abs(A @ sol - rhs).max())


def _rot(pts, th_deg):
    c, s = math.cos(math.radians(th_deg)), math.sin(math.radians(th_deg))
    return np.c_[pts[:, 0] * c - pts[:, 1] * s, pts[:, 0] * s + pts[:, 1] * c]


def _y_bounds(rp):
    hw = P.BORE_W / 2
    return -hw - rp[:, 0].min(), hw - rp[:, 0].max()


def _min_over_y(rp, walls=True):
    """Lowest centre height (and its y) of the posed outline resting on the rails, over every
    shift y the walls allow (walls=False: the free two-rail rocking path, no walls)."""
    if walls:
        lo, hi = _y_bounds(rp)
        if lo > hi + 1e-12:
            return math.inf, None
    else:
        lo, hi = -1.5, 1.5
    f = lambda y: float(np.max(rail_profile(rp[:, 0] + y) - rp[:, 1]))
    ys = np.linspace(lo, hi, 201)
    zs = [f(y) for y in ys]
    k = int(np.argmin(zs))
    a, b = ys[max(k - 2, 0)], ys[min(k + 2, len(ys) - 1)]
    if b - a < 1e-9:
        return zs[k], ys[k]
    r = minimize_scalar(f, bounds=(a, b), method="bounded", options=dict(xatol=1e-7))
    return (r.fun, r.x) if r.fun < zs[k] else (zs[k], ys[k])


def upright_drop(b: P.Bite, th_deg=0.25):
    """Energy test of the centred upright pose with NO walls (the free four-bar formed by the
    R2 corners on the R0.5 rail edges): how much LOWER (mm) the centre of mass gets when the
    bite leans th degrees and rolls.  > 0: upright is unstable; the walls only decide where
    the roll stops (rest_pose)."""
    pts = _outline(b.W, b.H, b.R, step=0.005)
    z0 = _min_over_y(pts, walls=False)[0]
    return z0 - min(_min_over_y(_rot(pts, t), walls=False)[0] for t in (th_deg, -th_deg))


def _geom_key():
    return (P.BORE_W, P.RAIL_IN_Y, P.RAIL_EDGE_R, P.RAIL_TOP_Z, P.BORE_BOT_Z)


def rest_pose(b: P.Bite):
    """Gravity rest pose (frictionless): minimise the centre height over lean angle and every
    wall-allowed shift y.  Cached per bite AND per rail/bore geometry."""
    return _rest_pose(b, _geom_key())


@lru_cache(None)
def _rest_pose(b: P.Bite, _key):
    pts = _outline(b.W, b.H, b.R)
    best = None
    for th in np.arange(-12, 12.0001, 0.1):
        z, y = _min_over_y(_rot(pts, th))
        if y is not None and (best is None or z < best[0] - 1e-12):
            best = (z, y, th)
    t0 = best[2]
    g = lambda t: _min_over_y(_rot(pts, t))[0]
    import warnings
    with warnings.catch_warnings(), np.errstate(invalid="ignore"):
        warnings.simplefilter("ignore", RuntimeWarning)
        r = minimize_scalar(g, bounds=(t0 - 0.1, t0 + 0.1), method="bounded", options=dict(xatol=1e-5))
    if r.fun < best[0]:
        best = (r.fun, _min_over_y(_rot(pts, r.x))[1], float(r.x))
    zc, y, th = best
    rp = _rot(pts, th)
    low = zc + float(rp[:, 1].min())
    low_y = float(rp[np.argmin(rp[:, 1]), 0] + y)
    upright = _pose(pts, 0.0)
    lo, hi = _y_bounds(rp)
    cts = _contacts(b, y, zc, th, walls=(abs(y - lo) < 1e-5, abs(y - hi) < 1e-5))
    k_lean = None
    if len(cts) >= 2:
        f, resid = normal_forces(cts, (y, zc))
        if (f > -1e-6).all() and resid < 1e-3:
            k_lean = float(f.sum())
    drop = upright_drop(b)
    return dict(centre=zc, y=y, lean_deg=th, lowest=low, lowest_y=low_y,
                upright_centre=upright[0], upright_bottom=upright[1],
                com_drop=upright[0] - zc, contacts=[c_[0] for c_ in cts],
                walls=sum(1 for c_ in cts if c_[0].startswith("wall")), k_lean=k_lean,
                upright_stable=drop <= 1e-7, upright_drop_um=1000 * drop)


def width_sweep(H=None, step=0.025):
    """k of the leaning rest pose across the whole bite-width tolerance band (at height H),
    refined around the worst width.  Returns (rows [(W, k, lean, walls)], worst row)."""
    H = P.BITE_H if H is None else H
    W0, W1 = P.BITE_W - P.BITE_W_TOL, P.BITE_W + P.BITE_W_TOL
    rows = []
    for W in np.round(np.arange(W0, W1 + 1e-9, step), 4):
        r = rest_pose(P.Bite("sweep", P.BITE_T, float(W), H))
        rows.append((float(W), r["k_lean"], r["lean_deg"], r["walls"]))
    valid = [x for x in rows if x[1] is not None]
    worst = max(valid, key=lambda x: x[1]) if valid else None
    if worst:
        for W in np.arange(max(W0, worst[0] - step), min(W1, worst[0] + step) + 1e-9, step / 5):
            r = rest_pose(P.Bite("sweep", P.BITE_T, float(W), H))
            if r["k_lean"] is not None and r["k_lean"] > worst[1]:
                worst = (float(W), r["k_lean"], r["lean_deg"], r["walls"])
    return rows, worst


if __name__ == "__main__":
    for k, b in P.BITES.items():
        r = rest_pose(b)
        print(k, {a: (round(v, 3) if isinstance(v, float) else v) for a, v in r.items()})
    for W in (18.0, 18.5, 19.0, 19.5, 20.0):
        b = P.Bite("w", P.BITE_T, W, P.BITE_H)
        r = rest_pose(b)
        print("W", W, "lean", round(r["lean_deg"], 2), "k_lean", r["k_lean"] and round(r["k_lean"], 3),
              "upright stable", r["upright_stable"], round(r["upright_drop_um"], 2), "um", r["contacts"])
