#!/usr/bin/env python3
"""Build feed/latest.json from day documents exported from the Curio artifact.

Usage: python3 tools/publish_feed.py <dir with YYYY-MM-DD.json files> [new images dir]

- Reads every day document (either the raw document or {"data": {...}}), keeps the newest 31.
- Copies new <card id>.jpg images into feed/img/ and keeps an image only when its file exists.
- Removes images no card references.
"""
import datetime
import glob
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED = os.path.join(ROOT, "feed")
IMG = os.path.join(FEED, "img")
os.makedirs(IMG, exist_ok=True)

src = sys.argv[1]
new_imgs = sys.argv[2] if len(sys.argv) > 2 else None
if new_imgs:
    for f in glob.glob(os.path.join(new_imgs, "*.jpg")):
        shutil.copy(f, IMG)

days = {}
for path in glob.glob(os.path.join(src, "*.json")):
    name = os.path.basename(path)[:-5]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", name):
        continue
    doc = json.load(open(path, encoding="utf-8"))
    doc = doc.get("data", doc)
    cards = doc.get("cards")
    if not isinstance(cards, list):
        continue
    out = []
    for c in cards:
        c = dict(c)
        im = c.get("image")
        if isinstance(im, dict):
            f = im.get("file")
            if f and re.fullmatch(r"[\w.-]+", f) and os.path.exists(os.path.join(IMG, f)):
                c["image"] = {k: v for k, v in im.items() if k != "id"}
            else:
                c.pop("image", None)
        out.append(c)
    days[name] = {"date": name, "cards": out}

ordered = [days[d] for d in sorted(days, reverse=True)[:31]]
if not ordered:
    raise SystemExit("no day documents found in " + src)

used = {c["image"]["file"] for d in ordered for c in d["cards"] if isinstance(c.get("image"), dict)}
for f in os.listdir(IMG):
    if f.endswith(".jpg") and f not in used:
        os.remove(os.path.join(IMG, f))

feed = {"updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "days": ordered}
json.dump(feed, open(os.path.join(FEED, "latest.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("feed:", ", ".join(f"{d['date']} ({len(d['cards'])})" for d in ordered), "| images:", len(used))
