"""Headless Metropole generate + GLB export for Molusco (Procgen Maps GPL-3.0)."""
import json
import os
import sys
import time

# Addon path
ADDON_PARENT = "/workspace/bene-proggen-maps"
EXPORT_DIR = "/workspace/procgen-export"
os.makedirs(EXPORT_DIR, exist_ok=True)
if ADDON_PARENT not in sys.path:
    sys.path.insert(0, ADDON_PARENT)

import bpy

# Clean default scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)

import procgen_maps
from procgen_maps.config import presets as preset_config
from procgen_maps.config import settings as global_settings
from procgen_maps.generators import city as city_gen
from procgen_maps.generators import terrain as terrain_gen
from procgen_maps.generators.city import buildings as buildings_mod
from procgen_maps.materials import city_mat, terrain_mat, world_mat
from procgen_maps.exporters import gltf_export

procgen_maps.register()

# Mobile-friendly: skip furnished interiors (huge poly cost, invisible from street for gameplay)
_orig_interior = buildings_mod._build_ground_floor_interior
def _skip_interior(*a, **k):
    return []
buildings_mod._build_ground_floor_interior = _skip_interior

# Slightly coarser terrain for export size
global_settings.TERRAIN_DEFAULT_RESOLUTION = 128

preset = preset_config.get_preset("METROPOLE")
seed = 1
print(f"[molusco] Generating Metropole seed={seed} radius={preset.radius}", flush=True)
t0 = time.time()

# Terrain
terrain_params = terrain_gen.TerrainParams(
    resolution=global_settings.TERRAIN_DEFAULT_RESOLUTION,
    world_size=max(global_settings.TERRAIN_DEFAULT_WORLD_SIZE, preset.radius * 2.5),
    scale=global_settings.TERRAIN_DEFAULT_SCALE,
    octaves=global_settings.TERRAIN_DEFAULT_OCTAVES,
    persistence=global_settings.TERRAIN_DEFAULT_PERSISTENCE,
    lacunarity=global_settings.TERRAIN_DEFAULT_LACUNARITY,
    max_height=global_settings.TERRAIN_DEFAULT_MAX_HEIGHT,
    seed=seed,
)
root = bpy.data.collections.new("ProcgenMaps")
bpy.context.scene.collection.children.link(root)
# Flat playable ground for Molusco (still Metropole layout/buildings from their code).
# Skip visible terrain mesh; pass terrain_params=None so buildings sit at z=0.
print("[molusco] flat ground (no terrain mesh)...", flush=True)
# Simple ground plane covering Metropole radius
import bmesh
bm=bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=preset.radius*1.15)
mesh=bpy.data.meshes.new("Molusco_Ground"); bm.to_mesh(mesh); bm.free()
gobj=bpy.data.objects.new("Molusco_Ground", mesh); root.objects.link(gobj)
gmat=bpy.data.materials.new("PM_Ground"); gmat.use_nodes=True
nt=gmat.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
out=nt.nodes.new("ShaderNodeOutputMaterial"); bsdf=nt.nodes.new("ShaderNodeBsdfPrincipled")
bsdf.inputs["Base Color"].default_value=(0.16,0.16,0.18,1); bsdf.inputs["Roughness"].default_value=0.92
nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
mesh.materials.append(gmat)

print("[molusco] city pipeline (flat)...", flush=True)
result = city_gen.generate_city(preset, terrain_params=None, seed=seed, parent_collection=None)

# Assign facade material like the operator does
mat = city_mat.get_or_create_city_material()
if mat is not None:
    for obj in result["building_objects"]:
        if obj.data and hasattr(obj.data, "materials"):
            if len(obj.data.materials) > 0:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)

# World sky (optional)
try:
    bpy.context.scene.world = world_mat.get_or_create_sky_world()
except Exception as e:
    print("[molusco] world skip:", e, flush=True)

# Realize collection instances (props) so glTF gets real meshes
print("[molusco] realizing instances...", flush=True)
bpy.ops.object.select_all(action='DESELECT')
empties = [o for o in bpy.data.objects if o.instance_type == 'COLLECTION' and o.instance_collection]
for o in empties:
    o.select_set(True)
if empties:
    bpy.context.view_layer.objects.active = empties[0]
    try:
        bpy.ops.object.duplicates_make_real()
    except Exception as e:
        print("[molusco] make_real warn:", e, flush=True)

# Delete leftover empties / lights for smaller GLB (game has own lighting)
for o in list(bpy.data.objects):
    if o.type in {'EMPTY', 'LIGHT', 'FONT', 'CAMERA'}:
        bpy.data.objects.remove(o, do_unlink=True)

# Bake procedural node materials to simple Principled for glTF (node groups often don't export well)
print("[molusco] simplifying materials for glTF...", flush=True)
# Facade palette keyed by material_index (approx from city_mat ColorRamp)
FACADE_COLORS = [
    (0.55, 0.65, 0.75, 1),  # glass_tower
    (0.72, 0.72, 0.74, 1),  # office
    (0.55, 0.28, 0.18, 1),  # brick
    (0.78, 0.72, 0.62, 1),  # apartment slab
    (0.70, 0.68, 0.66, 1),  # apartment tower
    (0.62, 0.48, 0.35, 1),  # townhouse
    (0.70, 0.58, 0.42, 1),  # cottage
    (0.85, 0.80, 0.70, 1),  # shopfront
    (0.45, 0.45, 0.48, 1),  # warehouse
    (0.40, 0.42, 0.40, 1),  # factory
    (0.35, 0.38, 0.42, 1),  # industrial tower
    (0.65, 0.55, 0.48, 1),  # mixed
    (0.90, 0.88, 0.82, 1),  # supermarket
    (0.25, 0.35, 0.55, 1),  # police
    (0.95, 0.95, 0.97, 1),  # hospital
    (0.75, 0.22, 0.18, 1),  # fire
    (0.55, 0.62, 0.45, 1),  # school
]
WINDOW_COLOR = (0.35, 0.55, 0.65, 1)
STREET_COLOR = (0.18, 0.18, 0.20, 1)
TERRAIN_COLOR = (0.25, 0.35, 0.22, 1)

