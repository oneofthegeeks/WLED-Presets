# WLED Halloween Hoops

Presets, playlists and a sunset-based schedule for 8 LED hoops in a row on a WLED 16 controller.
`python3 build.py` generates `presets.json`; deploy commands are in `CLAUDE.md`.

| # | Preset | # | Preset |
|---|---|---|---|
| 10 | Pumpkin Glow | 20 | Halloween Eyes |
| 11 | Witch Brew | 21 | Lightning Storm |
| 12 | Haunted Candles | 22 | Meteor Run |
| 13 | Spirit Twinkle | 23 | Fire Hoops |
| 30 | **Ambient** playlist | 24 | Toxic Drip |
| 31 | **Halloween Show** playlist | 32 | Preview All (once, then Ambient) |
| 40 | Lights Off | | |

Schedule (Oct 1 – Nov 1): sunset −15m Ambient → sunset +30m Show → 9:00pm Ambient → 11:30pm off.
Halloween night (Oct 31): Show starts at sunset −30m, no Ambient warm-up.
