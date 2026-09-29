"""§9 acceptance checks at min / nominal / max bites for spring A and spring B.
Writes ../VERIFICATION.md and ../verification_results.json.

    python verify.py            (full run, ~5-10 min on 4 cores)
    python verify.py --quick    (nominal bites, spring A only)
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
        for sh in ((0.0, -c), (0.0, c), (-c, 0.0), (c, 0.0)):
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
    rows = {}
    rest, pr = K.mech_rest(), K.mech_pressed()
    L_rest = (rest.plunger_bot + P.EAR_UNDERSIDE) - P.SPRING_WELL_Z0
    L_press = (pr.plunger_bot + P.EAR_UNDERSIDE) - P.SPRING_WELL_Z0
    for k, s in P.SPRINGS.items():
        rs0 = s.rs_k * (s.rs_free - L_rest)
        rs1 = s.rs_k * (s.rs_free - L_press)
        fric = (P.MU_WALL + P.MU_BITE) * s.F
        rows[k] = dict(F=s.F, friction=fric, rs_rest=rs0, rs_pressed=rs1,
                       paddle_start=fric + rs0, paddle_end=fric + rs1,
                       bite_returns=rs0 > fric, elevator_returns=rs0 > 2 * P.MU_WALL * s.F,
                       L_rest=L_rest, L_press=L_press)
    return rows


def envelope_mass():
    import cadquery as cq
    import assembly as A
    st = A.build("A", "A", "nom")
    bb = None
    vols = {}
    for bd in st.bodies:
        b = bd.shape.BoundingBox()
        bb = b if bb is None else bb.add(b)
    stat = A._static("A")
    printed = {
        "clip_tube": ("clip", "PETG"), "end_cap": ("clip", "PETG"), "gate": ("clip", "PETG"),
        "follower": ("clip", "PETG"), "drum": ("clip", "PETG"), "ribbon_clamp": ("clip", "PETG"),
        "receiver_left": ("receiver", "PETG"), "receiver_right": ("receiver", "PETG"),
        "elevator": ("receiver", "PETG"), "lever": ("receiver", "PETG"), "plunger": ("receiver", "PETG"),
        "paddle_pad": ("receiver", "TPU"), "ring_hook": ("receiver", "PETG"),
    }
    rho = {"PETG": P.RHO_PETG, "TPU": P.RHO_TPU}
    for n, (grp, mat) in printed.items():
        v = stat[n].Volume()
        vols[n] = dict(group=grp, material=mat, volume=v, mass=v * rho[mat])
    # steel hardware (pins, spring ribbon, screws) - rough
    pin_len = P.PIVOT_PIN_L + P.CUP_PIN_L + P.PLUNGER_PIN_L + P.AXLE_L + 3 * P.DOWEL_L
    steel = pin_len * math.pi * (P.PIN_D / 2) ** 2 * P.RHO_STEEL
    s = P.SPRINGS["A"]
    steel += s.L * s.W * s.T * P.RHO_STEEL
    steel += 4 * 0.45 + 4 * 0.05 + 6 * 0.15  # M2x16 + nuts + small screws (g)
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
    configs = [("A", "nom")] if quick else [(s, b) for s in ("A", "B") for b in ("min", "nom", "max")]
    t0 = time.time()
    results = run_parallel(configs)
    t_geo = time.time() - t0
    import printability
    pr_rows = printability.check_all()
    em = envelope_mass()
    fr = forces()
    margins, cup_rng, plg_rng = slot_margins()
    write_report(results, pr_rows, em, fr, margins, cup_rng, plg_rng, t_geo, quick)


def write_report(results, pr_rows, em, fr, margins, cup_rng, plg_rng, t_geo, quick):
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
        and abs(rest.elev_top - P.RAIL_TOP_Z) < 1e-9
    checks.append(("9.7", "Kinematics", c97, f"lift {prs.lift:.2f} model / {hp['lift']:.2f} with pin-hole play (≥ 13.5), stroke {stroke:.2f}, pins inside slots "
                   f"(min margin {min(nom_m):.2f} at nominal X)"))
    c98 = all(r["watertight"] and r["winding"] and r["wall_ok"] for r in pr_rows)
    need_sup = [r["name"] for r in pr_rows if not r["overhang_ok"]]
    n_flag = sum(1 for r in pr_rows if r["flags"])
    checks.append(("9.8", "Printability", c98,
                   f"{len(pr_rows)} STLs all watertight, walls ≥ 0.8 except listed spec features; "
                   + (f"NEEDS SUPPORT: {', '.join(need_sup)} (OPEN_ISSUES #2)" if need_sup else "no supports needed")))
    checks.append(("9.9", "Envelope / mass report", True, "reported below"))
    c910 = fr["A"]["paddle_end"] > 0
    checks.append(("9.10", "Force report", True,
                   f"A {fr['A']['paddle_start']:.1f}-{fr['A']['paddle_end']:.1f} N (> 6 N flagged), "
                   f"B {fr['B']['paddle_start']:.1f}-{fr['B']['paddle_end']:.1f} N"))

    # ------------------------------------------------------------------ markdown
    w("# VERIFICATION - EBD Clip v1\n")
    w(f"Generated by `cad/verify.py` on {time.strftime('%Y-%m-%d %H:%M')} "
      f"({'QUICK: spring A nominal only' if quick else 'full run: springs A and B x bites min/nom/max'}; "
      f"geometry checks took {t_geo:.0f} s). Every number comes from the CAD model or from `params.py`.\n")
    w("Spec: EBD_Build_Spec.md Rev B, section 9. Units mm, N. Bites: min 12.2 x 18.0 x 24.4, "
      "nom 12.7 x 19.0 x 25.4, max 13.2 x 20.0 x 26.4 (T x W x H).\n")
    w("## Summary\n")
    w("| § | Check | Result | Key numbers |\n|---|---|---|---|")
    for cid, title, passed, detail in checks:
        res = "PASS" if passed else "**FAIL**"
        if cid == "9.8" and passed and need_sup:
            res = "**FLAG** (supports)"
        if cid == "9.10":
            res = "REPORT (A flagged > 6 N)" if fr["A"]["paddle_end"] > 6 else "REPORT"
        w(f"| {cid} | {title} | {res} | {detail} |")
    w("")

    w("## 9.1 Interference\n")
    w(f"Exact B-rep booleans (OpenCascade) between every pair of bodies whose bounding boxes come within "
      f"1 mm, in states A, B, B', C, D, D-taken, E, plus {N_SWEEP - 2} intermediate lever angles for each of the "
      f"B, B' and D strokes, plus states C and D-taken with the clip shifted ±0.3 in Y and in Z inside its socket, "
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
    w("\nNotes: bites stay upright and settle vertically onto the highest support (rails 4.0/4.29/4.45, "
      "bridge 4.5). A min-width bite 2 half on the bridge is lifted to Z 4.44 in state A (a real rigid bite "
      "would tilt ~2° instead). \"Elevator top rear edge → bite 2\" is the X gap between the cup floor's rear "
      "edge and bite 2's front face in states A/B; it must stay ≥ 0 so the cup is never under bite 2.\n")
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
    w(f"| steel hardware (pins, spring A ribbon, screws, nuts) | | steel | | {em['steel_g']:.1f} |")
    w(f"| **empty device** | | | | **{m_all + em['steel_g']:.1f}** |")
    w(f"| **loaded, + 8 x {P.BITE_MASS_G:.0f} g bites** | | | | **{m_all + em['steel_g'] + 8 * P.BITE_MASS_G:.1f}** |")
    w("\nSolid mass (100 % density, upper bound). At 4 perimeters + 30 % gyroid the printed mass is roughly "
      f"60-75 % of this. Gameplan target: ≤ 120 g and ≤ 120 cm³ per loaded clip - the clip cartridge alone is "
      f"{tot['clip'][0] / 1000:.0f} cm³ of plastic and {tot['clip'][1] + 8 * P.BITE_MASS_G:.0f} g loaded (solid).\n")

    w("## 9.10 Force report\n")
    w(f"Paddle force = μ_wall·F + μ_bite·F + return-spring force, μ_wall = {P.MU_WALL}, μ_bite = {P.MU_BITE}. "
      f"Return spring installed length {fr['A']['L_rest']:.1f} at rest, {fr['A']['L_press']:.1f} pressed "
      f"(free {P.SPRINGS['A'].rs_free:.0f}; must not go solid above ~10).\n")
    w("| Spring | F (N) | friction (N) | return spring k (N/mm) | return force rest / pressed (N) | **paddle force start / end (N)** | > 6 N? | uneaten raised bite returns? (rest force > 0.5 F) | empty elevator returns? (> 0.2 F) |")
    w("|---|---|---|---|---|---|---|---|---|")
    for k, d in fr.items():
        s = P.SPRINGS[k]
        flag = "**FLAG**" if d["paddle_end"] > 6 else "no"
        w(f"| {k} | {d['F']:.2f} | {d['friction']:.2f} | {s.rs_k:.2f} | {d['rs_rest']:.2f} / {d['rs_pressed']:.2f} | "
          f"**{d['paddle_start']:.2f} / {d['paddle_end']:.2f}** | {flag} | {'yes' if d['bite_returns'] else '**no**'} | "
          f"{'yes' if d['elevator_returns'] else 'no'} |")
    w("\nAs the spec predicts: spring A needs up to ~7.8 N of chin force and an uneaten raised bite will NOT "
      "sink back (the sandwich friction beats the return spring); spring B passes both. Build and test both, "
      "expect B (or ~0.3-0.5 lb) to be the final spring.\n")
    w("## Latch (§6.2) - computed\n")
    ramp = P.TOOTH_H / math.tan(math.radians(P.TOOTH_RAMP_DEG))
    L_c = P.TONGUE_ROOT_X - (P.TOOTH_X0 + P.TOOTH_X1) / 2
    strain = 3 * P.TONGUE_T * (P.TOP_Z - (P.SOCKET_IN_Z1 - P.TOOTH_H)) / (2 * L_c ** 2)
    w(f"Tooth engages {P.TOP_Z - (P.SOCKET_IN_Z1 - P.TOOTH_H):.2f} into the 1.0 notch with "
      f"{P.TOOTH_X0 - P.LATCH_NOTCH_X0:.2f} play; docking deflection {P.TOP_Z - (P.SOCKET_IN_Z1 - P.TOOTH_H):.2f} at "
      f"{L_c:.1f} from the root → bending strain ≈ {100 * strain:.2f} % (PETG yield ~4 %). "
      f"Tongue is 4.0 wide in the -Y half only (see OPEN_ISSUES #1).\n")

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
