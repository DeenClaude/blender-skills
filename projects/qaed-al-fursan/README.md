# Qaed Al Fursan — 3D luxury perfume commercial (Blender)

A 16-second, 9:16 vertical commercial built entirely from one Blender Python script, following the 12-shot AI storyboard. Black × gold × Arabian heritage.

| | |
|---|---|
| Software | Blender 4.2+ or 5.x (tested on 5.3), Cycles |
| Output | MP4 (H.264), 1080 × 1920, 24 fps, 384 frames |
| Colour | AgX, Punchy look |
| Preview | 360 × 640, 12 samples (quick check of timing and motion) |

## Files

```
qaed-al-fursan/
├── qaed_al_fursan.py       # builds the whole project, saves the .blend, renders
├── make_assets.py          # regenerates the textures / Arabic outlines in assets/
├── qaed_al_fursan.blend    # saved project, written by the script (not in git: ~75 MB, regenerated on every run)
├── assets/
│   ├── label_mask.png      # front label foil mask (white = gold foil)
│   ├── box_mask.png        # retail box front panel
│   ├── horse_emblem.png    # horse emblem silhouette (rendered from the 3D horse)
│   ├── arabic_title.json   # shaped outlines of قائد الفرسان (HarfBuzz + Amiri)
│   └── fonts/              # Amiri Bold, EB Garamond (both SIL Open Font License)
└── render/                 # outputs (not in git)
    ├── qaed_al_fursan_preview.mp4
    └── qaed_al_fursan_final.mp4
```

## How to run

```bash
# Build + save the .blend + render a low-res preview MP4
blender -b -P qaed_al_fursan.py -- --quality preview --render

# Final 1080x1920 render
blender -b -P qaed_al_fursan.py -- --quality final --render

# Resumable PNG sequence (safe to stop and restart; finished frames are skipped)
blender -b -P qaed_al_fursan.py -- --quality final --png --render
ffmpeg -framerate 24 -i render/frames_final/f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 16 render/qaed_al_fursan_final.mp4

# Single test frames
blender -b -P qaed_al_fursan.py -- --quality preview --still 24 170 352
```

Other options: `--frames A-B` (render part of the timeline), `--out DIR`, `--no-save`.

Without Blender installed, `pip install bpy` (the official Blender-as-a-Python-module wheel) works the same way: `python qaed_al_fursan.py -- --quality preview --render`.

To open the project interactively, open `qaed_al_fursan.blend`. Shot cameras are bound to timeline markers `S01`–`S12`, so scrubbing the timeline switches cameras.

## Shot list (as built)

| # | Time | Frames | Shot | Camera |
|---|------|--------|------|--------|
| 01 | 0–2s | 1–48 | Desert sunrise, fade in from black | Slow dolly + tilt up, 28 mm |
| 02 | 2–4s | 49–96 | Arabian horse galloping on the dunes, hoof sand | Low tracking shot, 40 mm, sun behind |
| 03 | 4–5s | 97–120 | Horse emblem on the label, light sweep | Macro push-in, 85 mm, f/5.6 |
| 04 | 5–6s | 121–144 | Bottle silhouette against golden smoke, rims fade up | Slow dolly, 50 mm |
| 05 | 6–8s | 145–192 | Hero product on black marble plinth | Low-angle slow orbit, 50 mm |
| 06 | 8–10s | 193–240 | Ribbed cap + gold collar | Macro orbit, 85 mm, f/2.8 |
| 07 | 10–11s | 241–264 | Oud wood, amber, saffron, jasmine | Lateral dolly, 50 mm |
| 08 | 11–12s | 265–288 | Cap off, perfume spray (particles + mist volume) | Slow push, 50 mm |
| 09 | 12–13s | 289–312 | The wearer in thobe and ghutra, horse behind | Medium shot, 50 mm, f/2.8 |
| 10 | 13–14s | 313–336 | Bottle on a desert rock at sunset | Slow orbit, 50 mm |
| 11 | 14–15s | 337–360 | 3D gold قائد الفرسان / QAED AL FURSAN / EAU DE PARFUM | Static, rising type + glint sweep |
| 12 | 15–16s | 361–384 | Bottle + box end pack on the rock | Gentle push, 45 mm |

