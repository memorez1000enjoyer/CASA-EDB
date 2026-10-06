"""§9.8 printability checks on the exported STLs:
  - watertight / consistent winding / shell count
  - wall thickness >= 0.8 (inward ray cast from surface samples, device frame)
  - overhangs > 45° must be within 1.0 of a supported edge or bridge <= 25 between
    two supported edges (print frame, i.e. the STL as exported)
"""
import os
import json
import numpy as np
import trimesh
import networkx as nx
import params as P

HERE = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(HERE, "..", "stl")
WALL_TOL = 1e-3
CANTILEVER_OK = 1.0     # an unsupported ledge up to 1.0 wide prints fine with 4 perimeters
BRIDGE_MAX = 25.0
BED_TOL = 0.05
BED_EDGE_H = 0.8        # fillets/chamfers rising from the bed up to this height are fine

# Spec-defined features thinner than 0.8 (device-frame boxes) -> reported, not failed.
ALLOWED_THIN = {
    "follower": [((-0.1, 0.8, -10, 10, z - 0.4, z + 0.4), f"push rib (spec: 0.5 tall x 0.6)") for z in P.PUSH_RIB_Z],
    "follower_springA": [((-0.1, 0.8, -10, 10, z - 0.4, z + 0.4), "push rib (spec: 0.5 tall x 0.6)") for z in P.PUSH_RIB_Z],
    "clip_tube": [
        ((-0.1, 1.3, -10, 10, 2.0, 4.6), "rail stub in front of the gate slot: 1.2 lip with the spec 0.5 rail chamfer"),
        ((-0.1, 1.3, -12.3, 12.3, 32.8, 33.6), "top corner of the 1.2 mouth lip with the spec 0.5 mouth chamfer"),
        ((2.9, 4.6, -7.5, 7.5, -0.4, 0.1), "clamp notch (X 3.1-3.9) meets the Ø2.3 screw holes (X 3.85-6.15): spec overlap 0.05, not a wall"),
    ],
    "ribbon_clamp": [((P.CLAMP_NOTCH_X - 0.4, P.CLAMP_NOTCH_X + 0.4, -8, 8, -0.5, 0.2),
                      "clamp ridge (spec: 0.3 tall; 0.4 wide inside the 0.8 notch around the ribbon)")],
}


ALLOWED_THIN["clip_tube_viewslots"] = ALLOWED_THIN["clip_tube"]


def _device_mesh(name):
    """Tessellate the part in the device frame (for thickness + allowlists)."""
    import export
    import re as _re
    m = _re.search(r"_spring([AB])$", name)
    parts = export._parts(m.group(1) if m else P.DEFAULT_SPRING)
    base = _re.sub(r"_spring[AB]$", "", name)
    w = parts[base][0]
    shp = w.val() if len(w.vals()) == 1 else __import__("cadquery").Compound.makeCompound(w.vals())
    vs, fs = shp.tessellate(0.01, 0.1)
    return trimesh.Trimesh(np.array([v.toTuple() for v in vs]), np.array(fs))


def wall_thickness(mesh, n=80000, seed=1):
    area = mesh.area
    n = int(min(max(area * 4.0, 4000), n))   # ~4 samples per mm²
    pts, fi = trimesh.sample.sample_surface(mesh, n, seed=seed)
    nrm = mesh.face_normals[fi]
    orig = pts - nrm * 1e-4
    locs, idx_ray, _ = mesh.ray.intersects_location(orig, -nrm, multiple_hits=False)
    th = np.full(len(pts), np.inf)
    th[idx_ray] = np.linalg.norm(locs - orig[idx_ray], axis=1)
    return pts, th


def _in_box(p, b):
    x0, x1, y0, y1, z0, z1 = b
    return (p[:, 0] >= x0) & (p[:, 0] <= x1) & (p[:, 1] >= y0) & (p[:, 1] <= y1) & (p[:, 2] >= z0) & (p[:, 2] <= z1)


