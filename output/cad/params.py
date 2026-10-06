"""
EBD "Clip" v1 -- every dimension in one place.

Source of truth: EBD_Build_Spec.md Rev B.  "§" numbers below refer to that spec.
Units: mm, degrees, N, g.

Coordinate frame (§2), shared by every part, defined with the clip docked:
  X = 0  clip mouth face = receiver socket stop face.  +X runs back into the clip.
         The cup, lever and paddle are at -X.
  Y = 0  mid-plane (everything is centred in Y).
  Z = 0  bottom of the ribbon groove in the clip floor.  +Z is up (toward the mouth).

Tags used in the comments:
  MUST     functional requirement from the spec - do not change without flagging
  DEFAULT  chosen value from the spec - change only if a §9 check fails (log in CHANGES.md)
  DERIVED  computed from other values here - never type it twice
  CHANGED  a DEFAULT that was changed; see CHANGES.md for old -> new -> reason
  ADDED    a value the spec left to the CAD agent; see ASSUMPTIONS in CHANGES.md

Students: the numbers you are expected to touch are CLR_SLIDE and the PIN_*_D holes (from fit_coupon),
the SPRINGS table (measure your real spring), BITES (Esther's food trials),
PADDLE_X (reach test) and the RING_* values (measure the HUT neck ring).
After any change run  `python build_all.py`  and read VERIFICATION.md.
"""
from dataclasses import dataclass
import math

# =============================================================================
# §8.2 Tolerance rules
# =============================================================================
CLR_SLIDE = 0.30        # PARAM DEFAULT  sliding clearance per side - set from fit_coupon
CLR_PRESS = 0.10        # spec §8.2 table value only - NOT used by the model; set the PIN_*_D holes below
PIN_D = 2.0             # Ø2 steel pins / music wire (§8.3)
# Pin holes are set ONE BY ONE from the fit coupon's pin-hole row (README §2): a printer that
# prints holes small needs every one of them larger, which no single clearance can express.
PIN_PRESS_D = 1.9       # DEFAULT (§8.2) the coupon hole a Ø2 rod presses into and stays
PIN_SNUG_D = 2.1        # DEFAULT (§8.2) the coupon hole a rod pushes into snugly
PIN_FREE_D = 2.3        # DEFAULT (§8.2) the coupon hole a rod turns loosely in
PIN_RUN_D = 2.1         # ADDED running fit: the smallest coupon hole a rod spins freely in without wobble
                        # (lever pivot; ream after printing)
MIN_WALL = 1.2          # DEFAULT  minimum structural wall
MIN_WALL_ABS = 0.8      # MUST     absolute minimum wall
MIN_HOLE_D = 1.6        # DEFAULT  smallest printed hole
EDGE_CHAMFER = 0.5      # DEFAULT  chamfer on bite/face-touchable edges (0.3-0.5)
SMALL_CHAMFER = 0.3
PTFE_T = 0.08           # PTFE tape thickness (clearances already allow for it; not modelled)

# =============================================================================
# §3 Bite envelope (design envelope, not a printed part - dummies are §8.4)
# =============================================================================
BITE_T = 12.7           # PARAM  X  stacking thickness
BITE_W = 19.0           # PARAM  Y  width
BITE_H = 25.4           # PARAM  Z  height
BITE_R = 2.0            # PARAM  edge radius
BITE_T_TOL = 0.5        # MUST   ±0.5 on the stacking face
BITE_W_TOL = 1.0
BITE_H_TOL = 1.0
N_BITES = 8             # PARAM
BITE_MASS_G = 8.0       # §9.9 loaded-mass estimate


@dataclass(frozen=True)
class Bite:
    name: str
    T: float  # X
    W: float  # Y
    H: float  # Z
    R: float = BITE_R


BITES = {
    "min": Bite("min", BITE_T - BITE_T_TOL, BITE_W - BITE_W_TOL, BITE_H - BITE_H_TOL),
    "nom": Bite("nom", BITE_T, BITE_W, BITE_H),
    "max": Bite("max", BITE_T + BITE_T_TOL, BITE_W + BITE_W_TOL, BITE_H + BITE_H_TOL),
}

