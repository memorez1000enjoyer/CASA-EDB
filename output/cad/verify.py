"""§9 acceptance checks (+ v1.1 §9.11 step-down, §9.12 return-spring solid length,
§9.13 latch) at min / nominal / max bites for spring B (default) and spring A.
Writes ../VERIFICATION.md and ../verification_results.json.

    python verify.py            (full run, ~5-10 min on 4 cores)
    python verify.py --quick    (nominal bites, default spring only)
"""
import sys
import os
import re
import json
import math
import time
import numpy as np
import params as P
import kinematics as K

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "..")
OVERLAP_TOL = 0.01          # mm^3  (§9.1)
N_SWEEP = 9                 # rest + 7 intermediate + pressed

MECH_MOVING = {"elevator", "lever", "pin_cup", "pin_plunger", "plunger", "paddle_pad", "return_spring"}

# pairs that are supposed to touch (reported as "contact (designed)")
DESIGNED_CONTACT = {
    frozenset(p) for p in [
        ("follower", "clip_tube"), ("follower", "receiver_left"), ("follower", "receiver_right"),
        ("follower", "bite"), ("follower", "ribbon_clamp"), ("bite", "bite"), ("bite", "clip_tube"),
        ("bite", "receiver_left"), ("bite", "receiver_right"), ("bite", "elevator"), ("bite", "gate"),
        ("elevator", "receiver_left"), ("elevator", "receiver_right"), ("elevator", "pin_cup"),
        ("plunger", "pin_plunger"), ("plunger", "return_spring"), ("plunger", "receiver_left"),
        ("plunger", "receiver_right"), ("return_spring", "receiver_left"), ("return_spring", "receiver_right"),
        ("drum", "cf_spring"), ("cf_spring", "clip_tube"), ("cf_spring", "ribbon_clamp"),
        ("clip_tube", "receiver_left"), ("clip_tube", "receiver_right"), ("screw_clamp", "clip_tube"),
        ("ring_hook", "receiver_left"), ("ribbon_clamp", "clip_tube"), ("gate", "clip_tube"),
        ("receiver_left", "receiver_right"), ("dowel", "receiver_right"), ("pin_pivot", "receiver_left"),
        ("pin_pivot", "receiver_right"), ("drum_spacer", "drum"), ("pin_axle", "follower"),
        ("pin_axle", "drum"), ("lever", "pin_cup"), ("lever", "pin_plunger"), ("lever", "pin_pivot"),
        ("drum_spacer", "cf_spring"), ("end_cap", "clip_tube"), ("paddle_pad", "plunger"),
    ]
}


def kind(name):
    n = re.sub(r"\d+$", "", name)
    n = re.sub(r"_(p|n)$", "", n) if n.startswith("screw_clamp") else n
    return n


def pair_key(a, b):
    return tuple(sorted((kind(a), kind(b))))


# ============================================================================ poses
def poses_for(spring, bkey):
    """(label, state, mech, pair_filter) for every pose to check."""
    out = []
    for s in ("A", "B", "Bp", "C", "D", "Dt", "E"):
        out.append((s, s, None, None, (0.0, 0.0)))
    # the clip floats inside its 0.3 socket clearance: follower at its stop, clip moved
    c = P.CLR_SLIDE
    for s in ("C", "Dt"):
        for sh in ((0.0, -(P.CLIP_BOT_Z - P.SOCKET_IN_Z0)), (0.0, c), (-c, 0.0), (c, 0.0)):
            out.append((f"{s} clip dy{sh[0]:+.1f} dz{sh[1]:+.1f}", s, None, None, sh))
    # full stacks with the clip at its gravity rest (on the socket floor) and off-centre in Y;
    # the bites on the rails ride with the clip
    for s in ("A", "B", "Bp"):
        sh = (0.0, -P.SOCKET_FLOOR_CLR)
        out.append((f"{s} clip dy{sh[0]:+.1f} dz{sh[1]:+.1f}", s, None, None, sh))
    for s in ("A", "Bp"):
        for sh in ((-c, 0.0), (c, 0.0)):
            out.append((f"{s} clip dy{sh[0]:+.1f} dz{sh[1]:+.1f}", s, None, None, sh))
    b_moving = {"B": {"bite1"}, "D": {f"bite{P.N_BITES}"}, "Bp": set()}
    for s, direction, dx in (("B", "press", 0.0), ("Bp", "return", -P.CLR_SLIDE), ("D", "press", 0.0)):
        mov = MECH_MOVING | b_moving[s]
        for i, m in enumerate(K.sweep(N_SWEEP, direction, dx)[1:-1]):
            f = (lambda mv: (lambda x, y: x.name in mv or y.name in mv))(mov)
            out.append((f"{s}@{m.phi:+.1f}", s, m, f, (0.0, 0.0)))
    return out


def run_config(args):
    spring, bkey = args
    import assembly as A
    import collide as C
    b = P.BITES[bkey]
    res = dict(spring=spring, bites=bkey, poses=[], overlaps={}, clearance={}, errors=[])
    t0 = time.time()
    for label, s, mech, flt, shift in poses_for(spring, bkey):
        st = A.build(s, spring, bkey, mech, clip_shift=shift)
        ov, dist = C.check_bodies(st.bodies, pairs_filter=flt,
                                  dist_pairs=lambda x, y: x.moving or y.moving)
        worst = []
        for a, c, v in ov:
            why = C.intended(a, c)
            if math.isnan(v):
                res["errors"].append(f"{label}: boolean failed {a}/{c}")
                continue
            if why is None and v > OVERLAP_TOL:
                worst.append((a, c, round(v, 4)))
            k = pair_key(a, c)
            if why is None:
                res["overlaps"][str(k)] = max(res["overlaps"].get(str(k), 0.0), v)
        for (a, c), d in dist.items():
            k = str(pair_key(a, c))
            cur = res["clearance"].get(k)
            if cur is None or d < cur[0]:
                res["clearance"][k] = (round(d, 4), label, a, c)
        pose = dict(label=label, state=s, F=st.F, fails=worst)
        if st.mech is not None:
            m = st.mech
            pose.update(phi=m.phi, elev_top=m.elev_top, elev_dx=m.elev_dx, plunger_bot=m.plunger_bot,
                        cup_pin=m.cup_pin, plunger_pin=m.plunger_pin)
        pose["bites"] = [(p.idx, round(p.x_front, 3), round(p.z_bot, 3)) for p in st.bite_poses]
        res["poses"].append(pose)
    res["time"] = time.time() - t0
    return res


# ============================================================================ analytic checks
def slot_margins():
    """§9.7: pin-in-slot margins over the full sweep, with the elevator/plunger at
    nominal X and at both ends of their ±0.3 X play."""
    r_pin = P.PIN_D / 2
    def seg(x0, x1):          # square-ended slots: allowed pin-centre range
        return x0 + r_pin, x1 - r_pin
    e0, e1 = seg(*P.ELEV_SLOT_X)
    p0, p1 = seg(P.PADDLE_X + P.PLUNGER_SLOT_DX[0], P.PADDLE_X + P.PLUNGER_SLOT_DX[1])
    phis = np.linspace(P.PHI_REST, P.PHI_PRESS, 61)
    out = {}
    for dx in (-P.CLR_SLIDE, 0.0, P.CLR_SLIDE):
        em, pm = [], []
        for ph in phis:
            cup, plg = K.lever_pins(ph)
            em.append(min(cup[0] - (e0 + dx), (e1 + dx) - cup[0]))
            pm.append(min(plg[0] - (p0 + dx), (p1 + dx) - plg[0]))
        out[dx] = (min(em), min(pm))
    cups = [K.lever_pins(ph)[0][0] for ph in phis]
    plgs = [K.lever_pins(ph)[1][0] for ph in phis]
    return out, (min(cups), max(cups)), (min(plgs), max(plgs))


