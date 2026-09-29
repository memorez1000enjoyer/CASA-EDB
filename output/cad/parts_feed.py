"""Part group (b): follower, drum, drum spacer, ribbon clamp.
The follower and drum are built at F = 0 (push-rib crest plane at X = 0);
the assembly translates them by +F."""
import cadquery as cq
import params as P
from geom import box, cyl_y, cyl_z


def follower(spring: P.Spring) -> cq.Workplane:
    """§5.3  Body F -> F+28 riding on the rails, keel in the groove, coil pocket,
    open-bottom slot (drum + coil drop in from below), Ø2.1 axle holes."""
    hw = P.FOLLOWER_HW
    body = box(P.PUSH_RIB_D, P.FOLLOWER_L, -hw, hw, P.FOLLOWER_BOT_Z, P.FOLLOWER_TOP_Z)
    body = body.faces(">Z").edges().chamfer(P.FOLLOWER_CHAMFER)
    keel = box(P.KEEL_X0, P.FOLLOWER_L, -P.KEEL_HW, P.KEEL_HW, P.KEEL_BOT_Z, P.FOLLOWER_BOT_Z + 0.01)
    f = body.union(keel)
    for zc in P.PUSH_RIB_Z:
        f = f.union(box(0, P.PUSH_RIB_D + 0.01, -hw, hw, zc - P.PUSH_RIB_H / 2, zc + P.PUSH_RIB_H / 2))
    pd = P.pocket_d(spring)
    pocket_rear = P.POCKET_CX + pd / 2
    f = f.cut(cyl_y(P.POCKET_CX, P.POCKET_CZ, pd, -P.POCKET_HW, P.POCKET_HW))
    f = f.cut(box(P.KEEL_X0, pocket_rear, -P.POCKET_HW, P.POCKET_HW, P.KEEL_BOT_Z - 1, P.POCKET_CZ))
    f = f.cut(cyl_y(P.POCKET_CX, P.POCKET_CZ, P.AXLE_HOLE_D, -hw - 1, hw + 1))
    return f


def drum() -> cq.Workplane:
    """§5.4  Ø12.5 x 9.4 (Y), bore Ø2.3, edges chamfered 0.3.  At F = 0."""
    d = cyl_y(P.POCKET_CX, P.POCKET_CZ, P.DRUM_D, -P.DRUM_L / 2, P.DRUM_L / 2)
    d = d.faces(">Y or <Y").edges().chamfer(P.DRUM_CHAMFER)
    return d.cut(cyl_y(P.POCKET_CX, P.POCKET_CZ, P.DRUM_BORE_D, -P.DRUM_L, P.DRUM_L))


def spacer_dims(spring: P.Spring):
    """Spacer ring that slips over the drum beside a narrow ribbon (None if not needed)."""
    t = (P.DRUM_L - spring.W) / 2 - P.SPACER_AXIAL_CLR
    if t < 0.8:
        return None
    idd = P.DRUM_D + 2 * P.SPACER_ID_CLR
    odd = P.coil_od(spring) + P.SPACER_OD_OVER_COIL
    y_in = spring.W / 2 + P.SPACER_AXIAL_CLR
    return dict(t=t, id=idd, od=odd, y_in=y_in)


def drum_spacer(spring: P.Spring, side: int = +1):
    """Spacer ring (spring B only).  At F = 0, on the +Y (side=+1) or -Y side."""
    s = spacer_dims(spring)
    if s is None:
        return None
    y0, y1 = side * s["y_in"], side * (s["y_in"] + s["t"])
    ring = cyl_y(P.POCKET_CX, P.POCKET_CZ, s["od"], y0, y1)
    return ring.cut(cyl_y(P.POCKET_CX, P.POCKET_CZ, s["id"], y0 - side, y1 + side))


def ribbon_clamp(spring: P.Spring) -> cq.Workplane:
    """§5.5  15.4 x 6.0 x 1.2 plate lying on the ribbon (bottom Z = SPRING_T),
    0.3 ridge at X 3.5 into the floor notch, Ø1.6 pilots at X 5.0, Y ±6.0."""
    z0 = spring.T
    c = box(P.CLAMP_X0, P.CLAMP_X1, -P.CLAMP_HW, P.CLAMP_HW, z0, z0 + P.CLAMP_T)
    c = c.union(box(P.CLAMP_NOTCH_X - P.CLAMP_RIDGE_W / 2, P.CLAMP_NOTCH_X + P.CLAMP_RIDGE_W / 2,
                    -P.CLAMP_HW, P.CLAMP_HW, z0 - P.CLAMP_RIDGE_H, z0 + 0.01))
    for s in (+1, -1):
        c = c.cut(cyl_z(P.CLAMP_SCREW_X, s * P.CLAMP_SCREW_Y, P.CLAMP_PILOT_D, -1, 3))
    return c