# =============================================================================
# §4 / §5.2 Clip tube
# =============================================================================
WALL = 2.0              # PARAM  wall / floor / roof
GROOVE_W = 16.0         # PARAM  ribbon groove width  (Y ±8.0)
GROOVE_D = 2.0          # PARAM  ribbon groove depth  (Z 0 -> 2.0)
BORE_W = 20.5           # PARAM  bore width           (Y ±10.25)
BORE_TOP_Z = 31.5       # PARAM
BORE_BOT_Z = GROOVE_D   # DERIVED 2.0
RAIL_TOP_Z = 4.5        # PARAM
RAIL_IN_Y = GROOVE_W / 2    # DERIVED 8.0  rail inner face
RAIL_OUT_Y = BORE_W / 2  # CHANGED 9.75 -> 10.25: rails run to the wall (the 0.5 x 2.5 crevices were crumb traps)
RAIL_EDGE_R = 0.5       # DEFAULT R0.5 top edges
RAIL_FRONT_CHAMFER = 0.5
CLIP_L = 140.8          # PARAM
GROOVE_X0 = 2.0         # DEFAULT solid floor X 0 -> 2.0 at the mouth
TOP_Z = BORE_TOP_Z + WALL          # DERIVED 33.5  clip roof top = receiver top surface (PARAM TOP_Z)
CLIP_BOT_Z = -WALL                 # DERIVED -2.0
CLIP_HW = BORE_W / 2 + WALL        # DERIVED 12.25 half width
MOUTH_CHAMFER = 0.5     # DEFAULT outside chamfer at the mouth (never on the bore edge)
TUBE_EDGE_CHAMFER = 0.5 # ADDED   other outer tube edges

GATE_SLOT_X0 = 1.2      # DEFAULT
GATE_SLOT_X1 = 2.8      # DEFAULT
GATE_SLOT_WALL_CUT = 1.0                      # DEFAULT depth into each side wall
GATE_SLOT_HW = BORE_W / 2 + GATE_SLOT_WALL_CUT  # DERIVED 11.25

CLAMP_SCREW_X = 5.0     # DEFAULT
CLAMP_SCREW_Y = 6.0     # DEFAULT (±)
M2_CLEAR_D = 2.3        # DEFAULT (§5.2) M2 clearance - its own value, NOT tied to the pin fits or CLR_SLIDE
                        # (if an M2 threads into it, ream to 2.4 or raise this)
M2_CSK_HEAD_D = 3.8     # M2 countersunk head (DIN 965)
M2_CSK_CUT_D = 4.0      # ADDED countersink cut Ø (head recessed ~0.1)
CLAMP_NOTCH_X = 3.5     # DEFAULT centre
CLAMP_NOTCH_W = 0.8     # DEFAULT (X)
CLAMP_NOTCH_D = 0.3     # DEFAULT

LATCH_NOTCH_X0 = 12.0   # DEFAULT vertical catch face
LATCH_NOTCH_X1 = 16.0   # DEFAULT ramp meets roof top
LATCH_NOTCH_W = 8.6     # DEFAULT (Y ±4.3)
LATCH_NOTCH_D = 1.0     # DEFAULT (leaves a 1.0 roof)
LATCH_RAMP_DEG = 30.0   # DEFAULT

ENDCAP_L = 4.0          # DEFAULT plug length
ENDCAP_CLR = 0.2        # DEFAULT per side
ENDCAP_X0 = CLIP_L - ENDCAP_L                  # DERIVED 136.8 inner face
ENDCAP_SCREW_X = CLIP_L - ENDCAP_L / 2         # DERIVED 138.8
ENDCAP_SCREW_Z = (BORE_BOT_Z + BORE_TOP_Z) / 2  # DERIVED 16.75
ENDCAP_PILOT_DEPTH = 5.0                       # ADDED (M2 x 6 through a 2.0 wall)

# Optional viewing windows for an opaque tube (§5.2). CHANGED from one 113-long slot
# to short windows so every window top is a <=10 mm bridge (see CHANGES.md).
VIEW_SLOT = False       # set True if you print the tube in opaque filament
VIEW_Z0, VIEW_Z1 = 16.0, 20.0
VIEW_X0, VIEW_X1 = 12.0, 125.0
VIEW_WIN_L = 10.0       # CHANGED (was one continuous slot)
VIEW_WEB = 2.55         # CHANGED

# =============================================================================
# §5.1 Constant-force springs (purchased).  Only these rows change between configs.
# =============================================================================
@dataclass(frozen=True)
class Spring:
    name: str
    F: float        # SPRING_F  N
    W: float        # SPRING_W  ribbon width
    T: float        # SPRING_T  ribbon thickness
    L: float        # SPRING_L  total ribbon length
    max_ext: float  # rated extension
    # return (compression) spring paired with this config (§6.6)
    rs_k: float     # N/mm
    rs_free: float  # free length


SPRINGS = {
    # A: 1.48 lb, 0.38" wide, 0.0059" thick, 20.98" total, 17.99" extended
    "A": Spring("A", F=6.6, W=9.65, T=0.15, L=533.0, max_ext=457.0, rs_k=0.20, rs_free=35.0),
    # B: 0.33 lb, 0.25" wide, 0.0039" thick, 15" total, 12" extended (Amazon B0DL4KCGVB) - FINAL spring.
    # CHANGED (v1.1) return spring k 0.12 -> 0.13, free 35 -> 38: with real pin play the rest
    # installed length is 27.0, and free 35 at 0.12 left only ~1.0 N for sticky food.
    "B": Spring("B", F=1.47, W=6.35, T=0.10, L=381.0, max_ext=305.0, rs_k=0.13, rs_free=38.0),
}
DEFAULT_SPRING = "B"    # CHANGED (v1.1) A -> B: the team bought B (final). A = optional high-force tests