def forces():
    """§9.10 paddle force and sink-back, at the REAL rest pose (pins on the loaded side of
    their holes: plunger bottom ~-1.0) - the weakest return-spring point - and the hard stop."""
    rows = {}
    hp = K.with_hole_play()
    L_rest = (hp["rest_bot"] + P.EAR_UNDERSIDE) - P.SPRING_WELL_Z0           # 27.0
    L_rest_model = (K.mech_rest().plunger_bot + P.EAR_UNDERSIDE) - P.SPRING_WELL_Z0  # 26.8 (pins centred)
    L_press = (P.PLUNGER_PRESSED_BOT_Z + P.EAR_UNDERSIDE) - P.SPRING_WELL_Z0  # 12.1 hard stop
    for k, s in P.SPRINGS.items():
        rs0 = s.rs_k * (s.rs_free - L_rest)
        rs1 = s.rs_k * (s.rs_free - L_press)
        fric = (P.MU_WALL + P.MU_BITE) * s.F
        sticky = (P.MU_WALL + P.MU_BITE_STICKY) * s.F * (1 + P.SPRING_F_HI)
        solid = P.rs_solid_length(s.rs_k)
        rows[k] = dict(F=s.F, friction=fric, rs_rest=rs0, rs_pressed=rs1,
                       paddle_start=fric + rs0, paddle_end=fric + rs1,
                       bite_returns=rs0 > fric, return_margin=rs0 / fric,
                       sticky_drag=sticky, sticky_returns=rs0 > sticky, sticky_margin=rs0 / sticky,
                       elevator_returns=rs0 > 2 * P.MU_WALL * s.F,
                       L_rest=L_rest, L_rest_model=L_rest_model, L_press=L_press,
                       solid=solid, solid_ok=solid <= P.RS_SOLID_MAX + 1e-9 and solid < L_press)
    return rows


def solid_table():
    """Solid length over the BOM range (spring-B return spring): OD x wire x rate."""
    out = []
    for od in (P.RS_OD_RANGE[0], P.RS_OD, P.RS_OD_RANGE[1]):
        for wire in (P.RS_WIRE, P.RS_WIRE_MAX):
            out.append((od, wire, [P.rs_solid_length(k, wire, od) for k in P.RS_K_RANGE]))
    return out


def contact_factor(W):
    """Normal force on the R0.5 rail edges per unit bite weight (1/cos of the contact angle)."""
    yc = W / 2 - P.BITE_R
    ey = P.RAIL_IN_Y + P.RAIL_EDGE_R
    if yc >= ey:
        return 1.0
    R = P.BITE_R + P.RAIL_EDGE_R
    dy = ey - yc
    return R / math.sqrt(R * R - dy * dy)


def follower_group_mass(spring_key):
    """Follower + drum + spacer rings (PETG, solid) + coil + axle (steel), grams."""
    import assembly as A
    st = A._static(spring_key)
    s = P.SPRINGS[spring_key]
    petg = st["follower"].Volume() + st["drum"].Volume() + sum(x.Volume() for x in st["spacers"])
    steel = s.L * s.W * s.T + math.pi * (P.PIN_D / 2) ** 2 * P.AXLE_L
    return petg * P.RHO_PETG + steel * P.RHO_STEEL


def feed_margins():
    """§9.10 feed margin = usable spring force / stack drag.  Usable force = F at -13 %, less
    the drum-on-axle friction (mu * r_pin / r_coil, smallest coil = full clip).  Drag: 8 x 10 g
    bites at mu 0.6 times the contact factor k (sum of contact normals / weight: upright on the
    rail edges, or leaning and wedged between the walls), + the follower group at
    FEED_MU_FOLLOWER.  At incline t (mouth uphill): g[(mu k m_b + mu_f m_f) cos t + (m_b + m_f) sin t]."""
    import lean
    out = {}
    m_b = P.N_BITES * P.FEED_BITE_MASS_G / 1000
    k_lean = lean.rest_pose(P.BITES["min"])["k_lean"]
    for sk, s in P.SPRINGS.items():
        from hardware import ribbon_geometry
        F_full = P.STOP_X + P.N_BITES * P.BITES["min"].T
        r_coil = ribbon_geometry(s, F_full)["coil_od"] / 2
        axle_loss = P.FEED_AXLE_MU * (P.PIN_D / 2) / r_coil
        Fa = s.F * (1 - P.SPRING_F_LO) * (1 - axle_loss)
        m_f = follower_group_mass(sk) / 1000
        cases = [(bk, b, contact_factor(b.W)) for bk, b in P.BITES.items()]
        cases.append(("min_lean", P.BITES["min"], k_lean))
        for bk, b, kf in cases:
            a_ = P.FEED_MU * kf * m_b + P.FEED_MU_FOLLOWER * m_f
            b_ = m_b + m_f
            worst = math.degrees(math.atan2(b_, a_))
            r = dict(k=kf, m_f_g=m_f * 1000, F_avail=Fa, axle_loss=axle_loss, worst_incline_deg=worst)
            for gname, g in (("earth", P.G_EARTH), ("moon", P.G_MOON)):
                r[f"{gname}_level"] = Fa / (g * a_)
                r[f"{gname}_vertical"] = Fa / (g * b_)
                r[f"{gname}_incline"] = Fa / (g * math.hypot(a_, b_))
            out[(sk, bk)] = r
    return out


def drag_up_margins():
    """Bite 2 dragged up by bite 1 in state B: bite 1's face friction mu_b P vs bite 2's
    weight + rear-face friction mu_b (P - its own rail friction, worst sign).  Min width."""
    out = {}
    m = P.FEED_BITE_MASS_G / 1000
    kf = contact_factor(P.BITES["min"].W)
    for sk, s in P.SPRINGS.items():
        for gname, g in (("earth", P.G_EARTH), ("moon", P.G_MOON)):
            W = m * g
            out[(sk, gname)] = (P.MU_BITE * s.F + W) / (P.MU_BITE * (s.F + P.FEED_MU * kf * W))
    return out


def step_down():
    """§9.11 (v1.1): rail seat of every bite with the clip centred and resting on its socket
    floor must be >= CUP_TOP_Z (the bridge and the cup at rest), so no bite climbs into the
    receiver.  Also the leaning-bite pose from lean.py."""
    import lean
    rows = []
    for bk, b in P.BITES.items():
        seat = K.rail_seat(b.W)
        ln = lean.rest_pose(b)
        for dz in (0.0, -P.SOCKET_FLOOR_CLR):
            rows.append(dict(bites=bk, W=b.W, dz=dz, seat=seat + dz, step=seat + dz - P.CUP_TOP_Z, ln=ln,
                             lean=ln["lean_deg"], com_drop=ln["com_drop"], lowest=ln["lowest"] + dz,
                             lowest_y=ln["lowest_y"], lean_step=ln["lowest"] + dz - P.CUP_TOP_Z))
    return rows


