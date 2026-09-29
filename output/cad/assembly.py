"""Build the §7 states as lists of placed bodies (all in the shared §2 frame)."""
from dataclasses import dataclass, field
from functools import lru_cache
import cadquery as cq
import params as P
import kinematics as K
import hardware as H
from parts_clip import clip_tube, gate, end_cap
from parts_feed import follower, drum, drum_spacer, ribbon_clamp
from parts_receiver import receiver_left, receiver_right
from parts_mech import elevator, lever, plunger, paddle_pad
from parts_misc import ring_hook, bite
from geom import rot_about_y

# colours (RGB 0-1) and materials for renders / mass
COLORS = {
    "receiver_left": (0.80, 0.33, 0.28), "receiver_right": (0.86, 0.45, 0.38),
    "clip_tube": (0.62, 0.78, 0.90), "end_cap": (0.35, 0.50, 0.70), "gate": (0.95, 0.70, 0.20),
    "follower": (0.30, 0.55, 0.35), "drum": (0.55, 0.55, 0.60), "drum_spacer": (0.45, 0.45, 0.50),
    "ribbon_clamp": (0.35, 0.35, 0.40), "cf_spring": (0.75, 0.75, 0.78),
    "elevator": (0.95, 0.80, 0.25), "lever": (0.25, 0.40, 0.75), "plunger": (0.55, 0.30, 0.65),
    "paddle_pad": (0.15, 0.15, 0.15), "return_spring": (0.75, 0.75, 0.78), "ring_hook": (0.60, 0.60, 0.55),
    "pin": (0.70, 0.70, 0.72), "screw": (0.40, 0.40, 0.42), "bite": (0.72, 0.48, 0.28),
}
MATERIAL = {"paddle_pad": "TPU", "cf_spring": "steel", "return_spring": "steel", "pin": "steel",
            "screw": "steel"}


@dataclass
class Body:
    name: str           # unique in the assembly, e.g. "bite3", "pin_cup"
    kind: str           # part / hardware kind (colour + material key)
    shape: cq.Shape
    moving: bool = False
    group: str = ""     # "clip" | "receiver" | "food"

    @property
    def color(self):
        return COLORS.get(self.kind, (0.7, 0.7, 0.7))


@dataclass
class State:
    name: str
    spring: str
    bites: str
    mech: K.Mech = None
    F: float = None
    bodies: list = field(default_factory=list)
    bite_poses: list = field(default_factory=list)
    note: str = ""

    def get(self, name):
        return next(b for b in self.bodies if b.name == name)


def _v(w):
    return w.val() if isinstance(w, cq.Workplane) else w


@lru_cache(None)
def _static(spring_key):
    s = P.SPRINGS[spring_key]
    d = dict(
        receiver_left=_v(receiver_left()), receiver_right=_v(receiver_right()),
        clip_tube=_v(clip_tube()), end_cap=_v(end_cap()), gate=_v(gate()),
        ribbon_clamp=_v(ribbon_clamp(s)), ring_hook=_v(ring_hook()),
        follower=_v(follower(s)), drum=_v(drum()),
        elevator=_v(elevator()), lever=_v(lever()), plunger=_v(plunger()), paddle_pad=_v(paddle_pad()),
        pin_pivot=_v(H.pin_y(P.PIVOT_X, P.PIVOT_Z, P.PIVOT_PIN_L)),
        screw_clamp_p=_v(H.clamp_screw(+P.CLAMP_SCREW_Y)), screw_clamp_n=_v(H.clamp_screw(-P.CLAMP_SCREW_Y)),
        axle=_v(H.pin_y(P.POCKET_CX, P.POCKET_CZ, P.AXLE_L)),
    )
    for i, (x, z) in enumerate(P.DOWELS):
        d[f"dowel{i + 1}"] = _v(H.dowel(x, z))
    sp = [drum_spacer(s, +1), drum_spacer(s, -1)]
    d["spacers"] = [_v(x) for x in sp if x is not None]
    return d


@lru_cache(None)
def _bite_shape(bkey):
    return _v(bite(P.BITES[bkey]))


def _mv(shape, dx=0.0, dy=0.0, dz=0.0):
    return shape.moved(cq.Location(cq.Vector(dx, dy, dz)))