# convenience names for the default config (spec PARAM names)
SPRING_F = SPRINGS[DEFAULT_SPRING].F
SPRING_W = SPRINGS[DEFAULT_SPRING].W
SPRING_T = SPRINGS[DEFAULT_SPRING].T
SPRING_L = SPRINGS[DEFAULT_SPRING].L

# =============================================================================
# §5.4 Drum
# =============================================================================
DRUM_D = 12.5           # DEFAULT
DRUM_L = 9.4            # DEFAULT (Y)
DRUM_BORE_D = PIN_FREE_D  # 2.3 free on the axle
DRUM_CHAMFER = 0.3
# spacer rings for a narrow ribbon (see CHANGES.md: spec said "Ø10 x 1.5 washers",
# which cannot fit - they are rings that slip over the drum instead)
SPACER_ID_CLR = 0.25    # CHANGED (v1.1) 0.15 -> 0.25 radial clearance on the drum (small vertical hole: prints undersize)
SPACER_OD_OVER_COIL = 0.3  # ADDED spacer OD = max coil OD + this
SPACER_AXIAL_CLR = 0.05    # ADDED gap to the ribbon edge


def coil_od(spring: Spring, extension: float = 0.0) -> float:
    """Coil OD wound on the drum: sqrt(D^2 + 4*L_wound*T/pi)  (§5.1)."""
    wound = max(spring.L - extension, 0.0)
    return math.sqrt(DRUM_D ** 2 + 4.0 * wound * spring.T / math.pi)


# =============================================================================
# §5.3 Follower  (all X values relative to F = push-rib crest plane)
# =============================================================================
FOLLOWER_L = 28.0                       # DEFAULT
FOLLOWER_HW = BORE_W / 2 - CLR_SLIDE    # DERIVED 9.95
FOLLOWER_TOP_Z = BORE_TOP_Z - CLR_SLIDE  # DERIVED 31.2
FOLLOWER_BOT_Z = RAIL_TOP_Z             # DERIVED 4.5 (rides on the rail tops)
PUSH_RIB_D = 0.6        # DEFAULT rib depth (face recessed to F+0.6)
PUSH_RIB_H = 0.5        # DEFAULT
PUSH_RIB_Z = (10.0, 24.0)  # DEFAULT centres
KEEL_X0 = 9.6           # DEFAULT
KEEL_GROOVE_CLR = 0.8   # DEFAULT
KEEL_HW = GROOVE_W / 2 - KEEL_GROOVE_CLR  # DERIVED 7.2
KEEL_BOT_Z = 0.3        # DEFAULT
POCKET_CX = 18.0        # DEFAULT (rel F)
POCKET_CZ = 8.85        # DEFAULT
POCKET_HW = 5.3         # DEFAULT (also the open-bottom slot half width)
POCKET_CLR = 1.0        # DEFAULT pocket Ø = coil OD + 1.0
FOLLOWER_CHAMFER = 0.5  # DEFAULT top edges
AXLE_HOLE_D = PIN_SNUG_D  # 2.1
AXLE_L = 2 * FOLLOWER_HW  # DERIVED 19.9 (ends flush with the body sides)


def pocket_d(spring: Spring) -> float:
    return coil_od(spring, 0.0) + POCKET_CLR   # DERIVED A 17.06, B 15.31


# CHANGED: the pocket keeps a fixed BOTTOM height for every spring, so a smaller coil
# sits lower (with the centre fixed at Z 8.85 the spring-B ribbon tangent rose to
# Z 2.08; §9.5 requires < 2.0).  CHANGED (v1.1) 0.318 (derived from the spring-A coil
# through DRUM_D, so a bigger drum pushed the pocket below the groove floor) -> 0.3
# constant: pocket centre Z = pocket radius + 0.3 (spec Rev B.2).
POCKET_BOT_Z = 0.3
POCKET_REAR_WALL_MIN = MIN_WALL   # rear wall = F + 28.0 - pocket rear edge (§5.3)


def pocket_cz(spring: Spring) -> float:
    return POCKET_BOT_Z + pocket_d(spring) / 2   # DERIVED A 8.83, B 7.96


def pocket_rear_wall(spring: Spring) -> float:
    return FOLLOWER_L - (POCKET_CX + pocket_d(spring) / 2)   # DERIVED A 1.47, B 2.35


for _s in SPRINGS.values():
    assert pocket_rear_wall(_s) >= POCKET_REAR_WALL_MIN - 1e-9, \
        f"spring {_s.name}: follower rear wall {pocket_rear_wall(_s):.2f} < {POCKET_REAR_WALL_MIN} (drum/coil too big)"


