# CHANGES - EBD Clip v1 vs. EBD_Build_Spec.md Rev B

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
| 7 | Drum spacer washers (spring B) | "Ø10 × 1.5 washers, one each side" | **rings that slip over the drum**: ID 12.8, OD 14.6, 1.43 thick (`drum_spacer_springB.stl`, print 2) | Ø10 is smaller than the Ø12.5 drum, so it can't locate a coil that sits on the drum. On the axle beside the drum it doesn't fit: 9.4 + 2 × 1.5 = 12.4 > the 10.6 pocket. Rings on the drum fill 9.4 − 6.35 = 3.05 of width and stay 0.35 inside the Ø15.3 pocket. |
| 8 | Ring hook width | 20 | **26** (X −41 → −15, derived from the two pilots ± 4.0), countersunk M2 × 8 | The two spec pilots are 18 apart, which leaves no wall round Ø2.3 holes in a 20-wide bracket. Pan heads would stand into the flange gap. The width now follows `PADDLE_X` with the second pilot. |
| 9 | Optional viewing slot (opaque tube) | one slot Z 16 → 20, X 12 → 125 | **9 windows 10 long with 2.55 webs**, same band | §9.8: one 113-long slot is a 113 mm bridge when printed upright. Each window is now a 10 mm bridge. The default is translucent PETG with no windows (`VIEW_SLOT = False`). |
| 10 | Clip-tube outer chamfers | all outer edges (spec: mouth 0.5 × 45°) | mouth chamfer kept. **Not** on the two vertical back-end edges or on the top long edges over X 0.6 → 3.4 | §9.8 walls: the end-cap screw holes are 0.85 from the end face, and a chamfer there left 0.54. The gate-slot skin is 1.0, and a 0.5 chamfer on top of it left 0.5. |
| 11 | Plunger print orientation (§8.1) | −Y face down | **upside down** (flange top on the bed); one support under the ear | On −Y, the 18-wide flange holds the 12-wide body 3 mm off the bed. The lever notch is open at both X ends ("X full width"), so its cheek becomes a 9 mm cantilever instead of a bridge. Upside down, only the ear's top face needs support. See OPEN_ISSUES #2. |
| 12 | Fit-coupon labels | (text implied) | **engraved dots** | Font strokes leave sub-0.8 slivers. Sleeves: 1-4 dots = 0.20 / 0.25 / 0.30 / 0.35. Pin holes: 1-5 dots = Ø1.9 / 2.0 / 2.1 / 2.2 / 2.3. |

## B. Values the spec left open, and how they were resolved (ADDED)

| What | Resolution |
|---|---|
| Latch tongue tip | Transverse **tip cut X 10.5 → 11.5** (1.0) added. The spec gives only side cuts from X 11.5 → 24.0, which would leave the tongue joined at both ends. |
| Clamp ridge width | **0.4** (one line width), 0.3 tall. It leaves 0.2 each side of it in the 0.8 notch for the ribbon (0.15 A / 0.10 B). For spring B the clamp sits 0.05 lower (clamp bottom Z = `SPRING_T`). |
| Coil pocket | Ø = formula coil OD + 1.0 = **17.06 (A)** / **15.31 (B)**; the spec rounds A to 17.1. Spring A: centre (F + 18.0, Z 8.85) as §5.3 says. The pocket **bottom** (Z 0.32) is kept for every spring, so for B the centre is Z 7.97. The spec's fixed centre put the spring-B ribbon at Z 2.08, failing §9.5. |
| Coil OD in each state | Computed from the ribbon actually wound on the drum (15.3-16.1 for A, as the spec says). |
| Bite pose on the rails / bridge | Seat from the R2-on-R0.5 contact: **4.00 / 4.29 / 4.45** (§3). Bites stay upright and settle vertically onto the highest support under them, so a min-width bite 2 half on the bridge sits at Z 4.44. A rigid bite would tilt about 2°; the vertical settle is the conservative model for roof clearance. |
| Slot play | Taken up in the loaded direction: return spring at rest, chin when pressed. The elevator lags 0.3 on the way up, and on the way back down until the pin reaches the lower slot face. |
| Paddle pad "1.0-tall rim" | The pad is 25 long and the flange 16, so the rim is the two **pad ends hanging below the flange top** (0.2 clear of the flange ends). Now 1.8 deep (see C). Dome curved along X: 3.0 at the centre, 2.0 at the ends. 1.0 × 45° plan corners. |
| End cap | Plug profile = bore + groove at −0.2, with notches clearing the rails (which now run to the side walls). Pilots Ø1.6 × 5 from both sides. |
| Dowels (3 × Ø2 × 10) | At (X, Z) = (−2.6, −17.75), (−23.6, 19.0) (between the two X −23.6 screws), (−46.0, 18.0). Each clears every cavity by ≥ 1.2. Holes are 5.3 deep per half. |
| Return spring, config B | k = **0.12 N/mm** (free 35), about 1.0 N at rest, per §6.6 "a lighter spring". Config A: k = 0.20. |
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
| `CLR_PRESS` unused | `PIN_PRESS_D = Ø2 − CLR_PRESS`, `PIN_SNUG_D = Ø2 + CLR_PRESS`, `PIN_FREE_D = Ø2 + CLR_SLIDE` |
| Loading procedure left the stack unheld between bites | README: use the gate as a ratchet, one bite at a time |
| Stale docs (CHANGES rows, docstrings, OPEN_ISSUES numbering) | Rewritten |
| Clip sitting 0.3 low: the follower's square bottom-front edge had to climb the bridge lead-in, then had no clearance under the clip roof (last bite could jam, esp. spring B) | Follower underside **relieved 0.4 over its front 2.0** (`FOLLOWER_FRONT_RELIEF`): at its stop that part sits over the bridge and never touches it. `verify.py` now also checks states C and D-taken with the clip shifted ±0.3 in Y and in Z. |
| Tightened lever pivot left no free-running joint (binding risk against ~15–27 N·mm of return torque) | Lever pivot hole is a **running fit** `PIN_RUN_D` (Ø2 + `CLR_PRESS` = 2.1): ream it with a Ø2.1 drill so the lever spins freely without wobble; the pin itself is pressed into receiver_left |
| Pad rims 1.8 deep sat only 0.2 above the top at the hard stop (a deflected pad would land first) | `PAD_RIM_H` **1.2** (0.8 clear) |
