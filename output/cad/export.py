"""Export every part as a print-ready STL (in its print orientation, on Z = 0,
centred on the origin) plus a STEP in the device frame, and the state assemblies."""
import os
import json
import cadquery as cq
import params as P
import assembly as A
from parts_clip import clip_tube, gate, end_cap
from parts_feed import follower, drum, drum_spacer, ribbon_clamp
from parts_receiver import receiver_left, receiver_right
from parts_mech import elevator, lever, plunger, paddle_pad
from parts_misc import ring_hook, bench_base, fit_coupon, bite

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
STL_TOL, STL_ANG = 0.01, 0.1

# rotation steps: list of (axis, degrees) applied about the origin, in order
ORIENT = {
    "bottom_down": [],
    "top_down": [("X", 180)],
    "plusX_down": [("Y", 90)],        # +X face on the bed
    "minusX_down": [("Y", -90)],
    "plusY_down": [("X", -90)],       # +Y face on the bed
    "minusY_down": [("X", 90)],
}
AX = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}


def _parts(spring_key):
    s = P.SPRINGS[spring_key]
    d = {
        # name: (shape, orientation, material, note)
        "clip_tube": (clip_tube(False), "plusX_down", "PETG (translucent)",
                      "standing on its back end (+X): the roof is a wall, no bridge to sag into the 0.3 follower clearance; brim"),
        "clip_tube_viewslots": (clip_tube(True), "plusX_down", "PETG (opaque)",
                                "Only if printing opaque: 9 short viewing windows in the +Y wall."),
        "gate": (gate(), "plusX_down", "PETG", "flat"),
        "end_cap": (end_cap(), "plusX_down", "PETG", "flat, outer face down"),
        "follower": (follower(s), "plusX_down", "PETG", "rear (+X) face down: pocket arch bridges 10.6"),
        "drum": (drum(), "plusY_down", "PETG", "on its end"),
        "ribbon_clamp": (ribbon_clamp(s), "top_down", "PETG", "flat, top face down, ridge up"),
        "receiver_left": (receiver_left(), "plusY_down", "PETG", "split face (Y=0) down"),
        "receiver_right": (receiver_right(), "minusY_down", "PETG", "split face (Y=0) down"),
        "elevator": (elevator(), "bottom_down", "PETG", "bottom down: notch roof bridges 6.6"),
        "lever": (lever(), "plusY_down", "PETG", "on its side: all holes vertical"),
        "plunger": (plunger(), "top_down", "PETG", "upside down (flange on the bed); support under the ear only"),
        "paddle_pad": (paddle_pad(), "minusY_down", "TPU 95A", "on its side: a pure extrusion, no overhangs or bridges"),
        "ring_hook": (ring_hook(), "minusX_down", "PETG", "on its end (J profile on the bed)"),
        "bench_base": (bench_base(), "bottom_down", "PETG/PLA", "flat"),
        "fit_coupon": (fit_coupon(), "bottom_down", "PETG", "flat - print this first"),
        "bite_nominal": (bite(P.BITES["nom"]), "plusX_down", "PETG/PLA", "print 8"),
        "bite_min": (bite(P.BITES["min"]), "plusX_down", "PETG/PLA", "print 8"),
        "bite_max": (bite(P.BITES["max"]), "plusX_down", "PETG/PLA", "print 8"),
    }
    sp = drum_spacer(s, +1)
    if sp is not None:
        d["drum_spacer"] = (sp, "plusY_down", "PETG", f"spring {spring_key} only - print 2")
    return d


def mesh_of(shape: cq.Shape, tol=STL_TOL, ang=STL_ANG):
    """Tessellate and clean (merge coincident vertices, drop zero-area sphere-pole
    triangles) so every STL is a closed, consistently wound mesh."""
    import numpy as np
    import trimesh
    vs, fs = shape.tessellate(tol, ang)
    m = trimesh.Trimesh(np.array([v.toTuple() for v in vs]), np.array(fs), process=True)
    m.update_faces(m.nondegenerate_faces(height=1e-9))
    m.remove_unreferenced_vertices()
    m.merge_vertices()
    trimesh.repair.fix_normals(m, multibody=True)
    return m


def write_stl(shape, path):
    mesh_of(shape).export(path)


def _rotate(sh, orient):
    for ax, deg in ORIENT[orient]:
        sh = sh.rotate(cq.Vector(0, 0, 0), cq.Vector(*AX[ax]), deg)
    return sh


def print_offset(shape: cq.Shape, orient: str) -> cq.Vector:
    bb = _rotate(shape, orient).BoundingBox()
    return cq.Vector(-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin)