# =============================================================================
# §5.5 Ribbon clamp
# =============================================================================
CLAMP_X0 = GROOVE_X0    # DERIVED 2.0
CLAMP_X1 = 8.0          # DEFAULT back edge = follower stop face
CLAMP_HW = GROOVE_W / 2 - CLR_SLIDE  # DERIVED 7.7
CLAMP_T = 1.2           # DEFAULT
CLAMP_RIDGE_H = CLAMP_NOTCH_D   # DERIVED 0.3
CLAMP_RIDGE_W = 0.4     # ADDED one line width; leaves 0.2 each side of the 0.8 notch for the ribbon
CLAMP_PILOT_D = MIN_HOLE_D  # 1.6
F_STOP = CLAMP_X1 - KEEL_X0    # DERIVED -1.6 empty stop (keel legs hit the clamp)

# =============================================================================
# §5.6 Gate
# =============================================================================
GATE_T = 1.2
GATE_HW = GATE_SLOT_HW - 0.2   # DERIVED 11.05 (spec 22.1 wide)
GATE_TAB_Y0, GATE_TAB_Y1 = 6.5, 10.5   # DEFAULT
GATE_TAB_TOP_Z = 42.0          # DEFAULT
GATE_TETHER_D = 2.0            # ADDED lanyard hole in the tab (the gate is loose once armed)
STACK_X0_UNDOCKED = GATE_SLOT_X0 + GATE_T  # DERIVED 2.4 (stack starts here, gate in)

# =============================================================================
# §6.3 Elevator / cup and the bite path in the receiver (§6.1)
# =============================================================================
STOP_X = -14.3          # DEFAULT front-wall stop face (inner face of the front wall)
BRIDGE_X0 = -2.1        # DEFAULT bridge -X face = elevator channel rear face
ELEV_X0 = STOP_X + CLR_SLIDE      # DERIVED -14.0
ELEV_X1 = BRIDGE_X0 - CLR_SLIDE   # DERIVED -2.4
ELEV_CX = (ELEV_X0 + ELEV_X1) / 2  # DERIVED -8.2
ELEV_HW = BORE_W / 2 - CLR_SLIDE  # DERIVED 9.95
# CHANGED (v1.1, Rev C) bridge top = cup rest top 4.5 -> 3.7, below the lowest bite seat on the
# rails (min-width bite 4.0, 3.9 with the clip resting on its socket floor): every bite steps
# DOWN into the receiver.  Climbing the old 0.6 x 45° lead-in self-locks once bite-to-bite
# friction reaches ~0.43, however hard the spring pushes.  §9.11 checks the step.
CUP_TOP_Z = 3.7         # PARAM
LEDGE_Z = RAIL_TOP_Z - 20.0       # DERIVED -15.5, unchanged from v1 (spec: 20.0 elevator on a 4.5 cup)
ELEV_H = CUP_TOP_Z - LEDGE_Z      # CHANGED (v1.1) 20.0 -> 19.2: ledge, pivot, lever, plunger stay put
ELEV_REAR_CHAMFER = 0.5
ELEV_FRONT_CHAMFER = 0.3
ELEV_SIDE_CHAMFER = 0.3  # ADDED (bite-touchable)
LEVER_NOTCH_HW = 3.3    # DEFAULT (elevator and plunger)
LEVER_NOTCH_H = 9.0     # DEFAULT
ELEV_NOTCH_X1 = -5.0    # DEFAULT
SLOT_H = 2.3            # DEFAULT pin slots, horizontal
SLOT_Z = 3.0            # DEFAULT slot centre above the part bottom
ELEV_SLOT_X_SPEC = (-11.5, -6.8)   # DEFAULT
CUP_PIN_L = 19.4        # DEFAULT (ends at ±9.7)

