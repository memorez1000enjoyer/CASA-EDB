# EBD "Clip" v1.1: print-ready model

**Hickman High School CASA · NASA HUNCH 2026-27 · Extraterrestrial Bites Dispenser**
Team: Jessyn, Clayton, Esther. Built from `EBD_Build_Spec.md` Rev B, updated to **v1.1** from the Rev C
follow-up. Since Rev C, **this repo (`cad/params.py` + `CHANGES.md`) is the geometry master**; the spec keeps
the design rationale. Default spring: **B (0.33 lb, final)**.

![State A](renders/state_A_rest_full_iso.png)

The Clip is a hands-free bite dispenser that sits inside the suit just below the helmet ring. A
constant-force spring pushes 8 bites along a tube (the **clip**) into a small head (the **receiver**).
Tuck your chin onto the **paddle** and a 1:1 **lever** lifts the front bite about 13.9 mm, so about 9.5 mm
of it (8.5 for the smallest bite) sticks up through the **window** for your teeth. Let go and a return spring drops the cup back, and the
next bite slides on.

---

## 1. What's in this folder

| Folder / file | What it is |
|---|---|
| `stl/` | **Print these.** One STL per part, already turned to its print orientation and sitting on the bed. |
| `stl/*_springA.stl` | Parts for the optional 1.48 lb high-force test spring A (its follower; A needs no spacer rings). Everything else is the same for both springs. |
| `stl/assemblies/` | Whole-device STLs in each state (A, B, B′, C, D, D-taken, E) for viewing, not printing. |
| `step/parts/`, `step/assemblies/` | The same parts and states as STEP, for Fusion / Onshape / FreeCAD. |
| `renders/` | Pictures: iso, top and cut-away (section at Y = 0) views of the states, plus an exploded view. |
| `cad/` | The source code (CadQuery, Python). **`cad/params.py` holds every dimension.** |
| `VERIFICATION.md` | The §9 acceptance checks with the measured numbers (run automatically). |
| `CHANGES.md` | Every place the model differs from the spec, and why. |
| `OPEN_ISSUES.md` | Problems in the spec and decisions the team still has to make. **Read this.** |

## 2. Print the fit coupon FIRST, then set `CLR_SLIDE` and the pin holes

1. Print `stl/fit_coupon.stl` (PETG, same settings as below). It has a plate with four square sleeves, five
   pin-hole sizes, and a separate 10 × 10 slider bar.
2. **Sleeves** (dots next to each: 1 dot = 0.20, 2 = 0.25, 3 = 0.30, 4 = 0.35 mm clearance per side). Push the
   slider through each one. Pick the **tightest sleeve the slider slides through freely by hand without
   wobbling**. That number is your `CLR_SLIDE`.
3. **Pin holes** (1 dot = Ø1.9 … 5 dots = Ø2.3; top row vertical, side row horizontal). Try a piece of your
   Ø2 steel rod in each. You want one that **presses in and stays** (press), one that **pushes in snugly**
   (snug), the smallest one it **spins freely in without wobble** (run) and one it **turns loosely** in
   (free). The defaults are 1.9 / 2.1 / 2.1 / 2.3: run = snug because you ream the lever hole (section 5,
   step 4). If you won't ream, type the coupon's run hole instead (it costs 0.1-0.2 of lift, still ≥ 13.5).
4. Edit `cad/params.py` if your printer needs different values, then rebuild (section 7). `CLR_SLIDE` sets every
   sliding fit except the socket floor: `SOCKET_FLOOR_CLR` (0.10) is kept small so the latch engages 0.6 and
   bites step down into the receiver. If a clip is tight going into the socket, file the socket floor or set
   `SOCKET_FLOOR_CLR` to 0.2 (the step-down is then 0.1 and the latch engages 0.5). Each pin hole is its **own** number, typed straight from the coupon: `PIN_PRESS_D` (presses in),
   `PIN_SNUG_D` (snug), `PIN_RUN_D` (smallest hole the rod *spins freely* in without wobble: the lever pivot)
   and `PIN_FREE_D` (loose: the drum bore). The follower's axle holes print horizontal: if the side row differs,
   set `AXLE_HOLE_D` from it. Screw holes (`M2_CLEAR_D` = 2.3) don't follow any of these; if an M2 screw
   threads into one, ream it with a Ø2.4 drill.