def build(state: str, spring="A", bites="nom", mech: K.Mech = None, include_mount=True) -> State:
    """state in A, B, Bp (B'), C, D, Dt (D after the last bite is taken), E (undocked)."""
    s = P.SPRINGS[spring]
    st = _static(spring)
    b = P.BITES[bites]
    docked = state != "E"
    if docked and mech is None:
        mech = {"A": K.mech_rest(), "C": K.mech_rest(), "B": K.mech_pressed(), "D": K.mech_pressed(),
                "Dt": K.mech_pressed(), "Bp": K.mech_pressed(-P.CLR_SLIDE)}[state]
    poses, F = K.stack(state, b, mech)
    out = State(state, spring, bites, mech, F, bite_poses=poses)
    add = out.bodies.append

    # --- clip (cartridge)
    add(Body("clip_tube", "clip_tube", st["clip_tube"], group="clip"))
    add(Body("end_cap", "end_cap", st["end_cap"], group="clip"))
    add(Body("ribbon_clamp", "ribbon_clamp", st["ribbon_clamp"], group="clip"))
    add(Body("screw_clamp_p", "screw", st["screw_clamp_p"], group="clip"))
    add(Body("screw_clamp_n", "screw", st["screw_clamp_n"], group="clip"))
    if state == "E":
        add(Body("gate", "gate", st["gate"], group="clip"))
    add(Body("follower", "follower", _mv(st["follower"], F), True, "clip"))
    add(Body("drum", "drum", _mv(st["drum"], F), True, "clip"))
    add(Body("pin_axle", "pin", _mv(st["axle"], F), True, "clip"))
    for i, sp in enumerate(st["spacers"]):
        add(Body(f"drum_spacer{i + 1}", "drum_spacer", _mv(sp, F), True, "clip"))
    add(Body("cf_spring", "cf_spring", _v(H.cf_spring(s, F)), True, "clip"))

    # --- receiver (head)
    if docked:
        add(Body("receiver_left", "receiver_left", st["receiver_left"], group="receiver"))
        add(Body("receiver_right", "receiver_right", st["receiver_right"], group="receiver"))
        if include_mount:
            add(Body("ring_hook", "ring_hook", st["ring_hook"], group="receiver"))
        for i in range(len(P.DOWELS)):
            add(Body(f"dowel{i + 1}", "pin", st[f"dowel{i + 1}"], group="receiver"))
        add(Body("pin_pivot", "pin", st["pin_pivot"], group="receiver"))
        m = mech
        add(Body("elevator", "elevator", _mv(st["elevator"], m.elev_dx, 0, m.elev_dz), True, "receiver"))
        add(Body("lever", "lever", rot_about_y(st["lever"], P.PIVOT_X, P.PIVOT_Z, m.phi), True, "receiver"))
        add(Body("pin_cup", "pin", _v(H.pin_y(*m.cup_pin, P.CUP_PIN_L)), True, "receiver"))
        add(Body("pin_plunger", "pin", _v(H.pin_y(*m.plunger_pin, P.PLUNGER_PIN_L)), True, "receiver"))
        add(Body("plunger", "plunger", _mv(st["plunger"], 0, 0, m.plunger_bot), True, "receiver"))
        add(Body("paddle_pad", "paddle_pad", _mv(st["paddle_pad"], 0, 0, m.plunger_bot), True, "receiver"))
        add(Body("return_spring", "return_spring", _v(H.return_spring(m.plunger_bot)), True, "receiver"))

    # --- bites
    bs = _bite_shape(bites)
    for bp in poses:
        add(Body(f"bite{bp.idx}", "bite", _mv(bs, bp.x_front + b.T / 2, 0, bp.z_bot), True, "food"))
    return out


def to_assembly(st: State) -> cq.Assembly:
    a = cq.Assembly(name=f"EBD_state_{st.name}")
    for bd in st.bodies:
        a.add(bd.shape, name=bd.name, color=cq.Color(*bd.color))
    return a


if __name__ == "__main__":
    import time
    t = time.time()
    for sname in ("A", "B", "Bp", "C", "D", "Dt", "E"):
        st = build(sname, "A", "nom")
        print(sname, len(st.bodies), "F=%.2f" % st.F, [(p.idx, round(p.x_front, 2), round(p.z_bot, 3)) for p in st.bite_poses][:3])
    print("t", time.time() - t)