# =============================================================================
# §4 / §6.4 Lever and paddle
# =============================================================================
LIFT = 14.0             # PARAM nominal lift (model 14.1; ≈13.9 real after pin-hole play - see HOLE_LOST_MOTION)
PADDLE_X = -36.2        # PARAM plunger / paddle centre (reach test may move it ±10)
PADDLE_STROKE = 14.7    # CHANGED 14.3 -> 14.7: pin-hole play (pivot + end holes) costs 0.2 of lift; keeps lift >= 13.5
LEVER_R = (ELEV_CX - PADDLE_X) / 2     # DERIVED 14.0
PIVOT_X = (ELEV_CX + PADDLE_X) / 2     # DERIVED -22.2
PIVOT_Z = LEDGE_Z + SLOT_Z + LIFT / 2  # DERIVED -5.5
LEVER_SWING = math.degrees(math.asin((LIFT / 2) / LEVER_R))  # DERIVED 30.0 (nominal)
LEVER_T = 6.0           # DEFAULT (Y ±3.0)
LEVER_H = 5.0           # DEFAULT (ends full round R2.5)
LEVER_PIVOT_HOLE_D = PIN_RUN_D    # CHANGED 2.3 -> 2.1 running fit: pivot play counts double on a 1:1 lever
# CHANGED: the pivot pin is PRESSED into receiver_left (Ø1.9, like a dowel) and snug in
# receiver_right (Ø2.1), so the pin itself cannot float in the receiver.
RCV_PIVOT_HOLE_L = PIN_PRESS_D
RCV_PIVOT_HOLE_R = PIN_SNUG_D
LEVER_END_HOLE_D = PIN_SNUG_D     # 2.1
PIVOT_PIN_L = 26.0      # DEFAULT
PLUNGER_PIN_L = 11.4    # DEFAULT
PIN_SLOT_PLAY = (SLOT_H - PIN_D) / 2   # DERIVED 0.15
# Horizontal pin wander over the full swing (slot play included).  The slots below
# keep the spec's numbers at the default PADDLE_X and grow automatically if a
# reach-test PADDLE_X (and so LEVER_R) needs more room: pin radius + 0.2 margin.
SLOT_END_MARGIN = PIN_D / 2 + 0.2
_PHI_MAX = math.asin(min((LIFT / 2 + PIN_SLOT_PLAY) / LEVER_R, 1.0))
PIN_WANDER = LEVER_R * (1 - math.cos(_PHI_MAX))            # DERIVED 1.96
ELEV_SLOT_X = (min(ELEV_SLOT_X_SPEC[0], ELEV_CX - PIN_WANDER - SLOT_END_MARGIN),
               max(ELEV_SLOT_X_SPEC[1], ELEV_CX + SLOT_END_MARGIN))           # DERIVED (-11.5, -6.8)

# =============================================================================
# §6.5 Plunger + paddle pad
# =============================================================================
PLUNGER_LX = 10.0       # DEFAULT (X)
PLUNGER_LY = 12.0       # DEFAULT (Y)
FLANGE_LX = 16.0        # DEFAULT
FLANGE_LY = 18.0        # DEFAULT
FLANGE_T = 2.0          # DEFAULT
FLANGE_UNDERSIDE_REST_Z = TOP_Z + PADDLE_STROKE  # DERIVED 48.2 (spec 47.8 with stroke 14.3; 48.4 with hole play)
PLUNGER_SLOT_DX_SPEC = (-1.3, 3.2)   # DEFAULT rel PADDLE_X  (X -37.5 -> -33.0)
PLUNGER_SLOT_DX = (min(PLUNGER_SLOT_DX_SPEC[0], -SLOT_END_MARGIN),
                   max(PLUNGER_SLOT_DX_SPEC[1], PIN_WANDER + SLOT_END_MARGIN))  # DERIVED (-1.3, 3.2)
EAR_H = 5.0             # DEFAULT
EAR_UNDERSIDE = 10.0    # DEFAULT above the plunger bottom
EAR_X_END = PADDLE_X - 13.3     # DEFAULT -49.5
SPIGOT_D = 3.0
SPIGOT_L = 3.0
SPRING_WELL_X = PADDLE_X - 10.3  # DEFAULT -46.5
PAD_LX, PAD_LY, PAD_T = 25.0, 18.0, 3.0   # DEFAULT (TPU 95A)
PAD_DOME = 1.0          # DEFAULT
PAD_RIM_CLR = 0.2       # ADDED gap between the rim and the flange ends
PAD_CORNER_C = 1.0      # ADDED 45° plan-corner chamfers (pad prints on its side)
PAD_RIM_H = 1.2         # CHANGED 1.0 -> 1.2: rims locate the pad on the flange ends; 0.8 above the
                        # receiver top at the hard stop so a deflected pad never lands first
PAD_SNAP = (1.2, 0.0, 0.0)   # ADDED bead centre below the flange top, height, depth (TPU snaps on/off for washing)

# =============================================================================
# §6.6 Return spring (purchased) - geometry for the model
# =============================================================================
RS_OD = 6.0             # 5.5-6.5 (ID >= 3.4 to fit over the Ø3 spigot)
RS_OD_RANGE = (5.5, 6.5)
RS_WIRE = 0.40          # CHANGED (v1.1) 0.6 -> 0.40 (0.45 max): 0.5-0.6 wire goes solid before the stroke ends
RS_WIRE_MAX = 0.45
RS_K_RANGE = (0.12, 0.15)  # N/mm, buyable range for spring B (Rev C)
RS_FREE_RANGE = (37.0, 40.0)  # mm, buyable free length for spring B (Rev C)
RS_G = 79300.0          # N/mm^2 shear modulus, music wire (302 SS ~69000 gives fewer coils: shorter solid)
RS_DEAD_COILS = 3       # closed, not ground: solid = (n_active + 3) d  (ground ends: + 2)
RS_SOLID_MAX = 10.0     # MUST not go solid above 10 (pressed installed length is 12.1)
RS_WELL_D = 6.8         # DEFAULT


def rs_solid_length(k: float, wire: float = RS_WIRE, od: float = RS_OD, g: float = RS_G) -> float:
    """Solid length of a compression spring of rate k: n_active = G d^4 / (8 D^3 k)."""
    D = od - wire
    n = g * wire ** 4 / (8 * D ** 3 * k)
    return (n + RS_DEAD_COILS) * wire