## 3. Print settings and orientation

**PETG, 0.4 nozzle, 0.2 layers, 4 perimeters, 30 % gyroid.** Paddle pad in **TPU 95A**. The STLs are
already in the orientation below; just drop them on the bed.

| File | Qty | Material | Bed face (already oriented) | Supports | Notes |
|---|---|---|---|---|---|
| `clip_tube.stl` | 1 | PETG, **translucent** if you have it | bottom (−Z) | none | The roof is a 20.5 mm bridge 0.3 above the follower. After printing, check the roof underside with a straightedge: if it sags more than 0.2, see OPEN_ISSUES #7. For opaque filament use `clip_tube_viewslots.stl` (9 small windows so you can count bites). |
| `gate.stl` | 1 | PETG | flat | none | |
| `end_cap.stl` | 1 | PETG | flat (outer face) | none | |
| `follower.stl` | 1 | PETG | rear face | none | For spring B. (Spring A tests: `follower_springA.stl`, bigger coil pocket.) |
| `drum.stl` | 1 | PETG | on its end | none | Same drum for both springs. |
| `drum_spacer.stl` | **4** (2 + 2 spares) | PETG, **100 % infill** | flat | none | Rings that slip over the drum, one each side of the narrow spring-B coil. If one won't slide over the drum, sand its bore. |
| `ribbon_clamp.stl` | 1 | PETG | top face (ridge up) | none | |
| `receiver_left.stl` | 1 | PETG | split face | **YES**: see below | The −Y half: mount face, dowel press holes, nut traps, and the latch. |
| `receiver_right.stl` | 1 | PETG | split face | **YES**: see below | The +Y half: screw counterbores, gate-tab channel. |
| `elevator.stl` | 1 | PETG | bottom | none | |
| `lever.stl` | 1 | PETG | on its side | none | All three holes print vertical (round). |
| `plunger.stl` | 1 | PETG | **upside down** (flange on the bed) | **YES**: enforcer `stl/slicer_helpers/plunger_SUPPORT_ENFORCER.stl` (under the ear only) | Brim. |
| `paddle_pad.stl` | 1 | **TPU 95A** | on its side | none | Print slowly, with a brim. |
| `ring_hook.stl` | 1 | PETG | on its end | none | Placeholder size until the neck ring is measured (OPEN_ISSUES #4). |
| `bench_base.stl` | 1 | PETG or PLA | flat | none | Holds the device upright on the bench. **195.8 mm long: it won't fit a 180 mm bed** (print it diagonally or on a bigger printer). |
| `bite_nominal.stl`, `bite_min.stl`, `bite_max.stl` | 8 of each | PETG or PLA | flat | none | Dummy bites for testing: 12.7 × 19 × 25.4, 12.2 × 18 × 24.4, 13.2 × 20 × 26.4. |
| `fit_coupon.stl` | 1 | PETG | flat | none | Print first (section 2). |

**Already printed v1 parts?** Reprint `receiver_left`, `receiver_right` and `elevator`: v1.1 lowers the
bridge and shortens the elevator by 0.8. v1 spacer rings work if you sand the bore out to Ø13.0. Everything
else is unchanged (a v1 `follower_springB.stl` print is within 0.02 mm of the new `follower.stl`).

**Supports (receiver halves and plunger):** in the slicer, load each part's `stl/slicer_helpers/<part>_SUPPORT_ENFORCER.stl`
as a *support enforcer* modifier on that part (it lines up automatically), set supports to **enforcers only**, and
add a brim. In the preview, supports should appear only:
- inside the U-shaped socket opening (the part the clip slides into)
- under the thin roof strip beside the gate-tab channel (right half only)
- under the plunger's spring ear

Nothing else gets support. In particular, the bite-channel side wall next to the socket prints as a 27.8 mm
bridge on purpose, because support there would scar the elevator's sliding face.

Remove the supports with pliers and a hobby knife, then **file the socket's inner side faces smooth**: the clip
slides there with only 0.3 mm clearance. Then **dry-fit the elevator and a max-size dummy bite** in each half's
bite channel and scrape any sag on that bridged wall. Why supports are needed: OPEN_ISSUES #2.

## 4. Hardware (BOM)

| Qty | Item | Used for |
|---|---|---|
| 1 | Constant-force spring **B** 0.33 lb, ID 0.44″, ¼″ wide (SUS301; Amazon ASIN B0DL4KCGVB, 5-pack): **the final spring** | Bite feed |
| 1 | *Compression spring, OD 5.5–6.5 mm (ID ≥ 3.4 so it fits over the Ø3 spigot), **wire 0.40 mm / 0.016 in (0.45 max)**, free length 38 mm (37–40), rate 0.12–0.15 N/mm (0.7–0.85 lb/in), solid length ≤ 10 mm, music wire or 302 SS. **Do NOT buy 0.5–0.6 mm wire springs**: they go solid before the end of the stroke and halve the lift. Check: squeeze to 12 mm by hand, and it must not be coil-bound.* **Note from the model (VERIFICATION §9.12):** the "0.45 max" only holds on OD ≥ 6.0 with k ≥ 0.13. On a 5.5 OD, 0.45 wire goes solid at 10.8–13.2 mm and can coil-bind. If in doubt, buy 0.40. | Return spring (spring B) |
| (1) | *Optional:* constant-force spring **A** 1.48 lb (0.38″ wide) + a return spring of OD 5.5–6.5, wire 0.40–0.45 (not 0.5–0.6), free length 35, ≈ 0.20 N/mm, solid ≤ 10 | High-force feed tests only (chin force ~8 N, an uneaten bite won't sink back) |
| ~1 m | Ø2.0 steel rod: **5/64″ music wire** (1.98 mm) in the US. *Not* 3/32″ (2.38, too big). Cut to: pivot **26.0** (max 27.1), cup-end **19.4** (max 20.4), plunger-end **11.4** (max 12.5), drum axle **19.9** (max 20.4), dowels **3 × 10** | Pins (file the ends flat and deburr). The maxima are where a pin starts to rub a wall or no longer fits its blind holes. |
| 2 | M2 × 4 countersunk self-tapping | Ribbon clamp |
| 2 | M2 × 6 pan-head self-tapping | End cap |
| 4 + 4 | **M2 × 20 socket head** (ISO 4762 / DIN 912; a pan head is too wide for the Ø4.2 counterbore) + M2 nuts (a drop of medium threadlocker) | Receiver halves |
| 2 | M2 × 8 **countersunk** self-tapping | Ring hook |
| 2 + 2 | **M3 × 12–16** thumb screws + M3 nuts | Bench base |
| - | **Adhesive-backed** PTFE film 0.08 mm, industrial Velcro 2″, CA glue, 1.5 mm hex key, cut-off wheel for music wire (or buy Ø2 × 10 dowel pins) | |
| - | Reaming drills in a pin vise: **Ø2.1** for the lever pivot (US: **#45** = 2.08 or **#44** = 2.18) and **Ø2.4** for any M2 hole the screw threads into (US: **3/32″** = 2.38) | |

## 5. Assembly order

### Clip (cartridge), spec §5.7

0. **Tip:** with spring A, park the pulled-out coil with a binder clip at the back of the tube during steps 2–4. Spring B is much easier to handle.
1. **Clamp the ribbon.** Lay the free end of the spring ribbon flat in the groove at the mouth, centred
   between the two screw holes. Put the clamp on it with the **ridge down** over the little notch in the
   groove floor. Drive the two **M2 × 4 countersunk** screws up from underneath the tube into the clamp. The
   heads must end flush or below the bottom.
2. **Thread the coil through.** Pass the coil back along the groove and out of the back of the tube.
3. **Coil onto the drum.** *Spring B:* slide one spacer ring onto the drum, flush with one end. Twist the coil
   onto the drum from the other end until it touches the ring. Slide the second ring on. Drum, rings and coil
   drop into the follower as one 9.4-wide unit. (Both rings first can't work: the coil can't get past a ring.)
   *Spring A:* slip the wide coil straight onto the drum; its own preload grips it.
4. **Drum into the follower.** Drop drum + coil into the follower's pocket **from below**, through the open
   slot between the keel legs. The ribbon must come off the **bottom** of the coil and head toward the
   follower's front (push-rib) end. Push the 19.9 mm axle through the side holes and the drum. It ends flush
   with the follower sides; the tube walls keep it in.
5. **Follower into the tube.** Slide the follower in from the back, keel in the groove and the ribbon flat
   between the keel legs. Let the spring pull it forward gently; don't let it snap.
6. **End cap.** Push the end cap in (tongue in the groove) and drive the two **M2 × 6 pan-head** screws
   through the side-wall holes.

### Receiver (head)

1. Clean off the supports. Check the latch tongue flexes freely (run a knife through its 1.0 cuts if needed).
   Dry-fit the elevator, the plunger and a max-size dummy bite in each half, and file or scrape any tight
   channel face. Press the **3 dowels** into the Ø1.9 holes of the **left** half with a vise (they stick out
   about 5 mm).
2. Put **PTFE tape** on the elevator's front and rear faces and on the front-wall stop face (the flat wall at
   the front of the window) in both halves.
3. Drop an **M2 nut** into each of the 4 hex traps on the left half's outer face and hold it with a strip of
   masking tape. The M2 × 20 screws reach a nut anywhere in its trap and pull it in as you tighten.
4. Ream the lever's **centre** hole with a Ø2.1 drill in a pin vise until the lever spins freely on a Ø2 pin
   without wobble (the two end holes stay snug). Lay the left half split-face up. **Press** the **26.0 pivot
   pin** into its Ø1.9 hole with the vise, all the way to the bottom, like the dowels. Then slip the
   **lever** onto it.
5. **Elevator: in high, then slide down.** Hold the elevator about 9 mm up in its channel (above the
   lever), lower it into the half, then slide it down onto the ledge so the lever's end enters the elevator's
   open-bottom front notch from below. Push the **19.4 cup-end pin** through the elevator slot and the lever end.
   (A straight drop onto the ledge hits the lever: checked in CAD.)
6. **Plunger: lever down first.** Lift the elevator to the top of its travel so the lever's plunger end swings
   down. Lower the plunger into its channel with the ear near the **top** of the ear slot, slide it down over the
   lever end, then push the **11.4 plunger-end pin** through. (With the lever at rest, no straight drop clears
   it.)
7. **Return spring:** stand it in its well under the ear, with the spigot inside the spring. It has to be
   held compressed (38 → about 27 mm) while the right half closes: use a finger or tweezers.
8. Close with the **right** half (the dowels and pivot pin line it up). Put the four **M2 × 20** screws in from
   the right side (they sit 9 mm deep in their counterbores; use a long driver) and tighten into the nuts.
9. **Test:** press the plunger down to its stop (about 14.9 mm of travel). The cup should rise about 13.9 mm and
   fall back when you let go.
10. Scuff the flange top with sandpaper, then CA-glue the **TPU pad** onto it: the pad's two end rims go over
    the flange ends.
11. **File any M2 × 20 tip flush** with the left face (screw-length tolerance can leave one ≈ 0.3 proud, and
    the one at X −23.6, Z 26 is under the ring hook). Then screw the **ring hook** onto the left (mount) face
    with 2 × **M2 × 8 countersunk**. Add Velcro (OPEN_ISSUES #4).

### Load, dock, arm, undock

- **First bite:** with the gate **out**. On an empty clip the follower sits on its stop and fills the gate
  slot, so the gate can't go in yet. Push the first bite in through the mouth (it pushes the follower back)
  until it is about 3 mm past the gate slot, and drop the gate in.
- **Load the rest (one bite at a time, using the gate as a ratchet):** with the gate in, hold the next bite at
  the mouth and lift the gate out. Push the bite in about 3 mm past the gate slot with a pencil held low in the mouth.
  Slide the gate down until it rests on the pencil, pull the pencil out, and push the gate fully down. Repeat for
  each bite. **Keep eyes away from the mouth: spring A can fire a bite out.** Spring B makes this much easier.
  The gate's tab points to the right (+Y) side. Tie a short lanyard through its hole so it doesn't get lost on
  the bench; the gate is not used during an EVA.
- **Dock:** with the gate **in**, slide the clip into the socket so the gate's tab runs in the slot in the
  socket roof. Push until the latch clicks (the clip mouth meets the stop face).
- **Arm:** pull the gate straight up out of the socket.
- **Undock:** only when the clip is empty (OPEN_ISSUES #6). Lift the latch tab and pull the clip out.

## 6. How it's checked

`VERIFICATION.md` is written by `cad/verify.py`. It rebuilds every state at min / nominal / max bite size
for both springs and checks every pair of parts for overlap with exact solid booleans. It sweeps the lever
through 7 in-between angles, measures clearances, exposure, spring extension and slot margins, checks every
STL is watertight with walls ≥ 0.8, finds overhangs, and reports mass, chin force and feed margins. v1.1 adds
§9.11 (every bite steps *down* into the receiver), §9.12 (the return spring never goes solid) and §9.13 (latch
engagement). Current status: **§9.1–9.7 and §9.9–9.13 pass. §9.8 is flagged**: the receiver halves and the
plunger need support in known places (enforcers supplied), and one bite-channel wall is a bridge longer than
the 25 mm rule (OPEN_ISSUES #2).

### Bench go / no-go tests (before any demo)

1. **Feed:** small-width (18 mm) dummy bites made sticky (a little honey on the faces, or real food after the
   warm soak), clip resting in the socket, all 8 bites cycled, **level and with the mouth tilted ~50° up**.
   **Must not stall.** This is also the test for leaning bites: the model predicts the tilted case is
   marginal (OPEN_ISSUES #14).
2. **Sink-back:** raise a bite, don't take it, let go. **It must drop back**, with real or sticky bites, not
   just dry printed dummies.
3. **Lift:** press the paddle to its stop. The cup should rise about 13.9 mm, and at least 8 mm of the smallest
   bite should stand above the top surface.
4. **Latch:** a full clip can't be pulled out without lifting the tab.

## 7. Changing the design

All dimensions live in **`cad/params.py`** with the spec's names (`BITE_T`, `CLR_SLIDE`, `LIFT`,
`SPRING_W`, `PADDLE_X`, `RING_FLANGE_T`, …). Nothing is typed twice. After an edit:

```bash
pip install cadquery trimesh manifold3d embreex networkx shapely matplotlib vtk
cd cad
python build_all.py            # STLs, STEPs, renders, VERIFICATION.md, zip (~10 min)
python build_all.py --quick    # nominal bites + spring B only (~3 min)
```

(On Linux without a screen, renders need `xvfb-run`; `build_all.py` uses it automatically.)

Common edits:
- **Real bites (Esther's trials):** change `BITE_T`, `BITE_W`, `BITE_H` and the tolerances. The ±0.5 on
  `BITE_T` is a MUST: it stops the elevator lifting two bites.
- **Real spring:** edit its row in `SPRINGS` (force, width, thickness, length). The pocket size and spacer
  rings follow automatically. Measure the delivered coil's ID and set `DRUM_D` = 1.10–1.15 × that ID; the
  model stops with an error if the follower's rear wall would drop under 1.2.
- **Real return spring:** set `rs_k` and `rs_free` in the spring's `SPRINGS` row and `RS_WIRE` / `RS_OD`;
  §9.10 rechecks the chin force and sink-back, §9.12 the solid length.
- **Reach test (`PADDLE_X`):** the pivot, `LEVER_R`, plunger, channels, slot lengths, dowel and ring hook all
  follow. Moving the paddle up to 10 mm **further** from the window passes every check. Moving it **closer**
  only works to about 7 mm (`PADDLE_X` ≥ −29), because the pad then runs into the window (OPEN_ISSUES #11).
- **Neck ring:** set `RING_FLANGE_T`, `RING_HOOK_REACH`, `RING_HOOK_Z` after measuring `HUT – Largest.stl`.
