#!/usr/bin/env python3
"""Publish an Instagram carousel via Meta Graph API (system user token).
Usage: python3 -I ig_publish.py caption.txt URL1 URL2 ... (2-10 public HTTPS JPEG URLs)
       python3 -I ig_publish.py --check   (verify token + account, print quota)
Reads INSTAGRAM_ACCESS_TOKEN from env (strips <> and whitespace). Never prints the token.
Prints JSON {"id":..., "permalink":...} on success.
"""
import json, os, re, sys, time, urllib.parse, urllib.request

IG_ID = "17841450362732196"  # @raxmatulloh_numonov
G = "https://graph.facebook.com/v21.0"
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
    out.pop("paging", None)
    if "error" in out:
        raise SystemExit(f"API error on {path}: {out['error'].get('message')}")
    return out

def wait_ready(cid, tries=30):
    for _ in range(tries):
        s = call("GET", cid, fields="status_code").get("status_code")
        if s == "FINISHED":
            return
        if s in ("ERROR", "EXPIRED"):
            raise SystemExit(f"container {cid} status {s}")
        time.sleep(4)
    raise SystemExit(f"container {cid} not ready")


def facebook_too(cap_path, urls, here):
    """Best effort: also post to the Facebook Page via fb_publish.py --after. Never raises."""
    if not os.environ.get("FACEBOOK_PAGE_TOKEN", "").strip():
        return
    import subprocess
    fb = os.path.join(here, "fb_publish.py")
    try:
        r = subprocess.run([sys.executable, "-I", fb, "--after", cap_path, *urls],
                           capture_output=True, text=True, timeout=900)
        msg = (r.stdout.strip() or r.stderr.strip())[-300:]
        print(f"facebook: {msg}", file=sys.stderr)
    except Exception as e:
        print(f"facebook: error {e}", file=sys.stderr)

if sys.argv[1:] == ["--check"]:
    a = call("GET", IG_ID, fields="username,media_count")
    q = call("GET", f"{IG_ID}/content_publishing_limit", fields="quota_usage,config")
    print(json.dumps({"username": a["username"], "quota": q["data"][0]}))
    sys.exit()

caption = open(sys.argv[1], encoding="utf-8").read().strip()
urls = sys.argv[2:]
if not 2 <= len(urls) <= 10:
    sys.exit("need 2-10 image URLs")
import atexit
# __file__ is gone by atexit time in Python 3.13, so pass the folder now
atexit.register(facebook_too, sys.argv[1], urls, os.path.dirname(os.path.abspath(__file__)))
kids = []
for u in urls:
    kids.append(call("POST", f"{IG_ID}/media", image_url=u, is_carousel_item="true")["id"])
for k in kids:
    wait_ready(k)
cid = call("POST", f"{IG_ID}/media", media_type="CAROUSEL", children=",".join(kids), caption=caption)["id"]
wait_ready(cid)
mid = call("POST", f"{IG_ID}/media_publish", creation_id=cid)["id"]
info = call("GET", mid, fields="id,permalink,timestamp")
print(json.dumps(info))
