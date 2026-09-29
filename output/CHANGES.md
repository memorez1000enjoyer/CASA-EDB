# CHANGES - EBD Clip v1 vs. EBD_Build_Spec.md Rev B

Every change below is a **DEFAULT** (or a value the spec left to the CAD agent). **No MUST was changed.**
Each one is in `cad/params.py` next to a `CHANGED` or `ADDED` tag. Things that need a team
decision are in `OPEN_ISSUES.md`.

## A. DEFAULT values changed (old → new → reason)

| # | What | Old (spec) | New | Reason / check that failed |
|---|---|---|---|---|
| 1a | Paddle stroke `PADDLE_STROKE` and lever pivot hole | 14.3; pivot hole Ø2.3 | **14.7**; pivot hole **Ø2.1** | Review: clearance in the round pin holes (free pivot hole, snug end holes) adds about 0.3–0.5 of lost motion that slot play alone misses, which pushed the real lift under 13.5 (§9.7). Tighter pivot plus 0.4 more stroke gives 14.1 in the model and **13.8 with hole play**. |
| 1 | Plunger body length, bottom → flange underside (`FLANGE_OFFSET`, derived) | 49.3 (spec: bottom −1.5, flange underside 47.8 at rest) | **49.0** | The spec's rest numbers assume both pins sit centred in their 2.3 slots. In reality the return spring pushes the plunger up and the lever pushes the elevator onto its ledge, which takes up the play. The real rest is plunger bottom **−1.2** and lever −30.7°. Keeping the spec's flange underside (47.8 = `TOP_Z + PADDLE_STROKE`) and 14.3 stroke (§9.7) needs 49.0. Result: lift **13.7** (the spec's own "≈13.7 effective"). Pressed plunger bottom is −15.5, not −15.8. |
| 2 | Pin slots in the elevator and plunger | end shape not specified (X ranges only) | **square ends**, same X ranges | §9.1: with rounded ends, when bite 2 pushes the elevator 0.3 forward (state B′) the cup pin clipped the rounded slot end near lever 0° (0.045 mm³ overlap). Square ends use the full length: margin +0.10. |
| 3 | Slot lengths when `PADDLE_X` moves | fixed numbers | spec numbers at the default, **grow automatically** (`PIN_WANDER + 1.2`) | The spec says the reach test may move `PADDLE_X` ±10 and "pivot and LEVER_R follow automatically". A shorter lever swings further and needs longer slots. Default geometry is unchanged. |
| 4 | Receiver screws / nut traps | M2 × 16, trap 4.1 AF | **M2 × 20**, trap **4.3 AF** (depth 6.6 as spec) | An M2 × 16 reaches only **0.1 mm** into the nut (29.1 grip − 2 × 6.6). M2 × 20 fully engages and its tip stays 2.5 inside the trap. A printed 4.1 hex won't take a 4.0 AF nut. |
| 5 | Socket-lug bottom (`LUG_Z0`) | −10.0 | **−10.5** | §9.8 walls ≥ 0.8: the Ø4.2 counterbore for the screw at (X 12, Z −7.2) left **0.7** under it. Now 1.2. |
| 6 | Latch tongue, tooth, lift tab (`LATCH_Y`) | Y ±4.0, split in two by the Y = 0 parting line | **Y −4.0 → 0**, in the −Y half only | The +Y half of the socket roof centre would be a **loose island** once the receiver is split. See OPEN_ISSUES #1. |
| 7 | Drum spacer washers (spring B) | "Ø10 × 1.5 washers, one each side" | **rings that slip over the drum**: ID 12.8, OD 14.6, 1.43 thick (`drum_spacer_springB.stl`, print 2) | Ø10 is smaller than the Ø12.5 drum, so it can't locate a coil that sits on the drum. On the axle beside the drum it doesn't fit: 9.4 + 2 × 1.5 = 12.4 > the 10.6 pocket. Rings on the drum fill 9.4 − 6.35 = 3.05 of width and stay 0.35 inside the Ø15.3 pocket. |
| 8 | Ring hook width | 20 | **26** (X −41 → −15), countersunk M2 × 8 | The two spec pilots are 18 apart, which leaves no wall round Ø2.3 holes in a 20-wide bracket. Pan heads would stand into the flange gap. |
| 9 | Optional viewing slot (opaque tube) | one slot Z 16 → 20, X 12 → 125 | **9 windows 10 long with 2.55 webs**, same band | §9.8: one 113-long slot is a 113 mm bridge when printed upright. Each window is now a 10 mm bridge. The default is translucent PETG with no windows (`VIEW_SLOT = False`). |
| 10 | Clip-tube outer chamfers | all outer edges (spec: mouth 0.5 × 45°) | mouth chamfer kept. **Not** on the two vertical back-end edges or on the top long edges over X 0.6 → 3.4 | §9.8 walls: the end-cap screw holes are 0.85 from the end face, and a chamfer there left 0.54. The gate-slot skin is 1.0, and a 0.5 chamfer on top of it left 0.5. |
| 11 | Plunger print orientation (§8.1) | −Y face down | **upside down** (flange top on the bed); one support under the ear | On −Y, the 18-wide flange holds the 12-wide body 3 mm off the bed. The lever notch is open at both X ends ("X full width"), so its cheek becomes a 9 mm cantilever instead of a bridge. Upside down, only the ear's top face needs support. See OPEN_ISSUES #2. |
| 12 | Fit-coupon labels | (text implied) | **engraved dots** | Font strokes leave sub-0.8 slivers. Sleeves: 1-4 dots = 0.20 / 0.25 / 0.30 / 0.35. Pin holes: 1-5 dots = Ø1.9 / 2.0 / 2.1 / 2.2 / 2.3. |

## B. Values the spec left open, and how they were resolved (ADDED)

| What | Resolution |
|---|---|
| Latch tongue tip | Transverse **tip cut X 11.0 → 11.5** added. The spec gives only side cuts from X 11.5 → 24.0, which would leave the tongue joined at both ends. |
| Clamp ridge width | **0.5** (= 0.8 notch − 2 × 0.15 ribbon A); 0.3 tall. For spring B the ribbon is thinner and the clamp sits 0.05 lower (clamp bottom Z = `SPRING_T`). |
| Coil pocket | Ø = formula coil OD + 1.0 = **17.06 (A)** / **15.31 (B)**; the spec rounds A to 17.1. Centre stays at (F + 18.0, Z 8.85) for both springs, as §5.3 says. With B the pocket bottom is Z 1.2 and the ribbon tangent is Z ≈ 1.7 (< 2.0 ✓). |
| Coil OD in each state | Computed from the ribbon actually wound on the drum (15.3-16.1 for A, as the spec says). |
| Bite pose on the rails / bridge | Seat from the R2-on-R0.5 contact: **4.00 / 4.29 / 4.45** (§3). Bites stay upright and settle vertically onto the highest support under them, so a min-width bite 2 half on the bridge sits at Z 4.44. A rigid bite would tilt about 2°; the vertical settle is the conservative model for roof clearance. |
| Slot play | Taken up in the loaded direction: return spring at rest, chin when pressed. The elevator lags 0.3 on the way up, and on the way back down until the pin reaches the lower slot face. |
| Paddle pad "1.0-tall rim" | The pad is 25 long and the flange 16, so the rim is the two **pad ends hanging 1.0 below the flange top** (0.2 clear of the flange ends). A 16.4-wide channel runs underneath. Dome = spherical cap, 3.0 at the centre, 2.0 at the corners, R2 corners. |
| End cap | Plug profile = bore + groove at −0.2, rail notches +0.2. The 0.5 rail-to-wall gaps are **left open** (filling them gives a 0.1 sliver). Pilots Ø1.6 × 5 from both sides. |
| Dowels (3 × Ø2 × 10) | At (X, Z) = (−2.6, −17.75), (−27.5, 19.0), (−46.0, 18.0). Each clears every cavity by ≥ 1.2. Holes are 5.3 deep per half. |
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
| Clip roof: a 20.5 × 138 bridge only 0.3 above the follower | Clip tube now prints **standing on its back end** (brim), so the roof is a wall |
| Spring-B ribbon rose to Z 2.08 (§9.5) | The coil pocket keeps a fixed **bottom** Z; for spring B its centre drops to 7.97 |
| Clip can float 0.3 in its socket, and the follower's square front edges caught the bore opening | 0.6 chamfer on the follower's front vertical edges; 0.4 lead-in on the bore opening at X 0 |
| Pad held by CA only; TPU would have to bridge 16 mm | Pad is now a Y-extrusion printed on its side (no bridges), rims 1.8 deep over the flange ends. A snap bead was tried but left sub-0.8 slivers, so it was removed (OPEN_ISSUES #9). |
| Gate becomes a loose part after arming | Ø2 lanyard hole in the tab |
| Elephant foot on the elevator | 0.3 bottom-edge chamfers |
| Clamp ridge fit exactly 0.8 with no clearance | Ridge 0.4 wide |
| Support placement depends on the slicer | `stl/slicer_helpers/*_SUPPORT_ENFORCER.stl`: use supports = enforcers only |
| Dowel 2 not tied to `PADDLE_X` | Now midway between the plunger channel and the front wall |
