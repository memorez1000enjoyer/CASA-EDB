# OPEN ISSUES - EBD Clip v1

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

## 2. §9.8 overhang rule: the receiver halves and the plunger need support material (flagged)

The spec's print orientations can't be met without supports in three places. The model is otherwise
watertight with walls ≥ 0.8 (spec features excepted):

| Part | Where | Why |
|---|---|---|
| receiver_left / right | Inside the socket, under the socket side wall | Printed on the split face, the side wall is a 28 × 36.1 roof over the socket cavity. It is supported on 3 sides; the 4th is the open socket entry. The bridge would be **36.1 mm (limit 25)**, and sag there eats the 0.3 clip clearance. |
| receiver_right | Under the roof strip outside the gate-tab channel | A 1.75 × 26.8 strip, supported only at the front. |
| receiver_left / right | Bite-channel side wall next to the stop face | Between the bridge (Z 4.5) and the stripper strip (Z 31.5) is a **27 mm** bridge (limit 25), because the socket cavity starts at X = 0. |
| plunger | Under the spring ear (upside-down print) | The ear sticks out 8.3 from the body. No orientation of the spec'd plunger is support-free: the flange blocks side orientations and the ear blocks vertical ones. |

Printing the halves on their outer face instead removes every bridge, but then the latch tongue floats over
its 0.5 side cut, which is unprintable. So the split face stays.

**Recommended now:** load `stl/slicer_helpers/receiver_*_SUPPORT_ENFORCER.stl` as support-enforcer modifiers and set supports to *enforcers only*. The clip tube (now printed upright) also shows 6 mm² flagged at the mouth-lip bridge: it is a 22.5 mm bridge and needs no support. Supports should
appear only in the socket, the channel strip, and that one bite-channel wall. Clean them and file the
socket's inner side faces smooth, since the clip slides there with 0.3 clearance. For the plunger, use
"touching build plate" support under the ear.

**v2 option:** print the socket as its own part standing on its back end. Every socket wall is then
vertical, the tongue prints standing up, and it bolts to the stop face. This is a redesign, so it's the
team's call.

## 3. §6.6 "orthodontic-elastic" hook posts: omitted

The ear moves inside the **enclosed** ear slot (X −50.2 → −41.5, Z −6.5 → 14.5), so an elastic from an
ear post has no path up to a post "at the receiver top near X −46". The receiver screw at (X −45.8, Z 24)
sits exactly where a channel would go. Spring B is paired with a lighter compression spring instead
(k 0.12 N/mm, about 1.0 N at rest). If the team wants the elastic option, move that screw and cut a Ø3
channel from the ear slot to the top.

## 4. Mount layout (§6.7): ring hook and Velcro share the −Y face; ring-flange numbers are placeholders

The spec's ring-hook pilots (X −19 / −37, Z 20 / 26) sit inside the area the two 25 × 50 Velcro pads cover
(X −51 → −1). A 3.0-thick hook leg would hold the Velcro off the wall. For now, cut the pads round the
hook leg (X −41 → −15, Z ≥ 15), or use shorter pads (Z −20 → 14).

`RING_FLANGE_T = 4.0`, `RING_HOOK_REACH = 6.0` and `RING_HOOK_Z = 8.0` are still **placeholders**. Measure
the real flange in `HUT – Largest.stl` (NTRS 20260000671), set them in `params.py`, and rebuild.

## 5. Spring A is too stiff for the final design (as the spec predicted)

With the 1.48 lb spring the chin force is **4.9 → 7.8 N** (flagged > 6 N). An uneaten raised bite **does
not sink back**: 1.64 N of return force vs 3.30 N of sandwich friction. With spring B it is **1.7 → 3.4 N**
and the bite returns. Build and test both; plan on B (or about 0.3-0.5 lb).

## 6. Undocking a clip that still has bites in it

When the clip is pulled out, the stack follows the follower out of the mouth into the receiver. The gate
can't go back in while docked, because bite 2 fills the clip's gate slot. So **only undock an empty clip**
(state C/D). To remove a partly-used clip, take bites off the cup one at a time until it is empty. Test this
on the bench and decide whether v2 needs a second gate at the receiver side.

## 8. The last bite can be launched in lunar gravity (review finding, not fixed)

With a min-thickness last bite (states C/D) nothing clamps it against the front wall: 0.5 gap, and the follower sits on its stop. At the hard stop the elevator stops dead. At 1/6 g, a chin tuck of about 0.22 m/s is enough to throw the bite clear of the 15 mm retention (0.55 m/s at 1 g, so bench tests won't show it). The spec accepts the gap (§7 C). Suggested fixes: TPU cup lips on the window side walls, as the Gameplan proposed (about 0.3 N grip), or a flexure finger on the follower. A second concern: bite 2 may be dragged up by bite 1 in state B (about a 3 % friction margin); bench-test with min-height bites.

## 9. Paddle pad retention

The pad is located by rims over the flange ends and held with CA. A TPU snap bead was modelled but left sub-0.8 slivers, so it was removed. The pad is not held mechanically in Z. Check the glue joint after every wash, or design a clip-over pad in v2.

## 10. Crumb and saliva paths

After arming, the gate slot and the open socket-roof areas (a 36 mm² slot plus about 300 mm², more because of #1) lead onto bite 2 and the clip roof. The window stays open for the whole EVA. The 0.3 gaps round the elevator and plunger lead into the mechanism. Cleaning means taking the receiver apart. v2 options: a captive shutter over the gate slot, and a slit TPU membrane over the window (which would also help #8).

## 11. `PADDLE_X` reach range

A reach test moving the paddle **further** from the window (−46.2) passes every check. Moving it **closer** (−26.2) does not: the 25 mm pad overlaps the window and backstop lip, and a 9 mm lever has to swing ±52°. The practical limit toward the window is about **+7 mm** (`PADDLE_X` ≥ −29).

## 12. Clip in its socket

The one-sided latch and the ribbon clamp make a small yaw couple, so the clip can sit up to 0.3 off-centre and 0.3 low (bench gravity). The follower and bore lead-ins added in review handle this. Also:
- With the clip low, a min-width bite has a 0.8 step onto the bridge, which has a thin friction margin with spring B. Bench-test W-min bites.
- With the elevator at the +0.3 end of its play, the state-D push-rib gap is 0.5 (spec limit 0.8).

## 13. Review coverage

Four independent reviewers ran:
- printability/assembly and food-safety/FOD: completed
- kinematics: completed its analysis. It checked 1,500 poses with play in every combination and found 0 overlaps.
- geometry-vs-spec (number by number): cut off by a usage limit before it reported

A fresh second review round has not been run.

## 7. Margins worth knowing (not failures)

- **Pin slots:** with the elevator or plunger centred, the pins keep 0.24-0.40 from the slot ends over the
  whole stroke. At the extreme of their ±0.3 X play the margins drop to about 0.0-0.1. The plunger slot is
  −0.06 at −0.3: the pin just nudges the plunger 0.06 within its play, so there's no binding.
- **Last bite taken (state D):** the push ribs are 0.8 from the elevator rear face with the elevator
  centred, 0.5 if it sits at the back of its play.
- **Min-width bite 2** rests half on the bridge: it tilts about 2° (modelled as a 0.44 lift).
- **Roof sag (§8.1):** the follower clears the clip roof by 0.3. After printing, check the roof sag. If it
  is more than 0.2, split the roof into a snap-on lid.
- **Reach test:** see `VERIFICATION.md` / README "Changing PADDLE_X" for what moving `PADDLE_X` ±10 does.