def thin_report(name, mesh):
    pts, th = wall_thickness(mesh)
    thin = th < P.MIN_WALL_ABS - WALL_TOL
    allowed_notes = []
    allowed = np.zeros(len(pts), bool)
    for box, why in ALLOWED_THIN.get(name, []):
        m = _in_box(pts, box) & thin
        if m.any():
            allowed |= m
            allowed_notes.append(f"{why} {th[m].min():.2f}")
    bad = thin & ~allowed
    finite = th[np.isfinite(th)]
    min_all = float(finite.min()) if len(finite) else float("nan")
    min_bad = float(th[bad].min()) if bad.any() else None
    min_ok = float(th[~allowed & np.isfinite(th)].min())
    clusters = []
    if bad.any():
        bp = pts[bad]
        g = np.round(bp / 2.0).astype(int)
        keys, inv = np.unique(g, axis=0, return_inverse=True)
        for k in range(len(keys)):
            sel = inv.ravel() == k
            c = bp[sel].mean(axis=0)
            clusters.append(dict(at=[round(float(v), 1) for v in c], min=float(th[bad][sel].min()), n=int(sel.sum())))
    return dict(min_wall=min_ok, min_including_allowed=min_all, n_bad=int(bad.sum()), clusters=clusters[:12],
                allowed=allowed_notes, wall_ok=not bad.any())


# ------------------------------------------------------------------ overhangs
def _ray_hits(p, dirs, seg_a, seg_b):
    """For point p (2,), directions (k,2), segments (m,2)x2: distance to first hit per direction and segment idx."""
    d = seg_b - seg_a                                    # (m,2)
    res_t = np.full(len(dirs), np.inf)
    res_i = np.full(len(dirs), -1)
    for j, r in enumerate(dirs):
        den = r[0] * d[:, 1] - r[1] * d[:, 0]
        ok = np.abs(den) > 1e-12
        ap = seg_a - p
        t = np.where(ok, (ap[:, 0] * d[:, 1] - ap[:, 1] * d[:, 0]) / np.where(ok, den, 1), np.inf)
        u = np.where(ok, (ap[:, 0] * r[1] - ap[:, 1] * r[0]) / np.where(ok, den, 1), -1)
        hit = ok & (t > 1e-6) & (u >= -1e-9) & (u <= 1 + 1e-9)
        if hit.any():
            tt = np.where(hit, t, np.inf)
            i = int(np.argmin(tt))
            res_t[j], res_i[j] = tt[i], i
    return res_t, res_i