# =============================================================================
# §6.1 Receiver body
# =============================================================================
SOCKET_WALL = 2.0       # DEFAULT
RCV_HW = CLIP_HW + CLR_SLIDE + SOCKET_WALL   # DERIVED 14.55
RCV_X0 = PADDLE_X - 16.8  # DEFAULT -53.0
RCV_BOT_Z = -20.0       # DEFAULT
RCV_EDGE_CHAMFER = 0.5  # ADDED outer edges
BRIDGE_LEADIN = 0.2     # CHANGED (v1.1) 0.6 x 45° lead-in -> 0.2 edge break: the bridge is below every bite seat
BRIDGE_REAR_CHAMFER = 0.3  # DEFAULT -X top edge
RELIEF_X1 = -5.0        # DEFAULT lever-tip relief pocket in the ledge
RELIEF_HW = 3.6
RELIEF_Z0 = -17.0
FRONT_WALL_T = 2.0      # DEFAULT -> front wall X -16.3 -> -14.3
FRONT_WALL_X0 = STOP_X - FRONT_WALL_T  # DERIVED -16.3
LEVER_SLOT_HW = 3.5     # DEFAULT through the front wall
LEVER_SLOT_Z = (-14.0, 3.0)
LEVER_CHAMBER_X0 = PADDLE_X - 4.8   # DEFAULT -41.0
LEVER_CHAMBER_HW = 3.6
LEVER_CHAMBER_Z = (-16.0, 5.0)
PLUNGER_CH_HW_X = PLUNGER_LX / 2 + CLR_SLIDE   # DERIVED 5.3 (X -41.5 -> -30.9)
PLUNGER_CH_HW_Y = PLUNGER_LY / 2 + CLR_SLIDE   # DERIVED 6.3
PLUNGER_CH_Z0 = -16.5   # DEFAULT
EAR_SLOT_X0 = PADDLE_X - 14.0   # DEFAULT -50.2
EAR_SLOT_Z = (-6.5, 14.5)       # DEFAULT
SPRING_WELL_Z0 = -18.0          # DEFAULT (top = ear slot bottom)
STRIPPER_X = -0.8       # MUST (sharp, 0.2 chamfer max) window rear edge (its lower, bite-side edge)
# CHANGED: the 0.8-wide strip behind the window rises to the socket roof top (Z 35.8) and
# joins the socket front band - split at Y = 0 the flat 0.8 x 2.0 strip was two 10 mm
# cantilevers that snap at ~1.3 N (OPEN_ISSUES #8).
STRIPPER_WALL_TOP_Z = None  # set below = SOCKET_OUT_Z1
WINDOW_TOP_CHAMFER = 0.3  # ADDED on the window side edges only
BACKSTOP_H = 3.0        # DEFAULT raised lip Z 33.5 -> 36.5
BACKSTOP_HW = RCV_HW    # CHANGED ±10.25 -> full width: a dropped bite could slide round its ends
PIVOT_HOLE_SKIN = 1.0   # DEFAULT blind hole stops 1.0 short of each outer skin
RING_HOOK_PILOTS = [(-19.0, 20.0), (PADDLE_X - 0.8, 26.0)]   # DEFAULT (X, Z) on -Y face
RING_HOOK_PILOT_DEPTH = 7.0

# receiver screws along Y (§6.1: M2 x 16; changed to M2 x 20 socket head, see RCV_SCREW_L)
RCV_SCREWS = [
    ((PADDLE_X + PLUNGER_CH_HW_X + FRONT_WALL_X0) / 2, 12.0),  # -23.6 (midway channel/front wall)
    ((PADDLE_X + PLUNGER_CH_HW_X + FRONT_WALL_X0) / 2, 26.0),  # -23.6
    (PADDLE_X - 9.6, 24.0),                                     # -45.8
    (12.0, -7.2),                                               # through the socket lug
]
CBORE_D = 4.2           # DEFAULT head counterbore (+Y)
CBORE_DEPTH = 9.0       # CHANGED 6.6 -> 9.0: an M2 x 20 then reaches a nut lying anywhere in its trap
                        # (even at the trap mouth) and pulls it in; its tip stays 0.1 inside the -Y face
NUT_AF = 4.3            # CHANGED 4.1 -> 4.3: a printed 4.1 hex will not take a 4.0 AF nut by hand
NUT_TRAP_DEPTH = 6.6    # DEFAULT (screws are M2 x 20 - an M2 x 16 only reaches 0.1 into the nut)
RCV_SCREW_L = 20.0      # CHANGED BOM M2 x 16 -> M2 x 20
LUG_X = (8.0, 16.0)
LUG_Z0 = -10.5          # CHANGED -10.0 -> -10.5 (>= 0.8 wall round the counterbore; -10.0 left 0.7)
# dowels 3 x Ø2 x 10: ADDED positions (spec: "CAD agent places them")
DOWEL_L = 10.0
DOWEL_HOLE_DEPTH = 5.3  # each half -> 0.6 total axial play
DOWELS = [(-2.6, -17.75), ((PADDLE_X + PLUNGER_CH_HW_X + FRONT_WALL_X0) / 2, 19.0), (PADDLE_X - 9.8, 18.0)]
# (the middle dowel sits between the two X -23.6 screws and follows PADDLE_X)

