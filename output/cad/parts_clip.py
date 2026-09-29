"""Part group (a): clip tube, gate, end cap.  Built in place in the §2 frame."""
import math
import cadquery as cq
from params import *  # noqa: F401,F403  (spec names read better unqualified)
import params as P
from geom import box, cyl_y, cyl_z, cone_z, prism_xz, prism_yz


def _rail(side: int) -> cq.Workplane:
    """One bite rail: Y 8.0 -> 9.75 (x side), Z 2.0 -> 4.5, top edges R0.5,
    front end (X 0) chamfered 0.5 x 45°."""
    y_in, y_out = P.RAIL_IN_Y, P.RAIL_OUT_Y
    r = P.RAIL_EDGE_R
    zb, zt = P.BORE_BOT_Z - 0.01, P.RAIL_TOP_Z   # 0.01 overlap into the floor for a clean union
    prof = (cq.Workplane("YZ")
            .moveTo(y_in, zb).lineTo(y_out, zb).lineTo(y_out, zt - r)
            .threePointArc((y_out - r + r * math.cos(math.radians(45)), zt - r + r * math.sin(math.radians(45))),
                           (y_out - r, zt))
            .lineTo(y_in + r, zt)
            .threePointArc((y_in + r - r * math.cos(math.radians(45)), zt - r + r * math.sin(math.radians(45))),
                           (y_in, zt - r))
            .close()
            .extrude(P.CLIP_L))
    if side < 0:
        prof = prof.mirror("XZ")
    c = P.RAIL_FRONT_CHAMFER
    wedge = prism_xz([(-0.01, zt - c), (c, zt + 0.01), (-0.01, zt + 0.01)], -P.BORE_W / 2, P.BORE_W / 2)
    return prof.cut(wedge)


def clip_tube(view_slot: bool = None) -> cq.Workplane:
    """§5.2  Envelope X 0 -> 140.8, Y ±12.25, Z -2.0 -> 33.5, open both ends."""
    if view_slot is None:
        view_slot = P.VIEW_SLOT
    hw = P.CLIP_HW
    env = box(0, P.CLIP_L, -hw, hw, P.CLIP_BOT_Z, P.TOP_Z)
    # outside chamfers: mouth lead-in and all other outer edges (never the bore edge)
    # (not the two vertical back-end edges: the end-cap screw holes are 0.85 from the end face)
    env = env.edges("not(|Z and >X)").chamfer(P.MOUTH_CHAMFER)
    # keep the two top long edges square where the gate slot leaves a 1.0 skin
    # (a 0.5 chamfer there would thin the skin to 0.5)
    env = env.union(box(P.MOUTH_CHAMFER + 0.1, P.GATE_SLOT_X1 + 0.6, -hw, hw,
                        P.TOP_Z - P.MOUTH_CHAMFER - 0.1, P.TOP_Z))
    t = env
    # bore (constant profile, both ends open)
    t = t.cut(box(-1, P.CLIP_L + 1, -P.BORE_W / 2, P.BORE_W / 2, P.BORE_BOT_Z, P.BORE_TOP_Z))
    # ribbon groove X 2.0 -> end; solid floor at the mouth
    t = t.cut(box(P.GROOVE_X0, P.CLIP_L + 1, -P.GROOVE_W / 2, P.GROOVE_W / 2, 0, P.BORE_BOT_Z + 0.01))
    # rails
    t = t.union(_rail(+1)).union(_rail(-1))
    # clamp notch across the groove floor
    t = t.cut(box(P.CLAMP_NOTCH_X - P.CLAMP_NOTCH_W / 2, P.CLAMP_NOTCH_X + P.CLAMP_NOTCH_W / 2,
                  -P.GROOVE_W / 2, P.GROOVE_W / 2, -P.CLAMP_NOTCH_D, 0.01))
    # clamp screw holes + countersinks from the underside (90°, heads flush with Z -2.0)
    for s in (+1, -1):
        y = s * P.CLAMP_SCREW_Y
        t = t.cut(cyl_z(P.CLAMP_SCREW_X, y, P.M2_CLEAR_D, P.CLIP_BOT_Z - 1, 0.5))
        h = (P.M2_CSK_CUT_D - P.M2_CLEAR_D) / 2
        t = t.cut(cone_z(P.CLAMP_SCREW_X, y, P.CLIP_BOT_Z - 0.01, P.M2_CSK_CUT_D + 0.02,
                         P.CLIP_BOT_Z + h, P.M2_CLEAR_D))
    # gate slot: through the roof and 1.0 into each side wall, Z 2.0 -> top
    t = t.cut(box(P.GATE_SLOT_X0, P.GATE_SLOT_X1, -P.GATE_SLOT_HW, P.GATE_SLOT_HW, P.BORE_BOT_Z, P.TOP_Z + 1))
    # latch notch on the roof top: vertical face at X 12.0, 30° ramp up to the top at X 16.0
    z0 = P.TOP_Z - P.LATCH_NOTCH_D
    ramp_len = P.LATCH_NOTCH_D / math.tan(math.radians(P.LATCH_RAMP_DEG))
    pts = [(P.LATCH_NOTCH_X0, z0), (P.LATCH_NOTCH_X1 - ramp_len, z0), (P.LATCH_NOTCH_X1, P.TOP_Z),
           (P.LATCH_NOTCH_X1, P.TOP_Z + 1), (P.LATCH_NOTCH_X0, P.TOP_Z + 1)]
    t = t.cut(prism_xz(pts, -P.LATCH_NOTCH_W / 2, P.LATCH_NOTCH_W / 2))
    # end-cap screw holes through both side walls
    t = t.cut(cyl_y(P.ENDCAP_SCREW_X, P.ENDCAP_SCREW_Z, P.M2_CLEAR_D, -hw - 1, hw + 1))
    # optional viewing windows (opaque prints), +Y wall only
    if view_slot:
        x = P.VIEW_X0
        while x + P.VIEW_WIN_L <= P.VIEW_X1 + 1e-6:
            t = t.cut(box(x, x + P.VIEW_WIN_L, P.BORE_W / 2 - 0.5, hw + 1, P.VIEW_Z0, P.VIEW_Z1))
            x += P.VIEW_WIN_L + P.VIEW_WEB
    return t


