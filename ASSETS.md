# Molusco assets

## Character
- **diesel.glb** — Diesel humanoid (CC0). Visible player body.
- **molusco.glb** / **molusco_parkour.glb** — Quaternius UAL clips (CC0), invisible animation driver.

## City — Kenney City Kit (CC0)
Playable world is **not** Procgen Metropole.
- `city/kenney/commercial/` — City Kit Commercial buildings + skyscrapers (textured colormap)
- `city/kenney/suburban/` — suburban buildings
- `city/kenney/trees/` — park trees
- `city/kenney/roads/` — road tile refs (optional)
- Source: https://kenney.nl/assets/city-kit-commercial (+ Suburban / Roads)
- License: CC0 1.0 — `LICENSE-Kenney-CityKit-CC0.txt`

Layout: procedural grid N=6 (HALF≈139 m), sync AABB colliders + swing anchors, solid asphalt ground, grass parks. GLB prototypes cloned then merged by material for mobile draw calls.

## Why Metropole was removed from play
`city/metropole.glb` kept for reference only. Root cause of phone bugs:
1. Export had **0 textures** (Blender shader-node materials → flat baseColor only) → washed/white blink on mobile.
2. Game asphalt `ground.visible=false` + green `PM_Terrain` mesh → falling showed green flashing “limbo”.
3. Collision JSON alone couldn’t save a look that was already broken in screenshots.

## Legacy
- `city/metropole.*` — unused Procgen Maps Metropole export (GPL-3.0).