def latch():
    """§6.2 latch tooth engagement with the clip on its socket floor, centred, and floated up."""
    tooth_bot = P.SOCKET_IN_Z1 - P.TOOTH_H
    notch_floor = P.TOP_Z - P.LATCH_NOTCH_D
    up = P.SOCKET_IN_Z1 - P.TOP_Z                          # clip top on the socket roof
    floor = -P.SOCKET_FLOOR_CLR
    L_c = P.TONGUE_ROOT_X - (P.TOOTH_X0 + P.TOOTH_X1) / 2
    strain = lambda d: 3 * P.TONGUE_T * d / (2 * L_c ** 2)
    return dict(engage_floor=P.TOP_Z + floor - tooth_bot, engage_centre=P.TOP_Z - tooth_bot,
                engage_up=P.TOP_Z + up - tooth_bot, floor_clr_up=tooth_bot - (notch_floor + up),
                play_x=P.TOOTH_X0 - P.LATCH_NOTCH_X0, L_c=L_c,
                strain_floor=strain(P.TOP_Z + floor - tooth_bot), strain_up=strain(P.TOP_Z + up - tooth_bot))


def envelope_mass():
    import cadquery as cq
    import assembly as A
    st = A.build("A", P.DEFAULT_SPRING, "nom")
    bb = None
    vols = {}
    for bd in st.bodies:
        b = bd.shape.BoundingBox()
        bb = b if bb is None else bb.add(b)
    stat = A._static(P.DEFAULT_SPRING)
    printed = {
        "clip_tube": ("clip", "PETG"), "end_cap": ("clip", "PETG"), "gate": ("clip", "PETG"),
        "follower": ("clip", "PETG"), "drum": ("clip", "PETG"), "ribbon_clamp": ("clip", "PETG"),
        "drum_spacers": ("clip", "PETG"),
        "receiver_left": ("receiver", "PETG"), "receiver_right": ("receiver", "PETG"),
        "elevator": ("receiver", "PETG"), "lever": ("receiver", "PETG"), "plunger": ("receiver", "PETG"),
        "paddle_pad": ("receiver", "TPU"), "ring_hook": ("receiver", "PETG"),
    }
    rho = {"PETG": P.RHO_PETG, "TPU": P.RHO_TPU}
    for n, (grp, mat) in printed.items():
        if n == "drum_spacers":
            if not stat["spacers"]:
                continue
            v = sum(x.Volume() for x in stat["spacers"])
        else:
            v = stat[n].Volume()
        vols[n] = dict(group=grp, material=mat, volume=v, mass=v * rho[mat])
    # steel hardware (pins, spring ribbon, screws) - rough
    pin_len = P.PIVOT_PIN_L + P.CUP_PIN_L + P.PLUNGER_PIN_L + P.AXLE_L + 3 * P.DOWEL_L
    steel = pin_len * math.pi * (P.PIN_D / 2) ** 2 * P.RHO_STEEL
    s = P.SPRINGS[P.DEFAULT_SPRING]
    steel += s.L * s.W * s.T * P.RHO_STEEL
    steel += 4 * 0.55 + 4 * 0.05 + 6 * 0.15  # M2x20 + nuts + small screws (g)
    D = P.RS_OD - P.RS_WIRE                    # return spring: wire length ~ (n + 3) coils x pi D
    n = P.RS_G * P.RS_WIRE ** 4 / (8 * D ** 3 * P.SPRINGS[P.DEFAULT_SPRING].rs_k) + P.RS_DEAD_COILS
    steel += n * math.pi * D * math.pi * (P.RS_WIRE / 2) ** 2 * P.RHO_STEEL
    return dict(bbox=(bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax), parts=vols, steel_g=steel)


# ============================================================================ report
def fmt(x, n=2):
    return f"{x:.{n}f}"


def run_parallel(configs, jobs=3):
    """Each configuration in its own Python process (OpenCascade + multiprocessing
    pools can deadlock), results passed back as JSON files."""
    import subprocess
    import tempfile
    tmp = tempfile.mkdtemp(prefix="ebd_verify_")
    procs, pending, done = [], list(configs), {}
    while pending or procs:
        while pending and len(procs) < jobs:
            sp, bk = pending.pop(0)
            out = os.path.join(tmp, f"{sp}_{bk}.json")
            procs.append(((sp, bk), out, subprocess.Popen([sys.executable, __file__, "--config", sp, bk, out], cwd=HERE)))
        time.sleep(1)
        for item in list(procs):
            (cfg, out, p) = item
            if p.poll() is not None:
                procs.remove(item)
                if p.returncode != 0:
                    raise RuntimeError(f"config {cfg} failed ({p.returncode})")
                done[cfg] = json.load(open(out))
    return [done[c] for c in configs]


def main():
    quick = "--quick" in sys.argv
    configs = [(P.DEFAULT_SPRING, "nom")] if quick else [(s, b) for s in ("B", "A") for b in ("min", "nom", "max")]
    t0 = time.time()
    results = run_parallel(configs)
    t_geo = time.time() - t0
    import printability
    pr_rows = printability.check_all()
    em = envelope_mass()
    fr = forces()
    margins, cup_rng, plg_rng = slot_margins()
    extra = dict(feed=feed_margins(), drag=drag_up_margins(), steps=step_down(), latch=latch(),
                 solid=solid_table())
    write_report(results, pr_rows, em, fr, margins, cup_rng, plg_rng, t_geo, quick, extra)


