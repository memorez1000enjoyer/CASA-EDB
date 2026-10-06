"""PNG renders: shaded views (VTK, off-screen) and exact Y = 0 sections (matplotlib).
Run under xvfb-run if there is no display:  xvfb-run -a python render.py"""
import os
import numpy as np
import vtk
from vtk.util import numpy_support as ns
import cadquery as cq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import params as P
import assembly as A
import kinematics as K

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "renders")
TRANSLUCENT = {"clip_tube": 0.30, "receiver_right": 1.0}


def _polydata(shape, tol=0.03):
    vs, fs = shape.tessellate(tol, 0.25)
    pts = np.array([v.toTuple() for v in vs], dtype=float)
    tri = np.array(fs, dtype=np.int64)
    p = vtk.vtkPoints()
    p.SetData(ns.numpy_to_vtk(pts, deep=True))
    cells = np.hstack([np.full((len(tri), 1), 3), tri]).ravel()
    ca = vtk.vtkCellArray()
    ca.SetCells(len(tri), ns.numpy_to_vtkIdTypeArray(cells, deep=True))
    pd = vtk.vtkPolyData()
    pd.SetPoints(p)
    pd.SetPolys(ca)
    n = vtk.vtkPolyDataNormals()
    n.SetInputData(pd)
    n.SetFeatureAngle(35)
    n.SplittingOn()
    n.Update()
    return n.GetOutput()


def render(bodies, fname, view="iso", title="", size=(1800, 1150), opacity=None, zoom=1.0):
    opacity = opacity or {}
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)
    for bd in bodies:
        m = vtk.vtkPolyDataMapper()
        m.SetInputData(_polydata(bd.shape))
        a = vtk.vtkActor()
        a.SetMapper(m)
        pr = a.GetProperty()
        pr.SetColor(*bd.color)
        pr.SetOpacity(opacity.get(bd.kind, 1.0))
        pr.SetSpecular(0.25)
        pr.SetSpecularPower(20)
        pr.SetAmbient(0.18)
        pr.SetDiffuse(0.85)
        ren.AddActor(a)
        # crisp feature edges
        fe = vtk.vtkFeatureEdges()
        fe.SetInputData(_polydata(bd.shape, 0.05))
        fe.BoundaryEdgesOff(); fe.FeatureEdgesOn(); fe.ManifoldEdgesOff(); fe.NonManifoldEdgesOff()
        fe.SetFeatureAngle(40)
        em = vtk.vtkPolyDataMapper()
        em.SetInputConnection(fe.GetOutputPort())
        em.ScalarVisibilityOff()
        ea = vtk.vtkActor()
        ea.SetMapper(em)
        ea.GetProperty().SetColor(0.15, 0.15, 0.15)
        ea.GetProperty().SetOpacity(0.55 * opacity.get(bd.kind, 1.0))
        ea.GetProperty().SetLineWidth(1.0)
        ren.AddActor(ea)
    cam = ren.GetActiveCamera()
    cam.ParallelProjectionOn()
    dirs = {"iso": ((-0.62, 0.62, 0.48), (0, 0, 1)), "iso_back": ((0.55, -0.7, 0.45), (0, 0, 1)),
            "top": ((0, 0, 1), (0, 1, 0)), "front": ((0, 1, 0), (0, 0, 1)),
            "left": ((0, -1, 0), (0, 0, 1))}
    d, up = dirs[view]
    ren.ResetCamera()
    fp = np.array(cam.GetFocalPoint())
    cam.SetPosition(*(fp + 500 * np.array(d)))
    cam.SetViewUp(*up)
    ren.ResetCamera()
    cam.Zoom(zoom)
    kit = vtk.vtkLightKit()
    kit.AddLightsToRenderer(ren)
    if title:
        t = vtk.vtkTextActor()
        t.SetInput(title)
        t.GetTextProperty().SetFontSize(26)
        t.GetTextProperty().SetColor(0.1, 0.1, 0.1)
        t.SetPosition(20, size[1] - 50)
        ren.AddViewProp(t)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.AddRenderer(ren)
    win.SetSize(*size)
    win.SetMultiSamples(8)
    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.Update()
    wr = vtk.vtkPNGWriter()
    wr.SetFileName(os.path.join(OUT, fname))
    wr.SetInputConnection(w2i.GetOutputPort())
    wr.Write()


# ------------------------------------------------------------------ sections
def section_faces(shape, y=0.0):
    plane = cq.Face.makePlane(600, 600, basePnt=cq.Vector(0, y, 0), dir=cq.Vector(0, 1, 0))
    try:
        return shape.intersect(plane).Faces()
    except Exception:
        return []


