"""The scriptorium in Blender (Cycles): one desk, one lamp, four eras.

    python3 tools/art/desk_scene.py SHOT [--res W H] [--samples N] [--out PATH]

SHOT is one of: menu, era1, era2, era3, era4, read1, read2, read3, final, tray.
Everything is modelled in code; textures come from assets/art/tex (made by
tex_*.py). Units are metres; the desk top is z = 0, +y points at the door.
"""
import argparse
import math
import sys
from pathlib import Path

import bpy  # noqa: I001  (bpy must come first: it puts bmesh on the path)
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
TEX = ROOT / "assets/art/tex"
FLOOR_Z = -0.34
LAMP = Vector((-0.66, 0.30, 0.44))      # flame position: brass stand left of the desk
rng_state = [12345]
SETTINGS = {"bounce": 5.0}


def rnd():
    rng_state[0] = (1103515245 * rng_state[0] + 12345) % (2 ** 31)
    return rng_state[0] / 2 ** 31


# ================================================================ scene setup
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 4
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.sample_clamp_indirect = 4.0
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = 0.35
    for look in ("AgX - Medium High Contrast", "AgX - Base Contrast", "None"):
        try:
            sc.view_settings.look = look
            break
        except TypeError:
            continue
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.010, 0.007, 0.005, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    sc.world = world
    return sc


def link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def smooth(ob):
    for p in ob.data.polygons:
        p.use_smooth = True


def bevel(ob, width, segments=3):
    m = ob.modifiers.new("bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    return ob


def place(ob, loc=(0, 0, 0), rot=(0, 0, 0), scale=None):
    ob.location = loc
    ob.rotation_euler = rot
    if scale:
        ob.scale = scale
    return ob


# ================================================================ meshes
def grid(name, sx, sy, nx, ny, zfun=None):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    vs = [[None] * (nx + 1) for _ in range(ny + 1)]
    for j in range(ny + 1):
        for i in range(nx + 1):
            u, v = i / nx, j / ny
            x, y = (u - 0.5) * sx, (v - 0.5) * sy
            vs[j][i] = bm.verts.new((x, y, zfun(u, v, x, y) if zfun else 0.0))
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
            for loop, c in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                loop[uv].uv = (c[0] / nx, c[1] / ny)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    smooth(ob)
    return ob


def lathe(name, profile, seg=56):
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        rings.append([bm.verts.new((max(r, 1e-4) * math.cos(2 * math.pi * k / seg),
                                    max(r, 1e-4) * math.sin(2 * math.pi * k / seg), z)) for k in range(seg)])
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    smooth(ob)
    return ob


def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), bev=0.002, mat=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    place(ob, loc, rot)
    if bev:
        bevel(ob, bev)
    if mat:
        ob.data.materials.append(mat)
    return ob


