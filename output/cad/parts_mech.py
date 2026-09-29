"""Part group (d): elevator/cup, lever, plunger, paddle pad.
Reference poses: elevator at rest on its ledge (nominal X); lever horizontal
about its pivot; plunger and pad with the plunger bottom at Z = 0 (the assembly
translates it to the kinematic height)."""
import math
import cadquery as cq
import params as P
from geom import box, cyl_y, cyl_z, prism_xz, prism_yz, slot_y


def elevator() -> cq.Workplane:
    """§6.3  Block X -14.0 -> -2.4, Y ±9.95, Z -15.5 -> 4.5 at rest.
    Cup floor = top face.  Rear-top 0.5 / front-top 0.3 / side-top 0.3 chamfers."""
    x0, x1, hw = P.ELEV_X0, P.ELEV_X1, P.ELEV_HW
    z0, z1 = P.LEDGE_Z, P.RAIL_TOP_Z
    cf, cr = P.ELEV_FRONT_CHAMFER, P.ELEV_REAR_CHAMFER
    prof = [(x0, z0), (x1, z0), (x1, z1 - cr), (x1 - cr, z1), (x0 + cf, z1), (x0, z1 - cf)]
    e = prism_xz(prof, -hw, hw)
    cs = P.ELEV_SIDE_CHAMFER
    for s in (+1, -1):
        e = e.cut(prism_yz([(s * (hw + 0.01), z1 - cs - 0.01), (s * (hw + 0.01), z1 + 0.01),
                            (s * (hw - cs - 0.01), z1 + 0.01)], x0 - 1, x1 + 1))
    # lever notch in the front face, open at the bottom
    e = e.cut(box(x0 - 1, P.ELEV_NOTCH_X1, -P.LEVER_NOTCH_HW, P.LEVER_NOTCH_HW, z0 - 1, z0 + P.LEVER_NOTCH_H))
    # horizontal pin slots through both cheeks (square ends: the full X length is usable,
    # a rounded end would clip the pin when the elevator sits at the end of its 0.3 play)
    zs = z0 + P.SLOT_Z
    e = e.cut(box(P.ELEV_SLOT_X[0], P.ELEV_SLOT_X[1], -hw - 1, hw + 1, zs - P.SLOT_H / 2, zs + P.SLOT_H / 2))
    return e


def lever() -> cq.Workplane:
    """§6.4  28.0 between end-pin centres, 6.0 thick (Y), 5.0 tall, full-round ends.
    Built horizontal; +X end is the cup end."""
    L = 2 * P.LEVER_R + P.LEVER_H
    lv = (cq.Workplane("XZ", origin=(P.PIVOT_X, 0, P.PIVOT_Z)).slot2D(L, P.LEVER_H, 0)
          .extrude(-P.LEVER_T).translate((0, -P.LEVER_T / 2, 0)))
    lv = lv.cut(cyl_y(P.PIVOT_X, P.PIVOT_Z, P.LEVER_PIVOT_HOLE_D, -5, 5))
    for s in (+1, -1):
        lv = lv.cut(cyl_y(P.PIVOT_X + s * P.LEVER_R, P.PIVOT_Z, P.LEVER_END_HOLE_D, -5, 5))
    return lv


def plunger() -> cq.Workplane:
    """§6.5  10 x 12 body, 16 x 18 x 2 flange, lever notch, pin slots, spring ear
    with spigot.  Built with the plunger bottom at Z = 0."""
    px = P.PADDLE_X
    hx, hy = P.PLUNGER_LX / 2, P.PLUNGER_LY / 2
    body = box(px - hx, px + hx, -hy, hy, 0, P.FLANGE_OFFSET + 0.01)
    fl = box(px - P.FLANGE_LX / 2, px + P.FLANGE_LX / 2, -P.FLANGE_LY / 2, P.FLANGE_LY / 2,
             P.FLANGE_OFFSET, P.FLANGE_OFFSET + P.FLANGE_T)
    fl = fl.edges("|Z").chamfer(P.EDGE_CHAMFER)
    ear = box(P.EAR_X_END, px - hx + 0.01, -hy, hy, P.EAR_UNDERSIDE, P.EAR_UNDERSIDE + P.EAR_H)
    ear = ear.edges("<X and |Y").chamfer(P.SMALL_CHAMFER)
    spig = cyl_z(P.SPRING_WELL_X, 0, P.SPIGOT_D, P.EAR_UNDERSIDE - P.SPIGOT_L, P.EAR_UNDERSIDE + 0.01)
    p = body.union(fl).union(ear).union(spig)
    p = p.cut(box(px - hx - 1, px + hx + 1, -P.LEVER_NOTCH_HW, P.LEVER_NOTCH_HW, -1, P.LEVER_NOTCH_H))
    p = p.cut(box(px + P.PLUNGER_SLOT_DX[0], px + P.PLUNGER_SLOT_DX[1], -hy - 1, hy + 1,
                  P.SLOT_Z - P.SLOT_H / 2, P.SLOT_Z + P.SLOT_H / 2))
    return p


def paddle_pad() -> cq.Workplane:
    """§6.5  TPU 95A pad 25 x 18 x 3.0, top domed 1.0, a 1.0-tall rim at each X end
    locates it over the flange.  Built with the plunger bottom at Z = 0."""
    px = P.PADDLE_X
    zf = P.FLANGE_OFFSET + P.FLANGE_T          # flange top
    blank = (cq.Workplane("XY", origin=(px, 0, zf - P.PAD_RIM_H))
             .rect(P.PAD_LX, P.PAD_LY).extrude(P.PAD_RIM_H + P.PAD_T)
             .edges("|Z").fillet(P.PAD_CORNER_R))
    # channel that fits over the flange (leaves a rim at each X end)
    gx = P.FLANGE_LX / 2 + P.PAD_RIM_CLR
    blank = blank.cut(box(px - gx, px + gx, -P.PAD_LY, P.PAD_LY, zf - P.PAD_RIM_H - 1, zf))
    # dome: sphere through the top centre with PAD_DOME drop at the corners
    a = math.hypot(P.PAD_LX / 2, P.PAD_LY / 2)
    R = (a * a + P.PAD_DOME ** 2) / (2 * P.PAD_DOME)
    # sphere axis along Y so its poles (tessellation singularities) are far outside the pad
    sph = cq.Workplane("XY").add(cq.Solid.makeSphere(R, cq.Vector(px, 0, zf + P.PAD_T - R), cq.Vector(0, 1, 0),
                                                     angleDegrees1=-90, angleDegrees2=90))
    return blank.intersect(sph)