def plot_section(st, fname, title, xlim=(-60, 150), zlim=(-25, 58), annotate=True, y=0.0):
    fig, ax = plt.subplots(figsize=(18, 7.2), dpi=110)
    order = sorted(st.bodies, key=lambda b: b.kind == "bite")
    for bd in order:
        for f in section_faces(bd.shape, y):
            vs, tris = f.tessellate(0.02, 0.2)
            if not tris:
                continue
            xz = np.array([(v.x, v.z) for v in vs])
            polys = [xz[list(t)] for t in tris]
            ax.add_collection(PolyCollection(polys, facecolors=[bd.color], edgecolors="none", alpha=0.95))
            for e in f.Edges():
                pts = np.array([p.toTuple() for p in e.positions(np.linspace(0, 1, 40))])
                ax.plot(pts[:, 0], pts[:, 2], color="k", lw=0.5)
    ax.set_aspect("equal")
    ax.set_xlim(*xlim)
    ax.set_ylim(*zlim)
    ax.set_xlabel("X (mm)  -  mouth / stop face at X = 0, +X into the clip")
    ax.set_ylabel("Z (mm)")
    ax.axhline(P.TOP_Z, color="0.5", lw=0.6, ls="--")
    ax.text(xlim[1] - 1, P.TOP_Z + 0.6, "top surface Z 33.5", ha="right", fontsize=8, color="0.35")
    if annotate and st.mech is not None:
        m = st.mech
        ax.set_title(f"{title}   (lever {m.phi:+.1f}°, elevator top Z {m.elev_top:.2f}, "
                     f"plunger bottom Z {m.plunger_bot:.2f}, follower F {st.F:.2f})", fontsize=11)
    else:
        ax.set_title(title, fontsize=11)
    ax.grid(True, lw=0.3, alpha=0.4)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname))
    plt.close(fig)


# ------------------------------------------------------------------ exploded
def exploded_bodies():
    st = A.build("A", P.DEFAULT_SPRING, "nom")
    off = {
        "receiver_left": (0, -55, 0), "receiver_right": (0, 55, 0), "ring_hook": (0, -95, 0),
        "dowel": (0, -20, 0), "pin_pivot": (0, 30, 0), "pin_cup": (0, 38, 0), "pin_plunger": (0, 30, 0),
        "elevator": (0, 0, -45), "lever": (0, 0, -75), "plunger": (0, 0, 45), "paddle_pad": (0, 0, 70),
        "return_spring": (0, 0, -60),
        "clip_tube": (70, 0, 0), "end_cap": (135, 0, 0), "ribbon_clamp": (70, 0, -35),
        "screw_clamp": (70, 0, -55),
        "follower": (200, 0, 0), "drum": (200, 0, -40), "pin_axle": (200, 35, -40), "cf_spring": (200, 0, -40),
        "bite": (70, 0, 55),
    }
    out = []
    for bd in st.bodies:
        if bd.kind == "bite" and bd.name not in ("bite1", "bite2", "bite3"):
            continue
        key = next((k for k in off if bd.name.startswith(k)), None)
        dx, dy, dz = off.get(key, (0, 0, 0))
        if bd.name == "cf_spring":
            continue  # the ribbon is drawn with the follower below
        out.append(A.Body(bd.name, bd.kind, bd.shape.moved(cq.Location(cq.Vector(dx, dy, dz))), bd.moving))
    import hardware as H
    F = st.F
    sp = H.cf_spring(P.SPRINGS[P.DEFAULT_SPRING], F).val()
    out.append(A.Body("cf_spring", "cf_spring", sp.moved(cq.Location(cq.Vector(0, 0, -40))), True))
    g = A._static(P.DEFAULT_SPRING)["gate"]
    out.append(A.Body("gate", "gate", g.moved(cq.Location(cq.Vector(70, 0, 50))), False))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    for sn, label in (("A", "A_rest_full"), ("Bp", "Bprime_pressed_bite1_taken")):
        st = A.build(sn, P.DEFAULT_SPRING, "nom")
        nice = {"A": "State A - rest, full (docked, gate out)", "Bp": "State B' - pressed, bite 1 taken"}[sn]
        render(st.bodies, f"state_{label}_iso.png", "iso", f"{nice}  |  spring {P.DEFAULT_SPRING}, nominal bites",
               opacity=TRANSLUCENT, zoom=1.3)
        render(st.bodies, f"state_{label}_top.png", "top", f"{nice}  |  top view", opacity=TRANSLUCENT,
               size=(1900, 700), zoom=1.9)
        plot_section(st, f"state_{label}_section_Y0.png", f"{nice} - section at Y = 0")
        plot_section(st, f"state_{label}_section_Y0_zoom.png", f"{nice} - section at Y = 0 (receiver)",
                     xlim=(-56, 32), zlim=(-22, 56))
    # the other states as sections (quick reference)
    for sn, nice in (("B", "State B - pressed, bite 1 still on the cup"), ("C", "State C - rest, last bite"),
                     ("D", "State D - pressed, last bite"), ("Dt", "State D - pressed, last bite taken"),
                     ("E", "State E - undocked, full, gate in")):
        st = A.build(sn, P.DEFAULT_SPRING, "nom")
        plot_section(st, f"state_{sn}_section_Y0.png", nice)
    render(exploded_bodies(), "exploded.png", "iso", "Exploded view  |  EBD Clip v1.1", size=(2000, 1300), zoom=1.3)
    render(A.build("A", P.DEFAULT_SPRING, "nom").bodies, "state_A_rest_full_iso_back.png", "iso_back",
           "State A - mount (-Y) side with ring hook", opacity=TRANSLUCENT, zoom=1.3)


if __name__ == "__main__":
    main()
