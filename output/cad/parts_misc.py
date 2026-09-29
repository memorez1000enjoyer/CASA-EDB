"""Part group (e): ring hook, bench base, fit coupon, dummy bites."""
import cadquery as cq
import params as P
from geom import box, cyl_y, cyl_z, prism_yz, hex_y


def ring_hook() -> cq.Workplane:
    """§6.7  3.0-thick PETG J-bracket screwed to the -Y (mount) face at the two
    ring-hook pilots; hooks over a neck-ring flange of thickness RING_FLANGE_T whose
    top edge sits RING_HOOK_Z above the top surface.  PLACEHOLDER until the flange is
    measured in HUT - Largest.stl.  Profile in YZ, extruded along X."""
    t, c = P.RING_HOOK_T, P.RING_HOOK_CLR
    y_face = -P.RCV_HW                        # mount face
    y_leg_out = y_face - t                    # leg outer face
    y_gap_out = y_leg_out - c - P.RING_FLANGE_T - c
    y_lip_out = y_gap_out - t
    z_seat = P.TOP_Z + P.RING_HOOK_Z          # flange top edge seats here
    z_top = z_seat + t
    z_lip = z_seat - P.RING_HOOK_REACH
    pts = [(y_face, P.RING_HOOK_Z0), (y_face, z_top), (y_lip_out, z_top), (y_lip_out, z_lip),
           (y_gap_out, z_lip), (y_gap_out, z_seat), (y_leg_out, z_seat), (y_leg_out, P.RING_HOOK_Z0)]
    x0, x1 = P.RING_HOOK_X
    h = prism_yz(pts, x0, x1)
    h = h.edges("|X").chamfer(0.5)
    # countersunk M2 x 8 clearance holes (heads must not stand into the flange gap)
    for (x, z) in P.RING_HOOK_PILOTS:
        h = h.cut(cyl_y(x, z, P.M2_CLEAR_D, y_face + 1, y_leg_out - 1))
        cs = (P.M2_CSK_CUT_D - P.M2_CLEAR_D) / 2
        cone = cq.Solid.makeCone(P.M2_CSK_CUT_D / 2 + 0.01, P.M2_CLEAR_D / 2, cs + 0.01,
                                 pnt=cq.Vector(x, y_leg_out - 0.01, z), dir=cq.Vector(0, 1, 0))
        h = h.cut(cq.Workplane().add(cone))
    return h


def bench_base() -> cq.Workplane:
    """Flat plate that holds the device upright (-Z down): a fixed jaw on -Y, a jaw
    with two M3 thumb screws (nut traps) on +Y, an end stop at -X and a rest under
    the clip.  Dimensioned by the CAD agent."""
    clr = P.BASE_CLR
    zb = P.RCV_BOT_Z                      # device bottom sits on the plate top
    x0, x1 = P.RCV_X0 - 8, P.CLIP_L - 6
    plate = box(x0, x1, -26, 26, zb - P.BASE_T, zb)
    plate = plate.edges("|Z").fillet(4)
    jx0, jx1 = P.RCV_X0 + 3, -4.0
    hw = P.RCV_HW + clr
    fixed = box(jx0, jx1, -hw - 5, -hw, zb - 0.01, zb + 12)
    screw_jaw = box(jx0, jx1, hw, hw + 8, zb - 0.01, zb + 14)
    stop = box(P.RCV_X0 - clr - 4, P.RCV_X0 - clr, -12, 12, zb - 0.01, zb + 8)
    clip_rest_top = P.CLIP_BOT_Z - 0.6
    rest = box(P.CLIP_L - 36, P.CLIP_L - 26, -8, 8, zb - 0.01, clip_rest_top)
    b = plate.union(fixed).union(screw_jaw).union(stop).union(rest)
    zs = zb + 7.0
    for xs in (P.RCV_X0 + 12, -14.0):
        b = b.cut(cyl_y(xs, zs, P.M3_CLEAR_D, hw - 1, hw + 9))
        # nut slot dropped in from the top (open upward -> no overhang)
        ym = hw + 4.0
        b = b.cut(box(xs - P.M3_NUT_AF / 2, xs + P.M3_NUT_AF / 2, ym - P.M3_NUT_T / 2, ym + P.M3_NUT_T / 2,
                      zs - P.M3_NUT_AF / 2 - 0.3, zb + 15))
    return b


def _dots(cx, cy, n, top, d=1.4, pitch=2.2, depth=0.5):
    """n engraved dots in a row centred on (cx, cy) - a font-free label."""
    x0 = cx - (n - 1) * pitch / 2
    out = None
    for k in range(n):
        c = cyl_z(x0 + k * pitch, cy, d, top - depth, top + 1)
        out = c if out is None else out.union(c)
    return out


def fit_coupon() -> cq.Workplane:
    """§8.2  Plate with 10 x 10 square sleeves at 0.20/0.25/0.30/0.35 clearance,
    Ø2 pin holes at 1.9/2.0/2.1/2.2/2.3 (vertical and horizontal), plus the
    10 x 10 slider.  Print it first and set CLR_SLIDE from it.
    Labels are engraved dots (fonts leave sub-0.8 slivers): sleeves 1-4 dots =
    0.20/0.25/0.30/0.35 clearance; pin holes 1-5 dots = Ø1.9/2.0/2.1/2.2/2.3."""
    s = P.COUPON_SLIDER
    n = len(P.COUPON_CLEARANCES)
    pitch = 15.0
    L = n * pitch + 4
    T = 8.0
    plate = box(0, L, 0, 40, 0, T)
    plate = plate.edges("|Z").fillet(2)
    for i, c in enumerate(P.COUPON_CLEARANCES):
        cx = 2 + pitch / 2 + i * pitch
        a = s + 2 * c
        plate = plate.cut(box(cx - a / 2, cx + a / 2, 3, 3 + a, -1, T + 1))
        plate = plate.cut(_dots(cx, 17.0, i + 1, T))   # 1 dot = 0.20 ... 4 dots = 0.35
    for i, d in enumerate(P.COUPON_PIN_HOLES):
        cx = 6 + i * 12.5
        plate = plate.cut(cyl_z(cx, 24.0, d, -1, T + 1))
        plate = plate.cut(_dots(cx, 29.5, i + 1, T))   # 1 dot = Ø1.9 ... 5 dots = Ø2.3
        # horizontal hole into the +Y side face, 8 deep (same Ø, printed sideways)
        plate = plate.cut(cyl_y(cx, T / 2, d, 40 - 8, 41))
    slider = box(L + 6, L + 6 + s, 0, 30, 0, s)
    slider = slider.faces(">Y or <Y").edges().chamfer(0.5)
    return plate.union(slider)


def bite(b: P.Bite) -> cq.Workplane:
    """§8.4  R2-edged dummy bite, T (X) x W (Y) x H (Z), centred in X/Y, bottom at Z 0."""
    return (box(-b.T / 2, b.T / 2, -b.W / 2, b.W / 2, 0, b.H).edges().fillet(b.R))
