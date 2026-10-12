#!/usr/bin/env python3
"""Build presets.json for the Halloween hoops (WLED 16.0.1 on 172.16.2.56).

Run: python3 build.py   -> writes presets.json (full file, upload-ready)
Effect/palette IDs come from the live controller's /json/eff and /json/pal;
they change between WLED versions, so re-check after a firmware upgrade.
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
HOOPS, HOOP_LEN = 8, 46  # address order == left-to-right on the lawn
TOTAL = HOOPS * HOOP_LEN  # 368, matches the LED bus length
BRI = 160  # power limiter (8500mA) dims further if a look would exceed it

ORANGE, PURPLE, GREEN = [255, 72, 0], [110, 0, 255], [50, 255, 0]
RED, WHITE, BLACK = [255, 0, 0], [255, 255, 255], [0, 0, 0]
DIM_PURPLE = [15, 0, 30]

# effect / palette IDs on 16.0.1
FX = dict(breathe=2, colorwaves=67, candle_multi=102, twinklefox=80,
          eyes=82, lightning=57, meteor=76, fire2012=66, drip=96)
PAL_DEFAULT, PAL_COLORS_ONLY, PAL_FIRE = 0, 5, 35


def hoop(i, **fx):
    """Segment i = one hoop, with fixed bounds so every preset re-asserts the layout."""
    return {"id": i, "start": i * HOOP_LEN, "stop": (i + 1) * HOOP_LEN,
            "n": f"Hoop {i + 1}", "on": True, "bri": 255, "grp": 1, "spc": 0, "of": 0, **fx}


def look(name, segs, transition=15):
    return {"n": name, "on": True, "bri": BRI, "transition": transition, "mainseg": 0, "seg": segs}


def each(fn):
    return [hoop(i, **fn(i)) for i in range(HOOPS)]


def alt(a, b):
    return lambda i: a if i % 2 == 0 else b


looks = {
    # --- ambient (slow) ---
    10: look("Pumpkin Glow", each(lambda i: dict(
        fx=FX["breathe"], sx=50, ix=128, pal=PAL_DEFAULT,
        col=[alt(ORANGE, PURPLE)(i), BLACK, BLACK]))),
    11: look("Witch Brew", each(lambda i: dict(
        fx=FX["colorwaves"], sx=40, ix=128, pal=PAL_COLORS_ONLY,
        col=[ORANGE, PURPLE, GREEN]))),
    12: look("Haunted Candles", each(lambda i: dict(
        fx=FX["candle_multi"], sx=96, ix=200, pal=PAL_DEFAULT,
        col=[alt(ORANGE, PURPLE)(i), BLACK, BLACK]))),
    13: look("Spirit Twinkle", each(lambda i: dict(
        fx=FX["twinklefox"], sx=60, ix=180, pal=PAL_COLORS_ONLY,
        col=[PURPLE, GREEN, ORANGE]))),
    # --- show (punchy) ---
    20: look("Halloween Eyes", each(lambda i: dict(
        fx=FX["eyes"], sx=128, ix=128, pal=PAL_DEFAULT,
        col=[alt(RED, GREEN)(i), BLACK, BLACK])), transition=5),
    21: look("Lightning Storm", each(lambda i: dict(
        fx=FX["lightning"], sx=120 + i * 15, ix=100 + i * 10, pal=PAL_DEFAULT,  # staggered so hoops flash independently
        col=[WHITE, DIM_PURPLE, BLACK])), transition=5),
    # one segment over the whole row so the meteor travels hoop to hoop;
    # ponytail: deletes segments 1-7, the next look's bounds recreate them
    22: look("Meteor Run",
             [{"id": 0, "start": 0, "stop": TOTAL, "n": "All Hoops", "on": True, "bri": 255,
               "grp": 1, "spc": 0, "of": 0, "fx": FX["meteor"], "sx": 200, "ix": 128,
               "pal": PAL_DEFAULT, "col": [ORANGE, BLACK, BLACK]}]
             + [{"id": i, "stop": 0} for i in range(1, HOOPS)], transition=5),
    23: look("Fire Hoops", each(lambda i: dict(
        fx=FX["fire2012"], sx=128, ix=160, pal=PAL_FIRE, col=[ORANGE, BLACK, BLACK])), transition=5),
    24: look("Toxic Drip", each(lambda i: dict(
        fx=FX["drip"], sx=128, ix=64, pal=PAL_DEFAULT, col=[GREEN, DIM_PURPLE, BLACK])), transition=5),
}


def playlist(name, ps, dur_s, transition_s, repeat=0, end=0):
    # dur/transition are in tenths of a second; repeat 0 = loop forever
    return {"n": name, "on": True, "playlist": {
        "ps": ps, "dur": [dur_s * 10] * len(ps), "transition": [transition_s * 10] * len(ps),
        "repeat": repeat, "end": end}}


AMBIENT, SHOW, PREVIEW, OFF = 30, 31, 32, 40
extras = {
    AMBIENT: playlist("Ambient", [10, 11, 12, 13], dur_s=60, transition_s=3),
    SHOW: playlist("Halloween Show", [20, 21, 22, 23, 21, 24], dur_s=30, transition_s=1),
    PREVIEW: playlist("Preview All", [10, 11, 12, 13, 20, 21, 22, 23, 24], dur_s=15, transition_s=1,
                      repeat=1, end=AMBIENT),
    OFF: {"n": "Lights Off", "on": False},
}


def fix_existing(old):
    """Keep presets 1-3 but move them onto the 8-hoop layout (3 is the boot preset)."""
    out = {"0": old["0"]}
    for key, new_id in (("1", 0), ("2", 1)):  # Orange was seg 1 @0-46, Purple seg 2 @46-92
        p = json.loads(json.dumps(old[key]))
        p["seg"].update(id=new_id, n=f"Hoop {new_id + 1}")
        out[key] = p
    blend = json.loads(json.dumps(old["3"]))
    style = {k: v for k, v in blend["seg"][0].items()
             if k not in ("id", "start", "stop", "n", "sel", "len")}
    blend["seg"] = [{**style, **hoop(i)} for i in range(HOOPS)]
    out["3"] = blend
    return out


def check_tiling(segs):
    live = sorted((s["start"], s["stop"]) for s in segs if s.get("stop", 1) != 0)
    pos = 0
    for start, stop in live:
        assert start == pos and stop > start, f"gap/overlap at {start}-{stop}, expected start {pos}"
        pos = stop
    assert pos == TOTAL, f"segments end at {pos}, expected {TOTAL}"


def main():
    old = json.loads((ROOT / "backup/presets-2026-10-12.json").read_text())
    presets = {**fix_existing(old), **{str(k): v for k, v in {**looks, **extras}.items()}}
    for key, p in presets.items():
        if isinstance(p.get("seg"), list):
            check_tiling(p["seg"])
    (ROOT / "presets.json").write_text(json.dumps(presets, separators=(",", ":")))
    print(f"wrote presets.json: {len(presets)} presets")


if __name__ == "__main__":
    main()
