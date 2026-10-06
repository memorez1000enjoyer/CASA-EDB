# EBD Clip: Claude Code session report (v1 → v1.1)

**Repo:** `memorez1000enjoyer/CASA-EDB`, branch `claude/epic-cerf-hjqhd3` (the repo's only branch). Latest commit: d64fab1.
**Package:** `EBD_Clip_v1.1_output.zip` at the repo root, which is the same content as the `output/` folder.

## 1. What was built (v1, from spec Rev B)
- **Model:** a parametric CadQuery model in `output/cad/`. Every dimension lives in `params.py` under the spec's names, tagged MUST/DEFAULT/DERIVED/CHANGED/ADDED.
- **Outputs:**
  - print-oriented STLs in `output/stl/`
  - STEP parts and state assemblies (A, B, B′, C, D, D-taken, E) in `output/step/`
  - renders and Y=0 sections in `output/renders/`
  - support-enforcer helper files in `stl/slicer_helpers/`
- **Verification:** `verify.py` writes `VERIFICATION.md`. It covers every §9 check at min/nom/max bites for both springs, using exact B-rep collision across all states, lever sweeps and clip-float poses.
- **Docs:** `README.md` (student guide: fit coupon, print table, bill of materials, assembly), `CHANGES.md` (every DEFAULT change logged old → new → reason) and `OPEN_ISSUES.md` (spec defects and team decisions).
- **Review:** four adversarial review rounds on v1. All of their fixes are logged in CHANGES sections C–F.

## 2. v1.1 (from the Rev C follow-up, the model review and the prototype patch): all items done
- **Spring B is the default.** Spring-A parts carry a `_springA` suffix.
- **`CUP_TOP_Z` = 3.7.** The bridge and the cup now sit below every bite's seat on the rails, so bites step down into the receiver by at least 0.20 (new check §9.11). The elevator is 19.2 tall. The bridge's front edge is now a 0.2 edge break, set by a parameter.
- **Socket floor clearance is 0.1.** Latch engagement goes from 0.4 to 0.6 (new check §9.13).
- **Return spring is k 0.13, free length 38, wire 0.40.** It is checked at the real hole-play rest pose:
  - chin force 2.2 → 4.1 N
  - an uneaten bite sinks back with a 1.95× margin (1.26× with sticky food)
  - new check §9.12: solid length 5.6 mm against the 10 mm limit
- **Spacer rings:** bore clearance raised to 0.25.
- **Coil pocket:** `POCKET_BOT_Z` is now a fixed 0.3, with an assertion that the follower's rear wall stays at least 1.2.
- **Feed margins** are reported in §9.10.
- **README:**
  - the BOM's return-spring line, word for word
  - corrected assembly steps; the insertion paths were checked in CAD, and straight drops do collide
  - US hardware equivalents
  - first bite loaded with the gate out
  - the bench base's 195.8 mm length
  - the four go/no-go tests
- **Collision poses:** 258 in total, now including full stacks with the clip at its gravity rest and with the clip offset in Y. Zero unintended overlaps.
- **Extra fix:** a 0.37 mm corner sliver on the receiver, which v1 also had, was found and fixed. The wall-thickness checker now samples twice as densely.

## 3. Status (VERIFICATION.md)
- **Pass:** §9.1–9.7 and 9.9–9.13.
- **§9.8 flagged:** the receiver halves and the plunger need supports; enforcer files are supplied.
- **§9.10 flagged:** spring A's chin force is above 6 N, and leaning bites (§4) give a feed margin below 1.0 on Earth.

## 4. Issues found that the team should know about
1. **The BOM's "0.45 max" return-spring wire is unsafe on a 5.5 OD spring.** It goes solid at 10.8–13.2 mm, which can coil-bind before the 12.1 mm stroke end. A note in the README says to buy 0.40.
2. **Leaning bites (OPEN_ISSUES #14) are the biggest open risk.**
   - **The mechanism:** each bite's rounded R2 corners rest on the rails' R0.5 edges, so every bite width is unstable upright and only friction holds it there. If a bite leans, it wedges against the side walls and drag rises.
   - **The numbers:** with spring B and sticky bites, the worst Earth feed margin is about 0.91× (min and nominal widths) and about **0.79× even level at roughly 18.6 mm wide**. On the Moon it is 4.0× or more.
   - **The caveat:** these come from a rigid, frictionless model. It is a credible risk, not a measured result.
   - **The test:** bench go/no-go #1, using `bite_wedge_test.stl` (18.6 mm), level and at about 50° mouth-up.
   - **If it stalls:** make the rail tops flat (clip-side parts only; spring B only). That redesign has **not** been done; it is waiting on the team's decision.
3. The other known issues are unchanged:
   - latch only in the −Y receiver half (spec defect)
   - supports needed in the receiver halves and plunger
   - ring-hook dimensions are placeholders until the neck ring is measured
   - last-bite launch risk at 1/6 g
   - only undock an empty clip

## 5. What to print
Print everything in `output/stl/`, the top-level `.stl` files only, following README §3. Print `fit_coupon.stl` first.

Skip:
- `clip_tube_viewslots.stl` (only if the filament is opaque)
- `follower_springA.stl`
- `ring_hook.stl` (placeholder)
- `stl/assemblies/`
- `step/`

The `slicer_helpers/` files are support enforcers, not prints. Hardware (springs, Ø2 pins, M2 screws) is bought; see README §4.

## 6. Open decision for the team
Prototype the flat-rail fix now, or wait for the bench test result? Waiting for the test is recommended.