# =============================================================================
# §6.2 Socket and latch (part of the receiver halves)
# =============================================================================
SOCKET_L = 28.0         # DEFAULT
SOCKET_IN_HW = CLIP_HW + CLR_SLIDE          # DERIVED 12.55
SOCKET_FLOOR_CLR = 0.10  # CHANGED (v1.1, Rev C) 0.30 -> 0.10: the clip always rests on the floor under
                         # gravity; latch engagement 0.4 -> 0.6, smaller bite step into the receiver
SOCKET_IN_Z0 = CLIP_BOT_Z - SOCKET_FLOOR_CLR  # DERIVED -2.1
SOCKET_IN_Z1 = TOP_Z + CLR_SLIDE            # DERIVED 33.8
SOCKET_OUT_Z0 = SOCKET_IN_Z0 - SOCKET_WALL  # DERIVED -4.1
SOCKET_OUT_Z1 = SOCKET_IN_Z1 + SOCKET_WALL  # DERIVED 35.8
SOCKET_ENTRY_CHAMFER = 0.5  # ADDED lead-in at X 28
TONGUE_HW = 4.0         # DEFAULT
TONGUE_T = 1.6          # DEFAULT (Z 33.8 -> 35.4)
TONGUE_CUT_W = 1.0      # CHANGED 0.5 -> 1.0: a 0.5 gap under a 13 mm bridge fuses when printed
TONGUE_X0 = 11.5        # DEFAULT tip
TONGUE_ROOT_X = 24.0    # DEFAULT
TONGUE_TIP_CUT = 1.0    # ADDED transverse cut that frees the tip (X 10.5 -> 11.5)
TOOTH_X0, TOOTH_X1 = 12.1, 15.7  # DEFAULT
TOOTH_H = 1.0           # DEFAULT (bottom Z 32.8)
TOOTH_RAMP_DEG = 30.0   # DEFAULT +X lead-in
LIFT_TAB = (11.5, 15.5, 4.0, 3.0)  # DEFAULT X0, X1, width Y, height
# CHANGED (OPEN_ISSUES #1): tongue, tooth and lift tab exist only in the -Y half.
# The +Y half of the roof centre is an island once the receiver is split at Y = 0.
LATCH_Y = (-TONGUE_HW, 0.0)
TAB_CHANNEL_Y = (6.2, 10.8)        # DEFAULT gate-tab channel (open at the back)
STRIPPER_WALL_TOP_Z = SOCKET_OUT_Z1
FLOOR_RELIEF = (3.0, 7.0, 8.2, 0.5)  # DEFAULT X0, X1, half width, depth

# =============================================================================
# §6.7 Mounting parts and bench base
# =============================================================================
RING_FLANGE_T = 4.0     # PARAM placeholder - measure HUT - Largest.stl
RING_HOOK_REACH = 6.0   # PARAM
RING_HOOK_Z = 8.0       # PARAM hook seat height above the top surface
RING_HOOK_T = 3.0       # DEFAULT
RING_HOOK_CLR = 0.3     # ADDED flange gap clearance per side
RING_HOOK_EDGE = 4.0          # ADDED pilot centre to bracket end (countersink r 2.0 + 2.0 wall)
RING_HOOK_X = (min(x for x, _ in RING_HOOK_PILOTS) - RING_HOOK_EDGE,
               max(x for x, _ in RING_HOOK_PILOTS) + RING_HOOK_EDGE)  # CHANGED width 20 -> 26 (-41 -> -15); follows PADDLE_X
RING_HOOK_Z0 = 15.0     # ADDED bottom of the screw leg
VELCRO_X = (-51.0, -1.0)  # DEFAULT two 25 x 50 pads
VELCRO_H = 50.0

# bench base (dimensioned by the CAD agent)
BASE_T = 4.0
BASE_CLR = 0.3
M3_CLEAR_D = 3.4
M3_NUT_AF = 5.6
M3_NUT_T = 2.6

# =============================================================================
# §8.2 fit coupon, §8.4 dummy bites
# =============================================================================
COUPON_CLEARANCES = (0.20, 0.25, 0.30, 0.35)
COUPON_PIN_HOLES = (1.9, 2.0, 2.1, 2.2, 2.3)
COUPON_SLIDER = 10.0

