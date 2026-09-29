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
        "clip_tube": (clip_tube(False), "bottom_down", "PETG (translucent)",
                      "-Z face down; roof bridges 20.5. If roof sags > 0.2 see README."),
        "clip_tube_viewslots": (clip_tube(True), "bottom_down", "PETG (opaque)",
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
        "paddle_pad": (paddle_pad(), "bottom_down", "TPU 95A", "dome up; channel roof bridges 16.4"),
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


def to_print(shape: cq.Shape, orient: str) -> cq.Shape:
    sh = shape
    for ax, deg in ORIENT[orient]:
        sh = sh.rotate(cq.Vector(0, 0, 0), cq.Vector(*AX[ax]), deg)
    bb = sh.BoundingBox()
    return sh.translate(cq.Vector(-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))


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
    meta.update(export_parts("B", suffix="_springB"))
    with open(f"{OUT}/stl/parts_meta.json", "w") as f:
        json.dump(meta, f, indent=1)
    export_states("A", "nom")
    export_states("B", "nom", states=("A", "Bp"))
    print("exported", len(meta), "parts")