def gate() -> cq.Workplane:
    """§5.6  1.2 (X) x 22.1 (Y) plate, Z 2.0 -> 33.5, grip tab to Z 42.0.
    In place: seated against the front of its slot, X 1.2 -> 2.4."""
    x0, x1 = P.GATE_SLOT_X0, P.GATE_SLOT_X0 + P.GATE_T
    g = box(x0, x1, -P.GATE_HW, P.GATE_HW, P.BORE_BOT_Z, P.TOP_Z)
    tab = box(x0, x1, P.GATE_TAB_Y0, P.GATE_TAB_Y1, P.TOP_Z - 0.01, P.GATE_TAB_TOP_Z)
    tab = tab.edges("|X and >Z").chamfer(0.4)
    return g.union(tab)


def end_cap() -> cq.Workplane:
    """§5.7  Plug X 136.8 -> 140.8 matching the inner profile at -0.2 per side,
    with a tongue filling the groove.  The rail-to-wall gaps are left open
    (a 0.1-wide sliver there would be unprintable)."""
    c = P.ENDCAP_CLR
    x0, x1 = P.ENDCAP_X0, P.CLIP_L
    upper = box(x0, x1, -(P.BORE_W / 2 - c), P.BORE_W / 2 - c, P.RAIL_TOP_Z + c, P.BORE_TOP_Z - c)
    centre = box(x0, x1, -(P.RAIL_IN_Y - c), P.RAIL_IN_Y - c, c, P.RAIL_TOP_Z + c + 0.01)
    cap = upper.union(centre)
    cap = cap.faces(">X or <X").edges().chamfer(P.SMALL_CHAMFER)
    # M2 x 6 pan-head pilots from both sides
    hw = P.BORE_W / 2 - c
    for s in (+1, -1):
        y0 = s * hw
        y1 = s * (hw - P.ENDCAP_PILOT_DEPTH)
        cap = cap.cut(cyl_y(P.ENDCAP_SCREW_X, P.ENDCAP_SCREW_Z, P.MIN_HOLE_D, y0 + s * 0.5, y1))
    return cap