# =============================================================================
# §9 materials and friction
# =============================================================================
RHO_PETG = 1.27e-3      # g/mm^3
RHO_TPU = 1.21e-3
RHO_STEEL = 7.9e-3
MU_WALL = 0.1           # PTFE-taped wall
MU_BITE = 0.4           # bite on bite
MU_BITE_STICKY = 0.6    # sticky food (Rev C sink-back check, with SPRING_F_HI)
SPRING_F_LO = 0.13      # constant-force spring tolerance: -13 % (feed margin)
SPRING_F_HI = 0.10      # +10 % (sink-back check)
FEED_BITE_MASS_G = 10.0  # §9.10 feed margin: 8 x 10 g sticky bites
FEED_MU = 0.6           # bite on the rails (sticky)
FEED_MU_FOLLOWER = 0.4  # ADDED follower (PETG) on the PETG rail tops, dry
FEED_AXLE_MU = 0.3      # ADDED drum (PETG) turning on the steel axle: loss = mu * r_pin / r_coil of the spring force
G_EARTH, G_MOON = 9.81, 1.62

# =============================================================================
# Kinematics derived from the above (slot play taken up in the loaded direction)
# =============================================================================
# At rest the return spring pushes the plunger up, the lever pushes the elevator
# down onto its ledge: both pins sit on the lower slot faces.
_REST_CUP_PIN_Z = LEDGE_Z + SLOT_Z - PIN_SLOT_PLAY           # -12.65
PHI_REST = math.degrees(math.asin((_REST_CUP_PIN_Z - PIVOT_Z) / LEVER_R))  # -30.71
PLUNGER_REST_BOT_Z = (2 * PIVOT_Z - _REST_CUP_PIN_Z) - (SLOT_Z - PIN_SLOT_PLAY)  # -1.20 (pins at hole centres)
# CHANGED/derived: body length chosen so the flange underside sits at TOP_Z +
# PADDLE_STROKE at rest (spec 47.8) with the real rest position (-1.2, not -1.5).
FLANGE_OFFSET = FLANGE_UNDERSIDE_REST_Z - PLUNGER_REST_BOT_Z  # 49.4 with PADDLE_STROKE 14.7 (spec implied 49.3)
PLUNGER_PRESSED_BOT_Z = TOP_Z - FLANGE_OFFSET                 # -15.9 (channel floor -16.5)
_PRESS_PLUNGER_PIN_Z = PLUNGER_PRESSED_BOT_Z + SLOT_Z + PIN_SLOT_PLAY  # -12.75
PHI_PRESS = math.degrees(math.asin((PIVOT_Z - _PRESS_PLUNGER_PIN_Z) / LEVER_R))  # +31.19


def summary():
    rows = [
        ("LEVER_R", LEVER_R), ("PIVOT_X", PIVOT_X), ("PIVOT_Z", PIVOT_Z),
        ("LEVER_SWING nominal", LEVER_SWING), ("PHI_REST", PHI_REST), ("PHI_PRESS", PHI_PRESS),
        ("PLUNGER_REST_BOT_Z", PLUNGER_REST_BOT_Z), ("FLANGE_OFFSET", FLANGE_OFFSET),
        ("F_STOP", F_STOP), ("pocket_d A", pocket_d(SPRINGS["A"])), ("pocket_d B", pocket_d(SPRINGS["B"])),
        ("coil_od A", coil_od(SPRINGS["A"])), ("coil_od B", coil_od(SPRINGS["B"])),
    ]
    for k, v in rows:
        print(f"{k:24s} {v:9.3f}")


if __name__ == "__main__":
    summary()

# Round-hole clearances that the kinematic model (pins at hole centres) leaves out.
# Under load each hole sits off its pin by its RADIAL clearance, on the side the load
# pushes.  Pressed: both lever ends are loaded down, so the lever hangs on the pivot
# (lower by the lever-hole + receiver-hole clearance, which counts twice at the cup end
# of a 1:1 lever) and each end hole sits above its pin.  At rest everything reverses.
# The rest pose is fixed by the elevator ledge and the pressed pose by the flange hard
# stop, so the clearances take this much off the LIFT and add the same to the STROKE:
_RCV_PIVOT_RADIAL = 0.0   # pin pressed into receiver_left - it cannot move in the receiver
HOLE_LOST_MOTION = (2 * ((LEVER_PIVOT_HOLE_D - PIN_D) / 2 + _RCV_PIVOT_RADIAL)
                    + 2 * (LEVER_END_HOLE_D - PIN_D) / 2)       # DERIVED 0.2
FOLLOWER_FRONT_CHAMFER = 0.6   # ADDED vertical front edges: the clip can float 0.3 in its socket
FOLLOWER_FRONT_RELIEF = (2.0, 0.7)  # ADDED underside raised 0.7 over the front 2.0: at F_STOP that part sits
                                    # over the receiver bridge, which it must not have to climb if the clip sits low
                                    # (0.4 left only 0.1 with the clip 0.3 low; push ribs start at Z 9.75)
BORE_LEADIN = 0.4              # ADDED on the receiver bore opening's vertical edges at X 0