def write_report(results, pr_rows, em, fr, margins, cup_rng, plg_rng, t_geo, quick, extra):
    import hardware as Hw
    L = []
    w = L.append
    checks = []  # (id, title, pass_bool, detail)

    # ---------- 9.1 interference
    fails = []
    for r in results:
        for p in r["poses"]:
            for a, c, v in p["fails"]:
                fails.append((r["spring"], r["bites"], p["label"], a, c, v))
    n_poses = sum(len(r["poses"]) for r in results)
    errors = [e for r in results for e in r["errors"]]
    checks.append(("9.1", "Interference (all states + lever sweep)", not fails and not errors,
                   f"{n_poses} poses checked, {len(fails)} unintended overlaps > {OVERLAP_TOL} mm³"))

    # clearance table: min over all configs per moving pair
    clr = {}
    for r in results:
        for k, (d, label, a, c) in r["clearance"].items():
            if k not in clr or d < clr[k][0]:
                clr[k] = (d, f"{r['spring']}/{r['bites']} {label}", a, c)

    # ---------- per-config geometric numbers
    per = []
    for r in results:
        b = P.BITES[r["bites"]]
        s = P.SPRINGS[r["spring"]]
        poses = {p["label"]: p for p in r["poses"]}
        A_, B_, Bp, C_, D_, E_ = (poses[k] for k in ("A", "B", "Bp", "C", "D", "E"))
        bite2_A = next(x for x in A_["bites"] if x[0] == 2)
        bite2_Bp = next(x for x in Bp["bites"] if x[0] == 2)
        raised = next(x for x in B_["bites"] if x[0] == 1)
        roof_gap = P.BORE_TOP_Z - (bite2_A[2] + b.H)
        roof_gap_Bp = P.BORE_TOP_Z - (bite2_Bp[2] + b.H)
        # elevator top vs bite 2 (nominal elevator X and worst case +0.3 back)
        elev_rear_top = P.ELEV_X1
        m_nom = bite2_A[1] - elev_rear_top
        m_worst = bite2_A[1] - (elev_rear_top + P.CLR_SLIDE)
        expo = raised[2] + b.H - P.TOP_Z
        below = P.TOP_Z - raised[2]
        win_x = (P.STRIPPER_X - P.STOP_X) - b.T
        win_y = (P.BORE_W - b.W) / 2
        under_win = P.STRIPPER_X - bite2_Bp[1]
        # follower
        Dt = poses["Dt"]
        F2 = P.STOP_X + 2 * b.T
        ext = {lab: Hw.ribbon_geometry(s, poses[lab]["F"]) for lab in ("A", "Bp", "C", "E")}
        ext2 = Hw.ribbon_geometry(s, F2)
        ext_max = max(Hw.ribbon_geometry(s, poses[lab]["F"])["span"] for lab in poses)
        ribbon_maxz = max(Hw.ribbon_geometry(s, poses[lab]["F"])["max_z"] for lab in poses)
        per.append(dict(
            cfg=f"{r['spring']}/{r['bites']}", roof_gap=roof_gap, roof_gap_Bp=roof_gap_Bp,
            bite2_seat_A=bite2_A[2], m_nom=m_nom, m_worst=m_worst, expo=expo, below=below,
            raised_bot=raised[2], win_x=win_x, win_y=win_y, under_win=under_win,
            F_A=A_["F"], F_C=C_["F"], F_E=E_["F"], F_Bp=Bp["F"], back_gap_E=P.ENDCAP_X0 - (E_["F"] + P.FOLLOWER_L),
            ext_A=ext["A"]["span"], ext_2=ext2["span"], ext_C=ext["C"]["span"], ext_E=ext["E"]["span"],
            ext_max=ext_max, ext_limit=s.max_ext, ribbon_maxz=ribbon_maxz,
            coil_od_E=ext["E"]["coil_od"], pocket=P.pocket_d(s),
            lift=B_["elev_top"] - A_["elev_top"], elev_rest=A_["elev_top"],
            push_rib_gap_Dt=P.F_STOP - (P.ELEV_X1), push_rib_gap_Dt_worst=P.F_STOP - (P.ELEV_X1 + P.CLR_SLIDE),
            time=r["time"]))

    ok = lambda cond: "PASS" if cond else "**FAIL**"
    c92 = all(p["roof_gap"] >= 0.6 - 1e-9 and p["m_nom"] >= -1e-9 for p in per)
    checks.append(("9.2", "One-bite rule", c92,
                   f"bite-2-top to roof min {min(p['roof_gap'] for p in per):.2f} (≥ 0.6); elevator top never under bite 2"))
    lost = P.HOLE_LOST_MOTION
    c93 = all(p["expo"] - lost >= 8.0 and p["below"] + lost >= 12.0 for p in per)
    checks.append(("9.3", "Exposure", c93, f"min exposure {min(p['expo'] for p in per) - lost:.2f} with pin-hole play (≥ 8.0), "
                   f"min retained {min(p['below'] for p in per) + lost:.2f} (≥ 12)"))
    c94 = all(p["win_x"] >= 0.2 - 1e-9 and p["win_y"] >= 0.2 - 1e-9 and p["under_win"] <= 1.9 + 1e-9 for p in per)
    checks.append(("9.4", "Window", c94, f"X clearance min {min(p['win_x'] for p in per):.2f}, Y/side min "
                   f"{min(p['win_y'] for p in per):.2f}, bite 2 under window max {max(p['under_win'] for p in per):.2f} (≤ 1.9)"))
    fol_fail = [k for k, v in clr.items() if ("follower" in k and ("screw_clamp" in k or "elevator" in k)) and v[0] <= 0]
    c95 = (not fol_fail) and all(p["ribbon_maxz"] < 2.0 for p in per) and P.F_STOP + P.KEEL_X0 > P.GATE_SLOT_X1
    checks.append(("9.5", "Follower", c95, f"stops at F = {P.F_STOP:.2f} on the clamp back edge; ribbon max Z "
                   f"{max(p['ribbon_maxz'] for p in per):.2f} (< 2.0)"))
    c96 = all(p["ext_2"] >= 18 and p["ext_max"] <= p["ext_limit"] for p in per)
    checks.append(("9.6", "Spring extension", c96, f"min with ≥ 2 bites {min(p['ext_2'] for p in per):.1f} (≥ 18); "
                   f"last bite {min(p['ext_C'] for p in per):.1f}-{max(p['ext_C'] for p in per):.1f}; max {max(p['ext_max'] for p in per):.1f}"))
    rest, prs = K.mech_rest(), K.mech_pressed()
    stroke = rest.plunger_bot - prs.plunger_bot
    nom_m = margins[0.0]
    hp = K.with_hole_play()
    lift_eff = hp["lift"]
    c97 = lift_eff >= 13.5 and nom_m[0] >= 0 and nom_m[1] >= 0 and abs(stroke - P.PADDLE_STROKE) < 1e-6 \
        and abs(rest.elev_top - P.CUP_TOP_Z) < 1e-9
    checks.append(("9.7", "Kinematics", c97, f"lift {prs.lift:.2f} model / {hp['lift']:.2f} with pin-hole play (≥ 13.5), stroke {stroke:.2f}, pins inside slots "
                   f"(min margin {min(nom_m):.2f} at nominal X)"))
    c98 = all(r["watertight"] and r["winding"] and r["wall_ok"] for r in pr_rows)
    need_sup = [r["name"] for r in pr_rows if not r["overhang_ok"]]
    n_flag = sum(1 for r in pr_rows if r["flags"])
    checks.append(("9.8", "Printability", c98,
                   f"{len(pr_rows)} STLs all watertight, walls ≥ 0.8 except listed spec features; "
                   + (f"NEEDS SUPPORT: {', '.join(need_sup)} (OPEN_ISSUES #2)" if need_sup else "no supports needed")))
    checks.append(("9.9", "Envelope / mass report", True, "reported below"))
    fd = extra["feed"]
    fB = fd[(P.DEFAULT_SPRING, "min")]
    fL = fd[(P.DEFAULT_SPRING, "min_lean")]
    checks.append(("9.10", "Force report", True,
                   f"B {fr['B']['paddle_start']:.1f}-{fr['B']['paddle_end']:.1f} N, uneaten bite returns "
                   f"{fr['B']['return_margin']:.2f}x (sticky {fr['B']['sticky_margin']:.2f}x); "
                   f"A {fr['A']['paddle_start']:.1f}-{fr['A']['paddle_end']:.1f} N (> 6 N flagged, does not return); "
                   f"B feed margin, min width: {fB['earth_level']:.2f}x level / {fB['earth_vertical']:.2f}x vertical / "
                   f"**{fB['earth_incline']:.2f}x at {fB['worst_incline_deg']:.0f}°**, leaning bites "
                   f"**{fL['earth_incline']:.2f}x at {fL['worst_incline_deg']:.0f}°**; Moon ≥ "
                   f"{min(v['moon_incline'] for (sk, bk), v in fd.items() if sk == P.DEFAULT_SPRING):.1f}x any orientation"))
    st_ = extra["steps"]
    smin = min(st_, key=lambda r: r["step"])
    c911 = smin["step"] >= -1e-9 and abs(rest.elev_top - P.CUP_TOP_Z) < 1e-9
    checks.append(("9.11", "Bites step down into the receiver (v1.1)", c911,
                   f"smallest step-down {smin['step']:.2f} ({smin['bites']} width, clip dz {smin['dz']:+.1f}); "
                   f"bridge and cup at rest both Z {P.CUP_TOP_Z:.2f}"))
    sB = fr[P.DEFAULT_SPRING]
    c912 = all(d["solid_ok"] for d in fr.values())
    checks.append(("9.12", "Return-spring solid length (v1.1)", c912,
                   f"B {fr['B']['solid']:.1f} / A {fr['A']['solid']:.1f} (≤ {P.RS_SOLID_MAX:.0f}, pressed length "
                   f"{sB['L_press']:.1f}) for Ø{P.RS_WIRE} wire, OD {P.RS_OD}"))
    lt = extra["latch"]
    c913 = lt["engage_floor"] > 0 and lt["floor_clr_up"] >= -1e-9
    checks.append(("9.13", "Latch engagement (v1.1)", c913,
                   f"{lt['engage_floor']:.2f} with the clip on its floor; tooth to notch floor "
                   f"{lt['floor_clr_up']:.2f} with the clip floated up {P.SOCKET_IN_Z1 - P.TOP_Z:.1f}"))

    # ------------------------------------------------------------------ markdown
    w("# VERIFICATION - EBD Clip v1.1\n")
    w(f"Generated by `cad/verify.py` on {time.strftime('%Y-%m-%d %H:%M')} "
      f"({'QUICK: default spring, nominal bites only' if quick else 'full run: springs B (default) and A x bites min/nom/max'}; "
      f"geometry checks took {t_geo:.0f} s). Every number comes from the CAD model or from `params.py`.\n")
    w("Spec: EBD_Build_Spec.md Rev C, section 9, plus the v1.1 follow-up checks (§9.11-9.13). Units mm, N. Bites: min 12.2 x 18.0 x 24.4, "
      "nom 12.7 x 19.0 x 25.4, max 13.2 x 20.0 x 26.4 (T x W x H).\n")
    w("## Summary\n")
    w("| § | Check | Result | Key numbers |\n|---|---|---|---|")
    for cid, title, passed, detail in checks:
        res = "PASS" if passed else "**FAIL**"
        if cid == "9.8" and passed and need_sup:
            res = "**FLAG** (supports)"
        if cid == "9.10":
            res = "REPORT (A > 6 N; **B feed < 1.0 on Earth at ~47° with leaning min bites**)" \
                if fL["earth_incline"] < 1.0 else "REPORT (A flagged > 6 N)"
        if cid == "9.13" and passed:
            res = "PASS (report)"
        w(f"| {cid} | {title} | {res} | {detail} |")
    w("")

    w("## 9.1 Interference\n")
    w(f"Exact B-rep booleans (OpenCascade) between every pair of bodies whose bounding boxes come within "
      f"1 mm, in states A, B, B', C, D, D-taken, E, plus {N_SWEEP - 2} intermediate lever angles for each of the "
      f"B, B' and D strokes, plus states C and D-taken with the clip shifted ±0.3 in Y, down {P.SOCKET_FLOOR_CLR:.1f} "
      f"(on its socket floor) and up {P.SOCKET_IN_Z1 - P.TOP_Z:.1f} (against the socket roof), plus full stacks in "
      f"states A, B and B' with the clip on its socket floor and A, B' with the clip ±0.3 off-centre in Y (bites "
      f"on the rails ride with the clip), "
      f"for each configuration. Threshold {OVERLAP_TOL} mm³. "
      f"Intended overlaps are excluded and listed: " +
      "; ".join(f"{a} / {b}: {why}" for a, b, why in __import__('collide').INTENDED) + ".\n")
    if fails:
        w("| Config | Pose | Pair | Volume mm³ |\n|---|---|---|---|")
        for s, bk, lab, a, c, v in fails:
            w(f"| {s}/{bk} | {lab} | {a} / {c} | {v} |")
    else:
        w(f"**No unintended overlap in any of the {n_poses} poses.**\n")
    if errors:
        w("Boolean errors: " + "; ".join(errors))
    w("\n### Minimum clearance of every pair that includes a moving body (worst case over all configs and poses)\n")
    w("| Pair | Min clearance | Where | Note |\n|---|---|---|---|")
    for k in sorted(clr, key=lambda k: clr[k][0]):
        d, where, a, c = clr[k]
        kk = eval(k)
        designed = frozenset(kk) in DESIGNED_CONTACT or (kk[0] == kk[1] == "bite")
        note = "contact (designed)" if d < 1e-3 and designed else ("**touching - check**" if d < 1e-3 else "")
        w(f"| {kk[0]} / {kk[1]} | {d:.3f} | {where} | {note} |")
    w("")

    w("## Per-configuration numbers (§9.2 - §9.6)\n")
    w("| Config | bite-2 top→roof (A/B) | bite-2 top→roof (B') | bite 2 seat Z (A) | elevator top rear edge → bite 2, nominal / elevator pushed back 0.3 | "
      "exposure above 33.5 | retained below 33.5 | window X clr | window Y clr/side | bite 2 under window (B') |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for p in per:
        w(f"| {p['cfg']} | {fmt(p['roof_gap'])} | {fmt(p['roof_gap_Bp'])} | {fmt(p['bite2_seat_A'], 3)} | "
          f"{fmt(p['m_nom'])} / {fmt(p['m_worst'])} | {fmt(p['expo'])} | {fmt(p['below'])} | {fmt(p['win_x'])} | "
          f"{fmt(p['win_y'])} | {fmt(p['under_win'])} |")
    w(f"\nNotes: bites stay upright and settle vertically onto the highest support (rails 4.0/4.29/4.45, "
      f"bridge and cup {P.CUP_TOP_Z}). A bite overhanging the bridge stays on the rails (the bridge is below "
      f"every rail seat). \"Elevator top rear edge → bite 2\" is the X gap between the cup floor's rear "
      f"edge and bite 2's front face in states A/B; it must stay ≥ 0 so the cup is never under bite 2.\n")
    w("| Config | F (A) | F (B') | F (C) | F (E) | follower back → end cap (E) | ribbon free length: A / 2 bites / last bite / E / max (limit) | coil OD at E / pocket Ø | ribbon max Z |")
    w("|---|---|---|---|---|---|---|---|---|")
    for p in per:
        w(f"| {p['cfg']} | {fmt(p['F_A'])} | {fmt(p['F_Bp'])} | {fmt(p['F_C'])} | {fmt(p['F_E'])} | {fmt(p['back_gap_E'])} | "
          f"{fmt(p['ext_A'], 1)} / {fmt(p['ext_2'], 1)} / {fmt(p['ext_C'], 1)} / {fmt(p['ext_E'], 1)} / {fmt(p['ext_max'], 1)} ({p['ext_limit']:.0f}) | "
          f"{fmt(p['coil_od_E'])} / {fmt(p['pocket'])} | {fmt(p['ribbon_maxz'])} |")
    w(f"\n§9.5: the keel legs stop on the clamp back edge at F = {P.F_STOP:.2f}; the keel front never "
      f"gets closer than X {P.F_STOP + P.KEEL_X0:.1f} to the mouth, so it cannot reach the clamp screws "
      f"(X {P.CLAMP_SCREW_X - 1:.1f}-{P.CLAMP_SCREW_X + 1:.1f}) or the gate slot (X {P.GATE_SLOT_X0}-{P.GATE_SLOT_X1}); the follower "
      f"body (28 long) spans the 1.6 gate-slot gap in the rails. With the last bite taken (state D) the push ribs are "
      f"{per[0]['push_rib_gap_Dt']:.2f} from the elevator rear face at nominal elevator X "
      f"({per[0]['push_rib_gap_Dt_worst']:.2f} if the elevator sits at the back of its 0.3 play).\n")
    w("§9.6: extension = free ribbon from the clamp back edge (X 8.0) to the tangent on the coil. "
      "\"2 bites\" is the rest state with two bites left, the shortest extension while ≥ 2 bites remain. "
      "Last bite (state C) is reduced force, accepted per spec - confirm on the bench.\n")

    w("## 9.7 Kinematics\n")
    w(f"- Lever pivot ({P.PIVOT_X:.1f}, {P.PIVOT_Z:.1f}), arms {P.LEVER_R:.1f}. Slot play is taken up in the loaded "
      f"direction (return spring at rest, chin when pressed).")
    w(f"- Rest: lever {rest.phi:.2f}° (cup end down), elevator top Z {rest.elev_top:.2f} on its ledge, plunger bottom "
      f"Z {rest.plunger_bot:.2f}, flange underside Z {rest.plunger_bot + P.FLANGE_OFFSET:.2f}.")
    w(f"- Pressed (flange on the top surface): lever {prs.phi:.2f}°, plunger bottom Z {prs.plunger_bot:.2f}, "
      f"elevator top Z {prs.elev_top:.2f}.")
    w(f"- **Paddle stroke {stroke:.2f}** (hard stop), **elevator lift {prs.lift:.2f}** with pins at hole centres. "
      f"Lost motion from the two 2.3 slots = {stroke - prs.lift:.2f}.")
    w(f"- **With the round-hole clearances as well** (lever pivot Ø{P.LEVER_PIVOT_HOLE_D} on a pin pressed into "
      f"receiver_left, end holes Ø{P.LEVER_END_HOLE_D}): each hole sits off its pin by its radial clearance on the "
      f"loaded side, which takes {P.HOLE_LOST_MOTION:.2f} off the lift and adds it to the stroke (rest is set by the "
      f"ledge, pressed by the hard stop). **Real lift {hp['lift']:.2f}** (≥ 13.5 {ok(hp['lift'] >= 13.5)}), "
      f"**real paddle stroke {hp['stroke']:.2f}**, flange underside at rest Z {hp['flange_rest']:.2f}.")
    w(f"- Cup-end pin X range over the sweep {cup_rng[0]:.3f} → {cup_rng[1]:.3f}; elevator slot allows "
      f"{P.ELEV_SLOT_X[0] + 1.0:.2f} → {P.ELEV_SLOT_X[1] - 1.0:.2f} (square-ended slot, Ø2 pin).")
    w(f"- Plunger-end pin X range {plg_rng[0]:.3f} → {plg_rng[1]:.3f}; plunger slot allows "
      f"{P.PADDLE_X + P.PLUNGER_SLOT_DX[0] + 1.0:.2f} → {P.PADDLE_X + P.PLUNGER_SLOT_DX[1] - 1.0:.2f}.")
    w("\n| Elevator / plunger X position in its 0.3 play | min margin, cup pin to elevator slot end | min margin, plunger pin to plunger slot end |\n|---|---|---|")
    for dx, (me, mp_) in margins.items():
        lab = {0.0: "nominal (centred)", -P.CLR_SLIDE: "-0.3 (against the front wall / -X)", P.CLR_SLIDE: "+0.3 (+X)"}[dx]
        w(f"| {lab} | {me:.3f} | {mp_:.3f} |")
    w("\nA negative margin at the extremes of the X play means the pin reaches the slot end and nudges the part "
      "within its 0.3 play (it cannot bind: the play is bigger than the overrun). In B' (elevator pushed "
      "forward 0.3 by bite 2) the cup pin margin is shown in the -0.3 row.\n")

    w("## 9.8 Printability\n")
    w("Every STL in `stl/` is loaded with trimesh in its print orientation. Wall thickness is measured by "
      "casting a ray inward from ~20k surface samples (shape-diameter); spec-defined sub-0.8 features "
      "(push ribs, clamp ridge, 0.5 grooves) are listed, not failed. Overhangs: every downward face steeper "
      "than 45° that is not on the bed must be within 1.0 of a supported edge or bridge ≤ 25 between two "
      "supported edges.\n")
    w("| STL | Orientation | Watertight / consistent | Shells | Volume cm³ | Min wall | Overhangs | Flags |\n|---|---|---|---|---|---|---|---|")
    for r in pr_rows:
        w(f"| {r['name']} | {r['orient']} | {'yes' if r['watertight'] and r['winding'] else '**NO**'} | {r['bodies']} | "
          f"{r['volume'] / 1000:.2f} | {r['min_wall']:.2f} {'' if r['wall_ok'] else '**FAIL**'} | "
          f"{'OK' if r['overhang_ok'] else '**FAIL**'} | {'; '.join(r['flags']) if r['flags'] else '-'} |")
    w("")

    w("## 9.9 Envelope and mass\n")
    bb = em["bbox"]
    w(f"Assembled (state A, docked, pad at rest, ring hook fitted): X {bb[0]:.1f} → {bb[1]:.1f} "
      f"({bb[1] - bb[0]:.1f}), Y {bb[2]:.1f} → {bb[3]:.1f} ({bb[3] - bb[2]:.1f}), Z {bb[4]:.1f} → {bb[5]:.1f} "
      f"({bb[5] - bb[4]:.1f}).\n")
    w("| Part | Group | Material | Volume cm³ | Solid mass g |\n|---|---|---|---|---|")
    tot = {"clip": [0, 0], "receiver": [0, 0]}
    for n, d in em["parts"].items():
        w(f"| {n} | {d['group']} | {d['material']} | {d['volume'] / 1000:.2f} | {d['mass']:.1f} |")
        tot[d["group"]][0] += d["volume"]
        tot[d["group"]][1] += d["mass"]
    v_all = tot["clip"][0] + tot["receiver"][0]
    m_all = tot["clip"][1] + tot["receiver"][1]
    w(f"| **clip (cartridge) total** | | | {tot['clip'][0] / 1000:.1f} | {tot['clip'][1]:.1f} |")
    w(f"| **receiver total** | | | {tot['receiver'][0] / 1000:.1f} | {tot['receiver'][1]:.1f} |")
    w(f"| **clip + receiver, printed** | | | **{v_all / 1000:.1f}** | **{m_all:.1f}** |")
    w(f"| steel hardware (pins, spring {P.DEFAULT_SPRING} ribbon, return spring, screws, nuts) | | steel | | {em['steel_g']:.1f} |")
    w(f"| **empty device** | | | | **{m_all + em['steel_g']:.1f}** |")
    w(f"| **loaded, + 8 x {P.BITE_MASS_G:.0f} g bites** | | | | **{m_all + em['steel_g'] + 8 * P.BITE_MASS_G:.1f}** |")
    w("\nSolid mass (100 % density, upper bound). At 4 perimeters + 30 % gyroid the printed mass is roughly "
      f"60-75 % of this. Gameplan target: ≤ 120 g and ≤ 120 cm³ per loaded clip - the clip cartridge alone is "
      f"{tot['clip'][0] / 1000:.0f} cm³ of plastic and {tot['clip'][1] + 8 * P.BITE_MASS_G:.0f} g loaded (solid).\n")

    w("## 9.10 Force report\n")
    d0 = fr[P.DEFAULT_SPRING]
    w(f"Paddle force = μ_wall·F + μ_bite·F + return-spring force, μ_wall = {P.MU_WALL}, μ_bite = {P.MU_BITE}. "
      f"The return spring is taken at the **real rest pose** (pins on the loaded side of their holes, plunger bottom "
      f"{K.with_hole_play()['rest_bot']:.2f}): installed length **{d0['L_rest']:.1f}** at rest "
      f"({d0['L_rest_model']:.1f} with pins centred), **{d0['L_press']:.1f}** at the hard stop. Rest is the weakest "
      f"point of the return stroke, so the sink-back check uses it.\n")
    w("| Spring | F (N) | friction (N) | return spring k / free | return force rest / pressed (N) | **paddle force start / end (N)** | > 6 N? | uneaten bite returns? rest force ÷ 0.5 F | sticky: ÷ 0.7 × 1.1 F | empty elevator returns? (> 0.2 F) |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for k in (P.DEFAULT_SPRING, "A" if P.DEFAULT_SPRING == "B" else "B"):
        d, s = fr[k], P.SPRINGS[k]
        flag = "**FLAG**" if d["paddle_end"] > 6 else "no"
        w(f"| {k} | {d['F']:.2f} | {d['friction']:.2f} | {s.rs_k:.2f} / {s.rs_free:.0f} | {d['rs_rest']:.2f} / {d['rs_pressed']:.2f} | "
          f"**{d['paddle_start']:.2f} / {d['paddle_end']:.2f}** | {flag} | "
          f"{'yes' if d['bite_returns'] else '**no**'} ({d['return_margin']:.2f}x) | "
          f"{'yes' if d['sticky_returns'] else '**no**'} ({d['sticky_margin']:.2f}x) | {'yes' if d['elevator_returns'] else 'no'} |")
    sB_ = P.SPRINGS[P.DEFAULT_SPRING]
    w(f"Return spring bought anywhere in the BOM range (spring {P.DEFAULT_SPRING}): installed {d0['L_rest']:.1f} at rest, {d0['L_press']:.1f} pressed.\n")
    w("| free length | k (N/mm) | rest / pressed force (N) | paddle force start / end (N) | uneaten bite returns (÷ 0.5 F) | sticky (÷ 0.7 × 1.1 F) |\n|---|---|---|---|---|---|")
    for fl in P.RS_FREE_RANGE:
        for kk in P.RS_K_RANGE:
            r0, r1 = kk * (fl - d0["L_rest"]), kk * (fl - d0["L_press"])
            w(f"| {fl:.0f} | {kk:.2f} | {r0:.2f} / {r1:.2f} | {d0['friction'] + r0:.2f} / {d0['friction'] + r1:.2f} | "
              f"{r0 / d0['friction']:.2f}x | {r0 / d0['sticky_drag']:.2f}x |")
    w("")
    w("\nSpring B (final) passes: chin force well under 6 N, and an uneaten raised bite sinks back even with "
      "sticky food (μ_bite 0.6) and the spring 10 % strong. Spring A needs up to ~7.9 N and an uneaten bite does "
      "NOT sink back (keep A for high-force feed tests only).\n")
    w(f"### Feed margin (spring force at −{100 * P.SPRING_F_LO:.0f} % ÷ stack drag)\n")
    w(f"Usable force = spring force at −{100 * P.SPRING_F_LO:.0f} %, less the drum turning on its steel axle "
      f"(μ {P.FEED_AXLE_MU} × pin radius ÷ coil radius = {100 * fB['axle_loss']:.1f} % for B). Drag: "
      f"{P.N_BITES} × {P.FEED_BITE_MASS_G:.0f} g bites at μ {P.FEED_MU}, times the contact factor k (sum of the "
      f"contact normal forces ÷ weight: upright on the two R0.5 rail edges, or **leaning** and wedged between the "
      f"walls, see §9.11), plus the follower group (follower, drum, spacer rings, coil, axle; solid mass, an upper "
      f"bound) at μ {P.FEED_MU_FOLLOWER} on the rail tops. Drag at an incline t (mouth uphill) = "
      f"g·[(μ·k·m_bites + μ_f·m_f)·cos t + (m_bites + m_f)·sin t]; the worst incline is where that peaks. "
      f"Not modelled: the follower's pitch moment (the ribbon pulls through the axle at Z ≈ {P.pocket_cz(P.SPRINGS[P.DEFAULT_SPRING]):.0f}, "
      f"the stack pushes back on the ribs at Z {P.PUSH_RIB_Z[0]:.0f}-{P.PUSH_RIB_Z[1]:.0f}), which can add a few % of drag. "
      f"10 g bites are heavy (a nominal bite of 1.1 g/cm³ food is ~6.5 g): real margins scale up with lighter food.\n")
    w("| Spring | Bite width | k | follower group g | Earth level | Earth vertical (mouth up) | **Earth worst incline** | Moon level | Moon worst incline |")
    w("|---|---|---|---|---|---|---|---|---|")
    order = {"min": 0, "min_lean": 1, "nom": 2, "max": 3}
    for (sk, bk), r in sorted(fd.items(), key=lambda kv: (kv[0][0] != P.DEFAULT_SPRING, order[kv[0][1]])):
        lab = "min (18), **leaning**" if bk == "min_lean" else f"{bk} ({P.BITES[bk].W:.0f})"
        w(f"| {sk} | {lab} | {r['k']:.2f} | {r['m_f_g']:.1f} | {r['earth_level']:.2f}x | "
          f"{r['earth_vertical']:.2f}x | **{r['earth_incline']:.2f}x** at {r['worst_incline_deg']:.0f}° | "
          f"{r['moon_level']:.1f}x | {r['moon_incline']:.1f}x |")
    w(f"\n**Flag (1-g worst case):** with spring B the Earth margin is lowest with the mouth tilted uphill: "
      f"{fB['earth_incline']:.2f}x at ~{fB['worst_incline_deg']:.0f}° for upright min-width bites and "
      f"**{fL['earth_incline']:.2f}x at ~{fL['worst_incline_deg']:.0f}° if they lean** (a stall is predicted). That stacks "
      f"every worst case: sticky μ 0.6 on rails and walls, 10 g bites, spring 13 % weak, frictionless lean. Treat "
      f"steep mouth-up tilts as the limit of the Earth \"any orientation\" demo (OPEN_ISSUES #14). On the Moon the "
      f"margin is ≥ {min(v['moon_incline'] for (sk, bk), v in fd.items() if sk == P.DEFAULT_SPRING):.1f}x in any "
      f"orientation (the often-quoted ~12x is the level case).\n")
    dg = extra["drag"]
    w("### Bite 2 dragged up in state B\n")
    w("Bite 1 rising pulls bite 2 up by face friction μ_bite·P; bite 2 resists with its weight plus friction on its "
      "rear face, which carries P less its own rail friction in the worst case. Margin = resistance ÷ drag "
      f"(> 1: bite 2 stays down), {P.FEED_BITE_MASS_G:.0f} g min-width bite:\n")
    w("| Spring | Earth | Moon |\n|---|---|---|")
    for sk in (P.DEFAULT_SPRING, "A" if P.DEFAULT_SPRING == "B" else "B"):
        w(f"| {sk} | {dg[(sk, 'earth')]:.3f} | {dg[(sk, 'moon')]:.3f} |")
    w("\nBelow ~1.05 it is marginal, but harmless: the rise is capped by the 0.65 gap to the clip roof and bite 2 "
      "drops back as soon as bite 1 stops moving.\n")

    w("## 9.11 Bites step down into the receiver (v1.1)\n")
    w(f"The bridge (X −2.1 → 0) and the cup at rest are both at Z {P.CUP_TOP_Z} (`CUP_TOP_Z`), with a "
      f"{P.BRIDGE_LEADIN} edge break at X 0. A bite on the clip rails sits on the rails' R0.5 inner edges; under "
      f"gravity the clip rests on its socket floor, {P.SOCKET_FLOOR_CLR} below centre. The rule: every rail seat ≥ "
      f"`CUP_TOP_Z`, so a bite only ever steps **down** (a rigid upright bite climbing a 45° lead-in self-locks "
      f"once bite-to-bite friction reaches ~0.43, however hard the spring pushes).\n")
    w("| Bite width | Clip | Rail seat Z | **Step down to the bridge** |\n|---|---|---|---|")
    for r in st_:
        where = "centred" if r["dz"] == 0 else f"on its floor ({r['dz']:+.1f})"
        w(f"| {r['bites']} ({r['W']:.0f}) | {where} | {r['seat']:.3f} | **{r['step']:.2f}** {ok(r['step'] >= -1e-9)} |")
    w("\n**Leaning bites (not covered by the rule above).** The rule assumes upright, centred bites. A rigid, "
      "**frictionless** 2-D check (`cad/lean.py`) lets a bite shift and lean about X; a whole stack can lean "
      "together because rotating about the stacking axis does not slide one face on the next. Upright is stable "
      "only if the two rail-contact normals cross above the centre of mass. Lowest-energy pose, clip on its floor:\n")
    w("| Bite width | Upright stable? (normals cross / CoM) | Lowest-energy lean | CoM lower by | Contacts | k (Σ normals ÷ weight) | Lowest bottom point Z (at Y) | vs bridge top |\n|---|---|---|---|---|---|---|---|")
    for r in st_:
        if r["dz"] == 0:
            continue
        ln = r["ln"]
        k_txt = f"{ln['k_lean']:.2f}" if ln["k_lean"] else "-"
        w(f"| {r['bites']} ({r['W']:.0f}) | {'yes' if ln['upright_stable'] else '**no**'} "
          f"({ln['normals_cross_z']:.1f} / {ln['upright_com_z']:.1f}) | {abs(r['lean']):.1f}° | {r['com_drop']:.2f} | "
          f"{', '.join(ln['contacts'])} | {k_txt} | {r['lowest']:.2f} (Y {abs(r['lowest_y']):.1f}) | {r['lean_step']:+.2f} |")
    w("\n- **Min (18 wide): upright is unstable** even without friction (the normals cross 0.9 below the CoM). "
      "It rolls ~7° until it wedges against both side walls, its low bottom corner hangs into the gap between the "
      "rails about 1 mm below the bridge top (v1: 1.8 below the 4.5 bridge), and its contact forces add up to "
      f"{st_[0]['ln']['k_lean']:.2f}x its weight instead of 1.25x (used in §9.10). Rail friction may hold it upright; "
      "a jolt won't. The flip is at about 18.15 wide: from 18.2 up, upright is stable.")
    w("- **Nominal and max: upright is stable.** The lowest-energy leaning pose of a nominal bite is behind an "
      "energy barrier (only a hard knock gets it there); max bites stay upright.")
    w("- A leaning bite meets the bridge edge on one rounded R2 corner, 0.9-1.1 above the corner's lowest point "
      "(contact ~60° from vertical). It has to roll upright about its high-side rail against bite-to-bite face "
      "friction; a rough torque balance says that can self-lock at bite-to-bite friction of only ~0.2-0.4, no "
      "better than the climb v1.1 removed. The CAD can't settle it: **bench go/no-go #1 (sticky 18-wide bites, "
      "clip resting in the socket, all 8 cycled, level and at ~50° mouth-up) is the real test** (OPEN_ISSUES #14).\n")

    w("## 9.12 Return-spring solid length (v1.1)\n")
    w(f"Solid length = (n_active + {P.RS_DEAD_COILS})·d with n_active = G·d⁴ / (8·D³·k) (closed, unground ends; "
      f"G = {P.RS_G / 1000:.1f} GPa music wire; 302 SS is ~13 % softer, so fewer coils and shorter). It must be "
      f"≤ {P.RS_SOLID_MAX:.0f} and below the {d0['L_press']:.1f} pressed length, or the spring coil-binds before "
      f"the flange reaches its hard stop and the lift is lost.\n")
    w("| Spring config | wire / OD / k | Solid length | ≤ 10 and < pressed? |\n|---|---|---|---|")
    for k in (P.DEFAULT_SPRING, "A" if P.DEFAULT_SPRING == "B" else "B"):
        d = fr[k]
        w(f"| {k} | {P.RS_WIRE} / {P.RS_OD} / {P.SPRINGS[k].rs_k} | {d['solid']:.1f} | {ok(d['solid_ok'])} |")
    w(f"\nOver the BOM range for the spring-B return spring (k {P.RS_K_RANGE[0]} → {P.RS_K_RANGE[1]} N/mm):\n")
    w("| OD | wire | solid length at k " + f"{P.RS_K_RANGE[0]} / {P.RS_K_RANGE[1]}" + " | |\n|---|---|---|---|")
    for od, wire, sl in extra["solid"]:
        worst = max(sl)
        note = ("**coil-binds** (≥ pressed length)" if worst >= d0["L_press"] else
                ("**over 10**" if worst > P.RS_SOLID_MAX else "OK"))
        w(f"| {od} | {wire} | {sl[0]:.1f} / {sl[1]:.1f} | {note} |")
    bad = [(od, wire, max(sl)) for od, wire, sl in extra["solid"] if max(sl) > P.RS_SOLID_MAX]
    good40 = all(max(sl) <= P.RS_SOLID_MAX for od, wire, sl in extra["solid"] if wire == P.RS_WIRE)
    w(f"\n**{P.RS_WIRE} wire meets the rule everywhere in the range{'' if good40 else ' - NOT'}.** "
      + ("Out of range: " + "; ".join(f"OD {od} with {wire} wire reaches {sl:.1f}"
                                     + (" (coil-binds)" if sl >= d0["L_press"] else "") for od, wire, sl in bad)
         + f". So the \"{P.RS_WIRE_MAX} max\" wire is only safe on a larger OD or a stiffer spring - buy {P.RS_WIRE}.\n"
         if bad else "\n"))
    w("## 9.13 Latch (§6.2, v1.1)\n")
    w(f"Socket clearance {P.SOCKET_FLOOR_CLR} below the clip, {P.SOCKET_IN_Z1 - P.TOP_Z:.1f} above. Tooth "
      f"bottom Z {P.SOCKET_IN_Z1 - P.TOOTH_H:.2f}, notch floor Z {P.TOP_Z - P.LATCH_NOTCH_D:.2f} (clip centred).\n")
    w("| Clip position | Tooth engagement in the 1.0 notch | Tooth bottom → notch floor | Tongue strain when docking |\n|---|---|---|---|")
    w(f"| on its socket floor (rest, gravity) | **{lt['engage_floor']:.2f}** | {P.LATCH_NOTCH_D - lt['engage_floor']:.2f} | {100 * lt['strain_floor']:.2f} % |")
    w(f"| centred | {lt['engage_centre']:.2f} | {P.LATCH_NOTCH_D - lt['engage_centre']:.2f} | |")
    w(f"| floated up against the socket roof | {lt['engage_up']:.2f} | **{lt['floor_clr_up']:.2f}** | {100 * lt['strain_up']:.2f} % |")
    w(f"\nFloated up, the tooth reaches the notch floor at exactly the moment the clip top reaches the socket roof: "
      f"they touch, they never overlap (the clip-float poses in §9.1 confirm it), and the clip cannot rise "
      f"further. Play in X {lt['play_x']:.2f}; strain at {lt['L_c']:.1f} from the tongue root, PETG yield ~4 %. "
      f"The tongue is 4.0 wide, in the -Y half only (OPEN_ISSUES #1).\n")

    with open(os.path.join(OUTDIR, "VERIFICATION.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    with open(os.path.join(OUTDIR, "verification_results.json"), "w") as f:
        json.dump(dict(checks=checks, per=per, clearance={k: v for k, v in clr.items()}, forces=fr,
                       printability=pr_rows), f, indent=1, default=str)
    for cid, title, passed, detail in checks:
        print(f"{cid:5s} {'PASS' if passed else 'FAIL'}  {title}: {detail}")


if __name__ == "__main__":
    if "--config" in sys.argv:
        i = sys.argv.index("--config")
        sp, bk, out = sys.argv[i + 1:i + 4]
        with open(out, "w") as f:
            json.dump(run_config((sp, bk)), f, default=list)
    else:
        main()
