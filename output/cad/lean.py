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
    scan(np.radians(np.arange(-12, 12.01, 0.5)), np.linspace(-hw, hw, 41))
    _, y0, t0, _, _ = best
    scan(np.radians(np.linspace(t0 - 0.5, t0 + 0.5, 21)), np.linspace(y0 - 0.1, y0 + 0.1, 21))
    zc, y, th, low, low_y = best
    upright = _pose(pts, 0.0)
    return dict(centre=zc, y=y, lean_deg=th, lowest=low, lowest_y=low_y,
                upright_centre=upright[0], upright_bottom=upright[1],
                com_drop=upright[0] - zc)


if __name__ == "__main__":
    for k, b in P.BITES.items():
        r = rest_pose(b)
        print(k, {a: round(v, 3) for a, v in r.items()})
