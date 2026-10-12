Live: presets 10–40 + Oct 1–Nov 1 sunset schedule on the controller since 2026-10-12.

## What This Is
Presets + schedule for Taylor's Halloween hoops: 8 LED hoops in a row on one WLED controller.
`build.py` generates the controller's full `presets.json`; uploaded by hand (see Deployment).

## Stack
WLED 16.0.1 on ESP32 ("Niji"), 368 WS281x LEDs on one bus (pin 16), mic for AudioReactive.
Python 3 stdlib generator, no deps. Not a Docker app — nothing runs on Poppy.

## Local Development
```bash
python3 build.py          # writes presets.json, asserts segments tile 0-368
```

## Testing
Tests: none beyond the tiling assert in `build.py`. Real test = run preset 32 "Preview All" and watch.

## Deployment
Controller is `http://172.16.2.56` — **only reachable via `ssh poppy`**, not from this box.
```bash
ssh poppy "curl -s -F 'data=@-;filename=/presets.json' http://172.16.2.56/upload" < presets.json
ssh poppy "curl -s http://172.16.2.56/presets.json" | diff <(jq -S . presets.json) <(jq -S . -)
ssh poppy "curl -s -X POST -H 'Content-Type: application/json' --data-binary @- http://172.16.2.56/json/cfg" < schedule.json
```

## Key Files
- `build.py` — layout, looks (10-24), playlists (30 Ambient, 31 Show, 32 Preview), 40 Off
- `schedule.json` — NTP/timezone/location + timers, POSTed to `/json/cfg`
- `backup/` — controller `presets.json`/`cfg.json` from 2026-10-12, before any changes. Gitignored
  (repo is a PUBLIC fork of Snipercaine/WLED-Presets; cfg has network details). `build.py` reads it.

## Gotchas
- Effect/palette IDs are firmware-specific — take them from `/json/eff` and `/json/pal`, never from
  old preset collections (old "Halloween Eyes" fx 53 is "Image" on 16.x; it's 82 now).
- Hoop N = segment id N-1 = LEDs `46*(N-1)` to `46*N`. Every look re-states bounds so a bad
  layout self-heals; "Meteor Run" collapses to one segment and the next look rebuilds 8.
- Boot preset is 3 "Blend Taylor" — if its segments drift, every reboot reapplies the drift.
- Timers on 16.x: hour 254 = sunset, 255 = sunrise, `min` = ± offset. Needs NTP on + lat/long
  (set to Holladay, UT 40.67/-111.82, TZ index 6 = US Mountain — don't reset to defaults).
- 12 V strip, 18 A PSU: limiter `hw.led.maxpwr` = 15000 mA (~85%; strip max is ~11 A so it rarely bites), per-LED estimate 30 mA (WLED's 12 V
  value). POSTing `hw.led` to `/json/cfg` resets omitted `rgbwm`/`cb`/`fps` to defaults — send them too.
- Playlist `dur`/`transition` are tenths of a second.
- Color gamma is 2.8 and color order RGB (verified by eye). Mid RGB values get crushed, so colors in
  `build.py` are pre-boosted (orange 255,130,0 not 255,72,0) — check new colors on the hoops.
