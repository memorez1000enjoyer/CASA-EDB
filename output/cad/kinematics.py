"""Kinematics of the lever / elevator / plunger and placement of the bite stack.

Lever angle phi (deg) = angle of the cup arm above horizontal (negative = cup end down).
Slot play (2.3 slots on Ø2 pins, 0.15 each way) is taken up in the loaded direction:
  'press'  - chin pushes the plunger down: plunger slot TOP face on its pin, the cup pin
             lifts the elevator by its slot TOP face (elevator stays on the ledge until then)
  'return' - return spring pushes the plunger up: plunger slot BOTTOM face on its pin,
             the cup pin pushes the elevator down by its slot BOTTOM face.
"""
import math
from dataclasses import dataclass
import numpy as np
import params as P


def lever_pins(phi):
    a = math.radians(phi)
    c, s = math.cos(a), math.sin(a)
    cup = (P.PIVOT_X + P.LEVER_R * c, P.PIVOT_Z + P.LEVER_R * s)
    plg = (P.PIVOT_X - P.LEVER_R * c, P.PIVOT_Z - P.LEVER_R * s)
    return cup, plg


@dataclass
class Mech:
    phi: float
    direction: str
    elev_bot: float      # elevator bottom Z
    elev_dx: float       # elevator X shift inside its 0.3 play (-0.3 = against the front wall)
    plunger_bot: float   # plunger bottom Z
    cup_pin: tuple
    plunger_pin: tuple

    @property
    def elev_top(self):
        return self.elev_bot + P.ELEV_H

    @property
    def elev_dz(self):
        return self.elev_bot - P.LEDGE_Z

    @property
    def lift(self):
        return self.elev_dz


_UP = P.SLOT_Z + P.PIN_SLOT_PLAY     # 3.15 pin on the slot's top face
_DN = P.SLOT_Z - P.PIN_SLOT_PLAY     # 2.85 pin on the slot's bottom face


def mech_at(phi, direction="press", elev_dx=0.0) -> Mech:
    cup, plg = lever_pins(phi)
    if direction == "press":
        pb = plg[1] - _UP
        eb = max(P.LEDGE_Z, cup[1] - _UP)
    elif direction == "return":
        pb = plg[1] - _DN
        top_bot = lever_pins(P.PHI_PRESS)[0][1] - _UP      # where the press left the elevator
        eb = max(P.LEDGE_Z, min(top_bot, cup[1] - _DN))
    else:
        raise ValueError(direction)
    return Mech(phi, direction, eb, elev_dx, pb, cup, plg)


def mech_rest() -> Mech:
    return mech_at(P.PHI_REST, "return")


def mech_pressed(elev_dx=0.0) -> Mech:
    return mech_at(P.PHI_PRESS, "press", elev_dx)


def with_hole_play():
    """Rest and pressed poses including the round-hole clearances (see params.HOLE_LOST_MOTION).
    Rule: a hole loaded by its pin in direction u sits at pin - (Rh - Rp)*u.
    Returns real plunger rest bottom, real stroke to the hard stop and real lift."""
    rp = (P.LEVER_PIVOT_HOLE_D - P.PIN_D) / 2
    rr = P._RCV_PIVOT_RADIAL
    re = (P.LEVER_END_HOLE_D - P.PIN_D) / 2
    # rest: ends loaded up, pivot loads the lever down (lever sits high on the pin)
    c = P.PIVOT_Z + rr + rp
    cup_pin = P.LEDGE_Z + _DN
    cup_end = cup_pin - re
    plg_end = 2 * c - cup_end
    plg_pin = plg_end + re
    rest_bot = plg_pin - _DN
    # pressed: plunger at the hard stop, ends loaded down, lever hangs on the pivot
    press_bot = P.PLUNGER_PRESSED_BOT_Z
    plg_pin = press_bot + _UP
    c = P.PIVOT_Z - rr - rp
    plg_end = plg_pin + re
    cup_end = 2 * c - plg_end
    cup_pin = cup_end - re
    elev_top = cup_pin - _UP + P.ELEV_H
    return dict(rest_bot=rest_bot, stroke=rest_bot - press_bot, lift=elev_top - P.CUP_TOP_Z, elev_top=elev_top,
                flange_rest=rest_bot + P.FLANGE_OFFSET)


def sweep(n=9, direction="press", elev_dx=0.0):
    """n lever angles from rest to the hard stop, endpoints included (n-2 intermediate)."""
    return [mech_at(float(a), direction, elev_dx) for a in np.linspace(P.PHI_REST, P.PHI_PRESS, n)]


# ----------------------------------------------------------------------------- bites
def rail_seat(W: float, dy: float = 0.0) -> float:
    """Bite bottom Z when its R2 side edges rest on the rails' R0.5 inner edges (§3).
    dy: the bite sits that far off the clip centre, kept upright (the higher side sets it)."""
    yc = W / 2 - P.BITE_R + abs(dy)
    ey, ez = P.RAIL_IN_Y + P.RAIL_EDGE_R, P.RAIL_TOP_Z - P.RAIL_EDGE_R
    if yc >= ey:
        return P.RAIL_TOP_Z
    R = P.BITE_R + P.RAIL_EDGE_R
    dy = ey - yc
    return ez + math.sqrt(R * R - dy * dy) - P.BITE_R