Transitions: hard cuts on the beat, with exposure dips to black into shots 04, 07, 09 and 11, and a fade in from black at the start.

## Collections

`PRODUCT` (bottle; `LABEL` is nested inside so label parts travel with every bottle instance), `ENVIRONMENT` (dunes, haze, rock, studio, ingredients, horse, wearer), `LIGHTING`, `CAMERAS`, `PARTICLES` (desert dust, hoof sand, studio motes, perfume mist), `ANIMATION` (bottle instances, helpers), `BRAND_ELEMENTS` (end card, box).

The hero bottle exists once (in the studio). The bottles on the desert rock are collection instances of it, so edits to the bottle appear everywhere.

## How the main pieces are built

- **Bottle:** a beveled rectangular block of black lacquered glass (clear coat, smudge-modulated roughness), a gold collar, a lathed cap with seven horizontal grooves, and a gold atomizer under the cap. The label is a UV-mapped plane driven by `label_mask.png`: a gold metal/black lacquer mix with embossed bump. Built at 10× real scale (1 BU = 1 cm), 85 × 38 × 90 body.
- **Desert:** a 1.4 km numpy heightfield of sharp-crested dunes, flattened around the action area. Sand uses noise colour, wind-ripple wave bump and fine grain. A homogeneous volume gives aerial haze and god rays. The sky is a custom gradient with a sun disc and halo matched to the sun lamp.
- **Horse:** an FK armature with metaball muscle volumes parented to the bones. The gallop cycle is procedural (per-leg phase offsets, knee and hock flexion, body pitch, head nod, tail).
- **Arabic typography:** Blender text objects cannot join Arabic letters. `make_assets.py` shapes قائد الفرسان with HarfBuzz using the Amiri font and stores the outlines. The script builds them as real extruded and beveled 3D curves, so the lettering is correctly joined.
- **Studio:** a black acrylic floor, black marble plinth with gold rim, large key softbox, front strip, low bounce card, twin golden rim strips, a back glow card and a smoke volume. Light levels are keyed per shot.

## Validation (runs automatically before rendering)

The script checks for missing textures, a camera marker on every shot, timeline coverage of 1–384 with no gaps, a 9:16 aspect ratio, fps and frame range, bottle proportions, and fonts missing (falling back to Blender's built-in font). The result is printed as `[QAF] validation: OK`.

## Swapping in the real product artwork

No photo of the actual bottle was supplied, only the storyboard. So the label is a faithful stand-in in the storyboard's style (interlocking gold bands, horse emblem, Arabic and Latin name), not a copy of the original print. To use the real label:

1. Scan or photograph the front label straight-on and crop it square.
2. Convert it to a mask: gold foil = white, black lacquer = black. Save it as `assets/label_mask.png`, ideally 2048 px or larger.
3. Do the same for the box front (`assets/box_mask.png`, aspect 1 : 1.18).
4. Re-run the script. If the real bottle's proportions differ, edit `BODY_W / BODY_D / BODY_H / CAP_R / CAP_H` at the top of the script.

The wearer in shot 09 is a procedural stand-in (thobe, ghutra, agal). For a photoreal person, import a scanned or MPFB human and parent it to `Man_Root`. The camera, light and timing are already set.

## Render times (4-core CPU, Cycles)

- Preview 360 × 640: about 7–9 s per frame, roughly 50 min for all 384 frames.
- Final 1080 × 1920 at 64 samples with adaptive sampling and OpenImageDenoise: much longer on CPU. A GPU (OptiX/HIP/Metal) is strongly recommended. Set the device in Preferences, or change `c.device = "GPU"` in `configure_render`.