def overhang_report(mesh):
    n = mesh.face_normals
    tri = mesh.triangles
    zmin = mesh.bounds[0][2]
    down = n[:, 2] < -np.cos(np.radians(45.0)) - 1e-6
    on_bed = tri[:, :, 2].max(axis=1) < zmin + BED_TOL
    cand = down & ~on_bed
    regions = []
    if not cand.any():
        return True, regions
    adj = mesh.face_adjacency
    adj_e = mesh.face_adjacency_edges
    g = nx.Graph()
    g.add_nodes_from(np.nonzero(cand)[0])
    both = cand[adj[:, 0]] & cand[adj[:, 1]]
    g.add_edges_from(adj[both])
    V = mesh.vertices
    for comp in nx.connected_components(g):
        comp = np.array(sorted(comp))
        inreg = np.zeros(len(mesh.faces), bool)
        inreg[comp] = True
        one = inreg[adj[:, 0]] ^ inreg[adj[:, 1]]
        seg_a, seg_b, sup = [], [], []
        for (f0, f1), (v0, v1) in zip(adj[one], adj_e[one]):
            fo = f1 if inreg[f0] else f0
            ez = (V[v0, 2] + V[v1, 2]) / 2
            far = [v for v in mesh.faces[fo] if v not in (v0, v1)][0]
            supported = on_bed[fo] or V[far, 2] < ez - 1e-4 or (
                abs(V[far, 2] - ez) <= 1e-4 and mesh.face_normals[fo][2] > 0.5)
            seg_a.append(V[v0, :2]); seg_b.append(V[v1, :2]); sup.append(supported)
        seg_a, seg_b, sup = np.array(seg_a), np.array(seg_b), np.array(sup)
        area = float(mesh.area_faces[comp].sum())
        if area < 0.05:
            continue
        # rounded/chamfered bottom edges that start on the bed: each 0.2 layer steps out
        # < one line width, the normal "elephant-foot" zone - printable without support
        zr = mesh.triangles[comp][:, :, 2].max()
        if zr < zmin + BED_EDGE_H and sup.any():
            regions.append(dict(area=round(area, 1), bad_frac=0.0, bridge=0.0, z=round(float(zr), 2),
                                bbox=[], note="bed-edge fillet"))
            continue
        # sample points in the region (area-weighted)
        sub = mesh.submesh([comp], append=True)
        k = int(min(max(area * 4, 20), 1500))
        sp, _ = trimesh.sample.sample_surface(sub, k, seed=2)
        p2 = sp[:, :2]
        dirs = np.array([[np.cos(a), np.sin(a)] for a in np.radians(np.arange(0, 180, 10))])
        sa, sb = seg_a[sup], seg_b[sup]

        def dist_to_supported(p):
            if len(sa) == 0:
                return np.inf
            d = sb - sa
            t = np.clip(np.einsum("ij,ij->i", p - sa, d) / np.maximum(np.einsum("ij,ij->i", d, d), 1e-12), 0, 1)
            q = sa + t[:, None] * d
            return float(np.min(np.linalg.norm(q - p, axis=1)))

        bad = 0
        worst_span = 0.0
        for p in p2:
            if dist_to_supported(p) <= CANTILEVER_OK:
                continue
            tp, ip = _ray_hits(p, dirs, seg_a, seg_b)
            tn, iN = _ray_hits(p, -dirs, seg_a, seg_b)
            okb = (ip >= 0) & (iN >= 0)
            okb &= np.where(ip >= 0, sup[np.maximum(ip, 0)], False) & np.where(iN >= 0, sup[np.maximum(iN, 0)], False)
            spans = np.where(okb, tp + tn, np.inf)
            best = spans.min()
            if best <= BRIDGE_MAX:
                worst_span = max(worst_span, best)
                continue
            bad += 1
        bb = sub.bounds
        regions.append(dict(area=round(area, 1), bad_frac=round(bad / len(p2), 3), bridge=round(worst_span, 1),
                            z=round(float(sp[:, 2].mean()), 1),
                            bbox=[round(float(x), 1) for x in (bb[0][0], bb[1][0], bb[0][1], bb[1][1])]))
    failing = [r for r in regions if r["bad_frac"] > 0.02 and r["area"] * r["bad_frac"] > 0.5]
    return (not failing), regions


def check_all():
    meta = json.load(open(os.path.join(STL, "parts_meta.json")))
    rows = []
    for name, m in meta.items():
        mesh = trimesh.load(os.path.join(STL, name + ".stl"))
        wt, wc = mesh.is_watertight, mesh.is_winding_consistent
        bodies = len(mesh.split(only_watertight=False))
        dev = _device_mesh(name)
        tr = thin_report(name, dev)
        oh_ok, regs = overhang_report(mesh)
        flags = []
        failing = [r for r in regs if r["bad_frac"] > 0.02 and r["area"] * r["bad_frac"] > 0.5]
        for r in failing:
            flags.append(f"SUPPORT: {r['area'] * r['bad_frac']:.0f} mm² unsupported at print Z {r['z']} "
                         f"(x {r['bbox'][0]}..{r['bbox'][1]}, y {r['bbox'][2]}..{r['bbox'][3]})")
        for c in tr["clusters"]:
            flags.append(f"thin {c['min']:.2f} at device {c['at']}")
        for a in tr["allowed"]:
            flags.append(f"spec feature: {a}")
        maxb = max([r["bridge"] for r in regs], default=0.0)
        if maxb > 0:
            flags.append(f"longest bridge {maxb:.1f}")
        rows.append(dict(name=name, orient=m["orientation"], watertight=bool(wt), winding=bool(wc), bodies=bodies,
                         volume=float(mesh.volume), min_wall=tr["min_wall"], wall_ok=tr["wall_ok"],
                         overhang_ok=oh_ok, flags=flags, regions=regs))
        print(f"{name:22s} wt={wt} bodies={bodies} wall={tr['min_wall']:.2f} ok={tr['wall_ok']} overhang_ok={oh_ok} "
              f"{'; '.join(flags)[:300]}")
    return rows


if __name__ == "__main__":
    check_all()
