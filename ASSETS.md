# Molusco assets

## Character
- **diesel.glb** — Diesel humanoid (CC0, Mixamo-ready). Visible player body. Textures resized to 1024 and WebP-compressed (~922 KB).
- **molusco.glb** — Quaternius UAL1 Standard clips (CC0): Idle, Walk, Jog, Sprint, Jump_*, Roll, Crouch_*. Invisible animation driver.
- **molusco_parkour.glb** — Quaternius UAL2 Standard clips (CC0): ClimbUp_1m, NinjaJump_*, Slide_*.
- Runtime retarget maps UAL bones → Mixamo (`mixamorigHips`, …) every frame; procedural layer still drives swing/climb/flip overlays.

## City — Procgen Maps Metropole (required)
- **Source repo:** https://github.com/Beneking102/bene-proggen-maps (GPL-3.0-or-later). See `LICENSE-ProcgenMaps-GPL3.txt`.
- **Preset:** `METROPOLE` (largest archetype: radius 400 m, raster layout, building heights 15–120 m), seed `1`.
- **Pipeline used:** Blender 4.2.3 headless — registered the addon, ran their `generate_city(METROPOLE)` (layout → zones → streets → buildings → props → signage → parking), skipped furnished interiors for mobile poly count, joined meshes by material (~30 draw calls), exported glTF/GLB with Draco.
- **Published files:**
  - `city/metropole.glb` — Draco-compressed city mesh (~7.4 MB).
  - `city/metropole_collision.json` — AABBs + swing anchors derived from their `BuildingPlan` footprints/heights (same generator output).
  - `city/metropole_meta.json` — preset/seed/stats sidecar.
  - `city/generate_metropole.py` — exact headless script used to produce the export.
  - `city/metropole_shot.jpg` — Blender EEVEE overview of the exported Metropole used in-game.
- This is **not** a hand-authored city: geometry and layout come from Procgen Maps’ Metropole generator/export path.

## Skipped
- **Traverser v2.0** Unity FBX/C# toolkit — browser Three.js cannot run Unity scripts.
- **molusco_body.glb** (UMC Casual Hoodie) — replaced by Diesel as the visible hero (kept on disk unused).

## Performance (S24 Ultra)
- Quality presets: Baixo / Médio / Alto / Ultra. Default Alto; Ultra uses up to devicePixelRatio 3, 4K shadow maps, bloom.
- Main loop is uncapped `requestAnimationFrame` (no forced 30/45 cap unless user enables “Limitar FPS → 30”).
- Auto-quality steps down only if FPS stays under ~55.
- City: ~30 merged meshes, Draco decode, frustum culling; shadows only on building groups.
