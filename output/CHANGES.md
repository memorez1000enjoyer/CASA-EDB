# CHANGES - EBD Clip v1.1

Sections A-F: the v1 model vs. `EBD_Build_Spec.md` Rev B (all accepted by the team's model review, Oct 2 2026,
and folded into spec Rev C). **Section G: the v1.1 changes** (Rev C follow-up). Since Rev C this repo
(`cad/params.py` + this file) is the geometry master; the spec is the design rationale.

Every change below is a **DEFAULT** (or a value the spec left to the CAD agent). **No MUST was changed.**
Each one is in `cad/params.py` next to a `CHANGED` or `ADDED` tag. Things that need a team
decision are in `OPEN_ISSUES.md`.

## A. DEFAULT values changed (old → new → reason)

| # | What | Old (spec) | New | Reason / check that failed |
|---|---|---|---|---|
| 1 | Lever play, stroke and plunger length: `PADDLE_STROKE`, lever pivot hole, receiver pivot hole, `FLANGE_OFFSET` (derived) | stroke 14.3; lever pivot Ø2.3; receiver pivot Ø2.1 both halves; flange 49.3 above the plunger bottom (spec: bottom −1.5, flange underside 47.8 at rest) | stroke **14.7** (model); lever pivot **Ø2.1**; pivot pin **pressed** (Ø1.9) into receiver_left; flange **49.4** above the bottom | The spec's positions assume pins centred in their holes and slots. In reality the return spring and the hard stop load every joint, so each pin sits against one side of its hole or slot, and the side flips between rest and pressed. Slot play alone (2 × 0.3) with the spec's 14.3 stroke gave lift 13.7. Round-hole clearance costs more on top (0.5 with a Ø2.3 pivot hole), which put the real lift under 13.5 (§9.7). Now, with the pivot tightened and the pin pressed in, hole play costs 0.2. The model (pins at hole centres) gives rest plunger bottom −1.2, lever −30.7° → +31.2°, stroke 14.7, lift 14.1. **With hole play: stroke ≈ 14.9, lift ≈ 13.9**. |
| 2 | Pin slots in the elevator and plunger | end shape not specified (X ranges only) | **square ends**, same X ranges | §9.1: with rounded ends, when bite 2 pushes the elevator 0.3 forward (state B′) the cup pin clipped the rounded slot end near lever 0° (0.045 mm³ overlap). Square ends use the full length: margin +0.10. |
| 3 | Slot lengths when `PADDLE_X` moves | fixed numbers | spec numbers at the default, **grow automatically** (`PIN_WANDER + 1.2`) | The spec says the reach test may move `PADDLE_X` ±10 and "pivot and LEVER_R follow automatically". A shorter lever swings further and needs longer slots. Default geometry is unchanged. |
| 4 | Receiver screws, counterbores, nut traps | M2 × 16; counterbore Ø4.2 × 6.6; trap 4.1 AF × 6.6 | **M2 × 20**; counterbore **Ø4.2 × 9.0**; trap **4.3 AF** × 6.6 | An M2 × 16 reaches only **0.1 mm** into the nut (29.1 grip − 2 × 6.6). With a 9.0 counterbore, an M2 × 20 reaches a nut lying anywhere in its trap, even at the mouth, and pulls it in. Its tip stays 0.1 inside the −Y face. A printed 4.1 hex won't take a 4.0 AF nut. |
| 5 | Socket-lug bottom (`LUG_Z0`) | −10.0 | **−10.5** | §9.8 walls ≥ 0.8: the Ø4.2 counterbore for the screw at (X 12, Z −7.2) left **0.7** under it. Now 1.2. |
| 6 | Latch tongue, tooth, lift tab (`LATCH_Y`) | Y ±4.0, split in two by the Y = 0 parting line | **Y −4.0 → 0**, in the −Y half only | The +Y half of the socket roof centre would be a **loose island** once the receiver is split. See OPEN_ISSUES #1. |
| 7 | Drum spacer washers (spring B) | "Ø10 × 1.5 washers, one each side" | **rings that slip over the drum**: ID 12.8 (13.0 in v1.1, see G), OD 14.6, **1.475** thick (`drum_spacer.stl` in v1.1, print 2 + 2 spares) | Ø10 is smaller than the Ø12.5 drum, so it can't locate a coil that sits on the drum. On the axle beside the drum it doesn't fit: 9.4 + 2 × 1.5 = 12.4 > the 10.6 pocket. Rings on the drum fill 9.4 − 6.35 = 3.05 of width and stay 0.35 inside the Ø15.3 pocket. |
| 8 | Ring hook width | 20 | **26** (X −41 → −15, derived from the two pilots ± 4.0), countersunk M2 × 8 | The two spec pilots are 18 apart, which leaves no wall round Ø2.3 holes in a 20-wide bracket. Pan heads would stand into the flange gap. The width now follows `PADDLE_X` with the second pilot. |
| 9 | Optional viewing slot (opaque tube) | one slot Z 16 → 20, X 12 → 125 | **9 windows 10 long with 2.55 webs**, same band | §9.8: one 113-long slot is a 113 mm bridge when printed upright. Each window is now a 10 mm bridge. The default is translucent PETG with no windows (`VIEW_SLOT = False`). |
| 10 | Clip-tube outer chamfers | all outer edges (spec: mouth 0.5 × 45°) | mouth chamfer kept. **Not** on the two vertical back-end edges or on the top long edges over X 0.6 → 3.4 | §9.8 walls: the end-cap screw holes are 0.85 from the end face, and a chamfer there left 0.54. The gate-slot skin is 1.0, and a 0.5 chamfer on top of it left 0.5. |
| 11 | Plunger print orientation (§8.1) | −Y face down | **upside down** (flange top on the bed); one support under the ear | On −Y, the 18-wide flange holds the 12-wide body 3 mm off the bed. The lever notch is open at both X ends ("X full width"), so its cheek becomes a 9 mm cantilever instead of a bridge. Upside down, only the ear's top face needs support. See OPEN_ISSUES #2. |
| 12 | Fit-coupon labels | (text implied) | **engraved dots** | Font strokes leave sub-0.8 slivers. Sleeves: 1-4 dots = 0.20 / 0.25 / 0.30 / 0.35. Pin holes: 1-5 dots = Ø1.9 / 2.0 / 2.1 / 2.2 / 2.3. |
| 13 | Orthodontic-elastic hook posts (§6.6) | two Ø2 posts: one on the ear, one at the receiver top near X −46 | **omitted** | The ear moves inside the enclosed ear slot, so an elastic from it has no path to the top, and the receiver screw at (X −45.8, Z 24) sits where a channel would go. The return spring does the job. Details and how to add it: OPEN_ISSUES #3. |

