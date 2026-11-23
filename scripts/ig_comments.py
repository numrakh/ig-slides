#!/usr/bin/env python3
"""Find unanswered Instagram comments and post replies (system user token).
Usage: python3 -I ig_comments.py list [--posts N]       pending comments as JSON
       python3 -I ig_comments.py reply COMMENT_ID TEXT   reply to one comment
       python3 -I ig_comments.py --check                 verify token + comment access
A comment is pending when it is a top-level comment on one of the last N posts (default 25),
written by someone else, newer than scripts/comments_since.txt, and has no reply from
@raxmatulloh_numonov yet. `reply` re-checks that before posting, so it never double-replies.
Reads INSTAGRAM_ACCESS_TOKEN from env (strips <> and whitespace). Never prints the token.
The API cannot like comments; that stays manual.
"""
import json, os, re, sys, urllib.parse, urllib.request
from datetime import datetime

IG_ID = "17841450362732196"  # @raxmatulloh_numonov
OWNER = "raxmatulloh_numonov"
G = "https://graph.facebook.com/v21.0"
HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = re.sub(r"[<>\s\"']", "", os.environ.get("INSTAGRAM_ACCESS_TOKEN", ""))
if not TOKEN:
    sys.exit("INSTAGRAM_ACCESS_TOKEN missing")


def call(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params)
    url = f"{G}/{path}"
    req = urllib.request.Request(url + ("?" + data if method == "GET" else ""),
                                 data=data.encode() if method == "POST" else None, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            out = json.load(r)
    except urllib.error.HTTPError as e:
        out = json.loads(e.read() or b"{}")
    if "error" in out:
        raise SystemExit(f"API error on {path}: {out['error'].get('message')}")
    return out


def ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")


def since():
    with open(os.path.join(HERE, "comments_since.txt")) as f:
        return ts(f.read().strip())


def answered(c):
    return any(r.get("username") == OWNER for r in c.get("replies", {}).get("data", []))


def comments(media_id):
    out, after = [], None
    while True:
        p = {"fields": "id,text,username,timestamp,replies.limit(50){username}", "limit": 50}
        if after:
            p["after"] = after
        d = call("GET", f"{media_id}/comments", **p)
        out += d.get("data", [])
        after = d.get("paging", {}).get("cursors", {}).get("after")
        if not d.get("paging", {}).get("next"):
            return out


def pending(n_posts):
    cutoff = since()
    media = call("GET", f"{IG_ID}/media", fields="id,caption,comments_count,permalink",
                 limit=n_posts).get("data", [])
    res = []
    for m in media:
        if not m.get("comments_count"):
            continue
        for c in comments(m["id"]):
            if c.get("username") == OWNER or answered(c) or ts(c["timestamp"]) < cutoff:
                continue
            res.append({"comment_id": c["id"], "username": c.get("username"), "text": c.get("text", ""),
                        "timestamp": c["timestamp"], "post": m.get("permalink"),
                        "post_caption": (m.get("caption") or "")[:300]})
    return sorted(res, key=lambda r: r["timestamp"])


args = sys.argv[1:]
if args == ["--check"]:
    a = call("GET", IG_ID, fields="username")
    print(json.dumps({"username": a["username"], "since": since().isoformat(),
                      "pending": len(pending(25))}))
elif args[:1] == ["list"]:
    n = int(args[args.index("--posts") + 1]) if "--posts" in args else 25
    print(json.dumps(pending(n), ensure_ascii=False, indent=1))
elif len(args) == 3 and args[0] == "reply":
    cid, text = args[1], args[2].strip()
    if not text:
        sys.exit("empty reply")
    c = call("GET", cid, fields="id,username,replies.limit(50){username}")
    if c.get("username") == OWNER or answered(c):
        print(json.dumps({"skipped": cid, "reason": "own comment or already answered"}))
    else:
        r = call("POST", f"{cid}/replies", message=text[:2200])
        print(json.dumps({"replied": cid, "id": r.get("id")}))
else:
    sys.exit(__doc__)
