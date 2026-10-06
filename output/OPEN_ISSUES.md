# OPEN ISSUES - EBD Clip v1.1

Things the spec asks for that cannot be built exactly as written, and decisions that belong to the
team. Where the model had to pick something to stay printable, it says what was picked and why.
Numbers come from `VERIFICATION.md`.

---

## 1. Spec defect: half the latch tongue ends up as a loose piece in `receiver_right` (worked around)

**What the spec says:** the receiver is split at Y = 0 (§6.1). The socket roof has a centred 8-wide latch
tongue, a full-width gate slot at X 1.2 → 2.8, and a gate-tab channel at Y +6.2 → +10.8 that runs to the
back end and is **open at the back** so the tab can ride in while docking (§6.2).

**Why it can't be built as written:** in the +Y half, the roof between Y 0 and Y +6.2 (including the +Y half
of the tongue) is bounded by the gate slot at the front, the tab channel on the outside, the open socket end
at the back, and the split plane. It is attached to **nothing** in that half. The CAD split confirmed it
comes out as a separate 308 mm³ solid. The channel can't be closed (the tab must enter from the back), and
the gate slot can't be narrowed (the 22.1-wide gate must come out through it).

**What the model does now:** that island is removed. The latch tongue, tooth and lift tab are 4.0 wide and
live only in the −Y half (Y −4.0 → 0). They still engage the clip's centred 8.6-wide notch, 0.7 deep with
0.1 play. Holding strength comes from the tooth's vertical face, so half the width is ample for bench use.
The tongue half lies on the split face when printed, so it prints cleanly. The +Y roof centre over the clip
is simply open.

**Team decision (pick one for v2):**
- (a) Keep this (simplest; asymmetric latch).
- (b) Make the latch a separate one-piece part, printed on its side, captured between the halves. This gives
  a full 8-wide tongue.
- (c) Move the gate tab to Y = 0 and the tongue off-centre. This does **not** print on the split face (the
  tongue would float over its side cut), so it is not recommended.

## 2. §9.8 overhang rule: supports in the receiver halves and the plunger (flagged)

The spec's print orientations can't be met without support in three places. Everything else is
watertight with walls ≥ 0.8 (spec features excepted):

| Part | Where | Why |
|---|---|---|
| receiver_left / right | Inside the socket, under the socket side wall | Printed on the split face, the side wall is a 28 × 36.1 roof over the socket cavity. It is supported on 3 sides; the 4th is the open socket entry. The bridge would be **36.1 mm (limit 25)**, and sag there eats the 0.3 clip clearance. |
| receiver_right | Under the roof strip outside the gate-tab channel | A 1.75 × 26.8 strip, supported only at the front. |
| plunger | Under the spring ear (upside-down print) | The ear sticks out 8.3 from the body. No orientation of the spec'd plunger is support-free: the flange blocks side orientations and the ear blocks vertical ones. |

One more region is flagged but printed **without** support on purpose: the bite-channel side wall next to
the stop face. The span between the bridge (Z 3.7 since v1.1) and the roof (Z 31.5) is a **27.8 mm** bridge
(limit 25), because the socket cavity starts at X = 0. That wall is also the elevator's sliding face, and
support scars there would be worse than a slight sag. The README says to scrape it after a dry fit.

Printing the halves on their outer face instead removes every bridge, but then the latch tongue floats over
its side cut, which is unprintable. So the split face stays.

**What to do:** use the support-enforcer files in `stl/slicer_helpers/`. There is one per receiver half and
one for the plunger, and each reaches 0.6 into the surface it supports. Set supports to *enforcers only*.

**v2 option:** print the socket as its own part standing on its back end. Every socket wall is then
vertical, the tongue prints standing up, and it bolts to the stop face. This is a redesign, so it's the
team's call.

## 3. §6.6 "orthodontic-elastic" hook posts: omitted