## B. Values the spec left open, and how they were resolved (ADDED)

| What | Resolution |
|---|---|
| Latch tongue tip | Transverse **tip cut X 10.5 → 11.5** (1.0) added. The spec gives only side cuts from X 11.5 → 24.0, which would leave the tongue joined at both ends. |
| Clamp ridge width | **0.4** (one line width), 0.3 tall. It leaves 0.2 each side of it in the 0.8 notch for the ribbon (0.15 A / 0.10 B). For spring B the clamp sits 0.05 lower (clamp bottom Z = `SPRING_T`). |
| Coil pocket | Ø = formula coil OD + 1.0 = **17.06 (A)** / **15.31 (B)**; the spec rounds A to 17.1. The pocket **bottom** is kept for every spring (v1: Z 0.32; **v1.1: Z 0.30**, see G), so for B the centre is lower: Z 7.96 (A 8.83). The spec's fixed centre put the spring-B ribbon at Z 2.08, failing §9.5. |
| Coil OD in each state | Computed from the ribbon actually wound on the drum (15.3-16.1 for A, as the spec says). |
| Bite pose on the rails / bridge | Seat from the R2-on-R0.5 contact: **4.00 / 4.29 / 4.45** (§3). Bites stay upright and settle vertically onto the highest support under them. (v1: a min-width bite 2 half on the 4.5 bridge sat at Z 4.44. v1.1: the bridge is at 3.7, below every rail seat, so bites overhanging it stay on the rails.) |
| Slot play | Taken up in the loaded direction: return spring at rest, chin when pressed. The elevator lags 0.3 on the way up, and on the way back down until the pin reaches the lower slot face. |
| Paddle pad "1.0-tall rim" | The pad is 25 long and the flange 16, so the rim is the two **pad ends hanging below the flange top** (0.2 clear of the flange ends). Now 1.8 deep (see C). Dome curved along X: 3.0 at the centre, 2.0 at the ends. 1.0 × 45° plan corners. |
| End cap | Plug profile = bore + groove at −0.2, with notches clearing the rails (which now run to the side walls). Pilots Ø1.6 × 5 from both sides. |
| Dowels (3 × Ø2 × 10) | At (X, Z) = (−2.6, −17.75), (−23.6, 19.0) (between the two X −23.6 screws), (−46.0, 18.0). Each clears every cavity by ≥ 1.2. Holes are 5.3 deep per half. |
| Return spring, config B | v1: k 0.12 N/mm, free 35, about 1.0 N at rest, per §6.6 "a lighter spring". **v1.1: k 0.13, free 38, wire 0.40** (see G). Config A: k 0.20, free 35. |
| Bench base | 196 × 52 × 4 plate. Fixed jaw on −Y, a jaw with 2 × M3 thumb screws (drop-in nut slots) on +Y, an end stop at −X, and a rest 0.6 under the clip. |
| Chamfers the spec asked for "on every bite/face-touchable edge" | Window side top edges 0.3 (stripper edge left **sharp**), backstop lip 0.5, elevator side-top 0.3, flange corners 0.5, socket entry lead-in 0.5, receiver outer edges 0.5. |
| Ring hook shape | Placeholder **J-hook**: leg on the −Y face, seat 8.0 above the top surface, a gap of `RING_FLANGE_T` + 2 × 0.3, and a 6.0 lip. All values are `RING_*` params. |
| Gate tab top edge | 0.4 chamfer for fingers. |

