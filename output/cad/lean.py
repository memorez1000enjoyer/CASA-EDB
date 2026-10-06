"""2D (YZ) rigid-body check of a bite resting on the clip rails, free to shift in Y and
lean about X (the stacking axis: a whole stack can lean together without its faces
sliding, so face friction does not stop it).

For each bite size: the gravity rest pose (lowest centre of mass, walls at ±BORE_W/2),
and the lowest point of the bite in that pose.  Used by verify.py §9.11 to show how far
below CUP_TOP_Z a leaning bite's bottom corner can hang when it reaches the receiver.
"""
import math
import numpy as np
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


def _contacts(b: P.Bite, y, zc, th_deg, tol=2e-3):
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
    vy = max(verts, key=lambda q: q[0])                     # walls
    if vy[0] + b.R >= hw - tol:
        out.append(("wall+1", vy[0] + b.R, vy[1], (-1.0, 0.0)))
    vy = min(verts, key=lambda q: q[0])
    if vy[0] - b.R <= -hw + tol:
        out.append(("wall-1", vy[0] - b.R, vy[1], (1.0, 0.0)))
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
    """Frictionless static equilibrium (2-D) for 3 contacts under unit weight at com:
    returns the normal force at each contact, in units of the bite's weight."""
    A = np.zeros((3, len(contacts)))
    for j, (_, y, z, (ny, nz)) in enumerate(contacts):
        A[0, j], A[1, j] = ny, nz
        A[2, j] = (y - com[0]) * nz - (z - com[1]) * ny     # moment about the CoM
    rhs = np.array([0.0, 1.0, 0.0])
    sol, *_ = np.linalg.lstsq(A, rhs, rcond=None)
    return sol, float(np.abs(A @ sol - rhs).max())


def _centre_at(pts, th_deg):
    """Lowest centre height over shift y at lean angle th (the two-rail rocking path)."""
    c, s = math.cos(math.radians(th_deg)), math.sin(math.radians(th_deg))
    rp = np.c_[pts[:, 0] * c - pts[:, 1] * s, pts[:, 0] * s + pts[:, 1] * c]
    hw = (P.BORE_W - (pts[:, 0].max() - pts[:, 0].min())) / 2 + 1.0
    zs = [r[0] for r in (_pose(rp, y) for y in np.linspace(-hw, hw, 801)) if r is not None]
    return min(zs) if zs else math.inf


def upright_drop(b: P.Bite, th_deg=0.5):
    """Energy test of the centred upright pose: how much LOWER (mm) the centre of mass gets
    when the bite leans th degrees and rolls on its rail contacts.  > 0: upright is unstable.
    (The R2-corner-on-R0.5-edge contacts make a four-bar linkage; crossing contact normals
    alone do not decide it.)"""
    pts = _outline(b.W, b.H, b.R, step=0.005)
    z0 = _centre_at(pts, 0.0)
    return z0 - min(_centre_at(pts, th_deg), _centre_at(pts, -th_deg))


def rest_pose(b: P.Bite):
    """Gravity rest pose: minimise the centre height over shift y and lean angle."""
    pts = _outline(b.W, b.H, b.R)
    best = None

    def scan(ths, ys):
        nonlocal best
        for th in ths:
            c, s = math.cos(th), math.sin(th)
            rp = np.c_[pts[:, 0] * c - pts[:, 1] * s, pts[:, 0] * s + pts[:, 1] * c]
            for y in ys:
                r = _pose(rp, y)
                if r is not None and (best is None or r[0] < best[0] - 1e-9):
                    best = (r[0], y, math.degrees(th), r[1], r[2])

    hw = (P.BORE_W - b.W) / 2 + 0.3
    if best is None:
        pass
    scan(np.radians(np.arange(-12, 12.01, 0.5)), np.linspace(-hw, hw, 41))
    _, y0, t0, _, _ = best
    scan(np.radians(np.linspace(t0 - 0.5, t0 + 0.5, 21)), np.linspace(y0 - 0.1, y0 + 0.1, 21))
    _, y0, t0, _, _ = best
    scan(np.radians(np.linspace(t0 - 0.05, t0 + 0.05, 41)), np.linspace(y0 - 0.01, y0 + 0.01, 41))
    zc, y, th, low, low_y = best
    upright = _pose(pts, 0.0)
    c, s_ = math.cos(math.radians(th)), math.sin(math.radians(th))
    rp = np.c_[pts[:, 0] * c - pts[:, 1] * s_, pts[:, 0] * s_ + pts[:, 1] * c]
    cts = _contacts(b, y, zc, th)
    k_lean, resid = (None, None)
    if len(cts) in (2, 3):
        f, resid = normal_forces(cts, (y, zc))
        if (f > -1e-6).all() and resid < 1e-3:
            k_lean = float(f.sum())
    drop = upright_drop(b)
    return dict(centre=zc, y=y, lean_deg=th, lowest=low, lowest_y=low_y,
                upright_centre=upright[0], upright_bottom=upright[1],
                com_drop=upright[0] - zc, contacts=[c_[0] for c_ in cts], k_lean=k_lean,
                upright_stable=drop <= 1e-6, upright_drop_um=1000 * drop)


if __name__ == "__main__":
    for k, b in P.BITES.items():
        r = rest_pose(b)
        print(k, {a: (round(v, 3) if isinstance(v, float) else v) for a, v in r.items()})
    for W in (18.0, 18.5, 19.0, 19.5, 20.0):
        b = P.Bite("w", P.BITE_T, W, P.BITE_H)
        r = rest_pose(b)
        print("W", W, "lean", round(r["lean_deg"], 2), "k_lean", r["k_lean"] and round(r["k_lean"], 3),
              "upright stable", r["upright_stable"], round(r["upright_drop_um"], 1), "um", r["contacts"])
