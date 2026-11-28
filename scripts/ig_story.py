#!/usr/bin/env python3
"""Share one of the most-viewed recent Instagram posts as a plain Story (system user token).
Usage: python3 -I ig_story.py pick      show the ranking and which post this slot would share (no posting)
       python3 -I ig_story.py post      publish that post's image as a Story
Ranks feed posts from the last 7 days by views (falls back to reach, then likes+comments
when the token has no instagram_manage_insights), keeps the top 3, and
rotates through them by time slot (two slots a day: before/after 20:00 Tashkent), so the same
post never goes out twice in a row. Carousels use their first image; videos use their video.
The API cannot add a link sticker or reshare a post, so the Story is the image only.
Reads INSTAGRAM_ACCESS_TOKEN from env (strips <> and whitespace). Never prints the token.
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

IG_ID = "17841450362732196"  # @raxmatulloh_numonov
G = "https://graph.facebook.com/v21.0"
TOP = 3
DAYS = 7
TASHKENT = timezone(timedelta(hours=5))
TOKEN = re.sub(r"[<>\s\"']", "", os.environ.get("INSTAGRAM_ACCESS_TOKEN", ""))
if not TOKEN:
    sys.exit("INSTAGRAM_ACCESS_TOKEN missing")


def call(method, path, fail=True, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{G}/{path}" + ("?" + data if method == "GET" else ""),
                                 data=data.encode() if method == "POST" else None, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            out = json.load(r)
    except urllib.error.HTTPError as e:
        out = json.loads(e.read() or b"{}")
    if "error" in out and fail:
        raise SystemExit(f"API error on {path}: {out['error'].get('message')}")
    return out


def metric(m):
    for name in ("views", "reach"):
        d = call("GET", f"{m['id']}/insights", fail=False, metric=name)
        vals = d.get("data") or []
        if vals and vals[0].get("values"):
            return name, vals[0]["values"][0].get("value") or 0
    # token without instagram_manage_insights: fall back to likes + comments
    return "likes+comments", (m.get("like_count") or 0) + (m.get("comments_count") or 0)


def ranked():
    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS)
    media = call("GET", f"{IG_ID}/media", limit=30,
                 fields="id,media_type,media_url,permalink,timestamp,caption,like_count,comments_count,"
                        "children{media_type,media_url}").get("data", [])
    out = []
    for m in media:
        if datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z") < cutoff:
            continue
        src = m
        if m.get("media_type") == "CAROUSEL_ALBUM":
            kids = m.get("children", {}).get("data", [])
            if not kids:
                continue
            src = kids[0]
        if not src.get("media_url"):
            continue
        name, val = metric(m)
        out.append({"id": m["id"], "permalink": m.get("permalink"), "metric": name, "value": val,
                    "type": src.get("media_type"), "media_url": src["media_url"],
                    "caption": (m.get("caption") or "")[:80]})
    return sorted(out, key=lambda r: r["value"], reverse=True)


def choose(rows):
    now = datetime.now(TASHKENT)
    slot = now.toordinal() * 2 + (1 if now.hour >= 20 else 0)
    top = rows[:TOP]
    return top[slot % len(top)] if top else None


def publish(p):
    key = "video_url" if p["type"] == "VIDEO" else "image_url"
    c = call("POST", f"{IG_ID}/media", media_type="STORIES", **{key: p["media_url"]})["id"]
    for _ in range(45):
        s = call("GET", c, fields="status_code").get("status_code")
        if s == "FINISHED":
            break
        if s in ("ERROR", "EXPIRED"):
            raise SystemExit(f"story container status {s}")
        time.sleep(4)
    else:
        raise SystemExit("story container not ready")
    return call("POST", f"{IG_ID}/media_publish", creation_id=c)["id"]


args = sys.argv[1:]
if args not in (["pick"], ["post"]):
    sys.exit(__doc__)
rows = ranked()
p = choose(rows)
if not p:
    print(json.dumps({"skipped": "no posts in the last 7 days"}))
    sys.exit(0)
show = {k: p[k] for k in ("id", "permalink", "metric", "value", "caption")}
if args == ["pick"]:
    print(json.dumps({"chosen": show, "top": [{k: r[k] for k in ("permalink", "metric", "value")}
                                              for r in rows[:TOP]]}, ensure_ascii=False, indent=1))
else:
    sid = publish(p)
    print(json.dumps({"story_id": sid, "from": show}, ensure_ascii=False))
