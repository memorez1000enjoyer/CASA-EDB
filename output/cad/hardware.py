"""Purchased hardware modelled for assembly checks and renders:
steel pins, dowels, clamp screws, constant-force spring (coil + ribbon), return spring."""
import math
import cadquery as cq
import params as P
from geom import box, cyl_y, cyl_z, prism_xz


def pin_y(cx, cz, length, d=P.PIN_D):
    return cyl_y(cx, cz, d, -length / 2, length / 2)


def dowel(x, z):
    return pin_y(x, z, P.DOWEL_L)


def clamp_screw(y):
    """M2 x 4 countersunk self-tapper driven up from the underside (head in the
    tube's countersink, top 0.1 recessed above Z -2.0)."""
    x = P.CLAMP_SCREW_X
    z_head = P.CLIP_BOT_Z + (P.M2_CSK_CUT_D - P.M2_CSK_HEAD_D) / 2
    head = cq.Workplane().add(cq.Solid.makeCone(P.M2_CSK_HEAD_D / 2, 1.0, P.M2_CSK_HEAD_D / 2 - 1.0,
                                                pnt=cq.Vector(x, y, z_head), dir=cq.Vector(0, 0, 1)))
    shank = cyl_z(x, y, 2.0, z_head + 0.5, z_head + 4.0)
    return head.union(shank)


def ribbon_geometry(spring: P.Spring, F: float):
    """Straight free span of the ribbon from the clamp exit to its tangent point on
    the coil.  Returns dict with exit point, tangent point, span length, coil OD."""
    cx, cz = F + P.POCKET_CX, P.pocket_cz(spring)
    px, pz = P.CLAMP_X1, spring.T / 2
    od = P.coil_od(spring, 0.0)
    for _ in range(6):  # coil OD depends on how much ribbon is out; iterate
        rho = od / 2 - spring.T / 2
        dx, dz = cx - px, cz - pz
        d = math.hypot(dx, dz)
        tl = math.sqrt(max(d * d - rho * rho, 0.0))
        th_c = math.atan2(dz, dx)
        a = math.asin(min(rho / d, 1.0))
        th = th_c - a                       # lower tangent
        qx, qz = px + tl * math.cos(th), pz + tl * math.sin(th)
        unwound = (P.CLAMP_X1 - P.CLAMP_X0) + tl
        od = P.coil_od(spring, unwound)
    return dict(p=(px, pz), q=(qx, qz), span=tl, coil_od=od, centre=(cx, cz), unwound=unwound,
                max_z=max(qz, pz) + spring.T / 2)


def cf_spring(spring: P.Spring, F: float) -> cq.Workplane:
    """Coil on the drum + ribbon: under the clamp (dipping into the floor notch) and
    the straight free span to the coil tangent."""
    g = ribbon_geometry(spring, F)
    T, hw = spring.T, spring.W / 2
    cx, cz = g["centre"]
    coil = cyl_y(cx, cz, g["coil_od"], -hw, hw).cut(cyl_y(cx, cz, P.DRUM_D, -hw - 1, hw + 1))
    # ribbon under the clamp, wrapped round the clamp ridge in the 0.3 notch
    n0 = P.CLAMP_NOTCH_X - P.CLAMP_NOTCH_W / 2
    n1 = P.CLAMP_NOTCH_X + P.CLAMP_NOTCH_W / 2
    r0 = P.CLAMP_NOTCH_X - P.CLAMP_RIDGE_W / 2
    r1 = P.CLAMP_NOTCH_X + P.CLAMP_RIDGE_W / 2
    nd = P.CLAMP_NOTCH_D
    # closed polygon: along the floor/notch (bottom path), back along the clamp/ridge (top path)
    top = [(P.CLAMP_X1, T), (r1, T), (r1, T - nd), (r0, T - nd), (r0, T), (P.CLAMP_X0, T)]
    bottom = [(P.CLAMP_X0, 0), (n0, 0), (n0, -nd), (n1, -nd), (n1, 0), (P.CLAMP_X1, 0)]
    under = prism_xz(bottom + top, -hw, hw)
    # free span: thin plate along P->Q
    (px, pz), (qx, qz) = g["p"], g["q"]
    ang = math.atan2(qz - pz, qx - px)
    nx, nz = -math.sin(ang) * T / 2, math.cos(ang) * T / 2
    ext = 0.05
    span = prism_xz([(px - nx - ext * math.cos(ang), pz - nz), (qx - nx, qz - nz),
                     (qx + nx, qz + nz), (px + nx - ext * math.cos(ang), pz + nz)], -hw, hw)
    return coil.union(under).union(span)


def return_spring(plunger_bot_z: float) -> cq.Workplane:
    """Compression spring as a tube: well bottom -> ear underside."""
    z0, z1 = P.SPRING_WELL_Z0, plunger_bot_z + P.EAR_UNDERSIDE
    t = cyl_z(P.SPRING_WELL_X, 0, P.RS_OD, z0, z1)
    return t.cut(cyl_z(P.SPRING_WELL_X, 0, P.RS_OD - 2 * P.RS_WIRE, z0 - 1, z1 + 1))