def to_print(shape: cq.Shape, orient: str, offset: cq.Vector = None) -> cq.Shape:
    """Rotate into the print orientation and drop onto the bed centred on the origin.
    Pass `offset` to place a helper body (support enforcer) exactly like its part."""
    off = offset if offset is not None else print_offset(shape, orient)
    return _rotate(shape, orient).translate(off)


def support_enforcers():
    """Support-enforcer volumes for the receiver halves, in the same print frame as
    their STLs.  Load each as a 'support enforcer' modifier in the slicer and set
    supports to 'enforcers only' so nothing else (pin holes, sliding bridges) gets support."""
    from geom import box
    hw = P.SOCKET_IN_HW
    out = {}
    for name, side in (("receiver_left", -1), ("receiver_right", +1)):
        part = (receiver_left() if side < 0 else receiver_right()).val()
        orient = "plusY_down" if side < 0 else "minusY_down"
        off = print_offset(part, orient)
        # socket cavity, 0.2 inside every wall so the enforcer only reaches the roof
        vols = [box(0.2, P.SOCKET_L - 0.2, 0, side * (hw - 0.05), P.SOCKET_IN_Z0 + 0.2, P.SOCKET_IN_Z1 - 0.2)]
        if side > 0:   # under the roof strip beside the gate-tab channel
            vols.append(box(P.GATE_SLOT_X0 + 0.2, P.SOCKET_L - 0.2, 0, P.TAB_CHANNEL_Y[1] - 0.05,
                            P.SOCKET_IN_Z1 - 0.2, P.SOCKET_OUT_Z1 - 0.05))
        # bite-channel side wall next to the stop face (27 mm bridge) - optional
        vols.append(box(P.STOP_X + 5.0, -0.2, 0, side * (P.BORE_W / 2 - 0.05), P.RAIL_TOP_Z + 0.2, P.BORE_TOP_Z - 0.2))
        w = vols[0]
        for v in vols[1:]:
            w = w.union(v)
        out[name] = to_print(w.val(), orient, off)
    return out


def export_parts(spring_key="A", suffix=""):
    os.makedirs(f"{OUT}/stl", exist_ok=True)
    os.makedirs(f"{OUT}/step/parts", exist_ok=True)
    meta = {}
    for name, (w, orient, mat, note) in _parts(spring_key).items():
        if suffix and name not in ("follower", "drum_spacer"):
            continue  # only spring-dependent parts differ between configs
        shp = w.val() if isinstance(w, cq.Workplane) else w
        if len(w.vals()) > 1:
            shp = cq.Compound.makeCompound(w.vals())
        pr = to_print(shp, orient)
        fn = f"{name}{suffix}"
        if pr.BoundingBox().zmin < -1e-6:
            raise RuntimeError(f"{fn} is below the bed")
        write_stl(pr, f"{OUT}/stl/{fn}.stl")
        cq.exporters.export(shp, f"{OUT}/step/parts/{fn}.step")
        bb = pr.BoundingBox()
        meta[fn] = dict(orientation=orient, material=mat, note=note, volume_mm3=round(shp.Volume(), 1),
                        print_bbox=[round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)])
    return meta


def export_states(spring_key="A", bites="nom", states=("A", "B", "Bp", "C", "D", "Dt", "E")):
    import trimesh
    import numpy as np
    os.makedirs(f"{OUT}/step/assemblies", exist_ok=True)
    os.makedirs(f"{OUT}/stl/assemblies", exist_ok=True)
    label = {"Bp": "Bprime", "Dt": "D_taken"}
    for sn in states:
        st = A.build(sn, spring_key, bites)
        tag = f"state_{label.get(sn, sn)}_spring{spring_key}_{bites}"
        A.to_assembly(st).export(f"{OUT}/step/assemblies/{tag}.step")
        meshes = []
        for bd in st.bodies:
            vs, fs = bd.shape.tessellate(0.02, 0.2)
            m = trimesh.Trimesh(np.array([v.toTuple() for v in vs]), np.array(fs), process=False)
            m.visual.face_colors = [int(255 * c) for c in bd.color] + [255]
            meshes.append(m)
        trimesh.util.concatenate(meshes).export(f"{OUT}/stl/assemblies/{tag}.stl")


if __name__ == "__main__":
    import sys
    meta = export_parts("A")
    os.makedirs(f"{OUT}/stl/slicer_helpers", exist_ok=True)
    for n, sh in support_enforcers().items():
        write_stl(sh, f"{OUT}/stl/slicer_helpers/{n}_SUPPORT_ENFORCER.stl")
    meta.update(export_parts("B", suffix="_springB"))
    with open(f"{OUT}/stl/parts_meta.json", "w") as f:
        json.dump(meta, f, indent=1)
    export_states("A", "nom")
    export_states("B", "nom", states=("A", "Bp"))
    print("exported", len(meta), "parts")
