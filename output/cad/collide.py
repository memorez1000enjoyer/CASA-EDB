"""Exact B-rep interference (common volume) and minimum distance between bodies."""
import itertools
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib

# Pairs whose overlap is intended (press fits, self-tapping threads, clamped ribbon).
INTENDED = [
    ("dowel", "receiver_left", "Ø2 dowel pressed into Ø1.9 hole"),
    ("pin_pivot", "receiver_left", "Ø2 pivot pin pressed into Ø1.9 hole"),
    ("screw_clamp", "ribbon_clamp", "M2 self-tapper threads into Ø1.6 pilot"),
]


def intended(a, b):
    for x, y, why in INTENDED:
        if (a.startswith(x) and b.startswith(y)) or (b.startswith(x) and a.startswith(y)):
            return why
    return None


def bbox(shape, gap=0.0):
    bb = Bnd_Box()
    BRepBndLib.Add_s(shape.wrapped, bb, True)
    if gap:
        bb.Enlarge(gap)
    return bb


def common_volume(a, b) -> float:
    op = BRepAlgoAPI_Common(a.wrapped, b.wrapped)
    op.SetFuzzyValue(1e-6)
    op.Build()
    if not op.IsDone():
        return float("nan")
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(op.Shape(), props)
    return abs(props.Mass())


def min_distance(a, b) -> float:
    d = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped)
    d.Perform()
    return d.Value() if d.IsDone() else float("nan")


def check_bodies(bodies, pairs_filter=None, dist_pairs=None, near=1.0):
    """Returns (overlaps, distances).
    overlaps: list of (a, b, volume) for pairs with bbox contact.
    distances: {(a, b): d} for pairs in dist_pairs (names or prefixes)."""
    boxes = {bd.name: bbox(bd.shape, near / 2) for bd in bodies}
    overlaps, dists = [], {}
    for x, y in itertools.combinations(bodies, 2):
        if pairs_filter and not pairs_filter(x, y):
            continue
        if boxes[x.name].IsOut(boxes[y.name]):
            continue
        v = common_volume(x.shape, y.shape)
        overlaps.append((x.name, y.name, v))
        if dist_pairs is not None and dist_pairs(x, y):
            dists[(x.name, y.name)] = min_distance(x.shape, y.shape)
    return overlaps, dists
