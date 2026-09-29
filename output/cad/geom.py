"""Small CadQuery helpers so the part files read like the spec tables (X/Y/Z ranges)."""
import math
import cadquery as cq


def box(x0, x1, y0, y1, z0, z1) -> cq.Workplane:
    """Axis-aligned box from coordinate ranges (the way the spec writes them)."""
    xa, xb = sorted((x0, x1))
    ya, yb = sorted((y0, y1))
    za, zb = sorted((z0, z1))
    return (cq.Workplane("XY")
            .box(xb - xa, yb - ya, zb - za, centered=False)
            .translate((xa, ya, za)))


def cyl_y(cx, cz, d, y0, y1) -> cq.Workplane:
    """Cylinder with its axis along Y through (cx, cz), from y0 to y1."""
    ya, yb = sorted((y0, y1))
    return (cq.Workplane("XZ", origin=(cx, 0, cz)).circle(d / 2).extrude(-(yb - ya))
            .translate((0, ya, 0)))


def cyl_z(cx, cy, d, z0, z1) -> cq.Workplane:
    za, zb = sorted((z0, z1))
    return cq.Workplane("XY", origin=(cx, cy, za)).circle(d / 2).extrude(zb - za)


def cyl_x(cy, cz, d, x0, x1) -> cq.Workplane:
    xa, xb = sorted((x0, x1))
    return cq.Workplane("YZ", origin=(xa, cy, cz)).circle(d / 2).extrude(xb - xa)


def cone_z(cx, cy, z0, d0, z1, d1) -> cq.Workplane:
    """Truncated cone along Z (for countersinks)."""
    s = cq.Solid.makeCone(d0 / 2, d1 / 2, z1 - z0, pnt=cq.Vector(cx, cy, z0), dir=cq.Vector(0, 0, 1))
    return cq.Workplane("XY").add(s)


def prism_xz(pts, y0, y1) -> cq.Workplane:
    """Closed polygon given as (x, z) points, extruded along Y from y0 to y1."""
    ya, yb = sorted((y0, y1))
    # XZ workplane: local x = X, local y = Z, normal = -Y
    wp = cq.Workplane("XZ").polyline(pts).close().extrude(-(yb - ya))
    return wp.translate((0, ya, 0))


def prism_yz(pts, x0, x1) -> cq.Workplane:
    """Closed polygon given as (y, z) points, extruded along X from x0 to x1."""
    xa, xb = sorted((x0, x1))
    return cq.Workplane("YZ", origin=(xa, 0, 0)).polyline(pts).close().extrude(xb - xa)


def slot_y(cx0, cx1, cz, h, y0, y1) -> cq.Workplane:
    """Obround (stadium) slot running in X from cx0 to cx1 (overall), height h, cut along Y."""
    length = cx1 - cx0
    ya, yb = sorted((y0, y1))
    wp = (cq.Workplane("XZ", origin=((cx0 + cx1) / 2, 0, cz))
          .slot2D(length, h, 0).extrude(-(yb - ya)))
    return wp.translate((0, ya, 0))


def hex_y(cx, cz, af, y0, y1) -> cq.Workplane:
    """Hexagonal prism (nut trap) along Y, flats top and bottom (horizontal)."""
    ya, yb = sorted((y0, y1))
    d = af / math.cos(math.radians(30))  # across corners
    # polygon() puts a vertex on local +x -> flats are top/bottom in local y (= Z)
    wp = cq.Workplane("XZ", origin=(cx, 0, cz)).polygon(6, d).extrude(-(yb - ya))
    return wp.translate((0, ya, 0))


def union_all(items):
    it = iter(items)
    out = next(it)
    for w in it:
        out = out.union(w)
    return out


def solid(wp) -> cq.Shape:
    """Single compound/solid from a Workplane."""
    return wp.val() if len(wp.vals()) == 1 else cq.Compound.makeCompound(wp.vals())


def rot_about_y(shape, px, pz, deg):
    """Rotate a shape about the axis parallel to Y through (px, 0, pz).
    Positive deg lifts +X-side points (right-hand rotation about -Y)."""
    return shape.rotate(cq.Vector(px, 0, pz), cq.Vector(px, -1, pz), deg)