def tube(name, path, radii, seg=40, folds=0.0, flat=1.0, sag=0.0):
    """Sweep an ellipse along a polyline; radii per path point. Open at both ends."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    rings = []
    n = len(path)
    up = Vector((0, 0, 1))
    for i, p in enumerate(path):
        p = Vector(p)
        t = (Vector(path[min(i + 1, n - 1)]) - Vector(path[max(i - 1, 0)])).normalized()
        side = t.cross(up)
        if side.length < 1e-4:
            side = Vector((1, 0, 0))
        side.normalize()
        nrm = side.cross(t).normalized()
        ring = []
        grow = (i / max(1, n - 1)) ** 1.5
        for k in range(seg):
            a = 2 * math.pi * k / seg
            f = folds * (0.4 + grow)
            r = radii[i] * (1 + f * (0.6 * math.sin(5 * a + i * 0.7) + 0.4 * math.sin(9 * a - i * 0.4)))
            drop = sag * grow * max(0.0, -math.sin(a)) ** 1.5
            ring.append(bm.verts.new(p + side * (r * math.cos(a)) + nrm * (r * flat * math.sin(a)) - Vector((0, 0, drop))))
        rings.append(ring)
    for i in range(n - 1):
        for k in range(seg):
            f = bm.faces.new((rings[i][k], rings[i + 1][k], rings[i + 1][(k + 1) % seg], rings[i][(k + 1) % seg]))
            for loop, (kk, ii) in zip(f.loops, ((k, i), (k, i + 1), (k + 1, i + 1), (k + 1, i))):
                loop[uv].uv = (kk / seg, 1 - ii / (n - 1))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    smooth(ob)
    sol = ob.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = 0.004
    return ob


# ================================================================ materials
def img(name, colour=True):
    p = TEX / name
    if not p.exists():
        return None
    im = bpy.data.images.load(str(p), check_existing=True)
    if not colour:
        im.colorspace_settings.name = "Non-Color"
    return im


def principled(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    return mat, nt, nt.nodes["Principled BSDF"]


def tex_node(nt, image, proj="FLAT", coord=None, scale=None):
    n = nt.nodes.new("ShaderNodeTexImage")
    n.image = image
    n.projection = proj
    if proj == "BOX":
        n.projection_blend = 0.2
    if coord is not None:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        src = tc.outputs[coord]
        if scale:
            mp = nt.nodes.new("ShaderNodeMapping")
            mp.inputs["Scale"].default_value = scale
            nt.links.new(src, mp.inputs["Vector"])
            src = mp.outputs["Vector"]
        nt.links.new(src, n.inputs["Vector"])
    return n


def mat_textured(name, prefix, rough=0.6, bump=0.4, metal_default=0.0, coat=0.0, sheen=0.0, proj="FLAT", coord=None, scale=None):
    """Material from <prefix>_albedo/_rough/_height/_alpha/_metal PNGs."""
    mat, nt, b = principled(name)
    L = nt.links
    a = tex_node(nt, img(f"{prefix}_albedo.png"), proj, coord, scale)
    L.new(a.outputs["Color"], b.inputs["Base Color"])
    r_img = img(f"{prefix}_rough.png", False)
    if r_img:
        r = tex_node(nt, r_img, proj, coord, scale)
        rr = nt.nodes.new("ShaderNodeMapRange")
        rr.inputs["To Min"].default_value = 0.30
        rr.inputs["To Max"].default_value = 1.0
        L.new(r.outputs["Color"], rr.inputs["Value"])
        L.new(rr.outputs["Result"], b.inputs["Roughness"])
    else:
        b.inputs["Roughness"].default_value = rough
    m_img = img(f"{prefix}_metal.png", False)
    if m_img:
        m = tex_node(nt, m_img, proj, coord, scale)
        L.new(m.outputs["Color"], b.inputs["Metallic"])
    else:
        b.inputs["Metallic"].default_value = metal_default
    h_img = img(f"{prefix}_height.png", False)
    if h_img and bump > 0:
        h = tex_node(nt, h_img, proj, coord, scale)
        bn = nt.nodes.new("ShaderNodeBump")
        bn.inputs["Strength"].default_value = bump
        bn.inputs["Distance"].default_value = 0.002
        L.new(h.outputs["Color"], bn.inputs["Height"])
        L.new(bn.outputs["Normal"], b.inputs["Normal"])
    al_img = img(f"{prefix}_alpha.png", False)
    if al_img:
        al = tex_node(nt, al_img, proj, coord, scale)
        L.new(al.outputs["Color"], b.inputs["Alpha"])
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.08
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    return mat


def mat_flat(name, colour, rough=0.5, metal=0.0, coat=0.0, noise=0.0, noise_scale=40.0):
    mat, nt, b = principled(name)
    b.inputs["Base Color"].default_value = (*colour, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if noise:
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = noise_scale
        n.inputs["Detail"].default_value = 8
        ramp = nt.nodes.new("ShaderNodeMapRange")
        ramp.inputs["To Min"].default_value = rough - noise
        ramp.inputs["To Max"].default_value = rough + noise
        nt.links.new(n.outputs["Fac"], ramp.inputs["Value"])
        nt.links.new(ramp.outputs["Result"], b.inputs["Roughness"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["Factor"].default_value = 0.25
        mix.inputs["A"].default_value = (*colour, 1)
        mix.inputs["B"].default_value = (colour[0] * 0.6, colour[1] * 0.6, colour[2] * 0.6, 1)
        nt.links.new(n.outputs["Fac"], mix.inputs["Factor"])
        nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    return mat


def mat_brass():
    mat, nt, b = principled("brass")
    L = nt.links
    b.inputs["Metallic"].default_value = 1.0
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 60
    n.inputs["Detail"].default_value = 10
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.01
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (0.20, 0.13, 0.06, 1)     # tarnish in the crevices
    mix.inputs["B"].default_value = (0.78, 0.56, 0.26, 1)
    L.new(ao.outputs["AO"], mix.inputs["Factor"])
    L.new(mix.outputs["Result"], b.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.22
    rr.inputs["To Max"].default_value = 0.5
    L.new(n.outputs["Fac"], rr.inputs["Value"])
    L.new(rr.outputs["Result"], b.inputs["Roughness"])
    return mat


def mat_wood(name, era=1, base=(0.20, 0.11, 0.06), grain_scale=3.0, worn=True):
    """Walnut: wave-texture grain, polish worn at the front edge, era wear map."""
    mat, nt, b = principled(name)
    L = nt.links
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 7.0, 1.0)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "RINGS"
    wave.inputs["Scale"].default_value = grain_scale * 2.2
    wave.inputs["Distortion"].default_value = 14.0
    wave.inputs["Detail"].default_value = 6.0
    wave.inputs["Detail Scale"].default_value = 1.5
    L.new(mp.outputs["Vector"], wave.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 18
    noise.inputs["Detail"].default_value = 10
    L.new(mp.outputs["Vector"], noise.inputs["Vector"])
    col = nt.nodes.new("ShaderNodeMix")
    col.data_type = "RGBA"
    col.inputs["A"].default_value = (*base, 1)
    col.inputs["B"].default_value = (base[0] * 0.45, base[1] * 0.42, base[2] * 0.4, 1)
    L.new(wave.outputs["Fac"], col.inputs["Factor"])
    col2 = nt.nodes.new("ShaderNodeMix")
    col2.data_type = "RGBA"
    col2.blend_type = "MULTIPLY"
    col2.inputs["Factor"].default_value = 0.35
    L.new(col.outputs["Result"], col2.inputs["A"])
    L.new(noise.outputs["Color"], col2.inputs["B"])
    out_col = col2.outputs["Result"]
    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = 0.32
    rough.inputs["To Max"].default_value = 0.62
    L.new(noise.outputs["Fac"], rough.inputs["Value"])
    out_rough = rough.outputs["Result"]
    if worn:
        wear = img(f"desk_wear_era{era}.png", False)
        if wear:
            wt = tex_node(nt, wear, coord="UV")
            sep = nt.nodes.new("ShaderNodeSeparateColor")
            L.new(wt.outputs["Color"], sep.inputs["Color"])
            ink = nt.nodes.new("ShaderNodeMix")
            ink.data_type = "RGBA"
            ink.inputs["B"].default_value = (0.012, 0.009, 0.008, 1)
            L.new(sep.outputs["Red"], ink.inputs["Factor"])
            L.new(out_col, ink.inputs["A"])
            scr = nt.nodes.new("ShaderNodeMix")
            scr.data_type = "RGBA"
            scr.inputs["B"].default_value = (base[0] * 1.9, base[1] * 1.8, base[2] * 1.7, 1)
            scm = nt.nodes.new("ShaderNodeMath")
            scm.operation = "MULTIPLY"
            scm.inputs[1].default_value = 0.6
            L.new(sep.outputs["Green"], scm.inputs[0])
            L.new(scm.outputs["Value"], scr.inputs["Factor"])
            L.new(ink.outputs["Result"], scr.inputs["A"])
            burn = nt.nodes.new("ShaderNodeMix")
            burn.data_type = "RGBA"
            burn.inputs["B"].default_value = (0.008, 0.006, 0.005, 1)
            L.new(sep.outputs["Blue"], burn.inputs["Factor"])
            L.new(scr.outputs["Result"], burn.inputs["A"])
            out_col = burn.outputs["Result"]
            rmix = nt.nodes.new("ShaderNodeMix")
            rmix.data_type = "FLOAT"
            rmix.inputs["B"].default_value = 0.18
            L.new(sep.outputs["Red"], rmix.inputs["Factor"])
            L.new(out_rough, rmix.inputs["A"])
            out_rough = rmix.outputs["Result"]
    L.new(out_col, b.inputs["Base Color"])
    L.new(out_rough, b.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.15
    bump.inputs["Distance"].default_value = 0.0015
    L.new(wave.outputs["Fac"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return mat


def mat_emit(name, colour, strength):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*colour, 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def mat_plaster(name, colour=(0.25, 0.21, 0.16)):
    mat, nt, b = principled(name)
    L = nt.links
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 3.0
    n.inputs["Detail"].default_value = 12
    n.inputs["Roughness"].default_value = 0.65
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*colour, 1)
    mix.inputs["B"].default_value = (colour[0] * 0.55, colour[1] * 0.52, colour[2] * 0.5, 1)
    L.new(n.outputs["Fac"], mix.inputs["Factor"])
    L.new(mix.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.92
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    L.new(n.outputs["Fac"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return mat


# ================================================================ props
class Kit:
    """Builds the props; materials are made once and shared."""

    def __init__(self, era):
        self.era = era
        self.brass = mat_brass()
        self.iron = mat_flat("iron", (0.03, 0.028, 0.026), 0.55, 0.8, noise=0.15)
        self.reed = mat_flat("reed", (0.46, 0.33, 0.17), 0.45, noise=0.1, noise_scale=80)
        self.ink = mat_flat("ink", (0.004, 0.003, 0.003), 0.08)
        self.glaze = mat_flat("glaze", (0.83, 0.84, 0.80), 0.12, coat=0.6)
        self.paper_edge = mat_flat("paperedge", (0.72, 0.64, 0.50), 0.8)
        self.lacquer = mat_flat("lacquer", (0.16, 0.025, 0.02), 0.25, coat=0.8, noise=0.1)
        self.leather = mat_flat("leather", (0.12, 0.05, 0.03), 0.55, noise=0.2, noise_scale=300)
        self.wood_light = mat_wood("tray", era, base=(0.30, 0.18, 0.09), grain_scale=6, worn=False)

    # ---- the constant objects
    def desk(self):
        top = grid("desk_top", 1.40, 0.80, 2, 2)
        top.location = (0, 0, 0)
        sol = top.modifiers.new("thick", "SOLIDIFY")
        sol.thickness = 0.05
        sol.offset = -1
        bevel(top, 0.006, 4)
        top.data.materials.append(mat_wood("desk", self.era))
        apron = box("apron", (1.30, 0.70, 0.22), (0, 0, -0.16), bev=0.004, mat=mat_wood("desk2", self.era, worn=False))
        return top

    def lamp(self):
        prof = [(0.11, FLOOR_Z), (0.10, FLOOR_Z + 0.02), (0.035, FLOOR_Z + 0.05), (0.022, FLOOR_Z + 0.10),
                (0.016, 0.0), (0.03, 0.04), (0.016, 0.08), (0.016, 0.30), (0.045, 0.33), (0.07, 0.35),
                (0.075, 0.37), (0.06, 0.40), (0.02, 0.405)]
        stand = lathe("lamp_stand", prof)
        stand.location = (LAMP.x - 0.10, LAMP.y, 0)
        stand.data.materials.append(self.brass)
        spout = box("lamp_spout", (0.10, 0.022, 0.016), (LAMP.x - 0.045, LAMP.y, 0.388), (0, 0.22, 0), 0.004, self.brass)
        wick = lathe("wick", [(0.003, 0.0), (0.003, 0.012), (0.0015, 0.016)], 12)
        wick.location = (LAMP.x - 0.004, LAMP.y, 0.400)
        wick.data.materials.append(mat_flat("wick", (0.02, 0.015, 0.01), 0.9))
        flame = lathe("flame", [(0.0005, 0), (0.006, 0.006), (0.0075, 0.014), (0.006, 0.024), (0.003, 0.034), (0.0005, 0.042)], 24)
        flame.location = (LAMP.x - 0.004, LAMP.y, 0.412)
        flame.data.materials.append(mat_emit("flame", (1.0, 0.62, 0.26), 26.0))
        flame.visible_shadow = False
        L = bpy.data.lights.new("lamp", "POINT")
        L.energy = 34.0
        L.shadow_soft_size = 0.012
        L.color = (1.0, 0.56, 0.24)
        ob = link(bpy.data.objects.new("lamp_light", L))
        ob.location = LAMP
        glow = bpy.data.lights.new("glow", "POINT")
        glow.energy = 3.0
        glow.shadow_soft_size = 0.2
        glow.color = (1.0, 0.5, 0.2)
        g = link(bpy.data.objects.new("glow", glow))
        g.location = LAMP + Vector((0.05, -0.05, 0.25))
        bounce = bpy.data.lights.new("bounce", "AREA")
        bounce.shape = "DISK"
        bounce.size = 1.2
        bounce.energy = SETTINGS["bounce"]
        bounce.color = (1.0, 0.62, 0.34)
        bo = link(bpy.data.objects.new("bounce", bounce))
        bo.location = (-0.15, 0.10, 1.25)
        bo.visible_camera = False

    def room(self, door_light=True):
        plaster = mat_plaster("plaster")
        floor = grid("floor", 7, 8, 2, 2)
        floor.location = (0, 2.0, FLOOR_Z)
        mat, nt, b = principled("floor")
        brick = nt.nodes.new("ShaderNodeTexBrick")
        brick.inputs["Scale"].default_value = 1.2
        brick.inputs["Color1"].default_value = (0.10, 0.08, 0.06, 1)
        brick.inputs["Color2"].default_value = (0.07, 0.055, 0.045, 1)
        brick.inputs["Mortar"].default_value = (0.03, 0.025, 0.02, 1)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(tc.outputs["Object"], brick.inputs["Vector"])
        nt.links.new(brick.outputs["Color"], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.8
        floor.data.materials.append(mat)
        rug = grid("rug", 1.6, 2.2, 2, 2)
        rug.location = (0.2, 1.9, FLOOR_Z + 0.004)
        rm, rnt, rb = principled("rug")
        w = rnt.nodes.new("ShaderNodeTexWave")
        w.wave_type = "BANDS"
        w.bands_direction = "Y"
        w.inputs["Scale"].default_value = 6
        w.inputs["Distortion"].default_value = 0.0
        cr = rnt.nodes.new("ShaderNodeValToRGB")
        cr.color_ramp.interpolation = "CONSTANT"
        cr.color_ramp.elements[0].color = (0.10, 0.025, 0.02, 1)
        cr.color_ramp.elements[1].position = 0.5
        cr.color_ramp.elements[1].color = (0.025, 0.03, 0.06, 1)
        rnt.links.new(w.outputs["Fac"], cr.inputs["Fac"])
        rnt.links.new(cr.outputs["Color"], rb.inputs["Base Color"])
        rb.inputs["Roughness"].default_value = 0.95
        rb.inputs["Sheen Weight"].default_value = 0.15
        rug.data.materials.append(rm)
        back = box("wall_back_l", (3.0, 0.4, 3.0), (-1.95, 3.4, FLOOR_Z + 1.5), bev=0, mat=plaster)
        back = box("wall_back_r", (3.0, 0.4, 3.0), (2.55, 3.4, FLOOR_Z + 1.5), bev=0, mat=plaster)
        lintel = box("lintel", (1.1, 0.4, 1.0), (0.3, 3.4, FLOOR_Z + 2.5), bev=0, mat=plaster)
        box("wall_left", (0.4, 6.0, 3.0), (-2.3, 1.0, FLOOR_Z + 1.5), bev=0, mat=plaster)
        box("wall_right", (0.4, 6.0, 3.0), (2.4, 1.0, FLOOR_Z + 1.5), bev=0, mat=plaster)
        stone = mat_flat("stone", (0.22, 0.19, 0.15), 0.85, noise=0.1, noise_scale=8)
        for x in (-0.2, 0.8):
            box("jamb", (0.1, 0.42, 2.0), (x, 3.38, FLOOR_Z + 1.0), bev=0.01, mat=stone)
        box("sill", (1.1, 0.5, 0.06), (0.3, 3.36, FLOOR_Z + 0.03), bev=0.01, mat=stone)
        door_wood = mat_wood("door", 1, base=(0.12, 0.07, 0.04), grain_scale=4, worn=False)
        for k in range(5):
            box(f"plank{k}", (0.178, 0.05, 1.96), (-0.14 + 0.18 * k + 0.02, 3.3, FLOOR_Z + 1.0), bev=0.006, mat=door_wood)
        for z in (0.35, 1.55):
            box("strap", (0.9, 0.012, 0.06), (0.3, 3.27, FLOOR_Z + z), bev=0.003, mat=self.iron)
            for k in range(9):
                s = lathe("stud", [(0.012, 0), (0.012, 0.004), (0.006, 0.01), (0.0005, 0.012)], 12)
                s.location = (-0.08 + 0.095 * k, 3.264, FLOOR_Z + z)
                s.rotation_euler = (math.pi / 2, 0, 0)
                s.data.materials.append(self.iron)
        ring = bpy.data.meshes.new("ring")
        bm = bmesh.new()
        bmesh.ops.create_circle(bm, cap_ends=False, radius=0.05, segments=24)
        bm.to_mesh(ring)
        bm.free()
        r = link(bpy.data.objects.new("door_ring", ring))
        r.location = (0.62, 3.25, FLOOR_Z + 0.95)
        r.rotation_euler = (math.pi / 2, 0, 0)
        sk = r.modifiers.new("skin", "SCREW")
        sk.angle = 0
        sk.screw_offset = 0
        sk.steps = 1
        r.modifiers.new("sol", "SOLIDIFY").thickness = 0.01
        r.data.materials.append(self.iron)
        if door_light:
            em = mat_emit("daylight", (0.62, 0.74, 1.0), 90.0)
            gap = grid("gap_bottom", 0.9, 0.01, 1, 1)
            gap.location = (0.3, 3.31, FLOOR_Z + 0.004)
            gap.rotation_euler = (math.pi / 2, 0, 0)
            gap.data.materials.append(em)
            gap2 = grid("gap_side", 0.012, 1.95, 1, 1)
            gap2.location = (0.758, 3.33, FLOOR_Z + 1.0)
            gap2.rotation_euler = (math.pi / 2, 0, 0)
            gap2.data.materials.append(em)
            spill = bpy.data.lights.new("spill", "AREA")
            spill.shape = "RECTANGLE"
            spill.size = 0.9
            spill.size_y = 0.06
            spill.energy = 70
            spill.color = (0.62, 0.74, 1.0)
            so = link(bpy.data.objects.new("spill", spill))
            so.location = (0.3, 3.16, FLOOR_Z + 0.03)
            so.rotation_euler = (-math.pi / 2 + 0.25, 0, 0)
        # shelves on the left wall with bound books and rolls
        for z in (0.35, 0.75, 1.15):
            box("shelf", (0.32, 1.6, 0.03), (-1.95, 1.8, FLOOR_Z + z), bev=0.004, mat=mat_wood("shelf", 1, worn=False))
            y = 1.1
            while y < 2.5:
                th = 0.03 + 0.04 * rnd()
                hh = 0.2 + 0.1 * rnd()
                col = [(0.18, 0.06, 0.04), (0.10, 0.07, 0.04), (0.20, 0.14, 0.08), (0.08, 0.05, 0.05)][int(rnd() * 4)]
                box("book", (0.24, th, hh), (-1.95, y, FLOOR_Z + z + 0.015 + hh / 2), (0, 0, 0), 0.004,
                    mat_flat("bk", col, 0.6, noise=0.1, noise_scale=120))
                y += th + 0.005

    # ---- documents and tools
    def sheet(self, name, prefix, size, loc, rot_z=0.0, curl=0.006, wave=0.002, thick=0.0006, coat=0.0, bump=0.5):
        sx, sy = size

        def z(u, v, x, y):
            c = curl * ((abs(u - 0.5) * 2) ** 3) + wave * 0.5 * (1 + math.sin(u * 7.0 + v * 3.0) * math.sin(v * 5.0))
            return c + curl * 0.5 * ((abs(v - 0.5) * 2) ** 4)
        ob = grid(name, sx, sy, 48, int(48 * sy / sx), z)
        ob.location = (loc[0], loc[1], loc[2] + thick + 0.0002)
        ob.rotation_euler = (0, 0, rot_z)
        if thick:
            s = ob.modifiers.new("thick", "SOLIDIFY")
            s.thickness = thick
            s.offset = -1
        ob.data.materials.append(mat_textured(name, prefix, bump=bump, coat=coat))
        return ob

    def tablet(self, loc, rot_z=0.0):
        w, d, t = 0.25, 0.176, 0.03
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= w
            v.co.y *= d
            v.co.z *= t
        me = bpy.data.meshes.new("tablet")
        bm.to_mesh(me)
        bm.free()
        ob = link(bpy.data.objects.new("tablet", me))
        ob.location = (loc[0], loc[1], t / 2)
        ob.rotation_euler = (0, 0, rot_z)
        bevel(ob, 0.008, 5)
        ob.modifiers.new("sub", "SUBSURF").levels = 1
        ob.data.materials.append(mat_textured("tablet_side", "era1_tablet", bump=0.5, proj="BOX", coord="Object", scale=(3.5, 4.8, 1.0)))
        face = self.sheet("tablet_face", "era1_tablet", (w * 0.93, d * 0.92), (loc[0], loc[1], t + 0.0004), rot_z, curl=0.0, wave=0.0, thick=0, bump=2.2)
        # crumbs of soil around it
        soil = mat_flat("soil", (0.10, 0.07, 0.045), 0.95)
        for k in range(26):
            a = rnd() * 2 * math.pi
            r = 0.12 + 0.07 * rnd()
            s = 0.002 + 0.004 * rnd()
            c = box("crumb", (s, s * 1.3, s * 0.8), (loc[0] + r * math.cos(a), loc[1] + r * math.sin(a) * 0.8, s * 0.4), (rnd(), rnd(), rnd()), s * 0.3, soil)
        return ob

    def inkwell(self, loc):
        prof = [(0.032, 0), (0.036, 0.004), (0.038, 0.02), (0.034, 0.04), (0.022, 0.05), (0.016, 0.056), (0.017, 0.06), (0.012, 0.062)]
        ob = lathe("inkwell", prof)
        ob.location = loc
        ob.data.materials.append(self.brass)
        ink = lathe("ink_surface", [(0.0005, 0), (0.0115, 0)], 24)
        ink.location = (loc[0], loc[1], loc[2] + 0.058)
        ink.data.materials.append(self.ink)

    def pen(self, loc, rot_z, length=0.21):
        ob = lathe("pen", [(0.0045, 0), (0.0045, length * 0.8), (0.0042, length * 0.9), (0.0012, length)], 16)
        ob.location = loc
        ob.rotation_euler = (0, math.pi / 2 - 0.02, rot_z)
        ob.data.materials.append(self.reed)
        tip = lathe("pen_ink", [(0.0013, length * 0.97), (0.0009, length * 0.99), (0.0003, length)], 12)
        tip.location = loc
        tip.rotation_euler = ob.rotation_euler
        tip.data.materials.append(self.ink)

    def penbox(self, loc, rot_z=0.0):
        box("kalemdan", (0.30, 0.055, 0.032), (loc[0], loc[1], 0.016), (0, 0, rot_z), 0.006, self.lacquer)
        box("kalemdan_lid", (0.302, 0.057, 0.006), (loc[0], loc[1], 0.035), (0, 0, rot_z), 0.003, self.lacquer)

    def sandpot(self, loc):
        ob = lathe("rihdan", [(0.02, 0), (0.024, 0.01), (0.022, 0.03), (0.012, 0.042), (0.016, 0.046), (0.012, 0.048)])
        ob.location = loc
        ob.data.materials.append(self.brass)

    def knife(self, loc, rot_z):
        box("knife_blade", (0.05, 0.012, 0.0015), (loc[0] + 0.035 * math.cos(rot_z), loc[1] + 0.035 * math.sin(rot_z), 0.002), (0, 0, rot_z), 0.0005,
            mat_flat("steel", (0.55, 0.55, 0.56), 0.25, 1.0, noise=0.1))
        box("knife_handle", (0.07, 0.014, 0.01), (loc[0] - 0.025 * math.cos(rot_z), loc[1] - 0.025 * math.sin(rot_z), 0.005), (0, 0, rot_z), 0.003,
            mat_flat("bone", (0.72, 0.66, 0.52), 0.4, noise=0.1))

    def tray(self, loc, tiles, rot_z=0.0):
        """Rule tray: a wooden board with five shallow slots; tiles lie in them."""
        cx, cy = loc
        box("tray_base", (0.46, 0.115, 0.012), (cx, cy, 0.006), (0, 0, rot_z), 0.003, self.wood_light)
        for sx in (-0.226, 0.226):
            box("tray_end", (0.008, 0.115, 0.02), (cx + sx, cy, 0.01), (0, 0, rot_z), 0.002, self.wood_light)
        for sy in (-0.054, 0.054):
            box("tray_side", (0.46, 0.008, 0.02), (cx, cy + sy, 0.01), (0, 0, rot_z), 0.002, self.wood_light)
        for k in range(1, 5):
            box("tray_div", (0.004, 0.10, 0.016), (cx - 0.226 + 0.0904 * k, cy, 0.01), (0, 0, rot_z), 0.001, self.wood_light)
        for k, t in enumerate(tiles):
            if t:
                self.tile(t, (cx - 0.181 + 0.0904 * k, cy), 0.013, (rnd() - 0.5) * 0.04)

    def tile(self, prefix, loc, z0=0.0, rot_z=0.0, lift=0.0):
        w, h, t = 0.06, 0.08, 0.008
        body = box("tile_body", (w, h, t), (loc[0], loc[1], z0 + t / 2 + lift), (0, 0, rot_z), 0.0015, self.glaze)
        top = grid("tile_top", w * 0.97, h * 0.97, 2, 2)
        top.location = (loc[0], loc[1], z0 + t + 0.0002 + lift)
        top.rotation_euler = (0, 0, rot_z)
        top.data.materials.append(mat_textured(prefix, prefix, bump=0.3, coat=0.5))
        return body

    def notebook(self, prefix, loc, rot_z=0.0):
        w, h = 0.40, 0.28
        cover = box("nb_cover", (w + 0.02, h + 0.02, 0.006), (loc[0], loc[1], 0.003), (0, 0, rot_z), 0.002, self.leather)

        def z(u, v, x, y):
            return 0.004 + 0.010 * (1 - math.exp(-((x / 0.03) ** 2))) - 0.004 * (abs(x) / (w / 2)) ** 2
        pages = grid("nb_pages", w, h, 80, 40, z)
        pages.location = (loc[0], loc[1], 0.006)
        pages.rotation_euler = (0, 0, rot_z)
        pages.data.materials.append(mat_textured("nb", prefix, bump=0.4))
        block = box("nb_block", (w - 0.004, h - 0.004, 0.006), (loc[0], loc[1], 0.006), (0, 0, rot_z), 0.002, self.paper_edge)
        return pages

    def scroll(self, loc, rot_z):
        ob = lathe("scroll", [(0.017, 0), (0.017, 0.2)], 32)
        ob.location = (loc[0], loc[1], 0.018)
        ob.rotation_euler = (0, math.pi / 2, rot_z)
        ob.data.materials.append(mat_flat("scrollpaper", (0.80, 0.72, 0.56), 0.7, noise=0.1, noise_scale=60))
        cord = mat_flat("cord", (0.35, 0.08, 0.05), 0.8)
        for k in (0.07, 0.13):
            c = lathe("cord", [(0.0185, 0), (0.0185, 0.004)], 32)
            c.location = ob.location
            c.rotation_euler = ob.rotation_euler
            c.location.x += k * math.cos(rot_z)
            c.location.y += k * math.sin(rot_z)
            c.data.materials.append(cord)
        seal = grid("seal", 0.04, 0.04, 16, 16, lambda u, v, x, y: 0.003 * max(0.0, 1 - ((u - .5) ** 2 + (v - .5) ** 2) * 4))
        seal.location = (loc[0] + 0.1 * math.cos(rot_z), loc[1] + 0.1 * math.sin(rot_z) - 0.012, 0.03)
        seal.rotation_euler = (0.6, 0, rot_z)
        seal.data.materials.append(mat_textured("wax", "era2_wax", bump=1.2, coat=0.3))

    def sleeve(self, prefix, start, end, r0=0.06, r1=0.11, flat=0.7, hand=True):
        """A long sleeve reaching in from the frame edge; the hand stays inside it.
        An unseen hand shape casts its shadow forward onto the desk."""
        mid = start.lerp(end, 0.5) + Vector((0, 0, 0.05))
        path = []
        for i in range(19):
            t = i / 18
            p = (1 - t) ** 2 * start + 2 * (1 - t) * t * mid + t * t * end
            path.append(tuple(p))
        radii = [r0 + (r1 - r0) * (i / 18) ** 1.6 for i in range(19)]
        ob = tube("sleeve", path, radii, 64, folds=0.10, flat=flat, sag=0.035)
        ob.modifiers["thick"].material_offset = 1
        ob.data.materials.append(mat_textured("sleeve", prefix, bump=0.8, sheen=0.7))
        ob.data.materials.append(mat_flat("sleeve_in", (0.015, 0.011, 0.009), 0.95))
        if hand:
            d = (end - Vector(path[-3])).normalized()
            side = d.cross(Vector((0, 0, 1))).normalized()
            pts = []
            base = end + d * 0.01
            outline = [(-0.035, 0.0), (-0.04, 0.05), (-0.03, 0.085), (-0.018, 0.13), (-0.008, 0.135), (-0.006, 0.09),
                       (0.0, 0.142), (0.01, 0.142), (0.012, 0.095), (0.02, 0.136), (0.03, 0.13), (0.03, 0.09),
                       (0.042, 0.115), (0.05, 0.105), (0.045, 0.05), (0.035, 0.0)]
            bm = bmesh.new()
            vs = [bm.verts.new(base + side * a + d * b + Vector((0, 0, -0.012 + 0.04 * b))) for a, b in outline]
            bm.faces.new(vs)
            me = bpy.data.meshes.new("hand")
            bm.to_mesh(me)
            bm.free()
            h = link(bpy.data.objects.new("hand_shadow", me))
            h.modifiers.new("sol", "SOLIDIFY").thickness = 0.012
            h.visible_camera = False
            h.visible_glossy = False
            h.visible_diffuse = False
        return ob

    def ebru_box(self, loc, size, rot_z=0.0, label=None, open_=False):
        mat = mat_textured("ebru", "era4_ebru", bump=0.0, proj="BOX", coord="Object", scale=(3.0, 3.0, 3.0))
        if open_:
            sx, sy, sz = size
            box("ob_base", (sx, sy, 0.006), (loc[0], loc[1], 0.003), (0, 0, rot_z), 0.002, mat)
            for dx, dy, w, d in ((0, sy / 2, sx, 0.006), (0, -sy / 2, sx, 0.006), (sx / 2, 0, 0.006, sy), (-sx / 2, 0, 0.006, sy)):
                c, s = math.cos(rot_z), math.sin(rot_z)
                box("ob_wall", (w, d, sz), (loc[0] + dx * c - dy * s, loc[1] + dx * s + dy * c, sz / 2), (0, 0, rot_z), 0.002, mat)
            return
        b = box("archive_box", size, (loc[0], loc[1], loc[2] + size[2] / 2), (0, 0, rot_z), 0.004, mat)
        box("spine", (0.03, size[1] + 0.002, size[2] + 0.002), (loc[0] - size[0] / 2 + 0.012, loc[1], loc[2] + size[2] / 2), (0, 0, rot_z), 0.003, self.leather)
        if label:
            lab = grid("label", 0.1, 0.056, 2, 2)
            lab.location = (loc[0] + 0.02, loc[1] - size[1] / 2 - 0.0012, loc[2] + size[2] * 0.55)
            lab.rotation_euler = (math.pi / 2, 0, 0)
            m = mat_textured("label", label, bump=0)
            lab.data.materials.append(m)
        return b


# ================================================================ shots
def camera(loc, look_at, lens=21.0, focus=None, fstop=4.0, ortho=None):
    cam = bpy.data.cameras.new("cam")
    ob = link(bpy.data.objects.new("cam", cam))
    ob.location = loc
    d = Vector(look_at) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cam.sensor_width = 36
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    else:
        cam.lens = lens
    cam.dof.use_dof = focus is not None
    if focus is not None:
        cam.dof.focus_distance = focus
        cam.dof.aperture_fstop = fstop
    cam.clip_start = 0.01
    bpy.context.scene.camera = ob
    return ob


def desk_camera():
    return camera((0.0, -0.80, 0.50), (0.02, 0.32, -0.06), lens=21.0, focus=0.86, fstop=5.6)


def common(kit, notebook="era1_notebook", pens=True):
    kit.desk()
    kit.lamp()
    kit.room()
    kit.inkwell((0.30, 0.27, 0.0))
    kit.sandpot((0.39, 0.30, 0.0))
    kit.penbox((0.0, 0.33), 0.03)
    if pens:
        kit.pen((0.06, -0.05, 0.0046), 2.75)
        kit.pen((0.15, -0.31, 0.0046), 3.0, 0.19)
    kit.knife((0.37, -0.02), 1.9)
    shav = mat_flat("shaving", (0.62, 0.48, 0.28), 0.6)
    for k in range(14):
        a = rnd() * 6.28
        sh = lathe("shaving", [(0.0015 + 0.002 * rnd(), 0), (0.003, 0.004 + 0.008 * rnd()), (0.001, 0.012)], 8)
        sh.location = (0.40 + 0.05 * math.cos(a) * rnd(), -0.06 + 0.04 * math.sin(a) * rnd(), 0.0015)
        sh.rotation_euler = (math.pi / 2, 0, rnd() * 6.28)
        sh.data.materials.append(shav)
    if notebook:
        kit.notebook(notebook, (0.46, 0.06), -0.32)


def shot(name):
    era = {"menu": 1, "era1": 1, "era2": 2, "era3": 3, "era4": 4, "read1": 1, "read2": 2, "read3": 3, "final": 4, "tray": 2}[name]
    SETTINGS["bounce"] = 7.0 if name.startswith("read") else 1.5
    kit = Kit(era)
    if name == "menu":
        common(kit, notebook=None)
        kit.sheet("menu_cover", "menu_cover", (0.24, 0.34), (-0.02, 0.06, 0.042), 0.06, curl=0.0, wave=0.0, thick=0, bump=1.0)
        box("book_block", (0.236, 0.336, 0.036), (-0.02, 0.06, 0.022), (0, 0, 0.06), 0.003, kit.paper_edge)
        box("book_back", (0.244, 0.344, 0.006), (-0.02, 0.06, 0.003), (0, 0, 0.06), 0.002, kit.leather)
        for i, x in enumerate((-0.087, -0.029, 0.029, 0.087)):
            s = grid(f"slip{i}", 0.056, 0.02, 2, 2)
            ang = 0.06 + (rnd() - 0.5) * 0.05
            s.location = (-0.02 + x - 0.012, 0.06 - 0.168 - 0.007 + 0.002 * (i % 2), 0.012 + 0.003 * i)
            s.rotation_euler = (0, 0, ang)
            s.data.materials.append(mat_textured("slip", f"menu_slip_{i + 1}", bump=0))
        camera((0.0, -0.42, 0.36), (-0.03, 0.0, 0.0), lens=30, focus=0.52, fstop=4.0)
    elif name in ("era1", "read1"):
        common(kit)
        kit.tablet((-0.10, 0.12), 0.05)
        kit.sheet("copy", "era1_parchment", (0.20, 0.277), (0.2, -0.13, 0.0004), -0.08)
        kit.tray((-0.20, -0.25), ["tile_R1", "tile_R2", None, None, None])
        kit.tile("tile_R3_blank", (-0.47, -0.17), 0.0, 0.25)
        if name == "era1":
            kit.sleeve("sleeve_linen", Vector((1.15, 0.40, 0.24)), Vector((0.24, 0.24, 0.05)), 0.055, 0.075, 0.75)
            desk_camera()
        else:
            camera((-0.10, 0.12, 0.62), (-0.10, 0.12, 0.0), ortho=0.34)
    elif name in ("era2", "read2", "tray"):
        common(kit)
        kit.sheet("illum", "era2_illum", (0.24, 0.3467), (-0.08, 0.10, 0.0006), 0.04, bump=0.6)
        kit.sheet("copy", "era2_copy", (0.20, 0.277), (0.22, -0.12, 0.0004), -0.12)
        kit.sheet("deed", "era2_deed", (0.11, 0.183), (0.36, 0.18, 0.0012), 0.5)
        kit.tray((-0.20, -0.25), ["tile_R3", "tile_R4", "tile_R1", "tile_R2", None])
        kit.scroll((0.06, 0.32), 0.25)
        if name == "era2":
            kit.sleeve("sleeve_kemha", Vector((1.15, 0.46, 0.24)), Vector((0.26, 0.32, 0.05)), 0.055, 0.075, 0.75)
            desk_camera()
        elif name == "read2":
            camera((-0.08, 0.10, 0.62), (-0.08, 0.10, 0.0), ortho=0.40)
        else:
            camera((-0.20, -0.42, 0.24), (-0.20, -0.25, 0.0), lens=50, focus=0.30, fstop=8)
    elif name in ("era3", "read3"):
        common(kit, notebook="era3_notebook_argos")
        box("wrap", (0.27, 0.33, 0.003), (-0.08, 0.11, 0.0015), (0, 0, 0.12), 0.003, kit.leather)
        kit.sheet("burnt", "era3_burnt", (0.20, 0.271), (-0.07, 0.10, 0.0032), -0.06, curl=0.008, wave=0.003, bump=0.8)
        kit.sheet("copy", "era2_copy", (0.20, 0.277), (0.22, -0.12, 0.0004), -0.12)
        kit.tray((-0.20, -0.25), ["tile_R6_scorched", "tile_R5", None, None, None])
        if name == "era3":
            kit.sleeve("sleeve_felt", Vector((1.15, 0.42, 0.24)), Vector((0.20, 0.27, 0.05)), 0.06, 0.08, 0.75)
            desk_camera()
        else:
            camera((-0.07, 0.10, 0.62), (-0.07, 0.10, 0.0), ortho=0.31)
    elif name in ("era4", "final"):
        common(kit)
        kit.ebru_box((0.42, 0.24, 0.0), (0.30, 0.22, 0.09), -0.2, "era4_label_1")
        kit.ebru_box((0.40, 0.25, 0.09), (0.30, 0.22, 0.08), -0.15, "era4_label_2")
        kit.ebru_box((-0.10, 0.12), (0.26, 0.34, 0.07), 0.05, open_=True)
        for k in range(4):
            kit.sheet(f"stack{k}", "era2_copy" if k % 2 else "era3_burnt", (0.20, 0.277), (-0.10 + 0.004 * k, 0.12 - 0.003 * k, 0.008 + 0.003 * k), 0.05 + 0.03 * (rnd() - 0.5), curl=0.003, wave=0.001)
        kit.sheet("card", "era4_card", (0.15, 0.096), (0.16, -0.12, 0.0006), -0.1, curl=0.001, wave=0.0, thick=0.0008)
        kit.tray((-0.20, -0.25), ["tile_R2_worn", "tile_R6_scorched", None, None, None])
        if name == "era4":
            desk_camera()
        else:
            camera((0.15, -0.36, 0.30), (0.16, -0.09, 0.0), lens=36, focus=0.38, fstop=4.5)


def render(name, res, samples, out):
    sc = reset()
    shot(name)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.cycles.samples = samples
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("shot")
    ap.add_argument("--res", nargs=2, type=int, default=[960, 540])
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or str(ROOT / f"assets/art/bible/{a.shot}.png")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    render(a.shot, tuple(a.res), a.samples, out)
