# Molusco assets (CC0)

## Integrated
- **diesel.glb** — Diesel humanoid (CC0, Mixamo-ready). Visible player body. Textures resized to 1024 and WebP-compressed (~922 KB).
- **molusco.glb** — Quaternius UAL1 Standard clips (CC0): Idle, Walk, Jog, Sprint, Jump_*, Roll, Crouch_*. Invisible animation driver (UE-style bones).
- **molusco_parkour.glb** — Quaternius UAL2 Standard clips (CC0): ClimbUp_1m, NinjaJump_*, Slide_*.
- Runtime retarget maps UAL bones → Mixamo (`mixamorigHips`, …) every frame; procedural layer still drives swing/climb/flip overlays.

## Skipped
- **Traverser v2.0** Unity FBX/C# toolkit — browser Three.js cannot run Unity scripts; FBX→GLB conversion tooling (Blender/assimp) not available on the build box. Parkour locomotion covered by UAL clips + existing procedural poses instead.
- **Quaternius Ultimate Animated Characters / Heroes FBX** — older pack; UAL1/UAL2 Standard GLBs already supply the locomotion/parkour clips wired above. Heroes FBX would need the same missing FBX pipeline.
- **molusco_body.glb** (UMC Casual Hoodie) — replaced by Diesel as the visible hero (kept on disk unused).

## Performance (S24 Ultra)
- Quality presets: Baixo / Médio / Alto / Ultra. Default Alto; Ultra uses up to devicePixelRatio 3, 4K shadow maps, bloom.
- Main loop is uncapped `requestAnimationFrame` (no forced 30/45 cap unless user enables “Limitar FPS → 30”).
- Auto-quality steps down only if FPS stays under ~55.