def make_simple(name, rgba, metallic=0.0, roughness=0.75, emission=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = rgba
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    if emission is not None and 'Emission Color' in bsdf.inputs:
        bsdf.inputs['Emission Color'].default_value = emission
        bsdf.inputs['Emission Strength'].default_value = 2.0
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m

win_mat = make_simple("PM_Window", WINDOW_COLOR, metallic=0.3, roughness=0.15, emission=(0.4, 0.55, 0.7, 1))
street_mat = make_simple("PM_Street", STREET_COLOR, roughness=0.9)
terrain_simple = make_simple("PM_Terrain", TERRAIN_COLOR, roughness=0.95)
facade_mats = [make_simple(f"PM_Facade_{i}", FACADE_COLORS[i], roughness=0.7) for i in range(len(FACADE_COLORS))]

for obj in bpy.data.objects:
    if obj.type != 'MESH':
        continue
    name = obj.name
    if name.startswith("ProcgenMaps_Building") or "Building" in name:
        idx = int(obj.get("procgen_maps_material_index", 0)) % len(facade_mats)
        tint = float(obj.get("procgen_maps_tint", 0.5))
        # apply tinted copy lightly via existing palette
        mats = obj.data.materials
        while len(mats) < 2:
            mats.append(None)
        mats[0] = facade_mats[idx]
        mats[1] = win_mat
    elif "Street" in name or "street" in name or "Road" in name or "Intersection" in name:
        obj.data.materials.clear()
        obj.data.materials.append(street_mat)
    elif "Ground" in name or "Terrain" in name:
        obj.data.materials.clear()
        obj.data.materials.append(terrain_simple)

# Collision / anchor JSON from THEIR plans (exact footprints/heights)
colliders = []
anchors = []
for plan in result["building_plans"] + result["special_building_plans"]:
    xs = [p[0] for p in plan.footprint]
    ys = [p[1] for p in plan.footprint]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    cx = (minx + maxx) / 2
    cy = (miny + maxy) / 2
    base_z = 0.0
    h = plan.floors * plan.floor_height
    top = base_z + h
    # Blender XY -> Three.js XZ (Y up): map (x,y,z_blender) -> (x, z, -y) or (x,z,y)
    # We'll use Three convention: x=blender_x, y=height, z=blender_y
    pad = 0.4
    colliders.append({
        "min": [minx - pad, base_z, miny - pad],
        "max": [maxx + pad, top, maxy + pad],
        "roofY": top,
        "top": top + 0.9,
        "cx": cx, "cz": cy,
        "w": maxx - minx, "d": maxy - miny,
        "facade": plan.facade.key if hasattr(plan.facade, "key") else str(getattr(plan, "kind", "special")),
        "floors": plan.floors,
        "climb": True,
    })
    for x, z in ((minx, miny), (maxx, miny), (minx, maxy), (maxx, maxy), (cx, miny), (cx, maxy), (minx, cy), (maxx, cy)):
        anchors.append([x, top + 0.2, z])

meta = {
    "source": "https://github.com/Beneking102/bene-proggen-maps",
    "preset": "METROPOLE",
    "seed": seed,
    "radius": preset.radius,
    "block_size": preset.block_size,
    "layout_mode": preset.layout_mode,
    "buildings": len(result["building_plans"]),
    "special": len(result["special_building_plans"]),
    "streets": len(result["layout"].streets),
    "blocks": len(result["layout"].blocks),
    "axis": "blender_xy_to_three_xz",
    "note": "coords: x=blender_x, y=height, z=blender_y (Y-up Three.js)",
}
with open(os.path.join(EXPORT_DIR, "metropole_collision.json"), "w") as f:
    json.dump({"meta": meta, "colliders": colliders, "anchors": anchors}, f)
with open(os.path.join(EXPORT_DIR, "metropole_meta.json"), "w") as f:
    json.dump(meta, f, indent=2)

# Stats
verts = faces = 0
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.data:
        verts += len(obj.data.vertices)
        faces += len(obj.data.polygons)
print(f"[molusco] meshes={sum(1 for o in bpy.data.objects if o.type=='MESH')} verts={verts} faces={faces} t={time.time()-t0:.1f}s", flush=True)

# Join buildings into fewer objects for draw-call reduction (optional heavy)
print("[molusco] joining by material groups...", flush=True)
# Skip join if too many verts - just export as-is; Three can still frustum-cull

glb_path = os.path.join(EXPORT_DIR, "metropole.glb")
print(f"[molusco] exporting {glb_path}...", flush=True)
gltf_export.export_gltf(glb_path)
print(f"[molusco] done in {time.time()-t0:.1f}s size={os.path.getsize(glb_path)}", flush=True)

procgen_maps.unregister()