## C. Adversarial review round 1 (four independent reviewers), fixes applied

| Finding | Fix |
|---|---|
| Stripper strip, split at Y = 0, is two 0.8 × 2.0 × 10 cantilevers that break at ~1.3 N (FOD blocker) | The strip rises to Z 35.8 and joins the socket front band (L-section, about 5× stronger). Its lower bite-side edge stays sharp; the top is chamfered 0.5. |
| Latch tongue side cuts 0.5 would fuse under a 13 mm bridge | `TONGUE_CUT_W` and tip cut **1.0** |
| Backstop lip only ±10.25: a bite could slide round its ends | Full width, all edges chamfered 0.5 |
| Unchamfered face-zone edges | 0.5 chamfer on the plunger-channel rim, stripper-wall top and lift tab; 0.3 on the gate-slot and tab-channel rims and on the exposed Y = 0 roof and tongue edges; 0.5 on the plunger stem edges |
| Rail-to-wall crevices are crumb traps | Rails run to the wall (`RAIL_OUT_Y` 9.75 → 10.25) |
| Clip roof: a 20.5 × 138 bridge only 0.3 above the follower | First changed to printing standing on end, then **reverted in round 2** to the spec's −Z orientation. The 20.5 bridge meets §9.8, the spec already gives a remedy (a lid if sag > 0.2), and upright printing put layer ridges across the sliding direction and the gate face on a bridge. |
| Spring-B ribbon rose to Z 2.08 (§9.5) | The coil pocket keeps a fixed **bottom** Z; for spring B its centre drops to 7.97 |
| Clip can float 0.3 in its socket, and the follower's square front edges caught the bore opening | 0.6 × 45° chamfer on the follower body's front vertical edges, continued along the same line through the push ribs (rib crests now end at Y ±8.75; a min bite's flat face is ±7.0). 0.4 lead-in on the bore opening's vertical edges at X 0. |
| Pad held by CA only; TPU would have to bridge 16 mm | Pad is now a Y-extrusion printed on its side (no bridges), rims 1.8 deep over the flange ends. A snap bead was tried but left sub-0.8 slivers, so it was removed (OPEN_ISSUES #9). |
| Gate becomes a loose part after arming | Ø2 lanyard hole in the tab |
| Elephant foot on the elevator | 0.3 bottom-edge chamfers |
| Clamp ridge fit exactly 0.8 with no clearance | Ridge 0.4 wide |
| Support placement depends on the slicer | `stl/slicer_helpers/*_SUPPORT_ENFORCER.stl`: use supports = enforcers only |
| Dowel 2 not tied to `PADDLE_X` | Now midway between the plunger channel and the front wall |

## D. Adversarial review round 2 (three reviewers), fixes applied

| Finding | Fix |
|---|---|
| Hole-play lift estimate: one reviewer said 0.6, not 0.3 | Worked through joint by joint: the rest pose is fixed by the ledge and the pressed pose by the hard stop, so each hole's radial clearance (pivot counted twice on a 1:1 lever) comes off the lift and adds to the stroke. 0.6 is stroke − lift, which double-counts. `kinematics.with_hole_play()` now computes it explicitly. The reviewer's other suggestion was taken: the pivot pin is **pressed into receiver_left** (Ø1.9, `RCV_PIVOT_HOLE_L`). Real lift **13.9**, real stroke **14.9**. |
| Support enforcers stopped 0.05 short of the roofs they support, so slicers would add nothing | Each enforcer now reaches **0.6 into** the supported surface |
| Bite-channel enforcer put support scars on the elevator's sliding face | Removed. That wall prints as a 27 mm bridge; the README adds a dry-fit and scrape step. |
| Plunger needed a different support mode from the receiver halves | `plunger_SUPPORT_ENFORCER.stl` added (ear only, clear of the flange's hard-stop face), so every part uses "enforcers only" |
| README said M2 × 16 in step 8; a loose nut at the trap mouth was beyond the M2 × 20 tip | README fixed. Counterbore depth **6.6 → 9.0**, so the screw reaches a nut anywhere in its trap and pulls it in. |
| Ring hook didn't follow `PADDLE_X` (second pilot left the bracket) | `RING_HOOK_X` derived from the pilots ± 4.0 |
| Clip-tube orientation change not justified by a failed check | Reverted to the spec's −Z (see C) |
| Sharp stripper-wall outer corners; pockets under the lip and wall ends | Receiver top long edges chamfered only between the lip and the wall; stripper wall's outer vertical corners chamfered 0.5 |
| `CLR_PRESS` unused | `PIN_PRESS_D = Ø2 − CLR_PRESS`, `PIN_SNUG_D = Ø2 + CLR_PRESS`, `PIN_FREE_D = Ø2 + CLR_SLIDE` (superseded in E: each hole is now its own coupon value) |
| Loading procedure left the stack unheld between bites | README: use the gate as a ratchet, one bite at a time |
| Stale docs (CHANGES rows, docstrings, OPEN_ISSUES numbering) | Rewritten |
| Clip sitting 0.3 low: the follower's square bottom-front edge had to climb the bridge lead-in, then had no clearance under the clip roof (last bite could jam, esp. spring B) | Follower underside **relieved 0.4 over its front 2.0** (`FOLLOWER_FRONT_RELIEF`) (raised to 0.7 in E; with the v1.1 bridge at 3.7 it now has 1.4 to spare, kept anyway): at its stop that part sits over the bridge and never touches it. `verify.py` now also checks states C and D-taken with the clip shifted ±0.3 in Y and in Z. |
| Tightened lever pivot left no free-running joint (binding risk against ~15–27 N·mm of return torque) | Lever pivot hole is a **running fit** `PIN_RUN_D` (2.1): ream it with a Ø2.1 drill so the lever spins freely without wobble; the pin itself is pressed into receiver_left |
| Pad rims 1.8 deep sat only 0.2 above the top at the hard stop (a deflected pad would land first) | `PAD_RIM_H` **1.2** (0.8 clear) |

## E. Adversarial review round 3 (one reviewer re-checking round 2), fixes applied

Round 3 confirmed the round-2 fixes: the hole-play derivation (checked sign by sign), the follower relief and
clip-float poses, the enforcer alignment, the counterbore/nut stack and the README. It found nothing blocking.

| Finding | Fix |
|---|---|
| One `CLR_PRESS` drove the press hole down and the snug/running holes up; a printer that prints holes small needs all of them larger. `M2_CLEAR_D` followed `CLR_SLIDE`, so a 0.20 coupon result gave Ø2.2 screw holes that an M2 would thread into. | Pin holes are **separate numbers read straight off the coupon**: `PIN_PRESS_D` 1.9, `PIN_SNUG_D` 2.1, `PIN_RUN_D` 2.1, `PIN_FREE_D` 2.3 (spec §8.2 values, unchanged). `M2_CLEAR_D` is its own 2.3 (spec §5.2). No geometry changed at the defaults. README §2 step 4 rewritten. |
| Follower relief left 0.1 over the bridge with the clip 0.3 low | `FOLLOWER_FRONT_RELIEF` 0.4 → **0.7** (push ribs start at Z 9.75, so it costs nothing) |
| BOM allowed pan-head M2 × 20; an ISO 7045 pan head (up to Ø4.0) may not seat in a printed Ø4.2 counterbore | BOM: **socket head only** (ISO 4762, head Ø3.8) |
| Stale numbers: README "13.7 mm" lift; params comments (≈13.7 lift, ~0.3 play, flange 47.8, pin Z −12.35, "M2 x 16", "0.7 wall"); verify.py mass note "M2x16" | Corrected to 13.9, 0.2, 48.2, −12.75, M2 × 20, ≥ 0.8 |

## F. Review round 4 (convergence check)

No geometry finding: the round-3 fixes check out (STL volumes unchanged at the defaults apart from the follower
relief). Four documentation fixes: the BOM now lists the Ø2.1 and Ø2.4 reaming drills the procedures use;
README §2 names the fourth ("run") pin fit and why its default equals snug; `CLR_PRESS` is marked as a spec
table value the model doesn't use; the section-D relief row points to E.

## G. v1.1 (spec Rev C follow-up, after the team's independent model review)

The review rebuilt every part, probed 182 spec coordinates and re-ran every spring-B state through a second
collision engine; it accepted everything above. These are the v1.1 changes. The prototype patch for items 2-4
was applied as given, then its hard-coded numbers were turned into parameters.

| # | What | Old | New | Reason |
|---|---|---|---|---|
| G1 | `DEFAULT_SPRING` | A (1.48 lb) | **B (0.33 lb)** | The team bought B; it is the final spring. Default STLs (`follower.stl`, `drum_spacer.stl`), states and renders are now spring B. Spring A parts get a `_springA` suffix (`follower_springA.stl`; A needs no spacer rings). |
| G2 | `CUP_TOP_Z` (new PARAM): bridge top and cup rest height | 4.5 (= rail top) | **3.7** | **Feed-jam risk.** Bites seat on the rails at 4.0-4.45 (3.9-4.35 with the clip resting on its floor), so each had to climb a 0.6 × 45° lead-in onto the 4.5 bridge. For rigid upright bites that climb self-locks once bite-to-bite friction reaches ~0.43 whatever the spring force; wafer paper or sticky food gets there. (A shallower ramp was tried in the review and rejected: the 2.1-long bridge can't finish the lift, so the climb moves to the elevator's rear chamfer.) Now every bite steps **down** (≥ 0.2, new check §9.11). Cost: min exposure 9.3 → **8.5** (≥ 8.0), retained depth 15.1 → **15.9**. Lift unchanged (14.1 model / 13.9 real). |
| G3 | `ELEV_H` | 20.0 | **19.2** (derived: `CUP_TOP_Z − LEDGE_Z`) | Keeps the ledge (Z −15.5), pivot, lever, plunger and every channel exactly where they were. |
| G4 | `BRIDGE_LEADIN` | 0.6 × 45° lead-in | **0.2 edge break** | The bridge is below every bite seat, so it needs no lead-in. The −X 0.3 rear chamfer stays. The bore continuation and the stop-face opening now start at Z 3.7. |
| G5 | `SOCKET_FLOOR_CLR` (new): socket floor | 0.30 below the clip (Z −2.3) | **0.10** (Z −2.1); roof still 0.30 above | The clip always rests on the floor under gravity, which cost 0.3 of height: latch engagement only **0.4**. Now **0.6** (§9.13), and the bite step into the receiver is smaller. Socket outer bottom −4.3 → −4.1. Clip-float poses are now dz −0.1 / +0.3. |
| G6 | Return spring (spring B): `rs_k`, `rs_free`, `RS_WIRE` | k 0.12, free 35, wire 0.6 (model) | **k 0.13, free 38, wire 0.40** (0.45 max) | With real pin play the rest installed length is **27.0**, not 26.8: free 35 at 0.12 gave only ~1.0 N, too little for sticky food. Now 1.43 N at rest, 3.37 N pressed: chin force **2.2 → 4.1 N**, an uneaten bite returns with **1.95×** margin (μ_bite 0.4), and still returns (1.26×) at μ_bite 0.6 with the spring 10 % strong. §9.10 now uses the real (hole-play) rest pose. |
| G7 | Return-spring solid length (new check §9.12) | not checked | **≤ 10 and < 12.1 pressed** | Stock 6 mm springs often use 0.5-0.6 wire. At the rate this design needs, a 0.5-wire spring is solid at 11-22 mm (only the largest OD at the stiffest rate stays under the 12.1 stroke end), so it loses lift. A stock 0.6-wire spring of this size is several times too stiff. At 0.40 wire the solid length is 5.6 (B) / 4.1 (A). **The model found a hole in the BOM range:** 0.45 wire on a 5.5 OD spring is 10.8-13.2 solid (coil-binds at k 0.12), and 10.3 on a 6.0 OD at k 0.12. The README BOM line says so. |
| G8 | `SPACER_ID_CLR` | 0.15 (ring ID 12.8) | **0.25** (ID 13.0) | Small vertical hole: FDM prints it undersize. README: print 4 (2 spares) at 100 % infill. The ring wall is now exactly 0.8 radially (two perimeter lines, the absolute minimum; it carries no load). The OD stays 14.6: a bigger ring would cut its 0.35 clearance in the coil pocket, whose top is a sagging printed arch. |
| G9 | `POCKET_BOT_Z` | 0.318, derived from the spring-A coil through the global `DRUM_D` | **0.3 constant** + an assertion that the follower rear wall is ≥ 1.2 | Latent bug: a bigger drum (e.g. the 0.22 lb fallback spring, drum Ø15) pushed the pocket below the groove floor and thinned the rear wall under 1.2. Now pocket centre Z = pocket radius + 0.3 (spec Rev B.2): A 8.83, B 7.96 (rear walls 1.47 / 2.35). |
| G10 | Verification added | - | §9.11 step-down (+ a leaning-bite analysis, `cad/lean.py`), §9.12 solid length, §9.13 latch engagement, §9.10 feed margins (contact-angle factor, follower mass, Earth level / vertical / worst incline, Moon), bite-2 drag-up margin, return-spring BOM-range table | Follow-up items 2, 3, 4, 9. |
| G11 | Output clean-up | stale files could linger after a rename | `export.py` deletes previously generated STL/STEP files before writing | `follower_springB.stl` / `drum_spacer_springB.stl` would otherwise have stayed next to the new names. |
| G12 | README | | spring-B BOM first; the exact return-spring BOM line; US equivalents (reamers #45/#44, 3/32″, 5/64″ music wire, cut-length limits, M3 × 12-16); corrected clip step 3 (ring → coil → ring); receiver steps 5-7 (insertion paths **checked in CAD**: straight drops hit the lever by up to 134 mm³ for the elevator and 43 mm³ for the plunger, the described paths are clear); first bite with the gate out; bench-base 195.8 mm length; bench go/no-go tests | Follow-up item 7. |
| G13 | Receiver stripper wall (found while rebuilding v1.1) | its top outer edges square, the socket's chamfered from X 0 | **same 0.5 chamfer along the stripper wall** | The step at X 0 left a 0.37 corner sliver (§9.8 walls); v1 had it too, but the sparser wall sampling missed it. |
| G14 | Printability wall sampling | ~2 samples / mm², max 40 000 | **~4 / mm², max 80 000** | So small slivers like G13 aren't missed. |
| G15 | Docs corrections (follow-up item 8) | | OPEN_ISSUES #7 (bite-2 drag-up is a Moon effect for B), #8 (any last bite ≤ 12.7), CHANGES row 7 (ring 1.475) and row 13 (elastic posts) | |

## H. Adversarial review of v1.1 (one reviewer), fixes applied

| Finding | Fix |
|---|---|
| **Leaning min-width bites (MAJOR):** §9.10 used the upright contact factor 1.25 for min bites, but they lean and wedge against the walls (factor **1.77**). And the "probably not a self-locking climb" reassurance was not supported. | `lean.py` now solves the contact forces and checks upright stability; §9.10 reports a leaning row (spring B: **0.91× at ~47° mouth-up on Earth, a stall predicted** in the 1-g worst case; ≥ 5.5× on the Moon). §9.11 and OPEN_ISSUES #14 are reworded (frictionless worst case; corner climb could self-lock at μ ~0.2-0.4) with options: bench test at ~50° tilt, bite width ±0.8 (Esther's call), v2 rails. |
| Feed margin left out the drum turning on its axle | Included: μ 0.3 × pin radius ÷ coil radius (4.3 % for B). The follower pitch moment is stated as not modelled. |
| TPU-lip candidate (#8) had no sticky-food margin at 0.3 N | Cap the lip at 0.2 N, and buy the return spring at the nominal rate or stiffer |
| Collision check never ran the full stack at the clip's gravity rest; clip-shift poses didn't move the bites in the clip | Bites on the rails now ride with the clip. Added A / B / B′ with the clip on its floor, and A / B′ with the clip ±0.3 in Y. |
| README: "`CLR_SLIDE` sets every sliding fit" (not the socket floor any more); spring-A return spring had no wire spec | `SOCKET_FLOOR_CLR` explained, with a dry-fit fallback (0.2). Spring-A return spring: wire 0.40-0.45, solid ≤ 10. |
| Stale text: OPEN_ISSUES #3 (old return spring), comments in `parts_receiver.py` / `export.py`; zip shipped `__pycache__`; §9.10 table order; G7 wording; the bridge top is now a crumb shelf | Fixed; crumb shelf added to OPEN_ISSUES #10 |