The ear moves inside the **enclosed** ear slot (X −50.2 → −41.5, Z −6.5 → 14.5), so an elastic from an
ear post has no path up to a post "at the receiver top near X −46". The receiver screw at (X −45.8, Z 24)
sits exactly where a channel would go. Spring B is paired with a lighter compression spring instead
(v1.1: k 0.13 N/mm, free 38, about 1.43 N at rest). If the team wants the elastic option, move that screw and cut a Ø3
channel from the ear slot to the top.

## 4. Mount layout (§6.7): ring hook and Velcro share the −Y face; ring-flange numbers are placeholders

The spec's ring-hook pilots (X −19 / −37, Z 20 / 26) sit inside the area the two 25 × 50 Velcro pads cover
(X −51 → −1). A 3.0-thick hook leg would hold the Velcro off the wall. For now, cut the pads round the hook
leg (X −41 → −15, Z ≥ 15), or use shorter pads (Z −20 → 14). The bench base's fixed jaw also sits on the
lower −Y face, so take the Velcro off for bench tests.

`RING_FLANGE_T = 4.0`, `RING_HOOK_REACH = 6.0` and `RING_HOOK_Z = 8.0` are still **placeholders**. Measure
the real flange in `HUT – Largest.stl` (NTRS 20260000671), set them in `params.py`, and rebuild.

## 5. Spring A is too stiff for the final design (resolved in v1.1: spring B is the default)

With the 1.48 lb spring the chin force is about **4.9 → 7.9 N** (flagged > 6 N), and an uneaten raised bite
**does not sink back** (1.6 N of return force vs 3.3 N of sandwich friction). The team bought spring B, and
v1.1 makes it the default. With the v1.1 return spring (k 0.13, free 38) the chin force is **2.2 → 4.1 N** and an
uneaten bite returns with a 1.95× margin (1.26× with sticky food). Keep A for high-force feed tests only.

## 6. Undocking a clip that still has bites in it

When the clip is pulled out, the stack follows the follower out of the mouth into the receiver. The gate
can't go back in while docked, because bite 2 fills the clip's gate slot. So **only undock an empty clip**
(state C/D). To remove a partly-used clip, take bites off the cup one at a time until it is empty. Test this
on the bench and decide whether v2 needs a second gate at the receiver side.

## 7. Bench checks the CAD can't settle