def _raise(d, R):
    """Height of a bite's rounded bottom edge above its flat bottom, d from the face."""
    d = np.clip(d, 0, R)
    return R - np.sqrt(np.maximum(R * R - (R - d) ** 2, 0))


def _bridge_top(x):
    """Top profile of the receiver bridge X -2.1 -> 0 (top CUP_TOP_Z, 0.3 rear chamfer,
    BRIDGE_LEADIN edge break at X 0); -inf outside."""
    x = np.asarray(x, float)
    top = np.full_like(x, -np.inf)
    rc, li = P.BRIDGE_REAR_CHAMFER, P.BRIDGE_LEADIN
    m = (x >= P.BRIDGE_X0) & (x <= 0)
    top[m] = P.CUP_TOP_Z
    m1 = m & (x < P.BRIDGE_X0 + rc)
    top[m1] = P.CUP_TOP_Z - rc + (x[m1] - P.BRIDGE_X0)
    m2 = m & (x > -li)
    top[m2] = P.CUP_TOP_Z - (x[m2] + li)
    return top


# Bites sit 0.1 µm above their support.  Exact fillet-on-fillet tangency (R2 bite edge
# on the R0.5 rail edge) crashes the OpenCascade boolean kernel; 1e-4 mm is far below
# any tolerance and still reports as "contact".
CONTACT_EPS = 1e-4


def bite_seat(b: P.Bite, x_front: float, docked=True, cup_top=None) -> float:
    """Bottom Z of an upright bite whose front face is at x_front.
    Supports: rails (X >= 0.5), receiver bridge, and the cup floor (elevator top) when
    cup_top is given.  Bites are kept upright and settle vertically onto the highest
    support under them (conservative: a rigid bite on the bridge + rails would tilt
    slightly instead)."""
    R = b.R
    x0, x1 = x_front, x_front + b.T
    req = -np.inf
    # rails under the flat part of the bottom
    if x1 - R > P.RAIL_FRONT_CHAMFER:
        req = max(req, rail_seat(b.W))
    xs = np.linspace(x0, x1, 400)
    raise_ = np.maximum(_raise(xs - x0, R), _raise(x1 - xs, R))
    if docked:
        req = max(req, float(np.max(_bridge_top(xs) - raise_)))
        if cup_top is not None:
            cm = (xs >= P.ELEV_X0) & (xs <= P.ELEV_X1)
            if cm.any():
                req = max(req, float(np.max(cup_top - raise_[cm])))
    return req + CONTACT_EPS


@dataclass
class BitePose:
    idx: int          # 1 = the one at the front
    x_front: float
    z_bot: float
    on_cup: bool = False


def stack(state: str, b: P.Bite, mech: Mech = None, n=P.N_BITES):
    """Bite poses and follower F for a §7 state.  Returns (list[BitePose], F)."""
    T = b.T
    if state in ("A", "B"):
        m = mech or (mech_rest() if state == "A" else mech_pressed())
        poses = [BitePose(1, P.STOP_X, m.elev_top, True)]
        for k in range(2, n + 1):
            xf = P.STOP_X + (k - 1) * T
            poses.append(BitePose(k, xf, bite_seat(b, xf, True)))
        F = P.STOP_X + n * T
    elif state == "Bp":
        m = mech or mech_pressed(-P.CLR_SLIDE)
        x2 = P.ELEV_X1 + m.elev_dx               # bite 2 held by the elevator rear face
        poses = []
        for k in range(2, n + 1):
            xf = x2 + (k - 2) * T
            poses.append(BitePose(k, xf, bite_seat(b, xf, True)))
        F = x2 + (n - 1) * T
    elif state in ("C", "D"):
        m = mech or (mech_rest() if state == "C" else mech_pressed())
        F = max(P.F_STOP, P.STOP_X + T)
        poses = [BitePose(n, F - T, m.elev_top, True)]
    elif state == "Dt":
        F = P.F_STOP
        poses = []
    elif state == "E":
        poses = []
        for k in range(1, n + 1):
            xf = P.STACK_X0_UNDOCKED + (k - 1) * T
            poses.append(BitePose(k, xf, bite_seat(b, xf, docked=False)))
        F = P.STACK_X0_UNDOCKED + n * T
    else:
        raise ValueError(state)
    return poses, F


def spring_extension(spring: P.Spring, F: float) -> float:
    """Free ribbon from the clamp back edge to the coil tangent (§9.6)."""
    from hardware import ribbon_geometry
    return ribbon_geometry(spring, F)["span"]


if __name__ == "__main__":
    r, p = mech_rest(), mech_pressed()
    print(f"rest    phi {r.phi:7.3f} elev top {r.elev_top:6.3f} plunger bot {r.plunger_bot:6.3f} "
          f"cup pin {r.cup_pin[0]:.3f},{r.cup_pin[1]:.3f}")
    print(f"pressed phi {p.phi:7.3f} elev top {p.elev_top:6.3f} plunger bot {p.plunger_bot:6.3f} "
          f"lift {p.lift:.3f} stroke {r.plunger_bot - p.plunger_bot:.3f}")
    for k, b in P.BITES.items():
        print(k, "rail seat", round(rail_seat(b.W), 3),
              "bite2 seat A", round(bite_seat(b, P.STOP_X + b.T), 3),
              "bite2 seat B'", round(bite_seat(b, P.ELEV_X1 - P.CLR_SLIDE), 3))
