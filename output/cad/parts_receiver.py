"""Part group (c): receiver body with socket and latch, split at Y = 0 into
receiver_left (-Y half, mount face) and receiver_right (+Y half)."""
import math
import cadquery as cq
import params as P
from geom import box, cyl_y, cyl_z, prism_xz, prism_yz, hex_y, chamfer_edge_x, chamfer_edge_y, rim_chamfer, union_all

_CACHE = {}


def _entry_chamfer_cut() -> cq.Workplane:
    """0.5 x 45° lead-in around the socket opening at X = SOCKET_L."""
    c = P.SOCKET_ENTRY_CHAMFER
    zc = (P.SOCKET_IN_Z0 + P.SOCKET_IN_Z1) / 2
    w, h = 2 * P.SOCKET_IN_HW, P.SOCKET_IN_Z1 - P.SOCKET_IN_Z0
    x0 = P.SOCKET_L - c
    loft = (cq.Workplane("YZ", origin=(x0, 0, 0)).center(0, zc).rect(w, h)
            .workplane(offset=c + 0.01).rect(w + 2 * c + 0.02, h + 2 * c + 0.02).loft())
    return loft


def receiver_full() -> cq.Workplane:
    """§6.1 / §6.2 receiver as one body (split later)."""
    if "full" in _CACHE:
        return _CACHE["full"]
    hw = P.RCV_HW
    bw = P.BORE_W / 2
    main = box(P.RCV_X0, 0, -hw, hw, P.RCV_BOT_Z, P.TOP_Z)
    main = main.edges("<X or (|X and <Z)").chamfer(P.RCV_EDGE_CHAMFER)
    sock = box(0, P.SOCKET_L, -hw, hw, P.SOCKET_OUT_Z0, P.SOCKET_OUT_Z1)
    sock = sock.edges(">X or (|X and >Z)").chamfer(P.RCV_EDGE_CHAMFER)
    lug = box(P.LUG_X[0], P.LUG_X[1], -hw, hw, P.LUG_Z0, P.SOCKET_OUT_Z0 + 0.01)
    # backstop lip on the paddle side of the window, full width so a fumbled bite can't
    # slide round its ends toward the neck
    lip = box(P.FRONT_WALL_X0, P.STOP_X, -P.BACKSTOP_HW, P.BACKSTOP_HW, P.TOP_Z - 0.01, P.TOP_Z + P.BACKSTOP_H)
    lip = lip.edges("|Z or >Z").chamfer(P.EDGE_CHAMFER)
    # stripper wall: the 0.8 strip behind the window rises to the socket roof top and
    # joins the socket's front band (an L-section instead of a flat 0.8 x 2.0 strip)
    swall = box(P.STRIPPER_X, 0.01, -hw, hw, P.TOP_Z - 0.01, P.STRIPPER_WALL_TOP_Z)
    r = main.union(sock).union(lug).union(lip).union(swall)

    cuts = []
    # bite path: bore continuation above the bridge/elevator, and the elevator channel
    cuts.append(box(P.STOP_X, 0.01, -bw, bw, P.CUP_TOP_Z, P.BORE_TOP_Z))
    cuts.append(box(P.STOP_X, P.BRIDGE_X0, -bw, bw, P.LEDGE_Z, P.BORE_TOP_Z))
    # lever-tip relief in the ledge
    cuts.append(box(P.STOP_X, P.RELIEF_X1, -P.RELIEF_HW, P.RELIEF_HW, P.RELIEF_Z0, P.LEDGE_Z + 0.01))
    # bridge top CUP_TOP_Z (below every bite seat): +X edge break BRIDGE_LEADIN x 45°, -X 0.3 chamfer
    li = P.BRIDGE_LEADIN
    cuts.append(prism_xz([(0.01, P.CUP_TOP_Z - li - 0.01), (0.01, P.CUP_TOP_Z + 0.01),
                          (-li - 0.01, P.CUP_TOP_Z + 0.01)], -bw, bw))
    rc = P.BRIDGE_REAR_CHAMFER
    cuts.append(prism_xz([(P.BRIDGE_X0 - 0.01, P.CUP_TOP_Z - rc - 0.01), (P.BRIDGE_X0 - 0.01, P.CUP_TOP_Z + 0.01),
                          (P.BRIDGE_X0 + rc + 0.01, P.CUP_TOP_Z + 0.01)], -bw, bw))
    # window through the roof; rear edge X -0.8 is the sharp stripper edge
    cuts.append(box(P.STOP_X, P.STRIPPER_X, -bw, bw, P.BORE_TOP_Z - 0.01, P.TOP_Z + 1))
    wc = P.WINDOW_TOP_CHAMFER
    for s in (+1, -1):
        cuts.append(prism_yz([(s * (bw - 0.01), P.TOP_Z - wc - 0.01), (s * (bw + wc + 0.01), P.TOP_Z + 0.01),
                              (s * (bw - 0.01), P.TOP_Z + 0.01)], P.STOP_X, P.STRIPPER_X))
    # lever slot through the front wall, lever chamber
    cuts.append(box(P.FRONT_WALL_X0 - 0.01, P.STOP_X + 0.01, -P.LEVER_SLOT_HW, P.LEVER_SLOT_HW, *P.LEVER_SLOT_Z))
    cuts.append(box(P.LEVER_CHAMBER_X0, P.FRONT_WALL_X0 + 0.01, -P.LEVER_CHAMBER_HW, P.LEVER_CHAMBER_HW,
                    *P.LEVER_CHAMBER_Z))
    # plunger channel (open at the top), ear slot, return-spring well
    cuts.append(box(P.PADDLE_X - P.PLUNGER_CH_HW_X, P.PADDLE_X + P.PLUNGER_CH_HW_X,
                    -P.PLUNGER_CH_HW_Y, P.PLUNGER_CH_HW_Y, P.PLUNGER_CH_Z0, P.TOP_Z + 1))
    cuts.append(box(P.EAR_SLOT_X0, P.PADDLE_X - P.PLUNGER_CH_HW_X + 0.01,
                    -P.PLUNGER_CH_HW_Y, P.PLUNGER_CH_HW_Y, *P.EAR_SLOT_Z))
    cuts.append(cyl_z(P.SPRING_WELL_X, 0, P.RS_WELL_D, P.SPRING_WELL_Z0, P.EAR_SLOT_Z[0] + 0.01))
    # pivot-pin hole: blind, 1.0 short of each outer skin
    cuts.append(cyl_y(P.PIVOT_X, P.PIVOT_Z, P.RCV_PIVOT_HOLE_L, -(hw - P.PIVOT_HOLE_SKIN), hw - P.PIVOT_HOLE_SKIN))
    # socket interior (clip + 0.30)
    cuts.append(box(0, P.SOCKET_L + 1, -P.SOCKET_IN_HW, P.SOCKET_IN_HW, P.SOCKET_IN_Z0, P.SOCKET_IN_Z1))
    cuts.append(_entry_chamfer_cut())
    # gate slot and gate-tab channel through the socket roof
    zr0, zr1 = P.SOCKET_IN_Z1 - 0.01, P.SOCKET_OUT_Z1 + 1
    cuts.append(box(P.GATE_SLOT_X0, P.GATE_SLOT_X1, -P.GATE_SLOT_HW, P.GATE_SLOT_HW, zr0, zr1))
    cuts.append(box(P.GATE_SLOT_X0, P.SOCKET_L + 1, P.TAB_CHANNEL_Y[0], P.TAB_CHANNEL_Y[1], zr0, zr1))
    # latch tongue: side cuts, tip cut, thinned top (1.6 thick)
    th, cw = P.TONGUE_HW, P.TONGUE_CUT_W
    xt = P.TONGUE_X0 - P.TONGUE_TIP_CUT
    for s in (+1, -1):
        cuts.append(box(xt, P.TONGUE_ROOT_X, s * th, s * (th + cw), zr0, zr1))
    cuts.append(box(xt, P.TONGUE_X0, -(th + cw), th + cw, zr0, zr1))
    cuts.append(box(P.TONGUE_X0 - 0.01, P.TONGUE_ROOT_X, -th, th, P.SOCKET_IN_Z1 + P.TONGUE_T, zr1))
    # clamp-screw-head relief in the socket floor
    fx0, fx1, fhw, fd = P.FLOOR_RELIEF
    cuts.append(box(fx0, fx1, -fhw, fhw, P.SOCKET_IN_Z0 - fd, P.SOCKET_IN_Z0 + 0.01))
    # M2 x 20 clearance holes along Y
    for (x, z) in P.RCV_SCREWS:
        cuts.append(cyl_y(x, z, P.M2_CLEAR_D, -hw - 1, hw + 1))
    # top long edges of the main body, chamfered only between the raised lip and wall
    # (chamfering under them left sharp 0.5 pockets)
    ce = P.RCV_EDGE_CHAMFER
    for s in (+1, -1):
        for xa, xb in ((P.RCV_X0 - 1, P.FRONT_WALL_X0), (P.STOP_X, P.STRIPPER_X)):
            cuts.append(chamfer_edge_x(xa, xb, s * hw, P.TOP_Z, ce, -s))
        # outer vertical corners of the stripper wall (above the top surface)
        tri = [(P.STRIPPER_X - 0.01, s * (hw - ce)), (P.STRIPPER_X - 0.01, s * (hw + 0.01)), (P.STRIPPER_X + ce, s * (hw + 0.01))]
        cuts.append(cq.Workplane("XY", origin=(0, 0, P.TOP_Z - 0.01)).polyline(tri).close().extrude(5))
        # the socket's top outer edges are chamfered from X 0 on: carry the same chamfer along the
        # stripper wall's top outer edges, or the step at X 0 leaves a 0.37 corner sliver
        cuts.append(chamfer_edge_x(P.STRIPPER_X - 0.01, 0.05, s * hw, P.STRIPPER_WALL_TOP_Z, ce, -s))
    # chamfers on the face-zone edges of the top surface (§8.2) - never on the stripper edge
    zs = P.SOCKET_OUT_Z1
    cuts.append(rim_chamfer(P.PADDLE_X - P.PLUNGER_CH_HW_X, P.PADDLE_X + P.PLUNGER_CH_HW_X,
                            -P.PLUNGER_CH_HW_Y, P.PLUNGER_CH_HW_Y, P.TOP_Z, P.EDGE_CHAMFER))
    cuts.append(chamfer_edge_y(-hw - 1, hw + 1, P.STRIPPER_X, zs, P.EDGE_CHAMFER, +1))   # top of the stripper wall
    sc = P.SMALL_CHAMFER
    gs = P.GATE_SLOT_HW
    cuts.append(chamfer_edge_y(-gs - sc, gs + sc, P.GATE_SLOT_X0, zs, sc, -1))           # gate slot, front rim
    cuts.append(chamfer_edge_y(-gs - sc, 0, P.GATE_SLOT_X1, zs, sc, +1))                 # gate slot, rear rim (-Y)
    cuts.append(chamfer_edge_y(P.TAB_CHANNEL_Y[1], gs + sc, P.GATE_SLOT_X1, zs, sc, +1))  # (+Y)
    cuts.append(chamfer_edge_x(P.GATE_SLOT_X0 - sc, P.GATE_SLOT_X1 + sc, -gs, zs, sc, -1))
    cuts.append(chamfer_edge_x(P.GATE_SLOT_X0 - sc, P.GATE_SLOT_X1 + sc, gs, zs, sc, +1))
    cuts.append(chamfer_edge_x(P.GATE_SLOT_X1, P.SOCKET_L + 1, P.TAB_CHANNEL_Y[1], zs, sc, +1))  # tab channel rim
    li2 = P.BORE_LEADIN
    for s in (+1, -1):   # lead-in on the bore opening's vertical edges at the stop face
        tri = [(0.01, s * (bw - 0.01)), (0.01, s * (bw + li2)), (-li2, s * (bw - 0.01))]
        cuts.append(cq.Workplane("XY", origin=(0, 0, P.CUP_TOP_Z - P.BRIDGE_LEADIN)).polyline(tri).close()
                    .extrude(P.BORE_TOP_Z - P.CUP_TOP_Z + P.BRIDGE_LEADIN))
    for c in cuts:
        r = r.cut(c)

    # latch hook tooth under the tongue tip, 30° lead-in on its +X face.
    # CHANGED (OPEN_ISSUES #1): the latch lives in the -Y half only (Y -4.0 -> 0).
    zt = P.SOCKET_IN_Z1
    ramp = P.TOOTH_H / math.tan(math.radians(P.TOOTH_RAMP_DEG))
    ty0, ty1 = P.LATCH_Y
    tooth = prism_xz([(P.TOOTH_X0, zt + 0.01), (P.TOOTH_X0, zt - P.TOOTH_H),
                      (P.TOOTH_X1 - ramp, zt - P.TOOTH_H), (P.TOOTH_X1, zt + 0.01)], ty0, ty1)
    lx0, lx1, lw, lh = P.LIFT_TAB
    ztop = P.SOCKET_IN_Z1 + P.TONGUE_T
    tab = box(lx0, lx1, ty0, ty1, ztop - 0.01, ztop + lh).edges("|Z or >Z").chamfer(0.5)
    r = r.union(tooth).union(tab)
    # The gate slot (front) and the gate-tab channel (open at the back) cut the +Y
    # half's roof centre off from everything except the -Y half.  After the Y = 0
    # split it would be a loose island, so it is removed (OPEN_ISSUES #1).
    r = r.cut(box(P.GATE_SLOT_X1 - 0.01, P.SOCKET_L + 1, 0, P.TAB_CHANNEL_Y[0],
                  zt - P.TOOTH_H - 0.1, P.SOCKET_OUT_Z1 + 10))
    # the -Y half's roof and tongue edges now exposed at Y = 0 get a small chamfer
    r = r.cut(chamfer_edge_x(P.GATE_SLOT_X1, P.SOCKET_L + 1, 0.0, P.SOCKET_OUT_Z1, P.SMALL_CHAMFER, -1))
    r = r.cut(chamfer_edge_x(P.LIFT_TAB[1], P.TONGUE_ROOT_X, 0.0, P.SOCKET_IN_Z1 + P.TONGUE_T, P.SMALL_CHAMFER, -1))
    _CACHE["full"] = r
    return r