- **Roof sag (§8.1):** the follower clears the clip roof by 0.3. After printing, check the roof sag. If it
  is more than 0.2, split the roof into a snap-on lid (the spec's remedy). Printing the tube standing on
  its back end also avoids the bridge, but puts layer ridges across the sliding direction.
- **Stripper wall strength:** the L-shaped wall behind the window is still two cantilevers (one per half,
  10.25 long) loaded across the layer lines. Estimated breaking loads at about 25 MPa between layers:

  | Load | Vertical | Rearward (teeth levering a bite back) |
  |---|---|---|
  | Point load at the tip | ~7 N | ~3.7 N |
  | Spread across the bite | ~14 N | ~7 N |

  The old flat strip broke at about 1.3 N. Push-test the printed halves at the window centre with 20 N.
  v2: key or bond the halves there.
- **Bite 2 dragged up in state B:** with spring B this is a **Moon** effect and harmless. The margin is 1.11 on
  Earth and 1.02 on the Moon (spring A: 1.03 on Earth). Even if it does rise, the 0.65 gap to the clip roof caps it, and
  bite 2 drops back when bite 1 stops (VERIFICATION §9.10).
- **Bites onto the bridge:** fixed in v1.1 for upright bites (they step down ≥ 0.2, §9.11). Leaning bites
  are #14.
- **Lift margin:** real lift ≈ 13.9 with hole play (≥ 13.5). Lever bending under an 8 N chin (6 × 5 PETG,
  14 mm arms) costs roughly another 0.1, which leaves about 0.3 of margin. Holes printed undersize and then
  reamed give the same; holes left oversize eat the margin.
- **Pin slots:** with the elevator or plunger centred, the pins keep 0.18–0.40 from the slot ends. At the
  extreme of their ±0.3 X play the pin just nudges the part within its play; it does not bind.
- **Last bite taken (state D):** the push ribs are 0.8 from the elevator rear face with the elevator
  centred, 0.5 if it sits at the back of its play.

## 8. The last bite can be launched in lunar gravity (review finding, not fixed)

This applies to **any last bite 12.7 thick or thinner**, not only min thickness. The follower is on its stop
at F = −1.6, which holds a 12.7 bite with exactly zero preload and leaves a gap for anything thinner (0.5
for a min bite). Only a thicker bite (up to 13.2) is still clamped by the spring. At the hard stop the elevator
stops dead. At 1/6 g, a chin tuck of about 0.22 m/s is enough to throw the bite clear of the ~16 mm retention
(0.55 m/s at 1 g, so bench tests won't show it). The spec accepts the gap (§7 C).

**v1.1 candidate:** TPU lips on the window side walls, as the Gameplan proposed. The lip grip adds to the drag
an uneaten bite has to beat to sink back, so **keep it at 0.2 N or less**, and buy the return spring at its
nominal 0.13 N/mm / free 38 or stiffer:
- With a 0.2 N lip, the 1.43 N return force beats 0.74 + 0.2 N with dry food (1.5× margin) and 1.13 + 0.2 N
  with sticky food (1.07× margin).
- A 0.3 N lip leaves no sticky-food margin (1.00×). With the soft end of the BOM range (free 37, k 0.12,
  1.2 N) it fails.

Alternative: a flexure finger on the follower.

## 9. Paddle pad retention

The pad is located by rims over the flange ends and held with CA; scuff the flange first. A TPU snap bead
was modelled but left sub-0.8 slivers, so it was removed. The pad is not held mechanically in Z. Check the
glue joint after every wash, or design a clip-over pad in v2.

## 10. Crumb and saliva paths

After arming, crumbs and saliva can get in through:
- the gate slot (36 mm²) and the open socket-roof areas (about 300 mm², more because of #1), which lead onto
  bite 2 and the clip roof
- the window, which stays open for the whole EVA
- the 0.3 gaps round the elevator and plunger, which lead into the mechanism
- (v1.1) the bridge top (X −2.1 → 0, Z 3.7), which no bite sweeps any more because every bite passes 0.2-0.75
  above it, and the rail end faces (Z 3.7 → 4.5) now exposed at the mouth: a small crumb shelf. Brush it
  out when cleaning.

Cleaning means taking the receiver apart, and the pivot pin and dowels are pressed in. v2 options: a
captive shutter over the gate slot, and a slit TPU membrane over the window (which would also help #8).

## 11. `PADDLE_X` reach range

A reach test moving the paddle **further** from the window (−46.2) passes every check. The ring hook and all
paddle-related features follow `PADDLE_X`. Moving the paddle **closer** (−26.2) does not work: the 25 mm pad
overlaps the window and backstop lip, and a 9 mm lever has to swing ±52°. The practical limit toward the
window is about **+7 mm** (`PADDLE_X` ≥ −29).

## 12. Clip in its socket

The one-sided latch and the ribbon clamp make a small yaw couple, so the clip can sit up to 0.3 off-centre in
Y. In Z it rests on the socket floor, **0.1** low (v1.1; it was 0.3), and can float up to 0.3 against the roof. The
follower's front chamfer and underside relief, and the bore lead-in, handle this. `verify.py` checks states C
and D-taken with the clip moved ±0.3 in Y, −0.1 and +0.3 in Z. Floated up, the latch tooth just touches the
notch floor, at exactly the moment the clip reaches the roof (§9.13).

## 13. Review coverage

- **Round 1:** four independent reviewers: geometry vs spec, kinematics, printability and assembly,
  food safety/FOD. The geometry reviewer was cut off by a usage limit; the rest reported, and their valid
  findings were fixed (CHANGES.md section C).
- **Round 2:** geometry vs spec (full audit, about 190 point probes: no dimensional mismatch found),
  kinematics re-check, and print/assembly/FOD re-check. Fixes are in CHANGES.md section D.
- **Round 3:** one reviewer re-checked every round-2 fix. No blocker or major finding; four minor/nit items
  (pin-hole parameters, follower relief, screw head type, stale numbers) fixed in CHANGES.md section E.
- **Round 4:** convergence check of the round-3 fixes. No geometry finding; four documentation fixes
  (CHANGES.md section F). The loop stopped here: the last two rounds found nothing structural.
- **Team model review (Oct 2 2026):** an independent rebuild found 182 of 182 spec coordinates matching, and a
  second collision engine (manifold3d) found 0 collisions. Its findings became v1.1 (CHANGES.md section G).

## 14. Leaning bites: possible feed stall on Earth (needs the bench test)

The step-down rule (§9.11) and the upright drag numbers in §9.10 assume bites stand upright and centred on the
rails. A rigid, frictionless 2-D check (`cad/lean.py`, VERIFICATION §9.11) shows they don't have to:
- **Every bite width is unstable upright.** Each R2 bite corner sits on an R0.5 rail edge, which acts like a
  four-bar linkage: lean the bite a little and its centre of mass drops. Only friction at the rails and walls
  keeps the bites upright, and a jolt can tip them. The side walls decide where the roll stops. A whole stack
  can lean together, because rotating about the stacking axis doesn't slide one bite face on the next.
- **Where it stops depends on the width:**
  - From 18.0 to ~18.58 wide a bite rolls 5-7° and wedges against both walls; its contact forces add up to about
    **1.73×** its weight (upright: 1.25×).
  - Just wider, it can no longer reach both walls and pinches between one wall and the opposite rail edge, whose
    contact faces almost sideways. The two forces fight each other: **k jumps to about 3.1 at ~18.6 wide**, then
    falls (1.75 at 19.0, 1.34 at 19.5, 1.14 at 20.0).
- **Feed margin with spring B and sticky bites:** upright 1.02-1.07× at the worst Earth tilt (~56-60°
  mouth-up). Leaning min or nominal bites: about 0.91× at ~47°. **At the worst width (~18.6): about 0.79× even
  level, 0.66× at ~32°.** A margin below 1 means a stall is predicted. On the Moon it stays at 4.0× or more in any
  orientation.
- These numbers stack every worst case: μ 0.6 on rails and walls, 10 g bites, the spring 13 % weak, and a rigid,
  frictionless lean. The jump at ~18.6 is a sharp, geometry-sensitive feature of the rigid model. Real food
  deforms, and friction resists the lean in the first place. So this is a credible risk, not a measured result.
- A leaning min bite's low bottom corner hangs into the gap between the rails, **1.0-1.1 below the bridge top**
  (v1: 1.8-1.9). The bridge edge meets that rounded R2 corner at about 60° from vertical. Rolling it upright
  against bite-to-bite face friction could self-lock at a friction of only ~0.2-0.4 (rough torque balance). That
  is no better than the climb v1.1 removed. The CAD can't settle any of this.

**What to do (team decision):**
1. **Bench go/no-go #1 is the real test.** Use sticky dummy bites in three widths: `bite_min` (18),
   `bite_nominal` (19) and **`bite_wedge_test` (18.6, the worst width)**. Rest the clip in the socket and cycle
   all 8, level **and at ~50° mouth-up**. Also tap the clip sideways first to provoke a lean. If all three pass,
   nothing to change.
2. If the wedge-test or min bites stall, the fix is the **rail geometry** (v2, or v1.2 if the team wants it
   before the demo). Make the rail tops flat and wider than a min bite's flat bottom (±7.0), so every bite
   stands on two flats and can't roll. That means a narrower ribbon groove, clamp and keel; spring B's 6.35
   ribbon fits, spring A's doesn't. Tightening the bite-width tolerance is not a fix: the bad widths sit
   inside the band.
3. A stronger feed spring (about 0.5 lb) would raise the margin, but with this return spring the sticky sink-back
   check (§9.10) then fails. The return spring would need re-tuning.