def _half_common(full, side):
    hw = P.RCV_HW
    keep = box(P.RCV_X0 - 5, P.SOCKET_L + 5, 0, side * (hw + 5), P.RCV_BOT_Z - 5, 60)
    return full.intersect(keep)


def receiver_left() -> cq.Workplane:
    """-Y half: Ø1.9 press holes for the dowels, nut traps, ring-hook pilots (mount face)."""
    if "L" in _CACHE:
        return _CACHE["L"]
    hw = P.RCV_HW
    h = _half_common(receiver_full(), -1)
    for (x, z) in P.DOWELS:
        h = h.cut(cyl_y(x, z, P.PIN_PRESS_D, -P.DOWEL_HOLE_DEPTH, 0.01))
    for (x, z) in P.RCV_SCREWS:
        h = h.cut(hex_y(x, z, P.NUT_AF, -hw - 1, -hw + P.NUT_TRAP_DEPTH))
    for (x, z) in P.RING_HOOK_PILOTS:
        h = h.cut(cyl_y(x, z, P.MIN_HOLE_D, -hw - 1, -hw + P.RING_HOOK_PILOT_DEPTH))
    _CACHE["L"] = h
    return h


def receiver_right() -> cq.Workplane:
    """+Y half: Ø2.1 dowel holes, M2 head counterbores."""
    if "R" in _CACHE:
        return _CACHE["R"]
    hw = P.RCV_HW
    h = _half_common(receiver_full(), +1)
    for (x, z) in P.DOWELS:
        h = h.cut(cyl_y(x, z, P.PIN_SNUG_D, -0.01, P.DOWEL_HOLE_DEPTH))
    # pivot pin: pressed into the left half, snug in this one
    h = h.cut(cyl_y(P.PIVOT_X, P.PIVOT_Z, P.RCV_PIVOT_HOLE_R, -0.01, hw - P.PIVOT_HOLE_SKIN))
    for (x, z) in P.RCV_SCREWS:
        h = h.cut(cyl_y(x, z, P.CBORE_D, hw - P.CBORE_DEPTH, hw + 1))
    _CACHE["R"] = h
    return h
